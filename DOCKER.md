# Docker 化使用说明 (OrbStack / Docker Desktop 通用)

> macOS 推荐用 [OrbStack](https://orbstack.dev/) (轻量, Swift 原生, 0.1% CPU).

## 0. 一键切换到 OrbStack (已装的用户)

```bash
docker context use orbstack   # 已激活 (active context = orbstack)
```

如果是 Docker Desktop: `docker context use desktop-linux`

## 1. 启动 API 服务

```bash
docker compose up --build -d
# 等 30s (gunicorn 启动 + 健康检查)
curl http://localhost:8000/docs   # Swagger UI
```

停止: `docker compose down`
日志: `docker compose logs -f api`

### 镜像内容
- `python:3.11-slim` base
- `requirements.txt` 全装 (fastapi/pandas/reportlab/...)
- `gunicorn` 4 workers (替换 uvicorn dev server)
- 只读挂载 `data/` 目录, 写挂载 `logs/`
- 健康检查每 30s ping `/docs`

## 2. 按需跑 PaddleOCR 重 OCR (Mac 友好)

> PaddlePaddle 在 Mac arm64 + Python 3.14 没 wheel. 容器内跑 Linux x86_64 / arm64 通杀.

```bash
# 一次性跑 (默认 profile=ocr 不启动, 需 --profile 显式)
docker compose --profile ocr run --rm paddleocr
```

镜像内容:
- `paddlepaddle==3.0.0` + `paddleocr==3.0.0`
- 6 张 dxsbb 2024 PNG (hist_1/2/3 + phys_1/2/3, 2x 高清)
- 输出 `data/_cache/dxsbb_imgs/ocr_2024_*_v4.txt` (挂回 host)

## 3. 验证

```bash
docker compose ps            # 看 api container health
docker compose exec api python -c "from api.main import app; print('OK')"
docker compose logs api | tail -20
```

### 实测 (2026-06-08, OrbStack + daocloud mirror)

| 步骤 | 结果 |
|---|---|
| `docker build --target api -t gaokao-hubei-mvp:api .` | ✅ 14 layers, 212MB image |
| `docker run -d --rm -p 18000:8000 gaokao-hubei-mvp:api` | ✅ 8s 启动 |
| `curl http://localhost:18000/docs` | ✅ 200 OK, Swagger UI |
| `curl /api/meta` | ✅ 3 省份 × 2 科目 × 3 年 |
| `POST /api/score-to-rank {score:600, GD 物理}` | ✅ rank=18000 (校准后) |
| `POST /api/rank-to-score {rank:10000, GD 物理}` | ✅ score=620 |
| `POST /api/equivalent {rank:10000, HB 物理, 2024→2025}` | ✅ {2023:624, 2024:619, 2025:612} |
| `POST /api/recommend {rank:10000, HB 物理, 2025}` | ✅ 15 推 (含 985 西安交大 冲档) |
| Healthcheck (`/docs` 每 30s) | ✅ healthy |

## 4. 网络注意

- Docker Hub (registry-1.docker.io) 偶发 Bad Gateway, 镜像拉取失败时:
  - 换 `docker context use desktop-linux` 试 Docker Desktop
  - 或配置 Docker Hub 镜像 (`~/.docker/daemon.json`):
    ```json
    {"registry-mirrors": ["https://docker.m.daocloud.io"]}
    ```
  - 上面是 **2026-06-08 实测可用** 的 (daocloud 返回 401 = 可达需 auth, 比 ccs.tencentyun
    / ustc 都稳). 重启 OrbStack 后生效.
- OrbStack 自带缓存, 第二次 build 会快很多
- 手动预拉 base 镜像 (build 卡 metadata resolve 时): 
  ```bash
  docker pull docker.m.daocloud.io/library/python:3.11-slim
  docker tag docker.m.daocloud.io/library/python:3.11-slim python:3.11-slim
  ```

## 5. 文件结构

```
Dockerfile             # 多 target: base / api / paddleocr
docker-compose.yml     # api (default) + paddleocr (profile=ocr)
.dockerignore          # 排除 caches, logs, tests
requirements.txt       # 加了 gunicorn==23.0.0
scripts/paddleocr_ocr.py  # PaddleOCR 主脚本 (容器内 ENTRYPOINT)
```
