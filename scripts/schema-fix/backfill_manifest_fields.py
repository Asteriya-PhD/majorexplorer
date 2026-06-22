#!/usr/bin/env python3
"""
backfill_manifest_fields.py — 补全 curated/*.json 缺 discipline/sub_discipline/menjia_moe/menjia_name/theme_color

历史欠账 (2026-06-18 发现):
  - 206/307 缺 discipline
  - 152/307 缺 sub_discipline
  - 303/307 缺 menjia_moe / menjia_name / theme_color

补全策略 (3 级 fallback):
  1. style → 主门类 (13 门类码): eng→08 / sci→07 / medicine→10 / ...
  2. title/category 关键词 → sub_discipline (学科类)
  3. discipline → theme_color (13 主题色板)

跟 pre-commit hook 配合:
  - pre-commit 跑 `backfill_manifest_fields.py --check` (有 null 就 warn)
  - 开发者跑 `backfill_manifest_fields.py --apply` 补全
  - 不直接 modify (让开发者 review diff 后再 commit)

用法:
  python3 scripts/backfill_manifest_fields.py --check         # 报告缺什么, 不改
  python3 scripts/backfill_manifest_fields.py --check --json  # JSON 报告
  python3 scripts/backfill_manifest_fields.py --apply         # 写回 JSON (5 字段)
  python3 scripts/backfill_manifest_fields.py --apply --only discipline theme_color  # 选择性补
"""
import argparse, json, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"

# 13 门类 (MOE 标准 + index.html:190-201 颜色)
# 顺序: code, name, primary color (CSS), accent (lighter), soft (lightest)
VALID_DISC_CODES = {"01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"}

def is_valid_disc(d):
    """校验 discipline 是否是合法 2 位门类码 (01-13)"""
    return isinstance(d, str) and d in VALID_DISC_CODES

MENJIA = {
    "01": {"name": "哲学", "primary": "#5A4632", "accent": "#8A7158", "soft": "#EFE9E0"},
    "02": {"name": "经济学", "primary": "#5A4632", "accent": "#8A7158", "soft": "#EFE9E0"},
    "03": {"name": "法学", "primary": "#3A3A3A", "accent": "#5C5C5C", "soft": "#E8E6E1"},
    "04": {"name": "教育学", "primary": "#5C7C4A", "accent": "#7E9C6D", "soft": "#E8F1E2"},
    "05": {"name": "文学", "primary": "#6B4F35", "accent": "#8B6F55", "soft": "#EFE5D8"},
    "06": {"name": "历史学", "primary": "#6B4F35", "accent": "#8B6F55", "soft": "#EFE5D8"},
    "07": {"name": "理学", "primary": "#1E5E72", "accent": "#4A8FA3", "soft": "#E1EEF2"},
    "08": {"name": "工学", "primary": "#5B5B47", "accent": "#7E7E68", "soft": "#EBEAE0"},
    "09": {"name": "农学", "primary": "#6B7A3F", "accent": "#8B9A5F", "soft": "#EAEEDC"},
    "10": {"name": "医学", "primary": "#8B2424", "accent": "#C45B5B", "soft": "#F5E6E6"},
    "11": {"name": "军事学", "primary": "#4A4564", "accent": "#6E6988", "soft": "#E6E4EC"},
    "12": {"name": "管理学", "primary": "#4A4564", "accent": "#6E6988", "soft": "#E6E4EC"},
    "13": {"name": "艺术学", "primary": "#8B3A62", "accent": "#B05C84", "soft": "#F2E0EA"},
}

# style → 主门类 (从 manifest 实际 277 篇观察, 13 style 全覆盖 13 门类的子集)
STYLE_TO_DISC = {
    "eng": "08",            # 工学
    "cs": "08",             # 计算机属工学
    "sci": "07",            # 理学
    "medicine": "10",       # 医学
    "law": "03",            # 法学
    "gongan": "03",         # 公安学属法学
    "finance": "02",        # 经济学
    "business": "12",       # 工商管理
    "administration": "12", # 公共管理
    "education": "04",      # 教育学
    "humanities": "05",     # 文学 (默认, 关键词可细化)
    "arts": "13",           # 艺术学
    "agri": "09",           # 农学
}

