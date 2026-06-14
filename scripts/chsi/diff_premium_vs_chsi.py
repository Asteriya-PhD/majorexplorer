"""Step 3.2: chsi vs 精品 (v2 LLM-rewritten) 对照报告.

For 71 精品 majors (manifest.json), compare:
  - 精品 v2 内容 (curriculum / career / training_goal / overview_v2)
  - chsi 详情 (introduction / opening_schools / career_directions / graduate_directions / similar_majors)

Output:
  - docs/chsi-premium-diff-report.md: human-readable table
  - data/raw/chsi_premium_diff.json: machine-readable (per-major diff)

Inputs:
  - public/data/manifest.json (71 精品, 含 slug)
  - public/data/{slug}.html (精品 HTML, 含 v2 LLM 重写)
  - data/raw/major_detail/{spec_id}.json (chsi 详情)

Usage: python3 scripts/chsi/diff_premium_vs_chsi.py

Plan: §2 Step 3.2 (1h).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC_DATA = ROOT / "public" / "data"
PUBLIC_HTML = ROOT / "public"
RAW_DIR = ROOT / "data" / "raw"

OUT_JSON = RAW_DIR / "chsi_premium_diff.json"
OUT_MD = ROOT / "docs" / "chsi-premium-diff-report.md"


def _html_to_text(html: str) -> str:
    """Strip HTML tags + entities."""
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_section(text: str, keys: list[str]) -> str | None:
    """Pull a section by heading keywords. 精品 HTML uses doubled label like '就业方向 就业方向'."""
    for key in keys:
        # Match: <key> <key> <content until next section>
        m = re.search(rf"{key}\s+{key}\s+(.{{20,400}}?)(?=\s+(?:主要科目|主干课程|培养目标|就业方向|就业|相近专业|考研方向|主要课程|专业简介|课程|就业去向|毕业|就业前景))", text)
        if m:
            return m.group(1).strip()[:200]
        # Fallback: just <key> followed by colon or space + content
        m = re.search(rf"{key}\s*[：:]?\s*(.{{20,300}}?)(?=\s*(?:主要科目|主干课程|培养目标|就业方向|相近专业|考研方向|主要课程|专业简介|课程|毕业))", text)
        if m:
            return m.group(1).strip()[:200]
    return None


def _load_premium(slug: str) -> dict:
    """Load 精品 HTML + extract v2 fields."""
    f = PUBLIC_HTML / f"{slug}.html"
    if not f.exists():
        return {}
    html = f.read_text(encoding="utf-8")
    text = _html_to_text(html)
    # Find JSON-LD or data section
    out = {"has_v2": False, "intro_excerpt": "", "career_excerpt": "", "curriculum_excerpt": ""}
    # Look for "主要科目" / "主干课程" / "培养目标" / "就业方向" sections
    out["career_excerpt"] = _extract_section(text, ["就业方向", "就业"]) or ""
    out["curriculum_excerpt"] = _extract_section(text, ["主要科目", "主干课程"]) or ""
    out["intro_excerpt"] = text[:200]
    if out["career_excerpt"] or out["curriculum_excerpt"]:
        out["has_v2"] = True
    return out


def _load_chsi(name: str) -> dict | None:
    """Load chsi detail by major name."""
    # Match major name to spec_id via majors_list
    f = PUBLIC_DATA / "majors_list.json"  # not exists; check chsi_majors.json
    list_f = RAW_DIR / "majors_list.json"
    if not list_f.exists():
        return None
    majors = json.loads(list_f.read_text(encoding="utf-8"))
    found = next((m for m in majors if m.get("name") == name), None)
    if not found or not found.get("spec_id"):
        return None
    spec_id = found["spec_id"]
    detail_f = RAW_DIR / "major_detail" / f"{spec_id}.json"
    if not detail_f.exists():
        return {"spec_id": spec_id, "name": name, "missing": True}
    return json.loads(detail_f.read_text(encoding="utf-8"))


def _diff_pair(premium: dict, chsi: dict) -> dict:
    """Compare one 精品 vs chsi pair. Returns structured diff."""
    out = {
        "has_premium_v2": premium.get("has_v2", False),
        "has_chsi": bool(chsi and not chsi.get("missing")),
        "chsi_missing": bool(chsi and chsi.get("missing")),
    }
    if not chsi or chsi.get("missing"):
        return out
    # Compare career fields
    premium_career = (premium.get("career_excerpt") or "").strip()
    chsi_careers = chsi.get("career_directions") or []
    chsi_career_str = ", ".join(c.get("name", "") for c in chsi_careers if isinstance(c, dict)) if isinstance(chsi_careers, list) else ""
    out["premium_career"] = premium_career[:100]
    out["chsi_career"] = chsi_career_str[:100]
    # Compare intro
    out["chsi_intro_len"] = len(chsi.get("introduction") or "")
    out["chsi_schools"] = len(chsi.get("opening_schools") or [])
    out["chsi_grad_directions"] = len(chsi.get("graduate_directions") or [])
    out["chsi_similar_majors"] = chsi.get("similar_majors") or []
    return out


def main():
    manifest = json.loads((PUBLIC_DATA / "manifest.json").read_text(encoding="utf-8"))
    majors = manifest.get("majors") or []
    print(f"=== chsi vs 精品 diff ({len(majors)} 精品) ===", flush=True)

    diffs = []
    has_chsi = 0
    has_v2 = 0
    matched = 0
    for m in majors:
        slug = m.get("slug")
        name = m.get("title") or m.get("name")
        premium = _load_premium(slug or "")
        chsi = _load_chsi(name or "")
        diff = _diff_pair(premium, premium and chsi)
        diff["slug"] = slug
        diff["title"] = name
        if diff["has_premium_v2"]: has_v2 += 1
        if diff["has_chsi"]: has_chsi += 1
        if diff["has_chsi"] and diff["has_premium_v2"]: matched += 1
        diffs.append(diff)
        if len(diffs) % 10 == 0:
            print(f"  {len(diffs)}/{len(majors)}...", flush=True)

    OUT_JSON.write_text(json.dumps(diffs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Total 精品: {len(majors)}")
    print(f"  精品 has_v2: {has_v2}")
    print(f"  chsi has detail: {has_chsi}")
    print(f"  matched (both): {matched}")

    # Build MD report
    md_lines = [
        "# chsi vs 精品 (v2) 对照报告 (Step 3.2)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**精品总数**: {len(majors)}",
        f"**精品 has_v2 字段**: {has_v2}",
        f"**chsi 详情可用**: {has_chsi}",
        f"**两边都有**: {matched}",
        "",
        "## 摘要",
        "",
        f"- {len(majors) - has_chsi} 精品 chsi 没抓到 (bg 跑中, 后续会补)",
        f"- {has_chsi} 精品 chsi 抓到, 后续人审可对照",
        "",
        "## Per-major diff (matched 前 30)",
        "",
        "| 精品 | 精品 就业方向 | chsi 就业 | chsi 开设院校数 | chsi 考研方向数 |",
        "|---|---|---|---|---|",
    ]
    for d in diffs:
        if not d["has_chsi"]: continue
        p = (d.get("premium_career") or "")[:30] or "—"
        c = (d.get("chsi_career") or "")[:30] or "—"
        ns = d.get("chsi_schools", 0)
        ng = d.get("chsi_grad_directions", 0)
        md_lines.append(f"| {d['title']} | {p} | {c} | {ns} | {ng} |")
    md_lines.append("\n## 用途")
    md_lines.append("")
    md_lines.append("- 后续人工增补/校准精品 v2 内容, 让精品跟 chsi 官方数据对齐")
    md_lines.append("- 重点关注 chsi_schools 数: 少于 5 个的精品可能漏了主开院校")
    md_lines.append("- chsi career 列表可补充精品 就业方向 字段")
    md_lines.append("")
    md_lines.append(f"Plan: §2 Step 3.2")
    md_lines.append(f"\nJSON: {OUT_JSON.relative_to(ROOT)}")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"  → {OUT_JSON.relative_to(ROOT)}")
    print(f"  → {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()