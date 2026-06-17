#!/usr/bin/env python3
"""Schema cleanup for batch 30 (and any prior batch leftover).

清理 2 类问题 (按 user feedback 2026-06-17):
1. "自主创业/其他" 占位 → 拆细为具体路径
2. salary string → p25/p50/p75/yoy 对象

Usage:
  python3 scripts/batches/cleanup_batch30.py [--dry-run] [--batch 30]
"""
import json
import re
from pathlib import Path
import argparse

CURATED = Path('skills/gaokao-major-explorer/data/curated')

# 自主创业占位 → 具体路径映射 (per major)
ENTREPRENEUR_MAP = {
    # Batch 30
    'spanish': '跨境电商/西语培训/拉美贸易',
    'french': '法语培训/法企驻华/精品翻译工作室',
    'arabic': '中东贸易公司/阿语培训/跨境电商',
    'portuguese': '澳门/拉美/非洲葡语区贸易',
    'korean': '韩语培训/中韩电商/韩企驻华',
    'italian': '意大利语培训/奢侈品代购/艺术留学中介',
    'world-history': '历史博主/文博策展自由撰稿人/口述史工作室',
    'national-economy-management': '宏观研究咨询/智库助理/产业研究',
    'economics-finance': '量化私募分析师/家族办公室/产业基金',
    'asset-appraisal': '资产评估事务所合伙人/评估咨询公司',
    'discipline-inspection-supervision': '纪检工作 (体制内)',
    'economic-crime-investigation': '经侦领域律师/反洗钱咨询/金融犯罪调查',
    'police-command-tactics': '警务培训教官/安保公司/危机管理咨询',
    'sports-training': '体育培训工作室/退役运动员转型教练/赛事组织',
    'leisure-sports': '户外运动俱乐部/体育旅游/健身工作室',
    'veterinary-medicine': '宠物医院个体执业/兽医技术咨询',
    'pediatrics': '儿科诊所 (民营/合伙制)',
    'radiation-medicine': '医学影像中心合伙人/远程影像诊断',
    'chinese-painting': '独立画室/签约画廊/艺术品经纪',
    'health-service-management': '健康管理公司/养老机构运营',
    'new-energy-vehicle-engineering': '新能源创业/汽车后市场',
    'intelligent-perception-engineering': '智能硬件创业/技术咨询',
    'flexible-electronics': '柔性显示/可穿戴创业/技术转化',
    'intelligent-transportation': '智能交通方案商/集成商',
    'urban-underground-space-engineering': '岩土/地下工程咨询',
    'aerospace-engineering': '航天创业/卫星应用',
    'aircraft-propulsion-engineering': '航空发动机技术咨询',
    'ece-cs': 'AI/全栈开发/技术咨询',
    'applied-statistics': '数据科学咨询/统计培训',
    'nuclear-physics': '核能技术咨询/医疗物理师',
    # C session 之前的占位
    'supply-chain-management': '供应链咨询/物流创业',
    'credit-management': '信用管理咨询/征信创业',
    'cross-border-ecommerce': '跨境电商品牌出海',
    'fintech': '金融科技创业/区块链咨询',
    'animal-science': '畜牧业技术咨询',
    'russian': '俄语培训/中俄贸易',
    'horticulture': '花卉/果蔬种植创业',
    'environmental-resource-protection-law': '环境法咨询/律所合伙人',
    'pharmaceutical-engineering': '药企技术咨询',
}

def fix_entrepreneur(data: dict, slug: str) -> int:
    """Replace '自主创业/其他' placeholders in employment_direction. Return fix count."""
    fixed = 0
    directions = data.get('employment_direction', [])
    for d in directions:
        if d.get('name') in ('自主创业', '自主创业/其他', '其他', '其他方向'):
            d['name'] = f"自主创业 ({ENTREPRENEUR_MAP.get(slug, '专业相关方向')})"
            fixed += 1
    return fixed

def fix_salary(data: dict) -> int:
    """Convert salary strings to p25/p50/p75 dict. Return fix count."""
    fixed = 0
    salary = data.get('salary', {})
    if not isinstance(salary, dict):
        return 0
    for key, val in list(salary.items()):
        if isinstance(val, str):
            # parse '8K-12K' or '8000-12000'
            m = re.match(r'(\d+)(?:\.\d+)?[Kk]?\s*[-~到至]\s*(\d+)(?:\.\d+)?[Kk]?', val)
            if m:
                a, b = float(m.group(1)), float(m.group(2))
                # 处理 K 后缀
                if 'K' in val.upper() or 'k' in val:
                    a *= 1000
                    b *= 1000
                p25, p50, p75 = a, (a + b) / 2, b
                # 转换为万 (按年)
                salary[key] = {
                    'p25': round(p25 * 12 / 10000, 1),  # 万/年
                    'p50': round(p50 * 12 / 10000, 1),
                    'p75': round(p75 * 12 / 10000, 1),
                    'yoy': 5
                }
                fixed += 1
    return fixed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='Preview changes')
    ap.add_argument('--batch', type=int, default=30, help='Batch number to filter')
    args = ap.parse_args()

    print(f"=== Batch {args.batch} Schema Cleanup {'(DRY RUN)' if args.dry_run else ''} ===\n")

    total_files = 0
    total_fixes = 0
    for f in sorted(CURATED.glob('*.json')):
        if f.name in ('TEMPLATE.json', 'manifest.json'):
            continue
        slug = f.stem
        try:
            data = json.load(open(f))
        except Exception as e:
            print(f"❌ {slug}: {e}")
            continue

        fixes = 0
        fixes += fix_entrepreneur(data, slug)
        fixes += fix_salary(data)

        if fixes > 0:
            total_files += 1
            total_fixes += fixes
            if not args.dry_run:
                json.dump(data, open(f, 'w'), ensure_ascii=False, indent=2)
            print(f"  {slug:50s} {fixes} fixes")

    print(f"\n=== 总结 ===")
    print(f"受影响的文件: {total_files}")
    print(f"总修复数: {total_fixes}")

if __name__ == '__main__':
    main()
