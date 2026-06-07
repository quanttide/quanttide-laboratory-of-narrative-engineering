"""Step 1: 契约标注

对每个文本点，LLM 标注它触及了写作契约的哪些条款：
- style.yaml：触及的维度和 boundaries，触及性质（违反/边缘/遵守）
- motif.yaml：涉及的母题和使用方式
- story.yaml：相关的角色定义和场景 tension
"""
import json
from pathlib import Path

from packages.io import load_yaml
from packages.llm import call_llm


PROMPT_TEMPLATE = """你是一位写作契约分析专家。你的任务是分析一个具体的文本点，标注它触及了写作契约中的哪些条款。

## 写作契约

### style.yaml（审美契约）
{style_yaml}

### motif.yaml（母题契约）
{motif_yaml}

### story.yaml（角色契约）
{story_yaml}

## 文本点

位置：{location}
原文：{quote}

### 上下文
{context_before}
【此处是文本点】
{context_after}

## 任务

请标注该文本点触及了写作契约的哪些条款。输出 JSON，不要添加 markdown 代码块标记。

注意：
1. 只标注确实触及的条款，不要编造
2. "nature"/"alignment" 必须从列举的值中选择
3. reason 要具体到文本点的细节
4. JSON 中的字符串值如果包含双引号，必须用反斜杠转义（\\"），或者改用中文引号「」

输出 JSON 结构如下（请确保 JSON 中所有花括号和双引号正确对应）：
- style.touched_dimensions[]: dimension, boundary, nature(违反|边缘|遵守), reason
- motif.touched_motifs[]: motif, usage, alignment(对齐|偏离|边缘)
- story.touched_characters[]: character, behavior_assessment, alignment(一致|不一致|边缘)
- story.touched_tensions[]: tension, relevance
"""

SYSTEM_PROMPT = "你是一个严谨的写作契约分析专家。只输出 JSON，不要添加 markdown 代码块标记。确保 JSON 中的双引号被正确转义。"


def load_contracts():
    """加载写作契约文件。"""
    fiction_root = Path(__file__).resolve().parents[3] / "assets" / "fiction"
    return {
        "style_yaml": load_yaml(fiction_root / "style.yaml"),
        "motif_yaml": load_yaml(fiction_root / "motif.yaml"),
        "story_yaml": load_yaml(fiction_root / "story.yaml"),
    }


def format_style(style: dict) -> str:
    """格式化 style.yaml 为可读文本。"""
    lines = []
    for s in style.get("styles", []):
        lines.append(f"### {s['title']}")
        lines.append(s.get("description", ""))
        for b in s.get("boundaries", []):
            lines.append(f"- 边界：{b}")
        lines.append("")
    return "\n".join(lines)


def format_motif(motif: dict) -> str:
    """格式化 motif.yaml 为可读文本。"""
    lines = [f"标题：{motif.get('title', '')}"]
    lines.append(motif.get("description", ""))
    lines.append("")
    for m in motif.get("motifs", []):
        lines.append(f"- {m['title']}（权重 {m.get('weight', '?')}）：{m.get('description', '')}")
    return "\n".join(lines)


def format_story(story: dict) -> str:
    """格式化 story.yaml 为可读文本。"""
    lines = [f"标题：{story.get('title', '')}"]
    lines.append(story.get("description", ""))
    lines.append("")
    lines.append("### 角色")
    for c in story.get("characters", []):
        lines.append(f"- {c['name']}：{c.get('description', '')}")
    lines.append("")
    # 找到当前场景
    return "\n".join(lines)


def _clean_raw_json(raw: str) -> str:
    """清理 LLM 返回的 JSON 字符串，处理常见问题。"""
    raw = raw.strip()
    # 去掉 markdown 代码块标记
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines)
    return raw.strip()


def annotate(text_point, contracts, temperature=0.3, max_retries=3):
    """对单个文本点执行契约标注，带重试机制。"""
    prompt = PROMPT_TEMPLATE.format(
        style_yaml=format_style(contracts["style_yaml"]),
        motif_yaml=format_motif(contracts["motif_yaml"]),
        story_yaml=format_story(contracts["story_yaml"]),
        location=text_point["location"],
        quote=text_point["quote"],
        context_before=text_point.get("context_before", ""),
        context_after=text_point.get("context_after", ""),
    )

    for attempt in range(max_retries):
        raw = call_llm(prompt, system=SYSTEM_PROMPT, temperature=temperature)
        raw = _clean_raw_json(raw)
        try:
            result = json.loads(raw)
            return result
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                continue
            return {"error": f"JSON 解析失败（{max_retries} 次重试后）: {e}", "raw": raw}
    return {"error": "未知错误", "raw": raw}
