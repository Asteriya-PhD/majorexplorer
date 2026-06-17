#!/usr/bin/env python3
"""
check_major.py — Major 精品质量硬门禁 (Day 3 Team B 47 篇验证)

自动检查 commit 前 major JSON 是否满足 4 大 anti-pollution rules + 18 字段 schema.
挂 git pre-commit hook, 不通过则 commit 失败, 强制 agent 按 PIPELINE 流水线.

用法:
  python3 scripts/check_major.py <slug>           # 检查单个 major
  python3 scripts/check_major.py --all          # 检查 public/ 所有 major
  python3 scripts/check_major.py --staged       # 检查 git staged 但未 commit 的 JSON
"""
import json
import sys
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).parent.parent
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'

REQUIRED_FIELDS = [
    'title', 'slug', 'style', 'category', 'degree', 'duration_years',
    'tags', 'summary', 'hero_quote', 'curriculum', 'top_schools',
    'top_companies', 'salary', 'employment_direction', 'deep_study',
    'alumni_quotes', 'xuanke_req_list', 'overview_v2'
]

CURRICULUM_KEYS = [
    '公共必修 (所有院校都开)',
    '通用专业核心 (≈ 80% 院校覆盖)',
    '5 校特色选修 (按方向分流)'
]

# 公共必修允许的课程类型 (专业课必须放通用核心, 不能放公共必修)
PUBLIC_REQUIRED_ALLOWED = {
    '高数', '高等数学', '线代', '线性代数', '概率', '概率论', '数理统计',
    '物理', '大学物理', '化学', '生物', '英语', '思政', '马克思主义',
    '政治', '体育', '制图', 'CAD', '工程制图', '计算机基础'
}

# 真正的专业课 (绝不能放公共必修, 这些明显是专业核心而不是全校公共课)
FORBIDDEN_IN_PUBLIC = [
    '工程水文学', '卫生法学总论', '模拟集成电路', '机器人学基础',
    '电路原理', '数字集成电路', '播音发声学', '机器人学',
    '医学基础', '药理学概要', '卫生统计学', '文物鉴定',
    '卫生法学', '语料库语言学', '自然语言处理'
]

# anti-pollution 检查规则
POLLUTION_RULES = {
    'lede 模板套话': {
        'patterns': [
            '传统机械/材料的同学', 'AI 翻译/生成式写作时代',
            '问对问题', '4 年专业课是基础, 差异化靠选修',
            '传统机械/材料', '学 XX 的真正价值',
        ],
        'field': 'overview_v2.lede',
        'severity': 'CRITICAL',
        'msg': 'lede 不能是模板套话, 必须「主语+独特洞察+风险」三段式'
    },
    'who_fits_no 串台 (理工→人文本语)': {
        'patterns': ['文本阅读', '田野调研', '历史/语文', '写作训练'],
        'field': 'overview_v2.who_fits_no',
        'sci_field_check': True,  # 理工科 (eng/cs/sci/medicine) 才检查
        'severity': 'CRITICAL',
        'msg': '理工科 who_fits_no 不能出现人文本语词 (文本阅读/田野调研/历史/语文/写作训练)'
    },
    'who_fits_no 串台 (人文→理工经济)': {
        'patterns': ['数学/统计/经济', '持证上岗', '考证'],
        'field': 'overview_v2.who_fits_no',
        'humanities_field_check': True,  # 人文社科 (humanities/law/education/admin) 才检查
        'severity': 'CRITICAL',
        'msg': '人文社科 who_fits_no 不能出现理工经济词 (数学/统计/经济/考证)'
    },
    'deep_study CS/金融 12% 占位': {
        'patterns': ['跨学科就业 (CS/数据/金融)'],
        'field': 'deep_study',
        'severity': 'CRITICAL',
        'msg': '禁止用「跨学科就业 (CS/数据/金融)」占位, 改用专业真实主流去向'
    },
    'deep_study 路径占位「相关方向」': {
        'patterns': ['专业相关方向', '自主创业/其他', '国内博士 (学术研究)'],
        'field': 'deep_study',
        'severity': 'WARNING',
        'msg': 'deep_study 禁占位 (相关方向/学术研究/自主创业/其他), 必须用具体路径'
    },
    'employment_direction 字段空': {
        'patterns': [],
        'field': 'employment_direction',
        'min_count': 5,
        'severity': 'CRITICAL',
        'msg': 'employment_direction 必须 ≥5 个方向'
    },
    'top_schools 凑数 (空 tag)': {
        'patterns': [],
        'field': 'top_schools',
        'check_empty_tag': True,
        'severity': 'WARNING',
        'msg': 'top_schools 每所必须有非空 tag (含城市·特色)'
    },
    'salary string 占位 (未用 p25/p50/p75)': {
        'patterns': [],
        'field': 'salary',
        'check_string_value': True,
        'severity': 'WARNING',
        'msg': 'salary 各阶段必须用 {p25, p50, p75, yoy} 对象, 不能是 string'
    },
    'alumni_quotes < 2 条': {
        'patterns': [],
        'field': 'alumni_quotes',
        'min_count': 2,
        'severity': 'CRITICAL',
        'msg': 'alumni_quotes 必须 ≥2 条 (有 year/current/quote 字段, quote 含具体细节); 推荐 ≥3 条'
    },
}

