#!/usr/bin/env python3
"""
synth_trigger.py — 本地 CLI 触发 1 篇长尾专业按需生成.

7 步 pipeline:
  1. validate_is_major        LLM 0-shot 校验 (防误触发)
  2. search_multi             4 路 web search 30 段
  3. route_style              LLM 0-shot 主题路由
  4. synthesize_json          LLM 合成 (≤3 轮反喂)
  5. validate + score_quality JSON 校验
  6. render_html              subprocess generate_dashboard.py
  7. append_major             同步两份 manifest.json

用法:
  python scripts/synth_trigger.py --title 治安学 --slug gongzhi-xue
  python scripts/synth_trigger.py --title 治安学 --slug gongzhi-xue --style gongan --skip-search
  python scripts/synth_trigger.py --title 保险学 --slug insurance --style finance
  python scripts/synth_trigger.py --batch batch35.txt   (从文件批量)
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path

# 让 scf 包可被 import
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scf.synth.llm import get_client, get_client_with_fallback, RetryableError, PermanentError
from scf.synth.mock_llm import get_llm_client, MockLLM
from scf.synth.search import search_multi, queries_for_major, format_for_prompt
from scf.synth.prompts import (
    load_schema_doc, load_sample_for_style, summarize_sample, build_retry_prompt
)
from scf.synth.validator import validate, score_quality, format_for_retry
from scf.synth.manifest_ops import (
    load_manifest, append_major, upsert_manifest_minimal
)
from scf.synth.render_bridge import render_html, save_data_json, RenderError


def slugify(title: str) -> str:
    """从中文 title 派生英文 slug (拼音/字符 fallback)."""
    import re
    # 优先用 pypinyin, 没有则用占位
    try:
        from pypinyin import lazy_pinyin
        en = "-".join(s for s in lazy_pinyin(title) if s.strip())
        return re.sub(r"[^a-z0-9-]+", "-", en.lower()).strip("-")
    except ImportError:
        # 退化: 用 hex(title) 前 16 位
        return "x-" + hex(hash(title) & 0xFFFFFFFF)[2:]


def synth_one(
    title: str,
    slug: str | None = None,
    style_override: str | None = None,
    skip_search: bool = False,
    max_retries: int = 3,
) -> dict:
    """
    单篇按需生成完整 pipeline. 返回 summary dict.
    """
    t0 = time.time()
    slug = slug or slugify(title)
    summary: dict = {"title": title, "slug": slug, "steps": []}

    # ── 0. LLM 客户端 (auto-fallback: m3 → deepseek) ──
    try:
        llm, used_provider = get_client_with_fallback(chain=("m3", "deepseek"))
    except PermanentError as e:
        # 全失败, 退到 mock
        print(f"  ⚠️  所有 provider fail ({e}), 退到 MockLLM")
        llm = get_llm_client(root=ROOT)  # fallback to mock
        used_provider = "mock"
    llm_type = "MockLLM" if isinstance(llm, MockLLM) else type(llm).__name__
    summary["llm"] = llm_type
    summary["llm_provider"] = used_provider
    print(f"🤖 LLM 客户端就绪 ({llm_type} via {used_provider})")

    # ── 1. validate_is_major ──
    try:
        is_major, normalized = llm.validate_is_major(title)
    except RetryableError as e:
        # Day 7 Session 4: m3 validate 也可能 fail (max_tokens/thinking bug)
        if used_provider == "m3" and ("max_tokens" in str(e) or "thinking" in str(e) or "JSON" in str(e)):
            print(f"  ⚠️  m3 validate fail ({e}), 降级 deepseek")
            try:
                llm, used_provider = get_client_with_fallback(chain=("deepseek",), enable_thinking=False)
                summary["llm_provider"] = used_provider
                is_major, normalized = llm.validate_is_major(title)
            except (RetryableError, PermanentError) as e2:
                summary["error"] = f"validate_is_major m3→deepseek 都失败: {e2}"
                return summary
        else:
            summary["error"] = f"validate_is_major 失败: {e}"
            return summary
    summary["steps"].append({"step": 1, "is_major": is_major, "normalized": normalized})
    if not is_major:
        summary["error"] = f"输入不是本科专业: {title!r}"
        return summary
    if normalized and normalized != title:
        print(f"  ℹ️  标准化: {title!r} → {normalized!r}")
        title = normalized
        summary["title"] = title
    print(f"✅ Step 1: 是本科专业 ({title})")

    # ── 2. web search ──
    search_context = "(无搜索结果)"
    if not skip_search:
        try:
            queries = queries_for_major(title)
            print(f"🔍 Step 2: 跑 {len(queries)} 路 web search ...")
            snippets = search_multi(queries, per_query=8)
            search_context = format_for_prompt(snippets)
            summary["steps"].append({"step": 2, "queries": queries, "snippets": len(snippets)})
        except Exception as e:
            print(f"  ⚠️  search 失败 (用空上下文继续): {e}")
            summary["steps"].append({"step": 2, "error": str(e)})
    else:
        print("⏭️  Step 2: skip-search")
        summary["steps"].append({"step": 2, "skipped": True})
    print(f"✅ Step 2: search context {len(search_context)} chars")

    # ── 3. route_style ──
    if style_override:
        style = style_override
        print(f"⏭️  Step 3: --style override = {style}")
    else:
        try:
            # 先抓 summary 给路由参考
            brief = search_context[:500] if search_context != "(无搜索结果)" else ""
            style = llm.route_style(title, brief)
            summary["steps"].append({"step": 3, "style": style})
        except RetryableError as e:
            # Day 7 Session 4: m3 route_style 也可能 fail, 降级 deepseek
            if used_provider == "m3" and ("max_tokens" in str(e) or "thinking" in str(e) or "JSON" in str(e)):
                print(f"  ⚠️  m3 route_style fail, 降级 deepseek")
                try:
                    llm, used_provider = get_client_with_fallback(chain=("deepseek",), enable_thinking=False)
                    summary["llm_provider"] = used_provider
                    style = llm.route_style(title, brief)
                    summary["steps"].append({"step": 3, "style": style, "via": "deepseek"})
                except (RetryableError, PermanentError) as e2:
                    print(f"  ⚠️  route_style 双 provider fail ({e2}), fallback to 'cs'")
                    style = "cs"
            else:
                print(f"  ⚠️  route_style 失败 fallback to 'cs': {e}")
                style = "cs"
    summary["style"] = style
    print(f"✅ Step 3: route_style = {style}")

    # ── 4 + 5. synthesize_json + validate, 最多 3 轮反喂 ──
    schema_doc = load_schema_doc()
    sample = load_sample_for_style(ROOT, style)
    sample_summary = summarize_sample(sample)
    print(f"📝 Step 4: 加载 1-shot sample ({sample.get('title', '无')})")

    prev_errors: list[str] = []
    prev_warnings: list[str] = []
    data: dict | None = None
    quality: dict = {}

    for round_i in range(1, max_retries + 1):
        try:
            data = llm.synthesize_json(
                title=title, style=style,
                search_context=search_context,
                sample_json=sample, schema_doc=schema_doc,
                previous_errors=prev_errors, previous_warnings=prev_warnings,
            )
        except RetryableError as e:
            err_str = str(e)
            # Day 7 Session 4: m3 thinking 块 max_tokens bug → 自动降级 deepseek
            # (m3 强制 enabled thinking 4096, server 端 max_tokens 上限 8000 时全占 thinking 无空间给 JSON)
            if used_provider == "m3" and ("max_tokens" in err_str or "thinking" in err_str):
                print(f"  ⚠️  m3 thinking/max_tokens fail ({e}), 自动降级 deepseek")
                try:
                    llm, used_provider = get_client_with_fallback(chain=("deepseek",), enable_thinking=False)
                    summary["llm_provider"] = used_provider
                    # 重试 1 次 (不算 round)
                    data = llm.synthesize_json(
                        title=title, style=style,
                        search_context=search_context,
                        sample_json=sample, schema_doc=schema_doc,
                        previous_errors=prev_errors, previous_warnings=prev_warnings,
                    )
                except (RetryableError, PermanentError) as e2:
                    summary["error"] = f"synthesize_json m3→deepseek 都失败: {e2}"
                    return summary
            else:
                summary["error"] = f"synthesize_json 第 {round_i} 轮失败: {e}"
                return summary
        except PermanentError as e:
            summary["error"] = f"synthesize_json 第 {round_i} 轮失败: {e}"
            return summary

        # 5. validate
        ok, errs, warns = validate(data)
        score = score_quality(data)
        print(f"  轮 {round_i}: validate ok={ok} (errors={len(errs)}, warnings={len(warns)}), quality={score['quality_score']}")

        if ok and score["quality_score"] >= 0.7:
            prev_errors, prev_warnings = [], []
            quality = score
            break
        else:
            prev_errors, prev_warnings = errs, warns
            if round_i == max_retries:
                # 最后 1 轮, 失败
                quality = score
                summary["steps"].append({
                    "step": "4-5", "round": round_i, "errors": errs, "warnings": warns,
                    "quality": score,
                })

    if not data:
        summary["error"] = "synthesize_json 全部轮次失败"
        return summary
    if not quality or quality["quality_score"] < 0.7:
        # 3 轮都未达标, 标 fallback
        summary["error"] = f"质量分 {quality.get('quality_score', 0)} < 0.7, 标 fallback"
        summary["data"] = data
        return summary

    # 注入必要字段
    data.setdefault("slug", slug)
    data.setdefault("style", style)
    data.setdefault("updated_at", time.strftime("%Y-%m"))
    data.setdefault("data_source", f"按需生成 (DeepSeek-V3) + Web 搜索 + {time.strftime('%Y-%m-%d')}")
    print(f"✅ Step 4-5: 合成 + 校验通过 (quality={quality['quality_score']})")

    # ── 6. render_html ──
    try:
        save_data_json(data, slug)
        out_path, size = render_html(data, slug, style)
        summary["steps"].append({"step": 6, "path": out_path, "size": size})
        print(f"✅ Step 6: HTML 渲染 {size:,} bytes → {out_path}")
    except RenderError as e:
        summary["error"] = f"render_html 失败: {e}"
        return summary

    # ── 7. append manifest ──
    try:
        is_mock = bool(data.get("_mock"))
        ok = upsert_manifest_minimal(
            root=ROOT, slug=slug, title=data.get("title", title),
            style=style, category=data.get("category", ""),
            degree=data.get("degree", ""),
            duration_years=data.get("duration_years", 4),
            tags=data.get("tags", []),
            data_source=data.get("data_source", "按需生成"),
            _mock=is_mock,  # 守卫: mock 产物不入 manifest
        )
        summary["steps"].append({"step": 7, "manifest_upsert": ok})
        print(f"✅ Step 7: manifest {'追加' if ok else '已存在, 跳过'}")
    except Exception as e:
        summary["steps"].append({"step": 7, "error": str(e)})
        print(f"  ⚠️  manifest 追加失败 (HTML 已落地): {e}")

    summary["data"] = data
    summary["quality"] = quality
    summary["elapsed_sec"] = round(time.time() - t0, 1)
    summary["cost_cny"] = round(llm.cost_estimate_cny(), 4)
    summary["ok"] = True
    print(f"\n🎉 完成: {title} ({slug}) [{style}] quality={quality['quality_score']} "
          f"cost={summary['cost_cny']}元 耗时 {summary['elapsed_sec']}s")
    return summary


def main():
    p = argparse.ArgumentParser(description="按需生成 1 篇长尾专业")
    p.add_argument("--title", help="专业中文名 (单篇模式)")
    p.add_argument("--slug", help="URL slug (默认从 title 派生)")
    p.add_argument("--style", help="强制 style (跳过 route_style)")
    p.add_argument("--skip-search", action="store_true", help="跳过 web search (调试用)")
    p.add_argument("--max-retries", type=int, default=3, help="反喂轮数")
    p.add_argument("--batch", help="批量文件路径 (每行: title | slug | style)")
    p.add_argument("--out", help="summary JSON 输出路径")
    p.add_argument("--from-json", help="从已合成的 JSON 文件跑后半段 (skip LLM)")
    p.add_argument("--json-style", help="与 --from-json 配对, 强制 style")
    args = p.parse_args()

    if args.batch:
        # 批量模式 (默认 skip-search, 因为没有 web search API key)
        results = []
        skip_search = args.skip_search or True  # 批量默认 skip
        for line in Path(args.batch).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            title = parts[0]
            slug = parts[1] if len(parts) > 1 else None
            style = parts[2] if len(parts) > 2 else None
            print(f"\n{'='*60}\n📚 {title}\n{'='*60}")
            r = synth_one(title, slug, style, skip_search=skip_search)
            results.append(r)
            if not r.get("ok"):
                print(f"⚠️  {title} 失败: {r.get('error')}")
        if args.out:
            Path(args.out).write_text(
                json.dumps(results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"\n📊 批量结果写入: {args.out}")
        ok = sum(1 for r in results if r.get("ok"))
        print(f"\n=== 批量完成: {ok}/{len(results)} ok ===")
    elif args.from_json:
        # 半 pipeline 模式: 跑 5+6+7 (validate+render+manifest)
        from scf.synth.manifest_ops import upsert_manifest_minimal
        from scf.synth.render_bridge import render_html, save_data_json, RenderError
        from scf.synth.validator import validate, score_quality, format_for_retry
        json_path = Path(args.from_json)
        data = json.loads(json_path.read_text(encoding="utf-8"))
        slug = data.get("slug") or json_path.stem
        title = data.get("title", slug)
        style = args.json_style or data.get("style", "cs")
        ok, errs, warns = validate(data)
        score = score_quality(data)
        print(f"  validate: ok={ok}, errors={len(errs)}, warnings={len(warns)}, quality={score['quality_score']}")
        if not ok:
            print(format_for_retry(errs, warns))
            sys.exit(1)
        try:
            save_data_json(data, slug)
            out, size = render_html(data, slug, style)
            print(f"  render: {out} ({size:,} bytes)")
        except RenderError as e:
            print(f"  render 失败: {e}")
            sys.exit(1)
        try:
            ok2 = upsert_manifest_minimal(
                root=ROOT, slug=slug, title=title, style=style,
                category=data.get("category", ""),
                degree=data.get("degree", ""),
                duration_years=data.get("duration_years", 4),
                tags=data.get("tags", []),
                data_source=data.get("data_source", "按需生成 (测试)"),
            )
            print(f"  manifest upsert: {'✅' if ok2 else '已存在'}")
        except Exception as e:
            print(f"  manifest 失败: {e}")
        if args.out:
            Path(args.out).write_text(
                json.dumps({"data": data, "score": score, "ok": True}, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        print(f"\n🎉 --from-json 完成: {title} quality={score['quality_score']}")
        sys.exit(0)
    elif args.title:
        result = synth_one(args.title, args.slug, args.style, args.skip_search, args.max_retries)
        if args.out:
            Path(args.out).write_text(
                json.dumps(result, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            print(f"📊 summary 写入: {args.out}")
        sys.exit(0 if result.get("ok") else 1)
    else:
        p.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
