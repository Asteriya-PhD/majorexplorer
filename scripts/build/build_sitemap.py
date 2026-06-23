#!/usr/bin/env python3
"""
build_sitemap.py — Sitemap generator for Major Explorer (production).

Reads public/data/manifest.json (single source of truth) and emits
public/sitemap.xml covering:
  - Homepage + 6 top-level pages (priority 1.0 / 0.9)
  - All 616 major detail pages (PC, /<slug>.html) — priority 0.8
  - 14 mobile top-level pages (m/...) — priority 0.5
  - 3 legal pages — priority 0.3

Replaces the v1 implementation that read skills/.../curated/ (now legacy).
Lastmod per URL is the file mtime (most accurate build-time signal).

Usage:
    python3 scripts/build/build_sitemap.py
    python3 scripts/build/build_sitemap.py --base-url https://example.com
    python3 scripts/build/build_sitemap.py --output /tmp/test.xml
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC = REPO_ROOT / "public"
MANIFEST = PUBLIC / "data" / "manifest.json"

DEFAULT_BASE = "https://majorexplorer.com"

# Top-level pages — priority 0.9
TOP_PAGES = [
    "majors.html",
    "search.html",
    "wishlist.html",
    "preferences.html",
    "recommendations.html",
]

# Mobile top-level pages — priority 0.5
MOBILE_PAGES = [
    "m/index.html",
    "m/majors.html",
    "m/search.html",
    "m/wishlist.html",
    "m/preferences.html",
    "m/recommendations.html",
]

# Legal / support pages — priority 0.3
LEGAL_PAGES = [
    "privacy.html",
    "terms.html",
    "disclaimer.html",
]


def file_mtime_iso(path: Path) -> str:
    """Return file mtime as YYYY-MM-DD; today if path is missing."""
    if not path.is_file():
        return date.today().isoformat()
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def collect_major_slugs() -> list[dict]:
    """Return [{slug, title}, ...] from public/data/manifest.json.

    Slug ordering matches manifest (MOE codes first, then alpha).
    """
    with MANIFEST.open("r", encoding="utf-8") as f:
        m = json.load(f)
    out: list[dict] = []
    for entry in m.get("majors", []):
        slug = entry.get("slug")
        if not slug:
            continue
        out.append({"slug": slug, "title": entry.get("title", slug)})
    return out


def major_lastmod(slug: str) -> str:
    """Use the detail HTML mtime (most accurate last-modified signal)."""
    html = PUBLIC / f"{slug}.html"
    return file_mtime_iso(html)


def _esc(s: str) -> str:
    """Minimal XML attribute / text escape."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _url_block(loc: str, lastmod: str, changefreq: str, priority: str) -> list[str]:
    return [
        "  <url>",
        f"    <loc>{_esc(loc)}</loc>",
        f"    <lastmod>{lastmod}</lastmod>",
        f"    <changefreq>{changefreq}</changefreq>",
        f"    <priority>{priority}</priority>",
        "  </url>",
    ]


def build_sitemap_xml(base: str) -> str:
    """Render the full sitemap.xml as a string."""
    today = date.today().isoformat()
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    # 1. Homepage — priority 1.0
    lines.extend(_url_block(f"{base}/", today, "weekly", "1.0"))

    # 2. PC top-level pages — priority 0.9
    for page in TOP_PAGES:
        loc = f"{base}/{page}"
        lines.extend(_url_block(
            loc, file_mtime_iso(PUBLIC / page), "weekly", "0.9",
        ))

    # 3. Major detail pages (PC /<slug>.html) — priority 0.8
    majors = collect_major_slugs()
    for entry in majors:
        slug = entry["slug"]
        loc = f"{base}/{slug}.html"
        lines.extend(_url_block(
            loc, major_lastmod(slug), "monthly", "0.8",
        ))

    # 4. Mobile top-level pages — priority 0.5
    for page in MOBILE_PAGES:
        loc = f"{base}/{page}"
        lines.extend(_url_block(
            loc, file_mtime_iso(PUBLIC / page), "monthly", "0.5",
        ))

    # 5. Legal / support pages — priority 0.3
    for page in LEGAL_PAGES:
        loc = f"{base}/{page}"
        lines.extend(_url_block(
            loc, file_mtime_iso(PUBLIC / page), "yearly", "0.3",
        ))

    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Major Explorer sitemap.xml")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help=f"Base URL prefix (default: {DEFAULT_BASE}).",
    )
    parser.add_argument(
        "--output",
        default=str(PUBLIC / "sitemap.xml"),
        help="Output path (default: <repo>/public/sitemap.xml).",
    )
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    xml = build_sitemap_xml(args.base_url)
    out.write_text(xml, encoding="utf-8")

    # Quick stats
    url_lines = [l for l in xml.splitlines() if l.strip() == "<url>"]
    majors_count = len(collect_major_slugs())
    legal_count = len([l for l in xml.splitlines() if "<loc>" in l and any(p in l for p in LEGAL_PAGES)])
    top_count = len([l for l in xml.splitlines() if "<loc>" in l and any(p in l for p in TOP_PAGES)])
    mobile_count = len([l for l in xml.splitlines() if "/m/" in l and "<loc>" in l])
    print(
        f"Wrote {out} — {len(url_lines)} URLs "
        f"(home=1, top={top_count}, majors={majors_count}, "
        f"mobile={mobile_count}, legal={legal_count})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
