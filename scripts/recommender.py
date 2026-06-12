#!/usr/bin/env python3
"""湖北高考志愿推荐引擎 MVP"""
import json
from pathlib import Path
from collections import defaultdict
from statistics import median

ROOT = Path('/Users/zhewenliu/Claude/gaokao-hubei-mvp')
DATA = ROOT / 'data'


def load_data():
    colleges = {c['school_id']: c for c in json.load(open(DATA / 'colleges.json'))}
    school_history = json.load(open(DATA / 'school_history.json'))
    groups_latest = json.load(open(DATA / 'groups_latest.json'))
    province_lines = json.load(open(DATA / 'province_lines.json'))
    specialties = json.load(open(DATA / 'school_specialties.json'))
    yfyd = json.load(open(DATA / 'yfyd_2025.json'))
    return colleges, school_history, groups_latest, province_lines, specialties, yfyd


def score_to_rank(score, ttype, yfyd):
    """分数→位次 (用一分一段表反查)"""
    bucket = 'wuli' if ttype == '物理类' else 'lishi'
    rows = yfyd[bucket]['rows']
    for r in rows:
        if r['score'] <= score:
            return r['rank']
    return rows[-1]['rank']


def rank_to_score(rank, ttype, yfyd):
    """位次→分数"""
    bucket = 'wuli' if ttype == '物理类' else 'lishi'
    rows = yfyd[bucket]['rows']
    for r in rows:
        if r['rank'] >= rank:
            return r['score']
    return rows[-1]['score']


# 1. 选科硬过滤
def passes_xuanke(sg_info, user_xuanke_set, user_type):
    if not sg_info: return False
    first = '物理' if user_type == '物理类' else '历史'
    if f'首选{first}' not in sg_info: return False
    tail = sg_info.split('再选', 1)[-1] if '再选' in sg_info else ''
    if not tail or '不限' in tail: return True
    tail = tail.strip().rstrip('。.')
    if '和' in tail:
        reqs = [s.strip() for s in tail.split('和')]
        return all(r in user_xuanke_set for r in reqs if r)
    if '或' in tail:
        alts = [s.strip() for s in tail.split('或')]
        return any(a in user_xuanke_set for a in alts)
    return tail in user_xuanke_set


# 2. 位次法 — 冲稳保
def compute_chance(user_rank, school_median_rank):
    if not school_median_rank or school_median_rank <= 0:
        return None, None
    diff = (user_rank - school_median_rank) / school_median_rank
    if diff >= 0.30:   return '冲', 0.20
    elif diff >= 0.10: return '冲', 0.35
    elif diff >= -0.05: return '稳', 0.60
    elif diff >= -0.20: return '稳', 0.75
    elif diff >= -0.40: return '保', 0.88
    else: return '保', 0.95


# 3. 偏好融合评分
WEIGHTS = {'院校优先': (0.3, 0.2, 0.5), '专业优先': (0.6, 0.2, 0.2), '均衡': (0.4, 0.3, 0.3)}
TIER_SCORE = {'C9': 5.0, '985': 4.5, '211': 4.0, '双一流': 3.5, '公办本科': 2.5, '民办/独立': 1.5}


def major_match(school_id, interests, specialties):
    """v2: 用真实院校 top 10 主打专业匹配心愿专业 (+ 学科评估加权)"""
    if not interests or not specialties: return 0
    sp_data = specialties.get(str(school_id))
    if not sp_data: return 0
    top_specs = sp_data.get('top_specials', [])
    if not top_specs: return 0

    best = 0
    for spec in top_specs:
        sname = spec.get('name', '')
        for it in interests:
            kw = it['major']
            # 双向包含匹配: 心愿"计算机" ⊂ "计算机科学与技术" 或反之
            if kw in sname or sname in kw or sname[:2] == kw[:2]:
                # 学科评估加分: A+/A → bonus
                bonus = 0
                rk = spec.get('xueke_rank_score', '') or spec.get('ruanke_level', '')
                if rk.startswith('A+'): bonus = 0.5
                elif rk.startswith('A'): bonus = 0.3
                elif rk.startswith('B'): bonus = 0.1
                score = min(5.0, it['score'] + bonus)
                best = max(best, score)
                break  # 一个心愿专业只算一次
    return best


def city_match(school_city, cities):
    if not cities or not school_city: return 0
    for c in cities:
        if c['city'] in school_city or school_city in c['city']:
            return c['score']
    return 0


def compute_score(user, college, groups, specialties):
    a, b, g = WEIGHTS.get(user['mode'], WEIGHTS['均衡'])
    m_s = major_match(college['school_id'], user.get('interests', []), specialties)
    c_s = city_match(college.get('city',''), user.get('cities', []))
    t_s = TIER_SCORE.get(college.get('tier', '民办/独立'), 1.5)
    return {'total': round(a*m_s + b*c_s + g*t_s, 2),
            'major': m_s, 'city': c_s, 'tier': t_s,
            'weights': (a, b, g)}


