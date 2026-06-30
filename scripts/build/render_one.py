#!/usr/bin/env python3
"""Render single major HTML from JSON using v4_styles.render module."""
import sys, json
from pathlib import Path

# Ensure package context
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "gaokao-major-explorer" / "scripts"))

from v4_styles.render import render_v4  # type: ignore

ROOT = Path(__file__).parent.parent.parent
CURATION = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
PUBLIC = ROOT / "public"

slug = sys.argv[1]
data = json.load(open(CURATION / f"{slug}.json"))
# Inject style/category from manifest if not in JSON
manifest = json.load(open(PUBLIC / "data" / "manifest.json"))
m_entry = next((m for m in manifest["majors"] if m["slug"] == slug), None)
if m_entry:
    data["style"] = data.get("style") or m_entry.get("style", "")
    data["theme_color"] = data.get("theme_color") or m_entry.get("theme_color", {})
    data["html_path"] = data.get("html_path") or m_entry.get("html_path", "")
    data["data_path"] = data.get("data_path") or m_entry.get("data_path", "")

style = data.get("style", "humanities") or "humanities"
html = render_v4(data, style)
# Day 57 fix: 写双份 (public + curated). public/ 是部署镜像, curated/ 是
# inject_jsonld / inject_og 的 source-of-truth (默认扫 curated 目录, 缺它
# 则 SEO/og 注入直接 broken, 线上缺 og:title/JSON-LD).
public_out = PUBLIC / f"{slug}.html"
curated_out = CURATION / f"{slug}.html"
public_out.write_text(html, encoding="utf-8")
curated_out.write_text(html, encoding="utf-8")
print(f"✓ rendered {slug} → public/{public_out.name} + curated/{curated_out.name} ({len(html)} bytes)")
