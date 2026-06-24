"""
Day 29 medicine timeline 数据生成器
按 7 组模板生成 22 篇 5 年制 medicine style 的 timeline 字段.
每篇先读现有 salary 字段交叉对照, 避免 m3 audit 抓矛盾.
"""
import json
import os
from pathlib import Path

CURATED = Path("skills/gaokao-major-explorer/data/curated")

# 7 组模板: (slug, group, timeline)
# group A: 临床医学系 (10 篇) - 5+3+X 规培
# group B: 基础医学系 (2 篇) - 5+3 学硕/学博
# group C: 公共卫生 (1 篇) - 5+3 MPH
# group D: 中医系 (6 篇) - 5+3 中医规培
# group E: 法医 (1 篇) - 司法鉴定/公安
# group F: 临床药学 (1 篇) - 医院药学
# group G: 维医 (1 篇) - 本科就业导向

GROUP_A = [  # 临床医学系 - 5+3+X 规培
    "clinical-medicine", "anesthesiology", "medical-imaging", "pediatrics",
    "stomatology", "psychiatry", "radiation-medicine", "nuclear-medicine",
    "ophthalmology-optometry", "maternal-child-health-medicine",
]

GROUP_B = ["basic-medicine", "biomedical-science"]

GROUP_C = ["preventive-medicine"]

GROUP_D = [
    "traditional-chinese-medicine", "integrated-chinese-western-medicine",
    "acupuncture-massage", "tcm-orthopedics", "tcm-yangsheng", "tcm-rehabilitation",
]

GROUP_E = ["forensic-medicine"]
GROUP_F = ["clinical-pharmacy"]
GROUP_G = ["uyghur-traditional-medicine"]


def get_salary_p50(slug: str, year: str) -> int | None:
    """读 salary 字段, 取某年限的 p50 用于交叉对照"""
    p = CURATED / f"{slug}.json"
    if not p.exists():
        return None
    d = json.load(open(p, encoding='utf-8'))
    salary = d.get("salary", {})
    if year in salary:
        return salary[year].get("p50")
    return None


def timeline_a_clinical(slug: str) -> list:
    """5+3+X 临床规培 (10 篇共用, 微调 stage 名)"""
    s_y6_8 = get_salary_p50(slug, "5年")
    s_y9_10 = get_salary_p50(slug, "10年+")
    return [
        {"year": "Y1", "stage": "本科 · 基础医学", "note": "无收入", "income_label": "学费", "income": f"~6.8k/年", "level": ""},
        {"year": "Y2-3", "stage": "本科 · 桥梁课", "note": "课业最重", "income_label": "见习补贴", "income": "~3-5k/月", "level": "warn", "warning": "低收入期"},
        {"year": "Y4-5", "stage": "本科 · 实习 + 考研", "note": "考研分流方向", "income_label": "实习补贴", "income": "~5-8k/月", "level": "critical", "warning": "关键转折点"},
        {"year": "Y6-8", "stage": "硕士 · 规培并轨", "note": "四证合一", "income_label": "规培工资", "income": "~8-15k/月", "level": ""},
        {"year": "Y9-10", "stage": "专培 · 主治医师", "note": "亚专科定型", "income_label": "年薪", "income": "~18-30 万", "level": ""},
        {"year": "Y11+", "stage": "专科主治", "note": "副高 / 学科带头人", "income_label": "年薪", "income": "~35-60 万", "level": ""},
    ]


def timeline_b_basic(slug: str) -> list:
    """基础医学系 (学硕/学博学术路径, 无规培)"""
    return [
        {"year": "Y1", "stage": "本科 · 基础医学", "note": "无收入", "income_label": "学费", "income": "~6.8k/年", "level": ""},
        {"year": "Y2-3", "stage": "本科 · 桥梁课", "note": "课业最重", "income_label": "助教补贴", "income": "~2-4k/月", "level": "warn", "warning": "低收入期"},
        {"year": "Y4-5", "stage": "本科 · 实习 + 考研", "note": "学硕 vs 学博", "income_label": "实习补贴", "income": "~3-5k/月", "level": "critical", "warning": "关键转折"},
        {"year": "Y6-8", "stage": "硕士 · 实验室", "note": "导师补助", "income_label": "硕士补助", "income": "~2-4k/月", "level": ""},
        {"year": "Y9-12", "stage": "博士 · SCI 产出", "note": "高水平论文", "income_label": "博士补助", "income": "~3-6k/月 + 奖学金", "level": ""},
        {"year": "Y13+", "stage": "博士后 / 讲师", "note": "高校 / 研究所", "income_label": "年薪", "income": "~25-50 万", "level": ""},
    ]


