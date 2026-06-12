"""
SCF 入口 — 长尾专业按需生成 (handler + worker 二合一).

部署:
  - 腾讯云 SCF 香港地域, Python 3.11, timeout 900s (15min), memory 1024MB
  - API Gateway 触发器: POST /synth/generate, GET /synth/status

API 协议:
  POST /synth/generate
    body: {"title": "治安学", "slug": "gongzhi-xue"}
    resp: {"ok": true, "run_id": "...", "status_url": "/synth/status?run_id=..."}

  GET /synth/status?run_id=...
    resp: {
      "run_id": "...",
      "status": "queued|running|done|failed",
      "step": "synthesize_json|render_html|...",
      "progress": 0.0-1.0,
      "title": "治安学", "slug": "gongzhi-xue", "style": "gongan",
      "output_url": "/gongzhi-xue.html" (done 时),
      "error": "..." (failed 时),
      "started_at": "...", "updated_at": "...", "quality_score": 0.95
    }

并发模型:
  - POST /generate 立即返回 run_id, 状态写 COS synth-jobs/<run_id>.json
  - 在请求处理函数内**直接**跑完整 7 步 pipeline (15min 内)
  - 前端 GET /status 轮询; SCF 无状态
  - COS 不可用时降级: 内存 dict 缓存 (单实例限制, 但 HK SCF 单并发足够)

环境变量:
  DEEPSEEK_API_KEY     DeepSeek API key
  COS_SECRET_ID, COS_SECRET_KEY, COS_BUCKET, COS_REGION
  TENCENTCLOUD_SECRETID, TENCENTCLOUD_SECRETKEY, TENCENTCLOUD_REGION
"""
from __future__ import annotations
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# SCF 部署包里要带整套 scf/synth + skills/.../scripts
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills" / "gaokao-major-explorer" / "scripts"))

# 复用 synth_trigger 的单篇 pipeline
from scf.synth.llm import DeepSeekClient, RetryableError, PermanentError
from scf.synth.search import search_multi, queries_for_major, format_for_prompt
from scf.synth.prompts import load_schema_doc, load_sample_for_style, summarize_sample
from scf.synth.validator import validate, score_quality
from scf.synth.manifest_ops import upsert_manifest_minimal
from scf.synth.render_bridge import render_html, save_data_json, RenderError


# ── COS 状态层 (可选) ──
class JobStore:
    """跨 invocation 持久化 job 状态. 优先用 COS, 失败 fallback 内存."""

    def __init__(self):
        self.cos_bucket = os.environ.get("COS_BUCKET", "")
        self.cos_region = os.environ.get("COS_REGION", "ap-hongkong")
        self.cos_secret_id = os.environ.get("COS_SECRET_ID", "")
        self.cos_secret_key = os.environ.get("COS_SECRET_KEY", "")
        self._mem: dict[str, dict] = {}
        self._cos_client = None
        if self.cos_bucket and self.cos_secret_id:
            try:
                from qcloud_cos import CosConfig, CosS3Client
                cfg = CosConfig(Region=self.cos_region,
                                SecretId=self.cos_secret_id,
                                SecretKey=self.cos_secret_key)
                self._cos_client = CosS3Client(cfg)
            except ImportError:
                print("[JobStore] qcloud-cos-python-sdk 未装, 走内存模式", flush=True)
                self._cos_client = None

    def _key(self, run_id: str) -> str:
        return f"synth-jobs/{run_id}.json"

    def put(self, run_id: str, state: dict):
        body = json.dumps(state, ensure_ascii=False).encode("utf-8")
        if self._cos_client and self.cos_bucket:
            try:
                self._cos_client.put_object(
                    Bucket=self.cos_bucket, Key=self._key(run_id), Body=body,
                    ContentType="application/json",
                )
                return
            except Exception as e:
                print(f"[JobStore] COS put 失败, 走内存: {e}", flush=True)
        self._mem[run_id] = state

    def get(self, run_id: str) -> dict | None:
        if self._cos_client and self.cos_bucket:
            try:
                resp = self._cos_client.get_object(Bucket=self.cos_bucket, Key=self._key(run_id))
                return json.loads(resp["Body"].read().decode("utf-8"))
            except Exception as e:
                print(f"[JobStore] COS get 失败: {e}", flush=True)
        return self._mem.get(run_id)


