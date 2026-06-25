#!/usr/bin/env bash
# scripts/deploy.sh — 自动 bump cache-bust query + 验证 + push
#
# 解决问题 (Day 31 教训):
#   - 每次改 JS 都必须手动 sed 所有 HTML 的 ?v= query
#   - 漏 add public/data/ modified files → 部署失败
#   - 老 cache-bust query 在 CF CDN 命中老 etag → 必须再 bump 一次
#
# 这个脚本:
#   1. git status --short 必查, 阻止 modified files 漏 commit
#   2. 自动生成 cache-bust query (基于 git short SHA, 保证唯一)
#   3. sed 替换所有 HTML 的 ?v=XXXX 引用
#   4. 验证替换完整 (无残留老 query)
#   5. commit + push
#
# 用法:
#   ./scripts/deploy.sh "feat: yfyd 2026 更新"   # 自动 commit + push
#   ./scripts/deploy.sh                            # 用默认 message "deploy: bump cache"
#
# 环境:
#   - 在 git repo 根目录跑
#   - 网络能 push 到 origin (GH_TOKEN 或 ssh 配置)

set -euo pipefail

# ── 0. 路径 & 颜色 ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[err]${NC} $*" >&2; exit 1; }

# ── 1. 检查 git 状态 ──
log "1. 检查 git 状态..."
if ! git diff --quiet HEAD 2>/dev/null || [ -n "$(git status --short)" ]; then
  log "   有未提交的改动"
else
  log "   无未提交改动 (会 bump cache-bust 但无内容变化)"
fi

# ── 2. 检查 public/data/ 是否漏 add (Day 31 致命教训 #4) ──
log "2. 检查 public/data/ modified files 漏 add..."
MODIFIED_NOT_STAGED=$(git status --short public/data/ | grep "^.M" || true)
if [ -n "$MODIFIED_NOT_STAGED" ]; then
  err "public/data/ 有 modified 未 staged:
$MODIFIED_NOT_STAGED
必须手动 git add (CF Pages 直接 serve public/data/, 漏 add 会 serve 老版)"
fi
log "   ✅ 无漏 add"

# ── 3. 生成 cache-bust query (基于 git HEAD short SHA) ──
NEW_QUERY="v=$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
log "3. 生成 cache-bust query: ?$NEW_QUERY"

# 检测老 query (用于 sed 替换)
OLD_QUERY=""
if grep -rqE '\?v=[a-zA-Z0-9]+' public/*.html 2>/dev/null; then
  OLD_QUERY=$(grep -hoE '\?v=[a-zA-Z0-9]+' public/*.html | sort -u | head -1 | sed 's/?v=//')
  if [ -n "$OLD_QUERY" ]; then
    log "   老 query: ?v=$OLD_QUERY"
  fi
fi

# ── 4. 替换 HTML 引用的 cache-bust query ──
if [ -n "$OLD_QUERY" ] && [ "$OLD_QUERY" != "$NEW_QUERY" ]; then
  log "4. 替换 HTML ?v=$OLD_QUERY → ?$NEW_QUERY..."
  COUNT=$(grep -rl "\?v=$OLD_QUERY" public/*.html | wc -l | tr -d ' ')
  sed -i.bak "s|?v=$OLD_QUERY|?$NEW_QUERY|g" public/*.html
  rm -f public/*.bak
  log "   ✅ 替换 $COUNT 个 HTML 文件"
else
  log "4. 无老 query 或无变化, 跳过替换"
fi

# ── 5. 验证替换完整 (无残留) ──
log "5. 验证替换..."
REMAINING=$(grep -l "?v=$OLD_QUERY" public/*.html 2>/dev/null | wc -l | tr -d ' ')
if [ "$REMAINING" -gt 0 ]; then
  err "$REMAINING 个 HTML 还有老 ?v=$OLD_QUERY 残留, 部署失败"
fi
HAS_NEW=$(grep -l "&$NEW_QUERY\|?$NEW_QUERY" public/*.html 2>/dev/null | wc -l | tr -d ' ')
log "   ✅ $HAS_NEW 个 HTML 已带新 ?$NEW_QUERY"

# ── 6. git add + commit + push ──
MSG="${1:-deploy: bump cache-bust $NEW_QUERY}"
log "6. git add + commit + push..."
git add -A

# 检查是否有改动要 commit
if git diff --cached --quiet; then
  warn "无 staged 改动, 跳过 commit"
else
  git commit -m "$MSG

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
  log "   ✅ commit 完成"
fi

# push (如果用户配置了 remote)
if git remote get-url origin >/dev/null 2>&1; then
  log "7. git push origin main..."
  git push origin main
  log "   ✅ push 完成"
else
  warn "无 origin remote, 跳过 push (需要手动: git remote add origin ...)"
fi

log "🎉 部署完成! CF Pages 会在 1-3 分钟内自动 build + 部署"
log "   新 cache-bust query: $NEW_QUERY"
log "   1h 后用户浏览器自然 revalidate 拿到新版"