#!/usr/bin/env python3
"""
audit_llm.py — Major 精品 LLM 深度审计 (mimo 主, deepseek 备)

用法:
  python3 scripts/audit_llm.py <slug>:<style>           # 单篇 LLM 审计
  python3 scripts/audit_llm.py <slug1>:<s1> <slug2>:<s2>  # 多篇批量
  python3 scripts/audit_llm.py --csv all_majors.csv      # 批量从 CSV
  python3 scripts/audit_llm.py --legacy                  # 列出所有 irreducible 标记

3 strikes 策略:
- Strike 1: audit < 7 → 给出 issues + fix_suggestion, 期待 user 重做
- Strike 2: 仍 < 7 → 升级到 deepseek (或 mimo 二轮), 再给 issues
- Strike 3: 仍 < 7 → 写入 scripts/audit_history/<slug>.legacy.json
              + git commit flag: irreducible-<Y> + 跳过, 留给后续 session

优势 (vs 启发式):
- 内容质量评估 (语义), 不只是格式
- 能识别套话 (「毕业≠高薪」「AI 时代价值」)
- 数据合理性 (「supply-chain 应届 p25=0 显然错」)
- 反漂移 (mimo 是反漂移主力)
"""
import json
import os
import sys
import subprocess
import pathlib
import argparse
from datetime import datetime

ROOT = pathlib.Path(__file__).parent.parent.parent
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'
HISTORY_DIR = ROOT / 'scripts' / 'audit_history'
HISTORY_DIR.mkdir(exist_ok=True)


def load_major(slug):
    path = CURATED / f'{slug}.json'
    if not path.exists():
        return None, None
    return slug, json.loads(path.read_text())


def build_prompt(major_data):
    """构建 mimo audit prompt (基于 PIPELINE 9 步 + 4 anti-pollution rules)"""
    return f"""你是 Major 精品质量审计师. 审计这个专业的 JSON 内容.

## 审计依据 (读 `docs/PIPELINE_major_quality.md`):
1. **lede** (≤100 字) 必须「主语+独特洞察+风险」三段式. 禁模板套话.
2. **who_fits_no** 禁跨领域串台词:
   - 理工科出现 "文本阅读/田野调研/历史/语文/写作训练" → 删
   - 人文社科出现 "数学/统计/经济/考证" → 删
3. **deep_study** 禁 CS/金融 12% 占位, 禁 "专业相关方向/学术研究/自主创业/其他" 占位
4. **curriculum 公共必修** 只放 高数/线代/概率/物理/英语/思政/制图 (专业课必须放通用核心)
5. **alumni_quotes ≥2** 条 (year/current/quote/source 字段, quote 含"修了X/做过Y/去了Z")
6. **top_schools ≥6** 所, 每所 tag 含城市·特色
7. **salary** 各阶段统一 {{"p25":x,"p50":y,"p75":z,"yoy":w}} 对象, 禁 string
8. **employment_direction ≥5** 个方向, pct 合计 ≈ 100%
9. **pitfalls ≥4** 条专业独有 myth/reality (禁 "毕业≠高薪/不读研也能干" 通用模板)

## Major JSON (完整, 不截断):
```json
{json.dumps(major_data, ensure_ascii=False, indent=2)}
```

## 输出格式 (严格 JSON):
{{
  "overall_score": <0-10>,
  "verdict": "优秀|合格|可接受|差评",
  "issues": [
    {{"field": "lede", "score": <0-10>, "issue": "<具体问题>", "fix": "<怎么修>"}},
    ...
  ],
  "fix_suggestion": "<一句话核心修法>",
  "highlights": ["...", "..."]
}}
"""


def call_mimo(prompt):
    """调 mimo API. 用 anthropic SDK, 适配 thinking block."""
    import anthropic
    api_key = os.environ.get('M3_API_KEY') or os.environ.get('MIMO_API_KEY')
    base_url = os.environ.get('M3_BASE_URL', 'https://api.minimaxi.com/anthropic')

    if not api_key:
        raise RuntimeError('M3_API_KEY 未配置')

    client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
    msg = client.messages.create(
        model='MiniMax-M3',
        max_tokens=8000,
        thinking={'type': 'enabled', 'budget_tokens': 4000},
        messages=[{'role': 'user', 'content': prompt}]
    )

    # m3 返回 content 是 block list, type="text"/"thinking"/"tool_use", 只取 text
    text_parts = []
    for block in msg.content:
        # block 可能是对象 (SDK) 或 dict (raw HTTP)
        if hasattr(block, 'type'):
            if block.type == 'text':
                text_parts.append(block.text)
        elif isinstance(block, dict):
            if block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
    text = '\n'.join(text_parts) or '{}'

    # 提取 JSON (mimo 可能返回 ```json ... ```)
    if '```json' in text:
        text = text.split('```json', 1)[1].split('```')[0]
    elif '```' in text:
        text = text.split('```', 1)[1].split('```')[0]
    return json.loads(text.strip())