STORE = JobStore()


# ── 7 步 worker ──
def worker(run_id: str, title: str, slug: str, style_override: str | None = None):
    """
    7 步 pipeline, 每步把状态写 COS, 失败时标 failed.
    """
    state = {
        "run_id": run_id,
        "status": "running",
        "step": "init",
        "progress": 0.0,
        "title": title, "slug": slug,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cost_cny": 0.0,
        "quality_score": 0.0,
    }
    STORE.put(run_id, state)

    def update(step: str, progress: float, **extra):
        state["step"] = step
        state["progress"] = progress
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        state.update(extra)
        STORE.put(run_id, state)

    try:
        # ── Step 1: validate_is_major ──
        update("validate", 0.1)
        llm = DeepSeekClient()
        is_major, normalized = llm.validate_is_major(title)
        if not is_major:
            state["status"] = "failed"
            state["error"] = f"不是本科专业: {title}"
            STORE.put(run_id, state)
            return
        title = normalized or title
        state["title"] = title

        # ── Step 2: web search ──
        update("search", 0.2)
        queries = queries_for_major(title)
        snippets = search_multi(queries, per_query=8)
        search_context = format_for_prompt(snippets)
        state["search_snippets"] = len(snippets)

        # ── Step 3: route_style ──
        update("route_style", 0.3)
        if style_override and style_override in (
            "cs", "eng", "medicine", "education", "finance", "law",
            "humanities", "sci", "administration", "agri", "arts",
            "gongan", "business",
        ):
            style = style_override
        else:
            style = llm.route_style(title, search_context[:500])
        state["style"] = style

        # ── Step 4-5: synthesize + validate (≤3 轮) ──
        update("synthesize", 0.4)
        schema_doc = load_schema_doc()
        sample = load_sample_for_style(ROOT, style)
        sample_summary = summarize_sample(sample)
        prev_errs, prev_warns = [], []
        data, quality = None, {}
        for round_i in range(1, 4):
            data = llm.synthesize_json(
                title=title, style=style, search_context=search_context,
                sample_json=sample, schema_doc=schema_doc,
                previous_errors=prev_errs, previous_warnings=prev_warns,
            )
            ok, errs, warns = validate(data)
            quality = score_quality(data)
            if ok and quality["quality_score"] >= 0.7:
                break
            prev_errs, prev_warns = errs, warns
            state["synth_round"] = round_i
            state["synth_errors"] = errs[:5]
            STORE.put(run_id, state)

        if not data or quality.get("quality_score", 0) < 0.7:
            state["status"] = "failed"
            state["error"] = f"质量分 {quality.get('quality_score', 0)} < 0.7, 3 轮未达标"
            state["quality_score"] = quality.get("quality_score", 0)
            STORE.put(run_id, state)
            return

        data.setdefault("slug", slug)
        data.setdefault("style", style)
        data.setdefault("updated_at", time.strftime("%Y-%m"))
        data.setdefault("data_source", f"按需生成 (DeepSeek-V3) + Web 搜索 + {time.strftime('%Y-%m-%d')}")
        state["quality_score"] = quality["quality_score"]

        # ── Step 6: render_html ──
        update("render", 0.7)
        save_data_json(data, slug)
        out_path, size = render_html(data, slug, style)
        state["html_size"] = size
        state["html_path"] = out_path

        # ── Step 7: append manifest ──
        update("manifest", 0.9)
        ok = upsert_manifest_minimal(
            root=ROOT, slug=slug, title=data.get("title", title), style=style,
            category=data.get("category", ""), degree=data.get("degree", ""),
            duration_years=data.get("duration_years", 4),
            tags=data.get("tags", []), data_source=data.get("data_source", ""),
        )
        state["manifest_upsert"] = ok

        # ── 完成 ──
        state["status"] = "done"
        state["step"] = "complete"
        state["progress"] = 1.0
        state["output_url"] = f"/{slug}.html"
        state["cost_cny"] = round(llm.cost_estimate_cny(), 4)
        state["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STORE.put(run_id, state)
    except (RetryableError, PermanentError, RenderError) as e:
        state["status"] = "failed"
        state["error"] = f"{type(e).__name__}: {e}"
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STORE.put(run_id, state)
    except Exception as e:
        state["status"] = "failed"
        state["error"] = f"Unexpected: {type(e).__name__}: {e}"
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STORE.put(run_id, state)


# ── HTTP 路由 ──
def _resp(status: int, body: dict, headers: dict | None = None) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            **(headers or {}),
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def handler(event: dict, context: Any) -> dict:
    """SCF API Gateway 入口."""
    # OPTIONS 预检
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {"ok": True})

    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    query = event.get("queryString", {}) or {}
    body_str = event.get("body", "") or "{}"

    # 去掉前缀 /synth
    if path.startswith("/synth"):
        path = path[len("/synth"):] or "/"

    try:
        body = json.loads(body_str) if body_str.strip() else {}
    except json.JSONDecodeError:
        return _resp(400, {"ok": False, "error": "body 不是 JSON"})

    # ── POST /generate ──
    if method == "POST" and path == "/generate":
        title = (body.get("title") or "").strip()
        slug = (body.get("slug") or "").strip()
        style = (body.get("style") or "").strip() or None
        if not title:
            return _resp(400, {"ok": False, "error": "title 必填"})
        if not slug:
            # 用 title 简单 slugify
            import re
            slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")
        # 限流: 同 title 24h 内去重 (内存版, 适合 MVP)
        # 略 — 生产用 COS 查
        run_id = uuid.uuid4().hex[:16]
        # 同步跑 (15min 内) — 简单粗暴, 后续可改 async + EventBridge
        worker(run_id, title, slug, style)
        # 跑完后再读一次最新状态
        final = STORE.get(run_id) or {}
        return _resp(200, {
            "ok": final.get("status") == "done",
            "run_id": run_id,
            "status": final.get("status"),
            "output_url": final.get("output_url"),
            "quality_score": final.get("quality_score"),
            "error": final.get("error"),
        })

    # ── GET /status ──
    if method == "GET" and path == "/status":
        run_id = (query.get("run_id") or "").strip()
        if not run_id:
            return _resp(400, {"ok": False, "error": "run_id 必填"})
        st = STORE.get(run_id)
        if not st:
            return _resp(404, {"ok": False, "error": "run_id not found"})
        return _resp(200, st)

    # ── GET / (健康检查) ──
    if method == "GET" and path in ("/", "/health"):
        return _resp(200, {
            "ok": True,
            "service": "synth",
            "version": "0.1.0",
            "cos_enabled": bool(STORE._cos_client),
        })

    return _resp(404, {"ok": False, "error": f"not found: {method} {path}"})


# ── 本地调试 ──
if __name__ == "__main__":
    import json as _json
    # 健康检查
    r = handler({"httpMethod": "GET", "path": "/synth/health", "queryString": {}}, None)
    print(_json.loads(r["body"]))

    # 真实触发 (需 DEEPSEEK_API_KEY)
    if os.environ.get("DEEPSEEK_API_KEY"):
        r = handler({
            "httpMethod": "POST", "path": "/synth/generate",
            "body": _json.dumps({"title": "保险学", "slug": "insurance"}),
        }, None)
        print(_json.loads(r["body"]))
    else:
        print("(设 DEEPSEEK_API_KEY 后可本地触发真实合成)")
