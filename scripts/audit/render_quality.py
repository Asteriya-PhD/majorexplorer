#!/usr/bin/env python3
"""
render_quality.py — 渲染后 HTML 质量门 (Day 49)

校验已渲染的 PC HTML + mobile HTML + source JSON, 共 13 条规则:
  SAL-MONO-1: 阶段内 p25<=p50<=p75
  SAL-MONO-2: 跨阶段 p50 单调 (应届 < 3年 < 5年 < 10年+)
  SAL-CAP-1:  资深 (10年+/资深) p75<=100
  SAL-NOTE-1: note 仅 senior (WARN)
  HTML-PC-1:  PC 8 段齐备 (id="overview/curriculum/schools/companies/salary/directions/quotes/xuanke")
  HTML-PC-2:  meta description 50-160 字符 + 已转义
  HTML-PC-3:  JSON-LD <script type="application/ld+json"> 块存在
  HTML-PC-4:  og:title / og:description / og:image 三件套
  HTML-MB-1:  mobile 11 段 (一二三四五六七八十十一) 全有
  FIELD-1:    alumni_quotes 无 alum-N 字面占位
  FIELD-2:    hero_quote 10-200 字 + 含署名 (WARN)
  FIELD-3:    xuanke item 有 name 字段 (WARN)
  FIELD-4:    employment_direction pct 合计 ∈ [80, 120]

用法:
  python3 scripts/audit/render_quality.py --all [--sync-registry]
  python3 scripts/audit/render_quality.py --slug <slug>
  python3 scripts/audit/render_quality.py --staged
  python3 scripts/audit/render_quality.py --fixtures <dir>

退出码: 0 clean / 1 ≥1 ERROR / 2 catastrophic (manifest 坏)
输出: test_results/render_quality_{ts}.json + stdout 摘要
"""
import argparse
import json
import re
import subprocess
import sys
import time
import datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'
PUBLIC = ROOT / 'public'
PUBLIC_MOBILE = PUBLIC / 'm' / 'majors'
MANIFEST = PUBLIC / 'data' / 'manifest.json'
TEST_RESULTS = ROOT / 'test_results'
REGISTRY_SCRIPT = ROOT / 'scripts' / 'audit' / 'update_audit_registry.py'

# ───────────────────────────────────────────────────────────────────
# 规则定义
# ───────────────────────────────────────────────────────────────────

# 阶段排序: 越小越初级
STAGE_RANK = [
    ('应届', 0),
    ('0-2', 1),
    ('1-3', 2),
    ('2年', 2),
    ('3年', 3),
    ('5年', 4),
    ('8年', 5),
    ('10年', 6),
    ('资深', 6),
    ('主编', 6),
]

SENIOR_KEYWORDS = ['10年', '资深', '高级', '专家', '合伙人', '管理层', '主编']

NOTE_EXCEPTION_KEYWORDS = ['头部', '合伙人', 'CTO', '明星', '顶级', '首席', 'VP']

PC_SECTIONS = [
    'overview', 'curriculum', 'schools', 'companies',
    'salary', 'directions', 'quotes', 'xuanke',
]

MOBILE_NUMS = ['一', '二', '三', '四', '五', '六', '七', '八', '十', '十一']  # 10 段 (无 九)

ALUMNI_PLACEHOLDER_RE = re.compile(r'\balum-\d+\b')
META_DESC_RE = re.compile(
    r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE
)
JSONLD_RE = re.compile(
    r'<script\s+type="application/ld\+json">([^<]+)</script>', re.DOTALL
)
OG_TITLE_RE = re.compile(
    r'<meta\s+property="og:title"\s+content="([^"]+)"', re.IGNORECASE
)
OG_DESC_RE = re.compile(
    r'<meta\s+property="og:description"\s+content="([^"]+)"', re.IGNORECASE
)
OG_IMAGE_RE = re.compile(
    r'<meta\s+property="og:image"\s+content="([^"]+)"', re.IGNORECASE
)


