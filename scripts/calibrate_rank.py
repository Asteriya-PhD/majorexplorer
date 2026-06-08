"""
scripts/calibrate_rank.py — 校准 合成 rank 表 vs 真实投档位次

用 GD eea.gd 真实投档表 (3054 物理 + 1446 历史, 2024) 反查
score_to_rank, 对比真实 min_rank 与合成 rank 表输出.

输出:
- 总体偏差: median/mean/std (real_rank - synth_rank)
- 分段偏差: per 50 分 区间 (450-500, 500-550, ...)
- 偏差方向: 偏小 (synth 高估) / 偏大 (synth 低估)
- 修正建议: log_ratio = log10(real / synth), 作为校准系数
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from core.rank_utils import score_to_rank

DATA_DIR = PROJECT_DIR / "data"
REPORT_PATH = DATA_DIR / "_logs" / "rank_calibration_2024_guangdong.md"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def calibrate(province: str, subject: str, year: int = 2024) -> dict:
    src = DATA_DIR / f"{province}_admission_{subject}_{year}_real_eeagd.csv"
    df = pd.read_csv(src)
    df = df[(df["min_score"] >= 400) & (df["min_score"] <= 700) & (df["min_rank"] >= 1)].copy()
    print(f"\n=== {province} {subject} {year} ===")
    print(f"  数据: {len(df)} 行 (score 400-700, rank≥1)")

    synth_ranks, real_ranks, scores = [], [], []
    for _, r in df.iterrows():
        s = int(r["min_score"])
        synth = score_to_rank(s, province, subject, year)
        synth_ranks.append(synth)
        real_ranks.append(int(r["min_rank"]))
        scores.append(s)
    df["synth_rank"] = synth_ranks
    df["diff"] = df["min_rank"] - df["synth_rank"]
    df["log_ratio"] = np.log10(df["min_rank"] / df["synth_rank"].clip(lower=1))

    # 总体
    overall = {
        "n": len(df),
        "median_diff": float(df["diff"].median()),
        "mean_diff": float(df["diff"].mean()),
        "std_diff": float(df["diff"].std()),
        "median_log_ratio": float(df["log_ratio"].median()),
        "mean_log_ratio": float(df["log_ratio"].mean()),
    }
    print(f"  overall: median_diff={overall['median_diff']:+.0f} | "
          f"median_log_ratio={overall['median_log_ratio']:+.3f} "
          f"(10^x = {10**overall['median_log_ratio']:.3f}x)")

    # 分段 (50 分 区间)
    bands = []
    edges = list(range(400, 751, 50))
    for lo, hi in zip(edges, edges[1:]):
        sub = df[(df["min_score"] >= lo) & (df["min_score"] < hi)]
        if sub.empty:
            continue
        band = {
            "score_band": f"{lo}-{hi}",
            "n": len(sub),
            "median_diff": float(sub["diff"].median()),
            "median_log_ratio": float(sub["log_ratio"].median()),
            "p10_diff": float(sub["diff"].quantile(0.10)),
            "p90_diff": float(sub["diff"].quantile(0.90)),
        }
        bands.append(band)
        print(f"  band {band['score_band']:>10}: n={band['n']:>4} | "
              f"median_diff={band['median_diff']:+.0f} | "
              f"log10={band['median_log_ratio']:+.3f} ({10**band['median_log_ratio']:.2f}x) | "
              f"p10/p90=({band['p10_diff']:+.0f}/{band['p90_diff']:+.0f})")
    return {"subject": subject, "overall": overall, "bands": bands, "df": df}


def main():
    results = {}
    for subject in ["物理", "历史"]:
        results[subject] = calibrate("guangdong", subject, 2024)

    # 写报告
    lines = ["# 广东 2024 真实 vs 合成 rank 表 校准报告", ""]
    lines.append("**数据源**: `data/guangdong_admission_{物理|历史}_2024_real_eeagd.csv` (eea.gd 官方)")
    lines.append("")
    lines.append("**校准对象**: `data/guangdong_rank_{物理|历史}_2024.csv` (一分一段表, 合成)")
    lines.append("")
    lines.append("**方法**: 对每条 (min_score, min_rank) 记录, 用合成表 `score_to_rank(min_score)` "
                 "得到 synth_rank, 计算 diff = real - synth. 正值=合成低估 (真实位次比合成的差/靠后), "
                 "负值=合成高估 (真实位次比合成的优/靠前).")
    lines.append("")

    for subject, r in results.items():
        o = r["overall"]
        lines.append(f"## {subject}")
        lines.append("")
        lines.append(f"- 样本数: **{o['n']}**")
        lines.append(f"- median diff: **{o['median_diff']:+.0f}** 名次")
        lines.append(f"- mean diff: {o['mean_diff']:+.0f} (受极值影响)")
        lines.append(f"- std: {o['std_diff']:+.0f}")
        lines.append(f"- median log10(real/synth): **{o['median_log_ratio']:+.3f}** "
                     f"(10^x = {10**o['median_log_ratio']:.3f}x, 即合成位次 "
                     f"{'低估' if o['median_log_ratio'] > 0 else '高估'}真实位次 "
                     f"{abs(1 - 10**o['median_log_ratio'])*100:.1f}%)")
        lines.append("")
        lines.append("| score band | n | median diff | p10 | p90 | log10(med) | 倍数 |")
        lines.append("|---|---|---|---|---|---|---|")
        for b in r["bands"]:
            mult = 10**b["median_log_ratio"]
            lines.append(f"| {b['score_band']} | {b['n']} | "
                         f"{b['median_diff']:+.0f} | {b['p10_diff']:+.0f} | {b['p90_diff']:+.0f} | "
                         f"{b['median_log_ratio']:+.3f} | {mult:.2f}x |")
        lines.append("")

    # 修正建议
    lines.append("## 修正建议")
    lines.append("")
    lines.append("如果 median_log_ratio 系统性偏离 0, 表明合成 rank 表需要校准.")
    lines.append("建议校准公式 (per-subject, per-band):")
    lines.append("")
    lines.append("```python")
    lines.append("def calibrated_score_to_rank(score, province, subject, year):")
    lines.append("    raw = score_to_rank(score, province, subject, year)")
    lines.append("    # 校准系数 (从本报告抄)")
    lines.append("    band = score // 50 * 50  # 50-分一段")
    lines.append("    factor = CALIBRATION_FACTORS.get((province, subject, band), 1.0)")
    lines.append("    return int(raw * factor)")
    lines.append("```")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 报告写入: {REPORT_PATH.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()
