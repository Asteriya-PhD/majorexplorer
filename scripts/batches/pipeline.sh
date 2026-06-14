#!/usr/bin/env bash
# pipeline.sh — 一键跑完整修复流水线
# 顺序: normalize → render → fix_data_count → fix_fade_up → screenshot
set -e
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp
echo "=== 1/5 normalize ==="
python3 scripts/batches/normalize.py | tail -15
echo ""
echo "=== 2/5 render ==="
python3 scripts/batches/render_batch.py --csv scripts/batches/law_gongan_v1.csv | tail -15
echo ""
echo "=== 3/5 fix_data_count (144 处) ==="
python3 scripts/batches/fix_data_count.py | tail -15
echo ""
echo "=== 4/5 fix_html_paths (12 处, /js/ → ../../js/) ==="
python3 scripts/batches/fix_html_paths.py | tail -15
echo ""
echo "=== 5/5 fix_fade_up (299 处) ==="
python3 scripts/batches/fix_fade_up.py | tail -15
echo ""
echo "=== 5/5 screenshot (14 张) ==="
python3 scripts/batches/screenshot_batch.py | tail -18
echo ""
echo "✅ 完整 pipeline 完成"