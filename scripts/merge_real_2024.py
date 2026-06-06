"""
scripts/merge_real_2024.py — 合并 2024 湖北 投档表 真实数据源

数据源 (按优先级):
1. 555edu 逐校抓 (湖北本地 125 校, 327+425 行 含高职)
2. dxsbb 6261 一本 完整表 (985/211/重点, 99+39 行)
3. 原始 anchor 硬编码 (33 985/211 校)
4. OCR'd dxsbb PNGs (dzsbb 2024 历史/物理 完整图, ~280/380 行, 但精度有限)

输出: data/hubei_admission_{物理|历史}_2024.csv (新)
       备份原文件到 _logs
"""
import re
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = PROJECT_DIR / "data" / "_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 学校类型查询 (从 555edu SCHOOL_INFO + anchor 推断)
SCHOOL_TYPE = {
    "北京大学": "985", "清华大学": "985", "上海交通大学": "985", "复旦大学": "985",
    "中国科学技术大学": "985", "南京大学": "985", "浙江大学": "985", "中国人民大学": "985",
    "北京航空航天大学": "985", "同济大学": "985", "东南大学": "985", "武汉大学": "985",
    "华中科技大学": "985", "中山大学": "985", "华南理工大学": "985", "西安交通大学": "985",
    "哈尔滨工业大学": "985", "南开大学": "985", "天津大学": "985", "厦门大学": "985",
    "山东大学": "985", "四川大学": "985", "重庆大学": "985", "中南大学": "985",
    "湖南大学": "985", "西北工业大学": "985", "大连理工大学": "985", "东北大学": "985",
    "吉林大学": "985", "兰州大学": "985", "中国农业大学": "985", "北京师范大学": "985",
    "中央民族大学": "985", "国防科技大学": "985", "西北农林科技大学": "985",
    "中国海洋大学": "985", "电子科技大学": "985", "北京理工大学": "985",
    "中南财经政法大学": "211", "华中师范大学": "211", "武汉理工大学": "211",
    "华中农业大学": "211", "中国地质大学（武汉）": "211", "中国地质大学(武汉)": "211",
    "北京邮电大学": "211", "中央财经大学": "211", "对外经济贸易大学": "211",
    "北京外国语大学": "211", "中国政法大学": "211", "上海财经大学": "211",
    "华东理工大学": "211", "东华大学": "211", "上海大学": "211", "苏州大学": "211",
    "南京理工大学": "211", "南京航空航天大学": "211", "河海大学": "211",
    "江南大学": "211", "南京师范大学": "211", "南京农业大学": "211",
    "中国矿业大学": "211", "哈尔滨工程大学": "211", "天津医科大学": "211",
    "华北电力大学": "211", "暨南大学": "211", "广西大学": "211", "郑州大学": "211",
    "云南大学": "211", "新疆大学": "211", "石河子大学": "211", "宁夏大学": "211",
    "西藏大学": "211", "内蒙古大学": "211", "辽宁大学": "211", "延边大学": "211",
    "东北师范大学": "211", "东北农业大学": "211", "东北林业大学": "211",
    "合肥工业大学": "211", "福州大学": "211", "南昌大学": "211",
    "湖南师范大学": "211", "华南师范大学": "211", "广西师范大学": "211",
    "四川农业大学": "211", "西南大学": "211", "西南交通大学": "211",
    "西南财经大学": "211", "贵州大学": "211", "北京交通大学": "211",
    "北京科技大学": "211", "北京化工大学": "211", "北京工业大学": "211",
    "北京林业大学": "211", "北京中医药大学": "211", "中国传媒大学": "211",
    "中央音乐学院": "211", "北京体育大学": "211", "中国药科大学": "211",
    "中国矿业大学（北京）": "211", "中国石油大学（北京）": "211",
    "中国石油大学（华东）": "211", "中国地质大学（北京）": "211",
    "中国劳动关系学院": "普通",
}

