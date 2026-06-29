# 微信公众号推送脚本

将公众号发布版 HTML (`docs/retrospectives/2026-06-26_wechat-parents-push.html`)
+ 封面图 (`docs/retrospectives/assets/wechat-cover-final.png`)
推送到公众号草稿箱。

## 一次性配置

**1. 在项目根目录 `.env` 末尾加** (`.env` 已在 .gitignore, 不会泄露):

```bash
WECHAT_APPID=your_appid_here
WECHAT_SECRET=your_secret_here
```

**2. 公网出口 IP 加白名单**

微信公众号平台 → 开发 → 基本配置 → IP 白名单 → 加入你跑脚本这台机器的公网 IP
(本地跑: `curl ifconfig.me` 查出口 IP, 临时调试用, 上线前改成服务器固定 IP)

**3. 公众号类型**

API `draft/add` 需要**认证订阅号**或**服务号**。未认证订阅号 / 个人订阅号调不到。

## 每次发布流程

```bash
# Step 1: 把发布版 HTML 转成微信可推送的 inline-style 版
python3 scripts/push_wechat/inline_styles.py

# Step 2: 推送到草稿箱
python3 scripts/push_wechat/push_draft.py
```

## 推送结果

成功后输出:
```
✅ 草稿已创建: {media_id}
```

**下一步**:
1. 登录微信公众平台 → 草稿箱
2. 找到这篇, 检查预览
3. **API 标题限 32 字节(10 汉字)**, 当前标题 `帮 600 个高考专业, 写了一年的"真实"` 26 字节 ✓
4. 草稿改封面 / 改内容: 删了重建 (更新接口有编码坑, 见 skill)
5. 确认无误后: 公众号后台手动点"发布"

## 已踩的坑 (来自 wechat-article-layout skill)

1. **中文乱码**: 必须 `json.dumps(ensure_ascii=False).encode('utf-8')` + 显式 charset=utf-8
2. **黄色背景框**: 用 `<section>` + `background-color`, 不用 `<div>` + `background`
3. **class 残留**: 微信编辑器会过滤部分 CSS, 关键样式务必内联 (本脚本自动转)
4. **access_token 2h 有效**: 每次操作前重新拿
5. **更新草稿有编码坑**: 改文字内容用删了重建, 不用 update
6. **已发布不能改**: 只能在公众号后台手动编辑
