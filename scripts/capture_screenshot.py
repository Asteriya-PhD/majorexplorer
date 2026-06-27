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
                  wait_seconds: float = 2.0, full_page: bool = True,
                  verify_text: str | None = None):
    """截图, 可选 verify_text — 截前等 DOM 包含该文本才截(防止 JS 异步未完成)

    Args:
        verify_text: 若提供, 会反复检查 page body 是否含此字符串,
                     直到出现或超时 15 秒。用于等 countUp / IntersectionObserver / canvas 渲染。
    """
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

        # 强制触发 IntersectionObserver lazy load + 数字滚动动画
        # 方法: 滚动到底再滚回顶, 让所有 section 进入视口
        print(f"  ⏳ 滚动到底 + 等 IntersectionObserver 触发所有 lazy section")
        await page.evaluate("""async () => {
            // 1. 滚动到底, 让所有 section 进入视口
            window.scrollTo(0, document.body.scrollHeight);
            // 2. 等所有 lazy img 加载
            const imgs = document.querySelectorAll('img[loading="lazy"]');
            imgs.forEach(img => img.loading = 'eager');
            const dataImgs = document.querySelectorAll('img[data-src]');
            dataImgs.forEach(img => { img.src = img.dataset.src; });
            // 3. 滚回顶
            window.scrollTo(0, 0);
        }""")

        # 等额外时间 (canvas / 数字滚动 / IntersectionObserver 触发)
        if wait_seconds > 0:
            print(f"  ⏳ 等 {wait_seconds} 秒 (canvas / 数字滚动 / 异步渲染)")
            await page.wait_for_timeout(int(wait_seconds * 1000))

        # 可选: 反复等 DOM 含目标文本 (确认 JS 异步完成)
        if verify_text:
            print(f"  ⏳ 等 DOM 含 '{verify_text[:40]}...' (直到渲染完)")
            for i in range(30):  # 最多 15 秒
                content = await page.content()
                if verify_text in content:
                    print(f"  ✓ 目标文本已渲染 (用了 {i*0.5:.1f}s)")
                    break
                await page.wait_for_timeout(500)
            else:
                print(f"  ⚠ 15s 超时仍未见目标文本 (可能没渲染或拼写错)")

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
    ap.add_argument("--verify-text", default=None, help="等 DOM 含此字符串再截 (防异步未完成)")
    ap.add_argument("--no-full-page", action="store_true")
    args = ap.parse_args()

    w, h = map(int, args.viewport.split(","))
    asyncio.run(capture(args.url, (w, h), args.output, args.wait, not args.no_full_page, args.verify_text))


if __name__ == "__main__":
    main()
