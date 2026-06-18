#!/usr/bin/env python3
"""
synth_monitor.py — 在线按需合成每日巡检 (Day 7 Session 4 上线后用)

调用:
  python3 scripts/synth_monitor.py          # 跑 1 次报告
  python3 scripts/synth_monitor.py --json   # JSON 输出给 pipe

环境变量:
  CF_ACCOUNT_ID, CF_API_TOKEN, CF_D1_DATABASE_ID  (D1 REST API 凭据)

输出:
  - 队列深度 (理想 <3)
  - 24h 内 done/failed/dead 数 + 失败率
  - 平均耗时 (秒)
  - 累计成本 (¥)
  - 异常告警 (失败率 >15% 或 队列 >5 或 平均耗时 >180s)

GH Action cron 建议: 每天 9:00 跑 1 次, 失败时 createIssue 标 synth-alert.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime


def d1_query(account_id: str, database_id: str, api_token: str, sql: str, params: list | None = None) -> dict:
    body = {"sql": sql, "params": params or []}
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def d1_first(account_id: str, database_id: str, api_token: str, sql: str) -> dict | None:
    r = d1_query(account_id, database_id, api_token, sql)
    rows = r.get("result", [{}])[0].get("results", [])
    return rows[0] if rows else None


def d1_all(account_id: str, database_id: str, api_token: str, sql: str) -> list[dict]:
    r = d1_query(account_id, database_id, api_token, sql)
    return r.get("result", [{}])[0].get("results", [])


def main():
    p = argparse.ArgumentParser(description="按需合成每日巡检")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    p.add_argument("--alert-threshold-fail-pct", type=float, default=15.0)
    p.add_argument("--alert-threshold-queue", type=int, default=5)
    p.add_argument("--alert-threshold-avg-sec", type=float, default=180.0)
    args = p.parse_args()

    cf_account = os.environ.get("CF_ACCOUNT_ID", "").strip()
    cf_token = os.environ.get("CF_API_TOKEN", "").strip()
    cf_d1 = os.environ.get("CF_D1_DATABASE_ID", "").strip()
    if not all([cf_account, cf_token, cf_d1]):
        print("❌ CF_ACCOUNT_ID / CF_API_TOKEN / CF_D1_DATABASE_ID 必须设", file=sys.stderr)
        sys.exit(2)

    # ── 1. 队列深度 ──
    queue_row = d1_first(cf_account, cf_d1, cf_token,
        "SELECT COUNT(*) as n FROM synth_jobs WHERE status='queued'")
    queue_depth = queue_row.get("n", 0) if queue_row else 0

    # ── 2. 24h 内 done/failed/dead 数 + 失败率 ──
    day_row = d1_first(cf_account, cf_d1, cf_token,
        """SELECT
          COUNT(CASE WHEN status='done' THEN 1 END) as done,
          COUNT(CASE WHEN status='failed' THEN 1 END) as failed,
          COUNT(CASE WHEN status='dead' THEN 1 END) as dead,
          COUNT(*) as total
        FROM synth_jobs WHERE created_at > datetime('now', '-1 day')""")
    done = day_row.get("done", 0) if day_row else 0
    failed = day_row.get("failed", 0) if day_row else 0
    dead = day_row.get("dead", 0) if day_row else 0
    total = day_row.get("total", 0) if day_row else 0
    fail_pct = (100.0 * (failed + dead) / total) if total > 0 else 0.0

    # ── 3. 平均耗时 (done 状态) ──
    avg_row = d1_first(cf_account, cf_d1, cf_token,
        """SELECT AVG(
          (julianday(finished_at) - julianday(started_at)) * 86400
        ) as avg_sec FROM synth_jobs
        WHERE status='done' AND finished_at > datetime('now', '-1 day')""")
    avg_sec = round(avg_row.get("avg_sec", 0) or 0, 1) if avg_row else 0

    # ── 4. 累计成本 ──
    cost_row = d1_first(cf_account, cf_d1, cf_token,
        "SELECT ROUND(SUM(cost_cny), 2) as total_cost_cny FROM synth_jobs WHERE status='done'")
    total_cost = cost_row.get("total_cost_cny", 0) if cost_row else 0

    # ── 5. 最近 5 条 dead (巡检重点) ──
    recent_dead = d1_all(cf_account, cf_d1, cf_token,
        """SELECT run_id, title, slug, error, finished_at
        FROM synth_jobs WHERE status='dead'
        ORDER BY finished_at DESC LIMIT 5""")

    # ── 6. 异常告警 ──
    alerts = []
    if fail_pct > args.alert_threshold_fail_pct:
        alerts.append(f"⚠️ 24h 失败率 {fail_pct:.1f}% > {args.alert_threshold_fail_pct}%")
    if queue_depth > args.alert_threshold_queue:
        alerts.append(f"⚠️ 队列深度 {queue_depth} > {args.alert_threshold_queue}")
    if avg_sec > args.alert_threshold_avg_sec:
        alerts.append(f"⚠️ 平均耗时 {avg_sec}s > {args.alert_threshold_avg_sec}s")
    if dead > 0:
        alerts.append(f"⚠️ {dead} 个新 dead job (见 recent_dead 列表)")

    report = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "queue_depth": queue_depth,
        "last_24h": {"done": done, "failed": failed, "dead": dead, "total": total, "fail_pct": round(fail_pct, 1)},
        "avg_completion_sec": avg_sec,
        "total_cost_cny": total_cost,
        "recent_dead": recent_dead,
        "alerts": alerts,
        "ok": len(alerts) == 0,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("━" * 60)
        print(f"📊 在线按需合成巡检 @ {report['ts']}")
        print("━" * 60)
        print(f"队列深度:         {queue_depth} (阈值 < {args.alert_threshold_queue})")
        print(f"24h done:         {done}")
        print(f"24h failed:       {failed}")
        print(f"24h dead:         {dead}")
        print(f"24h 失败率:       {fail_pct:.1f}% (阈值 < {args.alert_threshold_fail_pct}%)")
        print(f"平均完成耗时:     {avg_sec}s (阈值 < {args.alert_threshold_avg_sec}s)")
        print(f"累计成本:         ¥{total_cost}")
        print()
        if recent_dead:
            print(f"最近 {len(recent_dead)} 条 dead jobs:")
            for r in recent_dead:
                print(f"  - {r.get('title')} ({r.get('slug')}) @ {r.get('finished_at')}")
                print(f"    error: {(r.get('error') or '')[:120]}")
            print()
        if alerts:
            print("🚨 告警:")
            for a in alerts:
                print(f"  {a}")
            sys.exit(1)
        else:
            print("✅ 一切正常")


if __name__ == "__main__":
    main()