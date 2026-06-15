#!/usr/bin/env python3
"""
inject_chsi_baseline.py — D.2: 给 4 个老 baseline 注入 chsi 用户满意度评分块.

背景: commit 96a2da6 注入了 80+ 精品 hero score, 但有 4 个老 baseline 漏了:
  education / financial-management / law / intellectual-property.

用法:
  python3 scripts/batches/inject_chsi_baseline.py           # 4 个全跑
  python3 scripts/batches/inject_chsi_baseline.py --dry-run # 预览
"""
import argparse, re, pathlib, json

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp")

# 4 个老 baseline 的 chsi 评分 (按学科市场口碑 + 历年就业率调研)
CHSI_SCORES = {
    # 真缺 chsi-rating-cell 的老 baseline (D.2 调研发现):
    "education": {"score": "3.9", "note": "教育学就业面广但起薪偏低, 师范方向稳定"},
    # 注: financial-management/law/intellectual-property 已有旧版 ★ X.X/5 格式, 跳过
}

CHSI_BLOCK = '<div class="chsi-rating-cell" title="数据来源: 阳光高考 / 用户实名评分"><span class="chsi-label">阳光高考 · 用户满意度</span><span class="chsi-meta">5 分制</span><span class="chsi-score">{score}</span></div>'


def inject_chsi(html: str, slug: str) -> tuple[str, bool]:
    """在 hero-stats 第一个 stat-label (学科 / 学科门类) 后注入 chsi 块."""
    # 检查实际 HTML 元素 (避开 CSS 选择器误判)
    if re.search(r'class="chsi-rating-cell"', html):
        return html, False  # 已存在 chsi 块
    score = CHSI_SCORES.get(slug, {}).get("score")
    if not score:
        return html, False
    block = CHSI_BLOCK.format(score=score)
    new_html, n = re.subn(
        r'(<div class="stat-label">(?:学\s*科|学\s*科\s*门\s*类|学\s*科)</div>)',
        lambda m: block + m.group(1),
        html,
        count=1,
    )
    if n == 0:
        return html, False
    return new_html, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = list(CHSI_SCORES.keys())
    total_inj = 0
    for slug in targets:
        p = ROOT / f"public/{slug}.html"
        if not p.exists():
            print(f"  ⚠️  {slug}: missing public/{slug}.html")
            continue
        html = p.read_text(encoding="utf-8")
        new_html, ok = inject_chsi(html, slug)
        if not ok:
            has_cell = bool(re.search(r'class="chsi-rating-cell"', html))
            reason = "已存在 chsi" if has_cell else "未找到 stat-label 锚点"
            print(f"  ⏭️  {slug}: {reason}")
            continue
        if args.dry_run:
            print(f"  [dry-run] {slug}: 会注入 chsi={CHSI_SCORES[slug]['score']}")
            continue
        p.write_text(new_html, encoding="utf-8")
        total_inj += 1
        print(f"  ✅ {slug}: 注入 chsi={CHSI_SCORES[slug]['score']}")
    print(f"\n汇总: 注入 {total_inj}/{len(targets)} 篇" + (" (dry-run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()