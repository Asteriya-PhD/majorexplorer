#!/usr/bin/env python3
"""
inject_og.py — Inject Open Graph (og:image, og:type, og:site_name) tags into
curated HTML pages.

This is the standalone OG-tag injector. The combined script
`inject_jsonld.py` does the same thing together with JSON-LD + canonical;
this file is a focused, minimal entry point for OG-only edits.

Behavior:
  - Scans skills/gaokao-major-explorer/data/curated/*.html (excludes *-demo,
    manifest).
  - If an og:image tag is already present, the page is SKIPPED.
  - Otherwise, inserts the OG block just before </head>.
  - Backs up the original to <file>.bak the first time (unless --no-backup).
  - Idempotent on re-run (skips already-injected pages).

Usage:
    python3 scripts/inject_og.py
    python3 scripts/inject_og.py --slug accounting --dry-run
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from html import escape as _esc
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED = REPO_ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"

DEFAULT_BASE = "https://[PLACEHOLDER_DOMAIN]"
OG_MARKER = "<!-- BEGIN_SEO_OG -->"

OG_TEMPLATE = (
    '{marker}'
    '<meta property="og:image" content="{img}">'
    '<meta property="og:image:width" content="1200">'
    '<meta property="og:image:height" content="630">'
    '<meta property="og:type" content="article">'
    '<meta property="og:site_name" content="Major Explorer">'
)


def list_targets() -> list[Path]:
    return sorted(
        p for p in CURATED.glob("*.html")
        if not p.stem.endswith("-demo") and p.stem != "manifest"
    )


def already_has_og(html: str) -> bool:
    """Skip if og:image is already present (with or without our marker)."""
    if OG_MARKER in html:
        return True
    if re.search(r'<meta\s+property="og:image"', html, re.IGNORECASE):
        return True
    return False


def inject(html: str, og_image: str) -> str:
    # Strip our own prior injection (include leading whitespace to keep idempotent).
    html = re.sub(
        r"[ \t]*\n?[ \t]*" + re.escape(OG_MARKER) + r".*?(?=</head>)",
        "",
        html,
        flags=re.DOTALL,
    )
    block = "\n  " + OG_TEMPLATE.format(marker=OG_MARKER, img=_esc(og_image)) + "\n"
    if "</head>" not in html:
        raise ValueError("no </head> tag found")
    return html.replace("</head>", f"{block}</head>", 1)


def process(html_path: Path, *, dry_run: bool, backup: bool, og_image: str) -> str:
    """Return one of: 'injected', 'skipped', 'failed'."""
    html = html_path.read_text(encoding="utf-8")
    if already_has_og(html):
        return "skipped"
    new_html = inject(html, og_image)
    if new_html == html:
        return "skipped"
    if backup and not dry_run:
        bak = html_path.with_suffix(html_path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(html_path, bak)
    if not dry_run:
        html_path.write_text(new_html, encoding="utf-8")
    return "injected"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject og:image / og:type into curated HTML pages.")
    parser.add_argument("--slug", help="Process only this slug.")
    parser.add_argument("--no-backup", action="store_true", help="Skip writing .bak files.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write.")
    parser.add_argument(
        "--og-image",
        default=f"{DEFAULT_BASE}/assets/og-default.png",
        help="og:image URL (default: https://[PLACEHOLDER_DOMAIN]/assets/og-default.png).",
    )
    args = parser.parse_args()

    targets = list_targets()
    if args.slug:
        targets = [p for p in targets if p.stem == args.slug]
    if not targets:
        print("No target files matched.", file=sys.stderr)
        return 1

    counts = {"injected": 0, "skipped": 0, "failed": 0}
    for p in targets:
        try:
            counts[process(p, dry_run=args.dry_run, backup=not args.no_backup, og_image=args.og_image)] += 1
        except Exception as e:  # noqa: BLE001
            counts["failed"] += 1
            print(f"  {p.name}: FAIL — {e}", file=sys.stderr)

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(
        f"\n[{mode}] processed={len(targets)} "
        f"injected={counts['injected']} "
        f"skipped={counts['skipped']} "
        f"failed={counts['failed']}"
    )
    return 0 if counts["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
