"""
synth/search.py — 4 路 web search 摘要, 供 LLM 合成用.

路由: Bing Web Search API → Tavily → Serper → DDG HTML 抓取 (fallback)

每路独立 try-except, 失败自动 fall-through.
最终汇总成 de-duped 30 段 (snippet), 输入到 synthesize prompt.

环境变量 (任一即可):
  BING_SEARCH_API_KEY   (Azure Bing Web Search)
  TAVILY_API_KEY
  SERPER_API_KEY

无任一 key 时, 直接走 DDG HTML 抓取 (无需 key, 但可能被 rate limit).
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import quote_plus

import requests

# 本地缓存: 7 天内同 query 直接复用 (web search 结果不要求新鲜)
_CACHE_DIR = os.path.expanduser("~/.cache/synth_search")
os.makedirs(_CACHE_DIR, exist_ok=True)
_CACHE_TTL = 7 * 86400  # 7 days


@dataclass
class Snippet:
    title: str
    url: str
    snippet: str
    source: str  # bing/tavily/serper/ddg

    def to_dict(self) -> dict:
        return asdict(self)


def _cache_path(q: str) -> str:
    h = hashlib.md5(q.encode("utf-8")).hexdigest()
    return os.path.join(_CACHE_DIR, f"{h}.json")


def _cache_get(q: str) -> list[dict] | None:
    p = _cache_path(q)
    if not os.path.exists(p):
        return None
    age = time.time() - os.path.getmtime(p)
    if age > _CACHE_TTL:
        return None
    try:
        return json.loads(open(p, encoding="utf-8").read())
    except Exception:
        return None


def _cache_put(q: str, items: list[dict]):
    p = _cache_path(q)
    try:
        open(p, "w", encoding="utf-8").write(json.dumps(items, ensure_ascii=False))
    except Exception:
        pass


# ── 单路实现 ──
def _bing_search(q: str, n: int = 10) -> list[Snippet]:
    """Azure Bing Web Search API (7 天 free trial)."""
    key = os.environ.get("BING_SEARCH_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            params={"q": q, "count": n, "mkt": "zh-CN"},
            headers={"Ocp-Apim-Subscription-Key": key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [bing] fail: {e}", flush=True)
        return []
    items = []
    for w in data.get("webPages", {}).get("value", []):
        items.append(Snippet(
            title=w.get("name", "")[:120],
            url=w.get("url", ""),
            snippet=w.get("snippet", "")[:300],
            source="bing",
        ))
    return items


def _tavily_search(q: str, n: int = 10) -> list[Snippet]:
    """Tavily Search API (1K/月 free)."""
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": q, "max_results": n,
                  "search_depth": "basic", "include_answer": False},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [tavily] fail: {e}", flush=True)
        return []
    return [
        Snippet(
            title=r.get("title", "")[:120],
            url=r.get("url", ""),
            snippet=r.get("content", "")[:300],
            source="tavily",
        )
        for r in data.get("results", [])
    ]


def _serper_search(q: str, n: int = 10) -> list[Snippet]:
    """Serper.dev Google Search API (2.5K/月 free)."""
    key = os.environ.get("SERPER_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            json={"q": q, "gl": "cn", "hl": "zh-cn", "num": n},
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [serper] fail: {e}", flush=True)
        return []
    return [
        Snippet(
            title=r.get("title", "")[:120],
            url=r.get("link", ""),
            snippet=r.get("snippet", "")[:300],
            source="serper",
        )
        for r in data.get("organic", [])
    ]


def _ddg_html_search(q: str, n: int = 10) -> list[Snippet]:
    """DuckDuckGo HTML scrape fallback (无 key, 易 rate-limit)."""
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": q, "kl": "cn-zh"},
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36"},
            timeout=10,
        )
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"  [ddg] fail: {e}", flush=True)
        return []

    items = []
    # DDG HTML 结果用 result__a / result__snippet 类名包裹
    for m in re.finditer(
        r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'<a class="result__snippet"[^>]*>(.*?)</a>',
        html, re.DOTALL,
    ):
        url = m.group(1)
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()[:120]
        snippet = re.sub(r"<[^>]+>", "", m.group(3)).strip()[:300]
        if url and title:
            items.append(Snippet(title=title, url=url, snippet=snippet, source="ddg"))
            if len(items) >= n:
                break
    return items


# ── 入口: 4 路 fallback, dedupe, top 30 ──
SEARCH_ROUTES = [_bing_search, _tavily_search, _serper_search, _ddg_html_search]


def search_major(title: str, max_snippets: int = 30) -> list[Snippet]:
    """
    4 路 fallback web search 汇总.
    1) 缓存命中直接返回
    2) 否则按 bing→tavily→serper→ddg 顺序, 任一返回 ≥5 条即停
    3) 都不够则 4 路合并 + dedup
    """
    cached = _cache_get(title)
    if cached:
        return [Snippet(**d) for d in cached]

    collected: list[Snippet] = []
    for route in SEARCH_ROUTES:
        if collected and len(collected) >= 8:
            break  # 已有, 停止
        items = route(title, n=10)
        if items:
            print(f"  [search] {route.__name__} → {len(items)} 条", flush=True)
            collected.extend(items)

    # dedupe by url
    seen = set()
    deduped = []
    for s in collected:
        if s.url and s.url not in seen:
            seen.add(s.url)
            deduped.append(s)
    deduped = deduped[:max_snippets]
    _cache_put(title, [s.to_dict() for s in deduped])
    return deduped


def format_for_prompt(snippets: list[Snippet]) -> str:
    """把 Snippet list 拼成 LLM 友好的搜索摘要."""
    if not snippets:
        return "(无搜索结果, 请基于训练知识回答并标'基于通用知识估算')"
    lines = []
    for i, s in enumerate(snippets, 1):
        lines.append(f"[{i}] {s.title}")
        lines.append(f"    {s.snippet}")
        if s.url:
            lines.append(f"    来源: {s.url}")
        lines.append("")
    return "\n".join(lines)


# ── 多查询策略 ──
def search_multi(queries: list[str], per_query: int = 8) -> list[Snippet]:
    """对一组 query 各跑 search_major, dedup, top 30."""
    collected: list[Snippet] = []
    seen = set()
    for q in queries:
        items = search_major(q, max_snippets=per_query)
        for s in items:
            if s.url not in seen:
                seen.add(s.url)
                collected.append(s)
    return collected[:30]


# ── 预设查询模板 ──
def queries_for_major(title: str) -> list[str]:
    """为新专业生成 4-6 路并行查询."""
    return [
        f"{title} 培养方案 课程",
        f"{title} 就业方向 薪资",
        f"{title} 头部院校 软科排名",
        f"{title} 校友访谈 知乎",
        f"{title} 学科评估 全国第四轮",
        f"{title} 选科要求 新高考 3+1+2",
    ]


# ── CLI ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python search.py <major_title>")
        sys.exit(1)
    title = sys.argv[1]
    items = search_multi(queries_for_major(title))
    print(f"\n=== {title}: {len(items)} 段 ===\n")
    print(format_for_prompt(items[:10]))
