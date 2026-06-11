#!/usr/bin/env python3
"""
build_sitemap.py — One-shot sitemap generator for Major Explorer.

Scans skills/gaokao-major-explorer/data/curated/*.html (excluding *-demo.html
and manifest), and emits sitemap.xml at the project root.

Usage:
    python3 scripts/build_sitemap.py
    python3 scripts/build_sitemap.py --base-url https://example.cn --output sitemap.xml

The base URL default is https://[PLACEHOLDER_DOMAIN] — replace at deploy time.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CURATED = REPO_ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"

DEFAULT_BASE = "https://[PLACEHOLDER_DOMAIN]"

# Legal / support pages (priority 0.3) — site root paths
LEGAL_PAGES = [
    "privacy.html",
    "terms.html",
    "disclaimer.html",
]

# YYYY-MM or YYYY-MM-DD -> YYYY-MM-DD (lastmod); first-of-month for partial dates
DATE_RE = re.compile(r"^(\d{4})-(\d{2})(?:-(\d{2}))?$")


def to_iso_lastmod(raw: str | None) -> str:
    """Normalize a JSON updated_at string to ISO YYYY-MM-DD."""
    if not raw:
        return date.today().isoformat()
    m = DATE_RE.match(raw.strip())
    if not m:
        return date.today().isoformat()
    y, mo, d = m.group(1), m.group(2), m.group(3) or "01"
    return f"{y}-{mo}-{d}"


def collect_major_slugs() -> list[str]:
    """Return sorted list of curated major slugs (no demo / manifest)."""
    slugs: list[str] = []
    for p in sorted(CURATED.glob("*.html")):
        name = p.stem
        if name == "manifest" or name.endswith("-demo"):
            continue
        slugs.append(name)
    return slugs


def major_lastmod(slug: str) -> str:
    """Pull updated_at from the matching JSON if present, else today."""
    j = CURATED / f"{slug}.json"
    if j.is_file():
        try:
            with j.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return to_iso_lastmod(data.get("updated_at"))
        except (OSError, json.JSONDecodeError):
            pass
    return date.today().isoformat()


def _esc(s: str) -> str:
    """Minimal XML attribute / text escape."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_sitemap_xml(base: str) -> str:
    """Render the full sitemap.xml as a string."""
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        # 1. Homepage — priority 1.0
        "  <url>",
        f"    <loc>{_esc(base + '/')}</loc>",
        f"    <lastmod>{date.today().isoformat()}</lastmod>",
        "    <changefreq>weekly</changefreq>",
        "    <priority>1.0</priority>",
        "  </url>",
    ]

    # 2. Curated major pages — priority 0.8
    for slug in collect_major_slugs():
        loc = f"{base}/skills/gaokao-major-explorer/data/curated/{slug}.html"
        lines.extend([
            "  <url>",
            f"    <loc>{_esc(loc)}</loc>",
            f"    <lastmod>{major_lastmod(slug)}</lastmod>",
            "    <changefreq>monthly</changefreq>",
            "    <priority>0.8</priority>",
            "  </url>",
        ])

    # 3. Legal pages — priority 0.3
    for page in LEGAL_PAGES:
        loc = f"{base}/{page}"
        lines.extend([
            "  <url>",
            f"    <loc>{_esc(loc)}</loc>",
            f"    <lastmod>{date.today().isoformat()}</lastmod>",
            "    <changefreq>yearly</changefreq>",
            "    <priority>0.3</priority>",
            "  </url>",
        ])

    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Major Explorer sitemap.xml")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help="Base URL prefix (default: placeholder; replace at deploy).",
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "sitemap.xml"),
        help="Output path (default: <repo>/sitemap.xml).",
    )
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    xml = build_sitemap_xml(args.base_url)
    out.write_text(xml, encoding="utf-8")

    # Quick stats from the rendered text
    url_lines = [l for l in xml.splitlines() if l.strip() == "<url>"]
    majors = sum(1 for l in xml.splitlines() if "/curated/" in l and "<loc>" in l)
    legal = sum(
        1 for l in xml.splitlines()
        if "<loc>" in l and any(p in l for p in LEGAL_PAGES)
    )
    home = len(url_lines) - majors - legal
    print(
        f"Wrote {out} — {len(url_lines)} URLs "
        f"(home={home}, majors={majors}, legal={legal})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
