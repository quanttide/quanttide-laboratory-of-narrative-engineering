"""Prompt 模板 — 读者自述、评价 prompt。

画像基于真实读者人群（年龄/职业/阅读经验/动机），使用行为锚定描述直接驱动 LLM。
"""


def build_reader_self_description(profile: dict) -> str:
    """读者自述 prompt — 用于 E4-0 操控性检验。"""
    if profile["id"] == "P0":
        return "请用一段话描述你作为读者的阅读风格和偏好——你通常关注什么、不能忍受什么。"

    anchor = profile.get("behavioral_anchor", "")
    return (
        f"{anchor}\n\n"
        "请用一段话描述你作为读者的阅读风格和偏好——你通常关注什么、不能忍受什么。"
    )


def build_evaluation_prompt(profile: dict, text: str) -> str:
    """评价 prompt — 用于 E4-1 分化验证。"""
    base = (
        "请从你的视角评价以下段落。\n"
        "输出 JSON 格式，严格按以下字段：\n"
        '{\n'
        '  "writing_quality": 1-7（文笔质量，越高越好）,\n'
        '  "emotional_impact": 1-7（情感冲击力，越高越强）,\n'
        '  "character_realism": 1-7（角色真实感，越高越真实）,\n'
        '  "cliche_level": 1-5（套路感，越高越套路化）,\n'
        '  "reading_difficulty": 1-5（阅读难度，越高越难读）,\n'
        '  "logic_break": {"detected": true/false, "positions": ["位置"]},\n'
        '  "structure_label": "逻辑断裂" / "有意留白" / "正常",\n'
        '  "aesthetic_grade": "A" / "A-" / "B" / "C"\n'
        '}\n\n'
    )
    if profile["id"] == "P0":
        return base + f"---\n{text}"
    anchor = profile.get("behavioral_anchor", "")
    return f"{anchor}\n\n{base}---\n{text}"
