# Dockerfile — 高考志愿推荐 API (单 target, OCR 走 MinerU SDK)
#
# Build: docker build -t gaokao-hubei-mvp:api .
# Run:   docker run -d --rm -p 8000:8000 gaokao-hubei-mvp:api
# 文档:  http://localhost:8000/docs
#
# OCR: 不在容器内跑. 用 MinerU SDK (`pip install mineru`) 在本地/Mac
# 直接调 flash_extract 解析 PDF/PNG. 见 scripts/parse_gk100_hb_2025_phys_full.py
# 与 docs/ARCHITECTURE.md "OCR 架构规定" 节.

ARG PYTHON_VERSION=3.11-slim

# ─────────────────────────────────────
# Base — 共享层
# ─────────────────────────────────────
FROM python:${PYTHON_VERSION} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 系统依赖 (gcc 给 pandas/numpy 编译, libgomp 不再需要 — PaddleOCR 已移除)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ \
        && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────
# API target (生产)
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
