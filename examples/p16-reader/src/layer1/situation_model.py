"""情境模型连贯性 — 全文五维度连贯性评分。"""

import re
from collections import Counter


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'[。！？\n]+', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _char_count(s: str) -> int:
    return len(re.sub(r'\s+', '', s))


def _uniformity(positions: list[float], n_sents: int) -> float:
    """分布均匀度：0=全部集中, 1=完全均匀。"""
    if n_sents <= 1 or len(positions) <= 1:
        return 0.5
    # 实际分布的熵 / 均匀分布的熵
    bins = max(3, n_sents // 2)
    hist = [0] * bins
    for p in positions:
        idx = min(int(p * bins), bins - 1)
        hist[idx] += 1
    total = sum(hist)
    if total == 0:
        return 0.5
    probs = [h / total for h in hist if h > 0]
    import math
    entropy = -sum(p * math.log(p) for p in probs)
    max_entropy = math.log(bins)
    return entropy / max_entropy if max_entropy > 0 else 0.5


def situation_model(text: str) -> dict:
    """返回五维度连贯性评分（0-1）。"""
    sents = _split_sentences(text)
    n_sents = len(sents)

    # 时间词
    time_words = re.findall(r'[时年日月周天][前后来里]?|今天|昨天|明天|以前|后来|未来|过去|现在|曾经|已经|正在|将要|突然|终于|最后', text)
    time_pos = []
    for s_idx, s in enumerate(sents):
        count = len(re.findall(r'[时年日月周天][前后来里]?|今天|昨天|明天|以前|后来|未来|过去|现在|曾经|已经|正在|将要|突然|终于|最后', s))
        for _ in range(count):
            time_pos.append(s_idx / max(n_sents - 1, 1))

    # 空间词
    space_words = re.findall(r'[里上中下前后外内旁]|家|公司|学校|房间|楼下|门外|街上|路边|角落|尽头|中心', text)
    space_pos = []
    for s_idx, s in enumerate(sents):
        count = len(re.findall(r'[里上中下前后外内旁]|家|公司|学校|房间|楼下|门外|街上|路边|角落|尽头|中心', s))
        for _ in range(count):
            space_pos.append(s_idx / max(n_sents - 1, 1))

    # 人物词（高频名词 + 称呼）
    all_words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
    word_freq = Counter(all_words)
    names = {w for w, c in word_freq.most_common(20) if c >= 2 and not any(t in w for t in ["因为", "所以", "但是", "虽然", "可以", "没有", "一个", "什么", "自己", "知道", "觉得", "时候", "不是", "就是", "如果", "已经", "这么", "怎么"])}
    char_recurrence = 0
    for s in sents:
        found = sum(1 for name in names if name in s)
        if found >= 1:
            char_recurrence += 1
    char_score = min(char_recurrence / max(n_sents, 1) * 2, 1.0)

    # 因果连贯性：因果词在各段的分布一致性
    causal_words = re.findall(r'因为|所以|因此|于是|从而|为了|由于|导致|使得', text)
    causal_per_sent = [len(re.findall(r'因为|所以|因此|于是|从而|为了|由于|导致|使得', s)) for s in sents]
    causal_mean = sum(causal_per_sent) / max(n_sents, 1)
    if causal_mean > 0:
        causal_var = sum((c - causal_mean) ** 2 for c in causal_per_sent) / n_sents
        causal_score = max(0, 1 - min(causal_var / causal_mean, 1))
    else:
        causal_score = 0.3

    # 意图连贯性：行为/心理动词密度
    action_verbs = re.findall(r'[走跑站坐拿放推拉打说看听想感觉知]', text)
    intent_density = len(action_verbs) / max(_char_count(text), 1) * 100
    intent_score = min(intent_density / 5, 1.0)

    result = {
        "time_coherence": round(_uniformity(time_pos, n_sents), 4) if time_pos else 0.5,
        "space_coherence": round(_uniformity(space_pos, n_sents), 4) if space_pos else 0.5,
        "character_coherence": round(char_score, 4),
        "causal_coherence": round(causal_score, 4),
        "intent_coherence": round(intent_score, 4),
    }
    return result
