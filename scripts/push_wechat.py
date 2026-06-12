#!/usr/bin/env python3
"""
push_wechat.py — 推送公众号草稿箱: Major Explorer 上线推文

步骤:
  1. 获取 access_token
  2. 上传 3 张图 (wechat-cover.png 封面 + cs.png + medicine.png 正文)
  3. 构造 HTML 正文 (按 wechat-article-layout skill 规范)
  4. 创建草稿
  5. 读取草稿 + 解码 + 验证 (检查中文是否乱码)

环境变量:
  WECHAT_APPID    公众号 AppID
  WECHAT_SECRET   公众号 AppSecret
  WECHAT_IP       当前公网 IP (需要在公众号后台白名单)
"""
import os
import sys
import json
import requests
from pathlib import Path

# ── 配置 ──
APPID = os.environ.get("WECHAT_APPID", "").strip()
SECRET = os.environ.get("WECHAT_SECRET", "").strip()

REPO = Path(__file__).resolve().parents[1]
PUBLIC = REPO / "public"
COVER = PUBLIC / "wechat-cover.png"
IMG1 = PUBLIC / "og" / "cs.png"
IMG2 = PUBLIC / "og" / "medicine.png"

TITLE = "看清专业, 比填好志愿更重要"
DIGEST = "高考出分前, 我做了一个叫 Major Explorer 的志愿项目。大厂做'分数能上哪', 我做'18 岁看清专业'。一个专业决定 4 年大学 + 30 年职业, 比一次填报重要得多。"

# ── HTML 正文 (按 wechat-article-layout skill 规范) ──
HTML = """
<section style="background:#FFFFFF;padding:24px 20px;">
  <p style="font-size:16px;line-height:1.85;color:#1A1A1A;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    高考出分前, 我做了一件有点"轴"的事: 跟几个朋友, 花了几天, 做了一个叫 Major Explorer 的高考志愿项目。
  </p>
</section>

<section style="background:#363A3B;padding:24px 16px;text-align:center;">
  <img src="{IMG1_URL}" style="width:90%;max-width:320px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.4);"/>
  <p style="color:rgba(255,255,255,0.65);font-size:13px;margin-top:10px;">计算机科学与技术 · 70+ 精品专业之一</p>
</section>

<section style="background:#FFFFFF;padding:24px 20px;">
  <p style="font-size:16px;line-height:1.85;color:#1A1A1A;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    千问下场做志愿, 是这几天的事。我做这个项目的时候, 还没听到这消息, 也不打算跟他们比什么方向。
  </p>
  <p style="font-size:16px;line-height:1.85;color:#1A1A1A;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    大厂做的是"分数能上哪"——一分一段表, 96 志愿生成, 概率测算, 这些都很成熟。
  </p>
  <p style="font-size:16px;line-height:1.85;color:#0FB880;font-weight:bold;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    我想做的是"18 岁看清专业"。
  </p>
  <p style="font-size:16px;line-height:1.85;color:#1A1A1A;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    一个专业决定的是 4 年大学 + 30 年职业, 比一次填报重要得多。太多学生毕业才发现自己学的不是自己以为的:
  </p>
  <ul style="font-size:15px;line-height:1.85;color:#333;margin:0 0 14px 0;padding-left:2em;">
    <li>选了 CS"AI 方向", 才发现很多岗是数据标注 + 调参, 核心岗留给清北浙 + 顶会论文的人</li>
    <li>选了工商管理, 才发现双非 ≈ 销售岗, 真正管培要 985 + 强实习, 名校才是入场券</li>
    <li>选了农学, 才发现"冷门好考"是假象——中国农大 2024 河北物理组最低 612 分 (全省前 1.5%)</li>
  </ul>
  <p style="font-size:16px;line-height:1.85;color:#1A1A1A;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    我希望他们在选之前, 就看清这些。
  </p>
</section>

<section style="background:rgba(15,184,128,0.08);padding:16px 20px;">
  <div style="background:#FFFFFF;border-radius:8px;padding:14px 16px;border-left:4px solid #0FB880;margin-bottom:10px;">
    <p style="font-size:15px;color:#333;line-height:1.75;margin:0;">
      所以我们做了 68 个精品专业的深度介绍: 学什么、什么人适合、避哪些坑、就业方向、院校推荐、校友真实反馈。
    </p>
  </div>
</section>

<section style="background:#363A3B;padding:24px 16px;text-align:center;">
  <img src="{IMG2_URL}" style="width:90%;max-width:320px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.4);"/>
  <p style="color:rgba(255,255,255,0.65);font-size:13px;margin-top:10px;">临床医学 · 70+ 精品专业之一</p>
</section>

<section style="background:#FFFFFF;padding:24px 20px;">
  <p style="font-size:16px;line-height:1.85;color:#1A1A1A;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    每一个专业都反复打磨——校友访谈, 6-7 个误区, 数据来源, 不确定性标注。13 个主题, 从计算机到农林到艺术到公安到法医学, 一个一个讲透。
  </p>
</section>

<section style="background-color:#fde68a;border-radius:8px;padding:18px 20px;border:2px solid #f59e0b;margin:16px 20px;">
  <p style="font-size:15px;color:#333;line-height:1.75;margin:0 0 8px;"><strong>📢 我们做了一个决定: 纯公益, 不变现。</strong></p>
  <p style="font-size:15px;color:#333;line-height:1.75;margin:0;">
    不接广告, 不开付费咨询, 不卖"卡位"。教师身份也没放进去 (避免被过度解读), 团队页只写"几个有高考经验的产品/数据/工程朋友"。
  </p>
</section>

<section style="background:#FFFFFF;padding:24px 20px;">
  <p style="font-size:16px;line-height:1.85;color:#1A1A1A;margin:0 0 14px 0;text-align:justify;text-indent:2em;">
    距离湖北出分还有 11 天。
  </p>
</section>

<section style="background:rgba(15,184,128,0.08);padding:18px 20px;text-align:center;">
  <p style="font-size:15px;color:#0FB880;font-weight:bold;margin:0 0 8px;">📌 阅读原文</p>
  <p style="font-size:14px;color:#333;margin:0;">https://majorexplorer.com</p>
  <p style="font-size:15px;color:#FF6B35;margin:14px 0 0 0;">❤️ 转发给身边的高三孩子和家长</p>
</section>
"""