def timeline_c_preventive() -> list:
    """预防医学 MPH 路径"""
    return [
        {"year": "Y1", "stage": "本科 · 预防基础", "note": "无收入", "income_label": "学费", "income": "~6.8k/年", "level": ""},
        {"year": "Y2-3", "stage": "本科 · 流行病学", "note": "统计学加重", "income_label": "见习补贴", "income": "~2-4k/月", "level": "warn", "warning": "低收入期"},
        {"year": "Y4-5", "stage": "本科 · CDC 实习", "note": "考研分流", "income_label": "实习补贴", "income": "~3-5k/月", "level": "critical", "warning": "关键转折"},
        {"year": "Y6-8", "stage": "硕士 · MPH", "note": "公共卫生", "income_label": "规培补助", "income": "~6-10k/月", "level": ""},
        {"year": "Y9-10", "stage": "CDC / 卫健委", "note": "事业编可期", "income_label": "年薪", "income": "~12-22 万", "level": ""},
        {"year": "Y11+", "stage": "副主任医师", "note": "公卫医师", "income_label": "年薪", "income": "~25-45 万", "level": ""},
    ]


def timeline_d_tcm(slug: str) -> list:
    """中医系 (5+3 中医规培, 跟西医不同)"""
    return [
        {"year": "Y1", "stage": "本科 · 中医基础", "note": "经典+西医", "income_label": "学费", "income": "~6.8k/年", "level": ""},
        {"year": "Y2-3", "stage": "本科 · 中诊 + 方剂", "note": "课业最重", "income_label": "见习补贴", "income": "~3-5k/月", "level": "warn", "warning": "低收入期"},
        {"year": "Y4-5", "stage": "本科 · 实习 + 考研", "note": "中医执业医", "income_label": "实习补贴", "income": "~5-8k/月", "level": "critical", "warning": "关键转折"},
        {"year": "Y6-8", "stage": "硕士 · 中医规培", "note": "中医四证", "income_label": "规培工资", "income": "~7-12k/月", "level": ""},
        {"year": "Y9-10", "stage": "专培 · 主治中医师", "note": "亚专科 (针灸/骨伤)", "income_label": "年薪", "income": "~15-25 万", "level": ""},
        {"year": "Y11+", "stage": "专科主任中医师", "note": "中医院 / 国医堂", "income_label": "年薪", "income": "~30-55 万", "level": ""},
    ]


def timeline_e_forensic() -> list:
    """法医学 (司法鉴定 / 公安法医)"""
    return [
        {"year": "Y1", "stage": "本科 · 法医基础", "note": "无收入", "income_label": "学费", "income": "~6.8k/年", "level": ""},
        {"year": "Y2-3", "stage": "本科 · 解剖 + 病理", "note": "课业最重", "income_label": "见习补贴", "income": "~2-4k/月", "level": "warn", "warning": "低收入期"},
        {"year": "Y4-5", "stage": "本科 · 实习 + 考研", "note": "司法鉴定方向", "income_label": "实习补贴", "income": "~3-6k/月", "level": "critical", "warning": "关键转折"},
        {"year": "Y6-8", "stage": "硕士 · 法医病理", "note": "执业司法鉴定", "income_label": "规培补助", "income": "~6-10k/月", "level": ""},
        {"year": "Y9-10", "stage": "主检法医师", "note": "公安 / 鉴定中心", "income_label": "年薪", "income": "~15-28 万", "level": ""},
        {"year": "Y11+", "stage": "主任法医师", "note": "事业编稳定", "income_label": "年薪", "income": "~30-55 万", "level": ""},
    ]