# sub_discipline 关键词匹配 (按优先级倒序, 先匹配覆盖后)
# 关键词 → (门类 code, 学科类名)
SUB_DISC_RULES = [
    # 01 哲学
    (r"哲学|伦理|逻辑|美学", "01", "哲学类"),
    # 02 经济学
    (r"经济|金融|财政|税收|统计.*经济|投资|保险|互联网金融|金融数学|金融科技|信用|贸易|电子商务|跨境电商|供应链|工商管理|会计|审计", "02", "经济与贸易类"),
    # 03 法学
    (r"法学|法律|司法|公安|警务|监狱|警察|纪检|监察|刑事|民法|商法|经济法|行政法|国际法|知识产权|卫生.*法|体育法|国际政治|政治学.*行政|外交|纪检监察", "03", "法学与公安学类"),
    # 04 教育学
    (r"教育|师范|小学|学前|人文教育|科学教育|艺术教育|体育教育|特殊教育|汉语国际", "04", "教育学类"),
    # 06 历史学
    (r"历史|考古|文物|博物馆|古文字|世界史|民族学", "06", "历史学类"),
    # 05 文学 (注意: 放 06 后, 因为 keywords 重叠)
    (r"语言|文学|汉语言|外国|英语|日语|法语|德语|俄语|阿拉伯|西班牙|葡萄牙|韩语|商务英语|商务日语|翻译|新闻|传播|广告|网络.*新媒体|广播电视|播音|主持|编辑|出版|数字出版|国际新闻|汉语国际|网络与新媒体|国际商务|影视技术|戏剧|电影|舞蹈|音乐|美术|绘画|雕塑|设计|动画|视觉传达|环境设计|产品设计|数字媒体|艺术|文物保护|文化遗产", "05", "文学与新闻传播类"),
    # 10 医学 (高优先级, 关键词明确)
    (r"临床医学|口腔医学|预防医学|中医学|中药学|针灸|推拿|中医康复|康复治疗|康复医学|护理|药学|医学检验|医学影像|麻醉|精神医学|儿科学|妇产|基础医学|法医学|放射医学|营养|眼视光|核医学|助产|听力.*言语康复|智能医学|药事管理|运动康复|中医养生|医学技术|医学信息|运动人体科学|临床工程|中医临床", "10", "医学类"),
    # 09 农学
    (r"农学|园艺|林学|草学|动物|兽医|水产|茶学|海洋渔业|植物保护|园林|农业经济|农村发展|农业智能|土地科学|农业工程|农业资源", "09", "农学类"),
    # 08 工学 (大量)
    (r"工程|计算机|软件|网络|网络工程|网络空间|信息.*工程|电子|电气|通信|光电|材料|机械|能源|动力|建筑|土木|水利|测绘|化工|制药|制药工程|食品|纺织|航空|船舶|兵器|矿业|冶金|汽车|机器人|智能制造|智能.*装备|区块链|密码|数据计算|量子|数字孪生|虚拟现实|遥感|储能|新能源|柔性电子|工业智能|脑机|仿生|智能建造|智能交通|智慧|海洋工程|海洋技术|勘查|地质.*工程|水文|地球信息|环境.*工程|生态.*工程|食品.*工程|测控|机械设计|核医学|核工程|核物理|应用化学|应用物理|应用统计|统计|物理学|化学|生物科学|生物技术|生物信息|生物医学|数学|天文|大气|海洋|地理|地质|生态|心理学|统计学|核物理|海洋科学|地球系统|全球气候|生态学|神经科学|脑科学|信息与计算|网络安全|物联网|人工智能|智能科学|智能感知|智能采矿|智能车辆|金融工程|信息管理|工业设计|环境设计|产品设计|视觉传达|数字媒体|动画|医学信息|医学工程|医学物理|工程力学|工程管理|物流管理|电子商务|工商管理|人力资源|市场营销|公共关系|健康服务|房地产|体育经济|旅游管理|工程管理|物业管理|行政管理|公共事业|公共管理|公共政策|社会工作|劳动关系|劳动与社会保障|海关|税务|审计|会计|财务管理|资产评估|国际商务|国际文化|国际事务|国际关系|外交|国际政治|国际新闻|国际传播|国际商务|国际经济|国际贸易|国际商务|海事|海商|海运|航运|物流|采购|供应链|信用管理|金融数学|金融科技|金融工程|投资学|金融学|保险学|风险|精算|经济犯罪|经济侦查|网络安全|网络空间|信息安全|数据科学|大数据|计算|虚拟现实|数字孪生|区块链|密码|网络空间|网络工程|物联网|传感器|智能感知|智能控制|工业智能|柔性电子|新型材料|纳米|复合材料|智能材料|能源化学|储能|能源.*工程|核能|核技术|核工程|核燃料|辐射防护|核反应|环境.*科学|环境.*工程|生态.*工程|环境.*生态|能源管理|能源经济|能源.*工程|能源.*动力|电气.*工程|电气.*自动化|机械.*工程|机械.*设计|机械.*制造|机械.*电子|工业.*工程|工业.*设计|工艺|技术|测控|仪器|光电|光信息|光学|光学工程|光源|照明|显示|集成电路|微电子|电子.*科学|电子.*技术|电子.*信息|电子.*工程|通信.*工程|信息.*工程|信息.*技术|计算机.*科学|计算机.*技术|计算机.*工程|软件.*工程|网络.*工程|空间.*信息|数字.*媒体|智能.*科学|智能.*技术|智能.*工程|智能.*系统|智能.*交通|智能.*车辆|智能.*建筑|智能.*海洋|智能.*制造|智能.*采矿|智能.*控制|智能.*感知|智能.*信息|智能.*医学|智能.*医疗|智能.*材料|智能.*装备|智能.*生产|智能.*工厂|智能.*电网|智能.*能源|智能.*物流|智能.*建造|智能.*城市|智能.*环境|智能.*生态|智能.*海洋|智能.*采矿|智能.*控制|智能.*感知|智能.*信息|智能.*医学|智能.*医疗", "08", "工学类"),
    # 12 管理学 (放最后, 关键词不明确)
    (r"管理|行政|工商|公共|人力资源|物流|旅游|电子商务|供应链|信用|工程管理|健康服务|房地产|体育经济|海关|税务|审计|会计|财务管理|资产评估|物业管理|公共事业|公共政策|社会工作|劳动关系|劳动与社会保障|行政管理|公共管理|信息管理|电子商务|工商管理|市场营销|公共关系|健康服务管理|体育经济与管理|国际商务|国际文化|国际事务|国际关系|外交|国际政治|国际新闻|国际传播", "12", "管理学与公共管理类"),
    # 13 艺术学
    (r"艺术|美术|音乐|舞蹈|戏剧|电影|广播电视|播音|主持|动画|视觉传达|环境设计|产品设计|数字媒体|艺术史|艺术管理|艺术教育|艺术学|艺术理论|文物保护|文化遗产|影视技术|戏剧.*表演|戏剧.*影视|电影.*电视|广播电视|播音.*主持|数字出版|艺术设计|视觉艺术|表演|音乐表演|舞蹈编导|戏剧文学|戏剧影视文学|美术学|绘画|雕塑|书法|中国画|艺术教育|艺术史论|艺术管理|公共艺术|实验艺术|跨媒体艺术|艺术与科技|艺术与设计|环境设计|产品设计|视觉传达设计|数字媒体艺术|艺术与科技|艺术设计|新媒体艺术|影视摄影与制作|广播电视编导|播音与主持艺术|戏剧影视导演|戏剧影视文学|音乐学|作曲与作曲技术理论|音乐表演|舞蹈表演|舞蹈编导|美术学|绘画|雕塑|摄影|中国画|书法学|实验艺术|跨媒体艺术|艺术史论|艺术管理|公共艺术|工艺美术|艺术设计|视觉传达设计|环境设计|产品设计|服装与服饰设计|公共艺术|动画|影视动画|数字媒体艺术|艺术与科技|艺术设计|新媒体艺术|音乐学|作曲|音乐表演|舞蹈表演|舞蹈编导|戏剧学|戏剧影视文学|表演|戏剧影视导演|戏剧影视美术设计|广播电视编导|播音与主持艺术|录音艺术|影视摄影与制作|影视技术|照明艺术|影视制片管理|电影学|戏剧学|广播电视学", "13", "艺术学类"),
]


