"""Prompt 加载: 从 prompts/ 目录加载模板文件（支持 $var 或 {var} 替换）"""

from pathlib import Path
from string import Template

PROMPTS_ROOT = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, **kwargs) -> str:
    """加载 prompt 模板并填充参数。使用 $var 语法替换，与 JSON 中的 {} 无冲突。"""
    path = PROMPTS_ROOT / f"{name}.txt"
    template_text = path.read_text("utf-8")
    if kwargs:
        return Template(template_text).safe_substitute(**kwargs)
    return template_text


def load_prompt_text(name: str) -> str:
    """直接加载 prompt 文本（不做格式化）。"""
    path = PROMPTS_ROOT / f"{name}.txt"
    return path.read_text("utf-8").strip()
