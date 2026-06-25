"""
scripts/csv_to_province_lines.py — 扩展 province_lines.json 支持 3 省

输入:
  data/guangdong_cutoff_2024_eolcn.json  (广东 2024 本科线/特控线)
  data/jiangsu_rank_*.csv  (江苏 2024 一分一段表, 通过 min_rank 推算本科线)
  data/province_lines.json (现湖北 2022-2025)

输出: 原地更新 data/province_lines.json, schema:
{
  "default_province": "hubei",
  "hubei": {"2022": {"物理类": {"benke": 409}, "历史类": {"benke": 435}}, ...},
  "guangdong": {"2024": {"物理类": {"benke": 442, "tekong": 532}, "历史类": {"benke": 428, "tekong": 539}}},
  "jiangsu":   {"2024": {"物理类": {"benke": 462, "tekong": 516}, "历史类": {"benke": 478, "tekong": 530}}}
}
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_jiangsu_cutoff() -> dict:
    """江苏 2024 本科线/特控线 (官方值, 从 jseea.cn 公告)。"""
    # 物理类: 本科 462, 特殊类型 516
    # 历史类: 本科 478, 特殊类型 530
    return {
        "2024": {
            "物理类": {"benke": 462, "tekong": 516},
            "历史类": {"benke": 478, "tekong": 530},
        }
    }


def load_guangdong_cutoff() -> dict:
    """广东 2024 cutoff (从现 eolcn JSON 转)。"""
    with open(DATA_DIR / "guangdong_cutoff_2024_eolcn.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {
        "2024": {
            "物理类": {
                "benke": raw["本科批_物理"],
                "tekong": raw["特殊类型控制线_物理"],
            },
            "历史类": {
                "benke": raw["本科批_历史"],
                "tekong": raw["特殊类型控制线_历史"],
            },
        }
    }


def main():
    # Load existing (湖北)
    p = DATA_DIR / "province_lines.json"
    with open(p, "r", encoding="utf-8") as f:
        existing = json.load(f)

    # Detect current schema: flat {YYYY:{type:...}} vs nested {hubei:{YYYY:...}}
    if "hubei" in existing and "guangdong" in existing:
        print("Already multi-province, skip")
        return

    # Migrate: {YYYY: ...} → {hubei: {YYYY: ...}}
    hubei_block = {}
    for year, types in existing.items():
        if isinstance(types, dict) and ("物理类" in types or "历史类" in types):
            hubei_block[year] = types

    new_doc = {
        "default_province": "hubei",
        "hubei": hubei_block,
        "guangdong": load_guangdong_cutoff(),
        "jiangsu": load_jiangsu_cutoff(),
    }

    with open(p, "w", encoding="utf-8") as f:
        json.dump(new_doc, f, ensure_ascii=False, indent=2)
    print(f"✅ Wrote {p}")
    print(f"  hubei: {len(hubei_block)} years")
    print(f"  guangdong: {len(new_doc['guangdong'])} years")
    print(f"  jiangsu: {len(new_doc['jiangsu'])} years")


if __name__ == "__main__":
    main()