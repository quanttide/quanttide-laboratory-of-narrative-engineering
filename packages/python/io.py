"""
文件 I/O 工具及缓存抽象。

从 p05/p09/p14 中提炼——文章读取、JSON / YAML 读写、路径管理、缓存。
"""
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml


def read_article_text(fiction_root: Path, path: str) -> str:
    """读取小说场景文本，过滤 markdown 标题行。

    参数：
        fiction_root: assets/fiction 目录路径
        path: 相对路径（如 "职场言情/4_成稿/1_1_咖啡厅重逢.md"）
    """
    full_path = fiction_root / path
    if not full_path.exists():
        raise FileNotFoundError(f"文件不存在: {full_path}")
    text = full_path.read_text("utf-8")
    lines = text.split("\n")
    body_lines = [
        " " if l.strip() == "" else l
        for l in lines
        if not l.startswith("# ")
    ]
    return "\n".join(body_lines).strip()


def save_json(path: Path, data, indent: int = 2) -> None:
    """写入 JSON 文件（ensure_ascii=False，保留中文）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8"
    )


def load_json(path: Path):
    """读取 JSON 文件。"""
    return json.loads(path.read_text("utf-8"))


def load_yaml(path: Path) -> dict:
    """加载 YAML 文件并返回 dict。"""
    return yaml.safe_load(path.read_text("utf-8")) or {}


def ensure_dir(path: Path) -> Path:
    """确保目录存在，返回该路径。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_motif_yaml(path: Path) -> dict:
    """加载 YAML，自动忽略 YAML 文档分隔符 `---` 和注释行。"""
    raw = path.read_text("utf-8")
    raw = "\n".join(
        line for line in raw.splitlines()
        if line.strip() and not line.strip().startswith("# ") and line.strip() != "---"
    )
    return yaml.safe_load(raw)


def cache_or_compute(
    cache_path: Path,
    compute_fn: Callable[[], Any],
    description: str = "",
    verbose: bool = True,
) -> Any:
    """缓存抽象: 如果缓存存在则读取，否则计算 JSON 序列化并保存。"""
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
        print(f"  ✓ ({len(result)} 字)" if len(result) > 0 else "✓")
    return result
