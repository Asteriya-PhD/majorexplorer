#!/usr/bin/env python3
"""inject_theme_colors.py — 把 render_mobile.py 的 THEMES 4 色注入 manifest.json

每个 major 加 theme_color: {primary, deep, soft, gold} 字段,
mobile detail.js 启动时读这 4 色, setProperty 注入到 --theme 等 CSS variable。

- Source of truth: scripts/render_mobile.py 的 THEMES 字典 (单一来源)
- 目标: public/data/manifest.json
- 备份: 写回前自动备份到 manifest.json.bak (上次成功的版本)
- 幂等: 重复运行结果一致 (覆盖式)
- 失败回滚: 写回失败自动恢复 .bak

Usage:
  python3 scripts/inject_theme_colors.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from render_mobile import THEMES  # noqa: E402

MANIFEST_PATH = ROOT / "public/data/manifest.json"
BACKUP_PATH = ROOT / "public/data/manifest.json.bak"


def main():
    if not MANIFEST_PATH.exists():
        print(f"❌ manifest.json 不存在: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ manifest.json 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    majors = manifest.get("majors", [])
    if not majors:
        print("❌ manifest.majors 为空", file=sys.stderr)
        sys.exit(1)

    updated = 0
    skipped = 0
    for m in majors:
        style = m.get("style")
        if not style or style not in THEMES:
            skipped += 1
            continue
        primary, deep, soft, gold = THEMES[style]
        m["theme_color"] = {
            "primary": primary,
            "deep": deep,
            "soft": soft,
            "gold": gold,
        }
        updated += 1

    # 备份当前 (将被覆盖的) manifest
    BACKUP_PATH.write_text(raw, encoding="utf-8")

    # 写回
    try:
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        # 失败: 恢复 .bak
        if BACKUP_PATH.exists():
            MANIFEST_PATH.write_text(BACKUP_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"❌ 写回失败, 已恢复备份: {e}", file=sys.stderr)
        sys.exit(1)

    # 备份已无效 (下次跑会再次备份), 删掉避免误回滚
    if BACKUP_PATH.exists():
        BACKUP_PATH.unlink()

    print(f"✅ {updated}/{len(majors)} majors 注入 theme_color")
    if skipped:
        print(f"⚠ {skipped} majors 跳过 (style 字段缺失或不在 THEMES 中)")
    # 抽样打印前 3 条供人眼验证
    print("\n抽样 (前 3 条):")
    for m in majors[:3]:
        tc = m.get("theme_color")
        print(f"  {m['slug']:35s} style={m.get('style', '-'):12s} → primary={tc.get('primary') if tc else '—'}")


if __name__ == "__main__":
    main()
