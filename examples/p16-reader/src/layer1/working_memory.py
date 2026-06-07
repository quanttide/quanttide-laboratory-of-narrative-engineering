"""工作记忆负载 — 每句的名词短语密度和句法复杂度。"""

import re


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'[。！？\n]+', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _count_noun_phrases(s: str) -> int:
    """统计"的"字结构名词短语（如"温柔的月光"、"熟悉的声音"）。"""
    return len(re.findall(r'[很非常特别好大]?\w*的\w+', s))


def _count_complexity_markers(s: str) -> int:
    """统计逗号 + 子句连接词数量。"""
    conj = re.findall(r'[，,]', s)
    sub_conj = ["和", "与", "但是", "虽然", "因为", "当", "如果", "即使", "尽管", "无论", "只要", "为了"]
    sc = sum(1 for c in sub_conj if c in s)
    return len(conj) + sc


def working_memory_load(text: str) -> list[float]:
    """对全文每句计算工作记忆负载得分。"""
    sents = _split_sentences(text)
    scores = []
    for s in sents:
        words = [w for w in s.split() if w.strip()]
        n_words = len(words)
        if n_words == 0:
            scores.append(0.0)
            continue

        # 名词短语密度
        np_count = _count_noun_phrases(s)
        np_density = np_count / max(n_words, 1)

        # 句法复杂度（归一化到 0-1）
        complexity = min(_count_complexity_markers(s), 5) / 5.0

        score = np_density * 2 + complexity
        scores.append(round(score, 4))
    return scores