def stage_rank(stage_name: str) -> int | None:
    """返回 stage 在 STAGE_RANK 中的 rank, 找不到返回 None"""
    for kw, rank in STAGE_RANK:
        if kw in stage_name:
            return rank
    return None


def is_senior(stage_name: str) -> bool:
    return any(kw in stage_name for kw in SENIOR_KEYWORDS)


# ───────────────────────────────────────────────────────────────────
# 规则实现
# ───────────────────────────────────────────────────────────────────

def check_salary_mono_1(salary: dict) -> list[dict]:
    """SAL-MONO-1: 阶段内 p25<=p50<=p75"""
    errs = []
    for stage_name, vals in salary.items():
        if not isinstance(vals, dict):
            continue
        p25 = vals.get('p25')
        p50 = vals.get('p50')
        p75 = vals.get('p75')
        if not all(isinstance(v, (int, float)) for v in (p25, p50, p75)):
            continue
        if p25 > p50:
            errs.append({
                'rule': 'SAL-MONO-1',
                'stage': stage_name,
                'msg': f'p25({p25}) > p50({p50})',
            })
        if p50 > p75:
            errs.append({
                'rule': 'SAL-MONO-1',
                'stage': stage_name,
                'msg': f'p50({p50}) > p75({p75})',
            })
    return errs


def check_salary_mono_2(salary: dict) -> list[dict]:
    """SAL-MONO-2: 跨阶段 p50 单调递增.

    同一 rank 内不比较 (允许"应届生"拆"一线/二三线"细分):
      应届生(一三线) p50=18, 应届生(二三线) p50=12 → 同 rank 0, 不报
      但 rank 0 的最小值(p50_max_within_rank=18) 必须 <= rank 1 的最小值
    """
    errs = []
    # 按 rank 分组, 取每组最高 p50 (代表该 stage 顶端) 与最低 p50 (代表底部)
    rank_groups: dict[int, list[tuple[str, float]]] = {}
    for stage_name, vals in salary.items():
        if not isinstance(vals, dict) or not isinstance(vals.get('p50'), (int, float)):
            continue
        rank = stage_rank(stage_name)
        if rank is None:
            continue
        rank_groups.setdefault(rank, []).append((stage_name, vals['p50']))
    # 对每个 rank, 取该 rank 所有细分中**最低** p50 (因为低端决定"是否后阶段比前阶段高")
    rank_min: dict[int, tuple[str, float]] = {}
    for rank, entries in rank_groups.items():
        entries.sort(key=lambda x: x[1])
        rank_min[rank] = entries[0]  # min
    sorted_ranks = sorted(rank_min.keys())
    for i in range(len(sorted_ranks) - 1):
        a_rank = sorted_ranks[i]
        b_rank = sorted_ranks[i + 1]
        if a_rank == b_rank:
            continue
        a_name, a_p50 = rank_min[a_rank]
        b_name, b_p50 = rank_min[b_rank]
        # 跳过相邻 rank 跨度 (允许应届 12 < 3年 18, 即低端 vs 高端)
        # 但要求低端(应届 min) ≤ 高端(3年 min): 也就是应届最低不应比 3年最低还高
        if a_p50 > b_p50:
            errs.append({
                'rule': 'SAL-MONO-2',
                'msg': f'p50 跨阶段倒挂: {a_name}(p50={a_p50}) > {b_name}(p50={b_p50})',
            })
    return errs


