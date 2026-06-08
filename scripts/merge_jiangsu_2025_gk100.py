"""
scripts/merge_jiangsu_2025_gk100.py — 合并 gk100 真实数据进 江苏 2025 主表

JS 2025 之前不存在 admission CSV. 本脚本从无到有创建:
  data/jiangsu_admission_{物理|历史}_2025.csv

源:
- gk100 TOP100 真实: data/jiangsu_admission_{物理|历史}_2025_real_gk100.csv
  (来自 parse_gk100_js_2025.py 解析 read_362938512.htm)

策略: 因为 JS 2025 之前是空, 直接用 gk100 TOP100 真值作为主表 floor.
后续如有 eol.cn 2025 / jseea 2025 XLS, 可参照 merge_hubei_2025_gk100.py 加多源.

JS schema 注意点:
- group_id 2 位零填充 ("05")
- group_code 保留原文 "05组" / "05组(中外合作)" / "01组(内地香港合作办学)"
- xuanke_req 简表默认 "不限" (TOP100 几乎都是高分不限组, 实际选科以 jseea 官方为准)
- is_special 由 group_code 后缀关键词检测
- min_rank 含 "126以内" → 估计值 (calibration 用, 不影响 score-only 模型)
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
    # group_id: 从 "05组" / "05组(中外合作)" 提取 2 位
    gids = df_gk["group_code"].apply(
        lambda c: (re.search(r"(\d+)组", str(c)) or re.match(r"(\d+)", str(c))).group(1).zfill(2)
        if (re.search(r"(\d+)组", str(c)) or re.match(r"(\d+)", str(c))) else "01"
    )
    out["group_id"] = gids
    out["group_code"] = df_gk["group_code"]
    out["xuanke_req"] = df_gk["xuanke_req"].fillna("不限")
    out["xuanke_subjects"] = out["xuanke_req"].apply(_xuanke_subjects_from_req)
    out["plan_count"] = 0  # gk100 TOP100 不给计划数
    out["min_score"] = df_gk["min_score"].astype(int)
    out["min_rank"] = df_gk["min_rank"].astype(int).clip(lower=0)
    out["tuition_yuan"] = 5500  # 默认值, 真实值需校核
    out["city"] = df_gk["school_name"].apply(get_school_city)
    out["is_special"] = df_gk["is_special"].fillna("否")
    out["data_source"] = "gk100 TOP100"
    return out


def create_main(subject: str) -> int:
    print(f"\n=== {subject} ===")
    gk_path = DATA_DIR / f"jiangsu_admission_{subject}_2025_real_gk100.csv"
    if not gk_path.exists():
        print(f"  ⚠️ 缺失 {gk_path.name}, 跑 parse_gk100_js_2025.py 先生成")
        return 0
    gk_raw = pd.read_csv(gk_path)
    gk_norm = _normalize_gk100(gk_raw)
    print(f"  gk100 TOP100 真实: {len(gk_norm)} 行")
    if gk_norm.empty:
        return 0

    out = DATA_DIR / f"jiangsu_admission_{subject}_2025.csv"
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
            print(f"  {s}: {n} 行真实数据 (JS 2025 新建, gk100 TOP100 floor)")


if __name__ == "__main__":
    main()
