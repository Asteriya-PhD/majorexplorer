"""
scripts/merge_guangdong_2025_gk100.py — 合并 gk100 真实数据进 广东 2025 主表

GD 2025 之前不存在 admission CSV. 本脚本从无到有创建:
  data/guangdong_admission_{物理|历史}_2025.csv

源:
- gk100 真实: data/guangdong_admission_{物理|历史}_2025_real_gk100.csv
  (来自 parse_gk100_gd_2025.py 解析 OCR 输出)

策略: 因为 GD 2025 之前是空, 直接用 gk100 真值作为主表.
如未来加其他源 (eol.cn / 555edu), 可参照 merge_hubei_2025_gk100.py 加多源.
"""
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from merge_real_2024 import (  # noqa: E402
    get_school_type, get_school_city,
)

DATA_DIR = PROJECT_DIR / "data"


def _group_id_from_code(group_code: str) -> str:
    """从 '221组' / '201组(内地香港合作办学)' 提取 group_id."""
    m = re.search(r"(\d+)组", str(group_code))
    if m:
        return m.group(1).zfill(2)
    return "01"


def _xuanke_subjects_from_req(xuanke_req: str) -> str:
    if not xuanke_req or "不限" in xuanke_req:
        return "不限"
    return xuanke_req.replace("+", "|")


def _normalize_gk100(df_gk: pd.DataFrame) -> pd.DataFrame:
    if df_gk.empty:
        return df_gk
    out = pd.DataFrame()
    out["year"] = 2025
    out["subject"] = df_gk["subject"]
    out["school_name"] = df_gk["school_name"]
    out["school_type"] = df_gk["school_name"].apply(get_school_type)
    out["group_id"] = df_gk["group_code"].apply(_group_id_from_code)
    out["group_code"] = df_gk["group_code"]
    out["xuanke_req"] = df_gk["xuanke_req"].fillna("不限")
    out["xuanke_subjects"] = out["xuanke_req"].apply(_xuanke_subjects_from_req)
    out["plan_count"] = df_gk["plan_count"].fillna(0).astype(int)
    out["min_score"] = df_gk["min_score"].astype(int)
    out["min_rank"] = df_gk["min_rank"].astype(int).clip(lower=0)
    out["tuition_yuan"] = 5500
    out["city"] = df_gk["school_name"].apply(get_school_city)
    out["is_special"] = df_gk["is_special"].fillna("否")
    out["data_source"] = "gk100 真实"
    return out


def create_main(subject: str) -> int:
    print(f"\n=== {subject} ===")
    gk_path = DATA_DIR / f"guangdong_admission_{subject}_2025_real_gk100.csv"
    if not gk_path.exists():
        print(f"  ⚠️ 缺失 {gk_path.name}, 跑 parse_gk100_gd_2025.py 先生成")
        return 0
    gk_raw = pd.read_csv(gk_path)
    gk_norm = _normalize_gk100(gk_raw)
    print(f"  gk100 真实: {len(gk_norm)} 行")
    if gk_norm.empty:
        return 0

    out = DATA_DIR / f"guangdong_admission_{subject}_2025.csv"
    gk_norm.to_csv(out, index=False)
    print(f"  ✅ 写入 {out.name} ({len(gk_norm)} 行)")
    scores = gk_norm["min_score"]
    ranks = gk_norm["min_rank"]
    print(f"  📊 score range: {scores.min()}-{scores.max()}, median {scores.median():.0f}")
    print(f"  📊 rank range: {ranks.min()}-{ranks.max()}, median {ranks.median():.0f}")
    return len(gk_norm)


def main():
    summary = {}
    for subject in ["物理", "历史"]:
        summary[subject] = create_main(subject)
    print("\n=== 总结 ===")
    for s, n in summary.items():
        if n:
            print(f"  {s}: {n} 行真实数据 (GD 2025 新建)")


if __name__ == "__main__":
    main()
