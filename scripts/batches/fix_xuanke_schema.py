"""fix_xuanke_schema.py — 修复 xuanke_req_list schema: per-subject → per-combination

2026-06-17: 136 篇用错 schema (per-subject 单科 sum 可超 100%).
正确 schema: name=选科组合+括号注释, course="3+1+2 选科组合", pct=院校覆盖率, reason=原因, sum=100.

修复策略: 走 m3 LLM 批量生成, 自带 retry + 校验 (sum=100, 3-5 条, 必含 course).
"""
from __future__ import annotations
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scf.synth.llm import M3Client, RetryableError, PermanentError

CUR = ROOT / "skills/gaokao-major-explorer/data/curated"
FIX_LIST = Path(os.environ.get("XUANKE_LIST", "/tmp/xuanke_to_fix.txt"))
LOG = Path(os.environ.get("XUANKE_LOG", "/tmp/xuanke_fix_log.txt"))

TOOL = {
    "name": "emit_xuanke",
    "description": "输出 xuanke_req_list 数组, 严格按 schema, 严禁其他文本.",
    "input_schema": {
        "type": "object",
        "properties": {
            "xuanke_req_list": {
                "type": "array",
                "minItems": 3,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "选科组合 + 括号注释, e.g. '物理 + 化学 + 生物 (传统理科, 90% 院校可报)'",
                        },
                        "course": {
                            "type": "string",
                            "enum": ["3+1+2 选科组合", "3+3 选科组合"],
                        },
                        "pct": {"type": "integer", "minimum": 0, "maximum": 100},
                        "reason": {
                            "type": "string",
                            "description": "为什么这个组合可报, 哪些方向, 25-50 字",
                        },
                    },
                    "required": ["name", "course", "pct", "reason"],
                },
            },
        },
        "required": ["xuanke_req_list"],
    },
}


def build_prompt(title: str, style: str, current: list) -> str:
    """current 是当前错误数据 (可能是 dict list 或 str list)."""
    cur_str = json.dumps(current, ensure_ascii=False)[:1500]
    return f"""你是中国高考专业数据编辑. 把"选科要求"数据从"按学科统计"重写为"按选科组合统计".

【专业】: {title} (style={style})
【当前错误数据 (per-subject, 来自旧 schema)】:
{cur_str}

【目标 schema (per-combination)】:
[
  {{"name": "物理 + 化学 + 生物 (传统理科, 90% 院校可报)", "course": "3+1+2 选科组合", "pct": 70, "reason": "..."}},
  {{"name": "物理 + 化学 (再选生物或不限)", "course": "3+1+2 选科组合", "pct": 18, "reason": "..."}},
  {{"name": "物理 + 生物 + 化学 (同组, 顺序差异)", "course": "3+1+2 选科组合", "pct": 8, "reason": "..."}},
  {{"name": "不限选科 (少数综合院校)", "course": "3+1+2 选科组合", "pct": 4, "reason": "..."}}
]

【硬约束】
1. 必须 3-5 条, pct 是 INTEGER (0-100), 全部 pct 之和 = 100 (允许 ±1 取整差)
2. name 必须含 "+" 分隔学科, 括号加 1 句定性注释 (e.g. "传统理科", "再选化学", "不限选科", "工科通用")
3. course 必须是 "3+1+2 选科组合" (本项目只用 3+1+2)
4. reason 25-50 字, 说明该组合可报的方向/原因
5. 严格 JSON 输出, 通过 emit_xuanke tool

【参考: 已知正确 schema 例子】
- 理工医主流: 物+化+生物 70 / 物+化 15 / 物+生+化 8 / 不限选科 7
- 文史法主流: 史+政+地 60 / 政+史 18 / 史+地 12 / 不限选科 10
- 工科通用: 物+化+技术 55 / 物+化 25 / 物+技术 12 / 不限选科 8
"""


