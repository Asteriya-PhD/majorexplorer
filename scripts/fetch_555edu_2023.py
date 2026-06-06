"""
scripts/fetch_555edu_2023.py — 2023 物理/历史 专用 fetcher
"""
import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0, str(Path(__file__).parent))
from fetch_555edu_hubei import fetch, get_school_list, CACHE_DIR, HEADERS

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"


def score_to_rank(score: int, rank_table: pd.DataFrame) -> int:
    df = rank_table.copy()
    df["score_int"] = df["score"].apply(
        lambda s: int(str(s).split("-")[0]) if "-" in str(s) else int(s)
    )
    eligible = df[df["score_int"] <= score]
    if eligible.empty:
        return 999999
    return int(eligible.loc[eligible["score_int"].idxmax()]["rank"])


def find_articles_2023(school_id: str, subject: str) -> str | None:
    """Paginate school article list to find 2023 湖北 article URL"""
    pattern = rf"2023年湖北.{{0,8}}{subject}"
    for page in range(1, 30):
        u = f"http://www.555edu.com/school-{school_id}-1-780/{page}"
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
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                time.sleep(0.5)
                continue
            except Exception:
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


def parse_article_cached(url: str, school_name: str, year: int, subject: str, rank_table: pd.DataFrame) -> list[dict]:
    """Parse the cached article (4 schemas: 10-col / 9-col / 8-col / 6-col)"""
    cache = CACHE_DIR / (url.replace("/", "_").replace(":", "") + ".html")
    if not cache.exists():
        txt = fetch(url)
        if not txt:
            return []
    else:
        txt = cache.read_text(encoding="utf-8", errors="replace")
    tables = re.findall(r'<table[^>]*>(.*?)</table>', txt, re.DOTALL)
    out = []
    for t in tables:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            cells_clean = [re.sub(r'<[^>]+>', ' ', c).strip() for c in cells]
            if not cells_clean:
                continue
            if any(k in cells_clean[0] for k in ['年份', '院校名称']):
                continue
            if len(cells_clean) < 5:
                continue
            # 新 (本科 10-col)
            if (len(cells_clean) >= 9 and re.match(r'^\d{4}$', cells_clean[1])
                    and cells_clean[2] in ('物理', '历史')):
                sname, y, subj, xuanke, group_code, group_name, batch, score, rank, note = cells_clean[:10]
                if y != str(year) or subj != subject:
                    continue
                if not (score.isdigit() and rank.isdigit()):
                    continue
                m = re.search(r'(\d+)$', group_code)
                g = m.group(1)[-2:].zfill(2) if m else group_code[-2:].zfill(2)
                out.append({"school_name": sname or school_name, "batch": batch,
                    "kind": note if note and note not in ('--', '/', '') else '普通类',
                    "min_score": int(score), "min_rank": int(rank),
                    "group_id": g, "group_name": group_name, "xuanke_req": xuanke})
            # 新 (高职高专 9-col)
            elif (len(cells_clean) >= 8 and re.match(r'^\d{4}$', cells_clean[1])
                    and cells_clean[3] in ('物理', '历史')):
                sname, y, batch, subj, group_name, xuanke, score, rank, note = cells_clean[:9]
                if y != str(year) or subj != subject:
                    continue
                if not (score.isdigit() and rank.isdigit()):
                    continue
                m = re.search(r'(\d+)', group_name)
                g = m.group(1).zfill(2) if m else "01"
                out.append({"school_name": sname or school_name, "batch": batch,
                    "kind": note if note and note not in ('--', '/', '') else '普通类',
                    "min_score": int(score), "min_rank": int(rank),
                    "group_id": g, "group_name": group_name, "xuanke_req": xuanke})
            # 2023 8-col: 院校名称 | 院校专业组代码 | 年份 | 科类 | 科目要求 | 批次 | 投档线 | 备注
            elif (len(cells_clean) >= 7 and cells_clean[0]
                    and re.match(r'^\d{4}$', cells_clean[2]) and cells_clean[3] in ('物理', '历史')):
                sname, group_code, y, subj, xuanke, batch, score, note = cells_clean[:8]
                if y != str(year) or subj != subject:
                    continue
                if not score.isdigit():
                    continue
                m = re.search(r'(\d+)$', group_code)
                g = m.group(1)[-2:].zfill(2) if m else group_code[-2:].zfill(2)
                rank = score_to_rank(int(score), rank_table)
                out.append({"school_name": sname or school_name, "batch": batch,
                    "kind": note if note and note not in ('--', '/', '') else '普通类',
                    "min_score": int(score), "min_rank": rank,
                    "group_id": g, "group_name": '', "xuanke_req": xuanke})
            # 旧 6-col
            else:
                if len(cells_clean) < 6:
                    continue
                y, batch, kind, score_rank, group, xuanke = cells_clean[:6]
                if y != str(year):
                    continue
                m = re.match(r'(\d+)\s*/\s*(\d+)', score_rank.replace(" ", ""))
                if not m:
                    continue
                score, rank = int(m.group(1)), int(m.group(2))
                g = re.sub(r'[^\d]', '', group)
                if not g:
                    continue
                out.append({"school_name": school_name, "batch": batch, "kind": kind,
                    "min_score": score, "min_rank": rank,
                    "group_id": g.zfill(2), "group_name": '', "xuanke_req": xuanke})
    return out


def main():
    schools = get_school_list()
    # Load rank tables for score->rank conversion
    rank_phys = pd.read_csv(DATA_DIR / "hubei_rank_物理_2023.csv")
    rank_hist = pd.read_csv(DATA_DIR / "hubei_rank_历史_2023.csv")

    results = {"历史": [], "物理": []}
    log = []
    for i, s in enumerate(schools):
        sid = s["school_id"]
        name = s["name"]
        for subject in ["物理", "历史"]:
            url = find_articles_2023(sid, subject)
            if not url:
                log.append({"school": name, "subject": subject, "status": "no_article"})
                continue
            rt = rank_phys if subject == "物理" else rank_hist
            rows = parse_article_cached(url, name, 2023, subject, rt)
            if rows:
                results[subject].extend(rows)
                log.append({"school": name, "subject": subject, "status": "ok", "rows": len(rows), "url": url})
            else:
                log.append({"school": name, "subject": subject, "status": "parse_fail", "url": url})
        if (i+1) % 20 == 0:
            ok_n = sum(1 for e in log if e.get('status') == 'ok')
            print(f"  [{i+1}/{len(schools)}] processed, ok: {ok_n}")
        time.sleep(0.2)

    for subj, rows in results.items():
        if not rows:
            print(f"{subj}: 0 rows")
            continue
        df = pd.DataFrame(rows).drop_duplicates(subset=['school_name', 'group_id'], keep='first')
        if "batch" in df.columns:
            df = df[df["batch"].fillna("").str.contains("本科|提前批", na=False)]
        df.insert(0, 'year', 2023)
        df.insert(1, 'subject', subj)
        out = DATA_DIR / f"hubei_admission_{subj}_2023_real_555edu.csv"
        df.to_csv(out, index=False)
        print(f"📦 {subj}: {len(df)} unique rows ({df['school_name'].nunique()} schools) → {out.name}")

    log_path = DATA_DIR / "_logs" / f"fetch_555edu_2023_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for e in log if e.get('status') == 'ok')
    print(f"📝 ok={ok} total={len(log)} log: {log_path.name}")


if __name__ == "__main__":
    main()
