#!/usr/bin/env python3
"""
claim.py — 防止 30 篇新任务串领

本地用 (gitignore), 不 git tracked. 1 人项目, 简化版.

用法:
  # 领任务 (新批次启动时)
  python3 scripts/claim.py --agent day5-A --slugs chinese-language applied-chinese ...

  # 看谁领了什么
  python3 scripts/claim.py --list

  # 检查冲突 (多个 agent 启跑前, 或 --check-conflict)
  python3 scripts/claim.py --check-conflict

  # 释放 (完工或取消)
  python3 scripts/claim.py --release day5-A           # 释放该 agent 全部
  python3 scripts/claim.py --release-slug chinese-language  # 释放单个

  # 清理过期 (>24h 自动失效)
  python3 scripts/claim.py --cleanup
"""
import argparse, json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMED = ROOT / "data" / "claimed.json"

# 24h 自动失效
EXPIRE_HOURS = 24


def load():
    if CLAIMED.exists():
        return json.load(open(CLAIMED))
    return {"version": "1.0", "claims": {}}


def save(data):
    data["updated_at"] = datetime.datetime.now().isoformat()
    CLAIMED.parent.mkdir(parents=True, exist_ok=True)
    CLAIMED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_claim(agent, slugs, task="unspecified"):
    data = load()
    now = datetime.datetime.now().isoformat()
    added = []
    skipped = []
    for slug in slugs:
        # 检查是否已被领
        existing = data["claims"].get(slug)
        if existing and existing.get("claimed_by") != agent:
            age = datetime.datetime.now() - datetime.datetime.fromisoformat(existing["claimed_at"])
            if age.total_seconds() < EXPIRE_HOURS * 3600:
                skipped.append(f"  ❌ {slug}: 被 {existing['claimed_by']} 领 ({age.total_seconds()/3600:.1f}h 前)")
                continue
        # claim
        data["claims"][slug] = {
            "claimed_by": agent,
            "claimed_at": now,
            "task": task,
        }
        added.append(slug)
    save(data)
    print(f"✅ Agent '{agent}' claim {len(added)} 个:")
    for s in added:
        print(f"  + {s}")
    if skipped:
        print(f"\n⚠️  跳过 {len(skipped)} 个 (被其他 agent 领):")
        for s in skipped:
            print(s)


def cmd_list():
    data = load()
    if not data["claims"]:
        print("✅ 无 claim")
        return
    by_agent = {}
    for slug, c in data["claims"].items():
        by_agent.setdefault(c["claimed_by"], []).append((slug, c))
    print(f"=== Claims ({len(data['claims'])} total) ===")
    for agent, claims in sorted(by_agent.items()):
        print(f"\n{agent} ({len(claims)}):")
        for slug, c in claims:
            print(f"  - {slug}  ({c['task']}, {c['claimed_at']})")


def cmd_release(agent):
    data = load()
    to_remove = [s for s, c in data["claims"].items() if c["claimed_by"] == agent]
    if not to_remove:
        print(f"⚠️  Agent '{agent}' 无 claim")
        return
    for s in to_remove:
        del data["claims"][s]
    save(data)
    print(f"✅ 释放 agent '{agent}' 的 {len(to_remove)} 个 claim")


def cmd_release_slug(slug):
    data = load()
    if slug not in data["claims"]:
        print(f"⚠️  {slug} 未被 claim")
        return
    del data["claims"][slug]
    save(data)
    print(f"✅ 释放 {slug}")


def cmd_check_conflict():
    data = load()
    if not data["claims"]:
        print("✅ 无冲突 (无 claim)")
        return 0
    # 检查过期
    now = datetime.datetime.now()
    expired = []
    for slug, c in list(data["claims"].items()):
        age = now - datetime.datetime.fromisoformat(c["claimed_at"])
        if age.total_seconds() > EXPIRE_HOURS * 3600:
            expired.append(slug)
    if expired:
        print(f"⚠️  {len(expired)} 个 claim 已过期 (>24h), 跑 --cleanup 自动清理")
    print(f"当前 {len(data['claims'])} 个 claim, {len(set(c['claimed_by'] for c in data['claims'].values()))} 个 agent")
    return 0


def cmd_cleanup():
    data = load()
    now = datetime.datetime.now()
    expired = []
    for slug, c in list(data["claims"].items()):
        age = now - datetime.datetime.fromisoformat(c["claimed_at"])
        if age.total_seconds() > EXPIRE_HOURS * 3600:
            expired.append(slug)
    for s in expired:
        del data["claims"][s]
    save(data)
    print(f"🗑️  清理 {len(expired)} 个过期 claim (>24h)")
    for s in expired:
        print(f"  - {s}")


def main():
    ap = argparse.ArgumentParser(description="claim 管理 (防串领)", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--agent", help="agent 名 (e.g. day5-A)")
    ap.add_argument("--slugs", nargs="*", help="要 claim 的 slug 列表")
    ap.add_argument("--task", default="unspecified", help="任务描述 (e.g. 'Day 5 30 篇')")
    ap.add_argument("--list", action="store_true", help="列出所有 claim")
    ap.add_argument("--release", help="释放指定 agent 全部 claim")
    ap.add_argument("--release-slug", help="释放单个 slug")
    ap.add_argument("--check-conflict", action="store_true", help="检查冲突 + 过期")
    ap.add_argument("--cleanup", action="store_true", help="清理过期 (>24h)")
    args = ap.parse_args()

    if args.list:
        cmd_list()
    elif args.release:
        cmd_release(args.release)
    elif args.release_slug:
        cmd_release_slug(args.release_slug)
    elif args.cleanup:
        cmd_cleanup()
    elif args.check_conflict:
        sys.exit(cmd_check_conflict())
    elif args.agent and args.slugs:
        cmd_claim(args.agent, args.slugs, args.task)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
