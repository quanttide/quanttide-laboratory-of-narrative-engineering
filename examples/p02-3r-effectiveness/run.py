#!/usr/bin/env python3
"""
p02 — 3R 循环效果度量实验

对 3 篇初稿运行 5 轮 3R（Review → Reflect → Rewrite），
每轮记录 5 维评分，分析收益递减。
"""

import json
import os
import sys
from pathlib import Path

import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
FICTION_ROOT = Path(__file__).resolve().parents[4] / "assets" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

EXPERIMENTAL = [
    {"id": "A", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md"},
    {"id": "B", "name": "赏雪谈心", "path": "校园言情/3_初稿/赏雪谈心.md"},
    {"id": "C", "name": "第六章（论坛热搜）", "path": "校园言情/3_初稿/6_第六章.md"},
]

REFERENCES = [
    {"id": "R1", "name": "深夜失眠", "path": "职场言情/4_成稿/1_2_深夜失眠.md"},
    {"id": "R2", "name": "傍晚小龙虾", "path": "职场言情/4_成稿/2_3_傍晚小龙虾.md"},
    {"id": "R3", "name": "书房陪伴", "path": "职场言情/4_成稿/10_1_书房陪伴.md"},
]

MAX_ROUNDS = 5


def read_article(path: str) -> str:
    full_path = FICTION_ROOT / path
    text = full_path.read_text("utf-8")
    lines = text.split("\n")
    body_lines = ["" if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body_lines).strip()


def call_llm(prompt: str, system: str = "") -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-chat", "messages": messages, "temperature": 0.3},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_review_prompt(text: str, references: list[str]) -> str:
    ref_text = "\n\n---\n".join(f"【参考文章 {i+1}】\n{r[:500]}" for i, r in enumerate(references))
    return f"""你是一个专业写作评审。请评审下面的文章，输出 5 维评分和空隙列表。

评分维度（每项 0-10）：
1. 空隙密度：文本中有多少时间跳跃、对话间隙、动作空隙、视角切换、过渡压缩（0=极多空隙，10=几乎没有）
2. 风格一致度：与参考文章风格的吻合程度（参考文章附后）
3. 情感张力：情感表达的层次感和释放节奏（0=平淡，10=感染力强）
4. 细节密度：有多少具体可感的物象细节（0=空洞，10=细节丰富）
5. 整体评分：综合可读性、完整性、感染力

输出 JSON：
{{
  "scores": {{"gap": 0-10, "style": 0-10, "tension": 0-10, "detail": 0-10, "overall": 0-10}},
  "gaps": [{{"type": "time_jump/dialog_gap/action_gap/perspective_shift/transition", "location": "段落位置描述", "detail": "问题说明"}}]
}}

参考文章（同一作者的好文章范例）：
{ref_text}

待评审文章：
{text}"""


def build_reflect_prompt(text: str, review_result: dict) -> str:
    gaps = review_result.get("gaps", [])
    scores = review_result.get("scores", {})
    gap_text = "\n".join(f"- {g['type']}: {g['detail']}" for g in gaps) if gaps else "- 无明显空隙"
    low_dims = [k for k, v in scores.items() if v is not None and v < 6]

    prompt = f"""基于以下评审结果，为作者生成具体的改写提示。

评审结果：
{json.dumps(scores, ensure_ascii=False)}

检测到的空隙：
{gap_text}

需要改进的低分维度：{', '.join(low_dims) if low_dims else '无'}

请输出 3-5 条具体的改写提示，每条包含：要改什么、怎么改、预期效果。

输出 JSON：
{{
  "suggestions": [
    {{"target": "修改目标（哪段/哪个方面）", "action": "具体修改方法", "expected": "预期效果"}}
  ]
}}"""
    return prompt


def build_rewrite_prompt(text: str, suggestions: list[dict]) -> str:
    sug_text = "\n".join(f"{i+1}. {s['action']}（目标：{s['target']}）" for i, s in enumerate(suggestions))
    return f"""请根据以下改写提示修改文章。保持原文的整体结构和风格，只针对性修改。

改写提示：
{sug_text}

输出格式：直接输出修改后的完整文章，不要额外的说明文字。

原文：
{text}"""


def build_score_only_prompt(text: str, references: list[str]) -> str:
    """只评分，不检测空隙（用于基线后的轮次）"""
    ref_text = "\n\n---\n".join(f"【参考文章 {i+1}】\n{r[:500]}" for i, r in enumerate(references))
    return f"""请评审下面文章，输出 5 维评分（0-10）。

维度：gap(空隙/流畅度), style(风格一致度), tension(情感张力), detail(细节密度), overall(整体)

参考文章：{ref_text}

输出 JSON：{{"scores": {{"gap": 0, "style": 0, "tension": 0, "detail": 0, "overall": 0}}}}

文章：
{text}"""


def run_experiment():
    RESULTS_DIR.mkdir(exist_ok=True)

    refs = [read_article(r["path"]) for r in REFERENCES]

    for art in EXPERIMENTAL:
        print(f"\n{'='*60}")
        print(f"文章 {art['id']}: {art['name']}")
        print(f"{'='*60}")

        text = read_article(art["path"])
        round_data = []

        for rnd in range(1, MAX_ROUNDS + 1):
            round_file = RESULTS_DIR / f"{art['id']}_round{rnd}.json"
            if round_file.exists():
                print(f"  第 {rnd} 轮 ← 读取缓存")
                round_data.append(json.loads(round_file.read_text("utf-8")))
                # 更新 text 为上一轮改写结果
                text = round_data[-1].get("rewritten_text", text)
                continue

            print(f"  第 {rnd} 轮...")

            # Step 1: Review
            print(f"    Review...", end=" ", flush=True)
            try:
                review_raw = call_llm(build_review_prompt(text, refs))
                review_raw = review_raw.strip()
                if review_raw.startswith("```"):
                    review_raw = review_raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                review_result = json.loads(review_raw)
                print(f"✓ 整体={review_result['scores']['overall']}")
            except Exception as e:
                print(f"✗ {e}")
                review_result = {"scores": {"gap": None, "style": None, "tension": None, "detail": None, "overall": None}, "gaps": []}

            # Step 2: Reflect
            print(f"    Reflect...", end=" ", flush=True)
            try:
                reflect_raw = call_llm(build_reflect_prompt(text, review_result))
                reflect_raw = reflect_raw.strip()
                if reflect_raw.startswith("```"):
                    reflect_raw = reflect_raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                reflect_result = json.loads(reflect_raw)
                suggestions = reflect_result.get("suggestions", [])
                print(f"✓ {len(suggestions)} 条建议")
            except Exception as e:
                print(f"✗ {e}")
                suggestions = []

            # Step 3: Rewrite
            if suggestions:
                print(f"    Rewrite...", end=" ", flush=True)
                try:
                    rewritten = call_llm(build_rewrite_prompt(text, suggestions))
                    rewritten = rewritten.strip()
                    if rewritten.startswith("```"):
                        rewritten = rewritten.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                    print(f"✓ {len(rewritten)} 字")
                except Exception as e:
                    print(f"✗ {e}")
                    rewritten = text
            else:
                rewritten = text
                print(f"    Rewrite → 无建议，跳过")

            # 保存该轮数据
            round_entry = {
                "round": rnd,
                "scores": review_result["scores"],
                "gaps": review_result.get("gaps", []),
                "suggestions": suggestions,
                "rewritten_text": rewritten,
            }
            round_file.write_text(json.dumps(round_entry, ensure_ascii=False, indent=2), "utf-8")
            round_data.append(round_entry)
            text = rewritten


def analyze():
    print(f"\n\n{'='*60}")
    print("p02 分析报告：3R 循环效果度量")
    print(f"{'='*60}")

    for art in EXPERIMENTAL:
        print(f"\n## {art['id']}: {art['name']}")
        print()

        rounds = []
        for rnd in range(1, MAX_ROUNDS + 1):
            f = RESULTS_DIR / f"{art['id']}_round{rnd}.json"
            if f.exists():
                rounds.append(json.loads(f.read_text("utf-8")))

        if not rounds:
            print("  无数据")
            continue

        # 评分表
        dims = ["gap", "style", "tension", "detail", "overall"]
        header = f"  {'轮次':>4}  " + "  ".join(f"{d:>7}" for d in dims)
        print(f"  {header}")
        print(f"  {'-' * (len(header))}")

        prev = None
        for r in rounds:
            s = r["scores"]
            vals = [s.get(d, "-") for d in dims]
            row = f"  {r['round']:>4}  " + "  ".join(f"{str(v):>7}" for v in vals)
            print(row)

            curr = sum(v for v in vals if isinstance(v, (int, float)))
            if prev is not None:
                delta = curr - prev
            prev = curr

        # 找收益递减拐点
        print()
        improvements = []
        prev_total = None
        for r in rounds:
            s = r["scores"]
            total = sum(s.get(d, 0) or 0 for d in dims)
            if prev_total is not None:
                imp = total - prev_total
                improvements.append((r["round"], imp))
            prev_total = total

        if improvements:
            print(f"  {'轮次':>4}  {'改善值':>6}  {'改善率':>6}")
            print(f"  {'-'*20}")
            for rnd, imp in improvements:
                rate = ""
                if len(improvements) > 0:
                    first_imp = improvements[0][1]
                    if first_imp != 0 and rnd > 1:
                        rate = f"{imp/first_imp*100:>5.0f}%"
                print(f"  {rnd:>4}  {imp:>+6.1f}  {rate:>6}")

            # 递减拐点：首次改善<上一轮50%
            for i in range(1, len(improvements)):
                if improvements[i][1] < improvements[i-1][1] * 0.5:
                    print(f"\n  ⬇ 递减拐点：第 {improvements[i][0]} 轮（改善 {improvements[i][1]:+.1f} < 上一轮 {improvements[i-1][1]:+.1f} 的 50%）")
                    break
            else:
                print(f"\n  ➡ 5 轮内未出现明显递减")

        # 空隙变化
        print()
        print(f"  空隙数量变化：")
        for r in rounds:
            gap_count = len(r.get("gaps", []))
            print(f"    第 {r['round']} 轮: {gap_count} 个空隙")


def main():
    print("=" * 60)
    print("p02 — 3R 循环效果度量实验")
    print("=" * 60)
    run_experiment()
    analyze()


if __name__ == "__main__":
    main()
