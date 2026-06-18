#!/usr/bin/env python3
"""
rebuild_manifest.py — 从 curated/*.json 重建 public/data/manifest.json

为啥需要:
  - manifest.json 是 major 列表的"部署视图" (前端 + 搜索 + 索引依赖)
  - 旧 manifest 容易漏同步: 新增 major JSON commit 后, 主页/搜索/聚合页看不到 (历史 bug: 210 vs 277 漏 64)
  - 这工具保证 commit 后 1 条命令同步, 避免下次 batch 写完主页又少几篇

数据源:  skills/gaokao-major-explorer/data/curated/*.json
输出:    public/data/manifest.json (含 total/count/styles_used/overview_v2/majors[])

字段映射 (major JSON → manifest entry):
  - title, slug, category, style, degree, duration_years, tags
  - data_source (人工精编标注)
  - html_path / data_path (相对 public/ 的路径, 跟现有 manifest 保持一致)
  - discipline, sub_discipline, menjia_moe, menjia_name, theme_color (从 major JSON 读)
  - status 永远 "done" (只有写过 JSON 的才进 manifest)

用法:
  python3 scripts/rebuild_manifest.py                # 重建并写入
  python3 scripts/rebuild_manifest.py --dry-run      # 只看 diff, 不写
  python3 scripts/rebuild_manifest.py --check        # 只对比当前 manifest, exit 0/1 报告
  python3 scripts/rebuild_manifest.py --add-slug foo # 单篇补登记 (新 major commit 后)
"""
import argparse, json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "curated_data" if (ROOT / "skills" / "gaokao-major-explorer" / "curated_data").exists() else ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
MANIFEST = ROOT / "public" / "data" / "manifest.json"

# manifest entry 字段顺序 (跟现有 277 保持 byte-identical 兼容)
ENTRY_KEYS = [
    "slug", "title", "category", "style", "degree", "duration_years", "tags",
    "status", "data_source", "html_path", "data_path",
    "discipline", "sub_discipline", "menjia_moe", "menjia_name", "theme_color",
]

# 排除的非 major 文件
EXCLUDE_SLUGS = {"TEMPLATE", "template", "README", "_index", "manifest", "_manifest"}


def build_entry(slug: str, data: dict) -> dict:
    """从 major JSON 构造 manifest entry (字段顺序固定, 跟旧版兼容)"""
    e = {"slug": slug}
    for k in ENTRY_KEYS[1:]:
        v = data.get(k)
        e[k] = v  # 允许 None (跟旧 manifest 保持一致, 比如老 major 没 theme_color)
    return e


def collect_majors():
    """扫 curated/*.json → [(slug, data), ...]"""
    out = []
    for f in sorted(CURATED.glob("*.json")):
        slug = f.stem
        if slug in EXCLUDE_SLUGS:
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  {slug}: 解析失败 {e}", file=sys.stderr)
            continue
        # 必须有 title 才算有效 major
        if not data.get("title"):
            print(f"⚠️  {slug}: 缺 title 字段, 跳过", file=sys.stderr)
            continue
        # 强制 slug 跟 filename 一致 (避免 JSON 内 slug 跟文件名不一致)
        if data.get("slug") and data["slug"] != slug:
            print(f"⚠️  {slug}: JSON 内 slug={data['slug']} 跟 filename 不一致, 用 filename")
        data["slug"] = slug
        out.append((slug, data))
    return out


def build_manifest(majors: list) -> dict:
    """构造完整 manifest (跟旧 schema 兼容)"""
    entries = [build_entry(slug, data) for slug, data in majors]
    styles_used = sorted({e["style"] for e in entries if e.get("style")})
    now = datetime.datetime.now().isoformat()
    return {
        "version": "0.3.0",
        "updated_at": now,
        "total": len(entries),
        "styles_used": styles_used,
        "overview_v2": {
            "lede": "",
            "what": {"foundations": [], "directions": [], "skills": [], "bonus": ""},
            "fit": {"yes": [], "no": []},
            "pitfalls": [],
        },
        "count": len(entries),
        "majors": entries,
    }


