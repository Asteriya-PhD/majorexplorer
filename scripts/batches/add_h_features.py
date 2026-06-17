"""add_h_features.py — Day 3 94 篇补 H 阶段 features (shared.css + topbar.js + og: meta)
- 8 OK 文件已加 (1.txt original 8 dirty files)
- 86 missing: 39 Team A + 47 Team B
- 模式:
  - <link shared.css> 插入 <style> 前
  - <script topbar.js> 插入 </body> 前
  - og: meta (canonical + og:url/site_name/title/description/type) 注入 <head>
- 幂等: 已含 features 的不重复插入
- 集成: deploy_to_public.py 末尾自动调本脚本, 防止 re-render 静默丢失
"""
import sys
from pathlib import Path

# 复用 inject_seo 的 og: 注入逻辑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from inject_seo import inject_seo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC = ROOT / "public"

TEAM_A_CSV = ROOT / "scripts/batches/day3_team_a.csv"
TEAM_B_CSV = ROOT / "scripts/batches/day3_team_b.csv"

SHARED_CSS_LINK = '<link rel="stylesheet" href="/css/shared.css">'
TOPBAR_JS_SCRIPT = '  <script src="/js/topbar.js"></script>'


def add_h_features(slug: str) -> tuple[bool, str]:
    """Add shared.css + topbar.js + og: meta to public/<slug>.html if missing.
    Returns (changed, reason)."""
    p = PUBLIC / f"{slug}.html"
    if not p.exists():
        return False, "MISSING"
    text = p.read_text(encoding="utf-8")
    original = text
    changes = []

    # 1. shared.css link — insert before first <style>
    if SHARED_CSS_LINK not in text:
        idx = text.find("<style>")
        if idx == -1:
            return False, "NO_STYLE_TAG"
        text = text[:idx] + SHARED_CSS_LINK + "\n" + text[idx:]
        changes.append("+shared.css")

    # 2. topbar.js script — insert before </body>
    if "topbar.js" not in text:
        idx = text.rfind("</body>")
        if idx == -1:
            return False, "NO_BODY_CLOSE"
        text = text[:idx] + TOPBAR_JS_SCRIPT + "\n" + text[idx:]
        changes.append("+topbar.js")

    # 写回 shared.css + topbar.js 修改
    if text != original:
        p.write_text(text, encoding="utf-8")
        original = text  # 更新 reference, 为 og: 步骤准备

    # 3. og: meta (canonical + og:url/site_name/title/description/type)
    #    inject_seo 内部幂等, 无 og: 时注入, 有则跳过
    seo_changed, seo_msg = inject_seo(p)
    if seo_changed:
        changes.append("+og:meta")

    if changes:
        return True, ", ".join(changes)
    return False, "ALREADY_OK"


def main():
    slugs = []
    for csv in (TEAM_A_CSV, TEAM_B_CSV):
        for line in csv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("slug"):
                continue
            slug = line.split(",")[0].strip()
            if slug:
                slugs.append(slug)

    changed = 0
    skipped = 0
    issues = []
    for slug in slugs:
        ok, reason = add_h_features(slug)
        if ok:
            changed += 1
        else:
            skipped += 1
            if reason not in ("ALREADY_OK",):
                issues.append(f"{slug}: {reason}")

    print(f"✅ 补 H features: {changed} 篇已改, {skipped} 篇跳过")
    if issues:
        print(f"⚠️  异常 {len(issues)}:")
        for s in issues:
            print(f"  {s}")


if __name__ == "__main__":
    main()