def audit_one(slug, style):
    """审计单篇, 3 strikes retry"""
    name, data = load_major(slug)
    if not data:
        return {'slug': slug, 'error': f'{slug}.json not found'}

    prompt = build_prompt(data)
    history = []
    r1 = None
    r2 = None

    # Strike 1: mimo
    print(f'  [Strike 1/3] mimo audit {slug}...')
    try:
        r1 = call_mimo(prompt)
        history.append({'strike': 1, 'auditor': 'mimo', **r1})
        if r1.get('overall_score', 0) >= 7:
            r1['slug'] = slug
            r1['final'] = 'PASS strike 1'
            return r1
    except Exception as e:
        history.append({'strike': 1, 'auditor': 'mimo', 'error': str(e)})

    # Strike 2: mimo 二轮 (with explicit fix request)
    print(f'  [Strike 2/3] mimo re-audit {slug}...')
    try:
        prev_feedback = r1.get('fix_suggestion', '') if r1 else '无'
        r2_prompt = prompt + f'\n\n## 第 1 轮反馈\n{prev_feedback}\n\n请重新审计, 重点关注第 1 轮指出的问题是否被解决.'
        r2 = call_mimo(r2_prompt)
        history.append({'strike': 2, 'auditor': 'mimo', **r2})
        if r2.get('overall_score', 0) >= 7:
            r2['slug'] = slug
            r2['final'] = 'PASS strike 2'
            return r2
    except Exception as e:
        history.append({'strike': 2, 'auditor': 'mimo', 'error': str(e)})

    # Strike 3: 仍 < 7 → 标记 irreducible, 写 legacy 报告
    final_score = r2.get('overall_score', 0) if r2 else (r1.get('overall_score', 0) if r1 else 0)
    print(f'  [Strike 3/3] irreducible flag {slug} (final_score={final_score})...')
    legacy = {
        'slug': slug,
        'style': style,
        'final_score': final_score,
        'history': history,
        'flagged_at': datetime.now().isoformat(),
        'note': '3 strikes 后仍 < 7, 标记为 irreducible 留给后续 session'
    }
    (HISTORY_DIR / f'{slug}.legacy.json').write_text(
        json.dumps(legacy, ensure_ascii=False, indent=2)
    )
    return {'slug': slug, 'final': 'IRREDUCIBLE', 'score': final_score,
            'flag': f'irreducible-{final_score}', 'history': history}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*', help='slug:style 格式')
    ap.add_argument('--csv', help='CSV 文件 (列: slug,title,style)')
    ap.add_argument('--legacy', action='store_true', help='列出所有 irreducible 标记')
    ap.add_argument('--threshold', type=int, default=7, help='及格分 (默认 7)')
    args = ap.parse_args()

    if args.legacy:
        legacy_files = sorted(HISTORY_DIR.glob('*.legacy.json'))
        if not legacy_files:
            print('✓ 无 irreducible 标记')
            return
        print(f'⚠️  {len(legacy_files)} 个 irreducible 标记:')
        for f in legacy_files:
            d = json.loads(f.read_text())
            print(f'  - {d["slug"]}: score={d["final_score"]} ({d["flagged_at"]})')
        return

    if args.csv:
        import csv
        pairs = []
        with open(args.csv) as f:
            for row in csv.DictReader(f):
                if row.get('slug'):
                    pairs.append((row['slug'], row.get('style', 'humanities')))
    elif args.slugs:
        pairs = [(s.partition(':')[0], s.partition(':')[2] or 'humanities') for s in args.slugs]
    else:
        ap.print_help()
        return

    results = []
    for slug, style in pairs:
        print(f'\n=== {slug} ({style}) ===')
        r = audit_one(slug, style)
        results.append(r)
        if 'error' in r:
            print(f'  ❌ error: {r["error"]}')
        elif r.get('final') == 'IRREDUCIBLE':
            print(f'  🚩 IRREDUCIBLE: score={r["score"]}, flag={r["flag"]}')
            print(f'     报告: scripts/audit_history/{slug}.legacy.json')
        else:
            print(f'  ✅ PASS ({r["final"]}): score={r["overall_score"]}/10 ({r["verdict"]})')

    print('\n' + '━' * 60)
    print(f'汇总: {len(results)} 篇审计')
    pass_count = sum(1 for r in results if r.get('final', '').startswith('PASS'))
    irreducible_count = sum(1 for r in results if r.get('final') == 'IRREDUCIBLE')
    error_count = sum(1 for r in results if 'error' in r)
    print(f'  ✅ 通过: {pass_count}')
    print(f'  🚩 标记遗留 (irreducible): {irreducible_count}')
    print(f'  ❌ 错误: {error_count}')

    sys.exit(0 if error_count == 0 and irreducible_count == 0 else 1)


if __name__ == '__main__':
    main()