CITY_BY_SCHOOL = {
    "北京大学": "北京", "清华大学": "北京", "北京航空航天大学": "北京",
    "北京理工大学": "北京", "中国人民大学": "北京", "北京师范大学": "北京",
    "中央民族大学": "北京", "中国农业大学": "北京", "北京邮电大学": "北京",
    "中央财经大学": "北京", "对外经济贸易大学": "北京", "北京外国语大学": "北京",
    "中国政法大学": "北京", "北京交通大学": "北京", "北京科技大学": "北京",
    "北京化工大学": "北京", "北京工业大学": "北京", "北京林业大学": "北京",
    "北京中医药大学": "北京", "中国传媒大学": "北京", "中国矿业大学（北京）": "北京",
    "中国石油大学（北京）": "北京", "中国地质大学（北京）": "北京", "北京体育大学": "北京",
    "中国劳动关系学院": "北京",
    "上海交通大学": "上海", "复旦大学": "上海", "同济大学": "上海",
    "华东师范大学": "上海", "上海财经大学": "上海", "华东理工大学": "上海",
    "东华大学": "上海", "上海大学": "上海", "上海外国语大学": "上海",
    "南京大学": "南京", "东南大学": "南京", "南京理工大学": "南京",
    "南京航空航天大学": "南京", "河海大学": "南京", "南京师范大学": "南京",
    "南京农业大学": "南京", "中国药科大学": "南京",
    "浙江大学": "杭州",
    "中国科学技术大学": "合肥", "合肥工业大学": "合肥",
    "武汉大学": "武汉", "华中科技大学": "武汉", "中南财经政法大学": "武汉",
    "华中师范大学": "武汉", "武汉理工大学": "武汉", "华中农业大学": "武汉",
    "中国地质大学（武汉）": "武汉", "中南民族大学": "武汉",
    "中山大学": "广州", "华南理工大学": "广州", "暨南大学": "广州", "华南师范大学": "广州",
}


def get_school_type(name: str) -> str:
    """从学校名推断 985/211/普通"""
    # 去掉括号后缀
    base = re.sub(r"[\(（][^）\)]*[\)）]", "", name).strip()
    if name in SCHOOL_TYPE:
        return SCHOOL_TYPE[name]
    if base in SCHOOL_TYPE:
        return SCHOOL_TYPE[base]
    # 看名字特征
    if any(k in name for k in ["民族班", "国家专项", "中外合作", "预科", "联培"]):
        return "普通"
    if "职业技术学院" in name or "职业学院" in name or "专科" in name:
        return "专科"
    if "学院" in name and "大学" not in name:
        return "普通"  # 民办/独立学院
    return "普通"


def get_school_city(name: str) -> str:
    """从学校名推断城市"""
    base = re.sub(r"[\(（][^）\)]*[\)）]", "", name).strip()
    if name in CITY_BY_SCHOOL:
        return CITY_BY_SCHOOL[name]
    if base in CITY_BY_SCHOOL:
        return CITY_BY_SCHOOL[base]
    # 湖北本地 优先 武汉
    hubei_local = {
        "武汉大学": "武汉", "华中科技大学": "武汉", "中南财经政法大学": "武汉",
        "华中师范大学": "武汉", "武汉理工大学": "武汉", "华中农业大学": "武汉",
        "中国地质大学（武汉）": "武汉", "中南民族大学": "武汉", "湖北大学": "武汉",
        "武汉科技大学": "武汉", "武汉工程大学": "武汉", "湖北工业大学": "武汉",
        "武汉纺织大学": "武汉", "武汉轻工大学": "武汉", "江汉大学": "武汉",
        "武汉商学院": "武汉", "武汉学院": "武汉", "武昌首义学院": "武汉",
        "武汉城市学院": "武汉", "武汉东湖学院": "武汉", "武汉工商学院": "武汉",
        "武昌工学院": "武汉", "武汉纺织大学外经贸学院": "武汉", "武汉华夏理工学院": "武汉",
        "武汉生物工程学院": "武汉", "武昌理工学院": "武汉", "湖北中医药大学": "武汉",
        "湖北经济学院": "武汉", "武汉职业技术学院": "武汉", "武汉船舶职业技术学院": "武汉",
        "武汉电力职业技术学院": "武汉",
        "三峡大学": "宜昌", "长江大学": "荆州", "湖北文理学院": "襄阳",
        "黄冈师范学院": "黄冈", "湖北师范大学": "黄石", "湖北民族大学": "恩施",
        "汉江师范学院": "十堰", "湖北工程学院": "孝感", "湖北医药学院": "十堰",
        "湖北科技学院": "咸宁", "湖北理工学院": "黄石", "荆楚理工学院": "荆门",
        "武汉体育学院": "武汉", "武汉音乐学院": "武汉", "湖北美术学院": "武汉",
    }
    if name in hubei_local:
        return hubei_local[name]
    if base in hubei_local:
        return hubei_local[base]
    return "其他"