def check_salary_cap_1(salary: dict) -> list[dict]:
    """SAL-CAP-1: 资深 stage p75 <= 100, 含例外 note 时 p75 <= 200"""
    errs = []
    for stage_name, vals in salary.items():
        if not isinstance(vals, dict) or not is_senior(stage_name):
            continue
        p75 = vals.get('p75')
        if not isinstance(p75, (int, float)):
            continue
        note = vals.get('note', '')
        has_exception = any(kw in note for kw in NOTE_EXCEPTION_KEYWORDS)
        if has_exception:
            if p75 > 200:
                errs.append({
                    'rule': 'SAL-CAP-1',
                    'stage': stage_name,
                    'msg': f'资深 p75={p75} 即便含头部例外仍 > 200',
                })
        else:
            if p75 > 100:
                errs.append({
                    'rule': 'SAL-CAP-1',
                    'stage': stage_name,
                    'msg': f'资深 p75={p75} > 100 无例外说明',
                })
    return errs


def check_salary_note_1(salary: dict) -> list[dict]:
    """SAL-NOTE-1: note 仅允许 senior (WARN)"""
    warns = []
    for stage_name, vals in salary.items():
        if not isinstance(vals, dict):
            continue
        if 'note' in vals and vals['note'] and not is_senior(stage_name):
            warns.append({
                'rule': 'SAL-NOTE-1',
                'stage': stage_name,
                'msg': f'非资深 stage 含 note 字段 (应仅 senior)',
            })
    return warns


def check_html_pc_1(html: str) -> list[dict]:
    """HTML-PC-1: PC 8 段齐备"""
    errs = []
    for sec in PC_SECTIONS:
        # 兼容 id="<sec>" 或 id="tab-<sec>"
        if not re.search(rf'id=["\'](?:tab-)?{sec}["\']', html):
            errs.append({
                'rule': 'HTML-PC-1',
                'section': sec,
                'msg': f'PC 缺 section: {sec}',
            })
    return errs


def check_html_pc_2(html: str) -> list[dict]:
    """HTML-PC-2: meta description 50-160 字符 + 已转义"""
    errs = []
    m = META_DESC_RE.search(html)
    if not m:
        errs.append({'rule': 'HTML-PC-2', 'msg': 'meta description 缺失'})
        return errs
    content = m.group(1)
    if len(content) < 50 or len(content) > 160:
        errs.append({
            'rule': 'HTML-PC-2',
            'msg': f'meta description 长度 {len(content)} 不在 [50, 160]',
        })
    # 已转义检查: 字面 `<` 在 HTML attribute content 里是非法的
    if '<' in content or '>' in content:
        errs.append({
            'rule': 'HTML-PC-2',
            'msg': 'meta description 含未转义 < 或 > (P0 html-escape bug)',
        })
    return errs


def check_html_pc_3(html: str) -> list[dict]:
    """HTML-PC-3: JSON-LD <script type="application/ld+json"> 块存在且合法 JSON"""
    errs = []
    m = JSONLD_RE.search(html)
    if not m:
        errs.append({'rule': 'HTML-PC-3', 'msg': 'JSON-LD <script> 块缺失'})
        return errs
    try:
        json.loads(m.group(1))
    except (json.JSONDecodeError, ValueError) as e:
        errs.append({
            'rule': 'HTML-PC-3',
            'msg': f'JSON-LD 内容非合法 JSON: {e}',
        })
    return errs


def check_html_pc_4(html: str) -> list[dict]:
    """HTML-PC-4: og:title / og:description / og:image 三件套 + content 非空"""
    errs = []
    for name, regex in [
        ('og:title', OG_TITLE_RE),
        ('og:description', OG_DESC_RE),
        ('og:image', OG_IMAGE_RE),
    ]:
        m = regex.search(html)
        if not m or not m.group(1).strip():
            errs.append({'rule': 'HTML-PC-4', 'msg': f'{name} 缺失或空'})
    return errs


def check_html_mb_1(html: str) -> list[dict]:
    """HTML-MB-1: mobile 11 段 (一二三四五六七八十十一) 全有"""
    errs = []
    for c in MOBILE_NUMS:
        if f'<span class="art-num">{c}</span>' not in html:
            errs.append({
                'rule': 'HTML-MB-1',
                'msg': f'mobile 缺 art-num: {c}',
            })
    return errs


