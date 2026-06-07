"""回溯重读预测 — 代词到最近前指的距离。"""

import re

PRONOUNS_MALE = {"他", "他们"}
PRONOUNS_FEMALE = {"她", "她们"}
PRONOUNS_NEUTRAL = {"它", "它们", "这", "那"}


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'[。！？\n]+', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _gender(pronoun: str) -> str:
    if pronoun in PRONOUNS_MALE:
        return "male"
    if pronoun in PRONOUNS_FEMALE:
        return "female"
    return "neutral"


def _token_count(s: str) -> int:
    return len(re.findall(r'\S+', s))


def _find_antecedent(pronoun: str, prev_sentence: str) -> int | None:
    """在前一句中寻找与代词性别一致的人物名词。返回词距离。"""
    if not prev_sentence:
        return None
    g = _gender(pronoun)
    # 性别相关的人物名词模式
    if g == "male":
        patterns = [r'[他]', r'(?:先生|男孩|男人|儿子|父亲|哥哥|弟弟|爷爷|爸爸|叔叔)']
    elif g == "female":
        patterns = [r'[她]', r'(?:女士|女孩|女人|女儿|母亲|姐姐|妹妹|奶奶|妈妈|阿姨)']
    else:
        patterns = [r'[它]', r'(?:东西|物体|猫|狗)']
    for pat in patterns:
        m = re.search(pat, prev_sentence)
        if m:
            # 词距离 ≈ 字符距离 / 2
            return max(1, m.start() // 2)
    return None


def backtracking_prediction(text: str) -> list[float]:
    """对全文每句计算回溯重读预测得分。"""
    sents = _split_sentences(text)
    scores = []
    prev_sent = ""

    for s in sents:
        pronouns = re.findall(r'[他她它]们?|这|那', s)
        if not pronouns:
            scores.append(0.0)
            prev_sent = s
            continue

        distances = []
        for p in pronouns:
            dist = _find_antecedent(p, prev_sent)
            if dist is not None:
                distances.append(dist)

        score = (sum(distances) / max(len(distances), 1)) / 100.0 if distances else 0.0
        scores.append(round(min(score, 1.0), 4))
        prev_sent = s

    return scores
