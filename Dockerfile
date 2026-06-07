# Dockerfile — 高考志愿推荐 API + PaddleOCR (二选一 build target)
#
# Build targets:
#   docker build --target api      -t gaokao-api .      (默认)
#   docker build --target paddleocr -t gaokao-paddleocr .
#
# 推荐: docker compose up (自动用 api 目标)

ARG PYTHON_VERSION=3.11-slim

# ─────────────────────────────────────
# 1. Base — 共享层
# ─────────────────────────────────────
FROM python:${PYTHON_VERSION} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 系统依赖 (gcc 给 pandas/numpy 编译, libgomp 给 paddleocr)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libgomp1 libgl1 libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────
# 2. API target (生产)
# ─────────────────────────────────────
FROM base AS api

# 装 Python deps (用 gunicorn 替代 uvicorn dev server)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目 (排除 caches / logs / .git — 见 .dockerignore)
COPY api/ ./api/
COPY core/ ./core/
COPY cli_demo.py .
COPY data/ ./data/

EXPOSE 8000

# Healthcheck: ping /docs
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs').read()" \
        || exit 1

# 4 workers × 1 thread (CPU bound 推荐 workers=cpu_count, 这里保守 4)
CMD ["gunicorn", "api.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

# ─────────────────────────────────────
# 3. PaddleOCR target (数据 ingest, 按需跑)
# ─────────────────────────────────────
FROM base AS paddleocr

# PaddlePaddle + PaddleOCR (Linux 才有 arm64/x86 wheels, 解决 Mac 上无 wheel 问题)
RUN pip install --no-cache-dir \
        paddlepaddle==3.0.0 \
        paddleocr==3.0.0 \
        Pillow

COPY scripts/parse_dxsbb_ocr.py ./scripts/
COPY data/_cache/dxsbb_imgs/ ./data/_cache/dxsbb_imgs/

# 默认不跑, 需 docker compose run --rm paddleocr 触发
ENTRYPOINT ["python", "scripts/paddleocr_ocr.py"]
