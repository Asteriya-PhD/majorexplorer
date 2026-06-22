"""
scripts/fetch_eolcn_gd_js.py — 抓 eol.cn (教育在线) 广东/江苏 2024 数据

数据源:
1. 录取最低分数线 (cutoff lines) — eol.cn 每年 6 月发布
2. 本科批 征求志愿 投档线 — eol.cn 每年 7-8 月发布 (二轮补录, 校数较少)
3. (未来) 一分一段表 — eol.cn shuju 频道

注: eol.cn 没有完整的"院校专业组"投档表, 完整数据在 eea.gd.gov.cn (广东省考试院) /
    jseea.cn (江苏省考试院) 的 Excel 附件. 本脚本只覆盖 eol.cn 公开的部分.

输出:
  data/{province}_admission_{subject}_{year}_real_eolcn.csv (征求志愿 部分)
  data/{province}_cutoff_{year}_eolcn.json (录取最低分 线)
"""
import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
CACHE_DIR = DATA_DIR / "_cache" / "eolcn"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

PROVINCE_SLUG = {
    "guangdong": "guang_dong",
    "jiangsu": "jiang_su",
    "hubei": "hu_bei",
}

PROVINCE_CN = {"guangdong": "广东", "jiangsu": "江苏", "hubei": "湖北"}


def fetch(url: str, timeout: int = 15) -> str | None:
    """Fetch URL with caching. Returns decoded text or None."""
    cache = CACHE_DIR / (url.replace("/", "_").replace(":", "") + ".html")
    if cache.exists():
        return cache.read_text(encoding="utf-8", errors="replace")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        # GBK / UTF-8 都试一下
        for enc in ("utf-8", "gbk", "gb18030"):
            try:
                txt = data.decode(enc)
                cache.write_text(txt, encoding="utf-8")
                return txt
            except UnicodeDecodeError:
                continue
        # 兜底: replace
        txt = data.decode("utf-8", errors="replace")
        cache.write_text(txt, encoding="utf-8")
        return txt
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"    ⚠️  fetch failed: {url} ({e})")
        return None


# 已知 eol.cn 2024 关键页面 (按发布日期)
# 模式: gaokao.eol.cn/{province_slug}/dongtai/YYYYMM/tYYYYMMDD_NNNNNNN.shtml
EOLCN_2024_PAGES = {
    "guangdong": {
        "20240625_cutoff": "https://gaokao.eol.cn/guang_dong/dongtai/202406/t20240625_2619168.shtml",
        "20240725_征集": "https://gaokao.eol.cn/guang_dong/dongtai/202407/t20240725_2626227.shtml",
    },
    "jiangsu": {
        # 2024-06-24 江苏省教育考试院发布第一阶段录取控制分数线
        "20240624_cutoff": "https://gaokao.eol.cn/jiang_su/dongtai/202406/t20240624_2618817.shtml",
        "20240724_征集_物理": "https://gaokao.eol.cn/jiang_su/dongtai/202407/t20240724_2625986.shtml",
    },
}


def parse_征求志愿_投档线(html: str, subject: str, province: str) -> list[dict]:
    """从 eol.cn 征求志愿 HTML 解析 (院校, 投档最低分) 列表.

    HTML 格式 (江苏 eol.cn):
    院校代号 院校、专业组(再选科目要求) 投档最低分 排序项...
    例: 1117 南京体育学院03专业组(不限)(中外合作办学) 485 178 101 112 68 64 1

    返回: school_name (clean) + group_id + xuanke_req + is_special + min_score
    """
    rows = []
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    for t in tables:
        trs = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
        for tr in trs:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', ' ', c).strip() for c in cells]
            if not cells or len(cells) < 3: continue
            first = cells[0]
            if not first.isdigit(): continue
            if any(k in first for k in ['代号', '院校', '投档', '最低']): continue
            full = cells[1]  # "南京体育学院03专业组(不限)(中外合作办学)"
            score = cells[2]
            if not (score.isdigit() and 200 <= int(score) <= 700): continue
            if not full: continue
            # 拆解: 学校名 + NN专业组 + (xuanke) + (...special...)
            m = re.match(r"^(.+?)(\d{2})专业组[（(]([^）)]+)[）)](.*)$", full)
            if m:
                school = m.group(1).strip()
                gid = m.group(2)
                xuanke = m.group(3).strip()
                rest = m.group(4)
                is_special = "是" if any(k in rest for k in ["中外合作", "联合培养", "专项", "预科", "民族", "校区", "分校"]) else "否"
            else:
                # fallback: 全名当 school
                school = re.sub(r"\d{2}专业组.*$", "", full).strip() or full
                gid = "01"
                xuanke = "不限"
                is_special = "否"
            rows.append({
                "school_name": school,
                "group_id": gid,
                "xuanke_req": xuanke,
                "is_special": is_special,
                "group_name": full,
                "min_score": int(score),
                "subject": subject,
                "source": "eol.cn 征求志愿",
            })
    return rows


