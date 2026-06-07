"""
scripts/merge_real_2024_gd_js.py — 合并 GD/JS 2024 多源真实数据

数据源 (按优先级):
1. 555edu 逐校 (anchor 级, 985/211 重点) — 高优先级
2. eol.cn 征求志愿 (普通本科 + 中外合作, 含 院校专业组 粒度) — 低优先级
3. 现有主文件 (锚点 + 合成) — fallback

输出: data/{guangdong|jiangsu}_admission_{物理|历史}_2024.csv
"""
import json
import re
from datetime import datetime
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = DATA_DIR / "_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# 复用 merge_real_2024 的校名/类型推断
import sys
sys.path.insert(0, str(Path(__file__).parent))
from merge_real_2024 import (  # noqa: E402
    get_school_type, get_school_city, _xuanke_to_subjects,
)


# 江苏城市关键字 (校名前缀含 → 视为江苏本地)
JIANGSU_CITY_KEYWORDS = [
    "南京", "苏州", "无锡", "常州", "镇江", "南通", "扬州",
    "泰州", "徐州", "淮安", "盐城", "连云港", "宿迁",
]

# 江苏本地学校白名单 (非 985/211 普通本科 + 独立学院)
# 解决 get_school_city 对普通本科返回 "其他" 的问题
JIANGSU_LOCAL_SCHOOLS = {
    # 南京
    "南京体育学院": "南京", "南京医科大学": "南京", "南京中医药大学": "南京",
    "南京工程学院": "南京", "南京森林警察学院": "南京", "南京特殊教育师范学院": "南京",
    "南京审计大学": "南京", "南京晓庄学院": "南京", "南京工业大学": "南京",
    "南京信息工程大学": "南京", "南京邮电大学": "南京", "南京财经大学": "南京",
    "南京医科大学康达学院": "南京", "南京审计大学金审学院": "南京",
    "南京理工大学紫金学院": "南京", "南京工业大学浦江学院": "南京",
    "南京财经大学红山学院": "南京", "南京传媒学院": "南京",
    "南京视觉艺术职业学院": "南京", "南京信息职业技术学院": "南京",
    "江苏警官学院": "南京", "南京艺术学院": "南京", "南京体育学院": "南京",
    "南京森林警察学院": "南京", "江苏第二师范学院": "南京",
    # 苏州
    "苏州大学": "苏州", "苏州科技大学": "苏州", "常熟理工学院": "苏州",
    "西交利物浦大学": "苏州", "昆山杜克大学": "苏州", "苏州城市学院": "苏州",
    "苏州大学应用技术学院": "苏州", "苏州科技大学天平学院": "苏州",
    "苏州工业园区职业技术学院": "苏州", "沙洲职业工学院": "苏州",
    # 无锡
    "江南大学": "无锡", "无锡太湖学院": "无锡",
    # 常州
    "常州大学": "常州", "常州工学院": "常州", "常州信息职业技术学院": "常州",
    "常州大学怀德学院": "常州", "常州机电职业技术学院": "常州",
    "江苏理工学院": "常州",
    # 镇江
    "江苏大学": "镇江", "江苏科技大学": "镇江", "镇江高等专科学校": "镇江",
    "江苏大学京江学院": "镇江",
    # 南通
    "南通大学": "南通", "南通理工学院": "南通", "南通职业大学": "南通",
    "南通大学杏林学院": "南通",
    # 扬州
    "扬州大学": "扬州", "扬州职业大学": "扬州", "扬州工业职业技术学院": "扬州",
    # 泰州
    "泰州学院": "泰州",
    # 徐州
    "中国矿业大学": "徐州", "江苏师范大学": "徐州", "徐州工程学院": "徐州",
    "徐州医科大学": "徐州", "江苏师范大学科文学院": "徐州",
    # 淮安
    "淮阴师范学院": "淮安", "淮阴工学院": "淮安", "南京林业大学淮安校区": "淮安",
    # 盐城
    "盐城师范学院": "盐城", "盐城工学院": "盐城",
    # 连云港
    "江苏海洋大学": "连云港", "南京医科大学康达学院": "连云港",
    # 宿迁
    "宿迁学院": "宿迁",
}


def is_jiangsu_local(name: str) -> bool:
    """判断学校是否江苏本地的.

    优先级:
    1. 白名单 (覆盖度最高)
    2. 校名前缀含江苏城市关键字
    3. 校名含"江苏"开头
    """
    if name in JIANGSU_LOCAL_SCHOOLS:
        return True
    for k in JIANGSU_CITY_KEYWORDS:
        if name.startswith(k):
            return True
    if name.startswith("江苏"):
        return True
    return False


