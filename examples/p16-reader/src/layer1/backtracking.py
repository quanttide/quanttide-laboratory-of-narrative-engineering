"""回溯重读预测 — 每句需要回读的概率（从 LLM 合并标注中提取）。"""

from .llm_labels import llm_label_all


def backtracking_prediction(sentences: list[str]) -> list[int]:
    """对每句调用 LLM 合并标注，从中提取回读概率（1-5）。"""
    results = []
    prev = ""
    for s in sentences:
        label = llm_label_all(s, prev)
        results.append(label.get("backtrack_prob", 3))
        prev = s
    return results
