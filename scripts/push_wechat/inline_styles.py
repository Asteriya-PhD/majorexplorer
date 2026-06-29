#!/usr/bin/env python3
"""
把 docs/retrospectives/2026-06-26_wechat-parents-final.html
转成纯 inline-style HTML (微信编辑器可推送版)
"""
import re
import sys
from pathlib import Path

SRC = Path("docs/retrospectives/2026-06-26_wechat-parents-final.html")
OUT = Path("docs/retrospectives/2026-06-26_wechat-parents-push.html")


def inline_styles(html: str) -> str:
    """把 class 替换为 inline style, 删 <style> 块"""

    # 1. header.head
    html = re.sub(
        r'<header class="head">\s*<h1>(.*?)</h1>\s*<p class="sub">(.*?)</p>\s*</header>',
        lambda m: (
            f'<header style="background:#E8E8E8;padding:28px 24px 20px;'
            f'text-align:center;border-radius:6px;margin-bottom:32px;">'
            f'<h1 style="font-size:22px;font-weight:bold;color:#1A1A1A;'
            f'line-height:1.4;margin:0 0 10px;">{m.group(1)}</h1>'
            f'<p style="font-size:13px;color:#999;margin:0;">{m.group(2)}</p>'
            f'</header>'
        ),
        html,
        flags=re.DOTALL,
    )

    # 2. div.lede
    html = re.sub(
        r'<div class="lede" style="background-color: var\(--bg-2\); padding: 24px 22px; border-radius: 8px; margin-bottom: 32px;">',
        '<div style="background-color:#F8F8F6;padding:24px 22px;border-radius:8px;margin-bottom:32px;">',
        html,
    )

    # 3. section.banner
    html = re.sub(
        r'<section class="banner"><h2>(.*?)</h2></section>',
        lambda m: (
            f'<section style="background:#0FB880;padding:14px 20px;'
            f'border-radius:4px;margin:36px 0 20px;">'
            f'<h2 style="color:#FFFFFF;font-size:18px;font-weight:bold;'
            f'margin:0;letter-spacing:1px;">{m.group(1)}</h2>'
            f'</section>'
        ),
        html,
    )

    # 4. div.card (含 lbl)
    def card_replace(m: re.Match) -> str:
        inner = m.group(1)
        # 抽 lbl
        lbl_m = re.search(
            r'<span class="lbl">(.*?)</span>', inner
        )
        lbl = lbl_m.group(1) if lbl_m else ""
        # 抽其余 p
        ps = re.findall(r'<p>(.*?)</p>', inner, flags=re.DOTALL)
        ps_html = "".join(
            f'<p style="color:#333;font-size:15px;line-height:1.7;margin:0 0 8px;">{p}</p>'
            for p in ps
        )
        return (
            f'<section style="background:rgba(15,184,128,0.08);'
            f'padding:16px 20px;border-radius:8px;'
            f'border-left:4px solid #0FB880;margin:20px 0;">'
            f'<span style="color:#0FB880;font-size:12px;font-weight:bold;'
            f'letter-spacing:0.1em;margin-bottom:8px;display:block;">{lbl}</span>'
            f'{ps_html}'
            f'</section>'
        )

    html = re.sub(
        r'<div class="card">(.*?)</div>',
        card_replace,
        html,
        flags=re.DOTALL,
    )

    # 5. div.highlight (黄底框)
    def highlight_replace(m: re.Match) -> str:
        inner = m.group(1)
        # 抽 ol/ul (保留列表结构) 或 p
        ol_m = re.search(r'<ol>(.*?)</ol>', inner, flags=re.DOTALL)
        ps = re.findall(r'<p>(.*?)</p>', inner, flags=re.DOTALL)
        # 处理 list 内的 li
        if ol_m:
            ol_inner = ol_m.group(1)
            lis = re.findall(r'<li>(.*?)</li>', ol_inner, flags=re.DOTALL)
            list_html = (
                '<ol style="padding-left:24px;margin:0;">'
                + "".join(
                    f'<li style="color:#333;font-size:15px;line-height:1.7;margin:4px 0;">{li}</li>'
                    for li in lis
                )
                + '</ol>'
            )
        else:
            list_html = ""
        ps_html = "".join(
            f'<p style="color:#333;font-size:15px;line-height:1.7;margin:0 0 8px;">{p}</p>'
            for p in ps
        )
        return (
            f'<section style="background-color:#FDE68A;'
            f'border-radius:8px;padding:16px 20px;'
            f'border:2px solid #F59E0B;margin:20px 0;">'
            f'{ps_html}{list_html}'
            f'</section>'
        )

    html = re.sub(
        r'<div class="highlight">(.*?)</div>',
        highlight_replace,
        html,
        flags=re.DOTALL,
    )

    # 6. div.stat (用 item 结构定位, 避开内嵌 div 干扰)
    def stat_replace(m: re.Match) -> str:
        items = re.findall(
            r'<div><b>(.*?)</b><span>(.*?)</span></div>', m.group(1)
        )
        if not items:
            return m.group(0)
        cells = "".join(
            f'<td style="text-align:center;padding:6px 12px;vertical-align:bottom;">'
            f'<div style="font-size:28px;color:#0FB880;font-weight:bold;line-height:1.1;">{v}</div>'
            f'<div style="font-size:12px;color:#999;letter-spacing:0.05em;margin-top:4px;">{l}</div>'
            f'</td>'
            for v, l in items
        )
        return (
            f'<table style="width:100%;margin:32px 0;'
            f'border-top:1px solid #E8E4D8;'
            f'border-bottom:1px solid #E8E4D8;border-collapse:collapse;">'
            f'<tr>{cells}</tr></table>'
        )

    # 用更严格的 marker: div class="stat"> 后跟 <div><b>NUMBER</b>...
    # 因为 stat 块始终以 <div class="stat">\n  <div><b> 开头, 以最后 </div>\n</div> 收尾
    # 用 lookahead 找从 <div class="stat"> 到下一个 class=" 之前的全部
    html = re.sub(
        r'<div class="stat">((?:(?!class=").)*?)(</div>)\s*</div>',
        stat_replace,
        html,
        flags=re.DOTALL,
    )
    # 上面 regex 复杂, 兜底用更直白: 抓 stat 块内容到下一个空行后 </div>
    # 实际上 stat_replace 已经在 m.group(1) 拿到内容, 问题在于 m.group(1) 的边界
    # 简化: 直接搜 <div class="stat">...到 "stat" 块结束 (这里只 1 处)
    # 退回: 用最朴素方法 - 找 stat 块开始到下一个章节 banner 或 footer
    if '<div class="stat">' in html:
        # 找到 stat 开始
        s = html.find('<div class="stat">')
        # 找最近的上一个 </section> 之后到 stat 开始的全部 inner
        # 但更简单: stat 块用 <div>...<div>... 嵌套, 看 line 170-177
        # 替代方案: 手动指定
        old_stat = re.search(
            r'<div class="stat">.*?</div>\s*</div>\s*</div>',
            html,
            flags=re.DOTALL,
        )
        if old_stat:
            items = re.findall(
                r'<div><b>(.*?)</b><span>(.*?)</span></div>', old_stat.group(0)
            )
            if items:
                cells = "".join(
                    f'<td style="text-align:center;padding:6px 12px;vertical-align:bottom;">'
                    f'<div style="font-size:28px;color:#0FB880;font-weight:bold;line-height:1.1;">{v}</div>'
                    f'<div style="font-size:12px;color:#999;letter-spacing:0.05em;margin-top:4px;">{l}</div>'
                    f'</td>'
                    for v, l in items
                )
                new_stat = (
                    f'<table style="width:100%;margin:32px 0;'
                    f'border-top:1px solid #E8E4D8;'
                    f'border-bottom:1px solid #E8E4D8;border-collapse:collapse;">'
                    f'<tr>{cells}</tr></table>'
                )
                html = html.replace(old_stat.group(0), new_stat)

    # 7. footer.foot
    def foot_replace(m: re.Match) -> str:
        inner = m.group(1)
        ps = re.findall(r'<p[^>]*>(.*?)</p>', inner, flags=re.DOTALL)
        ps_html = "".join(
            f'<p style="font-size:13px;color:#666;margin:4px 0;text-align:center;">{p}</p>'
            for p in ps
        )
        return (
            f'<section style="margin-top:56px;padding:20px;'
            f'background:#F8F8F6;border-radius:8px;text-align:center;">'
            f'{ps_html}</section>'
        )

    html = re.sub(
        r'<footer class="foot">(.*?)</footer>',
        foot_replace,
        html,
        flags=re.DOTALL,
    )

    # 8. p strong 颜色 (主色绿)
    html = re.sub(
        r'<p><strong>',
        '<p style="margin:14px 0;line-height:1.85;color:#1A1A1A;font-size:16px;"><strong style="color:#0FB880;">',
        html,
    )

    # 9. ol / li
    html = re.sub(
        r'<ol>',
        '<ol style="padding-left:24px;margin:14px 0;">',
        html,
    )
    html = re.sub(
        r'<ul>',
        '<ul style="padding-left:24px;margin:14px 0;">',
        html,
    )

    # 10. blockquote
    html = re.sub(
        r'<blockquote>',
        '<blockquote style="margin:20px 0;padding:4px 0 4px 18px;'
        'border-left:3px solid #666;color:#333;font-style:italic;">',
        html,
    )

    # 11. h3
    html = re.sub(
        r'<h3 style="color: var\(--ink\); font-size: 17px; margin: 24px 0 10px;">',
        '<h3 style="color:#1A1A1A;font-size:17px;margin:24px 0 10px;font-weight:bold;">',
        html,
    )

    # 12. 删 <style>...</style> 块
    html = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)

    # 13. 删 html/body/wrap 框架 (微信内部包)
    # 保留: 用户内容部分 (.wrap 内)
    # 实际上微信编辑器接受完整 HTML, 保留 wrap + html + body 也行
    # 但要确保最外层有 max-width 居中
    # 这里用 .wrap div 作为容器, 加 inline style
    html = re.sub(
        r'<div class="wrap">',
        '<div style="max-width:720px;margin:0 auto;padding:24px 20px 80px;">',
        html,
    )

    # 14. 移除 <code> inline style
    html = re.sub(
        r'<code>',
        '<code style="background:#F0F0F0;padding:1px 4px;font-size:13px;font-family:monospace;">',
        html,
    )

    # 15. 全局行高兜底: 在最外层 div 加
    # 已通过 .wrap inline 处理

    return html


