#!/usr/bin/env python3
"""
build_hierarchy.py — 把 manifest 里的 130 个 hierarchy-only 专业自动注入回 hierarchy.

输入:
  - public/data/discipline_hierarchy.json  (旧版本, 524 个专业)
  - public/data/manifest.json              (新增/特设, 458 个精品)

输出:
  - public/data/discipline_hierarchy.json  (合并后, ~654 个专业)

策略:
  1. 解析 manifest 每篇的 menjia_moe + category 字段
  2. 从 category 提取 sub_class 名称 (正则)
  3. 模糊匹配 hierarchy 现有 sub_class; 找不到则按 menjia_moe 创建新 sub_class
  4. 注入专业名 (不重复)
  5. 写回 hierarchy.json

用法:
  python3 scripts/build_hierarchy.py [--dry-run]
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
HIER_PATH = ROOT / "public/data/discipline_hierarchy.json"
MFST_PATH = ROOT / "public/data/manifest.json"

# 各门类的"默认 sub_class"(兜底用): 当 category 字段无法解析时, 把专业塞到这个 sub
DEFAULT_SUB = {
    '01': '0101',  # 哲学 → 哲学类
    '02': '0201',  # 经济学 → 经济学类
    '03': '0301',  # 法学 → 法学类
    '04': '0401',  # 教育学 → 教育学类
    '05': '0501',  # 文学 → 中国语言文学类
    '06': '0601',  # 历史学 → 历史学类
    '07': '0710',  # 理学 → 生物科学类
    '08': '0801',  # 工学 → 力学类
    '09': '0901',  # 农学 → 植物生产类
    '10': '1001',  # 医学 → 基础医学类
    '11': '1101',  # 军事学
    '12': '1201',  # 管理学 → 管理科学与工程类
    '13': '1301',  # 艺术学 → 艺术学理论类
    '14': '1401',  # 交叉学科
}

# 模糊匹配 sub_class 名称的关键词映射 (category 文字 → sub_class name 关键词)
SUB_CLASS_HINTS = {
    '中国语言文学': '中国语言文学类',
    '外国语言文学': '外国语言文学类',
    '新闻传播': '新闻传播学类',
    '机械': '机械类',
    '航空航天': '航空航天类',
    '农业工程': '农业工程类',
    '教育学类': '教育学类',
    '体育': '体育学类',
    '交通运输': '交通运输类',
    '生物工程': '生物工程类',
    '土木工程': '土木类',
    '土木': '土木类',
    '公安技术': '公安技术类',
    '公安学': '公安学类',
    '法学类': '法学类',
    '金融学': '金融学类',
    '经济学类': '经济学类',
    '经济与贸易': '经济与贸易类',
    '财政学': '财政学类',
    '植物生产': '植物生产类',
    '动物生产': '动物生产类',
    '艺术学理论': '艺术学理论类',
    '戏剧与影视': '戏剧与影视学类',
    '美术学': '美术学类',
    '设计学': '设计学类',
    '工商管理': '工商管理类',
    '公共管理': '公共管理类',
    '管理科学与工程': '管理科学与工程类',
    '物流管理': '物流管理与工程类',
    '电子商务': '电子商务类',
    '心理学': '心理学类',
    '生物科学': '生物科学类',
    '统计学': '统计学类',
    '海洋科学': '海洋科学类',
    '大气科学': '大气科学类',
    '地理科学': '地理科学类',
    '地球物理': '地球物理学类',
    '地质学': '地质学类',
    '化学': '化学类',
    '物理学': '物理学类',
    '数学': '数学类',
    '天文学': '天文学类',
    '心理学': '心理学类',
    '临床医学': '临床医学类',
    '基础医学': '基础医学类',
    '医学技术': '医学技术类',
    '中医学': '中医学类',
    '中药学': '中药学类',
    '药学': '药学类',
    '公共卫生': '公共卫生与预防医学类',
    '草学': '草学类',
    '美学': '哲学类',  # 美学属哲学类
}


def parse_category(category: str, menjia_moe: str, hier: dict) -> str:
    """从 category 字段提取 sub_class 名称, 返回 sub_class code (如 '0201').

    如果解析失败, 返回 DEFAULT_SUB[menjia_moe].
    """
    if not category:
        return DEFAULT_SUB.get(menjia_moe)

    # 找该门类下所有 sub_class
    menjia = hier.get('门类', {}).get(menjia_moe, {})
    subs = menjia.get('sub_classes', {})
    sub_name_to_code = {sc['name']: code for code, sc in subs.items()}

    # 1) 直接全名匹配
    for sub_name, code in sub_name_to_code.items():
        if sub_name in category:
            return code

    # 2) 关键词 hint 匹配
    for hint, target_name in SUB_CLASS_HINTS.items():
        if hint in category:
            if target_name in sub_name_to_code:
                return sub_name_to_code[target_name]

    # 3) 兜底
    return DEFAULT_SUB.get(menjia_moe)


def main(dry_run: bool = False):
    hier = json.loads(HIER_PATH.read_text(encoding='utf-8'))
    mfst = json.loads(MFST_PATH.read_text(encoding='utf-8'))

    # 现有 hierarchy 中所有专业名
    hier_names = set()
    for code, d in hier.get('门类', {}).items():
        for sc_code, sc in d.get('sub_classes', {}).items():
            for mn in sc.get('majors', []):
                hier_names.add(mn)

    # manifest-only 专业 (130 个)
    to_inject = []
    for m in mfst.get('majors', []):
        title = m.get('title', '')
        if title and title not in hier_names:
            to_inject.append(m)
    print(f'[build_hierarchy] manifest-only 专业: {len(to_inject)} 个待注入')

    # 注入计划
    plan = defaultdict(lambda: defaultdict(list))  # menjia → sub_code → [titles]
    fail = []
    for m in to_inject:
        title = m.get('title', '')
        menjia = m.get('menjia_moe', '')
        category = m.get('category', '')
        if not menjia or menjia not in hier.get('门类', {}):
            fail.append(f'{title} (menjia_moe={menjia!r} 无效)')
            continue
        sub_code = parse_category(category, menjia, hier)
        if not sub_code:
            fail.append(f'{title} (无法定位 sub_class)')
            continue
        plan[menjia][sub_code].append(title)

    # 应用
    added = 0
    for menjia, sub_codes in plan.items():
        m = hier['门类'][menjia]
        subs = m.setdefault('sub_classes', {})
        for sub_code, titles in sub_codes.items():
            sc = subs.get(sub_code)
            if not sc:
                # sub_class 不存在 (e.g. DEFAULT_SUB 命中了一个不存在的代码), 创建
                sc = {'name': f'{sub_code} 新增类', 'majors': []}
                subs[sub_code] = sc
            existing = set(sc.get('majors', []))
            for t in titles:
                if t not in existing:
                    sc['majors'].append(t)
                    added += 1

    # 报告
    print(f'[build_hierarchy] 注入成功 {added} 个 (跨 {len(plan)} 门类)')
    if fail:
        print(f'[build_hierarchy] 失败 {len(fail)} 个:')
        for f in fail[:10]:
            print(f'  - {f}')

    # 打印每门类前后对比
    print('\n--- 门类 前→后 专业数 ---')
    for code in sorted(hier['门类'].keys()):
        m = hier['门类'][code]
        cnt = sum(len(sc.get('majors', [])) for sc in m.get('sub_classes', {}).values())
        added_in_this = sum(len(ts) for ts in plan.get(code, {}).values())
        sign = f' (+{added_in_this})' if added_in_this else ''
        print(f'  {code} {m.get("name","?"):8s} {cnt:>3d} 专业{sign}')

    # 总数
    total = sum(
        len(sc.get('majors', []))
        for m in hier['门类'].values()
        for sc in m.get('sub_classes', {}).values()
    )
    print(f'\nhierarchy 总专业数: {total}')

    if dry_run:
        print('\n[dry-run] 不写回. 加 --apply 真写.')
        return

    HIER_PATH.write_text(json.dumps(hier, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n✅ 已写回 {HIER_PATH}')


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv or '-n' in sys.argv
    main(dry_run=dry)
