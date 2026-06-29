#!/usr/bin/env python3
"""
add_irreducible_7_flags.py — Day 44: 给 7 分 variance stuck 篇加 tier=irreducible-7.

机制: 跟 irreducible-8 一样, 但针对 7 分 stuck (audit_history 范围 4-7, variance noise
      概率 ≤20%). 后续 polish R3 误判 variance noise 容易 demote ≤6. flag 后告诉 agent
      不要重 polish.

候选标准:
- current_score == 7
- audit_count >= 5
- max(audit_history.score) <= 7 (真 stuck, 不能 promote)

用法:
  python3 scripts/audit/add_irreducible_7_flags.py --dry-run
  python3 scripts/audit/add_irreducible_7_flags.py
"""
import argparse, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / 'data' / 'audit_registry.json'

# Day 44 候选: taxation + traditional-chinese-medicine (Day 43 polish 后仍 7)
CANDIDATES = [
    "taxation",                          # 10 审 max=7
    "traditional-chinese-medicine",      # 9 审 max=7
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = json.load(open(REGISTRY, encoding='utf-8'))
    today = datetime.date.today().isoformat()

    flagged = []
    skipped = []
    for slug in CANDIDATES:
        entry = reg['majors'].get(slug)
        if not entry:
            skipped.append((slug, "missing"))
            continue
        score = entry.get('current_score')
        audit_count = entry.get('audit_count', 0)
        if score != 7:
            skipped.append((slug, f"score={score}"))
            continue
        if audit_count < 5:
            skipped.append((slug, f"audit_count={audit_count}"))
            continue
        history_scores = [a.get('score') for a in entry.get('audit_history', []) if a.get('score') is not None]
        max_score = max(history_scores) if history_scores else None
        if max_score and max_score > 7:
            skipped.append((slug, f"max={max_score} (可 promote)"))
            continue
        if entry.get('tier') == 'irreducible-7':
            skipped.append((slug, "already flagged"))
            continue
        # 写入
        entry['tier'] = 'irreducible-7'
        entry['irreducible_reason'] = (
            f"{audit_count} 审仍 {score} 分, "
            f"audit_history max={max_score}, variance stuck 7, "
            f"variance noise 概率 ≤20%"
        )
        entry['irreducible_since'] = today
        flagged.append((slug, audit_count, score, max_score))

    print(f"=== irreducible-7 flag {'DRY RUN' if args.dry_run else 'WRITE'} ===")
    print(f"待 flag: {len(flagged)} 篇")
    for slug, cnt, score, mx in flagged:
        print(f"  ✓ {slug}: {cnt} 审 / {score} 分 / max={mx}")
    print(f"\n跳过: {len(skipped)} 篇")
    for slug, reason in skipped:
        print(f"  - {slug}: {reason}")

    if args.dry_run:
        print("\nDRY-RUN: 没改 registry")
        return

    if flagged:
        reg['updated_at'] = datetime.datetime.now().isoformat()
        json.dump(reg, open(REGISTRY, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        print(f"\n✅ 已写入 {len(flagged)} 篇 → {REGISTRY}")


if __name__ == '__main__':
    main()