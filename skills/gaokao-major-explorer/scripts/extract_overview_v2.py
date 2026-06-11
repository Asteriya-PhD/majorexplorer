"""
extract_overview_v2.py — 把 v0 JSON 启发式转成 overview_v2 字段

策略:
- lede  ← summary (首段 or 全文)
- what.foundations ← curriculum["通用专业核心"] top N
- what.directions  ← what_you_learn "5 大方向" 段正则切分
- what.skills      ← what_you_learn "技能树三条" 段
- what.bonus       ← what_you_learn 末尾句
- fit.yes/no       ← who_fits 适合/不适合 段切分
- pitfalls[]       ← pitfalls 文本按 ❌ 切, 按 → 拆 myth/reality

Usage:
    python3 extract_overview_v2.py <json_path>             # 单个, dry-run (打印)
    python3 extract_overview_v2.py <json_path> --write     # 写回
    python3 extract_overview_v2.py <json_dir> --batch      # 批量
"""
import json
import os
import re
import sys
from pathlib import Path


def parse_pitfalls(text: str) -> list[dict]:
    """❌ 「myth」 → reality.  按 ❌ 切块, 块内按 → 拆 (myth, reality)."""
    if not text:
        return []
    out = []
    # 切成块 (保留首段 myth)
    blocks = re.split(r'❌\s*', text)
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        # 优先用 → 拆
        if '→' in b:
            myth_part, _, reality = b.partition('→')
        elif '：→' in b:  # 全角
            myth_part, _, reality = b.partition('：→')
        else:
            # 兜底: 找第一个「」or '""'
            m = re.match(r'「([^」]+)」\s*[:：\.]?\s*(.*)', b, re.DOTALL)
            if m:
                myth_part = m.group(1)
                reality = m.group(2)
            else:
                continue
        myth = re.sub(r'^[「"\']+|[」"\']+$', '', myth_part.strip())
        reality = reality.strip()
        if myth and reality and len(reality) > 8:
            out.append({"myth": myth[:120], "reality": reality[:600]})
    return out


def parse_fit(who_fits: str) -> tuple[list[str], list[str]]:
    """适合段: 第一段 yes; 第二段 (不适合以下几种人) 后是 no 列表."""
    if not who_fits:
        return [], []
    parts = re.split(r'\n\n', who_fits)
    yes_block = parts[0] if parts else ""
    no_block = "\n\n".join(parts[1:]) if len(parts) > 1 else ""

    # yes: 通用短语提取 — 去前缀 "适合" / "适合XX的" / "适合XX的人"，按「、,;/」切
    yes_list = _extract_phrases(yes_block)
    # no: 找 "不适合/慎选/慎重/慎报/不能/忌讳/不建议" 起点, 截到段尾
    no_list = []
    m_no = re.search(
        r'(?:不适合|慎选|慎重|慎报|不建议|慎[思入]?|不能|忌讳|忌入|避[免开]?)[^。]*[::]\s*(.+?)(?:\n\n|$)',
        who_fits, re.DOTALL
    )
    if m_no:
        no_list = _extract_phrases(m_no.group(1), prefer_short=True)
    if not no_list and no_block:
        no_list = _extract_phrases(no_block, prefer_short=True)
    return yes_list[:6], no_list[:6]


