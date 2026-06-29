#!/usr/bin/env python3
"""
add_irreducible_8_flags.py — Phase 3 Day 43: 给 20 篇 ≥10 审仍 7-8 分篇加 tier=irreducible-8.

为什么: 这些篇 audit_history 范围 5-9, R1→R10+ 多次验证, variance stuck 在 7-8.
      后续 polish R3 误判 variance noise 容易 demote 回 7. flag 后告诉 agent 不要重 audit.

机制:
  registry.majors[slug] 加字段:
    tier: "irreducible-8"
    irreducible_reason: "≥10 审仍 7-8, variance noise 概率 ≤20%"
    irreducible_since: ISO 日期

用法:
  python3 scripts/audit/add_irreducible_8_flags.py --dry-run  # 看候选
  python3 scripts/audit/add_irreducible_8_flags.py            # 写 registry
"""
import argparse, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / 'data' / 'audit_registry.json'

# 20 篇 irreducible-8 候选 (跟 PLAN_day43.md 阶段 3 一致)
# 排除标准: max audit_history score ≥9 (说明真能 promote,不算 irreducible)
CANDIDATES = [
    "service-science-engineering",         # 20 审 max=8
    "smart-agriculture",                   # 16 审 max=8
    "global-climate-change",               # 16 审 max=8
    "bioinformatics",                      # 14 审 max=8
    "bionic-science-engineering",          # 14 审 max=8
    "advertising",                         # 14 审 max=8
    "ndebele",                             # 14 审 max=8
    "criminal-investigation",              # 14 审 max=8
    "cross-border-ecommerce",              # 13 审 max=9 ⚠️ 不标
    "cyber-information-law",               # 12 审 max=8
    "remote-sensing-science-technology",   # 12 审 max=8
    "safety-engineering",                  # 11 审 max=8
    "intelligent-marine-equipment-engineering",  # 11 审 max=9 ⚠️ 不标
    "logistics-management",                # 11 审 max=8
    "flight-vehicle-control",              # 11 审 max=8
    "international-economic-cooperation",  # 11 审 max=8
    "intelligent-vehicle-engineering",     # 10 审 max=8
    "digital-twin-technology",             # 10 审 max=8
    "postal-engineering",                  # 10 审 max=8
    "numerical-foundation-science",        # 10 审 max=8
]

EXCLUDED_MAX_9 = {
    "cross-border-ecommerce",
    "intelligent-marine-equipment-engineering",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--exclude-max-9", action="store_true", default=True,
                    help="默认排除 max=9 的篇 (可能还能 promote)")
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
        if score is None or score < 7 or score > 8:
            skipped.append((slug, f"score={score}"))
            continue
        if audit_count < 10:
            skipped.append((slug, f"audit_count={audit_count}"))
            continue
        # 检查 max history
        history_scores = [a.get('score') for a in entry.get('audit_history', []) if a.get('score') is not None]
        max_score = max(history_scores) if history_scores else None
        if args.exclude_max_9 and max_score and max_score >= 9:
            skipped.append((slug, f"max={max_score} (可 promote)"))
            continue
        # 已 flag 过跳过
        if entry.get('tier') == 'irreducible-8':
            skipped.append((slug, "already flagged"))
            continue
        # 写入
        entry['tier'] = 'irreducible-8'
        entry['irreducible_reason'] = (
            f"{audit_count} 审仍 {score} 分, "
            f"audit_history max={max_score}, variance stuck, "
            f"variance noise 概率 ≤20%"
        )
        entry['irreducible_since'] = today
        flagged.append((slug, audit_count, score, max_score))

    print(f"=== irreducible-8 flag {'DRY RUN' if args.dry_run else 'WRITE'} ===")
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
        reg['version'] = '1.1'  # schema bump: 加 tier 字段
        reg['updated_at'] = datetime.datetime.now().isoformat()
        json.dump(reg, open(REGISTRY, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        print(f"\n✅ 已写入 {len(flagged)} 篇 → {REGISTRY}")


if __name__ == '__main__':
    main()