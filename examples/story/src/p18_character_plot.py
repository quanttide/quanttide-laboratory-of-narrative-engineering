#!/usr/bin/env python3
"""
p18 — 角色驱动的母题推理 (取代 p14/p15)

子命令:
  infer    情节推理（原 p18）
  check    角色一致性检查（原 p14）
  outline  推理 → 格式化写作备忘（原 p15）
  rhythm   叙事节奏分析（全量 13 对相邻场景）

用法:
  uv run python src/p18_character_plot.py infer
  uv run python src/p18_character_plot.py check <场景文件>
  uv run python src/p18_character_plot.py outline <场景ID>
  uv run python src/p18_character_plot.py rhythm
"""
import json, os, sys, statistics, argparse
from pathlib import Path
import requests, yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import FICTION_ROOT, GALLERY_ROOT, DATA_DIR

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
RESULTS_DIR = DATA_DIR / "p18"
URBAN_GALLERY = GALLERY_ROOT / "urban-romance"

ALL_SCENES = [
    "1_1_咖啡厅重逢", "1_2_深夜失眠", "2_1_展会再遇", "2_3_傍晚小龙虾",
    "4_1_便利店谈心", "4_2_夜市约会", "4_3_互相问早", "6_2_海边散步",
    "7_2_公园拥抱", "8_2_酒吧表白", "9_1_家里吃火锅", "10_1_书房陪伴",
    "10_2_客厅看剧", "10_3_阳台看星星",
]
ALL_PAIRS = [(ALL_SCENES[i], ALL_SCENES[i+1]) for i in range(len(ALL_SCENES)-1)]


# ─── 共享工具 ─────────────────────────────────────────

def call_llm(prompt, system="只输出 JSON。", temperature=0.3):
    for attempt in range(3):
        try:
            resp = requests.post(API_URL, headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [
                    {"role": "system", "content": system}, {"role": "user", "content": prompt},
                ], "temperature": temperature}, timeout=180)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                lines = raw.split("\n"); lines = lines[1:] if lines[0].startswith("```") else lines
                if lines and lines[-1].strip() == "```": lines = lines[:-1]
                raw = "\n".join(lines).strip()
            return raw
        except Exception:
            if attempt == 2: raise
    return ""


def read_scene(name):
    path = FICTION_ROOT / f"{name}.md"
    if not path.exists(): return ""
    text = path.read_text("utf-8")
    return "\n".join(" " if l.strip() == "" else l for l in text.split("\n") if not l.startswith("# ")).strip()


def id_from_name(name):
    return "_".join(name.split("_")[:2])


def load_yamls():
    texts = {}
    for name in ("story", "motif", "style"):
        fpath = URBAN_GALLERY / f"{name}.yaml"
        if fpath.exists(): texts[name] = fpath.read_text("utf-8")
    return texts


# ─── 子命令: infer ──────────────────────────────────

def build_profile(scene_texts):
    combined = "\n\n===\n\n".join(f"[{name}]\n{text[:1500]}" for name, text in scene_texts)
    prompt = f"""你是专业叙事分析师。从以下场景文本中构建两个主角的深度心理档案。
输出 JSON schema：
{{"林远亭":{{"personality":{{"core_traits":[],"communication_style":"","conflict_pattern":""}},
"internal_world":{{"core_belief":"","deepest_fear":"","unspoken_need":"","arc_trajectory":""}},
"behavior":{{"action_tendency":"","threshold_for_change":"","typical_defense":""}},
"relationship_with_陆知微":{{"perceived_distance":"","what_he_knows":"","what_he_hides":"","hope_and_fear":""}}}},
"陆知微":{{"personality":{{"core_traits":[],"communication_style":"","conflict_pattern":""}},
"internal_world":{{"core_belief":"","deepest_fear":"","unspoken_need":"","arc_trajectory":""}},
"behavior":{{"action_tendency":"","threshold_for_change":"","typical_defense":""}},
"relationship_with_林远亭":{{"perceived_distance":"","what_she_knows":"","what_she_hides":"","hope_and_fear":""}}}},
"relationship_dynamic":{{"stage":"","power_imbalance":"","unspoken_rules":"","breakthrough_events":[],"remaining_barriers":[]}}}}
文本：\n{combined[:12000]}"""
    return json.loads(call_llm(prompt, temperature=0.3))


