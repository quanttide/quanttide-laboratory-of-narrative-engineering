"""推理需求密度 — 每句的隐含信息量。"""


# 中文代词集合
PRONOUNS = {"他", "她", "它", "他们", "她们", "它们", "这", "那", "这个", "那个", "这些", "那些", "这里", "那里", "谁", "什么", "哪", "怎么"}

# 隐含因果关系连接词
CAUSAL_MARKS = {"因为", "所以", "于是", "却", "反而", "因此", "因而", "从而", "以致", "以至于", "结果", "果然", "毕竟", "原来", "既然"}


def _split_sentences(text: str) -> list[str]:
    """按句号/问号/感叹号/省略号分割句子。"""
    import re
    parts = re.split(r'[。！？\n]+', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _word_count(s: str) -> int:
    """简单字数统计（按空白 + 标点分割）。"""
    import re
    return len(re.findall(r'\S+', s))


def inference_demand(text: str) -> list[float]:
    """对全文每句计算推理需求密度得分。"""
    sents = _split_sentences(text)
    scores = []
    for s in sents:
        words = [w for w in s.split() if w.strip()]
        n_words = len(words)
        if n_words == 0:
            scores.append(0.0)
            continue

        # 代词密度
        pronoun_count = sum(1 for w in words if w in PRONOUNS)
        pronoun_density = pronoun_count / max(n_words, 1)

        # 省略结构标记：句首为动词性词（非名词/代词开头）
        first_word = words[0] if words else ""
        omit_mark = 0
        import re
        if first_word and not re.match(r'^[他她它我这你那]', first_word) and re.match(r'^[\u4e00-\u9fff]', first_word):
            # 以实词开头但不是代词，可能是省略主语
            omit_mark = 1

        # 隐含因果关系标记
        causal_count = sum(1 for w in words if w in CAUSAL_MARKS)
        causal_density = causal_count / max(n_words, 1)

        score = pronoun_density * 2 + omit_mark + causal_density
        scores.append(round(score, 4))
    return scores
