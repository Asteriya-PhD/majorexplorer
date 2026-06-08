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

## 2. OCR — 走 MinerU SDK (本地, 不容器化)

> 2026-06-08 架构升级: PaddleOCR 容器方案已废, 全部走 MinerU SDK (`pip install mineru`).
> 免 token, Mac/Linux/Win 通用, ~20s/页. 详见 `docs/ARCHITECTURE.md` "OCR 架构规定" 节.

```bash
# 一次性 OCR (本地 Python 调, 无需 Docker)
python3 -c "
from mineru import MinerU
client = MinerU(token=None)
client.set_source('gaokao-hubei-mvp')
r = client.flash_extract('input.png', is_ocr=True, enable_table=True, timeout=300)
print(r.markdown)
"
```

PNG 表格场景 (e.g. gk100 1998271 物理全表):
1. 大图 (>2000px 高) 切 chunk (PIL `Image.crop`, 重叠 50px)
2. 每 chunk `flash_extract(is_ocr=True, enable_table=True)`
3. 合并所有 chunk 的 HTML `<table>` → `pd.read_html` / regex
4. 反查 min_rank via `score_to_rank` (hubei_rank_*.csv)

实操脚本: `scripts/parse_gk100_hb_2025_phys_full.py` (5 chunk → 394 行 物理 投档表).

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
Dockerfile             # 单 target: api (OCR 走 MinerU SDK, 不容器化)
docker-compose.yml     # api only
.dockerignore          # 排除 caches, logs, tests
requirements.txt       # gunicorn + mineru (OCR SDK)
scripts/parse_gk100_hb_2025_phys_full.py  # MinerU OCR 实操模板
```
