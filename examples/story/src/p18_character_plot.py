#!/usr/bin/env python3
"""
p18 — 角色驱动的母题推理实验

Part A: 从全部场景聚合构建深度角色档案
Part B: 基于角色档案 + 当前场景状态 → 推理下一情节
Part C: 与 story.yaml 对比验证
"""
import json, os, sys
from pathlib import Path

import requests, yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import FICTION_ROOT, DATA_DIR

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
RESULTS_DIR = DATA_DIR / "p18"

ALL_SCENES = [
    "1_1_咖啡厅重逢", "1_2_深夜失眠", "2_1_展会再遇", "2_3_傍晚小龙虾",
    "4_1_便利店谈心", "4_2_夜市约会", "4_3_互相问早", "6_2_海边散步",
    "7_2_公园拥抱", "8_2_酒吧表白", "9_1_家里吃火锅", "10_1_书房陪伴",
    "10_2_客厅看剧", "10_3_阳台看星星",
]

# 推理场景对：(当前场景 → 下一场景)
INFERENCE_PAIRS = [
    ("1_1_咖啡厅重逢", "1_2_深夜失眠"),
    ("4_1_便利店谈心", "4_2_夜市约会"),
    ("6_2_海边散步",   "7_2_公园拥抱"),
    ("7_2_公园拥抱",   "8_2_酒吧表白"),
    ("8_2_酒吧表白",   "9_1_家里吃火锅"),
]


def call_llm(prompt, system="只输出 JSON。", temperature=0.3):
    for attempt in range(3):
        try:
            resp = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ], "temperature": temperature},
                timeout=180,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                lines = lines[1:] if lines[0].startswith("```") else lines
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                raw = "\n".join(lines).strip()
            return raw
        except Exception:
            if attempt == 2:
                raise
    return ""


def read_scene(name):
    path = FICTION_ROOT / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"场景不存在: {path}")
    text = path.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


# ─── Part A: 聚合构建角色深度档案 ───────────────────────────

def partA_build_profile(all_texts: list[tuple[str, str]]) -> dict:
    """从全部场景文本中聚合提取两个角色的深度心理档案。"""
    combined = "\n\n===\n\n".join(
        f"[{name}]\n{text[:2000]}" for name, text in all_texts
    )

    prompt = f"""你是专业叙事分析师。以下是同一部小说全部{len(all_texts)}个场景的文本，
请从中构建两个主角的深度心理档案。只基于文本证据，不引入外部知识。

输出 JSON（严格按此 schema）：

{{
  "林远亭": {{
    "personality": {{
      "core_traits": ["5-8个核心性格特质"],
      "communication_style": "他如何表达/不表达情感",
      "conflict_pattern": "面对压力和亲密时的典型反应"
    }},
    "internal_world": {{
      "core_belief": "关于自己和他人的深层信念",
      "deepest_fear": "最深的恐惧",
      "unspoken_need": "从未说出口的需求",
      "arc_trajectory": "从开场到终场的心理变化路径"
    }},
    "behavior": {{
      "action_tendency": "在关键情境下倾向于怎么做（靠近/退缩/沉默/行动）",
      "threshold_for_change": "什么条件下他会突破惯性",
      "typical_defense": "惯用的心理防御机制（回避/调侃/沉默/理性化等）"
    }},
    "relationship_with_陆知微": {{
      "perceived_distance": "他眼中两人的关系距离",
      "what_he_knows": "他确定她知道的事",
      "what_he_hides": "他刻意隐藏的事",
      "hope_and_fear": "对这段关系最大的期待和恐惧"
    }}
  }},
  "陆知微": {{
    "personality": {{ ... }},
    "internal_world": {{ ... }},
    "behavior": {{ ... }},
    "relationship_with_林远亭": {{ ... }}
  }},
  "relationship_dynamic": {{
    "stage": "当前关系阶段",
    "power_imbalance": "谁在推动/谁在退缩",
    "unspoken_rules": "双方默契但不言明的规则",
    "breakthrough_events": ["关键突破事件列表"],
    "remaining_barriers": ["仍未突破的障碍"]
  }}
}}

全部场景文本：
{combined[:15000]}"""
    return json.loads(call_llm(prompt, temperature=0.3))


# ─── Part B: 基于档案 + 当前状态 → 推理下一情节 ──────────

def partB_infer(profile: dict, current_text: str, current_name: str, next_name: str) -> dict:
    """基于角色深度档案 + 当前场景文本，推理下一情节。"""
    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
    prompt = f"""你既是叙事分析师又是创意写作者。给定一部小说的完整角色心理档案，
以及当前场景全文，请推理下一场《{next_name}》最可能的情节走向。

约束：
1. 推理必须严格符合角色的性格、行为模式和心理弧线
2. 下一场的情节应是当前角色状态的必然结果，而非作者的外部干预
3. 必须引用角色档案中的具体特质来佐证推理

角色深度档案：
{profile_json[:5000]}

当前场景《{current_name}》全文：
{current_text[:4000]}

输出 JSON：
{{
  "inferred_next": {{
    "core_beat": "15字内的核心事件",
    "detailed_scene": "200字以内的具体场景设想，含对话/动作/环境细节",
    "motivation": {{
      "driving_character": "哪个角色的动机在推动这场戏",
      "why_now": "为什么在当前时刻——不能更早也不能更晚",
      "traits_in_play": ["这个情节依赖的角色特质"]
    }},
    "tension_carried": "上一场未解决的张力在本场如何延续/转化/爆发"
  }},
  "alternative_path": {{
    "core_beat": "如果关键角色做出了不同选择的情节走向",
    "trigger": "什么会触发这个替代路径",
    "character_consistency": "这个替代路径是否同样符合角色性格（是/部分/否）"
  }}
}}"""
    return json.loads(call_llm(prompt, temperature=0.7))


