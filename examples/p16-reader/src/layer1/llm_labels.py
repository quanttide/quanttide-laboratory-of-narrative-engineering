"""LLM 标注函数 — 用于验证层1公式的准确度。

每个函数让 LLM 对句子/段落标注 1-5 分。
返回 int 或 None（解析失败时）。
"""
import json
from packages.llm import call_llm, clean_json

_SYSTEM = "只输出一个整数 1-5，不要有任何其他文字。"


def llm_label_inference_demand(sentence: str) -> int | None:
    """标注此句的推理需求（1-5）。"""
    prompt = (
        "请判断以下句子需要读者多大程度的脑补才能理解。"
        "输出 1-5 的整数：\n"
        "1 = 完全直接，不需要推断\n"
        "2 = 基本直接，少量推断\n"
        "3 = 中等推理需求\n"
        "4 = 较高推理需求\n"
        "5 = 极高推理需求，大量隐含信息\n\n"
        f"句子：{sentence}"
    )
    raw = call_llm(prompt, system=_SYSTEM, temperature=0.1)
    return _parse_int(raw)


def llm_label_working_memory(sentence: str) -> int | None:
    """标注此句的阅读难度（1-5）。"""
    prompt = (
        "请判断以下句子的阅读难度——即读者在阅读过程中需要同时记住和处理的信息量。"
        "输出 1-5 的整数：\n"
        "1 = 非常简单，一目了然\n"
        "2 = 简单\n"
        "3 = 中等难度\n"
        "4 = 较难，需要仔细阅读\n"
        "5 = 非常难，需要反复阅读\n\n"
        f"句子：{sentence}"
    )
    raw = call_llm(prompt, system=_SYSTEM, temperature=0.1)
    return _parse_int(raw)


def llm_label_backtracking(sentence: str, prev_sentence: str) -> int | None:
    """标注此句需要回读的概率（1-5）。"""
    prompt = (
        "请判断读者在阅读以下句子时，是否需要回看前文才能理解。"
        "输出 1-5 的整数：\n"
        "1 = 完全不需要，自立自足\n"
        "2 = 基本不需要\n"
        "3 = 可能需要回看\n"
        "4 = 很可能需要回看\n"
        "5 = 必须回看前文才能理解\n\n"
        f"前一句：{prev_sentence}\n"
        f"当前句：{sentence}"
    )
    raw = call_llm(prompt, system=_SYSTEM, temperature=0.1)
    return _parse_int(raw)


def llm_label_situation_model(text: str, dimension: str) -> int | None:
    """标注全文在某维度上的连贯性（1-5）。"""
    prompt = (
        f"请判断以下段落在「{dimension}」维度的连贯性。"
        "输出 1-5 的整数：\n"
        "1 = 完全不连贯，维度频繁跳跃\n"
        "2 = 较不连贯\n"
        "3 = 中等连贯\n"
        "4 = 较连贯\n"
        "5 = 非常连贯，维度的变化有清晰逻辑\n\n"
        f"段落：{text[:500]}"
    )
    raw = call_llm(prompt, system=_SYSTEM, temperature=0.1)
    return _parse_int(raw)


def _parse_int(raw: str) -> int | None:
    r"""从 LLM 输出中提取整数。"""
    raw = clean_json(raw).strip()
    import re
    m = re.search(r'[1-5]', raw)
    return int(m.group()) if m else None
