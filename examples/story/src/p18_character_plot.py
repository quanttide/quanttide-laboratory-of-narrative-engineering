#!/usr/bin/env python3
"""
p18 — 角色驱动的母题推理实验

步骤 1: 从文本提取结构化角色状态
步骤 2: 基于角色状态推理下一个情节走向
步骤 3: 与 story.yaml 的后续场景对比
步骤 4: 反向验证——从后续场景反推前一状态
步骤 5: 边界测试——跨作品/仅角色名推理
"""
import json
import os
import sys
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import FICTION_ROOT, DATA_DIR

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
RESULTS_DIR = DATA_DIR / "p18"

SCENES = [
    {"id": "T1", "name": "咖啡厅重逢", "file": "职场言情/4_成稿/1_1_咖啡厅重逢.md", "next_id": "1_2"},
    {"id": "T2", "name": "便利店谈心", "file": "职场言情/4_成稿/4_1_便利店谈心.md", "next_id": "4_2"},
    {"id": "T3", "name": "海边散步", "file": "职场言情/4_成稿/6_2_海边散步.md", "next_id": "7_2"},
    {"id": "T4", "name": "公园拥抱", "file": "职场言情/4_成稿/7_2_公园拥抱.md", "next_id": "8_2"},
]


def call_llm(prompt: str, system: str = "只输出 JSON。", temperature: float = 0.3) -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        },
        timeout=180,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()


def read_scene(path: str) -> str:
    full = FICTION_ROOT / path
    if not full.exists():
        raise FileNotFoundError(f"文件不存在: {full}")
    text = full.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def step1_extract_characters(text: str, scene_name: str) -> dict:
    prompt = f"""从以下场景《{scene_name}》的文本中提取两个角色的当前状态。

分析要求：
- 只基于文本中的信息，不要引入外部知识
- 关注角色的情感状态、行为倾向、未说出口的话
- 识别核心张力和已突破/未突破的关系边界

输出 JSON：
{{
  "characters": [
    {{
      "name": "...",
      "state": {{"当前情感": "...", "行为倾向": "...", "未说出口的话": "..."}},
      "arc_signal": "角色弧线信号"
    }}
  ],
  "relationship": {{
    "当前阶段": "...",
    "核心张力": "...",
    "已突破的边界": [],
    "未突破的边界": []
  }}
}}

文本：
{text[:4000]}"""
    return json.loads(call_llm(prompt))


def step2_infer_plot(char_state: dict, scene_name: str) -> dict:
    chars = json.dumps(char_state, ensure_ascii=False, indent=2)
    prompt = f"""以下是场景《{scene_name}》结束时两个角色的状态。请推理他们下一场戏最可能的情节走向。

约束：
- 推理必须完全基于角色状态，不允许引入外部知识
- 输出 1 个主推理 + 1 个替代推理（基于不同角色勇气值假设）

输出 JSON：
{{
  "inferred_next": {{
    "core_beat": "一句话核心事件",
    "motivation_breakdown": {{"角色名": "动机解释"}},
    "predicted_scene": "具体场景设想",
    "tension_remaining": "仍未解决的张力"
  }},
  "alternative": {{
    "core_beat": "...",
    "reason": "为什么这个替代路径合理",
    "trigger": "触发替代路径的事件"
  }}
}}

角色状态：
{chars}"""
    return json.loads(call_llm(prompt, temperature=0.7))


def step3_compare_with_story(inference: dict, actual_next: str, actual_next_name: str) -> dict:
    """对比推理结果与实际的下一场景。"""
    prompt = f"""对比以下两个情节描述，判断它们在核心事件上的吻合程度。

推理的下一个情节：
{inference['inferred_next']['core_beat']}

替代推理：
{inference['alternative']['core_beat']}

实际的下一场景（{actual_next_name}）：
{actual_next[:500]}

输出 JSON（严格按此格式）：
{{
  "beat_match": "吻合|部分吻合|不吻合",
  "explanation": "一句话解释判断理由",
  "main_vs_actual": "推理主事件 vs 实际事件的一致性 0-1",
  "alt_vs_actual": "替代推理 vs 实际事件的一致性 0-1"
}}"""
    return json.loads(call_llm(prompt))


def load_story_yaml() -> dict:
    path = Path(__file__).resolve().parents[3] / "assets" / "fiction" / "story.yaml"
    if not path.exists():
        raise FileNotFoundError(f"story.yaml 不存在: {path}")
    raw = path.read_text("utf-8")
    raw = "\n".join(line for line in raw.splitlines() if line.strip() and not line.strip().startswith("# "))
    return yaml.safe_load(raw) or {}


def step4_reverse_validation(next_text: str, prev_state: dict) -> dict:
    pass  # TODO: 从后续场景反推前一状态


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("p18 — 角色驱动的母题推理实验\n")

    story = load_story_yaml()
    plots_by_id = {p["id"]: p for p in story.get("plots", [])}

    comparisons = []

    for scene in SCENES:
        sid = scene["id"]
        cache = RESULTS_DIR / f"char_states_{sid}.json"

        text = read_scene(scene["file"])
        print(f"  {sid} {scene['name']} ({len(text)} chars)")

        if cache.exists():
            char_state = json.loads(cache.read_text("utf-8"))
            print(f"    ← 读取缓存")
        else:
            char_state = step1_extract_characters(text, scene["name"])
            cache.write_text(json.dumps(char_state, ensure_ascii=False, indent=2), "utf-8")
            print(f"    ✓ 角色提取")

        inf_cache = RESULTS_DIR / f"inference_{sid}.json"
        if inf_cache.exists():
            inference = json.loads(inf_cache.read_text("utf-8"))
            print(f"    ← 推理缓存")
        else:
            inference = step2_infer_plot(char_state, scene["name"])
            inf_cache.write_text(json.dumps(inference, ensure_ascii=False, indent=2), "utf-8")
            print(f"    ✓ 情节推理")
            print(f"      主: {inference['inferred_next']['core_beat'][:60]}")

        actual = plots_by_id.get(scene["next_id"])
        if actual:
            comp = step3_compare_with_story(inference, actual.get("description", ""), actual.get("title", ""))
            comp["scene_id"] = sid
            comp["actual_next"] = actual.get("title", "")
            comparisons.append(comp)
            print(f"      vs {actual.get('title', '')}: {comp['beat_match']}")

    comp_file = RESULTS_DIR / "comparison.json"
    comp_file.write_text(json.dumps(comparisons, ensure_ascii=False, indent=2), "utf-8")

    print(f"\n=== 对比汇总 ===")
    for c in comparisons:
        print(f"  {c['scene_id']} → {c.get('actual_next', '?'):<8}: {c['beat_match']}  (主={c.get('main_vs_actual','?')}, 替={c.get('alt_vs_actual','?')})")

    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