def infer_next(profile, curr_text, curr_name, next_name):
    prompt = f"""给定角色深度档案和当前场景，推理下一场最可能的情节。
角色档案：{json.dumps(profile, ensure_ascii=False)[:4000]}
当前场景《{curr_name}》：{curr_text[:3000]}
输出 JSON：{{"inferred_next":{{"core_beat":"","motivation":{{"driving_character":"","why_now":"","traits_in_play":[]}},"tension_carried":""}},"alternative_path":{{"core_beat":"","trigger":"","character_consistency":"是|部分|否"}}}}"""
    return json.loads(call_llm(prompt, temperature=0.7))


def evaluate(main_beat, alt_beat, actual_text, profile):
    prompt = f"""你是一个严格的评估器。评分必须基于角色档案中的具体特质，不是感觉。
角色档案：{json.dumps(profile, ensure_ascii=False)[:3000]}
推理：{main_beat}
替代：{alt_beat}
实际：{actual_text[:600]}
按 0-1 评分：motivation_accuracy（动机与角色是否一致）、tension_carryover（张力是否自然延续）、scene_plausibility（场景是否在行为范围内）、alternative_accuracy（替代路径的合理性）。每个评分必须附理由。
输出 JSON：{{"motivation_accuracy":0,"motivation_reason":"","tension_carryover":0,"tension_reason":"","scene_plausibility":0,"plausibility_reason":"","alternative_accuracy":0,"alternative_reason":"","summary":""}}"""
    return json.loads(call_llm(prompt, temperature=0.1))


def cmd_infer(args):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    scene_texts = {s: read_scene(s) for s in ALL_SCENES}
    story_yaml = URBAN_GALLERY / "story.yaml"
    story_plots = {}
    if story_yaml.exists():
        raw = story_yaml.read_text("utf-8")
        raw = "\n".join(l for l in raw.splitlines() if l.strip() and not l.strip().startswith("# "))
        story_plots = {p["id"]: p for p in (yaml.safe_load(raw) or {}).get("plots", [])}

    print(f"推理 {len(ALL_PAIRS)} 组相邻对...")
    results = []
    for idx, (curr, nxt) in enumerate(ALL_PAIRS):
        cid = id_from_name(curr)
        window = [(ALL_SCENES[i], scene_texts[ALL_SCENES[i]]) for i in range(ALL_SCENES.index(curr)+1)]
        prof = json.loads((RESULTS_DIR / f"profile_{cid}.json").read_text("utf-8")) if (RESULTS_DIR / f"profile_{cid}.json").exists() else build_profile(window)
        if not (RESULTS_DIR / f"profile_{cid}.json").exists():
            (RESULTS_DIR / f"profile_{cid}.json").write_text(json.dumps(prof, ensure_ascii=False, indent=2), "utf-8")
        inf = json.loads((RESULTS_DIR / f"inference_{cid}.json").read_text("utf-8")) if (RESULTS_DIR / f"inference_{cid}.json").exists() else infer_next(prof, scene_texts[curr], curr, nxt)
        if not (RESULTS_DIR / f"inference_{cid}.json").exists():
            (RESULTS_DIR / f"inference_{cid}.json").write_text(json.dumps(inf, ensure_ascii=False, indent=2), "utf-8")
        actual = story_plots.get(id_from_name(nxt), {})
        ev = evaluate(inf["inferred_next"]["core_beat"], inf["alternative_path"]["core_beat"], actual.get("description",""), prof) if actual else {}
        ev["curr"], ev["next"] = curr, nxt
        results.append(ev)
        m, t, a = ev.get("motivation_accuracy",0), ev.get("tension_carryover",0), ev.get("alternative_accuracy",0)
        print(f"  {idx+1:2d}/{len(ALL_PAIRS)} {curr[:16]}→{nxt[:16]}  动机={m:.1f} 张力={t:.1f} 替代={a:.1f}")
    print(f"\n平均动机={statistics.mean([r.get('motivation_accuracy',0) for r in results]):.2f}")
    print(f"结果: {RESULTS_DIR}")


# ─── 子命令: check（替代 p14） ──────────────────────

