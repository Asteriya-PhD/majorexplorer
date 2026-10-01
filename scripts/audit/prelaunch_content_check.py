#!/usr/bin/env python3
"""
prelaunch_content_check.py — 上线前内容检测 (2026-10-01)

定位: 专业 HTML 提交/部署**之前**跑的闸门, 与 commit 阶段解耦。
commit 阶段防的是"你写错了", 本脚本防的是"你忘了渲染 / 渲染漏了 /
渲染器坏了"。三类线上事故都是它拦下来的:

  A. 改了 JSON 没重渲 HTML  → 内容漂移 (alum-N 12 篇就是这么上线的)
  B. 渲染器字段名不匹配    → 内容静默丢失 (emp-desc 4224 处)
  C. SEO 注入块丢失/重复   → 部署后 meta 失效

用法:
  # 1. 最常用: 对 staged 的专业做全链路检查
  python3 scripts/audit/prelaunch_content_check.py --staged

  # 2. 全量巡检 (部署前跑这个, 625 篇 ~90s, 0¥)
  python3 scripts/audit/prelaunch_content_check.py --all

  # 3. 单篇
  python3 scripts/audit/prelaunch_content_check.py --slug <slug>

退出码: 0 = 可上线 / 1 = 有 BLOCKER
"""
import argparse
import json
import re
import subprocess
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'
PUBLIC = ROOT / 'public'
PUBLIC_MB = PUBLIC / 'm' / 'majors'
TEST_RESULTS = ROOT / 'test_results'
SKIP = {'manifest.json', 'TEMPLATE.json'}


def norm(s):
    if s is None:
        return ''
    import html as _h
    s = _h.unescape(str(s))
    # ⚠️ 只剥真正的 HTML 标签; 不能用 <[^>]+> —— 会把正文里的
    # "通过率 < 15%/科, ... 考不出注会" 当标签整段吃掉
    # (2026-10-01 实测踩过, 导致 5 篇内容在位却被判"未渲染")
    s = re.sub(r'<(?:!--.*?-->|/?[a-zA-Z][^<>]*?)>', '', s, flags=re.DOTALL)
    s = re.sub(r'\s+', '', s)
    for a, b in (('，', ','), ('。', '.'), ('、', ','), ('；', ';'),
                 ('：', ':'), ('（', '('), ('）', ')'), ('！', '!'),
                 ('？', '?'), ('“', '"'), ('”', '"'), ('‘', "'"),
                 ('’', "'"), ('—', '-'), ('／', '/'), ('％', '%')):
        s = s.replace(a, b)
    return s


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception as e:
        return {'__error__': str(e)}


