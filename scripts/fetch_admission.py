"""
scripts/fetch_admission.py — 抓真实院校专业组投档表

数据源 (按优先级):
1. gk100.com/read_38500828.htm — 2025 物理类完整版 (205 行)
2. gk100.com/read_9100048.htm — 2025 物理+历史 汇总
3. gk100.com/read_91260690.htm — 2025 位次对应大学 (1-3万名)
4. zizzs.com/172044.html — 2024 物理 985 完整版
5. eol.cn 投档线汇总 (各年模板)

输出: data/hubei_admission_{物理|历史}_{year}.csv
"""
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
CACHE_DIR = PROJECT_DIR / "data" / "_cache"
LOG_DIR = PROJECT_DIR / "data" / "_logs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────
# 工具
# ─────────────────────────────────────────
def fetch_url(url: str, timeout: int = 30, retries: int = 3, use_gbk: bool = False) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    for attempt in range(retries):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            for enc in (("gbk", "gb18030", "utf-8") if use_gbk else ("utf-8", "gbk", "gb18030")):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")
        except (URLError, HTTPError, TimeoutError) as e:
            wait = 2 ** attempt
            print(f"  ⚠️ {attempt+1} fail: {e}, wait {wait}s")
            time.sleep(wait)
    return None


def cache_path(url: str) -> Path:
    return CACHE_DIR / (url.split("/")[-1] or "page.html")


