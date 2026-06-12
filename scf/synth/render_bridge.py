"""
synth/render_bridge.py — subprocess 调 generate_dashboard.py 写两处产物.

复用 regenerate_all.py:_render_one() 模式:
  - 加载 data dict
  - generate_dashboard(data, style) -> html
  - 写 skills/.../curated/<slug>.html (source of truth)
  - 写 public/<slug>.html (EdgeOne 静态服务)

失败抛 RenderError, 包含 stderr 末尾 500 字符.
"""
from __future__ import annotations
import json
import os
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


def render_html(data: dict, slug: str, style: str) -> tuple[str, int]:
    """
    把 data dict 渲染为 HTML, 写两处, 返回 (public_path, size_bytes).

    流程:
      1) 把 data 写到临时 JSON
      2) python generate_dashboard.py --data <tmp.json> --style <style> --output <tmp.html>
      3) 把 html 复制到 curated/<slug>.html + public/<slug>.html
    """
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

        # 4. 读 HTML, 写两处
        html = Path(tmp_html).read_text(encoding="utf-8")
        CURATED_DIR.mkdir(parents=True, exist_ok=True)
        PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
        curated_path = CURATED_DIR / f"{slug}.html"
        public_path = PUBLIC_DIR / f"{slug}.html"
        curated_path.write_text(html, encoding="utf-8")
        public_path.write_text(html, encoding="utf-8")
        return str(public_path), len(html)
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