def lookup_sub_discipline(title: str, category: str):
    """根据 title + category 关键词返回 (code, sub_name), 找不到返回 None"""
    text = (title or "") + " " + (category or "")
    # 优先 10 医学, 03 法学, 04 教育 (关键词明确)
    for pattern, code, sub in SUB_DISC_RULES:
        if re.search(pattern, text):
            return code, sub
    return None


def build_theme_color(disc_code: str, style: str):
    """根据 discipline code + style 构造 theme_color dict"""
    base = MENJIA.get(disc_code, MENJIA["08"])
    primary = base["primary"]
    accent = base["accent"]
    soft = base["soft"]
    # sci 风格统一用 sci-eng (跟 env-science polish agent 一致)
    if style == "sci":
        return {"primary": primary, "accent": accent, "soft": soft, "style_hint": "sci-eng"}
    return {"primary": primary, "accent": accent, "soft": soft}


def needs_fill(data: dict):
    """返回 5 个字段哪些需要补 (含非法值)"""
    return {
        "discipline": not is_valid_disc(data.get("discipline")),
        "sub_discipline": not data.get("sub_discipline"),
        "menjia_moe": not is_valid_disc(data.get("menjia_moe")),
        "menjia_name": not data.get("menjia_name"),
        "theme_color": not data.get("theme_color"),
    }