def parse_cutoff_lines(html: str) -> dict:
    """从录取最低分数线 HTML 提取各批次最低分.

    eol.cn 页面结构: 段标题 (一/二/三/四/五) 下面有 (一)(二)(三) 子标题.
    用 section 切片, 在每段内找 "普通类（X）: 总分 Y 分" 第一次出现.

    返回: {section_subject: score}, section ∈ 本科批 / 特殊类型 / 地方专项 / 专科批 / 教师专项
    """
    out = {}
    # 找所有 (一) (二) (三) ... (五) 子标题位置
    section_pat = re.compile(r"[（(][一二三四五六七八九十]+[）)]")
    # 主标题 (一/二/三/...) 也算
    main_pat = re.compile(r"<b>\s*[一二三四五六七八九十]+、[^<]+</b>")
    # 找所有 section 边界
    boundaries = []
    for m in main_pat.finditer(html):
        boundaries.append((m.start(), m.group(0)))
    # 子标题也算 (用于更细的分类)
    for m in section_pat.finditer(html):
        # 找该子标题的"语义标签"
        ctx = html[max(0, m.start() - 100):m.start() + 50]
        # 简单标签: 看 ctx 是否含 关键 marker
        label = None
        if "本科各科类" in ctx or ("本科院校" in ctx and "批次" not in ctx):
            label = "本科批"
        elif "特殊类型招生录取控制线" in ctx:
            label = "特殊类型控制线"
        elif "地方专项计划" in ctx:
            label = "地方专项"
        elif "教师专项计划" in ctx:
            label = "教师专项"
        elif "专科院校" in ctx:
            label = "专科批"
        elif "军队本科批次" in ctx:
            label = "军队本科"
        elif "中国消防救援学院" in ctx:
            label = "消防救援"
        elif "本科院校订单定向" in ctx:
            label = "教师专项"
        if label:
            boundaries.append((m.start(), label))
    boundaries.sort()

    # 找所有 "普通类（X）:总分 Y 分" 位置
    line_pat = re.compile(r"普通类[（(](物理|历史)[）)][^:：]*[：:]\s*总分\s*(\d+)\s*分")

    for m in line_pat.finditer(html):
        subj = m.group(1)
        score = int(m.group(2))
        # 找最近的 boundary (往前)
        label = None
        for pos, lab in reversed(boundaries):
            if pos < m.start():
                label = lab if lab in ["本科批", "特殊类型控制线", "地方专项", "教师专项", "专科批", "军队本科", "消防救援"] else None
                if label: break
        if not label:
            continue
        key = f"{label}_{subj}"
        # 第一次出现优先 (本科批 + 历史/物理 各只取一次)
        if key not in out:
            out[key] = score
    return out


def main(province: str = "guangdong", year: int = 2024):
    slug = PROVINCE_SLUG.get(province)
    if not slug:
        print(f"⚠️ 不支持: {province}")
        return
    pages = EOLCN_2024_PAGES.get(province, {})
    print(f"📋 {province} {year} 共 {len(pages)} 个 eol.cn 页面")

    all_征求 = []
    cutoffs = {}

    for tag, url in pages.items():
        print(f"  抓 {tag} → {url}")
        html = fetch(url)
        if not html:
            continue
        if "cutoff" in tag:
            cutoffs = parse_cutoff_lines(html)
            print(f"    最低分线: {cutoffs}")
        elif "征集" in tag or "物理" in tag:
            # 默认物理 (eol.cn 经常分物理/历史 两个页面, 但 URL 模式相似)
            for subject in ["物理", "历史"]:
                rs = parse_征求志愿_投档线(html, subject, province)
                all_征求.extend(rs)
                print(f"    {subject}: {len(rs)} 行")
        time.sleep(0.3)

    # 保存 cutoff
    if cutoffs:
        out = DATA_DIR / f"{province}_cutoff_{year}_eolcn.json"
        out.write_text(json.dumps(cutoffs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"📦 {out.name}: {cutoffs}")

    # 保存征求志愿
    if all_征求:
        out = DATA_DIR / f"{province}_admission_2024_real_eolcn.csv"
        import pandas as pd
        df = pd.DataFrame(all_征求).drop_duplicates(subset=["school_name", "subject"], keep="first")
        df.to_csv(out, index=False)
        print(f"📦 {out.name}: {len(df)} 行")


if __name__ == "__main__":
    prov = sys.argv[1] if len(sys.argv) > 1 else "guangdong"
    yr = int(sys.argv[2]) if len(sys.argv) > 2 else 2024
    main(prov, yr)
