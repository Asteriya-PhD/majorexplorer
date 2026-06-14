#!/usr/bin/env bash
# pipeline_batch2.sh — Batch 2 (education + literature) 完整流水线
# 顺序: normalize → render → fix_data_count → fix_html_paths → fix_fade_up → screenshot
set -e
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp

CSVS="scripts/batches/education_v1.csv scripts/batches/literature_v1.csv"

echo "=== 1/6 normalize (Batch 2: 13 篇) ==="
for csv in $CSVS; do
  echo "  → $csv"
  python3 scripts/batches/normalize.py "$csv" 2>&1 | tail -16
done

echo ""
echo "=== 2/6 render ==="
for csv in $CSVS; do
  echo "  → $csv"
  python3 scripts/batches/render_batch.py --csv "$csv" 2>&1 | tail -15
done

echo ""
echo "=== 3/6 fix_data_count ==="
python3 scripts/batches/fix_data_count.py 2>&1 | tail -10

echo ""
echo "=== 4/6 fix_html_paths ==="
python3 scripts/batches/fix_html_paths.py 2>&1 | tail -10

echo ""
echo "=== 5/6 fix_fade_up ==="
python3 scripts/batches/fix_fade_up.py 2>&1 | tail -10

echo ""
echo "=== 6/6 screenshot (Batch 2: 13 张) ==="
for csv in $CSVS; do
  python3 scripts/batches/screenshot_batch.py --csv "$csv" 2>&1 | tail -10
done

echo ""
echo "✅ Batch 2 pipeline 完成"