# ─────────────────────────────────────────
# 学校静态信息(从生成样本 + 真实数据校准)
# ─────────────────────────────────────────
SCHOOL_INFO = {
    "北京大学": ("985", "北京"), "清华大学": ("985", "北京"),
    "上海交通大学": ("985", "上海"), "复旦大学": ("985", "上海"),
    "复旦大学上海医学院": ("985", "上海"), "上海交通大学医学院": ("985", "上海"),
    "浙江大学": ("985", "杭州"), "中国科学技术大学": ("985", "合肥"),
    "南京大学": ("985", "南京"), "中国人民大学": ("985", "北京"),
    "北京航空航天大学": ("985", "北京"), "同济大学": ("985", "上海"),
    "东南大学": ("985", "南京"), "武汉大学": ("985", "武汉"),
    "华中科技大学": ("985", "武汉"), "中山大学": ("985", "广州"),
    "华南理工大学": ("985", "广州"), "西安交通大学": ("985", "西安"),
    "哈尔滨工业大学": ("985", "哈尔滨"), "哈尔滨工业大学(深圳)": ("985", "深圳"),
    "南开大学": ("985", "天津"), "天津大学": ("985", "天津"),
    "厦门大学": ("985", "厦门"), "山东大学": ("985", "济南"),
    "四川大学": ("985", "成都"), "重庆大学": ("985", "重庆"),
    "中南大学": ("985", "长沙"), "湖南大学": ("985", "长沙"),
    "西北工业大学": ("985", "西安"), "大连理工大学": ("985", "大连"),
    "东北大学": ("985", "沈阳"), "吉林大学": ("985", "长春"),
    "兰州大学": ("985", "兰州"), "中国农业大学": ("985", "北京"),
    "北京师范大学": ("985", "北京"), "中央民族大学": ("985", "北京"),
    "国防科技大学": ("985", "长沙"), "西北农林科技大学": ("985", "咸阳"),
    "中国海洋大学": ("985", "青岛"), "电子科技大学": ("985", "成都"),
    "北京理工大学": ("985", "北京"),
    # 湖北本省
    "中南财经政法大学": ("211", "武汉"), "华中师范大学": ("211", "武汉"),
    "武汉理工大学": ("211", "武汉"), "华中农业大学": ("211", "武汉"),
    "中国地质大学(武汉)": ("211", "武汉"), "中南民族大学": ("普通", "武汉"),
    "湖北大学": ("普通", "武汉"), "武汉科技大学": ("普通", "武汉"),
    "三峡大学": ("普通", "宜昌"), "长江大学": ("普通", "荆州"),
    "武汉工程大学": ("普通", "武汉"), "湖北工业大学": ("普通", "武汉"),
    "武汉纺织大学": ("普通", "武汉"), "江汉大学": ("普通", "武汉"),
    "武汉商学院": ("普通", "武汉"), "黄冈师范学院": ("普通", "黄冈"),
    "湖北经济学院": ("普通", "武汉"), "武汉轻工大学": ("普通", "武汉"),
    "武汉职业技术学院": ("专科", "武汉"), "武汉船舶职业技术学院": ("专科", "武汉"),
    "湖北职业技术学院": ("专科", "孝感"), "黄冈职业技术学院": ("专科", "黄冈"),
    "武汉电力职业技术学院": ("专科", "武汉"),
    "湖北中医药大学": ("普通", "武汉"),
    "武汉学院": ("普通", "武汉"), "武昌首义学院": ("普通", "武汉"),
    "武汉城市学院": ("普通", "武汉"), "武汉东湖学院": ("普通", "武汉"),
    "湖北工程学院新技术学院": ("普通", "孝感"),
    "武汉工商学院": ("普通", "武汉"), "荆州学院": ("普通", "荆州"),
    "武昌工学院": ("普通", "武汉"), "武汉纺织大学外经贸学院": ("普通", "武汉"),
    "湖北恩施学院": ("普通", "恩施"), "湖北商贸学院": ("普通", "武汉"),
    "武汉生物工程学院": ("普通", "武汉"), "武昌理工学院": ("普通", "武汉"),
    "武汉华夏理工学院": ("普通", "武汉"), "湖北孝感美珈职业学院": ("专科", "孝感"),
    "湖北健康职业学院": ("专科", "咸宁"), "湖北幼儿师范高等专科学校": ("专科", "武汉"),
    "荆州教育学院": ("专科", "荆州"),
    # 省外 211
    "北京邮电大学": ("211", "北京"), "中央财经大学": ("211", "北京"),
    "对外经济贸易大学": ("211", "北京"), "北京外国语大学": ("211", "北京"),
    "中国政法大学": ("211", "北京"), "上海财经大学": ("211", "上海"),
    "华东理工大学": ("211", "上海"), "东华大学": ("211", "上海"),
    "上海大学": ("211", "上海"), "苏州大学": ("211", "苏州"),
    "南京理工大学": ("211", "南京"), "南京航空航天大学": ("211", "南京"),
    "河海大学": ("211", "南京"), "江南大学": ("211", "无锡"),
    "南京师范大学": ("211", "南京"), "南京农业大学": ("211", "南京"),
    "中国矿业大学": ("211", "徐州"),
    "深圳大学": ("普通", "深圳"), "广州大学": ("普通", "广州"),
    "广东工业大学": ("普通", "广州"), "杭州电子科技大学": ("普通", "杭州"),
    "浙江工业大学": ("普通", "杭州"), "南京邮电大学": ("普通", "南京"),
    "重庆邮电大学": ("普通", "重庆"), "西安邮电大学": ("普通", "西安"),
    "长沙理工大学": ("普通", "长沙"), "湘潭大学": ("普通", "湘潭"),
    "哈尔滨工程大学": ("211", "哈尔滨"),
    "西南石油大学": ("普通", "南充"),
    "天津医科大学": ("211", "天津"),
    "河北医科大学": ("普通", "石家庄"),
    "河北师范大学": ("普通", "石家庄"),
    "燕山大学": ("普通", "秦皇岛"),
    "山西财经大学": ("普通", "太原"),
    "山西大学": ("211", "太原"),
    "浙江科技大学": ("普通", "杭州"),
    "中国人民警察大学": ("普通", "廊坊"),
    "南通大学": ("普通", "南通"),
    "大连医科大学": ("普通", "大连"),
}


def get_school_type(school: str) -> str:
    """从静态表查学校层次"""
    # 去掉括号后缀
    base = re.sub(r"\([^)]*\)", "", school).strip()
    return SCHOOL_INFO.get(school, SCHOOL_INFO.get(base, ("普通", "其他")))[0]


def get_school_city(school: str) -> str:
    """从静态表查城市"""
    base = re.sub(r"\([^)]*\)", "", school).strip()
    return SCHOOL_INFO.get(school, SCHOOL_INFO.get(base, ("普通", "其他")))[1]


