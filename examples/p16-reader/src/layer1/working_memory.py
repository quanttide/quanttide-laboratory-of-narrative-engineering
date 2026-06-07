"""工作记忆负载 — 每句的阅读难度（从 LLM 合并标注中提取）。"""

from .llm_labels import llm_label_all


def working_memory_load(sentences: list[str]) -> list[int]:
    """对每句调用 LLM 合并标注，从中提取阅读难度（1-5）。"""
    results = []
    prev = ""
    for s in sentences:
        label = llm_label_all(s, prev)
        results.append(label.get("reading_difficulty", 3))
        prev = s
    return results
