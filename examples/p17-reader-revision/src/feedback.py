"""Step 4: 作者反馈（交互式）

作者看到材料后，对每个文本点给出三选一反馈：
  A — 契约解读准确，我看到差距了
  B — 契约解读准确，但这不是差距
  C — 契约解读不准确
"""
import sys
from packages.io import save_json


FEEDBACK_OPTIONS = {
    "A": "契约解读准确，我看到差距了（最有价值的反馈）",
    "B": "契约解读准确，但这不是差距——这里没有张力（系统灵敏度过高）",
    "C": "契约解读不准确——我的原意不是这样（系统理解错了）",
}


def collect_feedback(text_point, side_by_side_output, output_path):
    """交互式收集作者反馈。

    1. 打印材料并排输出
    2. 展示反馈选项
    3. 读取用户输入（A/B/C + 可选补充说明）
    4. 保存到文件

    返回: dict {choice, comment}
    """
    print()
    print("=" * 70)
    print(f"Step 4: 作者反馈 — {text_point['id']} {text_point['location']}")
    print("=" * 70)
    print()
    print("请阅读以下材料并排输出，然后给出你的反馈：")
    print()
    print(side_by_side_output)
    print()

    # 反馈选项
    print("─" * 50)
    print("你的反馈（三选一）：")
    for key, desc in FEEDBACK_OPTIONS.items():
        print(f"  [{key}] {desc}")
    print()

    # 读取选择
    choice = ""
    while choice not in FEEDBACK_OPTIONS:
        try:
            choice = input("请输入选项 (A/B/C): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print()
            print("反馈已跳过。")
            return {"choice": None, "comment": None, "skipped": True}

    # 可选补充说明
    try:
        comment = input("补充说明（可选，直接回车跳过）: ").strip()
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

    # 保存
    save_json(output_path, feedback)
    print(f"  反馈已保存: {choice}")

    return feedback
