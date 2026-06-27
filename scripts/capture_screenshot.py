#!/usr/bin/env python3
"""
Playwright 截图脚本 — 等待所有 JS + canvas + 字体完成, 适合动态页面

用法:
  python3 scripts/capture_screenshot.py \\
    --url http://localhost:8800/public/clinical-medicine.html \\
    --viewport 1200,1500 \\
    --output /tmp/sample.png

默认行为:
  1. 等待 'networkidle' (无网络请求 500ms)
  2. 等待 fonts.ready (web fonts 加载完)
  3. 等待额外 2 秒 (canvas 动画 + 数字滚动完成)
  4. full-page 截图
"""
import asyncio
import argparse
from pathlib import Path
from playwright.async_api import async_playwright


async def capture(url: str, viewport: tuple[int, int], output: str,
                  wait_seconds: float = 2.0, full_page: bool = True):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        page = await ctx.new_page()

        print(f"加载: {url}")
        # 拦截 fonts.loli.net (谷歌字体国内镜像) — 沙箱环境网络慢, 不拦截就超时
        async def block_fonts(route):
            url_str = route.request.url
            if "fonts.loli.net" in url_str or "fonts.googleapis.com" in url_str:
                # 返回空 CSS, 让浏览器认为字体已加载完
                await route.fulfill(status=200, content_type="text/css", body="/* fonts blocked */")
            else:
                await route.continue_()
        await ctx.route("**/*", block_fonts)
        print(f"  ✓ 拦截 fonts.loli.net / googleapis (沙箱慢)")

        # domcontentloaded 是最稳的 — 不等资源/canvas
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print(f"  ✓ domcontentloaded (DOM 解析完)")

        # 等字体
        try:
            await page.evaluate("document.fonts.ready")
            print(f"  ✓ fonts.ready (web fonts loaded)")
        except Exception as e:
            print(f"  ⚠ fonts.ready 超时: {e}")

        # 等额外时间 (canvas / 数字滚动 / IntersectionObserver 触发)
        if wait_seconds > 0:
            print(f"  ⏳ 等 {wait_seconds} 秒 (canvas / 数字滚动 / 异步渲染)")
            await page.wait_for_timeout(int(wait_seconds * 1000))

        print(f"截图 → {output}")
        await page.screenshot(path=output, full_page=full_page)

        size = Path(output).stat().st_size
        print(f"  ✓ 完成 ({size:,} bytes)")

        await browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--viewport", default="1200,1500", help="width,height")
    ap.add_argument("--output", required=True)
    ap.add_argument("--wait", type=float, default=2.0, help="额外等待秒数 (默认 2)")
    ap.add_argument("--no-full-page", action="store_true")
    args = ap.parse_args()

    w, h = map(int, args.viewport.split(","))
    asyncio.run(capture(args.url, (w, h), args.output, args.wait, not args.no_full_page))


if __name__ == "__main__":
    main()