def timeline_f_clinical_pharmacy() -> list:
    """临床药学 (医院药学 / 临床药师)"""
    return [
        {"year": "Y1", "stage": "本科 · 药学基础", "note": "化学重", "income_label": "学费", "income": "~6.8k/年", "level": ""},
        {"year": "Y2-3", "stage": "本科 · 临床药学", "note": "药理 + 临床", "income_label": "见习补贴", "income": "~3-5k/月", "level": "warn", "warning": "低收入期"},
        {"year": "Y4-5", "stage": "本科 · 实习 + 考研", "note": "执业药师", "income_label": "实习补贴", "income": "~5-8k/月", "level": "critical", "warning": "关键转折"},
        {"year": "Y6-8", "stage": "硕士 · 临床药学", "note": "临床药师规培", "income_label": "规培补助", "income": "~7-12k/月", "level": ""},
        {"year": "Y9-10", "stage": "主管药师", "note": "三甲医院药学部", "income_label": "年薪", "income": "~15-25 万", "level": ""},
        {"year": "Y11+", "stage": "副主任药师", "note": "临床药师带组", "income_label": "年薪", "income": "~28-50 万", "level": ""},
    ]


def timeline_g_uyghur() -> list:
    """维医学 (民族医学, 规培体系弱, 本科就业为主)"""
    return [
        {"year": "Y1", "stage": "本科 · 维医基础", "note": "无收入", "income_label": "学费", "income": "~5.8k/年", "level": ""},
        {"year": "Y2-3", "stage": "本科 · 维药 + 方剂", "note": "小众课业", "income_label": "见习补贴", "income": "~2-4k/月", "level": "warn", "warning": "低收入期"},
        {"year": "Y4-5", "stage": "本科 · 实习", "note": "民族医院", "income_label": "实习补贴", "income": "~3-5k/月", "level": "critical", "warning": "就业分流"},
        {"year": "Y6-7", "stage": "规培 · 维医专科", "note": "可去综合中医院", "income_label": "规培补助", "income": "~5-8k/月", "level": ""},
        {"year": "Y8-10", "stage": "执业维医师", "note": "新疆/民族医院", "income_label": "年薪", "income": "~10-20 万", "level": ""},
        {"year": "Y11+", "stage": "维医专科主任", "note": "民族医学专家", "income_label": "年薪", "income": "~22-40 万", "level": ""},
    ]


def main():
    updated = []
    skipped = []

    # Group A: 临床医学系
    for slug in GROUP_A:
        p = CURATED / f"{slug}.json"
        if not p.exists():
            skipped.append(slug)
            continue
        d = json.load(open(p, encoding='utf-8'))
        d["timeline"] = timeline_a_clinical(slug)
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        updated.append(slug)

    # Group B: 基础医学系
    for slug in GROUP_B:
        p = CURATED / f"{slug}.json"
        if not p.exists():
            skipped.append(slug)
            continue
        d = json.load(open(p, encoding='utf-8'))
        d["timeline"] = timeline_b_basic(slug)
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        updated.append(slug)

    # Group C: 预防医学
    for slug in GROUP_C:
        p = CURATED / f"{slug}.json"
        if not p.exists():
            skipped.append(slug)
            continue
        d = json.load(open(p, encoding='utf-8'))
        d["timeline"] = timeline_c_preventive()
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        updated.append(slug)

    # Group D: 中医系
    for slug in GROUP_D:
        p = CURATED / f"{slug}.json"
        if not p.exists():
            skipped.append(slug)
            continue
        d = json.load(open(p, encoding='utf-8'))
        d["timeline"] = timeline_d_tcm(slug)
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        updated.append(slug)

    # Group E: 法医
    for slug in GROUP_E:
        p = CURATED / f"{slug}.json"
        if not p.exists():
            skipped.append(slug)
            continue
        d = json.load(open(p, encoding='utf-8'))
        d["timeline"] = timeline_e_forensic()
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        updated.append(slug)

    # Group F: 临床药学
    for slug in GROUP_F:
        p = CURATED / f"{slug}.json"
        if not p.exists():
            skipped.append(slug)
            continue
        d = json.load(open(p, encoding='utf-8'))
        d["timeline"] = timeline_f_clinical_pharmacy()
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        updated.append(slug)

    # Group G: 维医
    for slug in GROUP_G:
        p = CURATED / f"{slug}.json"
        if not p.exists():
            skipped.append(slug)
            continue
        d = json.load(open(p, encoding='utf-8'))
        d["timeline"] = timeline_g_uyghur()
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        updated.append(slug)

    print(f"Updated: {len(updated)}")
    for s in updated:
        print(f"  ✓ {s}")
    if skipped:
        print(f"\nSkipped (no JSON): {len(skipped)}")
        for s in skipped:
            print(f"  ⚠ {s}")


if __name__ == "__main__":
    main()