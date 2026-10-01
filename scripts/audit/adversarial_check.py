#!/usr/bin/env python3
"""
adversarial_check.py — 专业 HTML 对抗性内容审查 (2026-10-01)

定位: 补 render_quality.py 13 规则 (只查结构) 的盲区 —— **内容正确性**。
render_quality 查的是"字段在不在/结构对不对", 本脚本查的是
"内容对不对/一不一 致/串没串台/数值讲不讲得通"。

9 大类对抗规则:
  X1 DRIFT-JSON-HTML  JSON 字段值在渲染 HTML 中找不到 (渲染漂移/漏渲)
  X2 DRIFT-PC-MB      PC 与 mobile 数据不一致 (双端分叉)
  X3 DRIFT-MANIFEST   manifest 与 source JSON 不一致
  X4 CROSS-TALK       学科串台: 文科内容出现在理工/反之, 模板套话
  X5 FACT-HARD        事实硬伤: 学位/学制/学信网占位/模板残留
  X6 NUM-CONTRA       数值矛盾: pct 合计/credit/名次/薪资
  X7 PLACEHOLDER      占位符未替换 (alum-N / XX / 待补充 / TODO)
  X8 DUP-CONTENT      跨专业大面积雷同 (抄袭式生成)
  X9 SCHEMA-DRIFT     schema 缺字段/类型错/枚举越界

用法:
  python3 scripts/audit/adversarial_check.py                # 全量
  python3 scripts/audit/adversarial_check.py --slug <slug>  # 单篇
  python3 scripts/audit/adversarial_check.py --cat X1        # 只跑某类
  python3 scripts/audit/adversarial_check.py --severity ERROR

退出码: 0 = 无 ERROR / 1 = 有 ERROR
"""
import argparse
import json
import re
import sys
import datetime
from pathlib import Path
from collections import defaultdict, Counter
from html import unescape

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'
PUBLIC = ROOT / 'public'
PUBLIC_MB = PUBLIC / 'm' / 'majors'
MANIFEST = PUBLIC / 'data' / 'manifest.json'
TEST_RESULTS = ROOT / 'test_results'

# ───────────────────────────────────────────────────────────────────
# 学科分组 (用于 X4 串台判定)
# ───────────────────────────────────────────────────────────────────

STEM = '理工农医'
HUM = '人文社科'
BUS = '经管法'
ART = '艺术体育'

# 每组独有的"信号词" —— 出现在错误学科组即为串台
# (只取区分度高的词, 避免 "大学/专业" 这类通用词误报)
GROUP_SIGNALS = {
    STEM: [
        '芯片', '半导体', '晶圆', '电路', '电路板', '嵌���式', '固件', '内核态',
        '分子', '原子', '化学反应', '化学键', '催化', '晶体结构', '晶格',
        '力学', '热力学', '流体', '刚体', '电磁', '量子', '波函数',
        '基因', '碱基', '蛋白质', '细胞培养', '菌株', '发酵', '酶活性',
        '飞行器', '气动', '推力', '弹道', '结构载荷', '疲劳寿命',
        '钻井', '储层', '页岩', '采收', '单产', '育种', '光合作用',
        '功率器件', '信号处理', '谐振', '阻抗匹配', '天线',
    ],
    HUM: [
        '文本细读', '田野调查', '口述史', '档案馆', '手稿', '版本学',
        '文学史', '修辞', '训诂', '诗学', '叙事学', '文献考证',
        '宪法原则', '法理', '罪刑法定', '程序正义',
        '民族志', '人类学', '符号学', '阐释学',
        # 语料/语言学向 (计算语言学、汉语言文学、翻译等)
        '语料', '音韵', '句法', '语义', '形态学', '语用', '方言',
        '文字学', '词汇', '语法', '语言学', '自然语言处理', '语料库',
        '修辞学', '语义学', '句法学', '音位',
        # 历史/哲学/教育
        '朝代', '史料', '文物', '遗址', '考据', '纪年', '年谱',
        '论证', '本体论', '认识论', '伦理学', '中国哲学', '西方哲学',
        '课程论', '教学论', '教育学', '心理学',
    ],
    BUS: [
        '报表合并', '审计准则', '内控', '成本核算', '现金流',
        '营销策略', '品牌溢价', '渠道', '定价', '促销',
        '个税', '所得税', '增值税', '税基', '税收法定',
        '尽职调查', '并购', '对赌', '私募', 'CFA', '财务建模',
        '民事权利', '违约责任', '善意第三人',
    ],
    ART: [
        '构图', '透视', '色��', '写生', '素描', '油画媒介',
        '乐理', '和声', '曲式', '视唱', '民族调式',
        '剧本', '角色塑造', '台步', '腔调',
    ],
}

ENG_MENJIA = {'理学', '工学', '农学', '医学', '管理学', '艺术学'}

# MOE 学科门类代码 → 组 (discipline 字段存的就是这个两位代码)
MOE2GROUP = {
    '01': HUM,    # 哲学
    '02': BUS,    # 经济学
    '03': BUS,    # 法学
    '04': STEM,   # 农学
    '05': HUM,    # 文学
    '06': HUM,    # 历史学
    '07': STEM,   # 理学
    '08': STEM,   # 工学
    '09': STEM,   # 农学(补充)
    '10': STEM,   # 医学
    '11': STEM,   # 军事学
    '12': BUS,    # 管理学
    '13': ART,    # 艺术学
    '14': HUM,    # 教育学
}

# ───────────────────────────────────────────────────────────────────
# 模板套话 (X4) —— 这些是"任何专业都能套"的空话, 不是专业洞察
# ───────────────────────────────────────────────────────────────────
TEMPLATE_BOILERPLAT = [
    r'是研究[^，。；]{2,14}的学科',
    r'在数字化时代',
    r'随着(社会|科技|时代|经济)的(发展|进步)',
    r'具有(广阔|良好)的发展前景',
    r'值得(每个|每位)(学生|同学)(深思|重视)',
    r'学科交叉',
    r'培养(复合型|高素质)人才',
]

