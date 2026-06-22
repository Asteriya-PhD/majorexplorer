#!/usr/bin/env python3
"""
scrub_jiaoyubu.py — 「教育部」字样扫尾脚本

扫描 skills/gaokao-major-explorer/data/curated/ 目录下所有 HTML 与 JSON 文件,
统计「教育部」出现位置, 标注合规 / 违规, 生成 Markdown 报告。

重要: 本脚本**只读不写**, 不修改任何原文件, 只生成报告。
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ─────────────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SCAN_DIR = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
REPORT_PATH = SCAN_DIR / "data_scrub_report.md"
KEYWORD = "教育部"

# 合规引用 (白名单) — 命中即合规, 保留
COMPLIANT_PATTERNS = [
    (r"教育部\s*第四轮学科评估", "学科评估数据源 (公开)"),
    (r"教育部\s*第五轮学科评估", "学科评估数据源 (公开)"),
    (r"教育部\s*学位中心", "官方数据源标注"),
    (r"教育部.{0,30}招生工作.{0,10}通知", "政策文件引用"),
    (r"教育部.{0,30}学科评估", "学科评估数据源 (公开)"),
    (r"教育部.{0,15}教学指导委员会", "政策制定方引用"),
]

# 违规暗示 (黑名单) — 命中即违规, 需替换
VIOLATION_PATTERNS = [
    (r"教育部\s*认证", "「教育部认证」 → 替换为「学科评估认证」"),
    (r"教育部\s*推荐", "「教育部推荐」 → 替换为「公开排行榜」"),
    (r"教育部\s*主办", "「教育部主办」 → 替换为「国家教学指导委员会」"),
    (r"教育部\s*官方", "「教育部官方」 → 替换为「公开官方」"),
    (r"教育部\s*认可", "「教育部认可」 → 替换为「公开评价」"),
    (r"教育部\s*指定", "「教育部指定」 → 替换为「公开遴选」"),
    (r"教育部\s*认证", "「教育部认证」"),
    (r"教育部\s*背书", "「教育部背书」 → 替换为「公开评价」"),
    (r"教育部\s*授权", "「教育部授权」 → 替换为「公开数据」"),
]

# 上下文窗口: 命中位置前后各 N 个字符
CONTEXT_WINDOW = 40


# ─────────────────────────────────────────────────────
# 扫描逻辑
# ─────────────────────────────────────────────────────
def classify_context(text: str, pos: int) -> tuple[str, str]:
    """根据命中位置的上下文判定合规 / 违规, 返回 (status, reason)。"""
    # 优先匹配违规模式
    for pat, reason in VIOLATION_PATTERNS:
        if re.search(pat, text[max(0, pos - 5): pos + len(KEYWORD) + 10]):
            return ("VIOLATION", reason)
    # 然后匹配合规模式
    for pat, reason in COMPLIANT_PATTERNS:
        m = re.search(pat, text)
        if m and abs(m.start() - pos) < 20:
            return ("COMPLIANT", reason)
    # 默认: 模糊引用, 需人工复核
    return ("REVIEW", "无明确白/黑名单命中, 需人工复核 (可能是说明性引用)")


def extract_context(text: str, pos: int, keyword_len: int = 3) -> str:
    """提取命中位置的上下文片段, 去除多余空白。"""
    start = max(0, pos - CONTEXT_WINDOW)
    end = min(len(text), pos + keyword_len + CONTEXT_WINDOW)
    snippet = text[start:end].replace("\n", " ").replace("\r", " ")
    snippet = re.sub(r"\s+", " ", snippet).strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def scan_file(path: Path) -> list[dict]:
    """扫描单个文件, 返回命中记录列表。"""
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="gbk")
        except Exception as e:
            print(f"[WARN] 无法读取 {path.name}: {e}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"[WARN] 读取 {path.name} 失败: {e}", file=sys.stderr)
        return []

    hits = []
    for m in re.finditer(KEYWORD, content):
        pos = m.start()
        status, reason = classify_context(content, pos)
        hits.append({
            "file": path.name,
            "rel_path": str(path.relative_to(ROOT)),
            "line": content[:pos].count("\n") + 1,
            "pos": pos,
            "context": extract_context(content, pos, len(KEYWORD)),
            "status": status,
            "reason": reason,
        })
    return hits


def scan_all() -> list[dict]:
    """扫描 SCAN_DIR 下所有 .html / .json 文件。"""
    if not SCAN_DIR.exists():
        print(f"[ERROR] 扫描目录不存在: {SCAN_DIR}", file=sys.stderr)
        return []
    all_hits = []
    targets = sorted(
        list(SCAN_DIR.glob("*.html")) + list(SCAN_DIR.glob("*.json"))
    )
    for p in targets:
        all_hits.extend(scan_file(p))
    return all_hits


# ─────────────────────────────────────────────────────
# 报告生成
# ─────────────────────────────────────────────────────
def group_by_file(hits: list[dict]) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for h in hits:
        grouped[h["rel_path"]].append(h)
    return dict(sorted(grouped.items()))


def render_report(hits: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# 「教育部」字样扫尾报告")
    lines.append("")
    lines.append(f"> 自动生成于 `scripts/scrub_jiaoyubu.py` — {os.popen('date "+%Y-%m-%d %H:%M:%S"').read().strip()}")
    lines.append("> 本报告**只读不写**, 不修改任何原文件。")
    lines.append("")

    # 总体统计
    total = len(hits)
    by_status = defaultdict(int)
    for h in hits:
        by_status[h["status"]] += 1
    files_with_hits = len({h["rel_path"] for h in hits})

    lines.append("## 一、总体统计")
    lines.append("")
    lines.append(f"- 扫描目录: `skills/gaokao-major-explorer/data/curated/`")
    lines.append(f"- 扫描文件总数: {len(list(SCAN_DIR.glob('*.html'))) + len(list(SCAN_DIR.glob('*.json')))}")
    lines.append(f"- 含「教育部」字样的文件数: **{files_with_hits}**")
    lines.append(f"- 命中总次数: **{total}**")
    lines.append("")
    lines.append("| 状态 | 数量 | 占比 | 处理建议 |")
    lines.append("|------|------|------|---------|")
    total_safe = total or 1
    lines.append(f"| COMPLIANT (合规引用) | {by_status['COMPLIANT']} | {by_status['COMPLIANT']*100//total_safe}% | 保留 |")
    lines.append(f"| REVIEW (需人工复核) | {by_status['REVIEW']} | {by_status['REVIEW']*100//total_safe}% | 逐条审视 |")
    lines.append(f"| VIOLATION (违规暗示) | {by_status['VIOLATION']} | {by_status['VIOLATION']*100//total_safe}% | 立即替换 |")
    lines.append("")

    # 替换词表
    lines.append("## 二、替换词表")
    lines.append("")
    lines.append("| 违规措辞 | 推荐替换 | 理由 |")
    lines.append("|---------|---------|------|")
    lines.append("| 教育部认证 | 学科评估认证 | 本站非认证机构, 无权认证 |")
    lines.append("| 教育部推荐 | 公开排行榜 | 教育部不推荐具体专业 |")
    lines.append("| 教育部主办 | 国家教学指导委员会 | 主语精确化 |")
    lines.append("| 教育部官方 | 公开官方 | 避免机构冒充 |")
    lines.append("| 教育部认可 | 公开评价 | 避免暗示背书 |")
    lines.append("| 教育部指定 | 公开遴选 | 避免暗示背书 |")
    lines.append("| 教育部背书 | 公开评价 | 避免暗示背书 |")
    lines.append("| 教育部授权 | 公开数据 | 避免暗示合作 |")
    lines.append("")

    # 合规白名单
    lines.append("## 三、合规白名单 (予以保留)")
    lines.append("")
    lines.append("下列模式属于公开数据引用 / 政策文本引用, **予以保留**:")
    lines.append("")
    lines.append("- 「教育部第四轮学科评估」「教育部第五轮学科评估」 — 学科评估数据源")
    lines.append("- 「教育部学位中心」 — 官方数据源标注")
    lines.append("- 「教育部 X 年普通高等学校招生工作通知」 — 政策文件引用")
    lines.append("- 「教育部 X 教学指导委员会」 — 政策制定方引用")
    lines.append("- 「教育部 X 学科评估」 — 学科评估数据源")
    lines.append("")

    # 按文件分组的详细列表
    lines.append("## 四、详细命中清单 (按文件分组)")
    lines.append("")

    grouped = group_by_file(hits)
    if not grouped:
        lines.append("_无命中。_")
        lines.append("")

    for rel_path, file_hits in grouped.items():
        lines.append(f"### {rel_path}")
        lines.append("")
        lines.append(f"- 命中次数: **{len(file_hits)}**")
        n_v = sum(1 for h in file_hits if h["status"] == "VIOLATION")
        n_r = sum(1 for h in file_hits if h["status"] == "REVIEW")
        n_c = sum(1 for h in file_hits if h["status"] == "COMPLIANT")
        lines.append(f"- 违规: {n_v} / 复核: {n_r} / 合规: {n_c}")
        lines.append("")

        # 状态用 emoji 前缀标识
        status_emoji = {
            "VIOLATION": "[违规]",
            "REVIEW": "[复核]",
            "COMPLIANT": "[合规]",
        }
        # 按行号排序
        file_hits.sort(key=lambda h: h["line"])
        for h in file_hits:
            emoji = status_emoji.get(h["status"], "[?]")
            lines.append(
                f"- {emoji} 第 {h['line']} 行 · {h['reason']}"
            )
            lines.append(f"  > `{h['context']}`")
        lines.append("")

    # 违规项汇总
    violations = [h for h in hits if h["status"] == "VIOLATION"]
    lines.append("## 五、违规项汇总 (需立即处理)")
    lines.append("")
    if not violations:
        lines.append("_未发现违规暗示, 全站通过。_")
    else:
        lines.append(f"共 **{len(violations)}** 处违规, 按文件汇总:")
        lines.append("")
        viol_by_file = defaultdict(list)
        for v in violations:
            viol_by_file[v["rel_path"]].append(v)
        for rel_path, vs in sorted(viol_by_file.items()):
            lines.append(f"### {rel_path} ({len(vs)} 处)")
            lines.append("")
            for v in vs:
                lines.append(
                    f"- 第 {v['line']} 行: {v['reason']}"
                )
                lines.append(f"  > `{v['context']}`")
            lines.append("")

    # 复核项汇总
    reviews = [h for h in hits if h["status"] == "REVIEW"]
    lines.append("## 六、复核项汇总 (建议人工审视)")
    lines.append("")
    if not reviews:
        lines.append("_无复核项。_")
    else:
        lines.append(f"共 **{len(reviews)}** 处需要人工复核 (多为说明性引用, 一般无需修改):")
        lines.append("")
        rev_by_file = defaultdict(list)
        for r in reviews:
            rev_by_file[r["rel_path"]].append(r)
        for rel_path, rs in sorted(rev_by_file.items()):
            lines.append(f"### {rel_path} ({len(rs)} 处)")
            lines.append("")
            for r in rs:
                lines.append(f"- 第 {r['line']} 行")
                lines.append(f"  > `{r['context']}`")
            lines.append("")

    # 附录
    lines.append("## 七、附录 · 扫描参数")
    lines.append("")
    lines.append(f"- 关键字: `{KEYWORD}`")
    lines.append(f"- 上下文窗口: ±{CONTEXT_WINDOW} 字符")
    lines.append(f"- 白名单模式数: {len(COMPLIANT_PATTERNS)}")
    lines.append(f"- 黑名单模式数: {len(VIOLATION_PATTERNS)}")
    lines.append(f"- 扫描文件类型: `.html` / `.json`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 本报告由 `scripts/scrub_jiaoyubu.py` 自动生成。")
    lines.append("> 脚本**只生成报告, 不修改任何原文件**。")
    lines.append("> 如需修改违规项, 请逐条人工确认后, 使用编辑工具调整, 再重新跑本脚本验证。")
    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────
def main() -> int:
    print(f"[INFO] 扫描目录: {SCAN_DIR}")
    print(f"[INFO] 关键字:   {KEYWORD}")
    print(f"[INFO] 报告输出: {REPORT_PATH}")
    print()

    hits = scan_all()
    print(f"[INFO] 命中总数: {len(hits)}")

    report = render_report(hits)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"[INFO] 报告已写入: {REPORT_PATH}")
    print()

    # 简要统计输出
    by_status = defaultdict(int)
    for h in hits:
        by_status[h["status"]] += 1
    print(f"[STATS] 合规: {by_status['COMPLIANT']} | "
          f"复核: {by_status['REVIEW']} | "
          f"违规: {by_status['VIOLATION']} | "
          f"文件数: {len({h['rel_path'] for h in hits})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
