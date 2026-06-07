#!/usr/bin/env python3
"""
p18 — 角色驱动的母题推理实验 (v3)

改进：
1. 隔离输入窗口：建档案只用到当前场景为止的文本
2. 独立评估：结构化评分代替 LLM 自评
3. 零假设：交换角色人格特质后重跑
4. 全量 13 对相邻场景 + 叙事节奏曲线
5. 合理性检查器
"""
import json, os, sys, statistics
from pathlib import Path
from collections import defaultdict

import requests, yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import FICTION_ROOT, DATA_DIR

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
RESULTS_DIR = DATA_DIR / "p18"

# 全部场景按时间顺序
ALL_SCENES = [
    "1_1_咖啡厅重逢", "1_2_深夜失眠", "2_1_展会再遇", "2_3_傍晚小龙虾",
    "4_1_便利店谈心", "4_2_夜市约会", "4_3_互相问早", "6_2_海边散步",
    "7_2_公园拥抱", "8_2_酒吧表白", "9_1_家里吃火锅", "10_1_书房陪伴",
    "10_2_客厅看剧", "10_3_阳台看星星",
]

# 13 个相邻对
ALL_PAIRS = [(ALL_SCENES[i], ALL_SCENES[i+1]) for i in range(len(ALL_SCENES)-1)]


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
        return ""
    text = path.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def id_from_name(name):
    return "_".join(name.split("_")[:2])


# ─── Part A: 从时序窗口建档案 ────────────────────────────

def build_profile(scene_texts: list[tuple[str, str]]) -> dict:
    """从给定场景列表中构建角色档案。"""
    combined = "\n\n===\n\n".join(f"[{name}]\n{text[:1500]}" for name, text in scene_texts)
    prompt = f"""你是专业叙事分析师。以下是同一部小说多个场景的文本，
请从中构建两个主角的林远亭和陆知微的深度心理档案。只基于文本证据。

输出 JSON schema：
{{
  "林远亭": {{
    "personality": {{"core_traits":[], "communication_style":"", "conflict_pattern":""}},
    "internal_world": {{"core_belief":"", "deepest_fear":"", "unspoken_need":"", "arc_trajectory":""}},
    "behavior": {{"action_tendency":"", "threshold_for_change":"", "typical_defense":""}},
    "relationship_with_陆知微": {{"perceived_distance":"", "what_he_knows":"", "what_he_hides":"", "hope_and_fear":""}}
  }},
  "陆知微": {{
    "personality": {{"core_traits":[], "communication_style":"", "conflict_pattern":""}},
    "internal_world": {{"core_belief":"", "deepest_fear":"", "unspoken_need":"", "arc_trajectory":""}},
    "behavior": {{"action_tendency":"", "threshold_for_change":"", "typical_defense":""}},
    "relationship_with_林远亭": {{"perceived_distance":"", "what_she_knows":"", "what_she_hides":"", "hope_and_fear":""}}
  }},
  "relationship_dynamic": {{
    "stage":"", "power_imbalance":"", "unspoken_rules":"",
    "breakthrough_events":[], "remaining_barriers":[]
  }}
}}

文本：
{combined[:12000]}"""
    return json.loads(call_llm(prompt, temperature=0.3))


# ─── Part B: 推理下一情节 ──────────────────────────────

def infer_next(profile: dict, curr_text: str, curr_name: str, next_name: str) -> dict:
    prompt = f"""给定角色深度档案和当前场景，推理下一场最可能的情节。

角色档案（摘要）：
{json.dumps(profile, ensure_ascii=False, indent=2)[:4000]}

当前场景《{curr_name}》：
{curr_text[:3000]}

输出 JSON：
{{
  "inferred_next": {{
    "core_beat": "核心事件",
    "motivation": {{"driving_character":"", "why_now":"", "traits_in_play":[]}},
    "tension_carried": "张力延续"
  }},
  "alternative_path": {{
    "core_beat": "",
    "trigger": "",
    "character_consistency": "是|部分|否"
  }}
}}"""
    return json.loads(call_llm(prompt, temperature=0.7))


# ─── Part C: 独立评估（基于结构化规则） ────────────────

