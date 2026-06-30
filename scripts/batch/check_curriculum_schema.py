#!/usr/bin/env python3
"""check_curriculum_schema.py — 校验 627 篇 major JSON 的 curriculum 子键 schema.

Schema 期望:
  curriculum.<key>: list[str] | list[dict]

常见 drift:
  - string 误写成逗号/顿号分隔的长串 → 渲染时按字符切分, 一字一行

用法:
  python3 scripts/batch/check_curriculum_schema.py             # 扫全量, 列出问题
  python3 scripts/batch/check_curriculum_schema.py --staged    # 只扫 git staged
  python3 scripts/batch/check_curriculum_schema.py --slug X    # 单篇
  python3 scripts/batch/check_curriculum_schema.py --json      # 输出 JSON 给 hook

退出码: 0 = 干净, 1 = 有 string 漂移
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"

# 这些键允许是 string (它们不是课程列表, 而是注释/元数据)
NON_LIST_KEYS = {
    "credit_hours_estimate",
    "credit_hours_note",
    "credit_requirement",
    "lab_practice",          # food/clinical 把它当 string 注释
    "evaluation",            # 评估说明
    "internship",            # 实习说明
    "typical_textbooks",     # 教材列表
}


def scan_file(json_path: Path) -> list[dict]:
    """Return list of {key, sample} for any curriculum sub-key that's a string."""
    issues = []
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return [{"error": str(e), "slug": json_path.stem}]

    curriculum = data.get("curriculum")
    if not isinstance(curriculum, dict):
        return issues

    for k, v in curriculum.items():
        if k in NON_LIST_KEYS:
            continue
        if isinstance(v, str):
            sample = v[:60] + ("…" if len(v) > 60 else "")
            issues.append({"slug": json_path.stem, "key": k, "sample": sample})

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--staged", action="store_true", help="只扫 git staged JSON")
    parser.add_argument("--slug", help="单篇 slug")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    targets: list[Path] = []

    if args.slug:
        targets = [CURATED / f"{args.slug}.json"]
    elif args.staged:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("skills/gaokao-major-explorer/data/curated/") and line.endswith(".json"):
                targets.append(ROOT / line)
    else:
        targets = sorted(CURATED.glob("*.json"))

    all_issues: list[dict] = []
    for p in targets:
        all_issues.extend(scan_file(p))

    if args.json:
        print(json.dumps({"issues": all_issues, "count": len(all_issues)}, ensure_ascii=False))
    else:
        if not all_issues:
            print(f"✅ {len(targets)} 篇全部干净 (curriculum schema 100%)")
            return 0
        print(f"❌ 发现 {len(all_issues)} 处 curriculum string drift:")
        by_slug: dict[str, list[dict]] = {}
        for issue in all_issues:
            by_slug.setdefault(issue.get("slug", "?"), []).append(issue)
        for slug, items in sorted(by_slug.items()):
            keys = ", ".join(i["key"] for i in items)
            print(f"  • {slug}: {keys}")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())