# 他科专属词: 出现在 who_fits_no (劝退理由) 里 = 串台
# AGENTS.md anti-pollution 铁律 2 原文:
#   "理工科出现'文本阅读/田野调研/历史/语文' → 删;
#    人文社科出现'数学/统计/经济/考证' → 删"
HUM_ONLY_FORBIDDEN = [      # 人文社科专属 (理工科 who_fits_no 出现即串台)
    # 2026-10-01 实测校准: 删掉 '田野调研'/'手稿'/'档案馆' —— 武术学
    # (martial-arts-traditional-sports) 的体能训练含田野调研, 属正常。
    # 只保留区分度最高、几乎不可能出现在理工科劝退理由里的词。
    '文本细读', '口述史', '版本学', '训诂', '古籍', '碑帖', '目录学',
]
ENG_ONLY_FORBIDDEN = [      # 理工农医专属 (人文社科/经管法 who_fits_no 出现即串台)
    '寄存器', '内核态', '固件', '晶圆', '晶格', '电路板',
    '推力', '弹道', '钻井', '储层', '页岩', '酶活性', '菌株',
    '谐振', '阻抗匹配', '单产', '育种', '焊点', '示波器',
]
BUS_ONLY_FORBIDDEN = [      # 经管法专属
    '审计准则', '报表合并', '尽职调查', '对赌', '私募', 'CFA',
    '财务建模', '个税', '增值税', '税基', '内控', '注册会计师', '注会',
    # 注: '考公'/'考证' 已移除 —— 2026-10-01 实测 18 篇全部误报:
    #     电工证/执业兽医证/HCIE/选调受限 都是该专业真实的劝退门槛, 不是串台
]
# 人文社科 who_fits_no 禁 "数学/统计/经济" (AGENTS.md 铁律 2 原话)
HUM_ONLY_IN_MATH_CTX = ['高等数学', '数学分析', '概率论', '数理统计', '统计模型']
ART_ONLY_FORBIDDEN = [      # 艺术体育专属
    '视唱', '曲式', '素描', '写生', '透视', '台步',
]

# ───────────────────────────────────────────────────────────────────
# 事实硬伤 (X5)
# ───────────────────────────────────────────────────────────────────
FACT_RULES = [
    # (规则id, 正则, 说明)
    ('FACT-ALUM-N', r'alum-\d', 'alumni_quotes 占位符未替换'),
    ('FACT-YY', r'[Xx]{2,}', 'XX 占位符未替换'),
    # ⚠️ '待定' 已移除 —— 2026-10-01 实测 9 篇全部误报:
    #    '"其他 (待定/转行)"' 是合法的就业出口写法, 不是 TODO 占位。
    #    真 TODO 用独立的 FACT-TODO-BARE 抓 (见 x5 末尾)。
    ('FACT-XSX', r'据.{0,8}学信网', '学信网/权威数据源占位话术'),
    # ⚠️ '其他方向' 已移除 —— 实测 3 篇全部误报:
    #    '乳品工程薪资比食品其他方向低' / '其他方向 (媒体/政府) 占比小'
    #    都是正常行文, 不是占位符。
    ('FACT-LOREM', r'(lorem ipsum|示例文本|placeholder)', 'Lorem/示例文本'),
    ('FACT-NONE', r'["\'](暂无|无|待定|none|null|N/A)["\']', 'null/暂无 值'),
]

# 医学/农学 等特殊专业的合理例外
FACT_EXEMPT = {
    'FACT-SELF-ENT': {'工商管理', '创业管理', '农村区域发展'},
}

DEGREE_ENUM = {'学士', '硕士', '博士', '副学士', '专科'}
DURATION_SET = {2, 3, 4, 5, 6, 7, 8}


# ───────────────────────────────────────────────────────────────────
# 工具
# ───────────────────────────────────────────────────────────────────

def norm(s):
    """归一化: 去 HTML 标签/空白/全角, 用于内容比对

    ⚠️ 标点必须归一化 —— 渲染器会把半角 ',;:' 转成全角 '，；：',
    不归一化会把"内容完全一致"误判成"未渲染"(2026-10-01 实测踩过)。
    """
    if s is None:
        return ''
    s = unescape(str(s))
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'[\s‌‍﻿]+', '', s)
    # 全角标点 → 半角
    for a, b in (('，', ','), ('。', '.'), ('、', ','), ('；', ';'),
                 ('：', ':'), ('（', '('), ('）', ')'), ('！', '!'),
                 ('？', '?'), ('“', '"'), ('”', '"'), ('‘', "'"),
                 ('’', "'"), ('、', ','), ('…', '...'), ('—', '-'),
                 ('－', '-'), ('／', '/'), ('％', '%')):
        s = s.replace(a, b)
    return s


def load_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception as e:
        return {'__error__': str(e)}


def find_group(discipline, menjia, category):
    """
    判定学科组

    注意: discipline 是 MOE 两位代码 ("05"=文学, "08"=工学), 不是中文名。
    故优先用 menjia_name (中文) 判定, discipline 仅作补充。
    """
    txt = ' '.join(str(x) for x in [menjia, category] if x)
    if not txt:
        txt = str(discipline or '')
        if txt.isdigit():            # 只有 MOE 代码, 退回代码表
            txt = MOE2GROUP.get(txt, '')
    if any(k in txt for k in ['艺术', '体育']):
        return ART
    if any(k in txt for k in ['管理', '经济', '法学', '经管', '商务']):
        return BUS
    if any(k in txt for k in ['理学', '工学', '农学', '医学', '理工']):
        return STEM
    if any(k in txt for k in ['文学', '历史', '哲学', '人文', '社科', '教育', '新闻']):
        return HUM
    if txt.isdigit():
        return MOE2GROUP.get(txt)
    return None


