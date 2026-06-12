"""
synth/manifest_ops.py — manifest.json atomic 追加.

双写:
  - skills/gaokao-major-explorer/data/curated/manifest.json  (渲染用, source of truth)
  - public/data/manifest.json                                (前端用, EdgeOne 服务)

约束:
  - 写前 flock + 读再写, 防 SCF 冷启动多并发
  - 写用 tmp + rename (POSIX atomic on same fs)
  - 同步两份, 失败回滚
"""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path


# 路径: 项目根 = <ROOT>
SKILL_MANIFEST = "skills/gaokao-major-explorer/data/curated/manifest.json"
PUBLIC_MANIFEST = "public/data/manifest.json"


def _atomic_write_json(path: Path, data: dict):
    """tmp + rename, 防半写."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _flock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


def _acquire_lock(lock: Path, timeout: float = 5.0) -> bool:
    """简单 flock, 失败返回 False."""
    deadline = __import__("time").time() + timeout
    while __import__("time").time() < deadline:
        try:
            lock.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close(fd)
            return True
        except FileExistsError:
            __import__("time").sleep(0.1)
    return False


def _release_lock(lock: Path):
    try:
        os.unlink(lock)
    except FileNotFoundError:
        pass


def load_manifest(root: Path) -> dict:
    """读 skills 那个 manifest (source of truth)."""
    p = root / SKILL_MANIFEST
    return json.loads(p.read_text(encoding="utf-8"))


def append_major(root: Path, entry: dict) -> bool:
    """
    追加 1 个 major entry 到两份 manifest.

    entry 必须含: slug, title, style, category, degree, duration_years, tags,
                  status="done", data_source, html_path, data_path.
    若 slug 已存在, 跳过返回 False.
    若 entry 含 _mock=True, 拒绝追加 (防 mock 产物污染 manifest).
    """
    # ── 守卫: mock 产物不入 manifest ──
    if entry.get("_mock"):
        print(f"  [manifest] slug={entry.get('slug', '?')} 是 mock 产物, 拒绝入 manifest")
        return False

    lock = root / SKILL_MANIFEST
    if not _acquire_lock(lock.with_suffix(lock.suffix + ".lock")):
        raise RuntimeError("manifest lock acquire timeout")

    try:
        # 1. 读两份
        skill_p = root / SKILL_MANIFEST
        public_p = root / PUBLIC_MANIFEST
        skill_data = json.loads(skill_p.read_text(encoding="utf-8"))
        public_data = json.loads(public_p.read_text(encoding="utf-8"))

        # 2. 查重
        for m in skill_data.get("majors", []):
            if m.get("slug") == entry.get("slug"):
                print(f"  [manifest] slug={entry['slug']} 已存在, 跳过")
                return False

        # 3. 补全字段
        entry.setdefault("status", "done")
        entry.setdefault("html_path", f"data/curated/{entry['slug']}.html")
        entry.setdefault("data_path", f"data/curated/{entry['slug']}.json")

        # 4. 追加
        skill_data.setdefault("majors", []).append(entry)
        public_data.setdefault("majors", []).append(entry)

        # 5. 更新 top-level 元数据
        for d in (skill_data, public_data):
            d["total"] = len(d["majors"])
            d["updated_at"] = entry.get("updated_at", "2026-06")
            styles = sorted({m["style"] for m in d["majors"] if m.get("style")})
            d["styles_used"] = styles

        # 6. atomic 写回
        _atomic_write_json(skill_p, skill_data)
        _atomic_write_json(public_p, public_data)
        return True
    finally:
        _release_lock(lock.with_suffix(lock.suffix + ".lock"))


def upsert_manifest_minimal(
    root: Path,
    slug: str,
    title: str,
    style: str,
    category: str,
    degree: str = "",
    duration_years: int = 4,
    tags: list[str] | None = None,
    data_source: str = "Web 搜索综合 (按需生成)",
    _mock: bool = False,
) -> bool:
    """便利函数: 凑齐最小 entry 追加. _mock=True 拒绝入 manifest."""
    return append_major(root, {
        "slug": slug,
        "title": title,
        "category": category,
        "style": style,
        "degree": degree,
        "duration_years": duration_years,
        "tags": tags or ["按需生成"],
        "data_source": data_source,
        "_mock": _mock,
    })


# ── CLI 调试 ──
if __name__ == "__main__":
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent
    m = load_manifest(root)
    print(f"current majors: {len(m.get('majors', []))}, styles: {m.get('styles_used')}")
    if len(sys.argv) >= 3 and sys.argv[1] == "upsert":
        slug, title, style = sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "cs"
        ok = upsert_manifest_minimal(root, slug, title, style)
        print(f"upsert {slug} → {ok}")
