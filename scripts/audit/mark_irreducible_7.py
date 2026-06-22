#!/usr/bin/env python3
"""
B Mark Irreducible-7: 扫 data/audit_registry.json 找 current_score=7 + audit_history ≥ 4 次
加 flags += ['irreducible-7'] + tier_history + reason

Usage:
  python3 scripts/mark_irreducible_7.py --dry-run   # 看哪些会被标
  python3 scripts/mark_irreducible_7.py --apply     # 实际改 registry
"""
import json
import sys
from pathlib import Path
from collections import Counter

REGISTRY = Path("data/audit_registry.json")

MIN_AUDIT_HISTORY = 4  # 至少 4 次审计历史


def score_history(m: dict) -> list[int]:
    """Extract score list from audit_history (兼容多种格式)."""
    history = m.get("audit_history", [])
    scores = []
    for h in history:
        if isinstance(h, dict):
            s = h.get("score")
        elif isinstance(h, (int, float)):
            s = h
        else:
            s = None
        if s is not None:
            try:
                scores.append(int(s))
            except (ValueError, TypeError):
                pass
    return scores


def variance_stuck(scores: list[int], target: int = 7, window: int = 3) -> bool:
    """最近 window 次 audits 都卡在 target ±1."""
    if len(scores) < window:
        return False
    recent = scores[-window:]
    return all(abs(s - target) <= 1 for s in recent)


def main():
    dry_run = "--dry-run" in sys.argv
    apply_mode = "--apply" in sys.argv

    if not dry_run and not apply_mode:
        print("Usage: --dry-run (default) | --apply")
        dry_run = True

    with REGISTRY.open() as f:
        reg = json.load(f)

    majors = reg.get("majors", {})
    candidates = []
    skip_reasons = Counter()

    for slug, m in majors.items():
        cs = m.get("current_score")
        if cs is None or cs != 7:
            continue
        # Already flagged?
        flags = m.get("flags", [])
        if any("irreducible" in str(f).lower() for f in flags):
            skip_reasons["already_flagged"] += 1
            continue
        scores = score_history(m)
        if len(scores) < MIN_AUDIT_HISTORY:
            skip_reasons[f"history<{MIN_AUDIT_HISTORY}"] += 1
            continue
        if not variance_stuck(scores, target=7):
            skip_reasons["not_stuck"] += 1
            continue
        candidates.append(
            {
                "slug": slug,
                "title": m.get("title", ""),
                "current_score": cs,
                "audit_count": len(scores),
                "score_history": scores[-5:],
                "reason": f"7 边界 ±1 stuck ≥{MIN_AUDIT_HISTORY} 次 audit, 内容已完整",
            }
        )

    print(f"扫 {len(majors)} 篇, candidates {len(candidates)} 篇")
    print(f"Skip reasons: {dict(skip_reasons)}")
    print(f"\n样例 (前 10):")
    for c in candidates[:10]:
        print(f"  {c['slug']:40s} score={c['current_score']} audits={c['audit_count']} history={c['score_history']}")

    if dry_run:
        out_path = Path("data/irreducible_7_candidates.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
            json.dump({"candidates": candidates}, f, ensure_ascii=False, indent=2)
        print(f"\n[DRY-RUN] 加 --apply 实际改 registry")
        print(f"[DRY-RUN] Candidates → {out_path}")
        return

    # Apply
    for c in candidates:
        slug = c["slug"]
        m = majors[slug]
        flags = m.get("flags", [])
        flags.append("irreducible-7")
        m["flags"] = flags
        # tier_history 是 list, append dict
        tier_history = m.get("tier_history", [])
        if not isinstance(tier_history, list):
            tier_history = []
        tier_history.append(
            {
                "tier": "irreducible-7",
                "reason": c["reason"],
                "audit_count": c["audit_count"],
                "score_history": c["score_history"],
            }
        )
        m["tier_history"] = tier_history

    with REGISTRY.open("w") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    print(f"\n[APPLIED] {len(candidates)} 篇标 irreducible-7")


if __name__ == "__main__":
    main()