"""Step 4: 作者反馈（交互式，从结构化数据生成摘要）"""
import json
from pathlib import Path
from packages.io import save_json


FEEDBACK_OPTIONS = {
    "A": "契约解读准确，我看到差距了",
    "B": "契约解读准确，但这不是差距——这里没有张力",
    "C": "契约解读不准确——我的原意不是这样",
}


def load_json_safe(path):
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def summarize(text_point, data_dir):
    """从已保存的结构化数据生成精简摘要。"""
    tid = text_point["id"]
    contract = load_json_safe(data_dir / f"{tid}_contract.json")
    reader = load_json_safe(data_dir / f"{tid}_reader.json")

    lines = [f"{tid} {text_point['location']}（{text_point['type']}）"]
    lines.append(f"原文：{text_point['quote']}")
    lines.append("")

    # 契约摘要：维度 + 性质
    if contract and "error" not in contract:
        style_dims = contract.get("style", {}).get("touched_dimensions", [])
        for d in style_dims:
            dim = d.get("dimension", "?")
            nature = d.get("nature", "?")
            lines.append(f"  契约·{dim} → {nature}")
        motifs = contract.get("motif", {}).get("touched_motifs", [])
        for m in motifs:
            lines.append(f"  母题·{m.get('motif', '?')} → {m.get('alignment', '?')}")
        chars = contract.get("story", {}).get("touched_characters", [])
        for c in chars:
            lines.append(f"  角色·{c.get('character', '?')} → {c.get('alignment', '?')}")

    # 读者摘要：关键信号
    if reader and reader.get("scene_ratings"):
        signals = reader.get("key_signals", {})
        max_var = signals.get("max_variance_dimension")
        if max_var and max_var[0]:
            lines.append(f"  读者最大分歧维度：{max_var[0]}（方差={max_var[1]}）")
        pair = signals.get("max_divergence_pair")
        if pair and len(pair) >= 4:
            lines.append(f"  最分歧画像对：{pair[0]} vs {pair[1]} 在 {pair[2]} 上差距 {pair[3]}")
        anomalies = signals.get("anomalies", [])
        for a in anomalies:
            lines.append(f"  异常：{a['profile']} 的 {a['field']}={a['value']}（偏差 {a['deviation']}）")

    return "\n".join(lines)


def collect_feedback(text_point, side_by_side_output, output_path, data_dir=None):
    """交互式收集作者反馈（精简摘要）。"""
    print()
    print("=" * 56)
    print(f"反馈 — {text_point['id']} {text_point['location']}")
    print("=" * 56)
    print()

    if data_dir:
        summary = summarize(text_point, data_dir)
        print(summary)
    else:
        short = "\n".join(side_by_side_output.split("\n")[:6])
        print(short)

    print()
    print("─" * 40)
    for key, desc in FEEDBACK_OPTIONS.items():
        print(f"  [{key}] {desc}")
    print()

    choice = ""
    while choice not in FEEDBACK_OPTIONS:
        try:
            choice = input("选项 (A/B/C): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print()
            return {
                "text_point_id": text_point["id"],
                "location": text_point["location"],
                "choice": None, "comment": None, "skipped": True,
            }

    try:
        comment = input("补充（可选，回车跳过）: ").strip()
    except (EOFError, KeyboardInterrupt):
        comment = ""

    feedback = {
        "text_point_id": text_point["id"],
        "location": text_point["location"],
        "choice": choice,
        "choice_label": FEEDBACK_OPTIONS[choice],
        "comment": comment if comment else None,
        "skipped": False,
    }
    save_json(output_path, feedback)
    print(f"  已保存: {choice}")
    return feedback
