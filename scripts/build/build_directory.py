#!/usr/bin/env python3
"""
build_directory.py — 13 门类 92 大类 868 专业 完整目录

数据源:
  - data/raw/majors_list.json: 868 chsi 候选 (moe_code/name/spec_id/satisfaction/...)
  - public/data/manifest.json: 337+ done (slug/title/category)
  - data/audit_registry.json: 237+ audited (score/verdict)
  - data/claimed.json: 当前 claimed 锁 (本地用, gitignore)

输出:
  - data/major_directory.json: 完整 13/92/868 树状 (git tracked, 单一真相)
  - docs/MAJOR_DIRECTORY.md: 人类可读 markdown 渲染 (git tracked, 给 user 看)

用法:
  python3 scripts/build_directory.py                    # 重建目录 (apply)
  python3 scripts/build_directory.py --stats           # 13 门类覆盖率
  python3 scripts/build_directory.py --stats --menjia 08  # 单门类
  python3 scripts/build_directory.py --render-md > docs/MAJOR_DIRECTORY.md
  python3 scripts/build_directory.py --check           # 只对比不写
"""
import argparse, json, re, sys, datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CHSI_POOL = ROOT / "data" / "raw" / "majors_list.json"
MANIFEST = ROOT / "public" / "data" / "manifest.json"
REGISTRY = ROOT / "data" / "audit_registry.json"
CLAIMED = ROOT / "data" / "claimed.json"
DIRECTORY = ROOT / "data" / "major_directory.json"

# 13 门类
MENJIA_ORDER = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"]
MENJIA_NAME = {
    "01": "哲学", "02": "经济学", "03": "法学", "04": "教育学",
    "05": "文学", "06": "历史学", "07": "理学", "08": "工学",
    "09": "农学", "10": "医学", "11": "军事学", "12": "管理学", "13": "艺术学",
}

def style_to_menjia(style):
    m = {
        "humanities": "05", "law": "03", "gongan": "03", "education": "04",
        "sci": "07", "eng": "08", "cs": "08", "agri": "09",
        "medicine": "10", "finance": "02", "business": "12",
        "administration": "12", "arts": "13",
    }
    return m.get(style, "08")


def load_sources():
    """加载所有数据源, 失败不阻断"""
    pool = json.load(open(CHSI_POOL)) if CHSI_POOL.exists() else []
    manifest = json.load(open(MANIFEST)) if MANIFEST.exists() else {"majors": []}
    registry = json.load(open(REGISTRY)) if REGISTRY.exists() else {"majors": {}}
    claimed = json.load(open(CLAIMED)).get("claims", {}) if CLAIMED.exists() else {}
    return pool, manifest.get("majors", []), registry.get("majors", {}), claimed


def match_done(pool_entry, done_by_title, done_by_slug):
    """匹配 pool entry 是否已完成, 返回 (status, slug, score, verdict) 或 (missing, ...)"""
    title = pool_entry["name"]
    moe = pool_entry["moe_code"]
    # 1. 精确匹配 title
    if title in done_by_title:
        slug = done_by_title[title]
        return ("done", slug, None, None)
    # 2. 模糊: slug 出现在 title
    for slug_t, slug_v in done_by_slug.items():
        if slug_t in title.lower() or title.lower() in slug_t:
            return ("done", slug_v, None, None)
    return ("missing", None, None, None)


