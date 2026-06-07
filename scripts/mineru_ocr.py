"""
scripts/mineru_ocr.py — MinerU Flash 模式重 OCR dxsbb 2024 PNGs

输入:  data/_cache/dxsbb_imgs/2024_{hist,phys}_{1,2,3}_2x.png
输出:  data/_cache/dxsbb_imgs/mineru_2024_{hist,phys}_{1,2,3}.md (markdown 含 HTML 表格)

Flash 模式 (mineru-open-sdk): 免费, 免 token, 输出 Markdown + 表格.

用法:
  pip install mineru-open-sdk
  export MINERU_TOKEN="..."  # 可选, 无则 Flash
  python scripts/mineru_ocr.py

注意: 比 Tesseract 慢 (单张 30-60s), 但表格结构 100% 保留, 校名 + 组号 + 投档线 全在 HTML 里.
"""
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
IMGS_DIR = PROJECT_DIR / "data" / "_cache" / "dxsbb_imgs"
OUT_DIR = IMGS_DIR

PNG_FILES = [
    ("历史", "2024_hist_1_2x.png"),
    ("历史", "2024_hist_2_2x.png"),
    ("历史", "2024_hist_3_2x.png"),
    ("物理", "2024_phys_1_2x.png"),
    ("物理", "2024_phys_2_2x.png"),
    ("物理", "2024_phys_3_2x.png"),
]


def main():
    try:
        from mineru import MinerU
    except ImportError:
        print("⚠️ mineru-open-sdk 未装. pip install mineru-open-sdk")
        sys.exit(1)

    # Flash 模式免 token (传 None), 有 token 自动 VLM 模式
    import os
    token = os.environ.get("MINERU_TOKEN") or None
    client = MinerU(token=token)
    client.set_source("gaokao-hubei-mvp")
    mode = "VLM (需 token)" if token else "Flash (免费)"
    print(f"📦 MinerU 引擎 ({mode}, {len(PNG_FILES)} 张 PNG)")

    total = 0
    for subject, fname in PNG_FILES:
        png = IMGS_DIR / fname
        if not png.exists():
            print(f"  ⚠️ {png.name} 缺失, 跳过")
            continue
        t0 = time.time()
        try:
            result = client.flash_extract(
                str(png),
                enable_table=True,
                timeout=600,  # 10 分钟, OCR 重图可能慢
            )
        except Exception as e:
            print(f"  ❌ {png.name} 失败: {e}")
            continue
        elapsed = time.time() - t0
        md = result.markdown or ""
        # 文件名: mineru_2024_hist_1.md / phys_1.md (按 batch 拆)
        # fname = "2024_hist_1_2x.png" → batch=1
        parts = fname.replace(".png", "").split("_")  # ["2024", "hist", "1", "2x"]
        batch = parts[2] if len(parts) > 2 else "1"
        out_name = f"mineru_2024_{subject}_{batch}.md"
        (OUT_DIR / out_name).write_text(md, encoding="utf-8")
        # 统计表格行数
        import re
        rows = len(re.findall(r"<tr", md))
        total += rows
        print(f"  {png.name}: {len(md):,} 字符 / {rows} 表格行 ({elapsed:.1f}s) → {out_name}")
    print(f"📊 总计 {total} 表格行")


if __name__ == "__main__":
    main()
