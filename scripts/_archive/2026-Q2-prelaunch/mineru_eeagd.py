"""
scripts/mineru_eeagd.py — MinerU Flash 解析 广东 2024 PDF (分批, 每批 20 页)

输入: data/_cache/eeagd_2024/gd20240719008.pdf (历史 29 页)
       data/_cache/eeagd_2024/gd20240719009.pdf (物理 58 页)
输出: data/_cache/eeagd_2024/gd2024_{历史|物理}.md (合并)

MinerU API 限 20 页/次, 分批处理.
"""
import sys
import time
from pathlib import Path
from mineru import MinerU

PDF_DIR = Path(__file__).parent.parent / "data" / "_cache" / "eeagd_2024"
TARGETS = [
    ("物理", "gd20240719009.pdf"),
    ("历史", "gd20240719008.pdf"),
]
PAGE_LIMIT = 20  # MinerU API 限制


def parse_pdf_in_chunks(client: MinerU, pdf_path: Path, page_limit: int = PAGE_LIMIT) -> str:
    """分批调用 MinerU, 合并 markdown."""
    import subprocess
    # 用 pdfplumber 或 pypdf 获取页数
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
    except ImportError:
        # 退化: 用 pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(str(pdf_path))
            total_pages = len(reader.pages)
        except ImportError:
            # 最后退化: 用 grep 找 /Type /Page 数
            import re
            data = pdf_path.read_bytes()
            total_pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
    print(f"  {pdf_path.name}: {total_pages} 页")

    chunks = []
    page = 1
    while page <= total_pages:
        end = min(page + page_limit - 1, total_pages)
        print(f"    解析 {page}-{end} ...", end=" ", flush=True)
        t0 = time.time()
        result = client.flash_extract(
            str(pdf_path),
            page_range=f"{page}-{end}",
            enable_table=True,
            timeout=600,
        )
        elapsed = time.time() - t0
        md = result.markdown or ""
        if not md:
            print(f"❌ (state={result.state}, err={result.err_code}, {result.error})")
        else:
            print(f"✓ {len(md):,} 字符 ({elapsed:.1f}s)")
        chunks.append(md)
        page = end + 1
    return "\n\n<!-- page_break -->\n\n".join(chunks)


def main():
    client = MinerU(token=None)
    client.set_source("gaokao-hubei-mvp")
    for subject, fname in TARGETS:
        pdf = PDF_DIR / fname
        if not pdf.exists():
            print(f"⚠️ {pdf} 缺失, 跳过")
            continue
        print(f"📦 {subject} {fname}")
        md = parse_pdf_in_chunks(client, pdf)
        out = PDF_DIR / f"gd2024_{subject}.md"
        out.write_text(md, encoding="utf-8")
        # 统计
        import re
        rows = len(re.findall(r"<tr", md))
        print(f"📊 {out.name}: {len(md):,} 字符 / {rows} 表格行")


if __name__ == "__main__":
    main()
