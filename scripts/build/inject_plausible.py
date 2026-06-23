#!/usr/bin/env python3
"""
inject_plausible.py — Inject Plausible Analytics into all top-level public/ pages.

What it does:
  - Adds <script defer data-domain="<DOMAIN>" src="https://plausible.io/js/script.js">
    into <head> of every public/*.html + public/m/*.html (not 616 detail pages —
    those are too numerous; Plausible auto-aggregates).
  - Adds an error reporter (window.onerror + unhandledrejection → POST /api/report)
    for client-side bug visibility.
  - Idempotent: re-runs are no-op if marker comment is present.

Usage:
    python3 scripts/build/inject_plausible.py --domain majorexplorer.com
    python3 scripts/build/inject_plausible.py --domain majorexplorer.com --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC = REPO_ROOT / "public"

PLAUSIBLE_MARKER = "<!-- BEGIN_PLAUSIBLE -->"
PLAUSIBLE_END = "<!-- END_PLAUSIBLE -->"

PLAUSIBLE_SCRIPT = (
    '<script defer data-domain="{domain}" src="https://plausible.io/js/script.js">'
    '</script>'
)

# Optional error reporter — sends to /api/report if it exists.
ERROR_REPORTER = """
<script>
(function(){
  if (!window.addEventListener) return;
  function report(kind, msg, src, ln, col, err) {
    try {
      var payload = JSON.stringify({
        kind: kind, msg: String(msg || '').slice(0, 500),
        src: src || '', line: ln || 0, col: col || 0,
        url: location.href, ua: navigator.userAgent
      });
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/report', new Blob([payload], {type: 'application/json'}));
      } else if (fetch) {
        fetch('/api/report', {method: 'POST', body: payload, keepalive: true}).catch(function(){});
      }
    } catch (e) {}
  }
  window.addEventListener('error', function(e){
    report('error', e.message, e.filename, e.lineno, e.colno, e.error);
  });
  window.addEventListener('unhandledrejection', function(e){
    var r = (e && e.reason) || {};
    report('reject', r.message || r.toString(), '', 0, 0, r);
  });
})();
</script>
""".strip()


def build_block(domain: str) -> str:
    return f"{PLAUSIBLE_MARKER}\n  {PLAUSIBLE_SCRIPT.format(domain=domain)}\n  {ERROR_REPORTER}\n  {PLAUSIBLE_END}"


def list_targets() -> list[Path]:
    """Top-level pages (PC + mobile), excludes 616 detail slugs."""
    out: list[Path] = []
    # PC top-level
    for name in (
        "index.html", "majors.html", "search.html", "wishlist.html",
        "preferences.html", "recommendations.html", "404.html",
        "disclaimer.html", "privacy.html", "terms.html",
    ):
        p = PUBLIC / name
        if p.is_file():
            out.append(p)
    # Mobile top-level
    m_dir = PUBLIC / "m"
    if m_dir.is_dir():
        for p in sorted(m_dir.glob("*.html")):
            # Skip the 586 detail pages (m/majors/*.html)
            if "/m/majors/" in str(p):
                continue
            out.append(p)
    return out


def inject(html: str, domain: str) -> tuple[str, int]:
    """Inject Plausible block. Returns (new_html, byte_delta)."""
    block = build_block(domain)
    # Strip existing if any.
    pattern = re.compile(
        r"[ \t]*\n?[ \t]*" + re.escape(PLAUSIBLE_MARKER)
        + r".*?" + re.escape(PLAUSIBLE_END),
        re.DOTALL,
    )
    cleaned = pattern.sub("", html)
    if "</head>" not in cleaned:
        raise ValueError("no </head>")
    new_html = cleaned.replace("</head>", f"\n  {block}\n</head>", 1)
    return new_html, len(new_html) - len(html)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject Plausible analytics + error reporter.",
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Plausible data-domain (e.g. 'majorexplorer.com'). "
             "Set after registering at plausible.io.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change, but don't write files.",
    )
    args = parser.parse_args()

    targets = list_targets()
    if not targets:
        print("No target files found.", file=sys.stderr)
        return 1

    injected = 0
    skipped = 0
    failed = 0
    for path in targets:
        try:
            html = path.read_text(encoding="utf-8")
            if PLAUSIBLE_MARKER in html:
                skipped += 1
                continue
            new_html, delta = inject(html, args.domain)
            if not args.dry_run:
                path.write_text(new_html, encoding="utf-8")
            injected += 1
            print(f"  {path.relative_to(PUBLIC)}: +{delta} bytes")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  {path}: FAIL — {e}", file=sys.stderr)

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"\n[{mode}] processed={len(targets)} injected={injected} "
          f"skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
