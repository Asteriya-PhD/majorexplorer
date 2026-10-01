#!/usr/bin/env bash
# re-render.sh — 重渲专业 HTML + 补齐 SEO 注入 (2026-10-01)
#
# 解决的问题: 重渲 render_one.py / render_mobile.py **不产出** SEO 块
# (og/twitter/JSON-LD/hreflang), 直接部署会导致:
#   - 社交分享卡片失效 (缺 og:title / og:description)
#   - 结构化数据消失 (缺 JSON-LD)
#   - 搜索引擎收录退化
# 且 5 个 inject_* 脚本之间有**顺序依赖** (实测):
#   inject_twitter_card.py 要求 og:title/desc/image 三件套先在,
#   否则直接 skipped —— 之前就是因此出现 "og 有了 twitter 没有"。
#
# 用法:
#   ./scripts/build/re-render.sh                  # 全量 (625 篇)
#   ./scripts/build/re-render.sh <slug> [<slug>]  # 指定 slug
#
# 成本: 全量 ~90s, 0¥
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${BLUE}▶ [1/6] 重渲 mobile${NC}"
if [ $# -gt 0 ]; then
  for s in "$@"; do python3 scripts/build/render_mobile.py --slug "$s"; done
else
  python3 scripts/build/render_mobile.py
fi

echo -e "${BLUE}▶ [2/6] 重渲 PC (render_one.py 逐篇)${NC}"
if [ $# -gt 0 ]; then
  for s in "$@"; do python3 scripts/build/render_one.py "$s"; done
else
  # 全量 PC: render_one.py 只支持单篇, 这里用 xargs 并发
  ls skills/gaokao-major-explorer/data/curated/*.json \
    | xargs -n1 basename | sed 's/\.json$//' \
    | grep -v -E '^(manifest|TEMPLATE)$' \
    | xargs -P 4 -I{} python3 scripts/build/render_one.py {} >/dev/null
  echo "  ✅ PC 全量重渲完成"
fi

# ↓↓↓ 顺序敏感: 这几个有依赖, 换序会导致 twitter/hreflang 被 skip ↓↓↓
echo -e "${BLUE}▶ [3/6] 注入 canonical + og:title/description (inject_seo)${NC}"
python3 scripts/build/inject_seo.py | tail -2

echo -e "${BLUE}▶ [4/6] 注入 og:image/type (inject_og, 需在 seo 之后)${NC}"
if [ $# -gt 0 ]; then
  for s in "$@"; do python3 scripts/build/inject_og.py --slug "$s" >/dev/null; done
  echo "  ✅ og 注入完成"
else
  python3 scripts/build/inject_og.py | tail -2
fi

echo -e "${BLUE}▶ [5/6] 注入 twitter (依赖 og 三件套, 必须最后)${NC}"
python3 scripts/build/inject_twitter_card.py | tail -2
python3 scripts/build/inject_hreflang.py | tail -2

echo -e "${BLUE}▶ [6/6] 注入 JSON-LD${NC}"
if [ $# -gt 0 ]; then
  for s in "$@"; do python3 scripts/build/inject_jsonld_v2.py --slug "$s" | tail -1; done
else
  python3 scripts/build/inject_jsonld_v2.py | tail -2
fi

echo ""
echo -e "${GREEN}✅ 重渲 + SEO 注入完成${NC}"
echo -e "${YELLOW}   部署前必跑: python3 scripts/audit/prelaunch_content_check.py --all${NC}"
