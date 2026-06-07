"""推理需求密度 — 每句的推理需求（从 LLM 合并标注中提取）。"""

from .llm_labels import llm_label_all


def inference_demand(sentences: list[str]) -> list[int]:
    """对每句调用 LLM 合并标注，从中提取推理需求（1-5）。"""
    results = []
    prev = ""
    for s in sentences:
        label = llm_label_all(s, prev)
        results.append(label.get("inference_demand", 3))
        prev = s
    return results