def _extract_phrases(text: str, prefer_short: bool = False) -> list[str]:
    """从散文段提取 4-80 字短语. 去前导 适合/不适合XX的人/慎选 等."""
    if not text:
        return []
    # 先砍掉所有完整配对括号 (含括号内逗号, 否则会误切)
    text = re.sub(r'[\(（][^)\）]*[\)）]', '', text)
    # 去前导 "适合 XXXX 的学生/的人" 前缀 (到第一个「,」「、」「，」)
    text = re.sub(r'^(?:适合|不适合|慎选|慎报|慎重|警告)[^,，、;；/]*[的]', '', text)
    text = re.sub(r'^(?:适合|不适合|慎选|慎报|慎重|警告)[^,，、;；/]*', '', text)
    # 按多种分隔符切 (句号 + 顿号 + 逗号 + 分号 + 斜杠)
    parts = re.split(r'[。、，,;；/]|\s{2,}', text)
    items = []
    for p in parts:
        p = p.strip()
        # 清理 包裹 「」或 引号
        p = re.sub(r'^[「"\']+|[」"\']+$', '', p).strip()
        # 截断半角/全角括号内容 (括号通常是解释, 砍掉)
        p = re.sub(r'\s*[\(（][^)\）]*[\)）].*$', '', p).strip()
        p = p.rstrip("。).）")
        if prefer_short and len(p) > 60:
            continue
        if 3 < len(p) < (60 if not prefer_short else 80) and not p.startswith(
            ("适合", "不适合", "慎选", "慎报", "慎重", "警告", "如果", "但", "而", "或", "即", "并", "且", "也", "的", "是")
        ):
            items.append(p)
    # 去重保序
    seen, out = set(), []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _split_to_items(text: str, leading: str = "") -> list[str]:
    """把段落切成 list. 优先看 「」包起来的, 其次按 ; 。切."""
    if not text:
        return []
    # 优先 「xxx」或'xxx'
    quoted = re.findall(r'「([^」]+)」', text)
    if len(quoted) >= 2:
        return [q.strip() for q in quoted if 4 < len(q) < 200][:6]
    # 否则按 「;」 「。」 「、」 切 (注意不要把句子切碎)
    # 用句号切, 再 trim
    sents = re.split(r'[。;；]', text)
    sents = [s.strip() for s in sents if s.strip() and len(s.strip()) > 4]
    return sents[:6]


def parse_foundations(curriculum: dict) -> list[str]:
    """取 通用专业核心 前 7 个 name."""
    block = curriculum.get("通用专业核心 (≈ 80% 院校覆盖)") or curriculum.get("通用专业核心") or []
    if isinstance(block, list):
        names = [c.get("name", "") for c in block if isinstance(c, dict)]
        # 清理: 去括号
        cleaned = []
        for n in names:
            n = re.sub(r'\s*\([^)]*\)\s*', '', n).strip()
            if n and n not in cleaned:
                cleaned.append(n)
        return cleaned[:7]
    return []


def parse_directions(what_you_learn: str, curriculum: dict | None = None, employment: list | None = None) -> list[dict]:
    """优先: what_you_learn 的 (1) name (desc) 段. 兜底: 5 校特色选修 + employment_direction."""
    if not what_you_learn:
        what_you_learn = ""
    # 1) 优先 (1) (2) 全角半角
    pat = re.compile(r'[（(]\s*(\d)\s*[)）]\s*([^（()\n]+?)\s*[（(]([^()]+)[)）]')
    out: list[dict] = []
    seen: set[str] = set()
    for m in pat.finditer(what_you_learn):
        name = m.group(2).strip()
        desc = m.group(3).strip()
        if name and name not in seen and 2 < len(name) < 30:
            seen.add(name)
            out.append({"name": name[:30], "desc": desc[:120]})
    if len(out) >= 2:
        return out[:6]
    # 2) 兜底: 5 校特色选修
    if curriculum:
        specials = curriculum.get("5 校特色选修 (按方向分流)") or curriculum.get("5 校特色选修") or []
        for c in specials[:5]:
            if isinstance(c, dict):
                full = c.get("name", "")
                # 格式: "清华大学 · xxx"
                if "·" in full:
                    school, _, topic = full.partition("·")
                    out.append({"name": topic.strip()[:30], "desc": f"{school.strip()} 特色方向"})
                else:
                    out.append({"name": full[:30], "desc": ""})
    if len(out) >= 2:
        return out[:6]
    # 3) 最后兜底: employment_direction 取前 5
    if employment:
        for e in employment[:5]:
            if isinstance(e, dict):
                out.append({"name": e.get("name", "")[:30], "desc": f"就业方向 {e.get('pct','')}%"})
    return out[:5]