# ─── Part C: 与 story.yaml 对比 ──────────────────────────

def load_story_yaml():
    path = FICTION_ROOT / "story.yaml"
    if not path.exists():
        raise FileNotFoundError(f"story.yaml 不存在: {path}")
    raw = path.read_text("utf-8")
    raw = "\n".join(l for l in raw.splitlines() if l.strip() and not l.strip().startswith("# "))
    return yaml.safe_load(raw) or {}


def partC_compare(inference: dict, actual_text: str, actual_title: str) -> dict:
    prompt = f"""对比推理情节与实际场景，从以下维度评估一致性。

推理的核心事件：{inference['inferred_next']['core_beat']}
推理的具体设想：{inference['inferred_next']['detailed_scene'][:300]}

替代路径：{inference['alternative_path']['core_beat']}

实际场景《{actual_title}》：
{actual_text[:800]}

输出 JSON：
{{
  "beat_match": "吻合|部分吻合|不吻合",
  "reasoning": "一句话解释",
  "motivation_accuracy": "推理的角色动机是否与实际一致 0-1",
  "scene_consistency": "设想的场景细节是否匹配 0-1",
  "tension_carryover": "张力延续是否被实际场景验证 0-1",
  "alternative_accuracy": "替代路径与实际的一致性 0-1"
}}"""
    return json.loads(call_llm(prompt))


# ─── Main ────────────────────────────────────────────────

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("p18 — 角色驱动的母题推理实验")
    print("=" * 60)

    # Part A: 构建角色档案
    profile_cache = RESULTS_DIR / "profile.json"
    if profile_cache.exists():
        profile = json.loads(profile_cache.read_text("utf-8"))
        print(f"\n[Part A] 角色档案 ← 缓存")
    else:
        print(f"\n[Part A] 从 {len(ALL_SCENES)} 个场景构建角色档案...")
        all_texts = [(s, read_scene(s)) for s in ALL_SCENES]
        profile = partA_build_profile(all_texts)
        profile_cache.write_text(json.dumps(profile, ensure_ascii=False, indent=2), "utf-8")
        print(f"  完成: {list(profile.keys())}")

    # 打印摘要
    for name in ["林远亭", "陆知微"]:
        p = profile.get(name, {})
        traits = p.get("personality", {}).get("core_traits", [])
        arc = p.get("internal_world", {}).get("arc_trajectory", "")[:60]
        print(f"  {name}: {', '.join(traits[:4])} | {arc}...")

    # Part B + C: 推理并对比
    story = load_story_yaml()
    plots_by_id = {p["id"]: p for p in story.get("plots", [])}

    print(f"\n[Part B+C] {len(INFERENCE_PAIRS)} 组推理 + 对比\n")

    comparisons = []
    for curr_name, next_name in INFERENCE_PAIRS:
        curr_id = "_".join(curr_name.split("_")[:2])
        next_id = "_".join(next_name.split("_")[:2])
        sid = curr_id.replace("_", "")

        text = read_scene(curr_name)
        print(f"  {curr_name} → {next_name} ({len(text)} chars)")

        inf_cache = RESULTS_DIR / f"inference_{sid}.json"
        if inf_cache.exists():
            inference = json.loads(inf_cache.read_text("utf-8"))
            print(f"    ← 推理缓存")
        else:
            inference = partB_infer(profile, text, curr_name, next_name)
            inf_cache.write_text(json.dumps(inference, ensure_ascii=False, indent=2), "utf-8")
            print(f"    ✓ 推理: {inference['inferred_next']['core_beat'][:50]}")

        # 找实际的下一场景
        actual = plots_by_id.get(next_id)
        if actual:
            actual_text = actual.get("description", "")
            comp = partC_compare(inference, actual_text, actual.get("title", ""))
            comp["scene_id"] = sid
            comp["current"] = curr_name
            comp["actual_next"] = actual.get("title", "")
            comparisons.append(comp)
            print(f"      vs 《{actual.get('title', '')}》: {comp['beat_match']}  (动机={comp.get('motivation_accuracy','?')})")
        else:
            print(f"      ⚠ 未找到实际场景: {next_id}")

    # 汇总
    comp_file = RESULTS_DIR / "comparison.json"
    comp_file.write_text(json.dumps(comparisons, ensure_ascii=False, indent=2), "utf-8")

    print(f"\n{'='*60}")
    print(f"对比汇总")
    print(f"{'='*60}")
    for c in comparisons:
        print(f"  {c['current']:12s} → {c.get('actual_next','?'):8s}: "
              f"{c['beat_match']:5s}  "
              f"动机={c.get('motivation_accuracy',0):.1f}  "
              f"场景={c.get('scene_consistency',0):.1f}  "
              f"张力={c.get('tension_carryover',0):.1f}  "
              f"替代={c.get('alternative_accuracy',0):.1f}")

    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
