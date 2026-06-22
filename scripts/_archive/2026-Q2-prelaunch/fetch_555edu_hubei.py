"""
scripts/fetch_555edu_hubei.py — 用 555edu 逐校抓 湖北本地 2024 投档线

策略:
1. 555edu.com/hubei/ 列出 135 个 湖北本地 校 + school_id
2. 每个校的 /school-{id}-1-780/{page} 列表,翻 25 页
3. 找 "2024年湖北历史类" / "2024年湖北物理类" 文章链接
4. 访问文章,parse 6 列表格:
   年份 | 录取批次 | 招生类型 | 最低分/最低位次 | 专业组 | 选科要求

输出: data/hubei_admission_{物理|历史}_2024_real_555edu.csv
"""
import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
CACHE_DIR = PROJECT_DIR / "data" / "_cache" / "555edu"
LOG_DIR = PROJECT_DIR / "data" / "_logs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
}


def fetch(url: str, retries: int = 3, use_gbk: bool = True, timeout: int = 15) -> str | None:
    cache = CACHE_DIR / (url.replace("/", "_").replace(":", "") + ".html")
    if cache.exists():
        return cache.read_text(encoding="utf-8", errors="replace")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            for enc in (("gbk", "gb18030", "utf-8") if use_gbk else ("utf-8", "gbk", "gb18030")):
                try:
                    txt = data.decode(enc)
                    cache.write_text(txt, encoding="utf-8")
                    return txt
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  ⚠️ {url[:80]} retry {i+1}: {e}")
            time.sleep(1.5 ** i)
    return None


def get_school_list() -> list[dict]:
    """Get 135 湖北 schools with name + school_id"""
    txt = fetch("http://www.555edu.com/hubei/")
    if not txt:
        return []
    links = re.findall(r'href="(/school-(\d+)/)"[^>]*>([^<]*)</a>', txt)
    seen = set()
    out = []
    for h, sid, t in links:
        if sid in seen:
            continue
        seen.add(sid)
        t = t.strip()
        if t and t not in ("院校直通车", "高校首页"):
            out.append({"school_id": sid, "name": t, "url": f"http://www.555edu.com{h}"})
    return out


def find_articles(school_id: str, year: int = 2024, subject: str = "历史") -> str | None:
    """Paginate school article list to find 2024 湖北 {subject} article URL"""
    subject_kw = "历史" if subject == "历史" else "物理"
    pattern = rf"{year}年湖北.{{0,8}}{subject_kw}"
    for page in range(1, 30):  # up to 30 pages
        u = f"http://www.555edu.com/school-{school_id}-1-780/{page}"
        # 404 = no more pages, don't retry
        cache = CACHE_DIR / (u.replace("/", "_").replace(":", "") + ".html")
        if not cache.exists():
            try:
                req = urllib.request.Request(u, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = r.read()
                for enc in ("gbk", "gb18030", "utf-8"):
                    try:
                        txt = data.decode(enc)
                        cache.write_text(txt, encoding="utf-8")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    txt = data.decode("utf-8", errors="replace")
                    cache.write_text(txt, encoding="utf-8")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                print(f"  ⚠️ {u[:80]} HTTP {e.code}")
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"  ⚠️ {u[:80]} {e}")
                time.sleep(0.5)
                continue
        txt = cache.read_text(encoding="utf-8", errors="replace")
        if not txt:
            break
        links = re.findall(r'href="(/school-'+school_id+'-1-780/\d+\.html)"[^>]*>([^<]*)</a>', txt)
        if not links:
            break
        for h, t in links:
            t = t.strip()
            if re.search(pattern, t):
                return f"http://www.555edu.com{h}"
    return None