def check_field_1(data: dict) -> list[dict]:
    """FIELD-1: alumni_quotes 无 alum-N 字面占位"""
    errs = []
    alumni = data.get('alumni_quotes', [])
    blob = json.dumps(alumni, ensure_ascii=False)
    if ALUMNI_PLACEHOLDER_RE.search(blob):
        matches = ALUMNI_PLACEHOLDER_RE.findall(blob)
        errs.append({
            'rule': 'FIELD-1',
            'msg': f'alumni_quotes 含字面占位符: {matches[:3]}',
        })
    return errs


def check_field_2(data: dict) -> list[dict]:
    """FIELD-2: hero_quote 10-200 字 + 含署名 (WARN)"""
    warns = []
    hq = data.get('hero_quote', '')
    if not isinstance(hq, str):
        return warns
    if not (10 <= len(hq) <= 200):
        warns.append({
            'rule': 'FIELD-2',
            'msg': f'hero_quote 长度 {len(hq)} 不在 [10, 200]',
        })
    # 署名标记: 含 —/——/「/" 或 hero_quote_sig 字段
    has_sig = any(marker in hq for marker in ['——', '—', '「', '"'])
    sig_field = data.get('hero_quote_sig', '')
    if not has_sig and not sig_field:
        warns.append({
            'rule': 'FIELD-2',
            'msg': 'hero_quote 缺署名 (无 —/——/「/"/hero_quote_sig)',
        })
    return warns


def check_field_3(data: dict) -> list[dict]:
    """FIELD-3: xuanke item 有 name 字段 (WARN)"""
    warns = []
    xuanke = data.get('xuanke_req_list', [])
    if not isinstance(xuanke, list):
        return warns
    for i, item in enumerate(xuanke):
        if not isinstance(item, dict):
            continue
        if 'name' not in item:
            field_names = list(item.keys())
            warns.append({
                'rule': 'FIELD-3',
                'index': i,
                'msg': f'xuanke[{i}] 缺 name 字段 (实际字段: {field_names})',
            })
    return warns


def check_field_4(data: dict) -> list[dict]:
    """FIELD-4: employment_direction pct 合计 ∈ [80, 120]"""
    errs = []
    emp = data.get('employment_direction', [])
    if not isinstance(emp, list) or not emp:
        return errs
    total = sum(e.get('pct', 0) for e in emp if isinstance(e, dict))
    if not (80 <= total <= 120):
        errs.append({
            'rule': 'FIELD-4',
            'msg': f'employment_direction pct 合计 {total} 不在 [80, 120]',
        })
    return errs


# ───────────────────────────────────────────────────────────────────
# 单 slug 检查入口
# ───────────────────────────────────────────────────────────────────

