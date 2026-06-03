#!/usr/bin/env python3
"""
p02 — 3R 循环效果度量实验（修正版）

按正确的 3R 定义：
  Review:  理解文本意图      → {genre, intent, stage, summary}
  Reflect: 检测空隙 + 多角度归因 → [{gap, 结构/人物/读者/技法归因}]
  Rewrite: 带理解去修改      → 新版本
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

MAX_ROUNDS = 5
GAP_TYPES = ["time_jump", "dialog_gap", "action_gap", "perspective_shift", "transition"]


def read_article(path: str) -> str:
    text = (FICTION_ROOT / path).read_text("utf-8")
    lines = text.split("\n")
    body = ["" if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


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


def build_review_prompt(text: str) -> str:
    """Review: 只理解意图，不找问题"""
    return f"""请阅读下面的文章片段，从写作意图的角度分析它。

不需要找问题。只需要理解这段文本在做什么。

输出 JSON：
{{
  "genre": "场景体裁分类（如：重逢场景/日常对话/情感释放/事件驱动），10字以内",
  "intent": "作者的创作意图（如：营造暧昧氛围/推进人物关系/展示角色性格），20字以内",
  "stage": "根据文本呈现出来的完成度，判断这是初稿还是成稿，以及一句话依据",
  "summary": "一句话总结这段文本在干什么（30字以内）"
}}

文章：
{text}"""


def build_reflect_prompt(text: str, review: dict) -> str:
    """Reflect: 先检测空隙，再多角度归因"""
    return f"""你是一个写作诊断专家。以下是对当前文本的意图理解：

体裁：{review.get('genre', '')}
意图：{review.get('intent', '')}
阶段：{review.get('stage', '')}

请检测文本中的写作空隙，并对每个空隙从 4 个角度分析深层原因。

空隙类型（5 种）：
- time_jump：时间跳跃没有过渡标记
- dialog_gap：对话之间缺少反应或沉默描写
- action_gap：动作之间缺少衔接
- perspective_shift：视角切换缺少锚点
- transition：场景转换缺少桥梁

必须输出 JSON 数组，格式如下（不要额外文字）：
[
  {{
    "gap_type": "time_jump",
    "location": "具体的段落位置描述",
    "detail": "问题说明",
    "structure": "叙事结构角度的归因",
    "psychology": "人物心理角度的归因",
    "reader": "读者期待角度的归因",
    "craft": "有意识留白 或 无意识忽略",
    "root_cause": "一句话总结根本原因"
  }}
]

文本：
{text}"""


def build_rewrite_prompt(text: str, review: dict, analysis: list[dict]) -> str:
    """Rewrite: 带着意图理解 + 空隙归因去修改"""
    analysis_text = "\n".join(
        f"{i+1}. [{a['gap_type']}] {a.get('detail', '')}\n"
        f"   叙事结构: {a.get('structure', '')}\n"
        f"   人物心理: {a.get('psychology', '')}\n"
        f"   读者期待: {a.get('reader', '')}\n"
        f"   写作技法: {a.get('craft', '')}\n"
        f"   根本原因: {a.get('root_cause', '')}"
        for i, a in enumerate(analysis)
    )

    return f"""当前文本的定位：
体裁：{review.get('genre', '')}
意图：{review.get('intent', '')}

对文本中空隙的诊断：
{analysis_text}

请带着以上理解重新修改文章。注意：
- 如果空隙被判定为"有意识留白"，不需要修改
- 如果空隙被判定为"无意识忽略"，针对性地补写
- 保持原文的风格和节奏
- 可以补写细节、调整过渡，但不要改变叙事走向

输出格式：直接输出修改后的完整文章。

