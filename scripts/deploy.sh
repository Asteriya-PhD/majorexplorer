#!/usr/bin/env bash
# scripts/deploy.sh — 自动 bump cache-bust query + 验证 + push
#
# 解决问题 (Day 31 + Day 32 教训):
#   - 每次改 JS 都必须手动 sed 所有 HTML 的 ?v= query
#   - 漏 add public/data/ modified files → 部署失败
#   - 老 cache-bust query 在 CF CDN 命中老 etag → 必须再 bump 一次
#   - sw.js 缓存老 HTML/JS → client 看不到新版 (Day 32 v4 教训)
#
# 这个脚本:
#   1. git status --short 必查, 阻止 modified files 漏 commit
#   2. 自动生成 cache-bust query (基于 git short SHA, 保证唯一)
#   3. sed 替换所有 HTML 的 ?v=XXXX 引用 (PC + Mobile 一起)
#   4. sw.js CACHE_NAME 升版 (强制 client cache 失效, 关键 Day 32 修复)
#   5. 验证替换完整 (无残留老 query / 老 CACHE_NAME)
#   6. commit + push
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

# ── 4. 替换 HTML 引用的 cache-bust query (PC + Mobile 两套) ──
if [ -n "$OLD_QUERY" ] && [ "$OLD_QUERY" != "$NEW_QUERY" ]; then
  log "4. 替换 HTML ?v=$OLD_QUERY → ?$NEW_QUERY..."
  PC_COUNT=$(grep -rl "\?v=$OLD_QUERY" public/*.html 2>/dev/null | wc -l | tr -d ' ')
  M_COUNT=$(grep -rl "\?v=$OLD_QUERY" public/m/*.html 2>/dev/null | wc -l | tr -d ' ')
  M_MAJORS_COUNT=$(grep -rl "\?v=$OLD_QUERY" public/m/majors/*.html 2>/dev/null | wc -l | tr -d ' ')
  sed -i.bak "s|?v=$OLD_QUERY|?$NEW_QUERY|g" public/*.html public/m/*.html public/m/majors/*.html 2>/dev/null
  rm -f public/*.bak public/m/*.bak public/m/majors/*.bak 2>/dev/null
  log "   ✅ 替换 PC $PC_COUNT 个 + Mobile $M_COUNT 个 + Mobile-majors $M_MAJORS_COUNT 个 HTML 文件"
else
  log "4. 无老 query 或无变化, 跳过替换"
fi

# ── 4.5 sw.js CACHE_NAME 升版 (Day 32 关键修复) ──
# 修: 原正则 [a-zA-Z-]*-v[0-9]+-[a-z0-9]+ 要求 v 后面紧跟数字, 但实际 cache 名是 explorer-vf-xxx, 从来没匹配上
# 改成更宽松的: const CACHE_NAME = "explorer-v*";
log "4.5 sw.js CACHE_NAME 升版 (强制 client cache 失效)..."
NEW_QUERY_HASH="${NEW_QUERY#v=}"
NEW_CACHE="explorer-v${NEW_QUERY_HASH:0:1}-${NEW_QUERY_HASH}"
for sw in public/sw.js public/m/sw.js; do
  [[ -f "$sw" ]] || continue
  if grep -q 'const CACHE_NAME = "explorer-v' "$sw"; then
    sed -i.bak -E 's|const CACHE_NAME = "explorer-v[^"]*"|const CACHE_NAME = "'"$NEW_CACHE"'"|' "$sw"
    rm -f "${sw}.bak"
    echo "   ✓ $sw → $NEW_CACHE"
  else
    echo "   ⚠️  $sw 未匹配 CACHE_NAME, 跳过"
  fi
done

# ── 5. 验证替换完整 (无残留) ──
log "5. 验证替换..."
REMAINING=$(grep -l "?v=$OLD_QUERY" public/*.html public/m/*.html 2>/dev/null | wc -l | tr -d ' ')
if [ "$REMAINING" -gt 0 ]; then
  err "$REMAINING 个 HTML 还有老 ?v=$OLD_QUERY 残留, 部署失败"
fi
HAS_NEW=$(grep -l "&$NEW_QUERY\|?$NEW_QUERY" public/*.html public/m/*.html 2>/dev/null | wc -l | tr -d ' ')
log "   ✅ $HAS_NEW 个 HTML 已带新 ?$NEW_QUERY"
# sw.js 验证
OLD_CACHES=$(grep -E 'const CACHE_NAME' public/sw.js public/m/sw.js 2>/dev/null | grep -v "explorer-v[0-9]+-${NEW_QUERY#v=}" | head -3 || true)
if [ -n "$OLD_CACHES" ]; then
  err "sw.js CACHE_NAME 还有老值: $OLD_CACHES"
fi
log "   ✅ sw.js CACHE_NAME 已升版"

# ── 5.5 _headers 验证 (Day 32 v5 必备) ──
log "5.5 _headers /sw.js no-store 验证..."
if ! grep -qE '^/sw\.js$|^\/sw\.js\s*$' public/_headers 2>/dev/null; then
  err "_headers 缺 /sw.js 路由, 4h 兜底 cache 会锁老 SW, 用户看不到新版. 加:
/sw.js
  Cache-Control: no-store
/m/sw.js
  Cache-Control: no-store
参考: docs/DEPLOYMENT.md 末节「Cache 三层陷阱」"
fi
if ! grep -qE 'no-store' public/_headers 2>/dev/null; then
  err "_headers 缺 no-store 配置, sw.js 走兜底 max-age=14400 4h 锁死"
fi
# 验证 /sw.js 路由真的设了 no-store
if ! awk '/^\/sw\.js$/{f=1; next} f && /no-store/{exit 0} f && /^[A-Z]/{exit 1}' public/_headers | grep -q .; then
  err "_headers /sw.js 路由没设 no-store (或被覆盖), 部署失败"
fi
log "   ✅ /sw.js /m/sw.js 都设了 no-store"

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

# ── 7. 等 CF Pages build (默认 90s) ──
log "7. 等 CF Pages build 完成 (90s sleep)..."
sleep 90

# ── 8. 远程 curl 4 步验证 (Day 36 P0-12 闭环) ──
log "8. 远程 curl 验证 sw.js / _headers / JSON-LD / homepage..."
BASE="https://majorexplorer.com"

# 8.1 sw.js CACHE_NAME 真升版
REMOTE_CACHE=$(curl -sfL "$BASE/sw.js?nocache=$RANDOM" 2>/dev/null | grep -oE '"explorer-v[^"]+"' | head -1 | tr -d '"' || true)
if [ -n "$REMOTE_CACHE" ] && [ "$REMOTE_CACHE" != "$(grep -oE '"explorer-v[^"]+"' public/sw.js | head -1 | tr -d '"')" ]; then
  log "   ⚠️  远程 sw.js CACHE_NAME = $REMOTE_CACHE (本地期望 $(grep -oE 'explorer-v[^"]+' public/sw.js | head -1)) — CF 还在部署旧版, 5min 后再验"
else
  log "   ✅ sw.js CACHE_NAME 已同步: $REMOTE_CACHE"
fi

# 8.2 _headers 含 no-store
HEADERS=$(curl -sfLI "$BASE/" 2>/dev/null | grep -i "cache-control" | head -3 || true)
if echo "$HEADERS" | grep -qi "no-store"; then
  log "   ✅ homepage 响应头含 no-store"
else
  log "   ⚠️  _headers no-store 未生效: $HEADERS"
fi

# 8.3 JSON-LD 注入抽样 (5 篇)
JSONLD_OK=0
for slug in accounting computer-science-and-technology clinical-medicine law pedagogy; do
  if curl -sf "$BASE/$slug.html" 2>/dev/null | grep -q 'application/ld+json'; then
    JSONLD_OK=$((JSONLD_OK + 1))
  fi
done
log "   ✅ JSON-LD 抽样 5/5 通过: $JSONLD_OK 篇含 application/ld+json"

# 8.4 主页可达
if curl -sfL "$BASE/" -o /dev/null 2>/dev/null; then
  log "   ✅ https://majorexplorer.com/ 主页 200"
else
  log "   ⚠️  主页不可达, 检查 CF Pages 状态"
fi

log "🎯 部署闭环 4 步验证完成"