def check_one(slug: str, *, data_override: dict | None = None,
              pc_html_override: str | None = None,
              mb_html_override: str | None = None) -> dict:
    """
    检查单个 slug, 返回 {errors: [...], warnings: [...], rule_counts: {...}}

    Override 参数 (用于 fixture 模式):
      data_override:    用此 dict 替代 curated/{slug}.json
      pc_html_override: 用此字符串替代 public/{slug}.html
      mb_html_override: 用此字符串替代 public/m/majors/{slug}.html
    """
    errors: list[dict] = []
    warnings: list[dict] = []

    # 1. 读 source JSON (override 优先)
    if data_override is not None:
        data = data_override
    else:
        json_path = CURATED / f'{slug}.json'
        if not json_path.exists():
            return {
                'slug': slug,
                'errors': [{'rule': 'META', 'msg': f'JSON 文件不存在: {json_path.name}'}],
                'warnings': [],
                'rule_counts': {},
            }
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError as e:
            return {
                'slug': slug,
                'errors': [{'rule': 'META', 'msg': f'JSON 解析失败: {e}'}],
                'warnings': [],
                'rule_counts': {},
            }

    # 2. 字段规则 (基于 JSON)
    salary = data.get('salary', {})
    if isinstance(salary, dict):
        errors.extend(check_salary_mono_1(salary))
        errors.extend(check_salary_mono_2(salary))
        errors.extend(check_salary_cap_1(salary))
        warnings.extend(check_salary_note_1(salary))

    errors.extend(check_field_1(data))
    warnings.extend(check_field_2(data))
    warnings.extend(check_field_3(data))
    errors.extend(check_field_4(data))

    # 3. PC HTML 规则
    if pc_html_override is not None:
        pc_html = pc_html_override
    else:
        pc_path = PUBLIC / f'{slug}.html'
        if pc_path.exists():
            try:
                pc_html = pc_path.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                errors.append({'rule': 'META', 'msg': f'PC HTML 读取失败: {e}'})
                pc_html = ''
        else:
            pc_html = ''
    if pc_html:
        errors.extend(check_html_pc_1(pc_html))
        errors.extend(check_html_pc_2(pc_html))
        errors.extend(check_html_pc_3(pc_html))
        errors.extend(check_html_pc_4(pc_html))
    elif pc_html_override is None:
        # 没传 override 且 PC HTML 不存在 → WARN (Day 49 baseline 期不少 major 还没渲染)
        warnings.append({'rule': 'META', 'msg': f'PC HTML 不存在: {slug}.html'})

    # 4. Mobile HTML 规则
    if mb_html_override is not None:
        mb_html = mb_html_override
    else:
        mb_path = PUBLIC_MOBILE / f'{slug}.html'
        if mb_path.exists():
            try:
                mb_html = mb_path.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                errors.append({'rule': 'META', 'msg': f'mobile HTML 读取失败: {e}'})
                mb_html = ''
            else:
                pass
        else:
            mb_html = ''
    if mb_html:
        errors.extend(check_html_mb_1(mb_html))
    # mobile 缺失不强制 (Day 49 早期 mobile 覆盖不全)

    rule_counts = defaultdict(int)
    for e in errors:
        rule_counts[e['rule']] += 1
    for w in warnings:
        rule_counts[w['rule']] += 1

    return {
        'slug': slug,
        'errors': errors,
        'warnings': warnings,
        'rule_counts': dict(rule_counts),
    }


# ───────────────────────────────────────────────────────────────────
# Manifest / staged / fixtures 入口
# ───────────────────────────────────────────────────────────────────

def load_manifest_slugs() -> list[str]:
    if not MANIFEST.exists():
        raise SystemExit(f'MANIFEST missing: {MANIFEST}')
    try:
        m = json.loads(MANIFEST.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(f'MANIFEST parse fail: {e}')
    return [entry['slug'] for entry in m.get('majors', [])]


def get_staged_slugs() -> list[str]:
    """从 git staged 取 slug (curated/*.json 或 public/<slug>.html)"""
    try:
        out = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            capture_output=True, text=True, cwd=ROOT
        ).stdout
    except Exception:
        return []
    slugs = set()
    for line in out.splitlines():
        line = line.strip()
        m = re.search(r'curated/([^/]+)\.json$', line)
        if m:
            slugs.add(m.group(1))
            continue
        m = re.search(r'public/(?:m/majors/)?([^/]+)\.html$', line)
        if m and not m.group(1).startswith('data'):
            slugs.add(m.group(1))
    return sorted(slugs)


