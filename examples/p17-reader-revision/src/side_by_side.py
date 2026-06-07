"""Step 3: 材料并排

核心步骤。LLM 不生成反思——只做一件事：
把契约立场和读者回响并排放在一起，不做任何分析、总结、建议。
"""
import json
from packages.llm import call_llm

CO_AUTHOR_PROMPT = """你是一位网络小说作者，和另一位作者共用同一套写作契约（style / motif / story 定义）。对方发来一个刚写好的片段，请你作为共同作者给直觉反馈。

## 你们共同的写作契约

{contracts}

## 片段

位置：{location}
原文：{quote}

## 任务

作为同样遵守这份契约的写作者，你读到这段的第一反应是什么？
- 它符合你们约定的写法吗？还是让你觉得"这里有点不对劲"？
- 不要说"作者想……"，只说"我看到……"或"我读到……"。
- 如果你觉得它越界了，点出哪里越界。
- 一句话，不超过 30 字。

输出纯文本。"""


def simulate_co_author(text_point, contracts, temperature=0.3) -> str:
    """模拟共同作者对文本点的直觉反应。"""
    from src.contract import format_style, format_motif, format_story
    c = format_style(contracts["style_yaml"])
    c += "\n" + format_motif(contracts["motif_yaml"])
    c += "\n" + format_story(contracts["story_yaml"])
    prompt = CO_AUTHOR_PROMPT.format(
        contracts=c,
        location=text_point["location"],
        quote=text_point["quote"],
    )
    raw = call_llm(prompt, system="你是一个网络小说作者。只说直觉，不分析不评价。", temperature=temperature)
    return raw.strip().strip('"\'')


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


def simulate_reader_opinions(text_point, reader_response, profiles, temperature=0.3):
    """让 LLM 模拟各画像在这个文本点上实际读到了什么。

    返回 dict: {profile_id: "该画像读者的阅读感受"}
    """
    ratings = reader_response.get("scene_ratings", {})
    if not ratings:
        return {}

    # 提取关键分歧的画像
    signals = reader_response.get("key_signals", {})
    max_pair = signals.get("max_divergence_pair", [])
    key_profiles = set()
    if max_pair and len(max_pair) >= 2:
        key_profiles.add(max_pair[0])
        key_profiles.add(max_pair[1])
    for a in signals.get("anomalies", []):
        key_profiles.add(a["profile"])
    # 再加 P0/P1/P3 作为基准
    for p in ["P1", "P3"]:
        key_profiles.add(p)

    opinions = {}
    for pid in key_profiles:
        prof = profiles.get(pid, {})
        r = ratings.get(pid, {})
        if not prof or not r:
            continue
        prompt = (
            f"你是一位{prof.get('label', pid)}读者。\n"
            f"{prof.get('behavioral_anchor', '')}\n\n"
            f"你在读以下这个场景片段（位置：{text_point['location']}）：\n"
            f"「{text_point['quote']}」\n\n"
            f"用一句话说出：你在这个位置上读到了什么？感受到了什么？\n"
            f"不要评价写得好不好，只说作为{prof.get('label', pid)}你的第一感受。\n"
            f"输出纯文本，不要 JSON。"
        )
        raw = call_llm(prompt, system="你是一个普通读者。只说感受，不分析不评价。", temperature=temperature)
        opinions[pid] = raw.strip().strip('"\'')
    return opinions


def format_reader_side_by_side(text_point, reader_response, profiles, opinions: dict = None) -> str:
    """从读者回响构建创作者可读的回响文本。

    输出格式：
      P3（资深老书虫）读到的："......"（cliche=1.72）
      P1（甜宠少女）读到的："......"（cliche=3.11）
    """
    ratings = reader_response.get("scene_ratings", {})
    signals = reader_response.get("key_signals", {})
    parts = []

    if ratings and opinions:
        lines = []
        for pid in ["P3", "P1", "P2", "P4", "P5"]:
            if pid in opinions and pid in ratings:
                label = profiles.get(pid, {}).get("label", pid)
                op = opinions[pid]
                cl = ratings[pid].get("cliche_level", "?")
                em = ratings[pid].get("emotional_impact", "?")
                lines.append(f"  {pid}（{label}）读到的：「{op}」")
                if pid in ["P3", "P1"] and cl != "?":
                    lines[-1] += f"（套路感={cl}）"
        if lines:
            parts.append("不同读者在这个位置上的感受：")
            parts.extend(lines)

    # 附加关键分歧（简化，不用统计术语）
    max_pair = signals.get("max_divergence_pair")
    if max_pair and len(max_pair) >= 4:
        p1_label = profiles.get(max_pair[0], {}).get("label", max_pair[0])
        p2_label = profiles.get(max_pair[1], {}).get("label", max_pair[1])
        parts.append(
            f"  → {max_pair[0]}（{p1_label}）和{max_pair[1]}（{p2_label}）"
            f"在「{max_pair[2]}」上感受差异最大（差{max_pair[3]}分）"
        )

    return "\n".join(parts).strip() if parts else "（无读者回响数据）"


def build_reader_text(reader_response: dict, profiles: dict) -> str:
    """（保留旧接口兼容）"""
    ratings = reader_response.get("scene_ratings", {})
    signals = reader_response.get("key_signals", {})
    parts = []

    if ratings:
        lines = ["各画像在本场景的评分："]
        # 简化为一行
        profile_order = ["P1", "P2", "P3", "P4", "P5"]
        values = []
        for pid in profile_order:
            if pid in ratings:
                r = ratings[pid]
                cl = r.get("cliche_level", "?")
                values.append(f"{pid}={cl}")
        if values:
            lines.append("  cliche_level: " + ", ".join(values))
        parts.append("\n".join(lines))

    return "\n".join(parts).strip() if parts else "（无读者回响数据）"


def generate_side_by_side(text_point, contract_annotation, reader_response, profiles, contracts, temperature=0.3):
    """生成材料并排输出。"""
    # 共同作者反馈（LLM）——模拟另一位遵守契约的写作者的直觉
    co_author_text = simulate_co_author(text_point, contracts, temperature)
    contract_annotation["co_author"] = co_author_text

    # 模拟读者意见（LLM）
    opinions = simulate_reader_opinions(text_point, reader_response, profiles, temperature)
    reader_response["reader_opinions"] = opinions
    reader_text = format_reader_side_by_side(text_point, reader_response, profiles, opinions)

    prompt = PROMPT_TEMPLATE.format(
        location=text_point["location"],
        quote=text_point["quote"],
        co_author_text=co_author_text,
        reader_text=reader_text,
    )

    raw = call_llm(
        prompt,
        system=SYSTEM_PROMPT,
        temperature=temperature,
    )
    return raw
