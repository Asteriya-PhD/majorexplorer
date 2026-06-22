"""
scripts/fetch_555edu_guangdong_jiangsu.py — 抓 555edu 广东/江苏 2024 投档线
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
from fetch_555edu_hubei import fetch, CACHE_DIR, HEADERS
from fetch_dxsbb_6261 import score_to_rank

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"


def get_school_list(province: str) -> list[dict]:
    """Get 555edu school list for given province"""
    u = f"http://www.555edu.com/{province}/"
    txt = fetch(u)
    if not txt:
        return []
    # Decode GBK
    if isinstance(txt, bytes):
        try: txt = txt.decode('gbk', errors='replace')
        except: txt = txt.decode('utf-8', errors='replace')
    links = re.findall(r'href="(/school-(\d+)/)"[^>]*>([^<]*)</a>', txt)
    seen = set()
    out = []
    for h, sid, t in links:
        if sid in seen: continue
        seen.add(sid)
        t = t.strip()
        if t and t not in ('院校直通车', '高校首页'):
            out.append({"school_id": sid, "name": t, "url": f"http://www.555edu.com{h}"})
    return out


def find_articles(school_id: str, province: str, year: int, subject: str) -> str | None:
    """Find 555edu article for given school+province+year+subject"""
    subject_kw = subject
    pattern = rf"{year}年{province_name(province)}.{{0,8}}{subject_kw}"
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
                        c = data.decode(enc)
                        cache.write_text(c, encoding="utf-8")
                        break
                    except UnicodeDecodeError:
                        continue
            except urllib.error.HTTPError as e:
                if e.code == 404: break
                time.sleep(0.5); continue
            except Exception:
                time.sleep(0.5); continue
        txt = cache.read_text(encoding="utf-8", errors="replace")
        if not txt: break
        links = re.findall(r'href="(/school-'+school_id+'-1-780/\d+\.html)"[^>]*>([^<]*)</a>', txt)
        if not links: break
        for h, t in links:
            t = t.strip()
            if re.search(pattern, t):
                return f"http://www.555edu.com{h}"
    return None


def province_name(prov: str) -> str:
    """Map pinyin to Chinese name"""
    return {"guangdong": "广东", "jiangsu": "江苏", "hubei": "湖北"}.get(prov, prov)


def parse_article_cached(url: str, school_name: str, year: int, subject: str, province: str, rank_table: pd.DataFrame) -> list[dict]:
    """Parse 555edu article (handles 4 schemas)"""
    cache = CACHE_DIR / (url.replace("/", "_").replace(":", "") + ".html")
    if not cache.exists():
        txt = fetch(url)
        if not txt: return []
    else:
        txt = cache.read_text(encoding="utf-8", errors="replace")
    tables = re.findall(r'<table[^>]*>(.*?)</table>', txt, re.DOTALL)
    out = []
    for t in tables:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            cells_clean = [re.sub(r'<[^>]+>', ' ', c).strip() for c in cells]
            if not cells_clean: continue
            if any(k in cells_clean[0] for k in ['年份', '院校名称']): continue
            if len(cells_clean) < 5: continue
            # 新 (本科 10-col)
            if (len(cells_clean) >= 9 and re.match(r'^\d{4}$', cells_clean[1])
                    and cells_clean[2] in ('物理', '历史')):
                sname, y, subj, xuanke, group_code, group_name, batch, score, rank, note = cells_clean[:10]
                if y != str(year) or subj != subject: continue
                if not (score.isdigit() and rank.isdigit()): continue
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
                if y != str(year) or subj != subject: continue
                if not (score.isdigit() and rank.isdigit()): continue
                m = re.search(r'(\d+)', group_name)
                g = m.group(1).zfill(2) if m else "01"
                out.append({"school_name": sname or school_name, "batch": batch,
                    "kind": note if note and note not in ('--', '/', '') else '普通类',
                    "min_score": int(score), "min_rank": int(rank),
                    "group_id": g, "group_name": group_name, "xuanke_req": xuanke})
            # 2023 8-col
            elif (len(cells_clean) >= 7 and cells_clean[0]
                    and re.match(r'^\d{4}$', cells_clean[2]) and cells_clean[3] in ('物理', '历史')):
                sname, group_code, y, subj, xuanke, batch, score, note = cells_clean[:8]
                if y != str(year) or subj != subject: continue
                if not score.isdigit(): continue
                m = re.search(r'(\d+)$', group_code)
                g = m.group(1)[-2:].zfill(2) if m else group_code[-2:].zfill(2)
                rank = score_to_rank(int(score), rank_table) if rank_table is not None else 0
                out.append({"school_name": sname or school_name, "batch": batch,
                    "kind": note if note and note not in ('--', '/', '') else '普通类',
                    "min_score": int(score), "min_rank": rank,
                    "group_id": g, "group_name": '', "xuanke_req": xuanke})
            # 2024 广东 7-col: 院校名称 | 年份 | 科类 | 选科要求 | 批次 | 投档线 | 投档线位次 | 备注
            elif (len(cells_clean) >= 7 and cells_clean[0]
                    and re.match(r'^\d{4}$', cells_clean[1]) and cells_clean[2] in ('物理', '历史')
                    and len(cells_clean) <= 8):
                sname, y, subj, xuanke, batch, score, rank, note = cells_clean[:8]
                if y != str(year) or subj != subject: continue
                if not (score.isdigit() and rank.isdigit()): continue
                # use group_id = "01" since no 专业组 code
                out.append({"school_name": sname or school_name, "batch": batch,
                    "kind": note if note and note not in ('--', '/', '') else '普通类',
                    "min_score": int(score), "min_rank": int(rank),
                    "group_id": "01", "group_name": '', "xuanke_req": xuanke})
            else:
                if len(cells_clean) < 6: continue
                y, batch, kind, score_rank, group, xuanke = cells_clean[:6]
                if y != str(year): continue
                m = re.match(r'(\d+)\s*/\s*(\d+)', score_rank.replace(" ", ""))
                if not m: continue
                score, rank = int(m.group(1)), int(m.group(2))
                g = re.sub(r'[^\d]', '', group)
                if not g: continue
                out.append({"school_name": school_name, "batch": batch, "kind": kind,
                    "min_score": score, "min_rank": rank,
                    "group_id": g.zfill(2), "group_name": '', "xuanke_req": xuanke})
    return out


def main(province: str = "guangdong", year: int = 2024):
    schools = get_school_list(province)
    print(f"📋 {province} {len(schools)} 校")
    rank_phys = pd.read_csv(DATA_DIR / f"{province}_rank_物理_{year}.csv") if (DATA_DIR / f"{province}_rank_物理_{year}.csv").exists() else None
    rank_hist = pd.read_csv(DATA_DIR / f"{province}_rank_历史_{year}.csv") if (DATA_DIR / f"{province}_rank_历史_{year}.csv").exists() else None
    if rank_phys is None or rank_hist is None:
        print(f"⚠️ 缺 {province} 一分一段表,无法 score→rank 转换")
        return
    results = {"历史": [], "物理": []}
    log = []
    for i, s in enumerate(schools):
        sid = s["school_id"]; name = s["name"]
        for subject in ["物理", "历史"]:
            url = find_articles(sid, province, year, subject)
            if not url:
                log.append({"school": name, "subject": subject, "status": "no_article"})
                continue
            rt = rank_phys if subject == "物理" else rank_hist
            rows = parse_article_cached(url, name, year, subject, province, rt)
            if rows:
                results[subject].extend(rows)
                log.append({"school": name, "subject": subject, "status": "ok", "rows": len(rows)})
            else:
                log.append({"school": name, "subject": subject, "status": "parse_fail"})
        if (i+1) % 30 == 0:
            ok_n = sum(1 for e in log if e.get('status') == 'ok')
            print(f"  [{i+1}/{len(schools)}] ok: {ok_n}")
        time.sleep(0.15)

    for subj, rows in results.items():
        if not rows: continue
        df = pd.DataFrame(rows).drop_duplicates(subset=['school_name','group_id'], keep='first')
        if "batch" in df.columns:
            df = df[df["batch"].fillna("").str.contains("本科|提前批", na=False)]
        df.insert(0, 'year', year)
        df.insert(1, 'subject', subj)
        out = DATA_DIR / f"{province}_admission_{subj}_{year}_real_555edu.csv"
        df.to_csv(out, index=False)
        print(f"📦 {subj}: {len(df)} 行 ({df['school_name'].nunique()} 校) → {out.name}")
    log_path = DATA_DIR / "_logs" / f"fetch_555edu_{province}_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for e in log if e.get('status') == 'ok')
    print(f"📝 ok={ok}/{len(log)}")


if __name__ == "__main__":
    import sys
    prov = sys.argv[1] if len(sys.argv) > 1 else "guangdong"
    yr = int(sys.argv[2]) if len(sys.argv) > 2 else 2024
    main(prov, yr)
