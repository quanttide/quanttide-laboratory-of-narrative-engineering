"""Step 3: 材料并排

核心步骤。LLM 不生成反思——只做一件事：
把契约立场和读者回响并排放在一起，不做任何分析、总结、建议。
"""
import json
from packages.llm import call_llm




SYSTEM_PROMPT = (
    "你是一个排版工具。你的唯一任务是把两段信息并排呈现。\n"
    "你绝对不输出：任何分析、总结、结论、建议、评价、判断。\n"
    "你绝对不写：'这意味着…'、'这说明…'、'因此…'、'建议…'、'可以…'、'需要注意…'。\n"
    "你不以判断句结尾。你不替作者完成任何思考。\n"
    "输出止于材料本身。反思发生在作者的脑子里，不在你的输出里。"
)

PROMPT_TEMPLATE = """把以下两段信息并排呈现。只呈现材料，不做任何分析。

## 位置

{location}
"{quote}"

## 共同作者反馈

{co_author_text}

## 读者回响

{reader_text}

## 输出格式

────────────────────────────────────────────
位置：{location} "{quote}"
────────────────────────────────────────────

## 共同作者

（另一位移用这份契约的写作者的直觉反应）

## 读者回响

（不同读者在这个位置上实际读到了什么 + 感受差异）

────────────────────────────────────────────
这里没有结论。这是作者需要自己看的东西。
────────────────────────────────────────────

注意：
1. 共同作者部分：用第一人称，像在跟作者聊天。
2. 读者回响部分：不同读者的话并排放，不要分析数据。
3. 绝对不能出现以下句式：
   - "这意味着……" / "这说明……"
   - "建议……" / "可以……" / "需要……"
   - "因此……" / "所以……"
   - 任何以判断结尾的句子
"""


def build_contract_text(contract_annotation: dict) -> str:
    """从契约标注结果构建可读的契约立场文本。"""
    parts = []

    style = contract_annotation.get("style", {})
    touched = style.get("touched_dimensions", [])
    if touched:
        parts.append("style.yaml 触及的维度 / boundaries：")
        for t in touched:
            parts.append(f"  维度：{t.get('dimension', '?')}")
            parts.append(f"  边界：{t.get('boundary', '?')}")
            parts.append(f"  性质：{t.get('nature', '?')}")
            parts.append(f"  理由：{t.get('reason', '?')}")
            parts.append("")

    motif = contract_annotation.get("motif", {})
    touched_m = motif.get("touched_motifs", [])
    if touched_m:
        parts.append("motif.yaml 涉及的母题：")
        for m in touched_m:
            parts.append(f"  母题：{m.get('motif', '?')}")
            parts.append(f"  使用方式：{m.get('usage', '?')}")
            parts.append(f"  对齐度：{m.get('alignment', '?')}")
            parts.append("")

    story = contract_annotation.get("story", {})
    chars = story.get("touched_characters", [])
    if chars:
        parts.append("story.yaml 相关角色：")
        for c in chars:
            parts.append(f"  角色：{c.get('character', '?')}")
            parts.append(f"  评估：{c.get('behavior_assessment', '?')}")
            parts.append(f"  一致度：{c.get('alignment', '?')}")
            parts.append("")

    tensions = story.get("touched_tensions", [])
    if tensions:
        parts.append("story.yaml 相关 tension：")
        for t in tensions:
            parts.append(f"  {t.get('tension', '?')}")
            parts.append(f"  关联：{t.get('relevance', '?')}")
            parts.append("")

    return "\n".join(parts).strip() if parts else "（无触及条款）"


def build_reader_text(reader_response: dict, profiles: dict) -> str:
    """将 p16 评分数据转为创作者可读的文本。

    只呈现数据，不做任何模拟或分析。
    """
    ratings = reader_response.get("scene_ratings", {})
    signals = reader_response.get("key_signals", {})
    parts = []

    if ratings:
        lines = ["各画像套路感评分（1-5，越低=越不套路）："]
        for pid in ["P3", "P1", "P2", "P4", "P5"]:
            r = ratings.get(pid, {})
            cl = r.get("cliche_level")
            if cl is not None:
                label = profiles.get(pid, {}).get("label", pid)
                lines.append(f"  {pid}（{label}）: {cl:.1f}")
        parts.append("\n".join(lines))

    max_pair = signals.get("max_divergence_pair")
    if max_pair and len(max_pair) >= 4:
        parts.append(
            f"分歧最大：{max_pair[0]}与{max_pair[1]}在「{max_pair[2]}」上差{max_pair[3]}分"
        )

    anom = signals.get("anomalies", [])
    if anom:
        a = anom[0]
        parts.append(f"异常：{a['profile']}的{a['field']}={a['value']}（其余均值{a['mean']:.1f}）")

    return "\n".join(parts).strip() if parts else "（无读者回响数据）"


def generate_side_by_side(text_point, contract_annotation, reader_response, profiles, contracts, temperature=0.3):
    """生成材料并排输出。只呈现实际数据，不做任何 LLM 模拟。"""
    reader_text = build_reader_text(reader_response, profiles)

    prompt = PROMPT_TEMPLATE.format(
        location=text_point["location"],
        quote=text_point["quote"],
        co_author_text="",
        reader_text=reader_text,
    )

    raw = call_llm(
        prompt,
        system=SYSTEM_PROMPT,
        temperature=temperature,
    )
    return raw
