"""
scripts/parse_mineru_ocr.py — 解析 MinerU Flash 输出 (HTML 表格)

输入:  data/_cache/dxsbb_imgs/mineru_2024_{hist,phys}_{1,2,3}.md
输出:  data/hubei_admission_{历史|物理}_2024_real_mineru.csv

格式 (例):
  <tr><td>A00102</td><td>北京大学第02组</td><td>不限</td><td>661</td>
       <td>246</td><td>131</td><td>143</td><td>85</td><td>99</td><td>88</td><td>1</td><td></td></tr>

列顺序 (11 列):
  0 院校专业组代号   (group_code, e.g. A00102)
  1 院校专业组名称   (school_name + "第NN组", e.g. "北京大学第02组")
  2 再选科目要求     (xuanke_req, e.g. "不限" / "化" / "化学")
  3 投档线           (min_score, e.g. 661)
  4-10 末位投档考生同分排序项 7 列 (语数/外语/再选等 — 跳过)
  11 备注            (is_special if "国家专项计划" 等)

group_id 提取: 从 "北京大学第02组" 拿 "02", 或 fallback 到 group_code 后两位
"""
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
OCR_DIR = DATA_DIR / "_cache" / "dxsbb_imgs"
SCHOOL_GROUP_PAT = re.compile(r"^(.+?)第(\d{1,2})组\s*$")
GROUP_CODE_PAT = re.compile(r"^([A-Z]\d{3})(\d{2})$")  # A00102 → (A001, 02)

# is_special 关键字
SPECIAL_KW = ["国家专项", "专项计划", "少数民族", "预科", "R班", "ER班",
              "中外合作", "联培", "校区", "分校", "民族班", "小语种", "马来西亚"]


def parse_html_table_row(tr: str) -> list[str]:
    """提取 <tr> 内所有 <td> 文本."""
    tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
    return [re.sub(r"<[^>]+>", " ", t).strip() for t in tds]


def parse_md_file(md_path: Path, year: int, subject: str) -> list[dict]:
    """解析单个 MD 文件 → row 列表."""
    if not md_path.exists():
        return []
    raw = md_path.read_text(encoding="utf-8", errors="replace")
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.DOTALL)
    rows = []
    skipped_empty = 0
    for tr in trs:
        cells = parse_html_table_row(tr)
        if len(cells) < 4:
            continue
        group_code = cells[0]
        full_name = cells[1]  # "北京大学第02组"
        xuanke = cells[2] if len(cells) > 2 else "不限"
        score_str = cells[3] if len(cells) > 3 else ""
        note = cells[11] if len(cells) > 11 else ""
        # 跳过表头
        if not re.match(r"^[A-Z]\d{5}$", group_code):
            continue
        if not score_str.isdigit():
            continue
        # 跳过校名空 (OCR 漏识别, 如 A02705)
        if not full_name or not full_name.strip():
            skipped_empty += 1
            continue
        # 拆 group_id
        m = SCHOOL_GROUP_PAT.match(full_name)
        if m:
            school_name = m.group(1).strip()
            group_id = m.group(2).zfill(2)
        else:
            # fallback: 从 group_code 拿
            gm = GROUP_CODE_PAT.match(group_code)
            school_name = full_name
            group_id = gm.group(2) if gm else "01"
        # is_special
        is_special = "是" if any(kw in note for kw in SPECIAL_KW) else "否"
        # xuanke 标准化: "化" / "化学" → "化学", 空 → "不限"
        xuanke_map = {"化": "化学", "生": "生物", "地": "地理", "政": "政治"}
        xuanke = xuanke_map.get(xuanke, xuanke) or "不限"
        rows.append({
            "year": year,
            "subject": subject,
            "school_name": school_name,
            "group_id": group_id,
            "group_code": group_code,
            "min_score": int(score_str),
            "min_rank": 0,  # 由 main() 用 rank 表反查
            "xuanke_req": xuanke,
            "is_special": is_special,
        })
    if skipped_empty:
        print(f"    ⚠️  {md_path.name}: 跳过 {skipped_empty} 行 (校名 OCR 空)")
    return rows


def fixup_group_id(rows: list[dict], subject: str, year: int = 2024) -> list[dict]:
    """group_id 不规范时, 试从 dxsbb 6261 表匹配同校真实组号."""
    ref_path = DATA_DIR / f"hubei_admission_{subject}_{year}_real_dxsbb6261.csv"
    if not ref_path.exists():
        return rows
    ref = pd.read_csv(ref_path)
    if "group_id" not in ref.columns:
        return rows
    real_pairs = set(zip(ref["school_name"], ref["group_id"].astype(str).str.zfill(2)))
    for r in rows:
        school = r["school_name"]
        candidates = [g for (s, g) in real_pairs if s == school]
        if candidates and r["group_id"] in ("00", "0"):
            r["group_id"] = sorted(candidates)[0]
    return rows


def load_rank_table(subject: str, year: int = 2024) -> pd.DataFrame:
    f = DATA_DIR / f"hubei_rank_{subject}_{year}.csv"
    if not f.exists():
        return pd.DataFrame()
    df = pd.read_csv(f)
    df["_score_int"] = df["score"].apply(
        lambda s: int(str(s).split("-")[0]) if "-" in str(s) else
                  int(s) if str(s).isdigit() else -1
    )
    return df[df["_score_int"] >= 0].copy()


def score_to_rank(score: int, rank_df: pd.DataFrame) -> int:
    if rank_df.empty:
        return 999999
    rows = rank_df[rank_df["_score_int"] == score]
    if rows.empty:
        rows = rank_df[rank_df["_score_int"] < score]
        if rows.empty:
            return 999999
        return int(rows.iloc[-1]["rank"])
    return int(rows.iloc[0]["rank"])


def main():
    summary = {}
    for subject, files in [
        ("历史", ["mineru_2024_历史_1.md", "mineru_2024_历史_2.md", "mineru_2024_历史_3.md"]),
        ("物理", ["mineru_2024_物理_1.md", "mineru_2024_物理_2.md", "mineru_2024_物理_3.md"]),
    ]:
        rank_df = load_rank_table(subject, 2024)
        all_rows = []
        for fname in files:
            p = OCR_DIR / fname
            rows = parse_md_file(p, 2024, subject)
            for r in rows:
                r["min_rank"] = score_to_rank(r["min_score"], rank_df)
            print(f"  {p.name}: 抽出 {len(rows)} 行")
            all_rows.extend(rows)
        # 修 group_id
        all_rows = fixup_group_id(all_rows, subject)
        # Dedup on (school_name, group_id)
        seen = set()
        deduped = []
        for r in all_rows:
            key = (r["school_name"], r["group_id"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        df = pd.DataFrame(deduped)
        out = DATA_DIR / f"hubei_admission_{subject}_2024_real_mineru.csv"
        df.to_csv(out, index=False)
        print(f"📦 {out.name}: {len(df)} 行 (raw {len(all_rows)} 去重 {len(all_rows) - len(deduped)})")
        summary[subject] = len(df)
    return summary


if __name__ == "__main__":
    main()
