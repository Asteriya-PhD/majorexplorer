"""
scripts/pdf_to_yfyd_csv.py — 解析广东 2026 PDF 一分一段表 → CSV

广东 eea.gd 官方 PDF 格式:
- 12 页 (670→440 分)
- 4 列: 文化总分 / 本科 人数 / 本科 累计 / 专科 人数 / 专科 累计 (实际 5 列)

PDF 含 watermark (广东省教育考试院) 干扰, pdftotext 输出破碎。
用 pdfplumber 提取真实表格行。

用法:
  python3 scripts/pdf_to_yfyd_csv.py --input gd_yfyd.pdf --output gd_yfyd.csv --type wuli
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import pdfplumber


def parse_pdf(pdf_path: Path) -> list[tuple[int, int, int]]:
    """Extract (score, count, cumulative) from PDF table."""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Try extract_tables first (more reliable)
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if not row or len(row) < 3:
                            continue
                        # First col is score, then 本科 人数 / 本科 累计
                        # OR 累计(不区分本/专), 选最长累计列
                        score_str = (row[0] or "").strip()
                        if not score_str:
                            continue
                        m = re.match(r"^(\d{3,4})(?:[（(].*?[)）])?$", score_str)
                        if not m:
                            continue
                        score = int(m.group(1))
                        if score < 100 or score > 800:
                            continue
                        # Find count + cumulative (look for numeric cells)
                        nums = []
                        for cell in row[1:]:
                            if cell:
                                cell_clean = re.sub(r"[^\d]", "", str(cell))
                                if cell_clean and cell_clean.isdigit():
                                    nums.append(int(cell_clean))
                        if len(nums) >= 2:
                            # First num = count, second = cumulative
                            rows.append((score, nums[0], nums[1]))
            else:
                # Fallback: extract text + parse lines
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    line = line.strip()
                    # Pattern: 669(含以上)  16  16  16  16  (header line skipped)
                    m = re.match(r"^(\d{3,4})\s*(?:[（(].*?[)）])?\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
                    if m:
                        score = int(m.group(1))
                        # 本科 人数 = group(2), 本科 累计 = group(3), 专科 人数 = group(4), 专科 累计 = group(5)
                        if score >= 100 and score <= 800:
                            rows.append((score, int(m.group(2)), int(m.group(3))))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--type", choices=["wuli", "lishi"], default="wuli")
    args = ap.parse_args()

    rows = parse_pdf(args.input)
    # Dedupe by score
    seen = set()
    deduped = []
    for r in rows:
        if r[0] in seen:
            continue
        seen.add(r[0])
        deduped.append(r)
    deduped.sort(key=lambda x: -x[0])

    print(f"Parsed {len(deduped)} unique rows from {args.input}")
    if deduped:
        print(f"  score range: {deduped[0][0]} (cum {deduped[0][2]}) → {deduped[-1][0]} (cum {deduped[-1][2]})")
        # 580 分位次
        for score, count, cum in deduped:
            if score <= 580:
                print(f"  580 分 → rank {cum} (count {count})")
                break

    with open(args.output, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["score", "rank", "count"])
        for score, count, cum in deduped:
            w.writerow([score, cum, count])
    print(f"✅ wrote {args.output}")


if __name__ == "__main__":
    main()