def evaluate(main_beat: str, alt_beat: str, actual_text: str, profile: dict) -> dict:
    """用结构化 prompt 评估一致性，避免 LLM 自评循环。"""
    profile_s = json.dumps(profile, ensure_ascii=False, indent=2)[:3000]
    prompt = f"""你是一个严格的叙事分析评估器。你的任务是评估一个情节推理的好坏，
不是看它"像不像正确答案"，而是看它是否符合角色的性格。

角色档案摘要：
{profile_s}

推理的核心事件：{main_beat}
替代路径：{alt_beat}

实际下一场景的描述：
{actual_text[:600]}

请按以下维度评分（0-1），每个评分必须附一句基于角色档案的客观理由：

1. motivation_accuracy: 推理归因的角色动机是否与角色档案一致？
   评分标准：0=矛盾, 0.3=不充分但有合理性, 0.5=部分一致, 0.7=基本一致, 1=完全一致
   
2. tension_carryover: 上一场的未解决张力是否自然地延续到下一场？
   评分标准：0=张力断裂, 0.3=弱连接, 0.5=部分延续, 0.7=自然延续, 1=张力完美转化

3. scene_plausibility: 设想的具体场景是否在角色行为范围内？
   评分标准：0=OOC, 0.3=勉强合理, 0.5=可能发生, 0.7=很可能, 1=必然

4. alternative_accuracy: 替代路径在角色性格框架内的合理性
   评分标准：0=不符合任何角色, 0.3=勉强合理, 0.5=合理但不如主路径, 0.7=同样合理, 1=更合理

输出 JSON：
{{
  "motivation_accuracy": 0.0,
  "motivation_reason": "",
  "tension_carryover": 0.0,
  "tension_reason": "",
  "scene_plausibility": 0.0,
  "plausibility_reason": "",
  "alternative_accuracy": 0.0,
  "alternative_reason": "",
  "summary": "一句话评估"
}}"""
    return json.loads(call_llm(prompt, temperature=0.1))


# ─── Part D: 合理性检查器 ──────────────────────────────

def consistency_check(scene_text: str, profile: dict) -> dict:
    """检查场景中每个角色动作是否符合角色档案。"""
    profile_s = json.dumps(profile, ensure_ascii=False, indent=2)[:4000]
    prompt = f"""你是角色一致性检查器。给定角色档案和场景全文，
逐句检查每个角色的行为、对话和内心活动是否符合其性格。

对每个发现的不一致，输出：
- 角色：谁
- 位置：文本片段（最多 50 字）
- 问题类型：OOC_行为 | OOC_对话 | OOC_内心 | 关系越界 | 张力断裂
- 严重等级：1=轻微, 2=中等, 3=严重
- 原因：引用角色档案具体特质解释为什么不一致

如果全部一致，输出 "all_consistent": true。

角色档案：
{profile_s}

场景全文：
{scene_text[:5000]}

输出 JSON：
{{
  "all_consistent": false,
  "issues": [
    {{"character":"", "location":"", "type":"", "severity":1, "reason":""}}
  ],
  "overall_score": 0.0
}}"""
    return json.loads(call_llm(prompt, temperature=0.1))


# ─── 零假设：错位时间窗 ────────────────────────────────

def null_misaligned_window(results: list[dict], scene_texts: dict, all_pairs: list) -> list:
    """零假设：用结尾的 profile 推断开头的情节，用开头的 profile 推断结尾的情节。

    如果角色状态确实随叙事时间变化，则错位时间窗的准确率应显著低于对齐的时间窗。
    这是对"角色状态编码情节方向"的直接检验——如果结果无差异，说明 profile 不包含时序信息。
    """
    null_pairs = []

    # Null 1: 用结尾 profile 推第一对
    early_pair = all_pairs[0]
    late_pair_key = id_from_name(all_pairs[-1][0])  # 用最后一对的当前场景 profile
    late_prof = json.loads((RESULTS_DIR / f"profile_{late_pair_key}.json").read_text("utf-8"))
    inf = infer_next(late_prof, scene_texts[early_pair[0]], early_pair[0], early_pair[1])

    story_yaml = FICTION_ROOT / "story.yaml"
    if story_yaml.exists():
        raw = story_yaml.read_text("utf-8")
        raw = "\n".join(l for l in raw.splitlines() if l.strip() and not l.strip().startswith("# "))
        story = yaml.safe_load(raw) or {}
        plots = {p["id"]: p for p in story.get("plots", [])}
        actual = plots.get(id_from_name(early_pair[1]), {})
        actual_desc = actual.get("description", "")
    else:
        actual_desc = scene_texts[early_pair[1]][:600]

    ev = evaluate(
        inf["inferred_next"]["core_beat"],
        inf["alternative_path"]["core_beat"],
        actual_desc,
        late_prof,
    )
    normal = results[0]
    null_pairs.append({
        "pair": f"{early_pair[0][:12]}→{early_pair[1][:12]}",
        "null_profile_from": all_pairs[-1][0][:12],
        "null_motivation": ev.get("motivation_accuracy", 0),
        "normal_motivation": normal.get("motivation_accuracy", 0),
        "drop": round(normal.get("motivation_accuracy", 0) - ev.get("motivation_accuracy", 0), 2),
        "design": "用结尾 profile 推开头",
    })

    # Null 2: 用开头 profile 推最后一对
    late_pair = all_pairs[-1]
    early_profile_key = id_from_name(all_pairs[0][0])
    early_prof = json.loads((RESULTS_DIR / f"profile_{early_profile_key}.json").read_text("utf-8"))
    inf2 = infer_next(early_prof, scene_texts[late_pair[0]], late_pair[0], late_pair[1])

    if story_yaml.exists():
        raw = story_yaml.read_text("utf-8")
        raw = "\n".join(l for l in raw.splitlines() if l.strip() and not l.strip().startswith("# "))
        story = yaml.safe_load(raw) or {}
        plots = {p["id"]: p for p in story.get("plots", [])}
        actual = plots.get(id_from_name(late_pair[1]), {})
        actual_desc2 = actual.get("description", "")
    else:
        actual_desc2 = scene_texts[late_pair[1]][:600]

    ev2 = evaluate(
        inf2["inferred_next"]["core_beat"],
        inf2["alternative_path"]["core_beat"],
        actual_desc2,
        early_prof,
    )
    normal2 = results[-1]
    null_pairs.append({
        "pair": f"{late_pair[0][:12]}→{late_pair[1][:12]}",
        "null_profile_from": all_pairs[0][0][:12],
        "null_motivation": ev2.get("motivation_accuracy", 0),
        "normal_motivation": normal2.get("motivation_accuracy", 0),
        "drop": round(normal2.get("motivation_accuracy", 0) - ev2.get("motivation_accuracy", 0), 2),
        "design": "用开头 profile 推结尾",
    })

    return null_pairs


