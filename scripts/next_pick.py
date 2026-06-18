#!/usr/bin/env python3
"""
next_pick.py — 智能挑 N 篇未做 major 跨门类均匀分布

策略 (默认 gap-priority):
  - 按 13 门类覆盖率升序排
  - 优先挑覆盖率最低的
  - 跨门类均匀分布 (e.g. 30 篇 6 门类 ≈ 各 5 篇)
  - 排除 done + claimed
  - 同 subclass 内随机分散 (避免一个专业类全挑完)

用法:
  # 挑 30 篇 (默认 gap-priority 策略)
  python3 scripts/next_pick.py --n 30

  # 挑 30 篇, 输出 CSV 格式 (可直接给 agent)
  python3 scripts/next_pick.py --n 30 --csv

  # 挑 30 篇, 输出 JSON 格式
  python3 scripts/next_pick.py --n 30 --json

  # 强制单门类 (e.g. 全部 08 工学)
  python3 scripts/next_pick.py --n 30 --menjia 08

  # 自动 claim (claim.py 集成, 避免重复)
  python3 scripts/next_pick.py --n 30 --claim day6-A
"""
import argparse, json, sys, random
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data" / "major_directory.json"

# 13 门类 (顺序 = 优先级)
MENJIA_ORDER = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"]


def load_dir():
    if not DIRECTORY.exists():
        print("❌ 目录不存在, 跑 scripts/build_directory.py", file=sys.stderr)
        sys.exit(1)
    return json.load(open(DIRECTORY))


def get_missing(directory, filter_menjia=None):
    """收集所有 missing major, 可选按门类过滤"""
    out = []
    for mj_code, mj in directory["menjia"].items():
        if filter_menjia and mj_code != filter_menjia:
            continue
        for sub_code, sub in mj["subclass"].items():
            for m_code, m in sub["majors"].items():
                if m["status"] == "missing":
                    out.append({
                        "moe_code": m_code,
                        "name": m["name"],
                        "menjia_moe": mj_code,
                        "menjia_name": mj["name"],
                        "subclass_chsi": sub_code,
                        "subclass_name": sub["name"],
                    })
    return out


def pick_gap_priority(directory, n, seed=42):
    """按 13 门类覆盖率升序, 跨门类均匀分布"""
    missing = get_missing(directory)
    if not missing:
        print("❌ 无 missing major")
        return []
    # 按门类分组
    by_menjia = defaultdict(list)
    for m in missing:
        by_menjia[m["menjia_moe"]].append(m)
    # 门类排序 (按 done/pct 升序, 优先补低覆盖率)
    menjia_pct = sorted(directory["menjia_stats"].items(), key=lambda x: (x[1]["pct"], -x[1]["missing"]))
    # 策略: 优先挑覆盖率最低的 6-8 门类, 各 4-5 篇
    target_menjias = [m for m, s in menjia_pct if s["missing"] > 0][:max(6, n // 5)]
    n_per_menjia = max(1, n // len(target_menjias))
    random.seed(seed)
    picked = []
    for mj_code in target_menjias:
        available = by_menjia.get(mj_code, [])
        random.shuffle(available)
        # 同 subclass 分散 (前 N 各 subclass 选 1, 然后 round-robin)
        picked_in_mj = []
        sub_seen = defaultdict(int)
        for m in available:
            sub = m["subclass_chsi"]
            if sub_seen[sub] < 2:  # 每个 subclass 最多 2 个
                picked_in_mj.append(m)
                sub_seen[sub] += 1
            if len(picked_in_mj) >= n_per_menjia:
                break
        picked.extend(picked_in_mj[:n_per_menjia])
        if len(picked) >= n:
            break
    # 不够再补
    if len(picked) < n:
        remain = [m for m in missing if m not in picked]
        random.shuffle(remain)
        picked.extend(remain[:n - len(picked)])
    return picked[:n]


def main():
    ap = argparse.ArgumentParser(description="智能挑 N 篇未做 major", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--n", type=int, required=True, help="要挑的篇数")
    ap.add_argument("--menjia", help="强制单门类 (e.g. 08)")
    ap.add_argument("--strategy", default="gap-priority", help="策略 (默认 gap-priority)")
    ap.add_argument("--seed", type=int, default=42, help="随机种子 (默认 42)")
    ap.add_argument("--csv", action="store_true", help="输出 CSV 格式")
    ap.add_argument("--json", action="store_true", help="输出 JSON 格式")
    ap.add_argument("--claim", help="自动 claim 到指定 agent")
    args = ap.parse_args()

    directory = load_dir()
    if args.menjia:
        picked = get_missing(directory, args.menjia)[:args.n]
    else:
        picked = pick_gap_priority(directory, args.n, args.seed)

    if not picked:
        print("❌ 无可用 missing")
        return

    # 输出
    if args.csv:
        print("slug,title,style,code,subclass")
        for m in picked:
            # slug 还没, 用 moe_code 临时
            slug = m["moe_code"]  # 占位
            print(f'{slug},{m["name"]},{style_for(m["menjia_moe"])},{m["menjia_moe"]},{m["subclass_name"]}')
    elif args.json:
        print(json.dumps(picked, ensure_ascii=False, indent=2))
    else:
        # 默认人类可读
        print(f"=== 挑 {len(picked)} 篇 (策略: {args.strategy}) ===")
        from collections import Counter
        c = Counter(m["menjia_name"] for m in picked)
        print(f"门类分布: {dict(c)}")
        print()
        for i, m in enumerate(picked, 1):
            print(f"  {i:2d}. [{m['menjia_moe']} {m['menjia_name']}] {m['name']} ({m['subclass_name']})")

    # 自动 claim
    if args.claim:
        import subprocess
        slugs = [m["moe_code"] for m in picked]  # 用 moe_code 当 slug 占位
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim.py"), "--agent", args.claim, "--slugs", *slugs, "--task", f"new pick n={args.n}"],
            capture_output=True, text=True
        )
        print()
        print(f"🔒 claim {args.claim}:")
        print(r.stdout)
        if r.returncode != 0:
            print(f"⚠️  claim returncode {r.returncode}: {r.stderr}", file=sys.stderr)


def style_for(menjia_moe):
    """简单 menja → style 映射 (跟 backfill 一致)"""
    m = {
        "01": "humanities", "02": "finance", "03": "law", "04": "education",
        "05": "humanities", "06": "humanities", "07": "sci", "08": "eng",
        "09": "agri", "10": "medicine", "11": "gongan", "12": "administration", "13": "arts",
    }
    return m.get(menjia_moe, "eng")


if __name__ == "__main__":
    main()
