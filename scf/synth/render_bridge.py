"""
synth/render_bridge.py — subprocess 调 generate_dashboard.py 写两处产物.

复用 regenerate_all.py:_render_one() 模式:
  - 加载 data dict
  - generate_dashboard(data, style) -> html
  - 写 skills/.../curated/<slug>.html (source of truth)
  - 写 public/<slug>.html (CF Pages 静态服务)
    - public 路径写完跑路径转换: ../../js/ → /js/, ../../css/ → /css/
    - 跑 3 个 inject (inject_og / inject_seo / inject_jsonld)

失败抛 RenderError, 包含 stderr 末尾 500 字符.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = ROOT / "skills" / "gaokao-major-explorer"
GEN_DASH = SKILL_DIR / "scripts" / "generate_dashboard.py"
CURATED_DIR = SKILL_DIR / "data" / "curated"
PUBLIC_DIR = ROOT / "public"


class RenderError(Exception):
    pass


def normalize_for_render(data: dict) -> dict:
    """
    在 render 之前对 data 做 best-effort 规范化, 防止 LLM 偶发返错 shape 时整篇崩.
    - overview_v2.fit/pitfalls/what 若是 string, 转 dict/list
    - top_schools/top_companies/alumni_quotes/employment_direction 元素若是 string, 包成 dict
    - alumni_quotes 字段名: author/position → current; source/position 合并
    - employment_direction 字段名: direction → name, ratio/detail → pct
    - curriculum 课程若是 string, 包成 {name, credit: "?"}
    - top_schools 字段 tag 若是空, 给个默认
    不修改原 dict, 返回深拷贝.
    """
    d = {**data}
    ov2 = d.get("overview_v2")
    if isinstance(ov2, dict):
        ov2 = {**ov2}
        # fit
        fit = ov2.get("fit")
        if isinstance(fit, str):
            ov2["fit"] = {"yes": [s.strip() for s in fit.split("\n") if s.strip()], "no": []}
        elif fit is None:
            ov2["fit"] = {"yes": [], "no": []}
        # pitfalls
        pp = ov2.get("pitfalls")
        if isinstance(pp, str):
            items = []
            for line in pp.split("\n"):
                line = line.strip().lstrip("❌").lstrip("✅").strip()
                if not line:
                    continue
                for sep in ("→", "—", " - ", ":"):
                    if sep in line:
                        m, r = line.split(sep, 1)
                        items.append({"myth": m.strip(), "reality": r.strip()})
                        break
                else:
                    items.append({"myth": line[:60], "reality": line[60:] or "见上"})
            ov2["pitfalls"] = items
        elif pp is None:
            ov2["pitfalls"] = []
        # what
        what = ov2.get("what")
        if isinstance(what, str):
            ov2["what"] = {"foundations": [s.strip() for s in what.split("\n") if s.strip()][:6]}
        elif what is None:
            ov2["what"] = {}
        d["overview_v2"] = ov2

    # ── 5 个 list 字段的 shape 修正 ──
    # top_schools: 元素若是 string, 包成 {name, tag}
    d["top_schools"] = [_coerce_school(x) for x in d.get("top_schools", []) if x]
    # top_companies: 元素若是 string, 包成 {name, tier: B}
    d["top_companies"] = [_coerce_company(x) for x in d.get("top_companies", []) if x]
    # alumni_quotes: 字段重命名 author/position → current
    d["alumni_quotes"] = [_coerce_quote(x) for x in d.get("alumni_quotes", []) if x]
    # employment_direction: direction→name, ratio/detail→pct
    d["employment_direction"] = [_coerce_direction(x) for x in d.get("employment_direction", []) if x]
    # deep_study: 若 list, 转 dict; 若 dict, 保留
    ds = d.get("deep_study")
    if isinstance(ds, list):
        d["deep_study"] = {x.get("name", str(x)): x.get("pct", 0)
                           for x in ds if isinstance(x, dict)}
    # xuanke_req_list: ratio→pct
    d["xuanke_req_list"] = [_coerce_xuanke(x) for x in d.get("xuanke_req_list", []) if x]
    # curriculum 块: 课程若是 string, 包成 dict
    c = d.get("curriculum")
    if isinstance(c, dict):
        d["curriculum"] = {
            k: [_coerce_course(x) for x in v if x]
            for k, v in c.items() if isinstance(v, list)
        }
    return d


def _coerce_school(x):
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        return {"name": x.strip(), "rank": "", "tag": ""}
    return {"name": str(x)}


def _coerce_company(x):
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        return {"name": x.strip(), "tier": "B", "headcount": "—", "salary": "—", "sparkline": []}
    return {"name": str(x)}


def _coerce_quote(x):
    """author/position → current, 保留 quote/source/year."""
    if isinstance(x, dict):
        out = dict(x)
        if "current" not in out:
            # 拼 author + position
            a = out.pop("author", "") if "author" in out else ""
            p = out.pop("position", "") if "position" in out else ""
            out["current"] = (a + " · " + p).strip(" ·") or (a or p) or "校友"
        # source 拆自 year+source
        if "source" not in out and "year" in out:
            out["source"] = str(out.get("year", ""))
        return out
    if isinstance(x, str):
        return {"current": "校友", "quote": x.strip(), "source": "公开访谈"}
    return {"current": "校友", "quote": str(x)}


def _coerce_direction(x):
    if isinstance(x, dict):
        out = dict(x)
        if "name" not in out and "direction" in out:
            out["name"] = out.pop("direction")
        if "pct" not in out:
            r = out.pop("ratio", out.pop("pct", 0))
            try:
                out["pct"] = int(r)
            except (TypeError, ValueError):
                out["pct"] = 0
        return out
    if isinstance(x, str):
        return {"name": x.strip(), "pct": 0}
    return {"name": str(x)}


def _coerce_xuanke(x):
    if isinstance(x, dict):
        out = dict(x)
        if "pct" not in out:
            r = out.pop("ratio", out.pop("pct", 0))
            try:
                out["pct"] = int(r)
            except (TypeError, ValueError):
                out["pct"] = 0
        return out
    if isinstance(x, str):
        return {"name": x.strip(), "pct": 0}
    return {"name": str(x)}


def _coerce_course(x):
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        return {"name": x.strip(), "credit": "?"}
    return {"name": str(x)}


def render_html(data: dict, slug: str, style: str) -> tuple[str, int]:
    """
    把 data dict 渲染为 HTML, 写两处, 返回 (public_path, size_bytes).

    流程:
      1) normalize_for_render (防 LLM 返错 shape)
      2) 把 data 写到临时 JSON
      3) python generate_dashboard.py --data <tmp.json> --style <style> --output <tmp.html>
      4) 写 skills/.../curated/<slug>.html (原始 HTML, ../../js/ 路径)
      5) 写 public/<slug>.html (跑路径转换 ../../js/ → /js/, 然后跑 3 个 inject)
    """
    data = normalize_for_render(data)
    if not GEN_DASH.exists():
        raise RenderError(f"generate_dashboard.py 找不到: {GEN_DASH}")

    # 1. 临时 JSON
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        tmp_json = f.name

    # 2. 临时 HTML 输出
    tmp_html = tempfile.mktemp(suffix=".html")

    try:
        # 3. subprocess 调 generate_dashboard.py
        proc = subprocess.run(
            [sys.executable, str(GEN_DASH),
             "--data", tmp_json, "--style", style, "--output", tmp_html],
            capture_output=True,
            text=True,
            cwd=str(SKILL_DIR / "scripts"),
            timeout=60,
        )
        if proc.returncode != 0:
            err = proc.stderr or proc.stdout or ""
            raise RenderError(
                f"generate_dashboard 失败 (rc={proc.returncode}):\n{err[-500:]}"
            )
        if not os.path.exists(tmp_html):
            raise RenderError(f"generate_dashboard 未输出 {tmp_html}")

        # 4. 读 HTML
        html = Path(tmp_html).read_text(encoding="utf-8")
        CURATED_DIR.mkdir(parents=True, exist_ok=True)
        PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

        # 4a. 写 curated (source of truth, 原始路径)
        curated_path = CURATED_DIR / f"{slug}.html"
        curated_path.write_text(html, encoding="utf-8")

        # 4b. 写 public (跑路径转换 ../../js/ → /js/, ../../css/ → /css/)
        PUBLIC_PATH_PATTERN = re.compile(r'(src|href)="\.\./\.\./((?:js|css)/[^"]+)"')
        html_for_public = PUBLIC_PATH_PATTERN.sub(
            lambda m: f'{m.group(1)}="/{m.group(2)}"', html
        )
        public_path = PUBLIC_DIR / f"{slug}.html"
        public_path.write_text(html_for_public, encoding="utf-8")

        # 4c. 跑 3 个 inject (SEO + OG + JSON-LD) — 直接 inline 调, 防死链
        for inject_script in ("inject_og.py", "inject_seo.py", "inject_jsonld.py"):
            inject_path = ROOT / "scripts" / inject_script
            if not inject_path.exists():
                print(f"  [inject] {inject_script} 不存在, 跳过")
                continue
            try:
                # 各 inject 接受 --slug <slug> (按需 verify 签名)
                inject_proc = subprocess.run(
                    [sys.executable, str(inject_path), "--slug", slug],
                    capture_output=True, text=True,
                    cwd=str(ROOT), timeout=30,
                )
                if inject_proc.returncode != 0:
                    err_tail = (inject_proc.stderr or inject_proc.stdout or "")[-200:]
                    print(f"  [inject] {inject_script} 警告 (rc={inject_proc.returncode}): {err_tail}")
                else:
                    print(f"  [inject] {inject_script} ✓")
            except subprocess.TimeoutExpired:
                print(f"  [inject] {inject_script} 超时 30s, 跳过")
            except Exception as e:
                print(f"  [inject] {inject_script} 失败: {type(e).__name__}: {e}")

        # 4d. 最终同步: inject 改的是 CURATED, 重新 sync 到 PUBLIC (带路径转换)
        #     保证 CF Pages 拿到的 public/<slug>.html 是最新版 + 路径绝对化
        if curated_path.exists():
            final_curated = curated_path.read_text(encoding="utf-8")
            final_public = PUBLIC_PATH_PATTERN.sub(
                lambda m: f'{m.group(1)}="/{m.group(2)}"', final_curated
            )
            public_path.write_text(final_public, encoding="utf-8")
            return str(public_path), len(final_public)
        return str(public_path), len(html_for_public)
    finally:
        for p in (tmp_json, tmp_html):
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass


def save_data_json(data: dict, slug: str) -> str:
    """把 data dict 写到 skills/.../curated/<slug>.json (供 regenerate_all 后续用)."""
    out = CURATED_DIR / f"{slug}.json"
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)