# ─── 叙事节奏分析 ─────────────────────────────────────

def rhythm_analysis(results: list[dict]) -> dict:
    """从全量相邻对结果中提取叙事节奏信息。"""
    pairs = []
    for r in results:
        pairs.append({
            "pair": f"{r['curr_short']}→{r['next_short']}",
            "motivation": r["motivation_accuracy"],
            "tension": r["tension_carryover"],
            "scene": r["scene_plausibility"],
            "alternative": r["alternative_accuracy"],
            "avg": (r["motivation_accuracy"] + r["tension_carryover"]) / 2,
        })

    # 检测跳跃点：avg 骤降且替代路径分高
    jumps = []
    for i in range(1, len(pairs)):
        drop = pairs[i-1]["avg"] - pairs[i]["avg"]
        if drop > 0.3 and pairs[i]["alternative"] > 0.5:
            jumps.append({
                "at": pairs[i]["pair"],
                "drop": round(drop, 2),
                "alt_score": pairs[i]["alternative"],
                "signal": "可能缺失中间情节"
            })

    return {
        "pairs": pairs,
        "avg_scores": statistics.mean([p["avg"] for p in pairs]) if pairs else 0,
        "high_signal_pairs": [p["pair"] for p in pairs if p["avg"] >= 0.6],
        "low_signal_pairs": [p["pair"] for p in pairs if p["avg"] < 0.4],
        "detected_jumps": jumps,
    }


