#!/usr/bin/env bash
# install-hooks.sh — 一键安装 pre-commit hook
#
# 作用: 把 .githooks/ 配置为 git 仓库的 hooks 目录
#       之后所有 `git commit` 自动跑 .githooks/pre-commit
#
# 用法:
#   ./scripts/install-hooks.sh              # 安装
#   ./scripts/install-hooks.sh --uninstall  # 卸载
#
# 兼容性: macOS / Linux, 不需要 sudo (只改 git config 本仓库)

set -e

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

HOOKS_DIR=".githooks"
HOOK_PATH="$HOOKS_DIR/pre-commit"

if [ "$1" = "--uninstall" ]; then
  echo "🗑️  卸载 pre-commit hook..."
  git config --unset core.hooksPath 2>/dev/null || true
  echo "✅ 已卸载 (git config core.hooksPath 清除)"
  echo "   后续 commit 不会跑 pre-commit 检查"
  exit 0
fi

# 1. 检查 hook 文件存在
if [ ! -f "$HOOK_PATH" ]; then
  echo "❌ $HOOK_PATH 不存在"
  exit 1
fi

# 2. chmod +x
chmod +x "$HOOK_PATH"
echo "✅ chmod +x $HOOK_PATH"

# 3. 配置 git core.hooksPath
git config core.hooksPath "$HOOKS_DIR"
echo "✅ git config core.hooksPath $HOOKS_DIR"

echo ""
echo "🎉 pre-commit hook 安装完成!"
echo ""
echo "验证:"
echo "  git config core.hooksPath     # 应该输出 .githooks"
echo "  cat .git/hooks/pre-commit     # 现在是 git 默认 hook (没用)"
echo ""
echo "下次 commit 自动跑 5 检查:"
echo "  1. backfill_manifest_fields.py --check  (5 字段完整性)"
echo "  2. check_major.py --staged              (L1 4 anti-pollution + schema)"
echo "  3. rebuild_manifest.py --check          (curated/ vs manifest 漂移)"
echo "  4. build_aggregates.py --check          (manifest ↔ aggregates 漂移)"
echo "  5. render_quality.py --staged           (Day 49 HTML 渲染质量门: 结构 + 薪资单调 + 字段完整, warn-only 至 Day 55)"
echo ""
echo "绕过 (不推荐): git commit --no-verify"
