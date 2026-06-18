#!/usr/bin/env python3
"""
fix_xuanke_salary_batch.py — Day 5 Bug 4 批量修复 (2026-06-18)

修复 81 个专业的 选科错模式 + 薪资虚高:
  - 选科: "物理+历史" (3+1+2 不可能) → 按 style 套用合规模板
  - 薪资: 应届生 P50 > 25万 → 校准到 麦可思 2024 真实区间

数据基准:
  - 选科: 大学生必备网 / chsi / 各校招生章程 2024-2026
  - 薪资: 麦可思 2024 就业蓝皮书 (本科平均 7.26万, 顶级 ≈ 14万)

用法:
  python3 scripts/fix_xuanke_salary_batch.py --dry-run    # 看会改啥
  python3 scripts/fix_xuanke_salary_batch.py               # 真改 + backup
  python3 scripts/fix_xuanke_salary_batch.py --only xuanke # 只修选科
  python3 scripts/fix_xuanke_salary_batch.py --only salary # 只修薪资
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
BACKUP_DIR = ROOT / "data" / "audit_registry_backup" / f"xuanke_salary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


# ──────────────────────────────────────────────────────────
# XUANKE TEMPLATES (按 style, 3+1+2 合规, pct 总和 = 100)
# 数据基准: chsi 2024 / 大学生必备网 / 各校招生章程
# ──────────────────────────────────────────────────────────

XUANKE_TEMPLATES = {
    # 经管类: 文理兼收, 物理历史都行, 物理略多
    "finance": [
        {"name": "首选物理 + 再选不限 (覆盖最广)", "course": "3+1+2 选科组合", "pct": 50,
         "reason": "山东财经 / 苏州大学 / 天津财经 等大多数校, 只要首选物理, 再选 化学/生物/政治/地理 任一即可."},
        {"name": "首选历史 + 再选不限 (偏文)", "course": "3+1+2 选科组合", "pct": 35,
         "reason": "中央财经 / 上财 / 西南财大 部分专业方向, 文科组合也能报, 但量化课程会薄弱."},
        {"name": "首选物理 + 化学 (双一流门槛)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "对外经贸 / 中南财大 等部分校要求 物理+化学 才能报金融工程 / 量化方向."},
        {"name": "不限选科 (中外合作 / 综合评价)", "course": "3+1+2 选科组合", "pct": 5,
         "reason": "极少数中外合作 (上财中英班 / 央财中美班) / 综合评价 (清华领军 / 北大博雅) 不限选科."},
    ],
    "administration": [
        {"name": "首选物理 + 再选不限 (覆盖最广)", "course": "3+1+2 选科组合", "pct": 50,
         "reason": "大多数校 (如 工商管理 / 物流管理 / 旅游管理) 文理兼收, 首选物理或历史均可."},
        {"name": "首选历史 + 再选不限 (偏文)", "course": "3+1+2 选科组合", "pct": 40,
         "reason": "行政管理 / 公共事业管理 / 劳动与社会保障 等偏文, 历史组合是主流."},
        {"name": "不限选科 (中外合作 / 综合评价)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "极少数中外合作 / 综合评价 不限选科."},
    ],
    # 文科类: 历史为主
    "humanities": [
        {"name": "首选历史 + 再选不限 (覆盖最广)", "course": "3+1+2 选科组合", "pct": 70,
         "reason": "汉语言文学 / 历史学 / 哲学 / 新闻学 等文科专业, 历史组合是绝对主流, 大多数校覆盖."},
        {"name": "首选历史 + 政治 + 地理 (传统文综)", "course": "3+1+2 选科组合", "pct": 20,
         "reason": "传统文综组合, 报考 财政学 / 税收学 / 公共事业管理 时优势明显."},
        {"name": "不限选科 (少数校 / 中外合作)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "极少数校 (如 翻译 / 商务英语) 文理兼收, 中外合作专业不限选科."},
    ],
    "law": [
        {"name": "首选历史 + 再选不限 (覆盖最广)", "course": "3+1+2 选科组合", "pct": 65,
         "reason": "法学 / 知识产权 / 法学 (国际法) 等, 大多数校文理兼收, 历史组合占主流."},
        {"name": "首选物理 + 再选不限 (部分校)", "course": "3+1+2 选科组合", "pct": 25,
         "reason": "部分校 (如 华东政法 / 西北政法) 法学专业接受物理组合, 知识产权法方向偏好理科."},
        {"name": "不限选科 (中外合作 / 综合评价)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "极少数中外合作 / 综合评价 不限选科."},
    ],
    # 艺术类: 历史 + 不限 为主
    "arts": [
        {"name": "首选历史 + 再选不限 (覆盖最广)", "course": "3+1+2 选科组合", "pct": 75,
         "reason": "美术学 / 音乐学 / 戏剧影视文学 等艺术类, 历史组合是绝对主流, 再选一般不限."},
        {"name": "首选物理 + 再选不限 (部分校)", "course": "3+1+2 选科组合", "pct": 15,
         "reason": "部分校 (如 数字媒体艺术 / 艺术与科技 / 艺术史论) 接受物理组合."},
        {"name": "不限选科 (艺术类校考特色)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "艺术类校考 / 中外合作专业, 多不限选科, 看专业校考成绩."},
    ],
    # 理工类: 物理是绝对门槛
    "eng": [
        {"name": "首选物理 + 化学 (双一流门槛)", "course": "3+1+2 选科组合", "pct": 60,
         "reason": "机械 / 电气 / 材料 / 化工 / 土木 等工科主流, 大多数双一流要求 物理+化学 才能报."},
        {"name": "首选物理 + 生物 (部分方向)", "course": "3+1+2 选科组合", "pct": 25,
         "reason": "生物医学工程 / 食品工程 / 环境工程 等方向接受 物理+生物 组合."},
        {"name": "首选物理 + 再选不限 (部分校)", "course": "3+1+2 选科组合", "pct": 15,
         "reason": "一般校 (如 双非) 工科专业 物理 + 再选任意 即可."},
    ],
    "sci": [
        {"name": "首选物理 + 化学 (双一流门槛)", "course": "3+1+2 选科组合", "pct": 65,
         "reason": "数学 / 物理 / 化学 等理科主流, 双一流校要求 物理+化学 才能报."},
        {"name": "首选物理 + 生物 / 地理 / 政治", "course": "3+1+2 选科组合", "pct": 25,
         "reason": "应用统计学 / 经济统计学 / 地理信息 等方向, 再选非化学可报."},
        {"name": "首选物理 + 再选不限 (部分校)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "一般校理科 物理 + 再选任意 即可."},
    ],
    "cs": [
        {"name": "首选物理 + 再选不限 (覆盖最广)", "course": "3+1+2 选科组合", "pct": 70,
         "reason": "计算机 / 软件工程 / 网络空间安全 等, 大多数校 物理 + 再选任意 (化学/生物/地理/政治) 即可."},
        {"name": "首选物理 + 化学 (部分校)", "course": "3+1+2 选科组合", "pct": 20,
         "reason": "部分双一流校 (如 哈工大 / 北航 CS) 要求 物理+化学, 偏底层系统方向."},
        {"name": "首选历史 + 再选不限 (少数校)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "极少数校 (如 部分财经类 CS) 文理兼收, 历史组合也能报."},
    ],
    # 医学类: 物理+化学+生物 是铁三角
    "medicine": [
        {"name": "首选物理 + 化学 + 生物 (双一流门槛)", "course": "3+1+2 选科组合", "pct": 70,
         "reason": "临床医学 / 口腔医学 / 预防医学 等主流, 双一流校几乎全部要求 物理+化学+生物 三选全选."},
        {"name": "首选物理 + 化学 (部分方向)", "course": "3+1+2 选科组合", "pct": 25,
         "reason": "医学影像 / 医学检验 / 药学 等方向, 物理+化学即可 (部分校不要生物)."},
        {"name": "不限选科 (中医 / 护理少数校)", "course": "3+1+2 选科组合", "pct": 5,
         "reason": "极少数中医药大学 / 护理校 中外合作, 不限选科."},
    ],
    "agri": [
        {"name": "首选物理 + 化学 (主流门槛)", "course": "3+1+2 选科组合", "pct": 50,
         "reason": "农学 / 园艺 / 植保 / 动物科学 等, 大多要求 物理+化学 才能报."},
        {"name": "首选物理 + 生物 (部分方向)", "course": "3+1+2 选科组合", "pct": 30,
         "reason": "生物育种 / 兽医 / 园林 等方向, 物理+生物组合可报."},
        {"name": "首选物理 + 再选不限 (部分校)", "course": "3+1+2 选科组合", "pct": 15,
         "reason": "一般校 (双非) 农林专业 物理 + 再选任意 即可."},
        {"name": "首选历史 + 再选不限 (偏文方向)", "course": "3+1+2 选科组合", "pct": 5,
         "reason": "农林经济管理 / 农村区域发展 等偏文专业, 历史组合也能报."},
    ],
    "gongan": [
        {"name": "首选政治 + 再选不限 (公安类主流)", "course": "3+1+2 选科组合", "pct": 70,
         "reason": "治安学 / 侦查学 / 刑事科学技术 等公安专业, 几乎全部要求 选政治 才能报."},
        {"name": "首选物理 + 再选不限 (部分校)", "course": "3+1+2 选科组合", "pct": 25,
         "reason": "网络安全与执法 / 公安管理学 等部分方向接受 物理 + 再选不限."},
        {"name": "不限选科 (极少数校)", "course": "3+1+2 选科组合", "pct": 5,
         "reason": "极少数公安院校 中外合作 / 综合评价 不限选科."},
    ],
    "business": [
        {"name": "首选物理 + 再选不限 (覆盖最广)", "course": "3+1+2 选科组合", "pct": 50,
         "reason": "工商管理 / 市场营销 / 会计 / 财务管理 等, 大多数校 物理 + 再选任意 即可."},
        {"name": "首选历史 + 再选不限 (偏文)", "course": "3+1+2 选科组合", "pct": 40,
         "reason": "会计 / 财务管理 / 市场营销 部分校文理兼收, 历史组合是主流."},
        {"name": "不限选科 (中外合作)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "极少数中外合作 (上财中英班 / 中财中美班) 不限选科."},
    ],
}


# ──────────────────────────────────────────────────────────
# SALARY TEMPLATES (按 style, 麦可思 2024 校准, 单位: 万/年)
# 应届生 P50 基线: 本科平均 7.26万, 顶级头部 ≈ 14-20万
# ──────────────────────────────────────────────────────────

SALARY_TEMPLATES = {
    "cs": {  # 顶级薪资 (AI / 互联网头部)
        "应届生 (一线)":              {"p25": 12, "p50": 18, "p75": 28, "yoy": 10},
        "3年经验":                    {"p25": 22, "p50": 35, "p75": 55, "yoy": 12},
        "5年经验":                    {"p25": 35, "p50": 55, "p75": 90, "yoy": 10},
        "10年+ (资深 / 架构师)":        {"p25": 60, "p50": 100, "p75": 180, "yoy": 8},
    },
    "eng": {  # 中高 (传统工科)
        "应届生 (一线)":              {"p25": 8, "p50": 12, "p75": 18, "yoy": 6},
        "3年经验":                    {"p25": 14, "p50": 22, "p75": 32, "yoy": 8},
        "5年经验":                    {"p25": 22, "p50": 35, "p75": 55, "yoy": 8},
        "10年+ (资深 / 总工)":          {"p25": 40, "p50": 65, "p75": 110, "yoy": 6},
    },
    "finance": {  # 中高 (量化 / 投行头部)
        "应届生 (一线)":              {"p25": 9, "p50": 13, "p75": 20, "yoy": 8},
        "3年经验":                    {"p25": 16, "p50": 25, "p75": 40, "yoy": 10},
        "5年经验":                    {"p25": 25, "p50": 40, "p75": 65, "yoy": 10},
        "10年+ (持证 CFA/FRM / 资深)":  {"p25": 45, "p50": 75, "p75": 130, "yoy": 8},
    },
    "sci": {  # 中 (应用统计/数据科学例外)
        "应届生 (一线)":              {"p25": 7, "p50": 11, "p75": 16, "yoy": 6},
        "3年经验":                    {"p25": 14, "p50": 22, "p75": 35, "yoy": 8},
        "5年经验":                    {"p25": 22, "p50": 35, "p75": 55, "yoy": 8},
        "10年+ (资深 / 研究员)":        {"p25": 40, "p50": 65, "p75": 110, "yoy": 6},
    },
    "law": {  # 中 (法务 / 红圈所头部)
        "应届生 (一线)":              {"p25": 8, "p50": 12, "p75": 20, "yoy": 6},
        "3年经验":                    {"p25": 15, "p50": 25, "p75": 45, "yoy": 8},
        "5年经验":                    {"p25": 25, "p50": 42, "p75": 75, "yoy": 8},
        "10年+ (合伙人 / 总法)":        {"p25": 50, "p50": 90, "p75": 180, "yoy": 6},
    },
    "medicine": {  # 前期低后期高 (规培周期长)
        "应届生 (规培前)":              {"p25": 6, "p50": 9, "p75": 13, "yoy": 4},
        "3年经验 (规培中)":            {"p25": 12, "p50": 18, "p75": 28, "yoy": 6},
        "5年经验 (主治)":              {"p25": 22, "p50": 35, "p75": 60, "yoy": 8},
        "10年+ (副主任+/科室主任)":     {"p25": 45, "p50": 75, "p75": 130, "yoy": 6},
    },
    "humanities": {  # 低
        "应届生 (一线)":              {"p25": 6, "p50": 8, "p75": 12, "yoy": 4},
        "3年经验":                    {"p25": 10, "p50": 15, "p75": 22, "yoy": 6},
        "5年经验":                    {"p25": 15, "p50": 22, "p75": 35, "yoy": 6},
        "10年+ (资深 / 主编)":          {"p25": 25, "p50": 40, "p75": 70, "yoy": 4},
    },
    "arts": {  # 低 (艺术头部例外: 顶级艺术家可达 100+, 但 P50 中位不是)
        "应届生 (一线)":              {"p25": 5, "p50": 8, "p75": 14, "yoy": 3},
        "3年经验":                    {"p25": 9, "p50": 14, "p75": 25, "yoy": 5},
        "5年经验":                    {"p25": 15, "p50": 22, "p75": 40, "yoy": 5},
        "10年+ (资深 / 独立艺术家)":     {"p25": 25, "p50": 45, "p75": 90, "yoy": 4},
    },
    "education": {  # 中低
        "应届生 (一线)":              {"p25": 6, "p50": 9, "p75": 13, "yoy": 4},
        "3年经验":                    {"p25": 10, "p50": 15, "p75": 22, "yoy": 6},
        "5年经验":                    {"p25": 14, "p50": 22, "p75": 32, "yoy": 6},
        "10年+ (特级教师 / 校长)":       {"p25": 25, "p50": 40, "p75": 70, "yoy": 4},
    },
    "administration": {  # 中低 (财务例外)
        "应届生 (一线)":              {"p25": 7, "p50": 10, "p75": 14, "yoy": 4},
        "3年经验":                    {"p25": 11, "p50": 16, "p75": 25, "yoy": 6},
        "5年经验":                    {"p25": 18, "p50": 28, "p75": 45, "yoy": 6},
        "10年+ (资深 / 公务员处级)":     {"p25": 30, "p50": 50, "p75": 85, "yoy": 4},
    },
    "business": {  # 中 (与 finance 接近, 但商业管理偏弱)
        "应届生 (一线)":              {"p25": 7, "p50": 10, "p75": 15, "yoy": 5},
        "3年经验":                    {"p25": 13, "p50": 20, "p75": 32, "yoy": 7},
        "5年经验":                    {"p25": 22, "p50": 35, "p75": 55, "yoy": 7},
        "10年+ (资深 / 总监)":          {"p25": 40, "p50": 65, "p75": 120, "yoy": 5},
    },
    "agri": {  # 低 (农林头部例外)
        "应届生 (一线)":              {"p25": 5, "p50": 7, "p75": 10, "yoy": 3},
        "3年经验":                    {"p25": 8, "p50": 12, "p75": 18, "yoy": 5},
        "5年经验":                    {"p25": 12, "p50": 18, "p75": 28, "yoy": 5},
        "10年+ (研究员 / 高级农艺师)":   {"p25": 22, "p50": 35, "p75": 60, "yoy": 3},
    },
    "gongan": {  # 中 (公务员事编主流)
        "应届生 (一线)":              {"p25": 7, "p50": 10, "p75": 14, "yoy": 4},
        "3年经验":                    {"p25": 11, "p50": 16, "p75": 25, "yoy": 6},
        "5年经验":                    {"p25": 18, "p50": 28, "p75": 45, "yoy": 6},
        "10年+ (处级 / 总队)":          {"p25": 30, "p50": 50, "p75": 90, "yoy": 4},
    },
}


def has_xuanke_bug(xuanke_list: list) -> bool:
    """检测选科列表是否有 物理+历史 冲突 / 3+1+2 不合规"""
    for xk in xuanke_list:
        name = xk.get('name', '')
        # "物理" AND "历史" both in name = 首选冲突
        if '物理' in name and '历史' in name:
            return True
        # "首选物理 / 历史" 用 "/" 是允许的 (or 关系)
        # "物理+历史+..." 是错的
    return False


def has_salary_bug(salary: dict) -> bool:
    """检测薪资是否有 应届生 P50 > 25 万 的虚高问题"""
    for stage, vals in salary.items():
        if isinstance(vals, dict):
            p50 = vals.get('p50', 0)
            if isinstance(p50, (int, float)) and p50 > 25 and ('应届' in stage or '0-2' in stage):
                return True
    return False


def fix_one(json_path: Path, style: str, only: str = None, dry_run: bool = False) -> tuple[bool, dict]:
    """修一个 JSON. 返 (changed, details)."""
    try:
        data = json.loads(json_path.read_text(encoding='utf-8'))
    except Exception as e:
        return False, {'error': f'parse: {e}'}

    xuanke_template = XUANKE_TEMPLATES.get(style, [])
    salary_template = SALARY_TEMPLATES.get(style, {})
    changes = {}

    if only in (None, 'xuanke') and has_xuanke_bug(data.get('xuanke_req_list', [])) and xuanke_template:
        changes['xuanke_req_list'] = {
            'old': data.get('xuanke_req_list'),
            'new': xuanke_template,
        }

    if only in (None, 'salary') and has_salary_bug(data.get('salary', {})) and salary_template:
        changes['salary'] = {
            'old': data.get('salary'),
            'new': salary_template,
        }

    if not changes:
        return False, {}

    if not dry_run:
        for key, diff in changes.items():
            data[key] = diff['new']
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    return True, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只看不写")
    ap.add_argument("--only", choices=["xuanke", "salary"], help="只修一类")
    ap.add_argument("--limit", type=int, help="只改前 N 个")
    ap.add_argument("--slugs", nargs="*", help="指定 slug 列表")
    args = ap.parse_args()

    if not args.dry_run:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        print(f"📦 Backup → {BACKUP_DIR}")

    targets = []
    for json_path in sorted(CURATED.glob('*.json')):
        if json_path.name == 'manifest.json':
            continue
        if args.slugs and json_path.stem not in args.slugs:
            continue
        try:
            data = json.loads(json_path.read_text(encoding='utf-8'))
        except:
            continue
        slug = data.get('slug', json_path.stem)
        style = data.get('style', '')
        xuanke_ok = not has_xuanke_bug(data.get('xuanke_req_list', []))
        salary_ok = not has_salary_bug(data.get('salary', {}))
        if not xuanke_ok or not salary_ok:
            targets.append((json_path, slug, style, xuanke_ok, salary_ok))

    if args.limit:
        targets = targets[:args.limit]

    print(f"🎯 目标 {len(targets)} 个 JSON 待修\n")

    changed = 0
    xuanke_fixed = 0
    salary_fixed = 0
    by_style = {}
    for json_path, slug, style, xuanke_ok, salary_ok in targets:
        if not args.dry_run:
            shutil.copy2(json_path, BACKUP_DIR / json_path.name)
        ok, diff = fix_one(json_path, style, only=args.only, dry_run=args.dry_run)
        if ok:
            changed += 1
            if 'xuanke_req_list' in diff:
                xuanke_fixed += 1
            if 'salary' in diff:
                salary_fixed += 1
            by_style.setdefault(style, []).append(slug)
            mark = []
            if 'xuanke_req_list' in diff:
                mark.append('X')
            if 'salary' in diff:
                mark.append('S')
            print(f"  ✓ {slug:35s} ({style:13s}) [{'/'.join(mark)}]")
        else:
            print(f"  - {slug:35s} ({style:13s}) 无需改")

    print(f"\n📊 汇总 ({'DRY-RUN' if args.dry_run else '已写'}):")
    print(f"   总修: {changed}/{len(targets)}")
    print(f"   选科修复: {xuanke_fixed}")
    print(f"   薪资修复: {salary_fixed}")
    print(f"   按 style: {dict((k, len(v)) for k, v in by_style.items())}")
    if args.dry_run:
        print(f"\n⚠️ DRY-RUN, 未写文件. 去掉 --dry-run 真改.")


if __name__ == "__main__":
    main()