def load_fixtures(fixtures_dir: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """加载 fixtures: 干净 slug 列表 + (fixture_name, expected_rule) 违规列表

    slug 优先读 fixture 内的 _fixture_slug 字段, fallback 到文件名 stem.
    """
    clean: list[str] = []
    violations: list[tuple[str, str]] = []
    if not fixtures_dir.exists():
        raise SystemExit(f'Fixtures dir not found: {fixtures_dir}')
    for json_file in sorted(fixtures_dir.glob('*.json')):
        try:
            d = json.loads(json_file.read_text())
        except Exception as e:
            print(f'⚠️  fixture {json_file.name} JSON 解析失败: {e}', file=sys.stderr)
            continue
        name = d.get('_fixture_slug') or json_file.stem
        if d.get('_expected_clean'):
            clean.append(name)
        for v in d.get('_expected_violations', []):
            violations.append((name, v))
    return clean, violations


# ───────────────────────────────────────────────────────────────────
# 输出 + 同步
# ───────────────────────────────────────────────────────────────────

def write_results(results: list[dict], *, slug_filter: str | None = None) -> dict:
    """汇总结果, 写 test_results/render_quality_{ts}.json"""
    totals = {
        'checked': len(results),
        'passed': sum(1 for r in results if not r['errors']),
        'errors': sum(1 for r in results if r['errors']),
        'warnings': sum(1 for r in results if r['warnings'] and not r['errors']),
    }
    rule_counts: dict[str, int] = defaultdict(int)
    for r in results:
        for e in r['errors']:
            rule_counts[e['rule']] += 1
        for w in r['warnings']:
            rule_counts[w['rule']] += 1

    payload = {
        'ts': int(time.time()),
        'version': '1.0',
        'filter': slug_filter,
        'totals': totals,
        'rule_counts': dict(rule_counts),
        'results': results,
    }
    TEST_RESULTS.mkdir(exist_ok=True)
    out_path = TEST_RESULTS / f'render_quality_{int(time.time())}.json'
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def print_summary(payload: dict, *, no_warn: bool = False) -> int:
    """打印摘要, 返回退出码 (0/1)"""
    t = payload['totals']
    rc = payload['rule_counts']
    print('\n── render_quality ──')
    print(f"扫描 {t['checked']} 篇")
    for rule, count in sorted(rc.items(), key=lambda x: -x[1]):
        print(f'  {rule}: {count} 次')
    print('──')
    print(f"✓ 通过: {t['passed']} 篇")
    if t['errors']:
        print(f"❌ 失败: {t['errors']} 篇 (有 ERROR)")
    if t['warnings'] and not no_warn:
        print(f"⚠️  警告: {t['warnings']} 篇")
    return 0 if t['errors'] == 0 else 1


def sync_registry(payload: dict) -> None:
    """调 update_audit_registry.py --from-render-quality"""
    # 找刚写的 test_results/render_quality_*.json
    candidates = sorted(TEST_RESULTS.glob('render_quality_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        print('⚠️  sync-registry: 无 test_results/render_quality_*.json 可同步', file=sys.stderr)
        return
    latest = candidates[0]
    cmd = ['python3', str(REGISTRY_SCRIPT), '--from-render-quality', str(latest)]
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            print(f'\n📋 registry 已同步: {latest.name}')
        else:
            print(f'\n⚠️  registry 同步失败 (exit={r.returncode}):', file=sys.stderr)
            print(r.stderr[:500], file=sys.stderr)
    except Exception as e:
        print(f'\n⚠️  registry 同步异常: {e}', file=sys.stderr)


# ───────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='渲染后 HTML 质量门 (Day 49)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--all', action='store_true', help='扫所有 manifest majors')
    g.add_argument('--slug', help='单 slug')
    g.add_argument('--staged', action='store_true', help='git staged diff')
    g.add_argument('--fixtures', help='fixtures 目录 (clean+violations)')
    ap.add_argument('--sync-registry', action='store_true', help='写完自动同步 registry')
    ap.add_argument('--no-warn', action='store_true', help='WARN 不显示, 只关心 ERROR')
    args = ap.parse_args()

    started = time.time()

    if args.fixtures:
        fixtures_dir = Path(args.fixtures)
        clean, violations = load_fixtures(fixtures_dir)
        results = []
        # 干净 fixture: 用 fixture 自身的 JSON 数据 (slug 仅作标签, 不读真实文件)
        # load_fixtures 已按 _fixture_slug 分桶, 直接遍历 fixtures_dir 找匹配文件
        slug_to_path: dict[str, Path] = {}
        for fp in fixtures_dir.glob('*.json'):
            try:
                d = json.loads(fp.read_text())
            except Exception:
                continue
            name = d.get('_fixture_slug') or fp.stem
            slug_to_path[name] = fp

        for slug in clean:
            fp = slug_to_path.get(slug)
            if not fp:
                results.append({
                    'slug': slug,
                    'errors': [{'rule': 'TEST-SETUP', 'msg': f'fixture JSON 找不到: {slug}'}],
                    'warnings': [], 'rule_counts': {},
                })
                continue
            d = json.loads(fp.read_text())
            r = check_one(slug, data_override=d)
            r['_fixture'] = slug
            results.append(r)
        # 违规 fixture: 期望 rule 出现在 errors 或 warnings 里
        for slug, expected_rule in violations:
            fp = slug_to_path.get(slug)
            if not fp:
                results.append({
                    'slug': slug,
                    'errors': [{'rule': 'TEST-SETUP', 'msg': f'fixture JSON 找不到: {slug}'}],
                    'warnings': [], 'rule_counts': {},
                })
                continue
            d = json.loads(fp.read_text())
            # fixture 内联 _pc_html / _mb_html 用于 HTML 检查
            pc_html = d.get('_pc_html')
            mb_html = d.get('_mb_html')
            r = check_one(
                slug,
                data_override=d,
                pc_html_override=pc_html,
                mb_html_override=mb_html,
            )
            r['_fixture'] = slug
            rule_in_errors = any(e['rule'] == expected_rule for e in r['errors'])
            rule_in_warnings = any(w['rule'] == expected_rule for w in r['warnings'])
            if rule_in_errors or rule_in_warnings:
                results.append({
                    '_fixture': slug + ' [PASS]',
                    'slug': slug,
                    'errors': [],
                    'warnings': [{'rule': 'TEST-PASS', 'msg': f'命中期望 rule {expected_rule}'}],
                    'rule_counts': {'TEST-PASS': 1},
                })
            else:
                results.append({
                    '_fixture': slug + ' [FAIL]',
                    'slug': slug,
                    'errors': [{
                        'rule': 'TEST-FAIL',
                        'msg': f'期望 {expected_rule} 未命中. 实际 errors={[e["rule"] for e in r["errors"]]} warnings={[w["rule"] for w in r["warnings"]]}',
                    }],
                    'warnings': [],
                    'rule_counts': {'TEST-FAIL': 1},
                })
        payload = write_results(results, slug_filter='fixtures')
        rc = print_summary(payload, no_warn=args.no_warn)
        elapsed = time.time() - started
        print(f'\n⏱️  {elapsed:.1f}s')
        sys.exit(0 if rc == 0 else 1)

    if args.slug:
        results = [check_one(args.slug)]
        payload = write_results(results, slug_filter=args.slug)
        rc = print_summary(payload, no_warn=args.no_warn)
        sys.exit(rc)

    if args.staged:
        slugs = get_staged_slugs()
        if not slugs:
            print('⏭️  无 staged slug')
            sys.exit(0)
        results = [check_one(s) for s in slugs]
        payload = write_results(results, slug_filter='staged')
        rc = print_summary(payload, no_warn=args.no_warn)
        if args.sync_registry:
            sync_registry(payload)
        sys.exit(rc)

    if args.all:
        slugs = load_manifest_slugs()
        print(f'扫描 manifest {len(slugs)} 篇 ...')
        results = []
        for i, s in enumerate(slugs, 1):
            results.append(check_one(s))
            if i % 50 == 0:
                print(f'  ... {i}/{len(slugs)}', file=sys.stderr)
        payload = write_results(results, slug_filter='all')
        rc = print_summary(payload, no_warn=args.no_warn)
        elapsed = time.time() - started
        print(f'\n⏱️  {elapsed:.1f}s')
        if args.sync_registry:
            sync_registry(payload)
        sys.exit(rc)


if __name__ == '__main__':
    main()