# 4. 主推荐流程
def recommend(user, colleges, school_history, groups_latest, province_lines, specialties, yfyd,
              top_chong=6, top_wen=10, top_bao=4):
    # 如果用户只给了分数没给位次, 用 OCR 反查
    if user.get('rank') is None and user.get('score') is not None:
        user['rank'] = score_to_rank(user['score'], user['type'], yfyd)
        print(f"[autocompute] score {user['score']} → rank {user['rank']}")
    user_xuanke_set = set(user['xuanke'])
    bucket = 'wuli' if user['type'] == '物理类' else 'lishi'
    by_school = defaultdict(list)
    for g in groups_latest[bucket]:
        by_school[g['school_id']].append(g)

    candidates = []
    for sid, school_groups in by_school.items():
        college = colleges.get(sid)
        if not college: continue
        history = school_history.get(str(sid), {}).get(user['type'], {})
        if not history: continue
        recent_medians = [h['median_rank'] for yr, h in history.items()
                          if int(yr) >= 2023 and h.get('median_rank')]
        if len(recent_medians) < 2: continue
        med_3y = median(recent_medians)
        passing = [g for g in school_groups
                   if passes_xuanke(g.get('sg_info'), user_xuanke_set, user['type'])]
        if not passing: continue
        cat, prob = compute_chance(user['rank'], med_3y)
        if not cat: continue
        score_info = compute_score(user, college, passing, specialties)
        # 用户位次附近 (±30%) 的专业组优先展示
        rank_targets = [pg for pg in passing
                        if pg.get('min_rank') and
                        abs((user['rank']-pg['min_rank'])/pg['min_rank']) < 0.30]
        rank_targets.sort(key=lambda x: abs(user['rank']-(x.get('min_rank') or 0)))
        if not rank_targets:
            rank_targets = sorted(passing, key=lambda x: -(x.get('min_score') or 0))
        # 该校 top 主打专业 (含学科评估)
        sp_data = specialties.get(str(sid), {})
        top_majors = [{'name': s['name'],
                       'xueke': s.get('xueke_rank_score',''),
                       'ruanke': s.get('ruanke_level','')}
                      for s in sp_data.get('top_specials', [])[:5]]
        candidates.append({
            'school_id': sid,
            'school_name': college['name'],
            'city': college.get('city',''),
            'tier': college.get('tier',''),
            'type': college.get('type',''),
            'nature': college.get('nature',''),
            'category': cat,
            'prob': prob,
            'median_rank_3y': med_3y,
            'history_brief': {yr: h.get('median_rank') for yr, h in history.items()},
            'score': score_info['total'],
            'score_breakdown': score_info,
            'top_groups': [
                {
                    'sg_name': g['sg_name'],
                    'sg_info': g['sg_info'],
                    'min_score_2025': g.get('min_score'),
                    'min_rank_2025': g.get('min_rank'),
                }
                for g in rank_targets[:3]
            ],
            'top_majors': top_majors,
        })

    # 分桶 + 桶内按 score 降序
    buckets = {'冲': [], '稳': [], '保': []}
    for c in candidates:
        buckets[c['category']].append(c)
    for k in buckets:
        buckets[k].sort(key=lambda x: -x['score'])

    return {
        '冲': buckets['冲'][:top_chong],
        '稳': buckets['稳'][:top_wen],
        '保': buckets['保'][:top_bao],
        'stats': {
            'total_candidates': len(candidates),
            'chong_pool': len(buckets['冲']),
            'wen_pool':   len(buckets['稳']),
            'bao_pool':   len(buckets['保']),
        }
    }


# 5. Demo 用例 + main
DEMO_USER = {
    'rank': 6300,
    'score': 580,
    'type': '物理类',
    'xuanke': ['物理', '化学', '生物'],
    'interests': [
        {'major': '计算机', 'score': 5},
        {'major': '人工智能', 'score': 4},
        {'major': '软件', 'score': 3},
        {'major': '电子', 'score': 3},
    ],
    'cities': [
        {'city': '武汉', 'score': 5},
        {'city': '上海', 'score': 4},
        {'city': '北京', 'score': 3},
    ],
    'mode': '均衡',
}


def print_card(c, idx):
    h = c['history_brief']
    h_str = '  '.join(f"{yr}:{r}" for yr, r in sorted(h.items()))
    bd = c['score_breakdown']
    print(f"  [{idx:2d}] {c['school_name']:18} {c['tier']:8} {c['city']:8} "
          f"P={c['prob']*100:.0f}%  3年中位={c['median_rank_3y']:>6.0f}  "
          f"score={c['score']:.1f}  [major={bd['major']:.1f} city={bd['city']:.0f} tier={bd['tier']:.1f}]")
    print(f"       4年位次: {h_str}")
    if c.get('top_majors'):
        majors_str = ' / '.join(
            f"{m['name']}({m['xueke'] or m['ruanke'] or '-'})" for m in c['top_majors'][:5])
        print(f"       主打: {majors_str}")
    for g in c['top_groups']:
        info = g['sg_info'] or ''
        print(f"       └ {g['sg_name']} {info[:30]}: 2025 min={g['min_score_2025']} 位次={g['min_rank_2025']}")


def main():
    colleges, school_history, groups_latest, province_lines, specialties, yfyd = load_data()
    print(f'=== USER ===')
    print(f"  位次: {DEMO_USER['rank']}  分数: {DEMO_USER['score']}  类别: {DEMO_USER['type']}")
    print(f"  选科: {DEMO_USER['xuanke']}")
    print(f"  心愿: {[i['major'] for i in DEMO_USER['interests']]}")
    print(f"  城市: {[c['city'] for c in DEMO_USER['cities']]}")
    print(f"  模式: {DEMO_USER['mode']}")
    print()

    result = recommend(DEMO_USER, colleges, school_history, groups_latest,
                       province_lines, specialties, yfyd)
    print(f"=== STATS ===")
    print(f"  {result['stats']}")
    print()
    print(f"=== 冲 (Top {len(result['冲'])}) ===")
    for i, c in enumerate(result['冲'], 1):
        print_card(c, i)
    print()
    print(f"=== 稳 (Top {len(result['稳'])}) ===")
    for i, c in enumerate(result['稳'], 1):
        print_card(c, i)
    print()
    print(f"=== 保 (Top {len(result['保'])}) ===")
    for i, c in enumerate(result['保'], 1):
        print_card(c, i)


if __name__ == '__main__':
    main()