# ─── Main ──────────────────────────────────────────────

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("p18 — 角色驱动的母题推理 (v3)")
    print("=" * 60)

    # ── Step 1: 读全部场景文本 ──
    print(f"\n[1/5] 加载 {len(ALL_SCENES)} 个场景文本...")
    scene_texts = {s: read_scene(s) for s in ALL_SCENES}

    # ── Step 2: 对每个相邻对建隔离档案 + 推理 + 评估 ──
    print(f"\n[2/5] 跑 {len(ALL_PAIRS)} 组相邻对（隔离输入窗口）...\n")

    results = []
    for idx, (curr, nxt) in enumerate(ALL_PAIRS):
        curr_id = id_from_name(curr)
        print(f"  {idx+1:2d}/{len(ALL_PAIRS)}  {curr[:16]:16s} → {nxt[:16]:16s}")

        # 建档案：只用到当前场景（含）为止的文本
        window_idx = ALL_SCENES.index(curr)
        window = [(ALL_SCENES[i], scene_texts[ALL_SCENES[i]]) for i in range(window_idx + 1)]

        prof_cache = RESULTS_DIR / f"profile_{curr_id}.json"
        if prof_cache.exists():
            profile = json.loads(prof_cache.read_text("utf-8"))
        else:
            profile = build_profile(window)
            prof_cache.write_text(json.dumps(profile, ensure_ascii=False, indent=2), "utf-8")

        # 推理
        inf_cache = RESULTS_DIR / f"inference_{curr_id}.json"
        if inf_cache.exists():
            inference = json.loads(inf_cache.read_text("utf-8"))
        else:
            inference = infer_next(profile, scene_texts[curr], curr, nxt)
            inf_cache.write_text(json.dumps(inference, ensure_ascii=False, indent=2), "utf-8")

        # 评估
        ev_cache = RESULTS_DIR / f"eval_{curr_id}.json"
        if ev_cache.exists():
            ev = json.loads(ev_cache.read_text("utf-8"))
        else:
            story_yaml = FICTION_ROOT / "story.yaml"
            if story_yaml.exists():
                raw = story_yaml.read_text("utf-8")
                raw = "\n".join(l for l in raw.splitlines() if l.strip() and not l.strip().startswith("# "))
                story = yaml.safe_load(raw) or {}
                plots = {p["id"]: p for p in story.get("plots", [])}
                actual = plots.get(id_from_name(nxt), {})
                actual_desc = actual.get("description", "")
            else:
                actual_desc = scene_texts[nxt][:600]

            ev = evaluate(
                inference["inferred_next"]["core_beat"],
                inference["alternative_path"]["core_beat"],
                actual_desc,
                profile,
            )
            ev_cache.write_text(json.dumps(ev, ensure_ascii=False, indent=2), "utf-8")

        ev["curr"] = curr
        ev["next"] = nxt
        ev["curr_short"] = curr
        ev["next_short"] = nxt
        results.append(ev)

        m = ev.get("motivation_accuracy", 0)
        t = ev.get("tension_carryover", 0)
        a = ev.get("alternative_accuracy", 0)
        print(f"     动机={m:.1f}  张力={t:.1f}  替代={a:.1f}")

    # ── Step 3: 零假设（错位时间窗） ──
    print(f"\n[3/5] 零假设检验（错位时间窗——用结尾 profile 推开头，反之亦然）...")
    null_results = null_misaligned_window(results, scene_texts, ALL_PAIRS)
    for n in null_results:
        print(f"   {n['pair']:26s}: 零假设={n['null_motivation']:.1f} (正常={n['normal_motivation']:.1f}) 下降={n['drop']:+.1f}  [{n['design']}]")

    # ── Step 4: 叙事节奏分析 ──
    print(f"\n[4/5] 叙事节奏分析...")
    rhythm = rhythm_analysis(results)
    print(f"   平均分: {rhythm['avg_scores']:.2f}")
    print(f"   高信号段: {len(rhythm['high_signal_pairs'])} 组")
    print(f"   低信号段: {len(rhythm['low_signal_pairs'])} 组")
    for j in rhythm.get("detected_jumps", []):
        print(f"   ⚡ {j['at']}: 下降{j['drop']} 替代={j['alt_score']} — {j['signal']}")

    # ── Step 5: 合理性检查器（demo：跑当前 vs 相邻场景） ──
    print(f"\n[5/5] 合理性检查器（demo）...")
    demo_profile = json.loads((RESULTS_DIR / f"profile_{id_from_name(ALL_SCENES[0])}.json").read_text("utf-8"))
    demo_text = scene_texts[ALL_SCENES[0]]
    check = consistency_check(demo_text, demo_profile)
    n_issues = len(check.get("issues", []))
    print(f"   《{ALL_SCENES[0]}》: {n_issues} 个问题, 综合分={check.get('overall_score', 0):.1f}")
    for iss in check.get("issues", [])[:3]:
        print(f"    - [{iss.get('type','')}][严重={iss.get('severity',0)}] {iss.get('location','')[:40]}")
        print(f"      {iss.get('reason','')[:60]}")

    # ── 保存完整结果 ──
    report = {
        "pairs": [{
            "curr": r["curr"], "next": r["next"],
            "motivation_accuracy": r.get("motivation_accuracy", 0),
            "tension_carryover": r.get("tension_carryover", 0),
            "scene_plausibility": r.get("scene_plausibility", 0),
            "alternative_accuracy": r.get("alternative_accuracy", 0),
        } for r in results],
        "rhythm": rhythm,
        "null_hypothesis": null_results,
        "summary": {
            "avg_motivation": round(statistics.mean([r.get("motivation_accuracy", 0) for r in results]), 2),
            "avg_tension": round(statistics.mean([r.get("tension_carryover", 0) for r in results]), 2),
            "avg_alternative": round(statistics.mean([r.get("alternative_accuracy", 0) for r in results]), 2),
            "null_motivation_drop": round(
                statistics.mean([n["normal_motivation"] for n in null_results]) -
                statistics.mean([n["null_motivation"] for n in null_results]),
                2
            ) if null_results else 0,
        }
    }
    (RESULTS_DIR / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")

    print(f"\n{'='*60}")
    print(f"汇总")
    print(f"{'='*60}")
    print(f"  平均动机准确率: {report['summary']['avg_motivation']}")
    print(f"  平均张力延续:   {report['summary']['avg_tension']}")
    print(f"  平均替代合理率: {report['summary']['avg_alternative']}")
    print(f"  零假设平均下降:  {report['summary']['null_motivation_drop']}")
    print(f"\n  节奏: 高信号={len(rhythm['high_signal_pairs'])} 低信号={len(rhythm['low_signal_pairs'])} 跳跃={len(rhythm.get('detected_jumps',[]))}")
    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