def cmd_rebuild(dry_run: bool, check_only: bool):
    majors = collect_majors()
    new = build_manifest(majors)

    # check 模式: 对比当前 manifest
    if check_only:
        if not MANIFEST.exists():
            print(f"❌ {MANIFEST} 不存在")
            return 1
        old = json.loads(MANIFEST.read_text(encoding="utf-8"))
        old_slugs = {m["slug"] for m in old.get("majors", [])}
        new_slugs = {m["slug"] for m in new["majors"]}
        added = new_slugs - old_slugs
        removed = old_slugs - new_slugs
        print(f"当前 manifest: {len(old_slugs)} 篇")
        print(f"重建结果:     {new['total']} 篇")
        if added:
            print(f"\n新增 ({len(added)}):")
            for s in sorted(added):
                print(f"  + {s}")
        if removed:
            print(f"\n移除 ({len(removed)}):")
            for s in sorted(removed):
                print(f"  - {s}")
        if not added and not removed and old_slugs == new_slugs:
            print("\n✅ 完全一致")
            return 0
        print("\n⚠️  有差异, 跑 `python3 scripts/rebuild_manifest.py` 同步")
        return 1

    # 写
    if dry_run:
        print(f"🔍 dry-run: 将写 {new['total']} 篇 → {MANIFEST}")
        print(f"   styles: {new['styles_used']}")
        return 0

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    # 保留 2 空格缩进, 跟旧 manifest byte-compatible
    MANIFEST.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已写 {MANIFEST}: {new['total']} 篇, styles={len(new['styles_used'])}")

    # 顺手 sync audit registry 的 totals.majors 计数
    reg_script = ROOT / "scripts" / "update_audit_registry.py"
    if reg_script.exists():
        import subprocess
        try:
            r = subprocess.run(
                ["python3", str(reg_script), "--stats"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                print(f"\n📊 registry 状态:")
                for line in r.stdout.strip().splitlines()[:8]:
                    print(f"   {line}")
        except Exception as e:
            print(f"⚠️  registry stats 失败: {e}")
    return 0


def cmd_add_slug(slug: str):
    """单篇补登记: 适用于 commit 后忘了跑 rebuild 的紧急情况"""
    f = CURATED / f"{slug}.json"
    if not f.exists():
        print(f"❌ {slug}: {f} 不存在")
        return 1
    if not MANIFEST.exists():
        print(f"❌ {MANIFEST} 不存在, 先跑 rebuild_manifest.py")
        return 1
    data = json.loads(f.read_text(encoding="utf-8"))
    data["slug"] = slug
    old = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # 替换或追加
    new_entry = build_entry(slug, data)
    replaced = False
    for i, m in enumerate(old["majors"]):
        if m["slug"] == slug:
            old["majors"][i] = new_entry
            replaced = True
            break
    if not replaced:
        old["majors"].append(new_entry)
    old["total"] = len(old["majors"])
    old["count"] = len(old["majors"])
    old["styles_used"] = sorted({m["style"] for m in old["majors"] if m.get("style")})
    old["updated_at"] = datetime.datetime.now().isoformat()
    MANIFEST.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ {'替换' if replaced else '新增'}: {slug} → {MANIFEST} (共 {old['total']} 篇)")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="重建 public/data/manifest.json (从 curated/*.json)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--dry-run", action="store_true", help="只看不写")
    ap.add_argument("--check", action="store_true", help="对比当前 manifest, exit code 报告差异")
    ap.add_argument("--add-slug", help="单篇补登记 (紧急用, 写完跑完整 rebuild)")
    args = ap.parse_args()

    if args.add_slug:
        sys.exit(cmd_add_slug(args.add_slug))
    sys.exit(cmd_rebuild(args.dry_run, args.check))


if __name__ == "__main__":
    main()
