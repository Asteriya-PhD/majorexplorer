#!/usr/bin/env python3
"""
inject_twitter_card.py — Inject Twitter Card meta tags into deployed HTML pages.

For each public/*.html + public/m/*.html + public/m/majors/*.html, this script:

  1. Reads existing og:title / og:description / og:image from the page.
  2. Builds 4 Twitter Card meta tags:
        - twitter:card        = "summary_large_image"
        - twitter:title       (reuses og:title)
        - twitter:description (reuses og:description)
        - twitter:image       (reuses og:image)
  3. Inserts / replaces them as a fenced block right before </head>.
  4. Idempotent: re-running strips the old block and rewrites it.

Reuses existing og: meta where present, so we don't have to maintain a separate
data source. Falls back gracefully if og:title/description/image is missing
(skips that page rather than injecting empty tags).

Usage:
    python3 scripts/build/inject_twitter_card.py [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from html import escape as _esc
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC = REPO_ROOT / "public"

# Markers — HTML comments fence the injected block for idempotency.
TWITTER_START = "<!-- BEGIN_SEO_TWITTER -->"
TWITTER_END = "<!-- END_SEO_TWITTER -->"

# Pattern to extract og: meta values from existing head.
OG_TITLE_RE = re.compile(
    r'<meta\s+property="og:title"\s+content="([^"]+)"',
    re.IGNORECASE,
)
OG_DESC_RE = re.compile(
    r'<meta\s+property="og:description"\s+content="([^"]+)"',
    re.IGNORECASE,
)
OG_IMAGE_RE = re.compile(
    r'<meta\s+property="og:image"\s+content="([^"]+)"',
    re.IGNORECASE,
)


def list_target_htmls() -> list[Path]:
    """Scan public PC + mobile top-level + mobile majors."""
    targets: list[Path] = []
    # PC: public/*.html (top-level + majors flat)
    targets.extend(sorted(p for p in PUBLIC.glob("*.html") if not p.stem.endswith("-demo")))
    # Mobile top-level: public/m/*.html (excludes _template.html etc.)
    targets.extend(
        sorted(p for p in (PUBLIC / "m").glob("*.html") if p.stem not in {"_template", "sw"})
    )
    # Mobile majors: public/m/majors/*.html
    targets.extend(
        sorted(p for p in (PUBLIC / "m" / "majors").glob("*.html") if p.stem != "_template")
    )
    return targets


def build_twitter_block(og_title: str, og_desc: str, og_image: str) -> str:
    """Build a fenced HTML block with 4 Twitter Card meta tags."""
    tags = (
        f'<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{_esc(og_title)}">'
        f'<meta name="twitter:description" content="{_esc(og_desc)}">'
        f'<meta name="twitter:image" content="{_esc(og_image)}">'
    )
    return f"{TWITTER_START}\n  {tags}\n  {TWITTER_END}"


def inject_into_html(html: str) -> str | None:
    """Strip old twitter block, insert new one. Returns None if missing required og: meta."""
    og_title_m = OG_TITLE_RE.search(html)
    og_desc_m = OG_DESC_RE.search(html)
    og_image_m = OG_IMAGE_RE.search(html)
    if not (og_title_m and og_desc_m and og_image_m):
        return None  # skip page without required og: meta

    block = build_twitter_block(
        og_title_m.group(1),
        og_desc_m.group(1),
        og_image_m.group(1),
    )

    # Strip old block (idempotent).
    strip_re = re.compile(
        r"[ \t]*\n?[ \t]*" + re.escape(TWITTER_START) + r".*?" + re.escape(TWITTER_END),
        re.DOTALL,
    )
    cleaned = strip_re.sub("", html)

    # Insert before </head>.
    if "</head>" not in cleaned:
        return None
    return cleaned.replace("</head>", f"\n  {block}\n  </head>", 1)


def process_file(html_path: Path, *, dry_run: bool, backup: bool) -> tuple[str, bool, int]:
    """Return (slug, injected?, byte_delta)."""
    slug = html_path.name
    html = html_path.read_text(encoding="utf-8")
    new_html = inject_into_html(html)
    if new_html is None or new_html == html:
        return slug, False, 0
    if backup and not dry_run:
        bak = html_path.with_suffix(html_path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(html_path, bak)
    if not dry_run:
        html_path.write_text(new_html, encoding="utf-8")
    return slug, True, len(new_html) - len(html)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject Twitter Card meta tags.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only.")
    parser.add_argument("--no-backup", action="store_true", help="Skip .bak files.")
    args = parser.parse_args()

    targets = list_target_htmls()
    if not targets:
        print("No target HTML files found.", file=sys.stderr)
        return 1

    injected = 0
    skipped = 0
    failed = 0
    for p in targets:
        try:
            slug, did, delta = process_file(
                p, dry_run=args.dry_run, backup=not args.no_backup
            )
            if did:
                injected += 1
                if args.dry_run:
                    print(f"  {slug}: +{delta} bytes")
            else:
                skipped += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  {p.name}: FAIL — {e}", file=sys.stderr)

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"\n[{mode}] processed={len(targets)} injected={injected} "
          f"skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())