def validate(result: list) -> tuple[bool, str]:
    if not isinstance(result, list):
        return False, f"not a list: {type(result).__name__}"
    if not (3 <= len(result) <= 5):
        return False, f"len={len(result)} not in [3,5]"
    for i, item in enumerate(result):
        if not isinstance(item, dict):
            return False, f"item {i} not dict"
        for f in ("name", "course", "pct", "reason"):
            if f not in item:
                return False, f"item {i} missing {f}"
        if not isinstance(item.get("pct"), int):
            return False, f"item {i} pct not int: {item.get('pct')!r}"
        if "+" not in item.get("name", "") and "不限" not in item.get("name", ""):
            return False, f"item {i} name no '+': {item.get('name')!r}"
        if item.get("course") != "3+1+2 选科组合":
            return False, f"item {i} bad course: {item.get('course')!r}"
    total = sum(item["pct"] for item in result)
    if not (99 <= total <= 101):
        return False, f"sum(pct)={total} not 100±1"
    return True, "ok"


def fix_one(client: M3Client, slug: str, title: str, style: str) -> tuple[bool, str, list | None]:
    """修单篇. 返回 (ok, msg, new_list)."""
    fp = CUR / slug
    if not fp.exists():
        return False, f"file missing: {fp}", None
    try:
        d = json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"json parse: {e}", None

    current = d.get("xuanke_req_list", [])
    if not current:
        return False, "empty list", None

    prompt = build_prompt(title, style, current)
    max_retry = 3
    for attempt in range(1, max_retry + 1):
        try:
            payload = client._call({
                "model": client.model,
                "max_tokens": 4000,
                "temperature": 0.3,
                "tools": [TOOL],
                "tool_choice": {"type": "tool", "name": "emit_xuanke"},
                "messages": [{"role": "user", "content": prompt}],
            }, expect_tool=True)
            # 抽 tool_use
            new_list = None
            for block in payload.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "emit_xuanke":
                    new_list = block.get("input", {}).get("xuanke_req_list")
                    break
            if new_list is None:
                raise RetryableError("no tool_use block")
            ok, msg = validate(new_list)
            if not ok:
                if attempt < max_retry:
                    continue
                return False, f"validate fail (attempt {attempt}): {msg}", None
            # 校验通过, 写回
            d["xuanke_req_list"] = new_list
            fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            return True, f"ok (attempt {attempt}, sum={sum(x['pct'] for x in new_list)})", new_list
        except (RetryableError, PermanentError) as e:
            if attempt >= max_retry:
                return False, f"LLM err: {str(e)[:100]}", None
            time.sleep(2 ** attempt)
    return False, "max retry exceeded", None


def main():
    if not FIX_LIST.exists():
        print(f"❌ {FIX_LIST} missing, run audit first")
        sys.exit(1)

    # 读 fix list
    items = []
    for line in FIX_LIST.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        slug, kind = parts[0], parts[1]
        fp = CUR / slug
        if not fp.exists():
            continue
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        items.append((slug, d.get("title", slug), d.get("style", "")))

    print(f"[fix] {len(items)} majors to fix")

    # 启动 m3
    try:
        client = M3Client(enable_thinking=False)
    except Exception as e:
        print(f"❌ M3Client init: {e}")
        sys.exit(2)

    # 并发修
    log_lines = []
    ok_count, fail_count = 0, 0
    start = time.time()
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = {pool.submit(fix_one, client, s, t, st): s for s, t, st in items}
        for fut in as_completed(futs):
            slug = futs[fut]
            try:
                ok, msg, _ = fut.result()
            except Exception as e:
                ok, msg = False, f"exception: {e}"
            if ok:
                ok_count += 1
                print(f"  ✅ {slug}: {msg}")
            else:
                fail_count += 1
                print(f"  ❌ {slug}: {msg}")
            log_lines.append(f"{'OK' if ok else 'FAIL'}\t{slug}\t{msg}")

    elapsed = time.time() - start
    print(f"\n[fix] done: {ok_count} ok, {fail_count} fail, {elapsed:.1f}s")
    print(f"     tokens: in={client.total_input_tokens}, out={client.total_output_tokens}")
    print(f"     cost: ¥{client.cost_estimate_cny():.2f}")

    LOG.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"[fix] log → {LOG}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
