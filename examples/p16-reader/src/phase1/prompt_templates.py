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
    if profile["id"] == "P0":
        return (
            "请从你的视角评价以下段落。"
            "输出 JSON 格式：\n"
            '{"logic_break": {"detected": true/false, "positions": ["位置"]}, '
            '"grammar_error": {"detected": true/false}, '
            '"emotional_impact": 1-7, '
            '"reading_difficulty": 1-5, '
            '"structure_label": "逻辑断裂" / "有意留白" / "正常", '
            '"aesthetic_grade": "A" / "A-" / "B" / "C"}\n\n'
            f"---\n{text}"
        )

    anchor = profile.get("behavioral_anchor", "")
    return (
        f"{anchor}\n\n"
        "请从上述读者的视角评价以下段落。"
        "输出 JSON 格式：\n"
        '{"logic_break": {"detected": true/false, "positions": ["位置"]}, '
        '"grammar_error": {"detected": true/false}, '
        '"emotional_impact": 1-7, '
        '"reading_difficulty": 1-5, '
        '"structure_label": "逻辑断裂" / "有意留白" / "正常", '
        '"aesthetic_grade": "A" / "A-" / "B" / "C"}\n\n'
        f"---\n{text}"
    )
