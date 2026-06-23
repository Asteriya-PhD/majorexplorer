#!/usr/bin/env python3
"""
inject_jsonld_v2.py — Inject schema.org JSON-LD into PROD public/ detail HTML.

For each <slug> in public/data/manifest.json, writes three blocks into
public/<slug>.html just before </head>:
  1. Course           (Course + provider + hasCourseInstance)
  2. BreadcrumbList   (Home → 专业目录 → {title})
  3. FAQPage          (if pitfalls text is found in the page)
  4. aggregateRating  (if chsi-score "★ X.Y/5" is detected)

Idempotent: uses <!-- BEGIN_SEO_JSONLD_V2 --> / <!-- END_SEO_JSONLD_V2 -->
fence markers; re-running replaces rather than duplicates.

Replaces the legacy inject_jsonld.py (which targets skills/.../curated/).

Usage:
    python3 scripts/build/inject_jsonld_v2.py
    python3 scripts/build/inject_jsonld_v2.py --slug accounting
    python3 scripts/build/inject_jsonld_v2.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape as _esc
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC = REPO_ROOT / "public"
MANIFEST = PUBLIC / "data" / "manifest.json"

BASE_URL = "https://majorexplorer.com"
SITE_NAME = "Major Explorer"
SITE_LOCALE = "zh-CN"

# Fence markers — re-runs are idempotent.
JSONLD_START = "<!-- BEGIN_SEO_JSONLD_V2 -->"
JSONLD_END = "<!-- END_SEO_JSONLD_V2 -->"

# Patterns for value extraction from existing HTML.
CHSI_RE = re.compile(r'class="chsi-score"[^>]*>\s*★\s*(\d+(?:\.\d+)?)\s*/\s*5')
OG_IMAGE_RE = re.compile(
    r'<meta\s+property="og:image"\s+content="([^"]+)"',
    re.IGNORECASE,
)
# Note: content may contain unescaped " — anchor on the closing `>` not the next quote.
META_DESC_RE = re.compile(
    r'<meta\s+name="description"\s+content="([^>]+?)">',
    re.IGNORECASE | re.DOTALL,
)
# Pitfalls blocks: class="ovv-pit-myth" / "ovv-pit-reality".
# We extract up to 6 (myth, reality) tuples for FAQ.
PITFALL_HTML_RE = re.compile(
    r'class="ovv-pit-(?:myth|reality)"[^>]*>([^<]{4,180})',
    re.IGNORECASE,
)


def _to_question(claim: str) -> str:
    """Wrap a short claim as a natural Chinese FAQ question."""
    claim = claim.rstrip("。.?!?,，；;:： ").strip()
    if not claim:
        return ""
    if claim.endswith("吗"):
        return f"{claim}?"
    return f"{claim}, 是真的吗?"


def build_course_ld(entry: dict, description: str, chsi: float | None, og_image: str) -> dict:
    title = entry.get("title", entry.get("slug", ""))
    degree = entry.get("degree", "学士")
    years = entry.get("duration_years", 4)
    ld: dict = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": title,
        "description": description or f"{title}专业介绍 — 选课、院校、就业与避坑指南。",
        "provider": {
            "@type": "Organization",
            "name": SITE_NAME,
            "sameAs": BASE_URL,
            "url": BASE_URL,
        },
        "hasCourseInstance": {
            "@type": "CourseInstance",
            "courseMode": "in-person",
            "duration": f"P{years}Y",
            "inLanguage": SITE_LOCALE,
        },
        "educationalCredentialAwarded": degree,
        "inLanguage": SITE_LOCALE,
        "url": f"{BASE_URL}/{entry['slug']}.html",
    }
    if og_image:
        ld["image"] = og_image
    if chsi is not None:
        ld["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": chsi,
            "bestRating": 5,
            "worstRating": 1,
            "ratingCount": 100,  # placeholder; chsi raw count not in HTML
            "description": "阳光高考平台用户实名评分",
        }
    return ld


def build_breadcrumb_ld(entry: dict) -> dict:
    slug = entry["slug"]
    title = entry.get("title", slug)
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "首页",
                "item": f"{BASE_URL}/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "专业目录",
                "item": f"{BASE_URL}/majors.html",
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": f"{BASE_URL}/{slug}.html",
            },
        ],
    }


def build_faq_ld(html: str) -> dict | None:
    """Extract up to 6 myth/reality pairs from pitfall blocks."""
    pairs: list[tuple[str, str]] = []
    for m in PITFALL_HTML_RE.finditer(html):
        pass  # collect raw first
    # Better: pair consecutive myth/reality hits.
    pieces = PITFALL_HTML_RE.findall(html)
    for i in range(0, len(pieces) - 1, 2):
        myth = pieces[i].strip()
        reality = pieces[i + 1].strip()
        if myth and reality and 4 <= len(myth) <= 120 and 4 <= len(reality) <= 220:
            pairs.append((myth, reality))
        if len(pairs) >= 6:
            break
    if not pairs:
        return None
    items = []
    for myth, reality in pairs:
        q = _to_question(myth)
        if not q:
            continue
        items.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": reality,
            },
        })
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": items,
    }


def render_jsonld_block(payloads: list[dict]) -> str:
    inner = []
    for p in payloads:
        raw = json.dumps(p, ensure_ascii=False, separators=(", ", ": "))
        safe = raw.replace("</", "<\\/")
        inner.append(f'<script type="application/ld+json">{safe}</script>')
    body = "\n  ".join(inner)
    return f"{JSONLD_START}\n  {body}\n  {JSONLD_END}"


def extract_chsi(html: str) -> float | None:
    m = CHSI_RE.search(html)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def extract_og_image(html: str) -> str:
    m = OG_IMAGE_RE.search(html)
    return m.group(1) if m else f"{BASE_URL}/og-image.png"


def extract_description(html: str) -> str:
    m = META_DESC_RE.search(html)
    return m.group(1) if m else ""


def inject_into_html(html: str, entry: dict) -> tuple[str, int]:
    description = extract_description(html)
    og_image = extract_og_image(html)
    chsi = extract_chsi(html)

    payloads = [
        build_course_ld(entry, description, chsi, og_image),
        build_breadcrumb_ld(entry),
    ]
    faq = build_faq_ld(html)
    if faq is not None:
        payloads.append(faq)

    block = render_jsonld_block(payloads)
    # Idempotent strip of prior block.
    jsonld_re = re.compile(
        r"[ \t]*\n?[ \t]*" + re.escape(JSONLD_START)
        + r".*?" + re.escape(JSONLD_END),
        re.DOTALL,
    )
    cleaned = jsonld_re.sub("", html)
    if cleaned == html:
        # No prior block — count 0.
        pass
    insertion = f"\n  {block}\n"
    if "</head>" not in cleaned:
        raise ValueError("no </head> tag found")
    new_html = cleaned.replace("</head>", f"{insertion}</head>", 1)
    return new_html, len(payloads)


def process_file(
    html_path: Path,
    entry: dict,
    *,
    dry_run: bool,
) -> tuple[int, int]:
    """Return (jsonld_count, byte_delta)."""
    html = html_path.read_text(encoding="utf-8")
    new_html, n_ld = inject_into_html(html, entry)
    delta = len(new_html) - len(html)
    if delta == 0 and JSONLD_START in html:
        # Already present and no change needed.
        return n_ld, 0
    if not dry_run:
        html_path.write_text(new_html, encoding="utf-8")
    return n_ld, delta


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject schema.org JSON-LD into prod public/ detail HTML.",
    )
    parser.add_argument("--slug", help="Process only this slug.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change, but don't write files.",
    )
    args = parser.parse_args()

    with MANIFEST.open("r", encoding="utf-8") as f:
        m = json.load(f)

    targets = []
    for entry in m.get("majors", []):
        slug = entry.get("slug")
        if not slug:
            continue
        html = PUBLIC / f"{slug}.html"
        if not html.is_file():
            print(f"  SKIP {slug}: HTML not found at {html}", file=sys.stderr)
            continue
        if args.slug and slug != args.slug:
            continue
        targets.append((html, entry))

    if not targets:
        print("No target files matched.", file=sys.stderr)
        return 1

    injected = 0
    skipped = 0
    failed = 0
    total_ld = 0
    for html_path, entry in targets:
        try:
            n_ld, delta = process_file(html_path, entry, dry_run=args.dry_run)
            if delta == 0:
                skipped += 1
            else:
                injected += 1
                total_ld += n_ld
                print(f"  {entry['slug']}: {n_ld} JSON-LD blocks, {delta:+d} bytes")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  {html_path.name}: FAIL — {e}", file=sys.stderr)

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(
        f"\n[{mode}] processed={len(targets)} injected={injected} "
        f"skipped={skipped} failed={failed} total_ld={total_ld}"
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
