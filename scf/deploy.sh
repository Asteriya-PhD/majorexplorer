#!/bin/bash
# deploy.sh — 一键部署长尾专业按需生成到腾讯云 SCF
#
# 前置:
#   1. pip install tencentcloud-sdk-python-cos
#   2. 腾讯云控制台开 SCF + COS + API Gateway
#   3. 设环境变量: TENCENTCLOUD_SECRETID, TENCENTCLOUD_SECRETKEY, TENCENTCLOUD_REGION
#   4. SCF 控制台设 DEEPSEEK_API_KEY + COS_SECRET_ID + COS_SECRET_KEY
#
# 用法:
#   ./scf/deploy.sh                    # 部署到 ap-hongkong
#   ./scf/deploy.sh --dry-run          # 只打包, 不上传
#   ./scf/deploy.sh --function-only    # 只更新函数代码, 不动 API Gateway

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCF_DIR="$ROOT/scf"
BUILD_DIR="$ROOT/.scf_build"
STAGE="${STAGE:-prod}"
REGION="${REGION:-ap-hongkong}"

echo "=== SCF Synth 部署 (stage=$STAGE, region=$REGION) ==="

# 0. 检查依赖
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 未装"; exit 1; }

# 1. 打包
echo "📦 打包 scf/synth + skills/.../scripts + curated manifest ..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/synth"
cp -r "$SCF_DIR/synth/"* "$BUILD_DIR/synth/"

# 复制 scf 入口主文件
cp "$SCF_DIR/synth/main.py" "$BUILD_DIR/synth/main.py"  # main.py 已在 synth/

# 复制项目根 (因为 main.py 引用 ROOT.parent)
# SCF 部署时 ROOT.parent = $BUILD_DIR, 所以把 scf/ 上移一级
mv "$BUILD_DIR" "$ROOT/.scf_build_tmp"
rm -rf "$ROOT/.scf_build"
mv "$ROOT/.scf_build_tmp" "$ROOT/.scf_build"

# 复制 skills scripts + curated (大文件多, 需 100MB 上限, 实际 ~5MB)
cp -r "$ROOT/skills" "$ROOT/.scf_build/skills"

# 复制 public (大, 但 SCF 不需要它, render_bridge 只写 public/)
# 不复制, 加快打包; render_bridge 写时 path 用 ROOT.parent/public/

# 2. dry-run
if [[ "${1:-}" == "--dry-run" ]]; then
  echo "📋 dry-run: 打包完成 → $ROOT/.scf_build"
  du -sh "$ROOT/.scf_build"
  echo "(用 ./scf/deploy.sh 真正部署)"
  exit 0
fi

# 3. 上传 (用 scf cli 或 cos 上传 zip)
if command -v scf >/dev/null 2>&1; then
  echo "⬆️  scf cli 部署..."
  cd "$ROOT/.scf_build"
  scf deploy -t "$SCF_DIR/template.yaml" --stage "$STAGE" --region "$REGION"
elif command -v sls >/dev/null 2>&1; then
  echo "⬆️  serverless framework 部署..."
  cd "$ROOT"
  sls deploy --stage "$STAGE" --region "$REGION"
else
  echo "❌ 需装 scf cli 或 serverless framework"
  echo "   pip install tencentcloud-sdk-python"
  echo "   或 npm i -g serverless"
  exit 1
fi

# 4. 验证
echo "🩺 健康检查..."
SERVICE_URL="${SERVICE_URL:-https://service-xxxx-${REGION}.apigw.tencentcs.com/release/synth}"
curl -sf "${SERVICE_URL}/health" | head -c 200
echo ""

# 5. 清理
rm -rf "$ROOT/.scf_build"

echo "✅ 部署完成"
echo "   API: $SERVICE_URL"
echo "   调用: curl -X POST $SERVICE_URL/generate -d '{\"title\":\"治安学\"}'"
