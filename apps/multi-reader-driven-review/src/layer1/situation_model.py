"""情境模型连贯性 — 全文五维度连贯性（一次 LLM 调用标注全部维度）。"""

from .llm_labels import llm_label_situation

DIMS = ["时间连贯性", "空间连贯性", "人物连贯性", "因果连贯性", "意图连贯性"]


def situation_model(text: str) -> dict:
    """对全文调用 LLM 一次性标注五维度连贯性（各 1-5），归一化到 0-1。"""
    raw = llm_label_situation(text)
    result = {}
    for dim in DIMS:
        val = raw.get(dim, 3)
        result[dim] = round((val - 1) / 4, 4)  # 1-5 → 0-1
    return result