原文：
{text}"""


def clear_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return raw


def run_experiment():
    RESULTS_DIR.mkdir(exist_ok=True)

    for art in EXPERIMENTAL:
        print(f"\n{'='*60}")
        print(f"文章 {art['id']}: {art['name']}")
        print(f"{'='*60}")

        text = read_article(art["path"])

        for rnd in range(1, MAX_ROUNDS + 1):
            round_file = RESULTS_DIR / f"{art['id']}_round{rnd}.json"
            if round_file.exists():
                print(f"  第 {rnd} 轮 ← 读取缓存")
                data = json.loads(round_file.read_text("utf-8"))
                text = data.get("rewritten_text", text)
                continue

            print(f"  第 {rnd} 轮...")

            # Step 1: Review
            print(f"    Review...", end=" ", flush=True)
            try:
                raw = clear_json(call_llm(build_review_prompt(text)))
                review = json.loads(raw)
                print(f"✓ {review.get('genre', '?')}")
            except Exception as e:
                print(f"✗ {e}")
                review = {"genre": "?", "intent": "?", "stage": "?", "summary": "?"}

            # Step 2: Reflect（检测 + 归因）
            print(f"    Reflect...", end=" ", flush=True)
            analysis = []
            for attempt in range(2):
                try:
                    raw = clear_json(call_llm(build_reflect_prompt(text, review)))
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        analysis = parsed
                    elif isinstance(parsed, dict) and "analysis" in parsed:
                        analysis = parsed["analysis"]
                    elif isinstance(parsed, dict):
                        analysis = [parsed]
                    if analysis:
                        break
                except Exception as e:
                    if attempt == 0:
                        continue
                    print(f"✗ {e}")
            if analysis:
                print(f"✓ {len(analysis)} 个空隙")
            else:
                print(f"→ 未检测到空隙")

            # Step 3: Rewrite
            if analysis:
                print(f"    Rewrite...", end=" ", flush=True)
                try:
                    rewritten = clear_json(call_llm(build_rewrite_prompt(text, review, analysis)))
                    print(f"✓ {len(rewritten)} 字")
                except Exception as e:
                    print(f"✗ {e}")
                    rewritten = text
            else:
                rewritten = text
                print(f"    Rewrite → 无空隙，跳过")

            entry = {
                "round": rnd,
                "review": review,
                "analysis": analysis,
                "rewritten_text": rewritten,
            }
            round_file.write_text(json.dumps(entry, ensure_ascii=False, indent=2), "utf-8")
            text = rewritten


def analyze():
    print(f"\n\n{'='*60}")
    print("p02 分析报告：3R 循环（修正版）")
    print(f"{'='*60}")

    for art in EXPERIMENTAL:
        print(f"\n## {art['id']}: {art['name']}")

        rounds = []
        for rnd in range(1, MAX_ROUNDS + 1):
            f = RESULTS_DIR / f"{art['id']}_round{rnd}.json"
            if f.exists():
                rounds.append(json.loads(f.read_text("utf-8")))

        if not rounds:
            continue

        # Review 输出的意图变化
        print(f"\n  Review 输出变化：")
        print(f"  {'轮次':>4}  {'体裁':<12} {'意图':<26} {'阶段':<14}")
        print(f"  {'-'*60}")
        for r in rounds:
            rv = r.get("review", {})
            print(f"  {r['round']:>4}  {rv.get('genre', ''):<12} {rv.get('intent', ''):<26} {rv.get('stage', '')[:12]:<14}")

        # 空隙数量与类型变化
        print(f"\n  空隙变化：")
        total_gaps = []
        for r in rounds:
            a = r.get("analysis", [])
            gaps_detail = ", ".join(f"{g['gap_type']}" for g in a)
            print(f"    第 {r['round']} 轮: {len(a)} 个空隙 [{gaps_detail}]")
            total_gaps.append(len(a))

        # 有意识 vs 无意识（汇总所有轮次）
        conscious_all = 0
        unconscious_all = 0
        total_all = 0
        for r in rounds:
            a = r.get("analysis", [])
            for g in a:
                total_all += 1
                craft = g.get("craft", "")
                if "有意识" in craft or "有意" in craft:
                    conscious_all += 1
                if "无意识" in craft or "忽略" in craft:
                    unconscious_all += 1
        if total_all:
            print(f"\n  留白类型汇总（全部轮次）：")
            print(f"    有意识留白: {conscious_all} / {total_all} ({conscious_all/total_all*100:.0f}%)")
            print(f"    无意识忽略: {unconscious_all} / {total_all} ({unconscious_all/total_all*100:.0f}%)")


def main():
    print("=" * 60)
    print("p02 — 3R 循环效果度量（修正版）")
    print("=" * 60)
    run_experiment()
    analyze()


if __name__ == "__main__":
    main()
