# gaokao-hubei-mvp Makefile (Day 59 / 2026-07-02)
# 单一入口聚合高频命令,新 session `make` 看全貌
#
# 设计原则:
#   1. 不重复 scripts/deploy.sh (那是 7 步 Cache 4 层锁死的专用 SOP)
#   2. 不内联逻辑 — 只调用现有 Python 脚本
#   3. 不引入 .PHONY 噪音 — 顶部一次性声明

.PHONY: help build render manifest aggregates seo sitemap audit quality deploy clean-cache reset-deps

help: ## 默认入口 — 显示所有 target
	@grep -E '^[a-z][a-z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: render manifest aggregates seo sitemap ## 全量构建入口 (新 session 推荐)

render: ## PC HTML 全量重建 (覆盖 625 major)
	python3 scripts/build/build_all_majors.py

manifest: ## public/data/manifest.json 增量更新
	python3 scripts/schema-fix/rebuild_manifest.py

aggregates: ## aggregates.json 重建 (门类统计)
	python3 scripts/build/build_aggregates.py

seo: ## JSON-LD + SEO meta 注入
	python3 scripts/build/inject_jsonld.py --no-backup
	python3 scripts/build/inject_seo.py

sitemap: ## sitemap.xml 生成
	python3 scripts/build/build_sitemap.py

audit: ## 智能混合审计 (Layer 1 启发 + Layer 2 LLM 路由)
	python3 scripts/audit/smart_audit.py

quality: ## 渲染质量硬门禁 (render_quality 双零 baseline,Day 56+)
	python3 scripts/audit/render_quality.py --all --sync-registry

deploy: ## ⚠️  部署必须走 scripts/deploy.sh (Cache 4 层锁死 SOP),不要手动 push
	@echo "用法: bash scripts/deploy.sh '<msg>'"
	@echo "不用直接 git push — 见 docs/DEPLOYMENT.md 末尾"
	@false

clean-cache: ## 清 Python __pycache__ 目录
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
	@echo "✅ __pycache__ cleared"

reset-deps: ## 重装 Python 依赖 (requirements.txt)
	pip install -r requirements.txt