# ─────────────────────────────────────────
# Parser: gk100.com 投档位次表
# 格式: 学校名 | 专业组 | 2025分数 | 2025位次
# ─────────────────────────────────────────
def parse_gk100_admission(html: str) -> list[dict]:
    """解析 gk100.com 风格的投档位次表"""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
    records = []
    for row in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL)
        if len(cells) < 4:
            continue
        cells_clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
        # 表头行: 学校名/专业组/2025分数/2025位次
        if cells_clean[2] in ("2025分数", "分数", ""):
            continue
        if not (re.match(r"^\d+$", cells_clean[2]) and re.match(r"^\d+$", cells_clean[3])):
            continue
        school, group, score, rank = cells_clean[0], cells_clean[1], int(cells_clean[2]), int(cells_clean[3])
        records.append({"school": school, "group": group, "score": score, "rank": rank})
    return records


# ─────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────
def fetch_year_admission(year: int, subject: str) -> list[dict]:
    """抓某年某科的全部院校投档表
    每个数据源已 hardcode subject,避免跨科串数据"""
    print(f"\n{'='*60}")
    print(f"📥 抓 {year} 湖北 {subject}类 投档表")
    print(f"{'='*60}")

    all_records = []
    # (URL, gbk?, 该 URL 实际代表的 subject)
    sources_by_subject = {
        "物理": [
            ("https://www.gk100.com/read_38500828.htm", False, "物理"),
            # 91260690 的 物理部分 已被它的 1-3万+2-2.3万 名次覆盖
        ],
        "历史": [
            ("https://www.gk100.com/read_91260690.htm", False, "历史"),  # 含 1-3000 名 + 2-2.3 万名
        ],
    }
    sources = sources_by_subject.get(subject, [])

    for url, gbk, _ in sources:
        print(f"  → 试 {url}")
        cached = cache_path(url)
        if cached.exists():
            html = cached.read_text(encoding="utf-8", errors="replace")
            print(f"     (cache: {cached.name})")
        else:
            html = fetch_url(url, use_gbk=gbk)
            if html:
                cached.write_text(html, encoding="utf-8")
        if not html:
            continue
        records = parse_gk100_admission(html)
        all_records.extend(records)
        print(f"     +{len(records)} 行 (累计 {len(all_records)})")

    return all_records


def records_to_admission_csv(records: list[dict], subject: str, year: int) -> pd.DataFrame:
    """records → 标准 hubei_admission_{subject}_{year}.csv schema"""
    out = []
    for r in records:
        school = r["school"]
        group = r["group"]
        is_special = "是" if any(k in group for k in ["国家专项", "中外合作", "民族", "预科", "联培"]) else "否"
        # 推断 选科要求
        if "国家专项" in group:
            xuanke = "不限"
        elif "中外合作" in group:
            xuanke = "不限"
        else:
            xuanke = "物理+化学" if subject == "物理" else "历史+不限"
        # 推断招生计划(从专业组后缀估)
        plan_count = 30 if "国家专项" in group else (15 if "中外合作" in group else 60)
        # 学费
        tuition = 60000 if "中外合作" in group else 5500
        out.append({
            "year": year,
            "subject": subject,
            "school_name": school,
            "school_type": get_school_type(school),
            "group_id": group.replace("第", "").replace("组", "").zfill(2),
            "xuanke_req": xuanke,
            "xuanke_subjects": "物理|化学" if subject == "物理" else "历史",
            "plan_count": plan_count,
            "min_score": r["score"],
            "min_rank": r["rank"],
            "tuition_yuan": tuition,
            "city": get_school_city(school),
            "is_special": is_special,
        })
    return pd.DataFrame(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--subject", choices=["物理", "历史", "both"], default="both")
    args = parser.parse_args()

    subjects = ["物理", "历史"] if args.subject == "both" else [args.subject]
    for subj in subjects:
        records = fetch_year_admission(args.year, subj)
        if not records:
            print(f"❌ {args.year} {subj} 无数据")
            continue
        df = records_to_admission_csv(records, subj, args.year)
        # 去重(同一 group 可能多次出现)
        df = df.drop_duplicates(subset=["school_name", "group_id"], keep="first")
        target = DATA_DIR / f"hubei_admission_{subj}_{args.year}.csv"
        if target.exists():
            backup = LOG_DIR / f"{target.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            target.rename(backup)
            print(f"  📦 旧文件备份: {backup.name}")
        df.to_csv(target, index=False)
        print(f"✅ 写入 {target.name} ({len(df)} 行)")


if __name__ == "__main__":
    main()