def parse_article(url: str, school_name: str, year: int = 2024, subject: str = "历史") -> list[dict]:
    """Parse 555edu article table.

    Three schemas observed:
    1. 旧: 年份 | 批次 | 招生类型 | 最低分/最低位次 | 专业组 | 选科要求
    2. 新 (本科): 院校名称 | 年份 | 科类 | 选科要求 | 院校专业组代码 | 专业组名称 | 批次 | 投档线 | 投档线位次 | 备注
    3. 新 (高职高专): 院校名称 | 年份 | 批次 | 科类 | 专业组名称 | 选科要求 | 投档线 | 投档线位次 | 备注
    """
    txt = fetch(url)
    if not txt:
        return []
    tables = re.findall(r'<table[^>]*>(.*?)</table>', txt, re.DOTALL)
    out = []
    for t in tables:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            cells_clean = [re.sub(r'<[^>]+>', ' ', c).strip() for c in cells]
            if not cells_clean or "年份" in cells_clean[0] or "院校名称" in cells_clean[0]:
                continue
            if len(cells_clean) < 5:
                continue
            # Schema detection: check if cells[1] is year (4 digits)
            # And if cells[2]/[3] is 科类
            # 新 (本科): sname, y, subj, xuanke, group_code, group_name, batch, score, rank, note
            if (len(cells_clean) >= 9 and re.match(r'^\d{4}$', cells_clean[1])
                    and cells_clean[2] in ("物理", "历史")):
                try:
                    sname, y, subj, xuanke, group_code, group_name, batch, score, rank, note = cells_clean[:10]
                except ValueError:
                    continue
                if y != str(year) or subj != subject:
                    continue
                if not (score.isdigit() and rank.isdigit()):
                    continue
                m = re.search(r'(\d+)$', group_code)
                g = m.group(1)[-2:].zfill(2) if m else group_code[-2:].zfill(2)
                out.append({
                    "year": year, "subject": subject,
                    "school_name": sname or school_name,
                    "batch": batch,
                    "kind": note if note and note not in ("--", "/", "") else "普通类",
                    "min_score": int(score), "min_rank": int(rank),
                    "group_id": g, "group_name": group_name,
                    "xuanke_req": xuanke, "source_url": url,
                })
            # 新 (高职高专): sname, y, batch, subj, group_name, xuanke, score, rank, note
            elif (len(cells_clean) >= 8 and re.match(r'^\d{4}$', cells_clean[1])
                    and cells_clean[3] in ("物理", "历史")):
                try:
                    sname, y, batch, subj, group_name, xuanke, score, rank, note = cells_clean[:9]
                except ValueError:
                    continue
                if y != str(year) or subj != subject:
                    continue
                if not (score.isdigit() and rank.isdigit()):
                    continue
                # Extract group id from "第04组"
                m = re.search(r'(\d+)', group_name)
                g = m.group(1).zfill(2) if m else "01"
                out.append({
                    "year": year, "subject": subject,
                    "school_name": sname or school_name,
                    "batch": batch,
                    "kind": note if note and note not in ("--", "/", "") else "普通类",
                    "min_score": int(score), "min_rank": int(rank),
                    "group_id": g, "group_name": group_name,
                    "xuanke_req": xuanke, "source_url": url,
                })
            # 旧: y, batch, kind, score_rank, group, xuanke
            else:
                try:
                    y, batch, kind, score_rank, group, xuanke = cells_clean[:6]
                except ValueError:
                    continue
                if y != str(year):
                    continue
                m = re.match(r'(\d+)\s*/\s*(\d+)', score_rank.replace(" ", ""))
                if not m:
                    continue
                score, rank = int(m.group(1)), int(m.group(2))
                g = re.sub(r'[^\d]', '', group)
                if not g:
                    continue
                out.append({
                    "year": year, "subject": subject,
                    "school_name": school_name,
                    "batch": batch, "kind": kind,
                    "min_score": score, "min_rank": rank,
                    "group_id": g.zfill(2), "group_name": "",
                    "xuanke_req": xuanke, "source_url": url,
                })
    return out


def main():
    print("📋 拉 555edu 湖北院校列表...")
    schools = get_school_list()
    print(f"  {len(schools)} 校")

    results = {"历史": [], "物理": []}
    log = []
    for i, s in enumerate(schools):
        sid = s["school_id"]
        name = s["name"]
        print(f"\n[{i+1}/{len(schools)}] {name} (id={sid})")
        for subject in ["历史", "物理"]:
            url = find_articles(sid, 2024, subject)
            if not url:
                log.append({"school": name, "subject": subject, "status": "no_article"})
                print(f"  ⚠️ {subject} 没找到 2024 湖北 文章")
                continue
            rows = parse_article(url, name, 2024, subject)
            if rows:
                results[subject].extend(rows)
                log.append({"school": name, "subject": subject, "status": "ok", "rows": len(rows), "url": url})
                print(f"  ✅ {subject}: {len(rows)} 行 ({url})")
            else:
                log.append({"school": name, "subject": subject, "status": "parse_fail", "url": url})
                print(f"  ⚠️ {subject} parse 失败 ({url})")
        # Rate limit
        time.sleep(0.3)

    # Save
    for subj, rows in results.items():
        df = pd.DataFrame(rows)
        out = DATA_DIR / f"hubei_admission_{subj}_2024_real_555edu.csv"
        df.to_csv(out, index=False)
        print(f"\n📦 {subj}: {len(df)} 行 → {out.name}")

    # log
    log_path = LOG_DIR / f"fetch_555edu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📝 log: {log_path.name}")


if __name__ == "__main__":
    main()