def load_dxsbb_6261(year: int, subject: str) -> pd.DataFrame:
    """Load dxsbb 6261 一本 真实数据 (985/211)"""
    f = DATA_DIR / f"hubei_admission_{subject}_{year}_real_dxsbb6261.csv"
    if not f.exists():
        return pd.DataFrame()
    df = pd.read_csv(f)
    df["data_source"] = "dxsbb 6261 一本"
    return df


def load_555edu(year: int, subject: str) -> pd.DataFrame:
    """Load 555edu 湖北本地 真实数据 (本科批 only)"""
    f = DATA_DIR / f"hubei_admission_{subject}_{year}_real_555edu.csv"
    if not f.exists():
        return pd.DataFrame()
    df = pd.read_csv(f)
    # Filter to 本科批 only (drop 高职高专批 = vocational)
    if "batch" in df.columns:
        df = df[df["batch"].fillna("").str.contains("本科|提前批", na=False)]
    df["data_source"] = "555edu 逐校"
    return df


def load_existing(year: int, subject: str) -> pd.DataFrame:
    """Load the existing file (with anchors + synthetic)"""
    f = DATA_DIR / f"hubei_admission_{subject}_{year}.csv"
    if not f.exists():
        return pd.DataFrame()
    return pd.read_csv(f)


def normalize(df: pd.DataFrame, subject: str) -> pd.DataFrame:
    """Normalize all sources to common schema"""
    if df.empty:
        return df
    # dxsbb 6261 doesn't have xuanke_req - default based on subject
    if "xuanke_req" not in df.columns:
        df["xuanke_req"] = "不限"
    # build xuanke_subjects from xuanke_req
    if "xuanke_subjects" not in df.columns:
        df["xuanke_subjects"] = df["xuanke_req"].apply(lambda x: _xuanke_to_subjects(str(x), subject))
    # plan_count default
    if "plan_count" not in df.columns:
        df["plan_count"] = 30
    # city + school_type
    df["school_type"] = df["school_name"].apply(get_school_type)
    df["city"] = df["school_name"].apply(get_school_city)
    # is_special
    if "is_special" not in df.columns:
        if "kind" in df.columns:
            df["is_special"] = df["kind"].apply(lambda k: "是" if k and k not in ("普通类", "nan", "") else "否")
        else:
            df["is_special"] = "否"
    # tuition
    if "tuition_yuan" not in df.columns:
        df["tuition_yuan"] = 5500
    # year/subject
    if "year" not in df.columns:
        df["year"] = 2024
    if "subject" not in df.columns:
        df["subject"] = subject
    return df[["year","subject","school_name","school_type","group_id","xuanke_req",
               "xuanke_subjects","plan_count","min_score","min_rank","tuition_yuan",
               "city","is_special","data_source"]]


def _xuanke_to_subjects(req: str, subject: str) -> str:
    """Convert xuanke_req like '不限' or '化' to xuanke_subjects like '物理' or '物理|化学'"""
    if not req or req in ("nan", "None"):
        return subject
    req = str(req).strip()
    if "不限" in req or "无要求" in req or "无" in req:
        return subject
    if "首选" in req:
        # 555edu format: "首选历史,再选不限" or "首选历史,再选地理"
        parts = req.replace("首选", "").replace("再选", "").split(",")
        if len(parts) >= 1:
            first = parts[0].strip()
            rest = parts[1].strip() if len(parts) > 1 else ""
            if first in ("物理", "历史"):
                if rest and rest not in ("不限", "无"):
                    return f"{first}|{rest}"
                return first
    # 化/生/地/政 单字符
    if len(req) <= 3 and req in ("化", "生", "地", "政", "化学", "生物", "地理", "政治"):
        m = {"化": "化学", "生": "生物", "地": "地理", "政": "政治"}.get(req, req)
        return f"{subject}|{m}"
    return subject