def jiangsu_local_city(name: str) -> str:
    """获取江苏本地学校的城市. 非本地返回 None."""
    if name in JIANGSU_LOCAL_SCHOOLS:
        return JIANGSU_LOCAL_SCHOOLS[name]
    for k in JIANGSU_CITY_KEYWORDS:
        if name.startswith(k):
            return k
    return None


def score_to_rank(score: int, rank_df: pd.DataFrame) -> int:
    """投档线 → 位次. 找不到时回退 999999 (避免 0 触发除 0)."""
    if rank_df.empty:
        return 999999
    rows = rank_df[rank_df["_score_int"] == score]
    if rows.empty:
        rows = rank_df[rank_df["_score_int"] < score]
        if rows.empty:
            return 999999
        return int(rows.iloc[-1]["rank"])
    return int(rows.iloc[0]["rank"])


def load_rank_table(subject: str, year: int = 2024) -> pd.DataFrame:
    f = DATA_DIR / f"jiangsu_rank_{subject}_{year}.csv"
    if not f.exists():
        return pd.DataFrame()
    df = pd.read_csv(f)
    df["_score_int"] = df["score"].apply(
        lambda s: int(str(s).split("-")[0]) if "-" in str(s) else
                  int(s) if str(s).isdigit() else -1
    )
    df = df[df["_score_int"] >= 0].copy()
    return df


def load_555edu(province: str, subject: str) -> pd.DataFrame:
    f = DATA_DIR / f"{province}_admission_{subject}_2024_real_555edu.csv"
    if not f.exists():
        return pd.DataFrame()
    df = pd.read_csv(f)
    if "batch" in df.columns:
        df = df[df["batch"].fillna("").str.contains("本科|提前批", na=False)]
    df["data_source"] = "555edu 逐校"
    return df


