#!/usr/bin/env python3
"""
inject_aggregates_meta.py — 把 aggregates.json 的数字直接写入 HTML 的 meta description / og:description

理由: SEO 爬虫 (Google/Bing) 不执行 JS, meta description 必须是 build-time 注入的静态 HTML.
     runtime JS 注入 (aggregates.json → DOM) 是兜底, build-time 是主路径.

幂等: 已有 placeholder `<!-- AGGREGATES_META_DESCRIPTION: ... -->` 替换.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGG = ROOT / "public" / "data" / "aggregates.json"
MAJORS_HTML = ROOT / "public" / "majors.html"
INDEX_HTML = ROOT / "public" / "index.html"


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace('"', "&quot;")
              .replace("<", "&lt;").replace(">", "&gt;"))


def inject_meta(html_path: Path, desc: str, lead_short: str) -> int:
    """替换 meta name=description 和 og:description + 替换 AGGREGATES_LEDE placeholder. 返改动行数."""
    if not html_path.exists():
        return 0
    text = html_path.read_text(encoding="utf-8")
    n = 0

    # 1. <meta name="description" content="...">
    new = re.sub(
        r'(<meta\s+name="description"\s+content=")[^"]*(")',
        lambda m: m.group(1) + escape_html(desc) + m.group(2),
        text, count=1,
    )
    if new != text:
        n += 1
        text = new

    # 2. <meta property="og:description" content="...">
    new = re.sub(
        r'(<meta\s+property="og:description"\s+content=")[^"]*(")',
        lambda m: m.group(1) + escape_html(desc) + m.group(2),
        text, count=1,
    )
    if new != text:
        n += 1
        text = new

    # 3. AGGREGATES_LEDE placeholder (HTML 注释 + 紧跟 <p>...</p>)
    if "<!-- AGGREGATES_LEDE" in text:
        new = text.replace(
            "<!-- AGGREGATES_LEDE: build_aggregates.py 注入, runtime 不要改 -->",
            f'<!-- AGGREGATES_LEDE: build_aggregates.py 注入 ({len(lead_short)} chars) -->',
        )
        # 把 <p class="lede">...</p> 替换为新的 (lead 已经是 HTML)
        new = re.sub(
            r'(<p\s+class="lede"\s+id="agg-lede">)[\s\S]*?(</p>)',
            lambda m: m.group(1) + "\n        " + lead_short + "\n      " + m.group(2),
            new, count=1,
        )
        if new != text:
            n += 1
            text = new

    if n > 0:
        html_path.write_text(text, encoding="utf-8")
        print(f"✅ {html_path.relative_to(ROOT)}: {n} 处替换")
    else:
        print(f"⏭️  {html_path.relative_to(ROOT)}: 无 placeholder, skip")
    return n


def build_lead(totals: dict) -> str:
    """构造 majors.html 的 lede 段落 HTML (短版, 用于 runtime fallback)."""
    return (
        f'《普通高等学校本科专业目录》全量 2 层结构 —— '
        f'<strong>{totals["menjia_count"]} 个学科门类</strong> · '
        f'<strong>{totals["subclass_count"]} 个专业类</strong> · '
        f'<strong>约 {totals["major_count"]} 种本科专业</strong> '
        f'(2026 年新增 {totals["new_2026"]} 种)。'
        f'我们已为 <strong style="color: #B8323A;" id="js-curated-count">'
        f'{totals["curated_count"]}+ 个</strong> 主流专业写了深度精品报告 '
        f'(✦ 标记可点开); 其余专业附 '
        f'<strong style="color: #C99A2A;">阳光高考官方满意度评分</strong> '
        f'({totals["chsi_rated_count"]} 个有评分)。'
    )


def main():
    if not AGG.exists():
        sys.exit(f"❌ {AGG} 不存在, 先跑 build_aggregates.py")
    agg = json.loads(AGG.read_text(encoding="utf-8"))
    t = agg["totals"]
    desc = agg["human"]["meta_description"]
    lead = build_lead(t)
    print(f"  totals: menjia={t['menjia_count']} subclass={t['subclass_count']} "
          f"major={t['major_count']} curated={t['curated_count']} "
          f"coverage={t['coverage_pct']}%\n")
    n1 = inject_meta(MAJORS_HTML, desc, lead)
    # index.html 不需要 lede 替换 (它有 sub-lede), 只换 meta description
    n2 = inject_meta(INDEX_HTML, desc, "")
    # n1+n2 == 0 算成功 (idempotent, 占位符已被替换是预期状态)
    if (n1 + n2) == 0:
        print("  ⏭️  占位符已被替换过, 幂等通过")
    return 0


if __name__ == "__main__":
    main()
