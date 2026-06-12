#!/usr/bin/env python3
"""
scf_local_e2e.py — 本地模拟 SCF API Gateway + handler 跑 e2e.

T14 部署验证: 不需要腾讯云账号, 本地模拟 API Gateway event,
直接调 scf/synth/main.py 的 handler(), 跑真实 LLM 全 pipeline.

用法:
  export DEEPSEEK_API_KEY=sk-...
  python3 scripts/scf_local_e2e.py --title 翻译 --slug translation --style humanities
  python3 scripts/scf_local_e2e.py --title 治安学 --slug public-order --style gongan --cleanup

模拟的事件格式参考 API Gateway 触发器 (腾讯云 SCF 文档):
  {
    "httpMethod": "POST",
    "path": "/synth/generate",
    "body": "{...json...}",
    "queryString": {},
    "headers": {...}
  }
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

# 让 import 找得到 scf 包
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser(description="本地模拟 SCF e2e")
    p.add_argument("--title", required=True, help="专业名")
    p.add_argument("--slug", required=True, help="URL slug")
    p.add_argument("--style", help="强制 style (跳过 route)")
    p.add_argument("--cleanup", action="store_true", help="跑前删旧产物 (slug.html / curated json)")
    args = p.parse_args()

    # 1. 跑前清理 (测 idempotency)
    if args.cleanup:
        for path in [
            ROOT / "public" / f"{args.slug}.html",
            ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated" / f"{args.slug}.html",
            ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated" / f"{args.slug}.json",
        ]:
            if path.exists():
                path.unlink()
                print(f"  🧹 清理: {path.name}")

    # 2. 模拟 API Gateway 健康检查
    from scf.synth import main as scf_main
    print("\n🩺 Step 0: 健康检查 (GET /synth/health)")
    health_event = {"httpMethod": "GET", "path": "/synth/health", "queryString": {}}
    health_resp = scf_main.handler(health_event, None)
    print(f"  状态: {health_resp['statusCode']}")
    print(f"  body: {health_resp['body']}")
    assert health_resp["statusCode"] == 200, "健康检查失败"
    assert "version" in health_resp["body"], "响应缺 version"

    # 3. 模拟 POST /synth/generate (跑 7 步 pipeline, ≤15min)
    print(f"\n🚀 Step 1: POST /synth/generate title={args.title!r}")
    body = {"title": args.title, "slug": args.slug}
    if args.style:
        body["style"] = args.style
    gen_event = {
        "httpMethod": "POST",
        "path": "/synth/generate",
        "queryString": {},
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"},
    }
    gen_resp = scf_main.handler(gen_event, None)
    print(f"  状态: {gen_resp['statusCode']}")
    print(f"  body: {gen_resp['body'][:500]}")
    assert gen_resp["statusCode"] == 200, f"generate 失败: {gen_resp['body']}"

    gen_data = json.loads(gen_resp["body"])
    run_id = gen_data.get("run_id")
    assert run_id, f"未拿到 run_id: {gen_data}"

    # 4. 模拟 GET /synth/status
    print(f"\n📊 Step 2: GET /synth/status?run_id={run_id[:8]}...")
    status_event = {
        "httpMethod": "GET",
        "path": "/synth/status",
        "queryString": {"run_id": run_id},
    }
    status_resp = scf_main.handler(status_event, None)
    print(f"  状态: {status_resp['statusCode']}")
    print(f"  body: {status_resp['body'][:500]}")
    assert status_resp["statusCode"] == 200, "status 查询失败"

    # 5. 验证产物落地
    print("\n✅ Step 3: 验证产物")
    public_html = ROOT / "public" / f"{args.slug}.html"
    curated_html = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated" / f"{args.slug}.html"
    assert public_html.exists(), f"public/{args.slug}.html 不存在"
    assert curated_html.exists(), f"curated/{args.slug}.html 不存在"
    public_size = public_html.stat().st_size
    print(f"  public/{args.slug}.html: {public_size:,} bytes")
    print(f"  curated/{args.slug}.html: {curated_html.stat().st_size:,} bytes")
    assert public_size > 50_000, f"HTML 太小 ({public_size}), 渲染异常"

    # 6. 验证 manifest 已含
    print("\n📋 Step 4: 验证 manifest")
    m = json.loads((ROOT / "public" / "data" / "manifest.json").read_text(encoding="utf-8"))
    found = any(x["slug"] == args.slug for x in m["majors"])
    assert found, f"manifest 不含 {args.slug}"
    entry = next(x for x in m["majors"] if x["slug"] == args.slug)
    print(f"  manifest total: {m['total']}, styles_used: {len(m['styles_used'])}")
    print(f"  {args.slug}: style={entry['style']}, category={entry['category']!r}")

    # 7. 总结
    status_data = json.loads(status_resp["body"])
    print(f"\n🎉 e2e 验证通过")
    print(f"  run_id: {run_id}")
    print(f"  quality_score: {status_data.get('quality_score', '?')}")
    print(f"  cost: ¥{status_data.get('cost_cny', '?')}")
    print(f"  output: /{args.slug}.html ({public_size:,} bytes)")
    print(f"\n☁️  T14 部署就绪: ./scf/deploy.sh (需腾讯云账号 + COS bucket)")


if __name__ == "__main__":
    main()
