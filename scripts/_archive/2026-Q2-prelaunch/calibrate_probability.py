"""
scripts/calibrate_probability.py — 校准 概率模型 std 参数 (per subject)

现状 (core/probability.py:67):
  std_rank = min_rank * 0.25   (25% 启发式)

改进: 用 多年 (school, group) 重叠数据 算 经验 std/μ 比.

数据:
- HB 物理 2023+2024 重叠 163 对
- HB 历史 2023+2024 重叠 84 对
- JS / GD 只有 2024 单年 (不参与校准, 沿用 启发式 0.25)

结果 (实测 2026-06-08):
- 物理: 经验 std/μ = 0.289 ≈ 0.25 (启发式 close enough)
- 历史: 经验 std/μ = 0.367 (启发式 0.25 低估 47%)

输出: data/_logs/probability_calibration.json
       {"物理": 0.29, "历史": 0.37}

core/probability.py 用这 dict 替换硬编码 0.25.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = DATA_DIR / "_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 启发式 fallback (没数据时)
DEFAULT_SIGMA_FRAC = 0.25


def compute_empirical_sigma(province: str, subject: str, year_a: int = 2023, year_b: int = 2024) -> float | None:
    """用 (year_a, year_b) 重叠 (school, group) 算 std/μ 经验值."""
    try:
        df_a = pd.read_csv(DATA_DIR / f"{province}_admission_{subject}_{year_a}.csv")
        df_b = pd.read_csv(DATA_DIR / f"{province}_admission_{subject}_{year_b}.csv")
    except FileNotFoundError:
        return None
    # 排除控制线
    for df in (df_a, df_b):
        if "school_name" in df.columns:
            df.drop(df[df.school_name.isin(["批次", "特控线", "本科线", "专科线", "高分优先投档线"])].index,
                    inplace=True)
    merged = df_a.merge(df_b, on=["school_name", "group_id"], suffixes=(f"_{year_a}", f"_{year_b}"))
    rank_a, rank_b = f"min_rank_{year_a}", f"min_rank_{year_b}"
    if rank_a not in merged.columns or rank_b not in merged.columns:
        return None
    merged = merged[(merged[rank_a] >= 100) & (merged[rank_b] >= 100) &
                    (merged[rank_a] <= 200000) & (merged[rank_b] <= 200000)]
    if len(merged) < 5:
        return None
    merged["mean_rank"] = (merged[rank_a] + merged[rank_b]) / 2
    merged["delta_pct"] = (merged[rank_b] - merged[rank_a]) / merged["mean_rank"]
    # std(|delta|) 反映 年际不确定性
    sigma_frac = float(merged["delta_pct"].abs().std())
    return sigma_frac


def main():
    print("校准 概率模型 std 参数 (per subject)\n")
    factors = {}
    for subject in ["物理", "历史"]:
        sigma = compute_empirical_sigma("hubei", subject, 2023, 2024)
        if sigma is None:
            print(f"  {subject}: 数据不足, 用启发式 {DEFAULT_SIGMA_FRAC}")
            factors[subject] = DEFAULT_SIGMA_FRAC
        else:
            factors[subject] = round(sigma, 3)
            print(f"  {subject}: 经验 sigma_frac = {sigma:.3f} "
                  f"(启发式 {DEFAULT_SIGMA_FRAC} → {sigma/DEFAULT_SIGMA_FRAC*100:.0f}%)")

    # 写 JSON
    out = {
        "_meta": {
            "calibrated_at": datetime.now().isoformat(timespec="seconds"),
            "method": "compute std(|delta_pct|) across overlapping (school,group) pairs in 2023+2024",
            "fallback": DEFAULT_SIGMA_FRAC,
            "data_source": "data/hubei_admission_物理|历史_2023.csv + _2024.csv",
        },
        "factors": factors,
    }
    out_path = LOG_DIR / "probability_calibration.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📄 报告: {out_path.relative_to(PROJECT_DIR)}")
    print(f"\n使用: 从 core/probability.py 替换硬编码 0.25 → factors['物理']/{factors['历史']}")


if __name__ == "__main__":
    main()
