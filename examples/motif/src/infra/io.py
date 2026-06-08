"""IO 基础设施: 文件读写, YAML 加载, 缓存抽象"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from src.config import FICTION_ROOT


def read_article_text(path: str) -> str:
    """加载并预处理文章文本（跳过标题行，保留空行占位）。"""
    full_path = FICTION_ROOT / path
    if not full_path.exists():
        raise FileNotFoundError(f"文件不存在: {full_path}")
    text = full_path.read_text("utf-8")
    lines = text.split("\n")
    body_lines = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body_lines).strip()


def load_motif_yaml(path: Path) -> dict:
    """加载 YAML，自动忽略 YAML 文档分隔符 `---` 和注释行。"""
    raw = path.read_text("utf-8")
    raw = "\n".join(
        line for line in raw.splitlines()
        if line.strip() and not line.strip().startswith("# ") and line.strip() != "---"
    )
    return yaml.safe_load(raw)


def load_yaml(path: Path) -> dict:
    """加载 YAML，返回空字典而非 None。"""
    return yaml.safe_load(path.read_text("utf-8")) or {}


def cache_or_compute(
    cache_path: Path,
    compute_fn: Callable[[], Any],
    description: str = "",
    verbose: bool = True,
) -> Any:
    """缓存抽象: 如果缓存存在则读取，否则计算并保存。
    
    用法:
        data = cache_or_compute(
            RESULTS_DIR / "result.json",
            lambda: some_computation(),
            "计算中...",
        )
    """
    if cache_path.exists():
        if verbose:
            print(f"  ← 读取缓存" + (f" ({description})" if description else ""))
        return json.loads(cache_path.read_text("utf-8"))

    if verbose and description:
        print(f"  {description}...", end=" ", flush=True)

    result = compute_fn()

    cache_path.parent.mkdir(exist_ok=True)
    cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")

    if verbose and description:
        if isinstance(result, dict):
            detail = f" ({len(result)} 项)" if hasattr(result, "keys") else ""
        elif isinstance(result, list):
            detail = f" ({len(result)} 项)"
        else:
            detail = ""
        print(f"✓{detail}")

    return result


def cache_or_compute_text(
    cache_path: Path,
    compute_fn: Callable[[], str],
    description: str = "",
    verbose: bool = True,
) -> str:
    """缓存抽象（纯文本版）: 如果文本文件存在则读取，否则计算并保存。"""
    if cache_path.exists():
        if verbose:
            print(f"  ← 读取缓存" + (f" ({description})" if description else ""))
        return cache_path.read_text("utf-8")

    if verbose and description:
        print(f"  {description}...", end=" ", flush=True)

    result = compute_fn()
    cache_path.parent.mkdir(exist_ok=True)
    cache_path.write_text(result, "utf-8")

    if verbose and description:
        print(f"✓ ({len(result)} 字)" if len(result) > 0 else "✓")
    return result


def load_full_text(scene_name: str, paragraph_map: dict[str, dict[str, str]], max_chars: int = 500) -> str:
    """从原文中加载与场景匹配的段落。"""
    info = paragraph_map.get(scene_name)
    if not info:
        return ""
    path = FICTION_ROOT / info["file"]
    if not path.exists():
        return ""
    text = path.read_text("utf-8")
    lines = text.split("\n")
    body = [l for l in lines if not l.startswith("# ")]
    full = "\n".join(body)

    keyword = info.get("keyword", "")
    if keyword and keyword in full:
        idx = full.index(keyword)
        start = max(0, idx - max_chars // 2)
        paragraph = full[start:start + max_chars]
    else:
        paragraph = full[:max_chars]

    return paragraph.strip()
