#!/usr/bin/env python3
"""
inject_jsonld.py — Inject SEO metadata (JSON-LD + canonical) into curated HTML pages.

For each skills/gaokao-major-explorer/data/curated/<slug>.html (excluding
*-demo.html and manifest), this script:

  1. Reads the matching <slug>.json for canonical data (title, summary, etc.).
  2. Builds three JSON-LD blocks:
        - Course           (Course + CourseInstance + provider Organization)
        - BreadcrumbList   (Home → 专业库 → {title})
        - FAQPage          (6 questions derived from pitfalls)
  3. Inserts / replaces them right before `</head>`.
  4. Inserts / replaces a <link rel="canonical"> tag inside <head>.
  5. Inserts / replaces og:image / og:type / og:site_name meta tags.

Run with --no-backup to skip writing .bak files (default: backup once).
Run with --dry-run to preview changes without writing.

Usage:
    python3 scripts/inject_jsonld.py
    python3 scripts/inject_jsonld.py --slug accounting
    python3 scripts/inject_jsonld.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from html import escape as _esc
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED = REPO_ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"

DEFAULT_BASE = "https://[PLACEHOLDER_DOMAIN]"

# Markers — we use HTML comments to fence the injected blocks so re-runs are idempotent.
JSONLD_START = "<!-- BEGIN_SEO_JSONLD -->"
JSONLD_END = "<!-- END_SEO_JSONLD -->"
CANONICAL_MARKER = "<!-- BEGIN_SEO_CANONICAL -->"
OG_MARKER = "<!-- BEGIN_SEO_OG -->"


# ---------------------------------------------------------------------------
# JSON-LD builders
# ---------------------------------------------------------------------------

def split_pitfalls(pitfalls_str: str) -> list[str]:
    """The pitfalls field is a single string with ❌ delimiters.

    Returns up to 6 cleaned statements suitable for FAQ questions.
    """
    if not pitfalls_str:
        return []
    parts = re.split(r"[❌✗×]+", pitfalls_str)
    cleaned: list[str] = []
    for p in parts:
        p = p.strip().lstrip("。,，. \n")
        if p:
            cleaned.append(p)
        if len(cleaned) >= 6:
            break
    return cleaned


def _strip_brackets(s: str) -> str:
    """Strip any leading/trailing 「」『』\"'() brackets, and remove any
    matching pair that encloses a short quoted phrase from inside."""
    s = s.strip()
    # Iteratively strip outer matching bracket pairs.
    pairs = ("「」", "『』", "()", "()", "\"\"", "''")
    changed = True
    while changed:
        changed = False
        for op, cl in pairs:
            if s.startswith(op) and s.endswith(cl) and len(s) >= 2:
                s = s[1:-1].strip()
                changed = True
    return s


def _split_myth_reality(stmt: str) -> tuple[str, str]:
    """Split a single pitfall into (myth, reality) at the first — or : delimiter.

    If no delimiter is found, the whole string is treated as the question.
    Returns a (question, answer) pair — the question is reformulated into a
    natural Chinese "是真的吗?" form so the FAQ reads as Q&A.
    """
    # Try common delimiters in priority order.
    for sep in (" — ", "—", " - ", "-", "：", ":"):
        if sep in stmt:
            head, _, tail = stmt.partition(sep)
            head = _strip_brackets(head)
            tail = tail.strip()
            if head and tail:
                return _to_question(head), tail
    # Fallback: question only.
    cleaned = _strip_brackets(stmt)
    return _to_question(cleaned), "这是常见误解, 实际请以高校官方培养方案和行业报告为准。"


def _to_question(claim: str) -> str:
    """Wrap a short claim as a natural Chinese FAQ question.

    Examples:
        "会计越老越值钱"  ->  "会计越老越值钱, 是真的吗?"
        "考过 CPA 就年薪百万"  ->  "考过 CPA 就年薪百万, 是真的吗?"
    """
    claim = claim.rstrip("。.?!?,，；;")
    return f"{claim}, 是真的吗?"


def build_faq_items(pitfalls_str: str) -> list[dict]:
    items: list[dict] = []
    for stmt in split_pitfalls(pitfalls_str):
        q, a = _split_myth_reality(stmt)
        items.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a,
            },
        })
    return items


def build_course_ld(slug: str, data: dict) -> dict:
    title = data.get("title", slug)
    summary = data.get("summary", "").strip()
    if not summary:
        summary = f"{title}专业介绍 — 选课、院校、就业与避坑指南。"
    degree = data.get("degree", "学士")
    years = data.get("duration_years", 4)
    provider_name = data.get("provider") or "Major Explorer"
    return {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": title,
        "description": summary,
        "provider": {
            "@type": "Organization",
            "name": provider_name,
            "sameAs": DEFAULT_BASE,
        },
        "hasCourseInstance": {
            "@type": "CourseInstance",
            "courseMode": "in-person",
            "duration": f"P{years}Y",
            "inLanguage": "zh-CN",
        },
        "educationalCredentialAwarded": degree,
        "inLanguage": "zh-CN",
    }


def build_breadcrumb_ld(slug: str, data: dict) -> dict:
    title = data.get("title", slug)
    base = DEFAULT_BASE
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "首页",
                "item": f"{base}/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "专业库",
                "item": f"{base}/skills/gaokao-major-explorer/data/curated/",
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": f"{base}/skills/gaokao-major-explorer/data/curated/{slug}.html",
            },
        ],
    }


def build_faq_ld(slug: str, data: dict) -> dict | None:
    items = build_faq_items(data.get("pitfalls", "") or data.get("overview_v2", {}).get("pitfalls", ""))
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": items,
    }


# ---------------------------------------------------------------------------
# HTML injection helpers
# ---------------------------------------------------------------------------

def render_jsonld_block(payloads: list[dict]) -> str:
    """Render one or more JSON-LD dicts as a single fenced <script> block."""
    inner = []
    for p in payloads:
        # json.dumps with ensure_ascii=False keeps Chinese readable;
        # </script> in any string is escaped to prevent premature tag close.
        raw = json.dumps(p, ensure_ascii=False, separators=(", ", ": "))
        safe = raw.replace("</", "<\\/")  # defensive
        inner.append(f'<script type="application/ld+json">{safe}</script>')
    body = "\n  ".join(inner)
    return f"{JSONLD_START}\n  {body}\n  {JSONLD_END}"


def build_canonical_tag(slug: str) -> str:
    href = f"{DEFAULT_BASE}/skills/gaokao-major-explorer/data/curated/{slug}.html"
    return f'{CANONICAL_MARKER}<link rel="canonical" href="{_esc(href)}">'


def build_og_tags(og_image: str) -> str:
    return (
        f'{OG_MARKER}'
        f'<meta property="og:image" content="{_esc(og_image)}">'
        f'<meta property="og:image:width" content="1200">'
        f'<meta property="og:image:height" content="630">'
        f'<meta property="og:type" content="article">'
        f'<meta property="og:site_name" content="Major Explorer">'
    )


def inject_into_html(
    html: str,
    slug: str,
    data: dict,
    og_image: str,
) -> str:
    payloads = [
        build_course_ld(slug, data),
        build_breadcrumb_ld(slug, data),
    ]
    faq = build_faq_ld(slug, data)
    if faq is not None:
        payloads.append(faq)

    jsonld_block = render_jsonld_block(payloads)
    canonical_tag = build_canonical_tag(slug)
    og_tags = build_og_tags(og_image)

    # Replace existing fenced blocks if present (idempotent re-runs).
    # We anchor each strip to start at the leading whitespace + marker, so the
    # surrounding newlines we inserted get removed too (otherwise the file
    # grows by 3 bytes per re-run).
    jsonld_re = re.compile(
        r"[ \t]*\n?[ \t]*" + re.escape(JSONLD_START) + r".*?" + re.escape(JSONLD_END),
        re.DOTALL,
    )
    canonical_re = re.compile(
        r"[ \t]*\n?[ \t]*" + re.escape(CANONICAL_MARKER) + r".*?(?=</head>)",
        re.DOTALL,
    )
    og_re = re.compile(
        r"[ \t]*\n?[ \t]*" + re.escape(OG_MARKER) + r".*?(?=</head>)",
        re.DOTALL,
    )

    # Strip all fenced blocks first.
    cleaned = jsonld_re.sub("", html)
    cleaned = canonical_re.sub("", cleaned)
    cleaned = og_re.sub("", cleaned)

    # Build the combined block.
    block = (
        f"\n  {canonical_tag}\n  "
        f"{og_tags}\n  "
        f"{jsonld_block}\n"
    )

    # Insert just before </head>.
    if "</head>" not in cleaned:
        raise ValueError(f"{slug}: no </head> tag found")
    new_html = cleaned.replace("</head>", f"{block}</head>", 1)

    return new_html


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def list_target_htmls() -> list[Path]:
    return sorted(
        p for p in CURATED.glob("*.html")
        if not p.stem.endswith("-demo") and p.stem != "manifest"
    )


def process_file(
    html_path: Path,
    *,
    dry_run: bool,
    backup: bool,
    og_image: str,
) -> tuple[str, int, int]:
    """Return (slug, jsonld_count, byte_delta)."""
    slug = html_path.stem
    json_path = CURATED / f"{slug}.json"
    if not json_path.is_file():
        return slug, 0, 0
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    html = html_path.read_text(encoding="utf-8")
    new_html = inject_into_html(html, slug, data, og_image)
    if new_html == html:
        return slug, 0, 0
    if backup and not dry_run:
        bak = html_path.with_suffix(html_path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(html_path, bak)
    if not dry_run:
        html_path.write_text(new_html, encoding="utf-8")
    jsonld_count = new_html.count('type="application/ld+json"')
    return slug, jsonld_count, len(new_html) - len(html)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject SEO JSON-LD + canonical + OG tags.")
    parser.add_argument("--slug", help="Process only this slug (e.g. accounting).")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip writing .bak files (not recommended for first run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change, but don't write files.",
    )
    parser.add_argument(
        "--og-image",
        default=f"{DEFAULT_BASE}/assets/og-default.png",
        help="og:image URL (default: https://[PLACEHOLDER_DOMAIN]/assets/og-default.png).",
    )
    args = parser.parse_args()

    targets = list_target_htmls()
    if args.slug:
        targets = [p for p in targets if p.stem == args.slug]
    if not targets:
        print("No target files matched.", file=sys.stderr)
        return 1

    injected = 0
    skipped = 0
    failed = 0
    for p in targets:
        try:
            slug, n_ld, delta = process_file(
                p,
                dry_run=args.dry_run,
                backup=not args.no_backup,
                og_image=args.og_image,
            )
            if n_ld == 0 and delta == 0:
                skipped += 1
            else:
                injected += 1
                print(f"  {slug}: {n_ld} JSON-LD blocks, {delta:+d} bytes")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  {p.name}: FAIL — {e}", file=sys.stderr)

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(
        f"\n[{mode}] processed={len(targets)} injected={injected} "
        f"skipped={skipped} failed={failed}"
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