def build():
    pool, manifest_majors, registry, claimed = load_sources()
    # done lookup
    done_by_title = {e["title"]: e["slug"] for e in manifest_majors}
    done_by_slug = {e["slug"]: e["slug"] for e in manifest_majors}

    # 13 门类 → 92 大类 → 868 专业
    directory = {
        "version": "1.0",
        "updated_at": datetime.datetime.now().isoformat(),
        "totals": {"menjia_count": 0, "subclass_count": 0, "major_count": 0,
                   "done": 0, "claimed": 0, "missing": 0},
        "menjia_stats": {},  # {code: {name, pool, done, claimed, missing, pct}}
        "menjia": {},
    }

    for code in MENJIA_ORDER:
        directory["menjia"][code] = {
            "name": MENJIA_NAME[code],
            "subclass": {},
        }

    # 遍历 pool
    for p in pool:
        mj_code = p["menjia_moe"]
        sub_code = p.get("subclass_chsi", mj_code + "00")[:4] if p.get("subclass_chsi") else mj_code + "00"
        sub_name = p.get("subclass_name", "未分类")
        major_code = p["moe_code"]
        title = p["name"]

        # 状态
        status, slug, _, _ = match_done(p, done_by_title, done_by_slug)
        audit_score = None
        audit_verdict = None
        if status == "done" and slug and slug in registry:
            entry = registry[slug]
            audit_score = entry.get("current_score")
            audit_verdict = entry.get("current_verdict")
        # claimed 覆盖 (status 提升为 claimed)
        if slug and slug in claimed:
            status = "claimed"

        # 写 sub-class
        mj = directory["menjia"][mj_code]
        if sub_code not in mj["subclass"]:
            mj["subclass"][sub_code] = {
                "name": sub_name,
                "majors": {},
            }
        mj["subclass"][sub_code]["majors"][major_code] = {
            "name": title,
            "moe_code": major_code,
            "status": status,
            "slug": slug,
            "audit_score": audit_score,
            "audit_verdict": audit_verdict,
            "claimed_by": claimed.get(slug, {}).get("claimed_by") if slug else None,
        }

    # 🆕 补 claimed.json 里没在 chsi pool / manifest 的 slug
    # 防止: agent claim 了 30 新 major, 目录漏显示
    # 即使 manifest 还没建, 也加 stub 让目录显示
    for slug, claim_info in claimed.items():
        # 检查是否已在 directory 里
        already_in_dir = False
        for mj_code, mj in directory["menjia"].items():
            for sub in mj["subclass"].values():
                for m in sub["majors"].values():
                    if m.get("slug") == slug:
                        already_in_dir = True
                        break
        if already_in_dir:
            continue
        # 查 manifest 看 title / style
        manifest_entry = next((e for e in manifest_majors if e.get("slug") == slug), None)
        if manifest_entry:
            title = manifest_entry.get("title", slug)
            style = manifest_entry.get("style", "eng")
        else:
            # 新 major, agent 还没建文件, 用 slug 作 fallback title
            title = slug.replace("-", " ").title()
            # 从 task 描述推断 style (e.g. "Day 5 10 篇 工科×创意" → eng)
            task = claim_info.get("task", "")
            if "humanities" in task or "文学" in task: style = "humanities"
            elif "工科" in task or "eng" in task: style = "eng"
            elif "农学" in task or "agri" in task: style = "agri"
            elif "公安" in task or "gongan" in task: style = "gongan"
            else: style = "eng"
        mj_code = style_to_menjia(style)
        sub_code = "9999"
        sub_name = "🆕 Claimed (待 chsi 收录 / agent 提交后归位)"
        major_code = f"NEW-{slug[:8].upper()}"
        mj = directory["menjia"][mj_code]
        if sub_code not in mj["subclass"]:
            mj["subclass"][sub_code] = {"name": sub_name, "majors": {}}
        mj["subclass"][sub_code]["majors"][major_code] = {
            "name": title,
            "moe_code": major_code,
            "status": "claimed",
            "slug": slug,
            "audit_score": None,
            "audit_verdict": None,
            "claimed_by": claim_info.get("claimed_by"),
        }

    # 统计
    for mj_code, mj in directory["menjia"].items():
        pool_n = done_n = claimed_n = missing_n = 0
        for sub in mj["subclass"].values():
            for m in sub["majors"].values():
                pool_n += 1
                if m["status"] == "done":
                    done_n += 1
                elif m["status"] == "claimed":
                    claimed_n += 1
                else:
                    missing_n += 1
        directory["menjia_stats"][mj_code] = {
            "name": MENJIA_NAME[mj_code],
            "pool": pool_n,
            "done": done_n,
            "claimed": claimed_n,
            "missing": missing_n,
            "pct": round(100 * done_n / pool_n, 1) if pool_n > 0 else 0,
        }
        directory["totals"]["major_count"] += pool_n
        directory["totals"]["done"] += done_n
        directory["totals"]["claimed"] += claimed_n
        directory["totals"]["missing"] += missing_n
    directory["totals"]["menjia_count"] = sum(1 for mj in directory["menjia"].values() if mj["subclass"])
    directory["totals"]["subclass_count"] = sum(len(mj["subclass"]) for mj in directory["menjia"].values())
    return directory


def cmd_apply():
    directory = build()
    DIRECTORY.parent.mkdir(parents=True, exist_ok=True)
    DIRECTORY.write_text(json.dumps(directory, ensure_ascii=False, indent=2), encoding="utf-8")
    t = directory["totals"]
    print(f"✅ 已写 {DIRECTORY}")
    print(f"   {t['menjia_count']} 门类 / {t['subclass_count']} 大类 / {t['major_count']} 专业")
    print(f"   done: {t['done']} / claimed: {t['claimed']} / missing: {t['missing']}")
    return 0


