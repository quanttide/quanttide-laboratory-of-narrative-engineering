"""Step 4: 作者反馈格式

作者看到材料后，对每个文本点给出三选一反馈：
  A — 契约解读准确，我看到差距了
  B — 契约解读准确，但这不是差距
  C — 契约解读不准确
"""

FEEDBACK_FORMAT = """
对这个点的反馈：

[ A ] 契约解读准确，我看到差距了（最有价值的反馈）
[ B ] 契约解读准确，但这不是差距——这里没有张力（系统灵敏度过高）
[ C ] 契约解读不准确——我的原意不是这样（系统理解错了）

补充说明（可选）：____________
"""


def generate_feedback_prompt(text_point):
    """生成反馈提示。"""
    return (
        f"## 文本点：{text_point['location']}\n\n"
        f'原文："{text_point["quote"]}"\n\n'
        f"请对上述材料并排输出给出反馈：\n"
        f"{FEEDBACK_FORMAT}\n\n"
        f"输出 JSON：\n"
        f'{{"choice": "A|B|C", "comment": "补充说明（可选）"}}'
    )