def git(*args):
    try:
        return subprocess.run(['git', *args], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ''


# ═══════════════════════════════════════════════════════════════════
# 检查项
# ═══════════════════════════════════════════════════════════════════

def check_a_freshness(slug, d, pc, mb):
    """A. 渲染新鲜度: JSON 内容是否真的出现在 HTML 里

    覆盖两类事故:
      - 完全没重渲 (HTML 是旧版)
      - 局部漏渲 (某字段没进 HTML)
    """
    errs = []
    if d.get('style') == 'medicine':
        return errs      # 医学类走 v4_medicine.py 独立渲染器, lede/pitfalls 不适用

    ov = d.get('overview_v2') or {}
    is_simple = bool(ov.get('what_you_learn')) or \
        isinstance(ov.get('who_fits_yes'), list)

    def probe(field, val, html, minlen=8):
        if not isinstance(val, str) or len(val) < minlen or not html:
            return
        full = norm(val)
        if full in norm(html):
            return
        if full[:12] in norm(html) or full[-12:] in norm(html):
            return
        errs.append(f'A/未渲染 {field}: …{full[:34]}…')

    if pc:
        probe('lede', ov.get('lede') or d.get('lede'), pc)
        probe('summary', d.get('summary'), pc)
        for i, p in enumerate(ov.get('pitfalls') or []):
            if isinstance(p, dict):
                probe(f'pitfalls[{i}].reality', p.get('reality'), pc, 10)
        for i, q in enumerate(d.get('alumni_quotes') or []):
            if isinstance(q, dict):
                probe(f'quotes[{i}]', q.get('quote'), pc, 10)

    if mb:
        # ⚠️ render_mobile.py:831 只渲染 emp_list[:8] —— 超出 8 条的方向
        # 不显示是设计上限, 不是 bug, 不计入闸门 (否则 23 篇永久噪音)。
        for i, e in enumerate(d.get('employment_direction') or []):
            if i >= 8:
                break
            if isinstance(e, dict):
                probe(f'empdir[{i}].desc', e.get('desc'), mb, 10)
    return errs


def check_b_render_loss(slug, d, pc, mb):
    """B. 渲染器静默丢失: HTML 里有容器但内容为空"""
    errs = []
    if mb:
        empties = len(re.findall(r'<div class="emp-desc">\s*</div>', mb))
        total = len(re.findall(r'<div class="emp-desc">', mb))
        if total and empties == total and total > 0:
            n = sum(1 for e in (d.get('employment_direction') or [])[:8]
                    if isinstance(e, dict) and (e.get('desc') or '').strip())
            if n:
                errs.append(
                    f'B/emp-desc 全空: {total} 个容器全空, 但 JSON 有 {n} 条 desc'
                    ' → 渲染器字段名不匹配 (check desc vs description)')
    if pc:
        for pat, desc in ((r'<strong>alum-\d', 'alum-N 占位符泄漏到页面'),
                          (r'\{\{[^}]+\}\}', '{{模板变量}} 未替换'),
                          (r'\[object Object\]', 'JS 渲染残留 [object Object]'),
                          (r'>\s*undefined\s*<', 'undefined 泄漏到正文')):
            m = re.search(pat, pc)
            if m:
                errs.append(f'B/{desc}: {m.group(0)[:24]}')
    return errs


def check_c_seo(slug, d, pc, mb):
    """C. SEO 注入块完整性 (重渲会丢, 重复注入会污染)"""
    errs = []
    for name, html in (('PC', pc), ('MB', mb)):
        if not html:
            continue
        for start, end, label in (
                ('<!-- BEGIN_SEO_TWITTER -->', '<!-- END_SEO_TWITTER -->', 'twitter'),
                ('<!-- BEGIN_SEO_HREFLANG -->', '<!-- END_SEO_HREFLANG -->', 'hreflang')):
            n = html.count(start)
            if n > 1:
                errs.append(f'C/{name}-{label} 块重复 {n} 次 (inject 脚本非幂等)')
    # meta 三件套 (只查 PC, 移动端不依赖)
    # ⚠️ 用正则实际探测, 不能用 `label in pc` —— label 是人类可读名
    #    ("JSON-LD"), 不是 HTML 里的字面量, 那样会 625 篇全误报。
    if pc:
        if not re.search(r'<meta\s+name="twitter:card"', pc):
            errs.append('C/PC 缺 twitter:card meta')
        if not re.search(r'<script\s+type="application/ld\+json"', pc):
            errs.append('C/PC 缺 JSON-LD 结构化数据')
        if not re.search(r'<meta\s+property="og:title"', pc):
            errs.append('C/PC 缺 og:title')
    return errs


def check_d_content(slug, d, pc=None, mb=None):
    """D. 内容底线: 占位符 / 空壳字段 (不依赖 HTML)"""
    errs = []
    blob = json.dumps(d, ensure_ascii=False)
    for pat, label in ((r'\bTODO\b|\bFIXME\b', 'TODO/FIXME 未清理'),
                       (r'alum-\d', 'alumni 占位符 alum-N'),
                       (r'lorem ipsum', 'Lorem 示例文本')):
        if re.search(pat, blob):
            errs.append(f'D/{label}')
    ov = d.get('overview_v2') or {}
    is_simple = bool(ov.get('what_you_learn')) or \
        isinstance(ov.get('who_fits_yes'), list)
    if not ov.get('who_fits_no') and is_simple:
        errs.append('D/simple 式 overview_v2 缺 who_fits_no (PC/MB 会空白)')
    if not ov.get('pitfalls'):
        errs.append('D/overview_v2 缺 pitfalls (避坑指南会空)')
    for f in ('lede', 'summary', 'curriculum', 'top_schools',
              'employment_direction', 'alumni_quotes'):
        if not d.get(f):
            errs.append(f'D/缺必填字段 {f}')
    return errs


CHECKS = (
    ('A 渲染新鲜度', check_a_freshness),
    ('B 渲染丢失', check_b_render_loss),
    ('C SEO 块', check_c_seo),
    ('D 内容底线', check_d_content),
)


def check_one(slug):
    d = load(CURATED / f'{slug}.json')
    if '__error__' in d:
        return [f'0/JSON 解析失败: {d["__error__"]}']
    pc_p, mb_p = PUBLIC / f'{slug}.html', PUBLIC_MB / f'{slug}.html'
    pc = pc_p.read_text(encoding='utf-8', errors='ignore') if pc_p.exists() else ''
    mb = mb_p.read_text(encoding='utf-8', errors='ignore') if mb_p.exists() else ''
    if not pc and not mb:
        return [f'0/HTML 未渲染: {slug} 既无 PC 也无 mobile 页面']
    errs = []
    for _, fn in CHECKS:
        try:
            errs += fn(slug, d, pc, mb)
        except Exception as e:  # noqa: BLE001
            errs.append(f'?/{fn.__name__} 异常: {e}')
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--staged', action='store_true',
                    help='只查 git staged 的专业')
    ap.add_argument('--all', action='store_true', help='全量 625 篇')
    ap.add_argument('--slug', help='单篇')
    ap.add_argument('--json-out', help='输出 JSON')
    args = ap.parse_args()

    files = sorted(f for f in CURATED.glob('*.json') if f.name not in SKIP)
    if args.slug:
        files = [f for f in files if f.stem == args.slug]
    elif args.staged:
        out = git('diff', '--cached', '--name-only', '--diff-filter=ACMR')
        names = {Path(x).name for x in out.splitlines() if x.strip()}
        files = [f for f in files if f.name in names]
        if not files:
            print('✅ 无 staged 专业 JSON, 跳过')
            return 0
    if not files:
        print('❌ 无文件', file=sys.stderr)
        return 1

    print()
    print('═' * 72)
    print(f'  prelaunch_content_check — {len(files)} 篇 '
          f'({"staged" if args.staged else "全量"})')
    print('═' * 72)

    bad = {}
    t0 = datetime.datetime.now()
    for i, f in enumerate(files):
        e = check_one(f.stem)
        if e:
            bad[f.stem] = e
        if (i + 1) % 150 == 0:
            print(f'  ... {i+1}/{len(files)}', flush=True)
    dur = (datetime.datetime.now() - t0).total_seconds()

    # 按检查类归因
    byclass = {}
    for slug, es in bad.items():
        for e in es:
            key = e.split('/')[0] + '/' + e.split('/')[1].split(':')[0] \
                if '/' in e else e[:2]
            byclass.setdefault(key, []).append(slug)

    print(f'\n  检查 {len(files)} 篇, {dur:.1f}s, 0¥')
    if not bad:
        print('  ✅ 全部可上线')
        return 0

    print(f'  ❌ {len(bad)} 篇有问题\n')
    print('  ── 按检查类归因 ──')
    for k, v in sorted(byclass.items(), key=lambda x: -len(x[1])):
        print(f'   {len(v):5d} 篇  {k}   e.g. {v[:3]}')
    print()
    for slug, es in sorted(bad.items())[:25]:
        print(f'  ▶ {slug}')
        for e in es[:6]:
            print(f'      {e}')

    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(bad, ensure_ascii=False, indent=1),
                     encoding='utf-8')
        print(f'\n  📄 → {p}')

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    tr = TEST_RESULTS / f'prelaunch_check_{ts}.json'
    tr.parent.mkdir(parents=True, exist_ok=True)
    tr.write_text(json.dumps({'ts': ts, 'scanned': len(files),
                              'failed': len(bad), 'detail': bad},
                             ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'  📄 → {tr}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