def load_eolcn(province: str, subject: str, local_only: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """eol.cn 征求志愿 抓的数据. 注意: 这是征求志愿 (二轮补录), 不是主批.

    Returns:
        (local_df, external_df). local = 江苏本地学校, external = 外省在江苏招生的.
        local_only=True 时 external_df 留空 (已存到独立文件).
    """
    f = DATA_DIR / f"{province}_admission_2024_real_eolcn.csv"
    if not f.exists():
        return pd.DataFrame(), pd.DataFrame()
    df = pd.read_csv(f)
    df = df[df["subject"] == subject].copy()
    if df.empty:
        return df, pd.DataFrame()
    df["batch"] = "本科批"
    df["kind"] = "普通类"
    df["min_rank"] = 0
    # 区分 本地 / 外省
    df["_is_jiangsu"] = df["school_name"].apply(is_jiangsu_local)
    local = df[df["_is_jiangsu"]].drop(columns=["_is_jiangsu"]).copy()
    external = df[~df["_is_jiangsu"]].drop(columns=["_is_jiangsu"]).copy()
    local["data_source"] = "eol.cn 征求志愿 (江苏本地)"
    external["data_source"] = "eol.cn 征求志愿 (外省在江苏招生)"
    if local_only:
        return local, external  # external 留 caller 存到独立 file
    return local, external


def load_existing(province: str, subject: str) -> pd.DataFrame:
    f = DATA_DIR / f"{province}_admission_{subject}_2024.csv"
    if not f.exists():
        return pd.DataFrame()
    return pd.read_csv(f)


def normalize_555edu(df: pd.DataFrame, subject: str) -> pd.DataFrame:
    """555edu → 主 CSV schema"""
    if df.empty:
        return df
    out = pd.DataFrame()
    out["year"] = 2024
    out["subject"] = subject
    out["school_name"] = df["school_name"]
    out["school_type"] = df["school_name"].apply(get_school_type)
    # 555edu group_id 已是 string (e.g. "205", "（08）专业组"), 用 "（08）专业组" 形式更清晰
    # eolcn 的 group_id 是 "1", "2", "3" 短数字
    # 保留原始 group_id + group_name
    out["group_id"] = df["group_id"].astype(str).str.zfill(2)
    out["xuanke_req"] = df.get("xuanke_req", "不限").fillna("不限")
    out["xuanke_subjects"] = out["xuanke_req"].apply(lambda x: _xuanke_to_subjects(str(x), subject))
    out["plan_count"] = 30
    out["min_score"] = df["min_score"]
    out["min_rank"] = df.get("min_rank", 0)
    out["tuition_yuan"] = 5500
    out["city"] = df["school_name"].apply(get_school_city)
    out["is_special"] = (df["is_special"] if "is_special" in df.columns else pd.Series(["否"] * len(df))).fillna("否")
    out["data_source"] = df["data_source"]
    return out


def normalize_eolcn(df: pd.DataFrame, subject: str) -> pd.DataFrame:
    """eol.cn 征求志愿 → 主 CSV schema.

    min_rank 从 jiangsu_rank_{subject}_{year}.csv 反查, 找不到时回退 999999.
    city 优先用白名单, fallback 到 get_school_city.
    """
    if df.empty:
        return df
    rank_df = load_rank_table(subject)
    out = pd.DataFrame()
    out["year"] = 2024
    out["subject"] = subject
    out["school_name"] = df["school_name"]
    out["school_type"] = df["school_name"].apply(get_school_type)
    out["group_id"] = df["group_id"].astype(str).str.zfill(2)
    out["xuanke_req"] = df["xuanke_req"].fillna("不限")
    out["xuanke_subjects"] = out["xuanke_req"].apply(lambda x: _xuanke_to_subjects(str(x), subject))
    out["plan_count"] = 30
    out["min_score"] = df["min_score"]
    if "min_rank" in df.columns and df["min_rank"].sum() > 0:
        out["min_rank"] = df["min_rank"]
    else:
        out["min_rank"] = df["min_score"].apply(lambda s: score_to_rank(int(s), rank_df))
    out["tuition_yuan"] = 5500
    # city: 白名单 → get_school_city → "其他"
    out["city"] = df["school_name"].apply(
        lambda n: jiangsu_local_city(n) or get_school_city(n) or "其他"
    )
    out["is_special"] = df["is_special"].fillna("否") if "is_special" in df.columns else pd.Series(["否"] * len(df))
    out["data_source"] = df["data_source"]
    return out


def save_external_eolcn(province: str, subject: str, external_df: pd.DataFrame):
    """保存外省在江苏招生的征求志愿 到按 subject 拆分的独立 file."""
    if external_df.empty:
        return
    out = DATA_DIR / f"{province}_eolcn_2024_external_征求志愿_{subject}.csv"
    external_df.to_csv(out, index=False)
    print(f"  📦 {out.name}: {len(external_df)} 行 (外省在江苏招生的征求志愿, {subject})")


def merge_year(province: str, subject: str):
    print(f"\n{'='*60}")
    print(f"📦 合并 {province} 2024 {subject} 投档表")
    print(f"{'='*60}")

    edu = load_555edu(province, subject)
    eol_local, eol_external = load_eolcn(province, subject, local_only=True)
    existing = load_existing(province, subject)

    print(f"  555edu: {len(edu)} 行")
    print(f"  eol.cn 征求志愿 (江苏本地): {len(eol_local)} 行")
    print(f"  eol.cn 征求志愿 (外省在江苏招生): {len(eol_external)} 行")
    print(f"  现有: {len(existing)} 行")

    # 保存外省到独立 file
    save_external_eolcn(province, subject, eol_external)

    real_dfs = []
    if not edu.empty:
        real_dfs.append(normalize_555edu(edu, subject))
    if not eol_local.empty:
        real_dfs.append(normalize_eolcn(eol_local, subject))
    if not real_dfs:
        print("  ⚠️ 无数据, 跳过")
        return pd.DataFrame()

    real = pd.concat(real_dfs, ignore_index=True)
    print(f"  真实源合并 (未去重): {len(real)} 行")

    # 555edu group_id (3位, e.g. 112/442) vs eol.cn group_id (1-2位, e.g. 01) 是不同 indexing scheme
    # 同源 555edu 内 同校多 group_id 是不同 院校专业组, 需保留
    # 不做跨源去重 (各自 source 内已自去重)
    print(f"  最终: {len(real)} 行 (跨源不去重, 同源各自自去重)")

    # 写盘
    target = DATA_DIR / f"{province}_admission_{subject}_2024.csv"
    if target.exists():
        backup = LOG_DIR / f"{target.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        target.rename(backup)
        print(f"  📦 备份: {backup.name}")

    real.to_csv(target, index=False)
    print(f"  ✅ 写入 {target.name} ({len(real)} 行)")
    print(f"  📊 数据源: {dict(real['data_source'].value_counts())}")
    return real


def main():
    for prov in ["guangdong", "jiangsu"]:
        for subj in ["物理", "历史"]:
            merge_year(prov, subj)


if __name__ == "__main__":
    main()