def annotate_chain(text, yamls, profile):
    y = "\n".join(f"--- {k} ---\n{v[:1500]}" for k,v in yamls.items())
    p = json.dumps(profile, ensure_ascii=False)[:2000] if profile else ""
    prompt = f"""你是专业叙事分析师。对以下场景做行为链标注 + 角色一致性检查。

角色档案（供判断动机一致性）：
{p}

YAML 参考：
{y}

输出 JSON，每个序列节点标注：
{{"seq":1,"actor":"","action":"","outward_motivation":"","inward_motivation":"","tension":"外向/内隐是否冲突","chain_status":"完整|有意断裂|无意断裂","ooc_flag":true/false,"ooc_reason":"如果 OOC 解释为什么"}}

场景文本：
{text[:4000]}"""
    return json.loads(call_llm(prompt))


def diagnose(chain, yamls):
    y = "\n".join(f"--- {k} ---\n{v[:1500]}" for k,v in yamls.items())
    prompt = f"""基于行为链标注识别薄弱点。类型：causal_gap|motivation_blind|emotional_jump|info_density|ooc。
输出 JSON：[{{"location":"","issue_type":"","severity":1-3,"ooc":true/false,"reasoning":"","before":"","after":""}}]
行为链：{json.dumps(chain[:20], ensure_ascii=False)}
YAML：{y}"""
    return json.loads(call_llm(prompt))


def suggest_fixes(diagnosis, yamls):
    y = "\n".join(f"--- {k} ---\n{v[:1500]}" for k,v in yamls.items())
    prompt = f"""对每个薄弱点生成 3 类修改建议。输出 JSON：
[{{"location":"","issue_type":"","fix_A":{{"category":"因果补链","description":"","expected_effect":""}},"fix_B":{{"category":"动机刻深","description":"","expected_effect":""}},"fix_C":{{"category":"边界校准","direction":"调远|调近","description":"","expected_effect":""}}}}]
薄弱点：{json.dumps(diagnosis, ensure_ascii=False)}
YAML：{y}"""
    return json.loads(call_llm(prompt, temperature=0.7))


def cmd_check(args):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    name = args.scene
    text = read_scene(name if not name.endswith(".md") else name.replace(".md",""))
    if not text:
        # Try as file path
        path = Path(name)
        if path.exists():
            text = path.read_text("utf-8")
            name = path.stem
        else:
            sys.exit(f"场景不存在: {name}")
    print(f"检查《{name}》({len(text)} chars)")

    yamls = load_yamls()
    print(f"  YAML 已加载: {list(yamls.keys())}")

    profile = None
    prof_file = RESULTS_DIR / "profile.json"
    if prof_file.exists():
        profile = json.loads(prof_file.read_text("utf-8"))
        print(f"  角色档案 ← 缓存")
    else:
        reply = input("  未找到角色档案，从全部场景构建？[Y/n] ")
        if reply.lower() in ("", "y", "yes"):
            texts = [(s, read_scene(s)) for s in ALL_SCENES]
            profile = build_profile(texts)
            prof_file.write_text(json.dumps(profile, ensure_ascii=False, indent=2), "utf-8")
            print(f"  角色档案已构建")

    cache_file = RESULTS_DIR / f"check_{id_from_name(name)}.json"
    if cache_file.exists() and not args.force:
        report = json.loads(cache_file.read_text("utf-8"))
        print(f"  结果 ← 缓存")
    else:
        chain = annotate_chain(text, yamls, profile)
        diag = diagnose(chain, yamls)
        fixes = suggest_fixes(diag, yamls)
        report = {"scene": name, "chain": chain, "diagnosis": diag, "suggestions": fixes}
        cache_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")

    n_issues = len(report.get("diagnosis", []))
    n_ooc = sum(1 for d in report.get("diagnosis", []) if d.get("ooc"))
    print(f"\n  薄弱点: {n_issues} ({n_ooc} 个 OOC)")
    for d in report.get("diagnosis", [])[:5]:
        ooc_tag = " [OOC]" if d.get("ooc") else ""
        print(f"    - [{d.get('issue_type','')}][严重={d.get('severity',0)}]{ooc_tag} {d.get('location','')[:50]}")
        print(f"      {d.get('reasoning','')[:60]}")
    print(f"\n结果: {cache_file}")


