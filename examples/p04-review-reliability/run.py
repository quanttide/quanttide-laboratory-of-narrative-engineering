#!/usr/bin/env python3
"""
p04 — Review 意图理解可靠性实验

同一篇文章多次 LLM Review，检验输出是否稳定。
"""

import json
import os
import sys
import random
from pathlib import Path

import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
FICTION_ROOT = Path(__file__).resolve().parents[4] / "assets" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

ARTICLES = [
    {"id": "A", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md"},
    {"id": "B", "name": "便利店闲坐", "path": "职场言情/4_成稿/4_1_便利店闲坐.md"},
    {"id": "C", "name": "第六章（论坛热搜）", "path": "校园言情/3_初稿/6_第六章.md"},
]

TRIALS = 5


def read_article(path: str) -> str:
    text = (FICTION_ROOT / path).read_text("utf-8")
    lines = text.split("\n")
    body = ["" if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def call_llm(prompt: str) -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的文本分析助手。理解文本的意图和类型。输出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_review_prompt(text: str) -> str:
    return f"""请阅读下面的文章片段，从写作意图的角度分析它。

不需要找问题。只需要理解这段文本在做什么。

输出 JSON：
{{
  "genre": "场景体裁分类（如：重逢场景/日常对话/事件驱动/情感释放/...），10字以内",
  "intent": "作者的创作意图（如：营造暧昧氛围/推进人物关系/展示角色性格/...），20字以内",
  "stage": "该片段属于写作的哪个阶段（如：初稿/成稿），以及依据",
  "summary": "一句话总结这段文本在干什么"
}}

文章：
{text}"""


def run():
    RESULTS_DIR.mkdir(exist_ok=True)

    for art in ARTICLES:
        print(f"\n{'='*50}")
        print(f"文章 {art['id']}: {art['name']}")
        print(f"{'='*50}")

        text = read_article(art["path"])

        for t in range(1, TRIALS + 1):
            out_file = RESULTS_DIR / f"{art['id']}_trial{t}.json"
            if out_file.exists():
                print(f"  第 {t} 次 ← 读取缓存")
                continue

            print(f"  第 {t} 次...", end=" ", flush=True)
            try:
                raw = call_llm(build_review_prompt(text))
                raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                result = json.loads(raw)
                result["_trial"] = t
                result["_article"] = art["id"]
                out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
                print(f"✓ {result.get('genre', '?')}")
            except Exception as e:
                print(f"✗ {e}")


def analyze():
    print(f"\n\n{'='*60}")
    print("p04 分析报告：Review 意图理解可靠性")
    print(f"{'='*60}")

    for art in ARTICLES:
        print(f"\n## {art['id']}: {art['name']}")

        trials = []
        for t in range(1, TRIALS + 1):
            f = RESULTS_DIR / f"{art['id']}_trial{t}.json"
            if f.exists():
                trials.append(json.loads(f.read_text("utf-8")))

        if not trials:
            continue

        # 体裁一致性
        genres = [t.get("genre", "?") for t in trials]
        unique_genres = set(genres)
        print(f"\n  体裁: {genres}")
        print(f"  唯一值: {unique_genres}")
        print(f"  一致性: {len(unique_genres) == 1}")

        # 意图一致性（是否矛盾）
        intents = [t.get("intent", "") for t in trials]
        print(f"\n  意图: {intents}")

        # 阶段判断
        stages = [t.get("stage", "")[:40] for t in trials]
        print(f"\n  阶段: {stages}")

        # 摘要
        summaries = [t.get("summary", "") for t in trials]
        print(f"\n  摘要:")
        for i, s in enumerate(summaries):
            print(f"    T{i+1}: {s[:80]}")

    # 跨文章区分度
    print(f"\n{'='*50}")
    print("跨文章区分度验证")
    print(f"{'='*50}")

    all_outputs = []
    for art in ARTICLES:
        for t in range(1, TRIALS + 1):
            f = RESULTS_DIR / f"{art['id']}_trial{t}.json"
            if f.exists():
                d = json.loads(f.read_text("utf-8"))
                all_outputs.append(d)

    # 打乱
    random.shuffle(all_outputs)

    # 让 LLM 聚类
    items_text = "\n\n".join(
        f"[样本 {i+1}]\n体裁: {d.get('genre', '')}\n意图: {d.get('intent', '')}\n摘要: {d.get('summary', '')}"
        for i, d in enumerate(all_outputs)
    )

    prompt = f"""以下 15 个样本是对 3 篇不同文章的 Review 结果（每篇 Review 了 5 次）。
请根据体裁、意图和摘要的相似度，将它们分成 3 组（每组对应一篇文章）。

每组内的样本应来自同一篇文章。

输出格式：
{{"groups": [{{"id": "组1", "samples": [1, 3, 5, ...], "reason": "..."}}, ...]}}

样本：
{items_text}"""

    try:
        raw = call_llm(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        clustering = json.loads(raw)

        print("\n聚类结果：")
        id_to_article = {}
        for d in all_outputs:
            id_to_article[d["_article"]] = id_to_article.get(d["_article"], 0) + 1

        correct = 0
        total = 0
        for g in clustering.get("groups", []):
            samples = g.get("samples", [])
            arts = [all_outputs[s - 1]["_article"] for s in samples if s <= len(all_outputs)]
            unique_arts = set(arts)
            print(f"  {g['id']}: 样本{samples} → {unique_arts} ({g.get('reason', '')[:40]})")
            if len(unique_arts) == 1:
                correct += len(samples)
            total += len(samples)

        rate = correct / total * 100 if total else 0
        print(f"\n  同文章聚类率: {correct}/{total} = {rate:.0f}%")

    except Exception as e:
        print(f"  聚类失败: {e}")


def main():
    print("=" * 60)
    print("p04 — Review 意图理解可靠性实验")
    print("=" * 60)
    run()
    analyze()


if __name__ == "__main__":
    main()
