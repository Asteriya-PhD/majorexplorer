"""
perf_measure.py — Lightweight perf measurement via playwright + Performance Timing API.

不需要 lighthouse npm 包. 收集核心指标:
  - FCP (First Contentful Paint)
  - LCP (Largest Contentful Paint) — 通过 PerformanceObserver
  - CLS (Cumulative Layout Shift)
  - DOM Content Loaded / Load 时间
  - 资源总数 + 字节数

用法:
    python3 scripts/perf_measure.py                         # 默认 3 个样板
    python3 scripts/perf_measure.py cs medicine agri        # 指定主题
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / "skills/gaokao-major-explorer/data/curated"

# 默认 5 主题: cs (终端) / medicine (Mayo Clinic 框架) / agri (装饰复杂) / humanities (多字体) / business (Bento+Bodoni)
DEFAULT_TARGETS = {
    "cs":         "computer-science",
    "medicine":   "pharmacy",
    "agri":       "horticulture",
    "humanities": "philosophy",
    "business":   "business-administration-demo",
}

# 注入到页面 wait 1.5s 后采集 — 等 LCP 稳定
PERF_SCRIPT = r"""
() => new Promise((resolve) => {
  const out = { fcp: null, lcp: null, cls: 0, dcl: null, load: null, resources: 0, transferKB: 0 };

  // Navigation Timing
  const nav = performance.getEntriesByType('navigation')[0];
  if (nav) {
    out.dcl = Math.round(nav.domContentLoadedEventEnd);
    out.load = Math.round(nav.loadEventEnd);
  }

  // Paint Timing
  const paints = performance.getEntriesByType('paint');
  const fcp = paints.find(p => p.name === 'first-contentful-paint');
  if (fcp) out.fcp = Math.round(fcp.startTime);

  // LCP
  try {
    const lcpObs = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries.length) out.lcp = Math.round(entries[entries.length - 1].startTime);
    });
    lcpObs.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {}

  // CLS
  try {
    const clsObs = new PerformanceObserver((list) => {
      for (const e of list.getEntries()) {
        if (!e.hadRecentInput) out.cls += e.value;
      }
    });
    clsObs.observe({ type: 'layout-shift', buffered: true });
  } catch (e) {}

  // Resources
  const res = performance.getEntriesByType('resource');
  out.resources = res.length;
  out.transferKB = Math.round(res.reduce((a, r) => a + (r.transferSize || r.encodedBodySize || 0), 0) / 1024);

  // wait 1.5s for LCP/CLS to settle
  setTimeout(() => {
    out.cls = +out.cls.toFixed(3);
    resolve(out);
  }, 1500);
});
"""


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(DEFAULT_TARGETS.keys())
    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for style in targets:
            slug = DEFAULT_TARGETS.get(style, style)
            html = CURATED / f"{slug}.html"
            if not html.exists():
                print(f"[skip] {style}: {html.name} not found")
                continue
            url = "file://" + str(html)
            for label, viewport in [("desktop", {"width": 1366, "height": 800}), ("mobile", {"width": 390, "height": 844})]:
                ctx = b.new_context(viewport=viewport)
                pg = ctx.new_page()
                pg.goto(url, wait_until="networkidle")
                metrics = pg.evaluate(PERF_SCRIPT)
                rows.append((style, label, metrics))
                ctx.close()
        b.close()
    # report
    print(f"\n{'theme':14s} {'mode':8s} {'FCP':>6s} {'LCP':>6s} {'CLS':>6s} {'DCL':>6s} {'Load':>6s} {'res':>4s} {'KB':>6s}")
    print("-" * 70)
    for style, mode, m in rows:
        print(f"{style:14s} {mode:8s} {m['fcp'] or '-':>6} {m['lcp'] or '-':>6} {m['cls']:>6} {m['dcl'] or '-':>6} {m['load'] or '-':>6} {m['resources']:>4} {m['transferKB']:>6}")
    print("\n指标 (ms): FCP=首字, LCP=最大内容元素, CLS=累积偏移 (越小越好, <0.1 优), DCL/Load=毫秒")


if __name__ == "__main__":
    main()
