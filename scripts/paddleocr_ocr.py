"""
scripts/paddleocr_ocr.py — PaddleOCR 重 OCR dxsbb 2024 PNGs

输入:  data/_cache/dxsbb_imgs/2024_{hist,phys}_{1,2,3}_2x.png
输出:  data/_cache/dxsbb_imgs/ocr_2024_{hist,phys}_{1,2,3}_v4.txt

跟 Tesseract (v3) 输出格式对齐: 1 行 1 条记录, 用 '|' 分 cell, 模拟表格.

用法 (Docker):
  docker compose --profile ocr run --rm paddleocr
或本地:
  pip install paddlepaddle==3.0.0 paddleocr==3.0.0
  python scripts/paddleocr_ocr.py
"""
import sys
import time
from pathlib import Path
from typing import Iterable

PROJECT_DIR = Path(__file__).parent.parent
IMGS_DIR = PROJECT_DIR / "data" / "_cache" / "dxsbb_imgs"
OUT_DIR = IMGS_DIR  # output 同目录, 文件名 v4

PNG_FILES = [
    ("历史", "2024_hist_1_2x.png"),
    ("历史", "2024_hist_2_2x.png"),
    ("历史", "2024_hist_3_2x.png"),
    ("物理", "2024_phys_1_2x.png"),
    ("物理", "2024_phys_2_2x.png"),
    ("物理", "2024_phys_3_2x.png"),
]


def ocr_paddle(png_path: Path) -> list[list[str]]:
    """跑 PaddleOCR, 返回每行的 cell list.

    试图还原 表格 结构:
      - 同一 y 坐标 (高度容差 10px) 内的 text box 视为同行
      - 同行的 box 按 x 排序
    """
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=False, lang="ch", show_log=False)
    result = ocr.ocr(str(png_path), cls=False)
    if not result or not result[0]:
        return []
    # result[0] = [(box, (text, score)), ...]
    # box = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    items = []
    for box, (text, _score) in result[0]:
        y = (box[0][1] + box[2][1]) / 2  # 中点 y
        x = (box[0][0] + box[2][0]) / 2
        items.append((y, x, text))
    # 按 y 排序, 同 y (容差 10) 视为同行
    items.sort(key=lambda t: (t[0], t[1]))
    rows: list[list[str]] = []
    cur_row: list[tuple[float, str]] = []
    cur_y = None
    for y, x, text in items:
        if cur_y is None or abs(y - cur_y) < 15:
            cur_row.append((x, text))
        else:
            cur_row.sort()
            rows.append([t for _, t in cur_row])
            cur_row = [(x, text)]
            cur_y = y
        if cur_y is None:
            cur_y = y
    if cur_row:
        cur_row.sort()
        rows.append([t for _, t in cur_row])
    return rows


def rows_to_pipe_lines(rows: Iterable[list[str]]) -> list[str]:
    """PaddleOCR rows → Tesseract 风格 '|' 分隔行."""
    out = []
    for row in rows:
        # 过滤空 / 纯符号
        cells = [c.strip() for c in row if c and c.strip()]
        if not cells:
            continue
        out.append("|".join(cells))
    return out


def main():
    if not IMGS_DIR.exists():
        print(f"⚠️ PNG 目录不存在: {IMGS_DIR}")
        sys.exit(1)

    print(f"📦 PaddleOCR 引擎 (lang=ch, {len(PNG_FILES)} 张 PNG)")
    total_lines = 0
    for subject, fname in PNG_FILES:
        png = IMGS_DIR / fname
        if not png.exists():
            print(f"  ⚠️ {png.name} 缺失, 跳过")
            continue
        t0 = time.time()
        rows = ocr_paddle(png)
        elapsed = time.time() - t0
        lines = rows_to_pipe_lines(rows)
        out_name = f"ocr_2024_{subject}_{fname.split('_')[1]}_v4.txt"
        (OUT_DIR / out_name).write_text("\n".join(lines), encoding="utf-8")
        total_lines += len(lines)
        print(f"  {png.name}: {len(lines)} 行 ({elapsed:.1f}s) → {out_name}")
    print(f"📊 总计 {total_lines} 行")


if __name__ == "__main__":
    main()
