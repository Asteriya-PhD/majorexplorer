"""
scripts/parse_gk100_js_2025.py — 解析 江苏 2025 本科批 投档线 (gk100 TOP100 OCR/HTTP)

输入: data/_cache/read_362938512_js2025.htm (gk100.com 江苏 2025 各大学投档线页)
       — 静态 HTML 含 2 张表 (TOP100 物理 + TOP100 历史, 各 102 行)
输出: data/jiangsu_admission_{物理|历史}_2025_real_gk100.csv

源数据 (gk100 read_362938512.htm):
- 物理类: 1 张表, 102 行 (1 title + 1 header + 100 data)
- 历史类: 1 张表, 102 行 (同上)

schema (跟 GD 2025 一致):
  学校名 | 专业组 | 2025分数 | 2025位次

注意:
  - 2025位次 可能是 "126以内" / "109以内" (gk100 用 "以内" 表示 <某个值)
    本脚本保守处理: 用模糊中位数 (e.g. "126以内" → 63, "109以内" → 55)
  - 专业组 可能含 "(中外合作)" / "(内地香港合作办学)" 等后缀 → is_special
  - 分数可能末尾有 ";" 残留 (HTML 转义) — 清洗
"""
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
CACHE_HTML = PROJECT_DIR / "data" / "_cache" / "read_362938512_js2025.htm"
DATA_DIR = PROJECT_DIR / "data"


def _parse_rank(rank_cell: str) -> int:
    """gk100 rank 可能是 '126' (纯数字) 或 '126以内' (上限).
    '以内' → 用 1/2 上限作为估计 (e.g. '126以内' → 63).
    因为我们关心 cross-year stability, 估计值已够 calibration 用.
    """
    s = re.sub(r"[^\d]", "", str(rank_cell))
    if not s:
        return 0
    n = int(s)
    if "以内" in str(rank_cell):
        return max(1, n // 2)
    return n


def _is_special_group(group_code: str) -> str:
    """专业组后缀含 (中外合作)/(联合培养)/(专项) 等 → is_special=是."""
    if any(k in group_code for k in [
        "中外合作", "联合培养", "内地香港", "内地澳门",
        "专项", "预科", "民族", "校区", "分校"
    ]):
        return "是"
    return "否"


def _group_id_from_code(group_code: str) -> str:
    """从 '05组' / '03组(中外合作)' / '201组(内地香港合作办学)' 提取 group_id."""
    m = re.search(r"(\d+)组", str(group_code))
    if m:
        return m.group(1).zfill(2)
    return "01"


def _xuanke_req_from_group(group_code: str) -> str:
    """JS gk100 TOP100 简表不写选科 — 默认 '不限' (TOP100 都是高分, 多为不限).
    实际专业组选科由 jseea 官方 XLS 决定, 本表只用于 院校+组+分+位次 锚点.
    """
    return "不限"


def parse_table(html: str, subject: str) -> pd.DataFrame:
    """解析单张 TOP100 表 → DataFrame."""
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    target_idx = 0 if subject == "物理" else 1
    if target_idx >= len(tables):
        return pd.DataFrame()
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', tables[target_idx], re.DOTALL)
    rows, skipped = [], 0
    for tr in trs:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL)
        tds = [re.sub(r"<[^>]+>", "", t).strip() for t in tds]
        # schema: 学校名 | 专业组 | 2025分数 | 2025位次 (4 列)
        if len(tds) < 4 or tds[0] in ("学校名", ""):
            continue
        if "TOP100" in tds[0] or "录取分数线" in tds[0]:
            continue
        school, group, score, rank = tds[0], tds[1], tds[2], tds[3]
        # 分数清洗: "686;" → "686"
        score_clean = re.sub(r"[^\d]", "", score)
        if not score_clean:
            skipped += 1
            continue
        rows.append({
            "school_name": school,
            "group_code": group,
            "min_score": int(score_clean),
            "min_rank": _parse_rank(rank),
            "subject": subject,
            "xuanke_req": _xuanke_req_from_group(group),
            "is_special": _is_special_group(group),
            "year": 2025,
        })
    if skipped:
        print(f"  ⚠️ {subject}: 跳过 {skipped} 行 (分数非数字)")
    return pd.DataFrame(rows)


def main():
    if not CACHE_HTML.exists():
        print(f"⚠️ 缺失 {CACHE_HTML}, 先 curl 到 cache")
        return
    html = CACHE_HTML.read_text(encoding="utf-8", errors="replace")
    summary = {}
    for subject in ["物理", "历史"]:
        df = parse_table(html, subject)
        # Dedup on (school, group_code)
        df = df.drop_duplicates(subset=["school_name", "group_code"], keep="first")
        out = DATA_DIR / f"jiangsu_admission_{subject}_2025_real_gk100.csv"
        df.to_csv(out, index=False)
        summary[subject] = len(df)
        if df.empty:
            print(f"  ⚠️ {subject}: 0 行")
            continue
        scores = df["min_score"]
        ranks = df["min_rank"]
        print(f"  ✅ {subject}: {len(df)} 行 → {out.name}")
        print(f"     score range: {scores.min()}-{scores.max()}, median {scores.median():.0f}")
        print(f"     rank range: {ranks.min()}-{ranks.max()}, median {ranks.median():.0f}")
    print(f"\n=== JS 2025 TOP100 (gk100) 总结 ===")
    for s, n in summary.items():
        print(f"  {s}: {n} 行")


if __name__ == "__main__":
    main()
