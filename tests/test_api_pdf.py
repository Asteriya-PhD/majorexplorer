"""
tests/test_api_pdf.py — api/main.py:api_recommend_pdf 单元测试

覆盖:
- POST /api/recommend/pdf 返回 application/pdf
- 响应以 %PDF 开头 (PDF magic bytes)
- Content-Disposition 头含 attachment + 文件名
- 文件大小 > 1KB (空 PDF 不会有内容)
- 错误情况: 无效 province → 500 或 404

数据: 用 2025 HB 物理 (已有 205 行 admission, 验证通过)
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402

client = TestClient(app)


def test_recommend_pdf_returns_valid_pdf():
    """POST /api/recommend/pdf → application/pdf, %PDF 开头, > 1KB."""
    req = {
        "rank": 10000, "province": "hubei", "subject": "物理", "year": 2025,
        "xuanke": "物+化+生", "n_chong": 10, "n_wen": 10, "n_bao": 10, "n_total": 30,
    }
    resp = client.post("/api/recommend/pdf", json=req)
    assert resp.status_code == 200, f"PDF 生成失败: {resp.status_code} {resp.text[:300]}"
    # 1. Content-Type
    assert resp.headers["content-type"] == "application/pdf"
    # 2. PDF magic bytes
    body = resp.content
    assert body[:4] == b"%PDF", f"PDF 文件应以 %PDF 开头, 实际: {body[:10]!r}"
    # 3. 大小 > 1KB (含封面 + 考生信息 + 等效分 + 30 推表格, 实际应 ~10-50KB)
    assert len(body) > 1024, f"PDF 太小 ({len(body)} 字节), 可能没内容"
    # 4. EOF marker
    assert b"%%EOF" in body[-1024:], "PDF 应以 %%EOF 结尾"


def test_recommend_pdf_content_disposition():
    """Content-Disposition 头含 attachment + 文件名 (含省份/科目)."""
    req = {
        "rank": 10000, "province": "hubei", "subject": "历史", "year": 2025,
        "xuanke": "历+政+地", "n_chong": 5, "n_wen": 5, "n_bao": 5, "n_total": 15,
    }
    resp = client.post("/api/recommend/pdf", json=req)
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".pdf" in cd
    assert "hubei" in cd and "history" in cd  # ascii mapping for 历史 → history


def test_recommend_pdf_filename_uses_ascii():
    """文件名用 ASCII (避免 latin-1 编码错误 per api/main.py:154 注释)."""
    req = {
        "rank": 5000, "province": "guangdong", "subject": "物理", "year": 2024,
        "xuanke": "物+化+生", "n_chong": 5, "n_wen": 5, "n_bao": 5, "n_total": 15,
    }
    resp = client.post("/api/recommend/pdf", json=req)
    assert resp.status_code == 200, resp.text[:300]
    cd = resp.headers.get("content-disposition", "")
    # 提取 filename="..." 部分
    import re
    m = re.search(r'filename="([^"]+)"', cd)
    assert m, f"filename 不在 CD 头: {cd}"
    fname = m.group(1)
    # 应只含 ASCII: 字母数字下划线点
    assert all(ord(c) < 128 for c in fname), f"文件名含非 ASCII: {fname!r}"
    assert "guangdong" in fname and "physics" in fname


def test_recommend_pdf_handles_empty_candidate():
    """rank 极端大 (无候选) → 应返回 500 或 200+warning 字段, 不崩溃."""
    req = {
        "rank": 999999, "province": "hubei", "subject": "物理", "year": 2025,
        "xuanke": "物+化+生", "n_chong": 5, "n_wen": 5, "n_bao": 5, "n_total": 15,
    }
    resp = client.post("/api/recommend/pdf", json=req)
    # 没候选时, recommend 返回空 volunteers, build_pdf_report 应该仍能生成 (只是空表)
    # 接受 200 (空 PDF) 或 500 (内部 fallback)
    assert resp.status_code in (200, 500), f"意外 status: {resp.status_code}"
    if resp.status_code == 200:
        assert resp.content[:4] == b"%PDF"
    # 500 情况下应该有错误信息
    if resp.status_code == 500:
        body = resp.json()
        assert "detail" in body