SCI_STYLES = {'eng', 'cs', 'sci', 'medicine', 'agri'}
HUMANITIES_STYLES = {'humanities', 'law', 'education', 'administration', 'finance', 'business'}


def check_major(slug):
    """检查单个 major, 返回 (passed, errors, warnings)"""
    path = CURATED / f'{slug}.json'
    if not path.exists():
        return False, [f'文件不存在: {path}'], []

    try:
        d = json.loads(path.read_text())
    except Exception as e:
        return False, [f'JSON 解析失败: {e}'], []

    errors = []
    warnings = []

    # 1. 必填字段检查
    missing = [f for f in REQUIRED_FIELDS if f not in d]
    if missing:
        errors.append(f'必填字段缺失: {", ".join(missing)}')

    style = d.get('style', '')

    # 2. 4 大 anti-pollution + 其他规则检查
    for rule_name, rule in POLLUTION_RULES.items():
        field_path = rule['field']

        # 取字段值 (支持点路径)
        obj = d
        for part in field_path.split('.'):
            if isinstance(obj, dict):
                obj = obj.get(part, {})
            else:
                obj = {}
                break

        # sci/humanities 选择性检查
        if rule.get('sci_field_check') and style not in SCI_STYLES:
            continue
        if rule.get('humanities_field_check') and style not in HUMANITIES_STYLES:
            continue

        # 模式匹配
        text = json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj
        for pattern in rule['patterns']:
            if pattern in text:
                msg = f'[{rule["severity"]}] {rule_name}: 「{pattern}」 命中 → {rule["msg"]}'
                if rule['severity'] == 'CRITICAL':
                    errors.append(msg)
                else:
                    warnings.append(msg)
                break

        # 计数检查
        if 'min_count' in rule:
            if isinstance(obj, list) and len(obj) < rule['min_count']:
                msg = f'[CRITICAL] {rule_name}: 当前 {len(obj)} 条 < {rule["min_count"]} → {rule["msg"]}'
                errors.append(msg)

        # 空 tag 检查
        if rule.get('check_empty_tag'):
            if isinstance(obj, list):
                empty_tag = [s.get('name', '?') for s in obj if not s.get('tag', '').strip()]
                if empty_tag:
                    warnings.append(f'[WARNING] {rule_name}: {empty_tag} tag 为空 → {rule["msg"]}')

        # salary string 检查
        if rule.get('check_string_value') and isinstance(obj, dict):
            string_keys = [k for k, v in obj.items() if isinstance(v, str)]
            if string_keys:
                warnings.append(f'[WARNING] {rule_name}: {string_keys} 是 string → {rule["msg"]}')

    # 3. curriculum 公共必修专业课检查
    curriculum = d.get('curriculum', {})
    public = curriculum.get('公共必修 (所有院校都开)', [])
    if isinstance(public, list):
        # 兼容 string 和 dict (e.g., {"name": "...", "credit": "..."})
        public_text = ' '.join(
            item if isinstance(item, str) else item.get('name', '')
            for item in public
        )
        for forbidden in FORBIDDEN_IN_PUBLIC:
            if forbidden in public_text:
                errors.append(f'[CRITICAL] curriculum 公共必修填专业课: 「{forbidden}」 命中 → 专业课必须放通用核心')

    # 4. curriculum 3 段必须都有内容
    for k in CURRICULUM_KEYS:
        v = curriculum.get(k, [])
        if isinstance(v, list) and len(v) == 0:
            warnings.append(f'[WARNING] curriculum.{k}: 空数组 → 应填真实课程')

    # 5. salary 应统一 schema (所有阶段都是对象)
    salary = d.get('salary', {})
    if isinstance(salary, dict):
        non_schema = [k for k, v in salary.items() if not isinstance(v, dict)]
        if non_schema:
            warnings.append(f'[WARNING] salary 这些阶段不是 p25/p50/p75 对象: {non_schema}')

    # 6. deep_study 5-7 路径合计应 ≈ 100%
    deep_study = d.get('deep_study', {})
    if isinstance(deep_study, dict) and deep_study:
        total = sum(v for v in deep_study.values() if isinstance(v, (int, float)))
        if total < 80 or total > 120:
            warnings.append(f'[WARNING] deep_study 合计 {total}% 不在 80-120 区间 (合理范围 95-105%)')

    # 7. employment_direction pct 合计应 ≈ 100%
    emp_dir = d.get('employment_direction', [])
    if isinstance(emp_dir, list) and emp_dir:
        total = sum(item.get('pct', 0) for item in emp_dir if isinstance(item, dict))
        if total < 80 or total > 120:
            warnings.append(f'[WARNING] employment_direction pct 合计 {total}% 不在 80-120 区间')

    passed = len(errors) == 0
    return passed, errors, warnings


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == '--all':
        slugs = sorted([p.stem for p in CURATED.glob('*.json')])
    elif sys.argv[1] == '--staged':
        import subprocess
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                              capture_output=True, text=True, cwd=ROOT)
        slugs = []
        for f in result.stdout.strip().split('\n'):
            if 'curated/' in f and f.endswith('.json'):
                slug = pathlib.Path(f).stem
                if slug not in slugs:
                    slugs.append(slug)
    else:
        slugs = sys.argv[1:]

    total_errors = 0
    total_warnings = 0
    failed = []
    warned = []

    for slug in slugs:
        passed, errors, warnings = check_major(slug)
        status = '✓' if passed else '❌'
        if errors:
            print(f'\n{status} {slug}:')
            for e in errors:
                print(f'  ❌ {e}')
            failed.append(slug)
        if warnings:
            if not errors:
                print(f'\n{status} {slug} (warnings):')
            for w in warnings:
                print(f'  ⚠️  {w}')
            warned.append(slug)
        elif not errors:
            print(f'{status} {slug}')
        total_errors += len(errors)
        total_warnings += len(warnings)

    print()
    print('━' * 60)
    print(f'汇总: {len(slugs)} 篇检查')
    print(f'  ✓ 通过: {len(slugs) - len(failed)} 篇')
    print(f'  ❌ 失败: {len(failed)} 篇 ({total_errors} errors)')
    print(f'  ⚠️  警告: {len(warned)} 篇 ({total_warnings} warnings)')
    if failed:
        print(f'\n失败列表: {", ".join(failed)}')
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()