def merge_year(year: int, subject: str):
    """Merge all sources for a given year+subject"""
    print(f"\n{'='*60}")
    print(f"📦 合并 {year} 湖北 {subject} 投档表")
    print(f"{'='*60}")

    # 1. dxsbb 6261
    d6261 = load_dxsbb_6261(year, subject)
    print(f"  dxsbb 6261: {len(d6261)} 行")

    # 2. 555edu
    edu = load_555edu(year, subject)
    print(f"  555edu: {len(edu)} 行 (含高职高专)")

    # 3. existing file (with anchors + synthetic)
    existing = load_existing(year, subject)
    print(f"  现有: {len(existing)} 行 (含锚点+合成)")

    # Combine all real sources first
    all_dfs = []
    if not d6261.empty:
        all_dfs.append(normalize(d6261, subject))
    if not edu.empty:
        all_dfs.append(normalize(edu, subject))

    real_combined = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    print(f"  真实源合并: {len(real_combined)} 行 (未去重)")

    # Drop duplicates on (school_name, group_id) - prefer 555edu (more complete) over dxsbb
    if not real_combined.empty:
        real_combined["_priority"] = real_combined["data_source"].map({
            "555edu 逐校": 2, "dxsbb 6261 一本": 1
        }).fillna(0)
        real_combined = real_combined.sort_values("_priority", ascending=False)
        real_combined = real_combined.drop_duplicates(subset=["school_name", "group_id"], keep="first")
        real_combined = real_combined.drop(columns=["_priority"]).reset_index(drop=True)
        print(f"  去重后真实: {len(real_combined)} 行")

    # Add anchors (only for rows not in real_combined)
    if not existing.empty:
        anchor_mask = existing["data_source"] == "真实锚点" if "data_source" in existing.columns else pd.Series([False]*len(existing))
        if anchor_mask.any():
            anchors = existing[anchor_mask].copy()
            anchors_norm = anchors.copy()
            # check which (school, group) is missing
            existing_keys = set(zip(real_combined["school_name"], real_combined["group_id"])) if not real_combined.empty else set()
            new_anchors = anchors_norm[
                ~anchors_norm.apply(lambda r: (r["school_name"], r["group_id"]) in existing_keys, axis=1)
            ]
            print(f"  新增锚点: {len(new_anchors)} 行")
            if not new_anchors.empty and "data_source" not in new_anchors.columns:
                new_anchors["data_source"] = "真实锚点"
            if not real_combined.empty and not new_anchors.empty:
                real_combined = pd.concat([real_combined, new_anchors], ignore_index=True)
            elif not new_anchors.empty:
                real_combined = new_anchors

    # Filter out 高职高专批 (keep 本科批 only) for main file
    # Detect batch column
    if "batch" in real_combined.columns:
        benke_mask = real_combined["batch"].fillna("").str.contains("本科|提前批", na=False) | real_combined["batch"].isna()
        real_benke = real_combined[benke_mask].copy()
        print(f"  本科批: {len(real_benke)} 行")
    else:
        real_benke = real_combined

    # Save
    target = DATA_DIR / f"hubei_admission_{subject}_{year}.csv"
    if target.exists():
        backup = LOG_DIR / f"{target.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        target.rename(backup)
        print(f"  📦 备份: {backup.name}")

    real_benke.to_csv(target, index=False)
    print(f"  ✅ 写入 {target.name} ({len(real_benke)} 行)")

    # Show summary
    print(f"\n  📊 最终统计:")
    print(f"    真实 (锚点+dxsbb+555edu): {len(real_benke[real_benke['data_source'].str.contains('真实|555edu|dxsbb', na=False)])}")
    print(f"    学校类型分布: {dict(real_benke['school_type'].value_counts().head())}")
    return real_benke


def main():
    for subj in ["历史", "物理"]:
        merge_year(2024, subj)


if __name__ == "__main__":
    main()
