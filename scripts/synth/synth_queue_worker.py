#!/usr/bin/env python3
"""
synth_queue_worker.py — Hybrid pipeline 队列 worker (CF Pages Function + GH Action)

调用:  GH Action cron */1 (公开仓库 0 成本)
位置:  scripts/synth_queue_worker.py

流程:
  1. 从 D1 拉 status='queued' AND attempts<3 的下一个 job
  2. 设 status='running', attempts++, started_at=now
  3. 调 scf/synth/main.py:worker(run_id, title, slug, style) — 复用 SCF 7 步 pipeline
     - 中途 step/progress 回调 → updateJob(D1)
  4. 跑完:
     - done → status='done', output_url, finished_at
     - failed → status='failed' (attempts 已 +1, 下次 cron 再 claim)
     - 3 次仍 failed → status='dead'
  5. 不动 git push (由 GH Action step 负责)

约束:
  - 单进程, 不并发 (CF Pages Function 10ms CPU 不允许, GH Action 1 process 也行)
  - DEEPSEEK_API_KEY 必设, 否则 raise
  - CF API Token 必须有 D1:Edit 权限
  - 1 次 cron 最多跑 1 个 job (避免 GH Action 20min timeout)
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


# ── D1 REST API 客户端 ──
class D1:
    def __init__(self, account_id: str, database_id: str, api_token: str):
        self.base = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def query(self, sql: str, params: list | None = None) -> dict:
        """D1 查询, 瞬时错误 (网络抖动 / 5xx / 429) 自动重试 2 次.

        GH Action cron 每 ~40min 跑一次, claim_next/update_progress 在 try 外,
        一次 CF API 抖动 = 整个 workflow 红. 指数退避 1s/2s 吸收瞬时故障.
        """
        body = {"sql": sql, "params": params or []}
        last_err: Exception | None = None
        for attempt in range(3):
            req = urllib.request.Request(
                f"{self.base}/query", data=json.dumps(body).encode("utf-8"),
                headers=self.headers, method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err = e.read().decode("utf-8", errors="replace")
                if e.code == 429 or e.code >= 500:
                    last_err = RuntimeError(f"D1 query failed (transient): HTTP {e.code} {err[:300]}")
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"D1 query failed: HTTP {e.code} {err[:300]}") from e
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last_err = RuntimeError(f"D1 query failed (transient): {type(e).__name__}: {e}")
                time.sleep(2 ** attempt)
                continue
            if not data.get("success"):
                raise RuntimeError(f"D1 query failed: {data.get('errors', [])}")
            return data.get("result", [{}])[0]
        raise last_err

    def first(self, sql: str, params: list | None = None) -> dict | None:
        r = self.query(sql, params)
        rows = r.get("results", [])
        return rows[0] if rows else None

    def all(self, sql: str, params: list | None = None) -> list[dict]:
        r = self.query(sql, params)
        return r.get("results", [])

    def execute(self, sql: str, params: list | None = None) -> int:
        """INSERT/UPDATE/DELETE, 返 affected rows."""
        r = self.query(sql, params)
        return r.get("meta", {}).get("changes", 0)


# ── 同步 D1 → SynthJob dict ──
def claim_next(d1: D1) -> dict | None:
    """原子抢占: status='queued' AND attempts<3, 改 running + attempts++."""
    job = d1.first(
        "SELECT run_id, title, slug, style, attempts FROM synth_jobs "
        "WHERE status='queued' AND attempts<3 "
        "ORDER BY created_at ASC LIMIT 1",
    )
    if not job:
        return None
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    affected = d1.execute(
        "UPDATE synth_jobs SET status='running', attempts=attempts+1, "
        "started_at=COALESCE(started_at, ?2), updated_at=?2 "
        "WHERE run_id=?1 AND status='queued'",
        [job["run_id"], now],
    )
    if affected == 0:
        return None  # 别人抢了
    job["status"] = "running"
    job["attempts"] = (job.get("attempts") or 0) + 1
    return job


def update_progress(d1: D1, run_id: str, **fields) -> None:
    """更新 progress/step/cost/... 任意字段 (不含 status 强制覆盖)."""
    if not fields:
        return
    set_parts = []
    final_params = []
    for i, (k, v) in enumerate(fields.items(), start=1):
        set_parts.append(f"{k}=?{i}")
        final_params.append(v)
    n = len(fields)
    set_parts.append(f"updated_at=?{n+1}")
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    final_params.append(now)
    final_params.append(run_id)
    sql = f"UPDATE synth_jobs SET {', '.join(set_parts)} WHERE run_id=?{n+2}"
    d1.query(sql, final_params)


def mark_done(d1: D1, run_id: str, **fields) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    fields.setdefault("finished_at", now)
    set_parts = [f"{k}=?" for k in fields]
    params = list(fields.values())
    set_parts.append("updated_at=?")
    params.append(now)
    set_parts.append("status='done'")
    params.append(run_id)
    sql = f"UPDATE synth_jobs SET {', '.join(set_parts)} WHERE run_id=?"
    d1.query(sql, params)


def mark_failed(d1: D1, run_id: str, error: str, dead: bool = False) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    status = "dead" if dead else "failed"
    d1.query(
        f"UPDATE synth_jobs SET status=?, error=?, updated_at=?, finished_at=? WHERE run_id=?",
        [status, error, now, now, run_id],
    )


# ── GH Issue 上报 (attempts 满 3 死信时调用) ──
def report_dead_to_github(title: str, slug: str, run_id: str, error: str) -> bool:
    """attempts=3 全失败时, 创建 GH Issue 让运营巡检 (Session 2 Task 4 加).

    需要 GITHUB_TOKEN + GITHUB_REPO env (来自 GH Action secret).
    Fail open: 网络/token 错不抛, 仅 print warning.
    """
    gh_token = os.environ.get("GITHUB_TOKEN", "").strip()
    # 兼容两种命名: GH 拒绝 GITHUB_ 前缀, 用户在 repo secrets 里配为 GH_REPO
    # CF Pages Function 端仍可用 GITHUB_REPO (没有这个限制)
    gh_repo = os.environ.get("GH_REPO") or os.environ.get("GITHUB_REPO") or os.environ.get("GITHUB_REPOSITORY") or ""
    gh_repo = gh_repo.strip()
    if not gh_token or not gh_repo:
        print(f"  [report-dead] GITHUB_TOKEN/GH_REPO 未设, 跳过 GH Issue 上报")
        return False
    try:
        safe_error = error[:300].replace("\n", " ")
        body = json.dumps({
            "title": f"[synth-dead] {title} ({slug})",
            "labels": ["synth-dead", "auto"],
            "body": (
                f"## Synth Dead Alert\n\n"
                f"- **Title**: {title}\n"
                f"- **Slug**: `{slug}`\n"
                f"- **Run ID**: `{run_id}`\n"
                f"- **Attempts**: 3 (全失败)\n"
                f"- **Last Error**: `{safe_error}`\n\n"
                f"---\n由 `synth_queue_worker.py` 自动生成."
            ),
        }, ensure_ascii=False)
        req = urllib.request.Request(
            f"https://api.github.com/repos/{gh_repo}/issues",
            data=body.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {gh_token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "synth-queue-worker/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            print(f"  [report-dead] ✓ GH Issue #{payload.get('number')}: {payload.get('html_url')}")
            return True
    except Exception as e:
        print(f"  [report-dead] ✗ GH Issue 创建失败: {type(e).__name__}: {str(e)[:200]}")
        return False


# ── 调 scf/synth worker (复用 7 步 pipeline) ──
def run_synth(run_id: str, title: str, slug: str, style: str | None,
              d1: D1, env: dict) -> dict:
    """
    调 scf/synth/main.py:worker() 但它内部写自己的 STORE, 拿不到状态.
    解决: 用 subprocess 跑 synth_trigger.py --from-json 半 pipeline 太复杂.
    折中: 用 sys.path 注入 + import worker, 包装它的 STORE.put 拦截.

    简化: 直接 subprocess 跑 synth_trigger.py 完整 pipeline,
    完成后再从 manifest 拿 output_url.
    """
    cmd = [
        sys.executable, str(ROOT / "scripts" / "synth_trigger.py"),
        "--title", title,
        "--slug", slug,
    ]
    if style:
        cmd += ["--style", style]
    # skip-search 在 GH Action 默认开 (没 web search API key)
    cmd += ["--skip-search"]

    print(f"  → subprocess: {' '.join(cmd)}")
    update_progress(d1, run_id, step="synthesize", progress=0.4)

    try:
        proc = subprocess.run(
            cmd, env=env, cwd=str(ROOT), capture_output=True, text=True,
            timeout=1800,  # 30min (Day 7 调整: m3 retry + deepseek fallback 可能 15-25min)
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"synth_trigger 超时 30min") from e

    print(f"  ← rc={proc.returncode}, stdout={len(proc.stdout)}c, stderr={len(proc.stderr)}c")
    if proc.returncode != 0:
        raise RuntimeError(f"synth_trigger rc={proc.returncode}: {proc.stderr[-500:]}")

    # 解析 summary
    # synth_trigger.py 写 --out 时返 JSON, 没写时输出到 stdout 末尾
    # 简单: 从 manifest.json 拿刚 upsert 的 entry
    manifest_p = ROOT / "public" / "data" / "manifest.json"
    if not manifest_p.exists():
        raise RuntimeError("manifest.json 不存在")
    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
    entry = next((m for m in manifest.get("majors", []) if m.get("slug") == slug), None)
    if not entry:
        raise RuntimeError(f"manifest 里没找到 slug={slug}")

    # 读 quality_score from data json
    data_p = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated" / f"{slug}.json"
    quality = 0.0
    cost = 0.0
    if data_p.exists():
        try:
            data = json.loads(data_p.read_text(encoding="utf-8"))
            # 优先 _meta (synth_trigger 写入)
            meta = data.get("_meta", {})
            quality = meta.get("quality_score", 0.0)
            cost = meta.get("cost_cny", 0.0)
        except Exception:
            pass

    return {
        "ok": True,
        "output_url": f"/{slug}.html",
        "quality_score": quality,
        "cost_cny": cost,
        "html_size": (ROOT / "public" / f"{slug}.html").stat().st_size if (ROOT / "public" / f"{slug}.html").exists() else 0,
    }


# ── 入口 ──
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="跑 1 个 job 后退出 (默认 GH Action 行为)")
    p.add_argument("--max", type=int, default=1, help="最多跑几个 job (防 GH Action timeout)")
    args = p.parse_args()

    # ── 凭据 ──
    cf_account = os.environ.get("CF_ACCOUNT_ID", "").strip()
    cf_token = os.environ.get("CF_API_TOKEN", "").strip()
    cf_d1 = os.environ.get("CF_D1_DATABASE_ID", "").strip()
    deepseek = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not all([cf_account, cf_token, cf_d1]):
        print("❌ CF_ACCOUNT_ID / CF_API_TOKEN / CF_D1_DATABASE_ID 必须设", file=sys.stderr)
        sys.exit(2)
    if not deepseek:
        print("❌ DEEPSEEK_API_KEY 未设 (worker 跑不了)", file=sys.stderr)
        sys.exit(2)

    d1 = D1(cf_account, cf_d1, cf_token)
    env = {**os.environ, "DEEPSEEK_API_KEY": deepseek}

    processed = 0
    while processed < args.max:
        job = claim_next(d1)
        if not job:
            print(f"⏭️  队列空 (processed={processed}), 退出")
            break

        run_id = job["run_id"]
        title = job["title"]
        slug = job["slug"]
        style = job.get("style")
        attempt_n = job["attempts"]
        print(f"\n{'='*60}\n📚 [{processed+1}/{args.max}] run_id={run_id} title={title!r} slug={slug!r} style={style} attempt={attempt_n}\n{'='*60}")

        update_progress(d1, run_id, step="init", progress=0.1)

        try:
            result = run_synth(run_id, title, slug, style, d1, env)
            mark_done(d1, run_id,
                step="complete",
                progress=1.0,
                output_url=result["output_url"],
                quality_score=result["quality_score"],
                cost_cny=result["cost_cny"],
                html_size=result["html_size"],
            )
            print(f"✅ done: {result['output_url']} quality={result['quality_score']} cost=¥{result['cost_cny']}")
        except Exception as e:
            err = f"{type(e).__name__}: {e}"[:500]
            print(f"❌ failed: {err}")
            # attempts 已经被 claim_next +1, 当前值是 attempt_n
            dead = attempt_n >= 3
            mark_failed(d1, run_id, err, dead=dead)
            if dead:
                print(f"💀 run_id={run_id} attempts 满 3 标 dead, 不再重试")
                # 自动上报 GH Issue (运营巡检用)
                report_dead_to_github(title=title, slug=slug, run_id=run_id, error=err)

        processed += 1

    print(f"\n=== worker done: processed={processed} ===")


if __name__ == "__main__":
    main()
