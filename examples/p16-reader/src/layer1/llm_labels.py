"""LLM 标注函数 — 用于层1认知负荷指标的逐句标注。

4 个维度的标注合并为一次 LLM 调用，减少 75% 的 API 开销。
返回 JSON 格式的字典，包含推理需求、阅读难度、回读概率。
"""
import json
from packages.llm import call_llm, clean_json


def llm_label_all(sentence: str, prev_sentence: str = "") -> dict:
    """一次调用标注所有维度，返回包含各维度评分的 dict。"""
    prompt = (
        "判断以下句子的认知负荷指标，严格输出 JSON 格式（不要有任何其他文字）：\n"
        "{\n"
        '  "inference_demand": 1-5（需要读者多少脑补/推断隐含信息）,\n'
        '  "reading_difficulty": 1-5（阅读难度，句子结构复杂程度）,\n'
        '  "backtrack_prob": 1-5（需要回看前文才能理解的程度）\n'
        "}\n\n"
        f"前一句：{prev_sentence}\n"
        f"当前句：{sentence}"
    )
    raw = call_llm(prompt, temperature=0.1)
    try:
        return json.loads(clean_json(raw))
    except (json.JSONDecodeError, TypeError):
        return {"inference_demand": 3, "reading_difficulty": 3, "backtrack_prob": 3}


def llm_label_situation(text: str) -> dict:
    """一次调用标注全文五维度连贯性，返回 dict。"""
    prompt = (
        "判断以下段落的五维度连贯性，严格输出 JSON（不要有任何其他文字）：\n"
        "{\n"
        '  "时间连贯性": 1-5,\n'
        '  "空间连贯性": 1-5,\n'
        '  "人物连贯性": 1-5,\n'
        '  "因果连贯性": 1-5,\n'
        '  "意图连贯性": 1-5\n'
        "}\n\n"
        f"段落：{text[:800]}"
    )
    raw = call_llm(prompt, temperature=0.1)
    try:
        return json.loads(clean_json(raw))
    except (json.JSONDecodeError, TypeError):
        return {d: 3 for d in ["时间连贯性", "空间连贯性", "人物连贯性", "因果连贯性", "意图连贯性"]}
