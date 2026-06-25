"""
scripts/ocr_yfyd_images.py — 用 tesseract OCR 湖北 2026 一分一段表 JPG/WebP

输入: 一组目录 (page0 物理 / page1 历史),每目录 5 张图
输出: hubei_rank_{物理|历史}_2026.csv (score,rank,count)
      yfyd 转为 JSON: data/yfyd_hubei_2026.json

tesseract 安装: brew install tesseract tesseract-lang
OCR 准确性依赖 chi_sim+eng 语言包

用法:
  python3 scripts/ocr_yfyd_images.py
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

WULI_DIR = Path("/tmp/3prov_monitor/hb_wuli_png")
LISHI_DIR = Path("/tmp/3prov_monitor/hb_lishi_png")
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)


def ocr_image(img_path: Path) -> str:
    """Run tesseract on image (via stdin pipe), return text.

    Note: tesseract on macOS 5.5.2 with leptonica 1.87 has a bug
    where it can't open files directly (`failed to open locally with tail`).
    Pipe via stdin works around this.
    """
    out_prefix = img_path.parent / f"_ocr_{img_path.stem}"
    try:
        with open(img_path, "rb") as f:
            data = f.read()
        result = subprocess.run(
            ["tesseract", "-", "-", "-l", "chi_sim+eng", "--psm", "4"],
            input=data, capture_output=True, timeout=60,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            print(f"  ⚠️  tesseract failed for {img_path.name}: {stderr[:200]}", file=sys.stderr)
            return ""
        return result.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️  exception: {e}", file=sys.stderr)
        return ""


def parse_rows(text: str) -> list[tuple[int, int, int]]:
    """
    Parse OCR text to list of (score, count, cumulative).
    Format per row: 分数  人数  累计人数  (3 cols × N rows)
    Example: '710        1           21           664       119        1838'
    """
    rows = []
    # Lines starting with 3-4 digit numbers (scores)
    score_re = re.compile(r"^\s*(\d{2,4})\s+(\d{1,5})\s+(\d{1,7})\s*(.*)$")
    for line in text.split("\n"):
        line = line.strip()
        if not line or not line[0].isdigit():
            continue
        m = score_re.match(line)
        if not m:
            continue
        score_str, count_str, cum_str, rest = m.groups()
        try:
            score = int(score_str)
            count = int(count_str)
            cum = int(cum_str)
            rows.append((score, count, cum))
            # 后面可能还有第二、三组 (684 24 3052 之类),parse 剩余部分
            rest_clean = rest.strip()
            if rest_clean:
                # Try to extract more triples from rest
                # Pattern: 分数  人数  累计
                triples = re.findall(r"(\d{2,4})\s+(\d{1,5})\s+(\d{1,7})", rest_clean)
                for s, c, cu in triples:
                    rows.append((int(s), int(c), int(cu)))
        except ValueError:
            continue
    return rows


def ocr_directory(dir_path: Path) -> list[tuple[int, int, int]]:
    """OCR all images in directory, return merged list of rows."""
    all_rows = []
    for img in sorted(dir_path.glob("*.png")):
        print(f"  OCR {img.name}...")
        text = ocr_image(img)
        rows = parse_rows(text)
        print(f"    → {len(rows)} rows")
        all_rows.extend(rows)
    return all_rows


def merge_consecutive_images(img_dir: Path) -> list[tuple[int, int, int]]:
    """OCR all images, merge by score (dedup across pages)."""
    rows = ocr_directory(img_dir)
    # Sort by score desc (highest first)
    rows.sort(key=lambda x: -x[0])
    # Dedupe by score (keep first occurrence — should be consistent across pages)
    seen = set()
    deduped = []
    for r in rows:
        if r[0] in seen:
            continue
        seen.add(r[0])
        deduped.append(r)
    return deduped


def rows_to_yfyd_json(rows: list[tuple[int, int, int]], subject_cn: str) -> dict:
    """Convert (score, count, cumulative) rows to yfyd JSON format."""
    return {
        "year": 2026,
        "province": "湖北",
        "source": f"湖北省2026年普通高考总分一分一段统计表—普通类 ({subject_cn}) 6/25 eea.gd",
        "wuli" if subject_cn == "物理" else "lishi": {
            "subject_type": f"{subject_cn}类",
            "rows": [{"score": s, "count": c, "rank": r} for (s, c, r) in rows],
        },
    }


def main():
    print("OCR 首选物理 (5 张图)...")
    wuli_rows = merge_consecutive_images(WULI_DIR)
    print(f"  total deduped: {len(wuli_rows)}")
    if wuli_rows:
        print(f"  score range: {wuli_rows[0][0]} (rank {wuli_rows[0][2]}) → {wuli_rows[-1][0]} (rank {wuli_rows[-1][2]})")
    else:
        print("  ❌ OCR 没提取到任何行, debug 必要")
        return

    print("\nOCR 首选历史 (5 张图)...")
    lishi_rows = merge_consecutive_images(LISHI_DIR)
    print(f"  total deduped: {len(lishi_rows)}")
    if lishi_rows:
        print(f"  score range: {lishi_rows[0][0]} (rank {lishi_rows[0][2]}) → {lishi_rows[-1][0]} (rank {lishi_rows[-1][2]})")

    # 写 CSV
    wuli_csv = OUT_DIR / "hubei_rank_物理_2026.csv"
    lishi_csv = OUT_DIR / "hubei_rank_历史_2026.csv"
    for path, rows in [(wuli_csv, wuli_rows), (lishi_csv, lishi_rows)]:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["score", "rank", "count"])
            for score, count, cum in rows:
                w.writerow([score, cum, count])
        print(f"✅ wrote {path}: {len(rows)} rows")

    # 写 JSON (给 convert_yfyd.py 用)
    import json
    wuli_json = OUT_DIR / "yfyd_hubei_2026_raw.json"
    lishi_json = OUT_DIR / "yfyd_hubei_2026_raw_lishi.json"
    with open(wuli_json, "w", encoding="utf-8") as f:
        json.dump(rows_to_yfyd_json(wuli_rows, "物理"), f, ensure_ascii=False, indent=2)
    with open(lishi_json, "w", encoding="utf-8") as f:
        json.dump(rows_to_yfyd_json(lishi_rows, "历史"), f, ensure_ascii=False, indent=2)
    print(f"✅ wrote raw JSON: {wuli_json}, {lishi_json}")

    # 580 分位次校准 (跟旧 2025 对比)
    for name, rows in [("物理", wuli_rows), ("历史", lishi_rows)]:
        for score, count, cum in rows:
            if score <= 580:
                print(f"\n{name} 580 分 → rank {cum} (count={count})")
                break


if __name__ == "__main__":
    main()