# ─── 子命令: outline（替代 p15） ─────────────────────

def cmd_outline(args):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    yamls = load_yamls()

    # 如果指定了场景，只生成那个
    scenes_to_gen = []
    for sc in ALL_SCENES:
        sid = id_from_name(sc)
        if args.scene_id and sid != args.scene_id: continue
        scenes_to_gen.append((sid, sc))

    if not scenes_to_gen:
        sys.exit(f"场景 {args.scene_id} 不存在")

    for sid, sc_name in scenes_to_gen:
        out_path = RESULTS_DIR / f"outline_{sid.replace('_','')}.md"
        if out_path.exists() and not args.force:
            print(f"  {sc_name} → 已存在，跳过")
            continue

        text = read_scene(sc_name)
        if not text:
            print(f"  {sc_name} ⚠ 场景文件不存在")
            continue

        # Try to get infer output for this scene
        inf_file = RESULTS_DIR / f"inference_{sid}.json"
        infer_json = json.loads(inf_file.read_text("utf-8")) if inf_file.exists() else None

        profile = None
        prof_file = RESULTS_DIR / "profile.json"
        if prof_file.exists():
            profile = json.loads(prof_file.read_text("utf-8"))

        print(f"  生成 {sc_name} 提纲...", end=" ", flush=True)

        story_data = ""
        try:
            raw = yamls.get("story", "")
            if raw:
                story_all = yaml.safe_load(raw) or {}
                for p in story_all.get("plots", []):
                    if p["id"] == sid:
                        desc = p.get("description", "")
                        tensions = "\n".join(p.get("tensions", []))
                        story_data = f"{desc}\n\n张力：{tensions}"
                        break
        except: pass

        inf_section = ""
        if infer_json:
            inf_section = f"""## 推理的情节走向

核心事件：{infer_json.get('inferred_next',{}).get('core_beat','')}
动机：{json.dumps(infer_json.get('inferred_next',{}).get('motivation',{}), ensure_ascii=False)}
张力延续：{infer_json.get('inferred_next',{}).get('tension_carried','')}"""

        md = call_llm(
            f"""基于以下数据，生成一份写作备忘 md 格式提纲。

# {sid} {sc_name[len(sid)+1:] if len(sc_name) > len(sid) else sc_name} — 写作备忘

模板包含：行为序列、结构难点、边界提醒（从 style.yaml boundaries 聚合，语言为执行式）、薄弱点与建议。

{inf_section}

## 输入数据

### 角色档案
{json.dumps(profile, ensure_ascii=False)[:2000] if profile else "(无)"}

### story.yaml
{story_data[:1500]}

### style.yaml boundaries
{yamls.get('style','')[:2000]}

### motif.yaml
{yamls.get('motif','')[:1500]}

### 场景全文
{text[:3000]}

生成完整 md。语言简洁、执行式、面向写作者。""",
            "叙事编辑。生成写作备忘 md，只输出 md 正文。", 0.3)

        out_path.write_text(md, "utf-8")
        print(f"✓ {out_path.name}")

    print(f"\n结果: {RESULTS_DIR}")


# ─── 子命令: rhythm ────────────────────────────────

def cmd_rhythm(args):
    cmd_infer(args)  # Reuse infer logic, prints rhythm stats


# ─── 主入口 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="p18 — 角色驱动的母题推理")
    parser.add_argument("command", choices=["infer", "check", "outline", "rhythm"],
        help="子命令: infer=情节推理, check=一致性检查, outline=写作备忘, rhythm=叙事节奏")
    parser.add_argument("scene", nargs="?", help="场景名或文件路径 (check 子命令)")
    parser.add_argument("--scene-id", help="场景 ID (outline 子命令)")
    parser.add_argument("--force", "-f", action="store_true", help="强制重新生成")
    args = parser.parse_args()

    if args.command == "infer":
        cmd_infer(args)
    elif args.command == "check":
        if not args.scene:
            print("用法: uv run python src/p18_character_plot.py check <场景名>")
            print("示例: uv run python src/p18_character_plot.py check 1_1_咖啡厅重逢")
            return
        cmd_check(args)
    elif args.command == "outline":
        cmd_outline(args)
    elif args.command == "rhythm":
        cmd_rhythm(args)


if __name__ == "__main__":
    main()
