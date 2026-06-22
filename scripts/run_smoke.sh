#!/usr/bin/env bash
# run_smoke.sh — Day 5 防踩 smoke fixture 验证 (5 篇陷阱 prompt → check_major 校验)
#
# 目的: 验证 m3/deepseek synth prompt 加 3+1+2 + salary 硬规则后,
#       不会再 hallucinate "物理+历史+政治" / 应届 P50=35万 等违规内容.
#
# 用法: bash scripts/run_smoke.sh
# 期望: 2 BAD 触发 (xuanke CRITICAL + salary WARNING), 3 GOOD 通过 (0 false positive).

set -euo pipefail
cd "$(dirname "$0")/.."

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Smoke Fixture — Day 5 防踩加固验证 (5 篇陷阱 prompt)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 跑 fixtures: 期望 4 通过 (3 GOOD + 1 BAD-with-only-WARNING), 1 失败 (BAD CRITICAL), 1 警告 (BAD WARNING)
# check_major.py --fixtures 退出码: 0=全过, 1=有失败
python3 scripts/audit/check_major.py --fixtures scripts/smoke_fixtures
SMOKE_EXIT=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 验收标准:"
echo "  • smoke_xuanke_1_finance_BAD    → ❌ CRITICAL 物历同现 (期望 1 个 CRITICAL)"
echo "  • smoke_xuanke_2_admin_GOOD     → ✓ 通过 (0 false positive)"
echo "  • smoke_xuanke_3_medicine_GOOD  → ✓ 通过 (0 false positive)"
echo "  • smoke_salary_4_finance_BAD    → ⚠️  WARNING 应届 P50=35万虚高 (期望 1 个 WARNING)"
echo "  • smoke_salary_5_cs_GOOD        → ✓ 通过 (0 false positive)"
echo ""
echo "🔁 何时跑:"
echo "  1. 新加/改 m3 synth prompt 模板时 (scripts/synth/batch_synth.py)"
echo "  2. 改 check_major.py 任何 anti-pollution 规则时"
echo "  3. 加新 style 模板校准数据时 (fix_xuanke_salary_batch.py)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 退出码: check_major 已退出 1 (有失败 = 1 个 BAD CRITICAL), 这是期望的
exit $SMOKE_EXIT
