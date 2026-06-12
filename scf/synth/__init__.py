"""
synth — 长尾专业按需生成模块.

包内模块:
  validator       JSON schema 校验 + 5 维质量分
  llm             DeepSeek 客户端 (Anthropic SDK 兼容)
  search          4 路 web search + 摘要
  prompts         3 个 prompt 模板 (synthesize / validate / route)
  manifest_ops    manifest.json atomic 追加
  render_bridge   subprocess 调 generate_dashboard.py 写两处产物
  main            SCF 入口 (HTTP 路由 + 7 步 worker)
"""
__version__ = "0.1.0"
