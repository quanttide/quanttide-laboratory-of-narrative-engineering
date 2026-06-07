"""
文件 I/O 工具。

从 p05/p09/p14 中提炼——文章读取、JSON / YAML 读写、路径管理。
"""
import json
from pathlib import Path


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
    import yaml
    return yaml.safe_load(path.read_text("utf-8")) or {}


def ensure_dir(path: Path) -> Path:
    """确保目录存在，返回该路径。"""
    path.mkdir(parents=True, exist_ok=True)
    return path