def backfill_one(data: dict):
    """补全单个 major 的 5 字段, 返回 (changed_fields, suggestions)"""
    title = data.get("title", "")
    category = data.get("category", "")
    style = data.get("style", "")
    changes = {}

    # 1. discipline (主门类): style 映射 (或关键词 fallback)
    if not is_valid_disc(data.get("discipline")):
        # 1a. 先用 style
        disc = STYLE_TO_DISC.get(style)
        # 1b. style 找不到用关键词
        if not disc:
            kw = lookup_sub_discipline(title, category)
            if kw:
                disc = kw[0]
        if disc:
            changes["discipline"] = disc
            data["discipline"] = disc

    # 2. sub_discipline (学科类): title/category 关键词
    if not data.get("sub_discipline"):
        result = lookup_sub_discipline(title, category)
        if result:
            disc_code, sub_name = result
            changes["sub_discipline"] = sub_name
            data["sub_discipline"] = sub_name

    # 3. menjia_moe (跟 discipline 同步, 必须是 2 位码)
    if not is_valid_disc(data.get("menjia_moe")) and is_valid_disc(data.get("discipline")):
        changes["menjia_moe"] = data["discipline"]
        data["menjia_moe"] = data["discipline"]

    # 4. menjia_name
    if not data.get("menjia_name") and is_valid_disc(data.get("discipline")):
        name = MENJIA.get(data["discipline"], {}).get("name")
        if name:
            changes["menjia_name"] = name
            data["menjia_name"] = name

    # 5. theme_color
    if not data.get("theme_color") and is_valid_disc(data.get("discipline")):
        tc = build_theme_color(data["discipline"], style)
        changes["theme_color"] = tc
        data["theme_color"] = tc

    return changes


def collect_majors():
    """扫 curated/*.json → [(slug, path, data), ...]"""
    out = []
    for f in sorted(CURATED.glob("*.json")):
        slug = f.stem
        if slug in ("TEMPLATE", "template", "README", "_index", "manifest", "_manifest"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  {slug}: parse fail {e}", file=sys.stderr)
            continue
        if not data.get("title"):
            continue
        out.append((slug, f, data))
    return out


def cmd_check(json_out=False):
    """只报告缺什么, 不改"""
    majors = collect_majors()
    field_stats = {f: 0 for f in ["discipline", "sub_discipline", "menjia_moe", "menjia_name", "theme_color"]}
    needs = []
    for slug, f, data in majors:
        nf = needs_fill(data)
        for k, v in nf.items():
            if v:
                field_stats[k] += 1
        if any(nf.values()):
            needs.append({"slug": slug, "title": data.get("title", ""), "needs": nf})
    if json_out:
        print(json.dumps({"total": len(majors), "needs_count": len(needs), "field_stats": field_stats, "needs": needs}, ensure_ascii=False, indent=2))
    else:
        print(f"=== backfill 缺口检查 ({len(majors)} 篇) ===")
        for k, v in field_stats.items():
            print(f"  缺 {k:18s}: {v:3d} 篇")
        if needs:
            print(f"\n共 {len(needs)} 篇需要补全:")
            for n in needs[:10]:
                fields = ",".join(k for k, v in n["needs"].items() if v)
                print(f"  - {n['slug']:42s} {n['title']:12s} 缺 [{fields}]")
            if len(needs) > 10:
                print(f"  ... 还有 {len(needs)-10} 篇")
            print(f"\n跑 `python3 scripts/backfill_manifest_fields.py --apply` 补全")
        else:
            print("\n✅ 全部 5 字段已填, 无需补全")
    return 0 if not needs else 1


def cmd_apply(only=None):
    """写回 JSON"""
    majors = collect_majors()
    target_fields = only or ["discipline", "sub_discipline", "menjia_moe", "menjia_name", "theme_color"]
    changed_count = 0
    for slug, path, data in majors:
        before = {k: data.get(k) for k in target_fields}
        # 临时清空 (only 模式只补指定字段, 其它跳过)
        original = {k: data.get(k) for k in target_fields}
        for k in target_fields:
            data[k] = original[k]  # 保持原状
        # 跑 backfill
        backfill_one(data)
        # 检查变更
        changed = False
        for k in target_fields:
            if data.get(k) != before[k]:
                changed = True
                break
        if changed:
            changed_count += 1
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            filled = [k for k in target_fields if data.get(k) and not before[k]]
            print(f"  ✅ {slug:42s} {data.get('title', ''):12s} 补: {','.join(filled)}")
    print(f"\n📊 共改 {changed_count}/{len(majors)} 个文件")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="补全 curated/*.json 缺的 5 字段 (discipline/sub_discipline/menjia_moe/menjia_name/theme_color)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--check", action="store_true", help="只报告缺什么, 不改")
    ap.add_argument("--apply", action="store_true", help="写回 JSON")
    ap.add_argument("--json", action="store_true", help="--check 时用 JSON 输出")
    ap.add_argument("--only", nargs="*", help="--apply 时只补指定字段 (e.g. discipline theme_color)")
    args = ap.parse_args()
    if args.check:
        sys.exit(cmd_check(args.json))
    elif args.apply:
        sys.exit(cmd_apply(args.only))
    else:
        # 默认 --check
        sys.exit(cmd_check(False))


if __name__ == "__main__":
    main()