def main():
    if not SRC.exists():
        print(f"ERR: {SRC} not found", file=sys.stderr)
        sys.exit(1)

    html = SRC.read_text()
    inlined = inline_styles(html)
    OUT.write_text(inlined)

    # 简单统计
    from html.parser import HTMLParser
    class V(HTMLParser):
        def __init__(self):
            super().__init__()
            self.errors = []; self.stack = []
        def handle_starttag(self, tag, attrs):
            if tag not in ('br', 'meta', 'link', 'img', 'input', 'hr'):
                self.stack.append(tag)
        def handle_endtag(self, tag):
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()
            else:
                self.errors.append(f"{tag}")

    p = V()
    p.feed(inlined)

    # 字数
    clean = re.sub(r'<[^>]+>', ' ', inlined)
    cjk = sum(1 for c in re.sub(r'\s', '', clean) if '一' <= c <= '鿿')

    # class 残留
    leftover = len(re.findall(r'class="[^"]+"', inlined))
    leftover_style = len(re.findall(r'<style', inlined))

    print(f"OK: {OUT} ({len(inlined)} bytes / {sum(1 for _ in open(OUT))} 行)")
    print(f"  parse: {'OK' if not p.errors and not p.stack else 'FAIL ' + str(p.errors[:2])}")
    print(f"  中文字: {cjk}")
    print(f"  class= 残留: {leftover} (应为 0)")
    print(f"  <style 残留: {leftover_style} (应为 0)")


if __name__ == "__main__":
    main()
