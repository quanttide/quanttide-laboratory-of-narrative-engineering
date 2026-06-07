"""Prompt 模板 — 读者自述、评价、行为锚定三套模板。"""


def _params_desc(p: dict) -> str:
    return (
        f"openness={p['openness']}, empathy={p['empathy']}, "
        f"need_for_closure={p['need_for_closure']}, "
        f"literary_expertise={p['literary_expertise']}, "
        f"genre_familiarity={p['genre_familiarity']}, "
        f"time_pressure={p['time_pressure']}, "
        f"reading_purpose={p['reading_purpose']}"
    )


def build_reader_self_description(profile: dict) -> str:
    """读者自述 prompt — 用于 E4-0 操控性检验。"""
    if profile["id"] == "P0":
        return "请用一段话描述你作为读者的阅读风格和偏好——你通常关注什么、不能忍受什么。"

    return (
        f"你是一位{_params_desc(profile['params'])}的读者。\n\n"
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

    return (
        f"你是一位{_params_desc(profile['params'])}的读者。\n\n"
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


def build_evaluation_behavioral_anchor(
    profile: dict, text: str
) -> str:
    """行为锚定版评价 prompt — fallback。"""
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


def build_self_description_behavioral_anchor(profile: dict) -> str:
    """行为锚定版读者自述 prompt — fallback。"""
    anchor = profile.get("behavioral_anchor", "")
    if not anchor:
        return "请用一段话描述你作为读者的阅读风格和偏好——你通常关注什么、不能忍受什么。"
    return (
        f"{anchor}\n\n"
        "请用一段话描述你作为读者的阅读风格和偏好——你通常关注什么、不能忍受什么。"
    )
