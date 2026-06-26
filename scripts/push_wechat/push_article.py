#!/usr/bin/env python3
"""
通用公众号草稿推送脚本 (urllib 版本, 解决 requests 中文乱码 bug)

用法:
  python3 scripts/push_wechat/push_article.py \\
    --title "高考专业页生成器 16 天" \\
    --author "Claude Day 32" \\
    --digest "16 天演化, 质量分 7.0 → 9.05" \\
    --html docs/retrospectives/2026-06-26_skill-architecture_push.html \\
    --cover docs/retrospectives/assets/skill-arch-2026-06-26/og-card.png

依赖: .env 里有 WECHAT_APPID + WECHAT_SECRET
"""
import os
import sys
import json
import argparse
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
ENV = ROOT / ".env"
load_dotenv(ENV)

API = "https://api.weixin.qq.com/cgi-bin"


def get_token(appid: str, secret: str) -> str:
    url = f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if "access_token" not in data:
        raise RuntimeError(f"获取 token 失败: {data}")
    return data["access_token"]


def upload_cover(token: str, cover_path: Path) -> str:
    """上传封面图 (支持 PNG/JPG), 拿 thumb_media_id"""
    boundary = "----pyformdata-bound"
    mime = "image/png" if cover_path.suffix.lower() == ".png" else "image/jpeg"
    with open(cover_path, "rb") as f:
        cover_bytes = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{cover_path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8") + cover_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"{API}/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if "media_id" not in data:
        raise RuntimeError(f"封面上传失败: {data}")
    return data["media_id"]


def create_draft(
    token: str, title: str, author: str, digest: str,
    content_html: str, thumb_media_id: str,
) -> str:
    """创建草稿 (中文 UTF-8 安全)"""
    payload = {
        "articles": [{
            "title": title,
            "author": author,
            "digest": digest,
            "content": content_html,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
    }
    # 关键: ensure_ascii=False + UTF-8 bytes + 显式 charset 头
    # (用 requests.post 会中文乱码, urllib 不会)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = f"{API}/draft/add?access_token={token}"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if "media_id" not in data:
        raise RuntimeError(f"创建草稿失败: {data}")
    return data["media_id"]


def delete_draft(token: str, media_id: str) -> dict:
    """删除草稿 (用于重推前清旧)"""
    body = json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8")
    url = f"{API}/draft/delete?access_token={token}"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())


def verify_draft(token: str, media_id: str, key_phrases: list[str]) -> dict:
    """验证草稿内容 (读 API 回来对关键词)"""
    body = json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8")
    url = f"{API}/draft/get?access_token={token}"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    if "news_item" not in data:
        return {"ok": False, "reason": "无 news_item", "raw": data}

    news = data["news_item"][0]
    title = news.get("title", "")
    content = news.get("content", "")
    from html import unescape
    content_decoded = unescape(content)

    hits = {p: (p in content_decoded) for p in key_phrases}
    return {
        "ok": all(hits.values()),
        "title": title,
        "content_len": len(content_decoded),
        "hits": hits,
        "preview": content_decoded[:300],
    }


def main():
    ap = argparse.ArgumentParser(description="通用公众号草稿推送 (urllib)")
    ap.add_argument("--title", required=True, help="标题 (限 32 字节)")
    ap.add_argument("--author", default="Claude Day 32", help="作者")
    ap.add_argument("--digest", default="", help="摘要 (50-80 字)")
    ap.add_argument("--html", required=True, type=Path, help="内容 HTML 路径 (inline-style 版)")
    ap.add_argument("--cover", required=True, type=Path, help="封面图路径 (PNG/JPG)")
    ap.add_argument("--delete-old", default=None, help="先删除旧草稿的 media_id")
    args = ap.parse_args()

    title_bytes = len(args.title.encode("utf-8"))
    if title_bytes > 32:
        print(f"❌ 标题超长: {title_bytes} 字节 (限 32)", file=sys.stderr)
        sys.exit(1)

    appid = os.environ.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET")
    if not appid or not secret:
        print("❌ .env 缺 WECHAT_APPID 或 WECHAT_SECRET", file=sys.stderr)
        sys.exit(1)

    print(f"=== 推送公众号草稿 ===")
    print(f"标题: {args.title} ({title_bytes} 字节)")
    print(f"作者: {args.author}")
    print(f"内容: {args.html} ({args.html.stat().st_size:,} bytes)")
    print(f"封面: {args.cover} ({args.cover.stat().st_size:,} bytes)")

    token = get_token(appid, secret)
    print(f"\n✓ token: {token[:8]}...")

    if args.delete_old:
        r = delete_draft(token, args.delete_old)
        print(f"✓ 删旧草稿: {r}")

    thumb_id = upload_cover(token, args.cover)
    print(f"✓ 封面上传: {thumb_id[:30]}...")

    content_html = args.html.read_text(encoding="utf-8")
    media_id = create_draft(token, args.title, args.author, args.digest, content_html, thumb_id)
    print(f"\n✅ 草稿已创建: {media_id}")

    # 验证
    key_phrases = [args.title, "gaokao-major-explorer", "16 天演化", "9 步质量闭环",
                   "智能路由", "质量分从 7.0"]
    v = verify_draft(token, media_id, key_phrases)
    print(f"\n=== 验证 ===")
    print(f"返回标题: {v.get('title')!r}")
    print(f"内容长度: {v.get('content_len'):,}")
    print(f"关键词命中:")
    for k, hit in v.get("hits", {}).items():
        print(f"  {'✓' if hit else '✗'} '{k}'")
    if v.get("ok"):
        print(f"\n✅ 全部关键词命中, 中文无乱码")
        print(f"\n下一步: 登录微信公众平台 → 草稿箱 → 找这篇 → 检查预览 → 手动发布")
    else:
        print(f"\n❌ 验证失败: {v}")


if __name__ == "__main__":
    main()