def get_token() -> str:
    url = "https://api.weixin.qq.com/cgi-bin/token"
    r = requests.get(url, params={"grant_type": "client_credential", "appid": APPID, "secret": SECRET}, timeout=15)
    r.raise_for_status()
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token 获取失败: {data}")
    return data["access_token"]


def upload_image(token: str, path: Path, name: str) -> dict:
    """上传永久素材, 返回 {url, media_id}"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(path, "rb") as f:
        r = requests.post(url, files={"media": (name, f, "image/png")}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "media_id" not in data or "url" not in data:
        raise RuntimeError(f"{name} 上传失败: {data}")
    return {"url": data["url"], "media_id": data["media_id"]}


def create_draft(token: str, cover_media_id: str, img1_url: str, img2_url: str) -> str:
    body = HTML.replace("{IMG1_URL}", img1_url).replace("{IMG2_URL}", img2_url)
    # 必须 ensure_ascii=False
    payload = {
        "articles": [
            {
                "title": TITLE,
                "author": "Major Explorer",
                "digest": DIGEST,
                "content": body,
                "thumb_media_id": cover_media_id,  # 封面用 media_id, 不是 url
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }
        ]
    }
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    r = requests.post(
        url,
        data=raw,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "media_id" not in data:
        raise RuntimeError(f"草稿创建失败: {data}")
    return data["media_id"]


def verify_draft(token: str, media_id: str) -> bool:
    """读取草稿, 解码 (Latin-1 → UTF-8), 验证关键文本无乱码."""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    r = requests.post(url, json={"offset": 0, "count": 5}, timeout=15)
    r.raise_for_status()
    data = r.json()
    items = data.get("item", [])
    target = next((it for it in items if it.get("media_id") == media_id), None)
    if not target:
        return False
    raw = target["content"]["news_item"][0]["content"]
    decoded = raw.encode("latin1").decode("utf-8")
    if "看清专业" not in decoded or "majorexplorer.com" not in decoded:
        print(f"⚠️  草稿内容校验失败, 可能乱码")
        print(f"原始: {raw[:200]}")
        print(f"解码: {decoded[:200]}")
        return False
    return True


def main():
    if not APPID or not SECRET:
        print("❌ 缺少 WECHAT_APPID 或 WECHAT_SECRET 环境变量")
        print("设置方法:")
        print("  export WECHAT_APPID='wx123...'")
        print("  export WECHAT_SECRET='abc...'")
        print("或:")
        print("  WECHAT_APPID='wx123...' WECHAT_SECRET='abc...' python3 scripts/push_wechat.py")
        sys.exit(1)

    for f in [COVER, IMG1, IMG2]:
        if not f.exists():
            print(f"❌ 找不到文件: {f}")
            sys.exit(1)

    print("🔑 获取 access_token...")
    token = get_token()
    print(f"   ✅ token: {token[:20]}...")

    print("📤 上传 3 张图 (永久素材)...")
    cover = upload_image(token, COVER, "wechat-cover.png")
    print(f"   ✅ 封面: media_id={cover['media_id'][:30]}...")
    img1 = upload_image(token, IMG1, "cs.png")
    print(f"   ✅ 图1 (cs): {img1['url'][:60]}...")
    img2 = upload_image(token, IMG2, "medicine.png")
    print(f"   ✅ 图2 (medicine): {img2['url'][:60]}...")

    print("📝 创建草稿...")
    media_id = create_draft(token, cover["media_id"], img1["url"], img2["url"])
    print(f"   ✅ media_id: {media_id}")

    print("🔍 验证草稿 (无乱码)...")
    if verify_draft(token, media_id):
        print("   ✅ 验证通过, 中文正常")
    else:
        print("   ⚠️  验证失败, 可能在草稿箱里看到乱码, 需要在微信编辑器手动修正")

    print(f"\n🎉 草稿已创建! media_id: {media_id}")
    print(f"📱 打开微信公众平台 → 草稿箱 → 找到 '{TITLE}' → 预览 → 群发")


if __name__ == "__main__":
    main()
