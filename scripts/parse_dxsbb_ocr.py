"""
scripts/parse_dxsbb_ocr.py — 解析 dxsbb PNG OCR 文本 (v5, PSM 4 + rank 表反查)

输入: data/_cache/dxsbb_imgs/ocr_2024_{hist,phys}_{1,2,3}_v3.txt
  (用 tesseract --psm 4 在 2x 高清图上重 OCR 得到)
输出: data/hubei_admission_历史_2024_real_dxsbb_ocr.csv
      data/hubei_admission_物理_2024_real_dxsbb_ocr.csv

v5 改进:
  - rank 不用 OCR (OCR rank 经常错位到同分排序项), 用 hubei_rank_{subject}_{year}.csv 反查
  - group_id 出现 "00" 时 (OCR 漏掉首数字), 试从 6261 真实表匹配
  - 接受 OCR 漏分 (hist_3 / phys_3 ~50% 漏) 的局限, 优先保证质
"""
import re
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
OCR_DIR = DATA_DIR / "_cache" / "dxsbb_imgs"
DXSBB_6261_FILE = "hubei_admission_{subject}_{year}_real_dxsbb6261.csv"

# 校名 + 第NN组 (校名只含 中文+括号+点+空格; 第NN组中 NN 可 1-2 位)
SCHOOL_GROUP_PAT = re.compile(r"([一-龥（）()·\s]{2,20}?)第(\d{1,2})组")

# group_code: A + 5 数字 (允许 l/1, O/0 误识)
GROUP_CODE_PAT = re.compile(r"\b([Aa][Oo]?[Il1]?\d{4})\b")

# 再选科 关键词 (长→短优先)
XUANKE_KEYWORDS = ["不限", "化学", "生物", "地理", "政治", "化", "生", "地", "政"]

# 投档线 (3 位, 400-700)
SCORE_PAT = re.compile(r"\b([4-7]\d{2})\b")

# 位次 (1-6 位, 1-200000)
RANK_PAT = re.compile(r"\b([1-9]\d{0,5})\b")

# 备注 → is_special = "是"
SPECIAL_KW = [
    "国家专项", "专项计划", "少数民族预科", "预科班", "R班", "ER班",
    "中外合作", "联培", "校区", "分校", "民族班", "小语种", "马来西亚",
]

# OCR 误识 "不限" 的常见形式 (PSM 6 输出: "me", "am", "eR", "mE" 等)
LIMITED_GARBAGE = re.compile(r"^(me|am|eR|mE|sk|mt|em|am|aw|at|st|au|MT|AM|EM|ET|ME)$")


def detect_xuanke_from_cells(cells: list[str]) -> str:
    """在 cells 中找 再选科. 长词优先, 完整词 "不限" 优先. 噪声 cell 默认 不限."""
    for c in cells:
        cs = c.strip()
        if not cs or len(cs) > 6:  # 跳过非 token 长 cell
            continue
        # 限短 cell 找 关键词
        for kw in XUANKE_KEYWORDS:
            if kw in cs:
                if kw in ("化学", "生物", "地理", "政治", "不限"):
                    return kw
                return {"化": "化学", "生": "生物", "地": "地理", "政": "政治"}[kw]
    return "不限"


def detect_special(line: str) -> str:
    return "是" if any(kw in line for kw in SPECIAL_KW) else "否"


def extract_school_and_group(line: str) -> tuple[str, str] | None:
    """从整行提取 (校名, 组号). 校名 = 校名第NN组 中的中文段. 1 位组号 → 0N."""
    m = SCHOOL_GROUP_PAT.search(line)
    if not m:
        return None
    school_name = m.group(1).strip()
    # 校名至少 3 个汉字 (三峡=2 汉字, 允许)
    cn_count = len(re.sub(r"[^一-龥]", "", school_name))
    if cn_count < 2:
        return None
    group_id = m.group(2).zfill(2)
    return school_name, group_id


def extract_score_rank_from_cells(cells: list[str], subject: str) -> tuple[int | None, int | None]:
    """从 cells 找 投档线. 位次不用 OCR (错位多), 调用方从 rank 表反查."""
    score_min = 400
    score_max = 700 if subject == "物理" else 650
    score = None
    for c in cells:
        cs = c.strip()
        if not cs:
            continue
        for m in SCORE_PAT.finditer(cs):
            v = int(m.group(1))
            if score_min <= v <= score_max:
                score = v
                break
        if score is not None:
            break
    return score, None


def load_rank_table(subject: str, year: int = 2024) -> pd.DataFrame:
    """加载 一分一段表. 返回按 score 升序的 DataFrame."""
    f = DATA_DIR / f"hubei_rank_{subject}_{year}.csv"
    if not f.exists():
        return pd.DataFrame()
    df = pd.read_csv(f)
    # 标准化 score 列 (可能有 "695-750" 范围)
    def parse_score(s):
        s = str(s).strip()
        if "-" in s:
            return int(s.split("-")[0])
        try:
            return int(s)
        except (ValueError, TypeError):
            return -1
    df["_score_int"] = df["score"].apply(parse_score)
    df = df[df["_score_int"] >= 0].copy()
    return df