def cmd_stats(menjia=None):
    directory = build()
    if menjia:
        s = directory["menjia_stats"].get(menjia)
        if not s:
            print(f"❌ 无门类 {menjia}")
            return 1
        print(f"=== {s['name']} ({menjia}) ===")
        for k in ["pool", "done", "claimed", "missing", "pct"]:
            print(f"  {k:10s} {s[k]}")
    else:
        print(f"=== 13 门类覆盖率 (done / pool = pct) ===")
        for code in MENJIA_ORDER:
            s = directory["menjia_stats"].get(code, {})
            print(f"  {code} {s.get('name',''):6s}  {s.get('done',0):3d} / {s.get('pool',0):3d} = {s.get('pct',0):5.1f}%   (claimed {s.get('claimed',0)})")
        t = directory["totals"]
        print(f"\nTotal: {t['done']} done / {t['major_count']} pool = {round(100*t['done']/t['major_count'],1) if t['major_count']>0 else 0}%")
    return 0


def cmd_render_md():
    directory = build()
    lines = []
    lines.append(f"# 13 门类 / 92 大类 / 868 专业 完整目录")
    lines.append(f"")
    lines.append(f"> 更新于 {directory['updated_at']}")
    t = directory["totals"]
    lines.append(f"> Total: {t['done']} done / {t['claimed']} claimed / {t['missing']} missing / {t['major_count']} pool = {round(100*t['done']/t['major_count'],1) if t['major_count']>0 else 0}% 覆盖")
    lines.append(f"")
    lines.append(f"**图例**: ✅ done (有 audit 分数) | 🟡 claimed (被领) | ⚪ missing (未做) | ❓ done but no audit")
    lines.append(f"")
    for code in MENJIA_ORDER:
        s = directory["menjia_stats"].get(code, {})
        if s.get("pool", 0) == 0:
            continue
        lines.append(f"## {code} {s.get('name','')} ({s.get('done',0)}/{s.get('pool',0)} = {s.get('pct',0)}%)")
        mj = directory["menjia"][code]
        for sub_code in sorted(mj["subclass"].keys()):
            sub = mj["subclass"][sub_code]
            lines.append(f"")
            lines.append(f"### {sub_code} {sub['name']} ({sum(1 for m in sub['majors'].values() if m['status']=='done')}/{len(sub['majors'])})")
            for mcode in sorted(sub["majors"].keys()):
                m = sub["majors"][mcode]
                if m["status"] == "done":
                    score = m.get("audit_score")
                    verdict = m.get("audit_verdict", "")
                    icon = "❓" if score is None else "✅"
                    score_str = f" (audit: {score}/10 {verdict})" if score else ""
                    lines.append(f"- {icon} **{m['name']}** ({mcode}){score_str}")
                elif m["status"] == "claimed":
                    lines.append(f"- 🟡 {m['name']} ({mcode}) _claimed by {m.get('claimed_by','?')}_")
                else:
                    lines.append(f"- ⚪ {m['name']} ({mcode})")
        lines.append("")
    print("\n".join(lines))
    return 0


def cmd_check():
    if not DIRECTORY.exists():
        print(f"❌ {DIRECTORY} 不存在, 跑 build_directory.py 生成")
        return 1
    old = json.load(open(DIRECTORY))
    new = build()
    if old.get("totals") == new.get("totals") and old.get("menjia_stats") == new.get("menjia_stats"):
        print("✅ 目录无变化")
        return 0
    print("⚠️ 目录有变化:")
    print(f"   old totals: {old.get('totals')}")
    print(f"   new totals: {new.get('totals')}")
    print("   跑 `python3 scripts/build_directory.py` 更新")
    return 1


def main():
    ap = argparse.ArgumentParser(description="构建 13 门类完整目录", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--stats", action="store_true", help="显示 13 门类统计")
    ap.add_argument("--menjia", help="指定门类 (e.g. 08)")
    ap.add_argument("--render-md", action="store_true", help="渲染 markdown 输出到 stdout")
    ap.add_argument("--check", action="store_true", help="对比模式")
    args = ap.parse_args()
    if args.stats:
        sys.exit(cmd_stats(args.menjia))
    if args.render_md:
        sys.exit(cmd_render_md())
    if args.check:
        sys.exit(cmd_check())
    sys.exit(cmd_apply())


if __name__ == "__main__":
    main()