def iter_fields(obj, prefix=''):
    """深度遍历, 产出 (路径, 标量值)"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_fields(v, f'{prefix}.{k}' if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_fields(v, f'{prefix}[{i}]')
    else:
        yield prefix, obj


# ═══════════════════════════════════════════════════════════════════
# X1  DRIFT-JSON-HTML  JSON 值在 HTML 中丢失
# ═══════════════════════════════════════════════════════════════════
def x1_drift(slug, d, pc, mb):
    """
    JSON 值在渲染 HTML 中找不到 (渲染漂移/漏渲)

    关键校准 (2026-10-01 实测):
      - hero_quote: PC 端 5/80 才有, mobile 80/80 → PC 漏渲是设计如此还是 bug?
        归为 WARN (需人工确认渲染器意图), 不报 ERROR
      - employment_direction.desc: PC 0/551, mobile 有 → PC 端确实不渲染 desc
        只查 mobile
      - lede/summary/pitfalls/quote/schools: PC+MB 双端都应渲染
    """
    out = []
    if not pc:
        return out

    def chk(field, val, minlen=4, sev='ERROR', target='PC'):
        """
        探针策略: 不用固定偏移 [10:50] 切片 —— 切片容易跨标点/跨 HTML 实体
        (如 &amp; &quot; 转义后长度变化), 导致完整内容被误判为"未渲染"。
        改为: 优先用整串比对; 整串因转义失败时, 退化为取首尾两段短片段
        (各 12 字, 避开中段转义区), 任一命中即视为已渲染。
        """
        if not isinstance(val, str) or len(val) < minlen:
            return
        html = pc if target == 'PC' else mb
        if not html:
            return
        full = norm(val)
        if len(full) < minlen:
            return
        h = norm(html)
        if full in h:                       # 最优: 整串命中
            return
        # 退化: 首尾片段 (避开 HTML 实体密集的中段)
        head = full[:12]
        tail = full[-12:]
        if head and head in h:
            return
        if tail and tail in h:
            return
        out.append((f'X1/{field}', sev,
                    f'{target} HTML 缺失: …{full[:36]}…'))

    # ── PC 端必渲字段 ──
    # ⚠️ lede 必须查 overview_v2.lede, 不是顶层 d['lede']:
    #    25 篇顶层 lede 是陈旧旧版, HTML 一律渲染 overview_v2.lede
    #    (generate_dashboard.py:114 / overview_simple.py:114 都是 ov.lede 优先)
    #
    # ⚠️ style=medicine 走 v4_medicine.py 独立渲染器, 该渲染器**不渲染**
    #    overview_v2.lede / what_you_learn / pitfalls (41 篇医学类)。
    #    2026-10-01 实测确认: 41 篇 lede 告警 100% 是这类 → 跳过。
    ov = d.get('overview_v2') or {}
    if d.get('style') == 'medicine':
        return out      # 医学类独立渲染器, X1 规则不适用
    chk('lede', ov.get('lede') or d.get('lede'))
    chk('summary', d.get('summary'))

    for i, p in enumerate(ov.get('pitfalls') or []):
        if isinstance(p, dict):
            chk(f'pitfalls[{i}].myth', p.get('myth'), minlen=2)
            chk(f'pitfalls[{i}].reality', p.get('reality'), minlen=6)
    # v2 式: what_you_learn 缺失是正常的, 内容在 what/fit 里由 v2 渲染器处理
    if ov.get('what_you_learn'):
        chk('ov.what_you_learn', ov.get('what_you_learn'))
    for i, q in enumerate(d.get('alumni_quotes') or []):
        if isinstance(q, dict):
            chk(f'quotes[{i}]', q.get('quote'), minlen=6)
    for i, s in enumerate(d.get('top_schools') or []):
        if isinstance(s, dict):
            chk(f'schools[{i}].name', s.get('name'), minlen=2)

    # ── hero_quote: 全库 80/80 在 mobile, PC 仅 5/80 → 归 WARN 待人工判定 ──
    chk('hero_quote', d.get('hero_quote'), minlen=8, sev='WARN')

    # ── employment_direction.desc: PC 端 0/551 → 只查 mobile ──
    for i, e in enumerate(d.get('employment_direction') or []):
        if isinstance(e, dict):
            chk(f'empdir[{i}].desc', e.get('desc'), minlen=6, target='MB')
    return out


# ═══════════════════════════════════════════════════════════════════
# X2  DRIFT-PC-MB  双端数据分叉
# ═══════════════════════════════════════════════════════════════════
def x2_pc_mb(slug, d, pc, mb):
    out = []
    if not pc or not mb:
        return out
    npc, nmb = norm(pc), norm(mb)

    # 2.1 院校名单
    sch = [s.get('name') for s in (d.get('top_schools') or [])
           if isinstance(s, dict) and s.get('name')]
    miss = [s for s in sch if norm(s) not in nmb]
    if miss:
        out.append(('X2/schools-missing-in-MB', 'ERROR',
                    f'{len(miss)}/{len(sch)} 校在 mobile 缺失: {miss[:4]}'))

    # 2.2 就业方向
    # ⚠️ render_mobile.py:831 只渲染 emp_list[:8] (设计上限 8 条),
    #    超过 8 条的方向在 mobile 缺失是预期行为, 只查前 8 条。
    emp_all = [e.get('name') for e in (d.get('employment_direction') or [])
               if isinstance(e, dict) and e.get('name')]
    emp = emp_all[:8]
    miss = [e for e in emp if norm(e) not in nmb]
    if miss:
        out.append(('X2/empdir-missing-in-MB', 'ERROR',
                    f'前 8 个方向中 {len(miss)} 个在 mobile 缺失: {miss[:4]}'))
    if len(emp_all) > 8:
        out.append(('X2/empdir-overflow-8', 'INFO',
                    f'{len(emp_all)} 个方向, mobile 只渲前 8 (超出 {len(emp_all)-8} 个不显示)'))

    # 2.3 薪资数字
    sal = d.get('salary') or {}
    vals = []
    for k, v in sal.items():
        if isinstance(v, dict) and 'p50' in v:
            vals.append(int(v['p50']))
    for p50 in vals[:8]:
        if f'{p50}' not in mb:
            out.append(('X2/salary-p50-missing-in-MB', 'WARN',
                        f'p50={p50}k 未出现在 mobile'))
            break

    # 2.4 校友 quote
    aq = [q.get('quote') for q in (d.get('alumni_quotes') or [])
          if isinstance(q, dict) and q.get('quote')]
    miss = [q for q in aq if norm(q)[:30] not in nmb]
    if miss:
        out.append(('X2/quotes-missing-in-MB', 'WARN',
                    f'{len(miss)}/{len(aq)} 条校友语录 mobile 缺失'))

    # 2.5 lede 双源一致性
    #     顶层 d['lede'] 与 overview_v2.lede 是同一段话的两次存储。
    #     2026-10-01 实测: 25 篇两者不同 —— 顶层是陈旧旧版, HTML 一律用
    #     overview_v2.lede, 所以**不影响渲染**, 但 scripts/build/sync_lede_to_top.py
    #     的同步没覆盖到这批, 属数据一致性问题 (非渲染 bug) → WARN。
    top_lede = d.get('lede')
    ov_lede = (d.get('overview_v2') or {}).get('lede')
    if isinstance(top_lede, str) and isinstance(ov_lede, str) \
            and len(top_lede) > 20 and len(ov_lede) > 20 \
            and norm(top_lede)[:40] != norm(ov_lede)[:40]:
        out.append(('X2/lede-dual-source', 'WARN',
                    f'顶层 lede ≠ overview_v2.lede (顶层为旧版, '
                    f'HTML 用 ov2): 顶层「{top_lede[:22]}…」 vs ov2「{ov_lede[:22]}…」'))
        return out

    # 双端渲染一致性 (顶层与 ov2 一致时才比, 否则无意义)
    # ⚠️ medicine 走 v4_medicine.py 独立渲染器, lede 呈现方式不同 → 跳过
    lede = ov_lede if isinstance(ov_lede, str) and len(ov_lede) > 20 \
        else top_lede
    if d.get('style') != 'medicine' and isinstance(lede, str) and len(lede) > 20:
        p10, m10 = norm(lede)[:30], norm(lede)[:30]
        if (p10 in npc) != (m10 in nmb):
            out.append(('X2/lede-mismatch', 'ERROR', 'lede 双端不一致'))
    return out


# ═══════════════════════════════════════════════════════════════════
# X3  DRIFT-MANIFEST
# ═══════════════════════════════════════════════════════════════════
def x3_manifest(d, mrow):
    out = []
    if not mrow:
        return [('X3/missing-in-manifest', 'ERROR', 'manifest 无此 slug')]
    t = d.get('title')
    if t and mrow.get('title') and norm(t) != norm(mrow['title']):
        out.append(('X3/title-mismatch', 'ERROR',
                    f'manifest={mrow["title"]!r} vs json={t!r}'))
    for f in ('discipline', 'category', 'degree', 'menjia_name'):
        a, b = d.get(f), mrow.get(f)
        if a and b and norm(a) != norm(b):
            out.append((f'X3/{f}-mismatch', 'WARN',
                        f'manifest={b!r} vs json={a!r}'))
    # 学科门类自洽
    if d.get('menjia_name') and d.get('discipline'):
        mn, dc = str(d['menjia_name']), str(d['discipline'])
        if mn == '管理学' and '经济' in dc:
            out.append(('X3/menjia-discipline', 'WARN',
                        f'menjia=管理学 但 discipline={dc}'))
    return out


# ═══════════════════════════════════════════════════════════════════
# X4  CROSS-TALK  学科串台
# ═══════════════════════════════════════════════════════════════════
def x4_crosstalk(slug, d, group):
    """
    学科串台检测

    严格对齐 AGENTS.md anti-pollution 铁律 2:
      "who_fits_no 串台 ❌ 理工科出现'文本阅读/田野调研/历史/语文' → 删;
                人文社科出现'数学/统计/经济/考证' → 删"

    关键校准 (2026-10-01): 初版把整个 blob (lede+pitfalls+curriculum...) 都拿去
    比对, 导致 050104 中国少数民族语言文学 因 lede 正常提到"文学史/田野调查"
    被误报 47 篇。串台只应发生在 who_fits_no (劝退人群描述) 字段 —— 那里
    出现他科词汇才是"劝退理由串台"。正文提到本学科术语是正确的。
    """
    out = []
    if group is None:
        return out
    ov = d.get('overview_v2') or {}

    # ── 4.1 串台: 只查 who_fits_no (AGENTS.md 铁律 2 的原文定义) ──
    wfn = ' '.join(str(x) for x in (ov.get('who_fits_no') or []))
    forbid = {
        STEM: HUM_ONLY_FORBIDDEN + BUS_ONLY_FORBIDDEN + ART_ONLY_FORBIDDEN,
        HUM: ENG_ONLY_FORBIDDEN + BUS_ONLY_FORBIDDEN + ART_ONLY_FORBIDDEN,
        BUS: ENG_ONLY_FORBIDDEN + HUM_ONLY_FORBIDDEN + ART_ONLY_FORBIDDEN,
        ART: ENG_ONLY_FORBIDDEN + HUM_ONLY_FORBIDDEN + BUS_ONLY_FORBIDDEN,
    }.get(group, [])

    hits = sorted({w for w in forbid if w in wfn})
    if hits:
        out.append((f'X4/crosstalk-{group}', 'ERROR',
                    f'who_fits_no 出现他科专属词: {hits[:5]}'))

    # ── 4.2 模板套话 (lede 层, 全 blob) ──
    blob = ' '.join(str(x) for x in [
        d.get('lede'), d.get('summary'), d.get('hero_quote'),
        ov.get('what_you_learn'), d.get('data_source'),
    ])
    tmpl = [p for p in TEMPLATE_BOILERPLAT if re.search(p, blob)]
    if tmpl:
        out.append(('X4/template-boilerplate', 'WARN',
                    f'命中 {len(tmpl)} 条模板套话: {tmpl[:3]}'))

    # ── 4.3 领域词汇缺失 = 内容泛化 (WARN) ──
    if group in (STEM, HUM, BUS):
        sig = GROUP_SIGNALS[group]
        full = ' '.join(str(x) for x in [
            d.get('lede'), d.get('summary'), ov.get('what_you_learn'),
            str(d.get('curriculum') or ''), str(d.get('pitfalls') or ''),
            str(ov.get('pitfalls') or ''), str(d.get('employment_direction') or ''),
        ])
        if not any(w in full for w in sig) and len(full) > 200:
            out.append((f'X4/no-domain-vocab-{group}', 'WARN',
                        f'{group} 内容 0 个专业信号词 (内容泛化)'))
    return out


# ═══════════════════════════════════════════════════════════════════
# X5  FACT-HARD
# ═══════════════════════════════════════════════════════════════════
def x5_fact(slug, d, group):
    out = []
    blob = json.dumps(d, ensure_ascii=False)
    title = str(d.get('title') or '')

    for rid, pat, desc in FACT_RULES:
        if rid in FACT_EXEMPT and title in FACT_EXEMPT[rid]:
            continue
        m = re.search(pat, blob)
        if m:
            seg = blob[max(0, m.start() - 40):m.end() + 40]
            out.append((rid, 'ERROR', f'{desc} → …{seg}…'))

    # 5.x 学位合法
    deg = d.get('degree')
    if deg and str(deg) not in DEGREE_ENUM and '学士' not in str(deg):
        out.append(('FACT-DEGREE', 'WARN', f'degree={deg!r} 不在枚举 {DEGREE_ENUM}'))

    # 5.x 学制 vs 学位矛盾
    dur, deg = d.get('duration_years'), str(d.get('degree') or '')
    if isinstance(dur, int) and dur not in DURATION_SET:
        out.append(('FACT-DURATION', 'WARN', f'duration_years={dur} 异常'))

    # 5.x 医学 5/8 年制 vs 学士
    if any(k in title for k in ['临床医学', '口腔医学', '麻醉学']) and dur == 4:
        out.append(('FACT-MED-DURATION', 'WARN', '医学类标 4 年制'))

    # 5.x 门类 vs 学科不一致
    # 注意: discipline 是 MOE 两位代码 (如 "05"=文学), 不是中文名, 不能直接做子串匹配
    men, dc = str(d.get('menjia_name') or ''), str(d.get('menjia_name_moe') or '')
    if not dc:
        dc = str(d.get('menjia_moe') or '')
    if men and dc:
        m2d = {'理学': '05', '工学': '08', '农学': '04', '医学': '10',
               '管理学': '12', '艺术学': '13', '文学': '05', '历史学': '06',
               '哲学': '01', '法学': '06', '经济学': '02', '教育学': '14',
               '理学门类': '05', '工学门类': '08'}
        # 文学/历史学/法学 共享部分 MOE 代码, 放宽为"同组"检查
        SAME = [{'文学', '历史学', '法学'}, {'理学', '工学', '农学', '医学',
                '管理学', '艺术学'}]
        exp = m2d.get(men)
        if exp and dc and dc != exp:
            ok_group = any(men in g and (m2d.get(x) == dc) for g in SAME
                           for x in g if x in m2d)
            if not ok_group:
                out.append(('FACT-MENJIA-MOE', 'WARN',
                            f'menjia_name={men} 但 menjia_moe={dc} (期望 {exp})'))

    # 5.x 光杆占位检测 (2026-10-01 实测校准)
    #   '自主创业 (家庭农场/合作社)'  = 真实就业出口 → 不报
    #   '自主创业' 光杆 (无括号/无 dest) = Day 47 坑 7 的 C session 占位 → 报
    for e in (d.get('employment_direction') or []):
        if not isinstance(e, dict):
            continue
        nm = str(e.get('name') or '')
        if re.fullmatch(r'自主创业(/?其他)?', nm.strip()) and not e.get('dest'):
            out.append(('FACT-SELF-ENT-BARE', 'ERROR',
                        f'就业方向光杆占位: name={nm!r} 无 dest/desc'))
    for path, val in iter_fields(d):
        if isinstance(val, str) and val.strip() in ('其他', '其它', '其他方向'):
            out.append(('FACT-BARE-OTHER', 'WARN',
                        f'{path} = {val!r} 光杆"其他"占位'))
        # 真 TODO: 裸 TODO/FIXME/待补充 作为独立值或标记出现
        if isinstance(val, str) and re.search(
                r'\b(TODO|FIXME|XXX)\b|待补充', val):
            out.append(('FACT-TODO-BARE', 'ERROR',
                        f'{path} 含未清理 TODO/待补充: {val[:60]!r}'))
    return out


# ═══════════════════════════════════════════════════════════════════
# X6  NUM-CONTRA  数值矛盾
# ═══════════════════════════════════════════════════════════════════
def x6_num(slug, d):
    out = []

    # 6.1 employment pct 合计
    emp = d.get('employment_direction') or []
    if emp:
        s = sum(e.get('pct', 0) for e in emp if isinstance(e, dict)
                and isinstance(e.get('pct'), (int, float)))
        if not (95 <= s <= 105):
            out.append(('X6/emp-pct-sum', 'ERROR', f'pct 合计={s} (应≈100)'))
        if len(emp) > 12:
            out.append(('X6/emp-count', 'WARN', f'就业方向 {len(emp)} 条过多'))

    # 6.2 xuanke pct
    xk = d.get('xuanke_req_list') or []
    if xk:
        s = sum(x.get('pct', 0) for x in xk if isinstance(x, dict)
                and isinstance(x.get('pct'), (int, float)))
        if not (90 <= s <= 110):
            out.append(('X6/xuanke-pct-sum', 'WARN', f'xuanke pct 合计={s}'))

    # 6.3 deep_study 合计
    ds = d.get('deep_study') or {}
    if ds and isinstance(ds, dict):
        vals = [v for v in ds.values() if isinstance(v, (int, float))]
        s = sum(vals)
        if vals and not (95 <= s <= 105):
            out.append(('X6/deepstudy-pct-sum', 'WARN', f'deep_study 合计={s}'))
        if any(v < 0 for v in vals):
            out.append(('X6/deepstudy-negative', 'ERROR', 'deep_study 有负值'))

    # 6.4 curriculum credit — 只报"字符串型异常值"
    # 注: credit=0 占全库 60% (8991/14969), 是普遍未填, 不是 bug, 不报
    cur = d.get('curriculum') or {}
    if isinstance(cur, dict):
        n_zero, n_tot = 0, 0
        for grp, items in cur.items():
            if not isinstance(items, list):
                continue
            for it in items:
                if not isinstance(it, dict):
                    continue
                c = it.get('credit')
                n_tot += 1
                if c == 0:
                    n_zero += 1
                if isinstance(c, str) and not re.match(r'^(\d+(\.\d+)?|\d+-\d+)$', c):
                    out.append(('X6/credit-format', 'WARN',
                                f'{grp}/{it.get("name")} credit={c!r} 格式异常'))
        if n_tot and n_zero == n_tot:
            out.append(('X6/credit-all-zero', 'WARN',
                        f'全 {n_tot} 门课 credit=0 (学分普遍未填)'))

    # 6.5 salary 量级
    sal = d.get('salary') or {}
    for k, v in sal.items():
        if not isinstance(v, dict):
            continue
        for f in ('p25', 'p50', 'p75'):
            x = v.get(f)
            if isinstance(x, (int, float)):
                if not (3 <= x <= 200):
                    out.append(('X6/salary-range', 'WARN',
                                f'salary/{k}/{f}={x}k 量级异常'))
        yoy = v.get('yoy')
        if isinstance(yoy, (int, float)) and not (-50 <= yoy <= 100):
            out.append(('X6/yoy-range', 'WARN',
                        f'salary/{k}/yoy={yoy}% 异常'))

    # 6.6 top_schools rank 格式
    for s_ in (d.get('top_schools') or []):
        if isinstance(s_, dict):
            rk = str(s_.get('rank') or '')
            m = re.search(r'(\d+)', rk)
            if m and not (1 <= int(m.group(1)) <= 100):
                out.append(('X6/rank-range', 'WARN',
                            f'院校 {s_.get("name")} rank={rk}'))

    # 6.7 alumni year
    for q in (d.get('alumni_quotes') or []):
        if isinstance(q, dict):
            y = re.search(r'(19|20)\d{2}', str(q.get('year') or ''))
            if y and not (2005 <= int(y.group(0)) <= 2026):
                out.append(('X6/alumni-year', 'WARN',
                            f'校友 year={q.get("year")} 越界'))
    return out


# ═══════════════════════════════════════════════════════════════════
# X7  PLACEHOLDER
# ═══════════════════════════════════════════════════════════════════
def x7_placeholder(slug, pc, mb):
    out = []
    for name, html in (('PC', pc), ('MB', mb)):
        if not html:
            continue
        for pat, desc in [(r'\{\{[^}]+\}\}', '{{模板变量}} 未替换'),
                          (r'\{%[^%]+\}%', '{% jinja %} 未替换'),
                          (r'\$\{[^}]+\}', '${变量} 未替换'),
                          (r'alum-\d', 'alum-N 占位'),
                          (r'undefined|NaN|\[object Object\]',
                           'JS 渲染残留 undefined/NaN'),
                          (r'\bNone\b', 'Python None 泄漏')]:
            ms = re.findall(pat, html)
            if ms:
                uniq = list(dict.fromkeys(ms))[:3]
                out.append((f'X7/{name}-placeholder', 'ERROR',
                            f'{desc}: {uniq}'))
        # HTML 注释里的 TODO
        if re.search(r'<!--[^>]*(TODO|FIXME|待补充|DEBUG)', html):
            out.append((f'X7/{name}-comment', 'WARN', 'HTML 注释含 TODO/DEBUG'))
    return out


# ═══════════════════════════════════════════════════════════════════
# X8  DUP-CONTENT  跨专业雷同
# ═══════════════════════════════════════════════════════════════════
def build_dup_index(files):
    """建 lede / what_you_learn / hero_quote 的指纹索引"""
    idx = defaultdict(list)
    for f in files:
        slug = Path(f).stem
        d = load_json(f)
        if '__error__' in d:
            continue
        ov = d.get('overview_v2') or {}
        for field, val in (('lede', d.get('lede')),
                           ('what_you_learn', ov.get('what_you_learn')),
                           ('hero_quote', d.get('hero_quote'))):
            if not isinstance(val, str) or len(val) < 25:
                continue
            idx[(field, norm(val))].append(slug)
    return idx


def x8_dup(slug, d, idx):
    out = []
    ov = d.get('overview_v2') or {}
    for field, val in (('lede', d.get('lede')),
                       ('what_you_learn', ov.get('what_you_learn')),
                       ('hero_quote', d.get('hero_quote'))):
        if not isinstance(val, str) or len(val) < 25:
            continue
        peers = idx.get((field, norm(val)), [])
        if len(peers) > 1 and slug in peers:
            out.append((f'X8/dup-{field}', 'ERROR',
                        f'{field} 与 {len(peers)-1} 篇完全相同: {peers[:4]}'))
    return out


# ═══════════════════════════════════════════════════════════════════
# X9  SCHEMA-DRIFT
# ═══════════════════════════════════════════════════════════════════
REQUIRED = ['title', 'slug', 'style', 'category', 'degree', 'duration_years',
            'tags', 'difficulty', 'summary', 'hero_quote', 'hero_quote_sig',
            'lede', 'curriculum', 'top_schools', 'salary',
            'employment_direction', 'alumni_quotes', 'xuanke_req_list',
            'deep_study', 'discipline', 'sub_discipline', 'menjia_moe',
            'menjia_name', 'theme_color', 'overview_v2', 'data_source']

# style 实际取值 (2026-10-01 实测 627 篇全量统计)
STYLE_ENUM = {'cs', 'eng', 'sci', 'medicine', 'agri', 'arts', 'humanities',
              'administration', 'law', 'finance', 'education', 'gongan',
              'business'}


def x9_schema(slug, d):
    out = []
    if '__error__' in d:
        return [('X9/parse', 'ERROR', f'JSON 解析失败: {d["__error__"]}')]

    for f in REQUIRED:
        if f not in d or d[f] in (None, '', [], {}):
            out.append((f'X9/missing-{f}', 'ERROR', f'缺必填字段 {f}'))

    if d.get('slug') and d['slug'] != slug:
        out.append(('X9/slug-mismatch', 'ERROR',
                    f'文件名={slug} vs json.slug={d["slug"]}'))

    if d.get('style') and d['style'] not in STYLE_ENUM:
        out.append(('X9/style-enum', 'WARN', f'style={d["style"]!r} 非枚举'))

    # overview_v2 子字段
    # ⚠️ 存在两种合法 schema (2026-10-01 实测):
    #   simple 式: lede / what_you_learn / who_fits_yes / who_fits_no / pitfalls
    #   v2 式:     lede / what(foundations+skills+bonus) / fit / who_fits /
    #              who_fits_no / pitfalls
    #   判据: overview_simple.py:170 —— 有 what_you_learn 或 who_fits_yes 是 list
    #   → simple; 否则走 v2 渲染。两种都合法, 只查"两套都没有"。
    ov = d.get('overview_v2') or {}
    if 'lede' not in ov:
        out.append(('X9/missing-overview_v2.lede', 'ERROR', 'overview_v2 缺 lede'))
    is_simple = bool(ov.get('what_you_learn')) or \
        isinstance(ov.get('who_fits_yes'), list)
    if is_simple:
        if not ov.get('what_you_learn'):
            out.append(('X9/missing-overview_v2.what_you_learn', 'ERROR',
                        'simple 式 overview_v2 缺 what_you_learn'))
        if not isinstance(ov.get('who_fits_yes'), list) or \
                not ov.get('who_fits_yes'):
            out.append(('X9/missing-overview_v2.who_fits_yes', 'ERROR',
                        'simple 式 overview_v2 缺 who_fits_yes'))
    else:
        # v2 式: what / fit / who_fits 至少要有 what 或 fit
        if not (ov.get('what') or ov.get('fit')):
            out.append(('X9/missing-overview_v2.what/fit', 'ERROR',
                        'v2 式 overview_v2 缺 what 且缺 fit'))
    if not ov.get('who_fits_no') and is_simple:
        # simple 式: renderer (overview_simple.py:117) 直接读 who_fits_no,
        # 缺了就是真的渲染不出"不适合"列 → ERROR
        out.append(('X9/missing-overview_v2.who_fits_no', 'ERROR',
                    'simple 式 overview_v2 缺 who_fits_no (PC/MB 会空白)'))
    if not ov.get('pitfalls'):
        out.append(('X9/missing-overview_v2.pitfalls', 'ERROR',
                    'overview_v2 缺 pitfalls'))
    if len(ov.get('who_fits_no') or []) < 3:
        out.append(('X9/who_fits_no-thin', 'WARN',
                    f'who_fits_no 仅 {len(ov.get("who_fits_no") or [])} 条'))
    if len(ov.get('pitfalls') or []) < 3:
        out.append(('X9/pitfalls-thin', 'WARN',
                    f'pitfalls 仅 {len(ov.get("pitfalls") or [])} 条'))
    for i, p in enumerate(ov.get('pitfalls') or []):
        if not isinstance(p, dict) or not p.get('myth') or not p.get('reality'):
            out.append((f'X9/pitfall-shape[{i}]', 'ERROR',
                        f'pitfall[{i}] 缺 myth/reality'))

    # 数量下限
    for f, lo in (('top_schools', 5), ('alumni_quotes', 3),
                  ('employment_direction', 3), ('xuanke_req_list', 2)):
        n = len(d.get(f) or [])
        if n < lo:
            out.append((f'X9/thin-{f}', 'WARN', f'{f} 仅 {n} 条 (建议≥{lo})'))

    # 类型
    if not isinstance(d.get('tags'), list):
        out.append(('X9/tags-type', 'WARN', 'tags 非 list'))
    if not isinstance(d.get('duration_years'), (int, float)):
        out.append(('X9/duration-type', 'WARN', 'duration_years 非数值'))
    return out


# ═══════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════
def check_one(slug, mrow, idx, cats):
    d = load_json(CURATED / f'{slug}.json')
    pc_p = PUBLIC / f'{slug}.html'
    mb_p = PUBLIC_MB / f'{slug}.html'
    pc = pc_p.read_text(encoding='utf-8', errors='ignore') if pc_p.exists() else ''
    mb = mb_p.read_text(encoding='utf-8', errors='ignore') if mb_p.exists() else ''

    group = find_group(d.get('discipline'), d.get('menjia_name'),
                       d.get('category'))

    res = []
    if 'X1' in cats:
        res += x1_drift(slug, d, pc, mb)
    if 'X2' in cats:
        res += x2_pc_mb(slug, d, pc, mb)
    if 'X3' in cats:
        res += x3_manifest(d, mrow)
    if 'X4' in cats:
        res += x4_crosstalk(slug, d, group)
    if 'X5' in cats:
        res += x5_fact(slug, d, group)
    if 'X6' in cats:
        res += x6_num(slug, d)
    if 'X7' in cats:
        res += x7_placeholder(slug, pc, mb)
    if 'X8' in cats:
        res += x8_dup(slug, d, idx)
    if 'X9' in cats:
        res += x9_schema(slug, d)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', help='单篇')
    ap.add_argument('--cat', nargs='*', default=None,
                    help='只要某几类, 如 --cat X1 X4')
    ap.add_argument('--severity', choices=['ERROR', 'WARN'], default='ERROR',
                    help='最低严重度')
    ap.add_argument('--staged', action='store_true',
                    help='只查 git staged 的 curated/*.json (pre-commit 用)')
    ap.add_argument('--json-out', help='输出 JSON 路径')
    args = ap.parse_args()

    cats = set(args.cat) if args.cat else {
        f'X{i}' for i in range(1, 10)}

    manifest = {}
    if MANIFEST.exists():
        mm = load_json(MANIFEST)
        items = mm if isinstance(mm, list) else mm.get('majors', [])
        for it in items:
            if isinstance(it, dict) and it.get('slug'):
                manifest[it['slug']] = it

    # curated/manifest.json 是目录索引, TEMPLATE.json 是 schema 模板
    # (带 _comment, 不在 manifest, 不对应任何线上页面) —— 都不是专业, 排除
    SKIP = {'manifest.json', 'TEMPLATE.json'}
    files = sorted(f for f in CURATED.glob('*.json')
                    if f.name not in SKIP)
    if args.slug:
        files = [f for f in files if f.stem == args.slug]
    if args.staged:
        import subprocess as _sp
        try:
            out = _sp.run(
                ['git', 'diff', '--cached', '--name-only',
                 '--diff-filter=ACMR'],
                capture_output=True, text=True, cwd=str(ROOT),
                timeout=30).stdout
            staged = {ln.strip() for ln in out.splitlines()
                      if ln.strip().endswith('.json')}
            files = [f for f in files
                     if str(f.relative_to(ROOT)) in staged
                     or f.name in {Path(s).name for s in staged}]
        except Exception as e:
            print(f'⚠️  --staged 读取失败 ({e}), 回退全量', file=sys.stderr)
    if not files:
        print('❌ 无文件', file=sys.stderr)
        return 1

    idx = build_dup_index(sorted(f for f in CURATED.glob('*.json')
                                 if f.name not in SKIP))

    all_res = defaultdict(list)
    sev_count = Counter()
    rule_count = Counter()
    rule_sev = Counter()
    affected = defaultdict(set)

    t0 = datetime.datetime.now()
    for i, f in enumerate(files):
        slug = f.stem
        for rid, sev, msg in check_one(slug, manifest.get(slug), idx, cats):
            rule_count[rid] += 1
            rule_sev[(rid, sev)] += 1
            affected[rid].add(slug)
            if sev == 'WARN' and args.severity == 'ERROR':
                continue          # 过滤输出, 但保留统计
            all_res[slug].append((rid, sev, msg))
            sev_count[sev] += 1
        if (i + 1) % 150 == 0:
            print(f'  ... {i+1}/{len(files)}', flush=True)

    dur = (datetime.datetime.now() - t0).total_seconds()

    print()
    print('═' * 74)
    print(f'  adversarial_check — 扫 {len(files)} 篇, {dur:.1f}s, 0¥')
    print('═' * 74)
    print(f"  ERROR: {sev_count['ERROR']}   WARN: {sev_count['WARN']}")
    print(f"  受影响专业: {len(all_res)} / {len(files)} "
          f"({len(all_res)/max(1,len(files))*100:.1f}%)")
    print()
    print('  ── 规则命中 (按严重度, 仅显示 --severity 过滤后的) ──')
    shown = Counter()
    shown_sev = {}
    for slug, items in all_res.items():
        for rid, sev, _ in items:
            shown[rid] += 1
            shown_sev[rid] = sev
    for rid, c in shown.most_common(45):
        print(f'   {c:5d}  [{shown_sev[rid]:<5}] {rid:<36} {len(affected[rid])} 篇')
    print()

    if args.slug or args.cat:
        for slug, items in sorted(all_res.items()):
            print(f'  ▶ {slug}')
            for rid, sev, msg in items:
                print(f'      [{sev}] {rid}: {msg}')
    else:
        print('  ── 各篇明细 (前 60 篇, 按 ERROR 数排序) ──')
        ranked = sorted(all_res.items(),
                        key=lambda kv: -sum(1 for x in kv[1] if x[1] == 'ERROR'))
        for slug, items in ranked[:60]:
            ne = sum(1 for x in items if x[1] == 'ERROR')
            nw = len(items) - ne
            print(f'  ▶ {slug}  (E{ne}/W{nw})')
            for rid, sev, msg in items[:8]:
                print(f'      [{sev}] {rid}: {msg}')
            if len(items) > 8:
                print(f'      ... 另 {len(items)-8} 条')

    if args.json_out:
        out = {s: [{'rule': r, 'severity': v, 'msg': m} for r, v, m in items]
               for s, items in all_res.items()}
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                     encoding='utf-8')
        print(f'\n  📄 → {p}')

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    tr = TEST_RESULTS / f'adversarial_check_{ts}.json'
    tr.parent.mkdir(parents=True, exist_ok=True)
    tr.write_text(json.dumps({
        'ts': ts, 'scanned': len(files),
        'errors': sev_count['ERROR'], 'warnings': sev_count['WARN'],
        'affected': len(all_res),
        'rules': {k: v for k, v in rule_count.items()},
        'detail': {s: [{'rule': r, 'severity': v, 'msg': m}
                       for r, v, m in items] for s, items in all_res.items()},
    }, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'  📄 → {tr}')

    return 1 if sev_count['ERROR'] else 0


if __name__ == '__main__':
    sys.exit(main())