def score_to_rank(score: int, rank_df: pd.DataFrame) -> int | None:
    """投档线 → 位次. 取该分数对应的累计人数."""
    if rank_df.empty:
        return None
    rows = rank_df[rank_df["_score_int"] == score]
    if rows.empty:
        # 取最近的更低分
        rows = rank_df[rank_df["_score_int"] < score]
        if rows.empty:
            return None
        return int(rows.iloc[-1]["rank"])
    return int(rows.iloc[0]["rank"])


def extract_group_code(line: str) -> str:
    m = GROUP_CODE_PAT.search(line)
    if not m:
        return ""
    return m.group(1).upper().replace("O", "0").replace("L", "1").replace("I", "1")


def parse_line(line: str, year: int, subject: str) -> dict | None:
    """解析单行. 失败返回 None."""
    line = line.strip()
    if not line or "|" not in line:
        return None
    # 1. 校名+组号
    sg = extract_school_and_group(line)
    if not sg:
        return None
    school_name, group_id = sg
    # 2. 切 cell
    cells = [c.strip() for c in line.split("|")]
    cells = [c for c in cells if c]  # 去空
    # 3. 再选科
    xuanke_req = detect_xuanke_from_cells(cells)
    # 4. 投档线 (位次不用 OCR, 由 main() 用 rank 表反查)
    score, _ = extract_score_rank_from_cells(cells, subject)
    if score is None:
        return None
    # 5. group_code
    group_code = extract_group_code(line)
    # 6. is_special
    is_special = detect_special(line)
    return {
        "year": year,
        "subject": subject,
        "school_name": school_name,
        "group_id": group_id,
        "group_code": group_code,
        "min_score": score,
        "min_rank": 0,  # 由 main() 后填
        "is_special": is_special,
    }


def parse_file(ocr_txt: Path, year: int, subject: str) -> list[dict]:
    raw = ocr_txt.read_text(encoding="utf-8", errors="replace")
    rows: list[dict] = []
    for line in raw.split("\n"):
        rec = parse_line(line, year, subject)
        if rec:
            rows.append(rec)
    return rows


def fixup_group_id(rows: list[dict], subject: str, year: int = 2024) -> list[dict]:
    """group_id="00" (OCR 漏首字) 时, 试从 dxsbb 6261 表匹配同校真实组号."""
    ref_path = DATA_DIR / DXSBB_6261_FILE.format(subject=subject, year=year)
    if not ref_path.exists():
        return rows
    ref = pd.read_csv(ref_path)
    # ref: school_name, group_id (clean)
    real_pairs = set(zip(ref["school_name"], ref["group_id"].astype(str).str.zfill(2)))
    for r in rows:
        if r["group_id"] != "00":
            continue
        school = r["school_name"]
        # 同校有多个真实组号, 取第一个
        candidates = [g for (s, g) in real_pairs if s == school]
        if candidates:
            r["group_id"] = sorted(candidates)[0]  # 默认取最小
    return rows


def main():
    summary = {}
    for subject, files in [
        ("历史", ["ocr_2024_hist_1_v3.txt", "ocr_2024_hist_2_v3.txt", "ocr_2024_hist_3_v3.txt"]),
        ("物理", ["ocr_2024_phys_1_v3.txt", "ocr_2024_phys_2_v3.txt", "ocr_2024_phys_3_v3.txt"]),
    ]:
        # 加载 rank 表 (用于 score → rank)
        rank_df = load_rank_table(subject, 2024)
        all_rows: list[dict] = []
        for fname in files:
            p = OCR_DIR / fname
            if not p.exists():
                print(f"  ⚠️  {p.name} 缺失")
                continue
            rows = parse_file(p, 2024, subject)
            # score → rank
            for r in rows:
                rank = score_to_rank(r["min_score"], rank_df)
                if rank is not None:
                    r["min_rank"] = rank
            print(f"  {p.name}: 抽出 {len(rows)} 行")
            all_rows.extend(rows)
        # 修 group_id="00"
        all_rows = fixup_group_id(all_rows, subject)
        # Dedup on (school_name, group_id)
        seen: set = set()
        deduped = []
        for r in all_rows:
            key = (r["school_name"], r["group_id"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        df = pd.DataFrame(deduped)
        out = DATA_DIR / f"hubei_admission_{subject}_2024_real_dxsbb_ocr.csv"
        df.to_csv(out, index=False)
        print(f"📦 {out.name}: {len(df)} 行 (raw {len(all_rows)} 去重 {len(all_rows) - len(deduped)})")
        summary[subject] = len(df)
    return summary


if __name__ == "__main__":
    main()
