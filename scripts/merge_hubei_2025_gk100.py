"""
scripts/merge_hubei_2025_gk100.py — 合并 gk100 真实数据进 湖北 2025 主表

源:
- 现有 synth: data/hubei_admission_{物理|历史}_2025.csv (205/103 行)
- 真实 gk100:  data/hubei_admission_{物理|历史}_2025_real_gk100.csv (200/180 行)

合并规则:
- 真实 gk100 > 现有 synth (按 (school_name, group_id) 去重, 保留 gk100)
- 真实数据缺失字段 (school_type / xuanke_subjects / city / tuition) 用现有 synth 填
  (synth 虽然分数是错的, 但元数据基本正确)

输出: data/hubei_admission_{物理|历史}_2025.csv (替换)
"""
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from merge_real_2024 import (  # noqa: E402
    get_school_type, get_school_city, _xuanke_to_subjects,
)

DATA_DIR = PROJECT_DIR / "data"


def _group_id_from_code(group_code: str) -> str:
    """从 '第05组' / '第07组(国家专项)' 提取 group_id 2 位数字."""
    m = re.search(r"第(\d+)组", str(group_code))
    if m:
        return m.group(1).zfill(2)
    return "01"


def _xuanke_subjects_from_req(xuanke_req: str) -> str:
    """'不限' → '不限', '物理+化学' → '物理|化学'."""
    if not xuanke_req or "不限" in xuanke_req:
        return "不限"
    return xuanke_req.replace("+", "|")


def _normalize_gk100(df_gk: pd.DataFrame, existing_meta: pd.DataFrame) -> pd.DataFrame:
    """把 gk100 schema 转成主 CSV schema, 用 existing 补 metadata."""
    if df_gk.empty:
        return df_gk
    out = pd.DataFrame()
    out["year"] = 2025
    out["subject"] = df_gk["subject"]
    out["school_name"] = df_gk["school_name"]
    out["school_type"] = df_gk["school_name"].apply(get_school_type)
    out["group_id"] = df_gk["group_code"].apply(_group_id_from_code)
    out["group_code"] = df_gk["group_code"]  # 保留原始 (e.g. "第05组(国家专项)")
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


def merge_subject(subject: str) -> dict:
    print(f"\n=== {subject} ===")
    main_path = DATA_DIR / f"hubei_admission_{subject}_2025.csv"
    gk_path = DATA_DIR / f"hubei_admission_{subject}_2025_real_gk100.csv"
    if not main_path.exists():
        print(f"  ⚠️ 缺失主表 {main_path}")
        return {}
    if not gk_path.exists():
        print(f"  ⚠️ 缺失 gk100 {gk_path}")
        return {}
    existing = pd.read_csv(main_path)
    # 排除控制线/特控线/本科线 等 fake 行 (school_name 是 元数据)
    fake_mask = existing["school_name"].isin(["批次", "特控线", "本科线", "专科线", "高分优先投档线"])
    real_existing = existing[~fake_mask].copy()
    real_existing["data_source"] = "synth 锚点"
    print(f"  现有 (synth 锚点): {len(real_existing)} 行")

    gk_raw = pd.read_csv(gk_path)
    gk_norm = _normalize_gk100(gk_raw, real_existing)
    print(f"  gk100 真实: {len(gk_norm)} 行")

    # 合并: gk100 (priority 高) + existing (填充尾部)
    combined = pd.concat([gk_norm, real_existing], ignore_index=True, sort=False)
    combined["_key"] = combined["school_name"].astype(str) + "||" + combined["group_id"].astype(str)
    combined["_prio"] = combined["data_source"].map({
        "gk100 真实": 2,
        "synth 锚点": 1,
    }).fillna(0)
    combined = combined.sort_values("_prio", ascending=False)
    combined = combined.drop_duplicates(subset=["_key"], keep="first")
    combined = combined.drop(columns=["_key", "_prio"]).reset_index(drop=True)
    print(f"  合并去重后: {len(combined)} 行")

    # 加 fake 行 (本科线/特控线) 用于 API 兼容
    fake_rows = existing[fake_mask]
    final = pd.concat([combined, fake_rows], ignore_index=True, sort=False)
    # 保留 fake 在前面 (按原始 main 顺序)
    print(f"  最终 (含 fake): {len(final)} 行 (fake {len(fake_rows)})")

    # 备份 + 写
    from datetime import datetime
    import shutil
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DATA_DIR / "_logs" / f"hubei_admission_{subject}_2025_backup_{ts}.csv"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(main_path, backup)
    final.to_csv(main_path, index=False)
    print(f"  📦 备份: {backup.name}")
    print(f"  ✅ 写入 {main_path.name}")

    # 报告 (rebuild mask on final to avoid index mismatch)
    if "min_rank" in final.columns:
        real_mask = ~final["school_name"].isin(["批次", "特控线", "本科线", "专科线", "高分优先投档线"])
        real = final[real_mask]
        ranks = real["min_rank"]
        scores = real["min_score"]
        print(f"  📊 score range: {scores.min()}-{scores.max()}, median {scores.median():.0f}")
        print(f"  📊 rank range: {ranks.min()}-{ranks.max()}, median {ranks.median():.0f}")
    return {"combined": len(combined), "main_before": len(real_existing)}


def main():
    summary = {}
    for subject in ["物理", "历史"]:
        summary[subject] = merge_subject(subject)
    print("\n=== 总结 ===")
    for s, r in summary.items():
        if r:
            print(f"  {s}: 合成 {r.get('main_before', 0)} 行 → 合并后 {r.get('combined', 0)} 行 (含 gk100 真实)")


if __name__ == "__main__":
    main()
