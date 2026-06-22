"""
scripts/calibrate_rank.py — 校准 合成 rank 表 vs 真实投档位次

模式 1: eea.gd 投档表 (GD) — 完整 (3054 物理 + 1446 历史)
模式 2: sparse 锚点 (JS) — 用 8 个真实 anchor (sina/官方发布)

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
REPORT_PATH = DATA_DIR / "_logs" / "rank_calibration_2024.md"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def calibrate_full(province: str, subject: str, year: int = 2024) -> dict:
    """完整投档表反查 — 仅 GD 可用 (eea.gd 有真 min_rank)."""
    src = DATA_DIR / f"{province}_admission_{subject}_{year}_real_eeagd.csv"
    df = pd.read_csv(src)
    df = df[(df["min_score"] >= 400) & (df["min_score"] <= 700) & (df["min_rank"] >= 1)].copy()
    print(f"\n=== {province} {subject} {year} (完整投档表) ===")
    print(f"  数据: {len(df)} 行 (score 400-700, rank≥1)")

    synth_ranks = [score_to_rank(int(s), province, subject, year) for s in df["min_score"]]
    df["synth_rank"] = synth_ranks
    df["diff"] = df["min_rank"] - df["synth_rank"]
    df["log_ratio"] = np.log10(df["min_rank"] / df["synth_rank"].clip(lower=1))

    overall = {
        "n": len(df),
        "median_diff": float(df["diff"].median()),
        "mean_diff": float(df["diff"].mean()),
        "std_diff": float(df["diff"].std()),
        "median_log_ratio": float(df["log_ratio"].median()),
    }
    print(f"  overall: median_diff={overall['median_diff']:+.0f} | "
          f"median_log_ratio={overall['median_log_ratio']:+.3f} (factor={10**overall['median_log_ratio']:.3f}x)")

    bands = []
    for lo, hi in zip(range(400, 751, 50), range(450, 751, 50)):
        sub = df[(df["min_score"] >= lo) & (df["min_score"] < hi)]
        if sub.empty:
            continue
        bands.append({
            "score_band": f"{lo}-{hi}",
            "n": len(sub),
            "median_diff": float(sub["diff"].median()),
            "median_log_ratio": float(sub["log_ratio"].median()),
        })
        b = bands[-1]
        print(f"  band {b['score_band']:>10}: n={b['n']:>4} | "
              f"median_diff={b['median_diff']:+.0f} | factor={10**b['median_log_ratio']:.2f}x")
    return {"mode": "full", "subject": subject, "overall": overall, "bands": bands}


def calibrate_anchors(province: str, subject: str, anchors: list[tuple], year: int = 2024) -> dict:
    """稀疏锚点校准 — 拿不到完整投档表时用 (e.g. JS 用 sina 发布 8 个 anchor)."""
    print(f"\n=== {province} {subject} {year} (稀疏锚点, {len(anchors)} 个) ===")
    rows = []
    for score, real_cum in anchors:
        synth = score_to_rank(score, province, subject, year)
        rows.append((score, real_cum, synth))
        print(f"  score={score:>3}: real={real_cum:>7} synth={synth:>7} "
              f"diff={real_cum - synth:+>7} factor={real_cum/synth:.2f}x")
    df = pd.DataFrame(rows, columns=["score", "real", "synth"])
    df["log_ratio"] = np.log10(df["real"] / df["synth"].clip(lower=1))
    return {
        "mode": "anchors",
        "subject": subject,
        "overall": {
            "n": len(df),
            "median_diff": float((df["real"] - df["synth"]).median()),
            "median_log_ratio": float(df["log_ratio"].median()),
        },
        "df": df,
    }


def main():
    results = {}
    # GD 完整 (eea.gd)
    for subject in ["物理", "历史"]:
        results[("guangdong", subject)] = calibrate_full("guangdong", subject, 2024)

    # JS 稀疏 (sina 2024-06-25 发布)
    # 来源: http://www.zgjssw.gov.cn/yaowen/202406/t20240625_8347277.shtml
    # 物理: 680+ = 371, 660+ = 2475, 640+ = 8014, 630+ = 12125, 600+ = 30768,
    #       570+ = 58417, 540+ = 93432, 462 (本科线) = 187958
    # 历史: 640+ = 327, 600+ = 4028, 580+ = 8377, 560+ = 14582, 530+ = 26805, 478+ = 50966
    js_phys_anchors = [
        (680, 371), (660, 2475), (640, 8014), (630, 12125),
        (600, 30768), (570, 58417), (540, 93432), (462, 187958),
    ]
    js_hist_anchors = [
        (640, 327), (600, 4028), (580, 8377),
        (560, 14582), (530, 26805), (478, 50966),
    ]
    for subject, anchors in [("物理", js_phys_anchors), ("历史", js_hist_anchors)]:
        results[("jiangsu", subject)] = calibrate_anchors("jiangsu", subject, anchors, 2024)

    # 写报告
    lines = ["# 2024 真实 vs 合成 rank 表 校准报告", ""]
    for prov in ["guangdong", "jiangsu"]:
        for subj in ["物理", "历史"]:
            r = results.get((prov, subj))
            if not r:
                continue
            lines.append(f"## {prov} {subj}")
            lines.append("")
            if r["mode"] == "full":
                o = r["overall"]
                lines.append(f"- 模式: 完整投档表 (n={o['n']})")
                lines.append(f"- median diff: **{o['median_diff']:+.0f}**")
                lines.append(f"- median log10: **{o['median_log_ratio']:+.3f}** (factor={10**o['median_log_ratio']:.3f}x)")
                lines.append("")
                lines.append("| band | n | median_diff | factor |")
                lines.append("|---|---|---|---|")
                for b in r["bands"]:
                    lines.append(f"| {b['score_band']} | {b['n']} | {b['median_diff']:+.0f} | {10**b['median_log_ratio']:.2f}x |")
            else:
                o = r["overall"]
                lines.append(f"- 模式: 稀疏锚点 (n={o['n']})")
                lines.append(f"- median diff: **{o['median_diff']:+.0f}**")
                lines.append(f"- median log10: **{o['median_log_ratio']:+.3f}** (factor={10**o['median_log_ratio']:.3f}x)")
                lines.append("")
                lines.append("| score | real | synth | diff | factor |")
                lines.append("|---|---|---|---|---|")
                df = r["df"]
                for _, row in df.iterrows():
                    lines.append(f"| {int(row['score'])} | {int(row['real'])} | {int(row['synth'])} | "
                                 f"{int(row['real']-row['synth']):+} | {row['real']/row['synth']:.2f}x |")
            lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 报告写入: {REPORT_PATH.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()

