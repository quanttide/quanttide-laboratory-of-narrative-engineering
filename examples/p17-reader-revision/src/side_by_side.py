"""Step 3: 材料并排

核心步骤。LLM 不生成反思——只做一件事：
把契约立场和读者回响并排放在一起，不做任何分析、总结、建议。
"""
import json
from packages.llm import call_llm

SYSTEM_PROMPT = (
    "你是一个材料整理工具。你的唯一任务是把两段信息并排呈现。\n"
    "你绝对不输出：任何分析、总结、结论、建议、评价、判断。\n"
    "你绝对不写：'这意味着…'、'这说明…'、'因此…'、'建议…'、'可以…'、'需要注意…'。\n"
    "你不以判断句结尾。你不替读者完成任何思考。\n"
    "输出止于材料本身。反思发生在读者的脑子里，不在你的输出里。"
)

PROMPT_TEMPLATE = """把以下两段信息并排呈现。只呈现材料，不做任何分析。

## 位置

{location}
"{quote}"

## 契约立场

{contract_text}

## 读者回响

{reader_text}

## 输出格式

用以下格式呈现，只有两个模块，没有第三部分：

────────────────────────────────────────────
位置：{location} "{quote}"
────────────────────────────────────────────

## 契约立场

（引用 style.yaml / motif.yaml / story.yaml 中的相关条款原文 + 该点在契约中的判断）

## 读者回响

（引用 p16 各画像在该场景的评分数据 + 关键信号）

────────────────────────────────────────────
这里没有结论。这是作者需要自己看的东西。
────────────────────────────────────────────

注意：
1. 契约立场部分：直接引用条款原文，不要改写。判断只陈述事实（"该行为属于认知泄露"），不做评价（"这是不对的"）。
2. 读者回响部分：只呈现数据和分歧，不要解释"这意味着什么"。
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
    """从读者回响映射结果构建可读的读者回响文本。"""
    parts = []

    ratings = reader_response.get("scene_ratings", {})
    if ratings:
        lines = ["各画像在本场景的评分："]
        header = "画像        writing  emotional  character  cliche"
        lines.append(header)
        for pid in ["P1", "P2", "P3", "P4", "P5"]:
            if pid in ratings:
                r = ratings[pid]
                label = profiles.get(pid, {}).get("label", pid)
                w = r.get("writing_quality", "?")
                e = r.get("emotional_impact", "?")
                cr = r.get("character_realism", "?")
                cl = r.get("cliche_level", "?")
                w_s = f"{w:<8}" if isinstance(w, (int, float)) else f"{str(w):<8}"
                e_s = f"{e:<10}" if isinstance(e, (int, float)) else f"{str(e):<10}"
                cr_s = f"{cr:<10}" if isinstance(cr, (int, float)) else f"{str(cr):<10}"
                cl_s = f"{cl}" if isinstance(cl, (int, float)) else str(cl)
                lines.append(f"  {pid} {label:<8}  {w_s}{e_s}{cr_s}{cl_s}")
        parts.append("\n".join(lines))

    signals = reader_response.get("key_signals", {})
    if signals.get("warning"):
        parts.append(f"\n⚠️ {signals['warning']}")
    else:
        max_var = signals.get("max_variance_dimension")
        if max_var and max_var[0]:
            parts.append(f"\n画像间方差最大的维度：{max_var[0]}（方差={max_var[1]}）")

        max_pair = signals.get("max_divergence_pair")
        if max_pair and len(max_pair) >= 4:
            p1_label = profiles.get(max_pair[0], {}).get("label", max_pair[0])
            p2_label = profiles.get(max_pair[1], {}).get("label", max_pair[1])
            parts.append(
                f"分歧最大的画像对：{max_pair[0]}（{p1_label}）vs "
                f"{max_pair[1]}（{p2_label}）在 {max_pair[2]} 上差距 {max_pair[3]}"
            )

        anomalies = signals.get("anomalies", [])
        if anomalies:
            parts.append("\n异常值：")
            for a in anomalies:
                p_label = profiles.get(a["profile"], {}).get("label", a["profile"])
                parts.append(
                    f"  {a['profile']}（{p_label}）的 {a['field']}={a['value']}"
                    f"（均值 {a['mean']}，偏差 {a['deviation']}）"
                )

    return "\n".join(parts).strip() if parts else "（无读者回响数据）"


def generate_side_by_side(text_point, contract_annotation, reader_response, profiles, temperature=0.3):
    """生成材料并排输出。"""
    contract_text = build_contract_text(contract_annotation)
    reader_text = build_reader_text(reader_response, profiles)

    # 如果合同文本或读者文本为空/无数据，构建一个最小版本
    if not contract_text or contract_text == "（无触及条款）":
        contract_text = "（该文本点未触及任何明确契约条款）"

    prompt = PROMPT_TEMPLATE.format(
        location=text_point["location"],
        quote=text_point["quote"],
        contract_text=contract_text,
        reader_text=reader_text,
    )

    # 这里使用非 JSON 输出模式（直接输出格式化的 markdown 文本）
    raw = call_llm(
        prompt,
        system=SYSTEM_PROMPT,
        temperature=temperature,
    )
    return raw