def parse_skills(what_you_learn: str, curriculum: dict | None = None) -> list[str]:
    """优先: 「技能树」 段. 兜底: 抓 通用专业核心中含方法/分析/工具/统计/实验 等 hard skill 类名."""
    if not what_you_learn:
        what_you_learn = ""
    # 1) 优先 技能树 / 技能三条
    m = re.search(r'技能[树三][^:：]*[:：]\s*(.+?)(?:\n\n|\Z)', what_you_learn, re.DOTALL)
    if m:
        block = m.group(1)
        items = re.findall(r'[（(]\s*\d\s*[)）]\s*([^（()\n]+)', block)
        if items:
            return [i.strip() for i in items if 4 < len(i.strip()) < 80][:5]
    # 2) 兜底: 从 通用专业核心 找 hard skill 关键词 (分析/统计/实验/设计/技术/工具/编程/工程/写作)
    if curriculum:
        core = curriculum.get("通用专业核心 (≈ 80% 院校覆盖)") or curriculum.get("通用专业核心") or []
        hard_kw = r'(分析|统计|实验|设计|技术|工具|编程|工程|写作|建模|计算|诊断|测|检测|管理|策划|研究|开发|应用)'
        names = []
        for c in core:
            n = re.sub(r'\s*\([^)]*\)\s*', '', c.get("name", "")).strip()
            if n and 2 < len(n) < 25 and re.search(hard_kw, n):
                names.append(n)
        if names:
            return names[:5]
        # 仍空 → 取前 5 个核心课
        for c in core[:5]:
            n = re.sub(r'\s*\([^)]*\)\s*', '', c.get("name", "")).strip()
            if n and n not in names:
                names.append(n)
        return names[:5]
    return []


def parse_bonus(what_you_learn: str, summary: str = "") -> str:
    """取末尾 1-2 句作为 bonus."""
    if what_you_learn:
        sents = [s.strip() for s in re.split(r'[。\n]', what_you_learn) if s.strip()]
        # 取最后 1-2 句
        tail = "。".join(sents[-2:]) if len(sents) >= 2 else sents[-1] if sents else ""
        if tail and 20 < len(tail) < 400:
            return tail + ("。" if not tail.endswith("。") else "")
    return ""


def extract_v2(data: dict) -> dict:
    """主入口: v0 → v2 启发式提取."""
    summary = data.get("summary", "")
    what_you_learn = data.get("what_you_learn", "")
    who_fits = data.get("who_fits", "")
    pitfalls_text = data.get("pitfalls", "")
    curriculum = data.get("curriculum", {})

    lede = summary
    what = {
        "foundations": parse_foundations(curriculum),
        "directions": parse_directions(what_you_learn, curriculum, data.get("employment_direction")),
        "skills": parse_skills(what_you_learn, curriculum),
        "bonus": parse_bonus(what_you_learn, summary),
    }
    yes_list, no_list = parse_fit(who_fits)
    pitfalls = parse_pitfalls(pitfalls_text)

    return {
        "lede": lede,
        "what": what,
        "fit": {"yes": yes_list, "no": no_list},
        "pitfalls": pitfalls,
    }


def quality_report(v2: dict) -> dict:
    """报告各字段的填充率."""
    w = v2.get("what", {})
    f = v2.get("fit", {})
    p = v2.get("pitfalls", [])
    return {
        "lede_chars": len(v2.get("lede", "")),
        "foundations": len(w.get("foundations", [])),
        "directions": len(w.get("directions", [])),
        "skills": len(w.get("skills", [])),
        "bonus_chars": len(w.get("bonus", "")),
        "fit_yes": len(f.get("yes", [])),
        "fit_no": len(f.get("no", [])),
        "pitfalls": len(p),
    }


def process_file(path: Path, write: bool = False) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "overview_v2" in data:
        return {"path": str(path), "status": "skipped (already has v2)"}
    v2 = extract_v2(data)
    rep = quality_report(v2)
    data["overview_v2"] = v2
    if write:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {"path": str(path), "status": "ok", "report": rep}


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    write = "--write" in args
    batch = "--batch" in args
    args = [a for a in args if not a.startswith("--")]

    if batch:
        d = Path(args[0])
        files = sorted(d.glob("*.json"))
        for fp in files:
            if "demo" in fp.name:
                continue
            r = process_file(fp, write=write)
            print(json.dumps(r, ensure_ascii=False))
    else:
        for a in args:
            r = process_file(Path(a), write=write)
            print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
