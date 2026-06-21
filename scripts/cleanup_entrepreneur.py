#!/usr/bin/env python3
"""
A.1 Cleanup: 扫 employment_direction / deep_study 找 自主创业/其他 占位
按 slug.style 映射到具体路径 (Day 8.5 老坑)

Usage:
  python3 scripts/cleanup_entrepreneur.py           # dry-run → report
  python3 scripts/cleanup_entrepreneur.py --apply    # 实际改 JSON
  python3 scripts/cleanup_entrepreneur.py --slug=X   # 单篇
"""
import json
import sys
from pathlib import Path
from collections import Counter

CURATED = Path("skills/gaokao-major-explorer/data/curated")
REPORT_PATH = Path("data/cleanup_entrepreneur_report.json")

ENTREPRENEUR_MAP = {
    "agri": "自主创业 (家庭农场/合作社/农资经销)",
    "arts": "自由职业 (画廊签约/独立工作室)",
    "finance": "自主创业 (私募/咨询/家族办公室)",
    "cs": "自主创业 (AI 创业/SaaS/外包)",
    "medicine": "自主创业 (私人诊所/医美机构)",
    "eng": "自主创业 (工程咨询/技术服务)",
    "law": "自主创业 (律所合伙人/法律科技)",
    "humanities": "自主创业 (翻译公司/文化传媒)",
    "administration": "自主创业 (管理咨询/猎头)",
    "gongan": "考公 (公安联考入警, 不算创业)",
    "safety": "自主创业 (EHS 咨询/安全评价)",
    "sci": "自主创业 (科研服务/数据分析)",
}

GENERIC_PATTERNS = ["自主创业", "其他", "其他灵活就业", "灵活就业"]


def is_placeholder(name: str) -> bool:
    s = str(name or "").strip()
    if not s:
        return True
    return s in ("自主创业", "其他", "其他灵活就业", "灵活就业")


def scan_one(path: Path) -> list[dict]:
    """Return list of {section, key, old_name, style} for each placeholder hit."""
    try:
        with path.open() as f:
            data = json.load(f)
    except Exception:
        return []

    style = data.get("style", "")
    hits = []
    for section in ("employment_direction", "deep_study"):
        d = data.get(section)
        if not isinstance(d, dict):
            continue
        for key, items in d.items():
            if not isinstance(items, list):
                continue
            for idx, it in enumerate(items):
                if not isinstance(it, dict):
                    continue
                name = it.get("name") or it.get("path") or it.get("direction") or ""
                if is_placeholder(name):
                    hits.append(
                        {
                            "section": section,
                            "key": key,
                            "idx": idx,
                            "old_name": str(name),
                            "style": style,
                            "new_name": ENTREPRENEUR_MAP.get(
                                style, "自主创业 (具体路径待补)"
                            ),
                        }
                    )
    return hits


def main():
    apply_mode = "--apply" in sys.argv
    single_slug = None
    for arg in sys.argv[1:]:
        if arg.startswith("--slug="):
            single_slug = arg.split("=", 1)[1]

    files = sorted(CURATED.glob("*.json"))
    if single_slug:
        files = [f for f in files if f.stem == single_slug]

    all_hits = []
    for f in files:
        h = scan_one(f)
        for hit in h:
            hit["slug"] = f.stem
        all_hits.extend(h)

    style_counter = Counter(h["style"] for h in all_hits)
    section_counter = Counter(h["section"] for h in all_hits)

    print(f"扫 {len(files)} 篇, 占位 {len(all_hits)} 处")
    print(f"By style: {dict(style_counter)}")
    print(f"By section: {dict(section_counter)}")
    print(f"\n样例 (前 10):")
    for h in all_hits[:10]:
        print(
            f"  {h['slug']:40s} {h['section']:20s} {h['key']:15s} '{h['old_name']}' → '{h['new_name']}'"
        )

    if not apply_mode:
        print(f"\n[DRY-RUN] 加 --apply 实际改")
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with REPORT_PATH.open("w") as f:
            json.dump(
                {
                    "total_files": len(files),
                    "total_hits": len(all_hits),
                    "by_style": dict(style_counter),
                    "by_section": dict(section_counter),
                    "hits": all_hits,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"[DRY-RUN] Report → {REPORT_PATH}")
        return

    # Apply
    changed_files = set()
    for f in files:
        with f.open() as fp:
            data = json.load(fp)
        hits = scan_one(f)
        if not hits:
            continue
        style = data.get("style", "")
        new_name = ENTREPRENEUR_MAP.get(style, "自主创业 (具体路径待补)")
        for h in hits:
            section = h["section"]
            items = data[section][h["key"]]
            items[h["idx"]]["name"] = new_name
        with f.open("w") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        changed_files.add(f.stem)
    print(f"\n[APPLIED] 改 {len(changed_files)} 篇")


if __name__ == "__main__":
    main()