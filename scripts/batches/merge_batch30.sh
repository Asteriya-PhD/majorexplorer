#!/usr/bin/env bash
# Batch 30 merge + cleanup + audit + push
# 合并 day3-batch30-{A,B,C} 3 个分支到 main, 跑 cleanup + 全量 audit
set -euo pipefail

cd /Users/zhewenliu/Claude/gaokao-hubei-mvp

echo "=== 1) Pre-merge: 检查 stash ==="
git stash list
git status --short

echo ""
echo "=== 2) 合并 3 个分支到 main ==="
for branch in day3-batch30-A day3-batch30-B day3-batch30-C; do
  echo "--- 合并 $branch ---"
  git merge --no-ff "$branch" -m "merge: $branch (10 majors P1) → main" || {
    echo "❌ 合并 $branch 失败, 需手动解决冲突"
    exit 1
  }
done

echo ""
echo "=== 3) 验证合并结果 ==="
git log --oneline -25
echo "新增 JSON 数量: $(git diff HEAD~3 HEAD --name-only | grep -c '\.json$' || true)"

echo ""
echo "=== 4) Schema Cleanup: 拆细 '自主创业/其他' 占位 ==="
# 这一步是 session 任务, 必跑
# 详见 session memory day3-team-b-post-merge-cleanup-2026-06-17.md

echo ""
echo "=== 5) 全量 audit ==="
source .env
export DEEPSEEK_API_KEY M3_API_KEY M3_BASE_URL M3_MODEL
# 30 篇分批跑, 避免 timeout
python3 scripts/batches/content_audit.py --csv /tmp/batch30_audit.csv

echo ""
echo "=== 6) 推送 main 到 origin ==="
git push origin main

echo ""
echo "=== 7) CF Pages 自动 rebuild 验证 ==="
echo "(等 30-60s 后 CF dashboard 看部署状态)"
