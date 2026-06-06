#!/usr/bin/env python3
"""
p08 — 母题缝隙分析与多向改进实验

检测初稿中的母题缝隙，从 6 个方向生成差异化改进建议。
"""
import json
import os
import sys
from pathlib import Path

import requests
import yaml

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[4]
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction"
P05_RESULTS = REPO_ROOT / "examples" / "default" / "examples" / "p05-motif-extraction" / "results"
RESULTS_DIR = Path(__file__).parent / "results"

ARTICLES = [
    {"id": "D1", "series": "urban", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md"},
    {"id": "D2", "series": "urban", "name": "酒吧表白",   "path": "职场言情/3_初稿/8_2_酒吧表白.md"},
    {"id": "D3", "series": "campus", "name": "第六章",     "path": "校园言情/3_初稿/6_第六章.md"},
    {"id": "D4", "series": "campus", "name": "第十章 KTV", "path": "校园言情/4_成稿/10_第十章.md"},
]

DIRECTIONS = [
    {"id": "amplify",  "name": "增强", "desc": "强化已存在但偏弱的母题",               "trigger": "母题已被检测到但 weight 偏低"},
    {"id": "introduce","name": "引入", "desc": "添加一个完全缺失的母题",               "trigger": "母题完全缺失"},
    {"id": "borrow",   "name": "借用", "desc": "从跨作品母题镜像或同系列其他场景借用变体", "trigger": "素材库有可用变体"},
    {"id": "transform","name": "转化", "desc": "将现有场景元素改造成母题载体",          "trigger": "场景中已存在可承载母题的元素"},
    {"id": "restrain", "name": "克制", "desc": "建议不做某事，保持克制",               "trigger": "weight ≤ 6 或已有 2+ 高 weight 母题"},
    {"id": "reverse",  "name": "反向", "desc": "有意违抗母题以制造张力",               "trigger": "无限制，需标风险"},
]

CROSS_WORK_MIRRORS = {
    "手势": ["校园: 纸巾擦眼泪→拆开鬼使神差擦上去", "校园: 披外套→扣扣子→拉进怀里"],
    "雨": ["校园: 无对应（校园无雨母题）"],
    "十年": ["校园: 无对应（校园无时间跨度母题）"],
    "孤独": ["校园: 无对应"],
    "歌声": ["校园: 无对应"],
    "论坛": ["都市: 无对应"],
    "协作书写": ["都市: 无对应"],
    "旁观者": ["都市: 封闭二人空间（反向: 缺席即在场）"],
    "随身携带的温柔": ["都市: 超市新买的毛巾→不知不觉伸出去擦头发"],
}


def call_llm(prompt: str, system: str = "你是一个专业的叙事学分析助手。只输出 JSON。", temperature: float = 0.3, retries: int = 3) -> str:
    for attempt in range(retries):
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
        try:
            cleaned = clean_json(raw)
            json.loads(cleaned)
            return raw
        except json.JSONDecodeError:
            if attempt < retries - 1:
                print(f"(retry {attempt+1})", end=" ", flush=True)
                continue
    raise RuntimeError(f"JSON parse failed after {retries} retries")


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()


def read_article_text(path: str) -> str:
    full_path = FICTION_ROOT / path
    text = full_path.read_text("utf-8")
    lines = text.split("\n")
    body_lines = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body_lines).strip()


def load_motif_yaml(path: Path) -> dict:
    raw = path.read_text("utf-8")
    raw = "\n".join(line for line in raw.splitlines() if line.strip() and not line.startswith("# ") and line.strip() != "---")
    return yaml.safe_load(raw)


def extract_motifs(text: str, article_name: str) -> dict:
    sample = text[:3000]
    prompt = f"""分析下面名为《{article_name}》的文章，从中提取叙事母题（motif）。
母题定义：在叙事中反复出现的主题元素，包括具体意象、关系模式、行为习惯、叙事惯例。
要求：提取 3-6 个母题，每个母题须有来自原文的具体线索。
输出格式（JSON）：{{"motifs": [{{"title":"母题名","description":"一句话描述","weight":5,"evidence":["线索1"]}}]}}
文章：{sample}"""
    raw = call_llm(prompt)
    return json.loads(clean_json(raw))


def compute_gap_report(extracted: dict, target_motifs: list[dict]) -> dict:
    extracted_titles = {m["title"] for m in extracted.get("motifs", [])}
    target_map = {m["title"]: m for m in target_motifs}

    covered = []
    missing = []
    weak = []
    for tm in target_motifs:
        t = tm["title"]
        if t in extracted_titles:
            ext = next(m for m in extracted["motifs"] if m["title"] == t)
            if ext.get("weight", 0) < tm.get("weight", 5) * 0.5:
                weak.append({"title": t, "extracted_weight": ext["weight"], "target_weight": tm["weight"]})
            else:
                covered.append({"title": t, "extracted_weight": ext["weight"], "target_weight": tm["weight"]})
        else:
            # 尝试 subtitle 匹配
            found = False
            for et in extracted.get("motifs", []):
                if t in et["title"] or et["title"] in t:
                    if et.get("weight", 0) < tm["weight"] * 0.5:
                        weak.append({"title": t, "extracted_weight": et["weight"], "target_weight": tm["weight"], "matched_via": et["title"]})
                    else:
                        covered.append({"title": t, "extracted_weight": et["weight"], "target_weight": tm["weight"], "matched_via": et["title"]})
                    found = True
                    break
            if not found:
                missing.append({"title": t, "target_weight": tm["weight"], "description": tm.get("description", "")})

    return {"covered": covered, "missing": missing, "weak": weak}


def gap_attribution(article_name: str, text_sample: str, missing_motif: dict) -> dict:
    prompt = f"""场景《{article_name}》缺少母题「{missing_motif['title']}」。
该母题定义：{missing_motif['description']}
可能原因：场景类型不支持 / 作者用了替代母题 / 单纯遗漏。可标注多个。
输出 JSON：{{"gap_types": ["scene_incompatible"], "alternative_motif": "替代母题名（如有）", "reasoning": "一句话原因"}}
场景片段：{text_sample[:2000]}"""
    raw = call_llm(prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.2)
    return json.loads(clean_json(raw))


def generate_suggestions(article_name: str, text_sample: str, gap: dict, gap_types: list[str], target_motif: dict, series: str) -> list[dict]:
    mirror_text = ""
    mirrors = CROSS_WORK_MIRRORS.get(target_motif["title"], [])
    if mirrors:
        mirror_text = "跨作品/跨场景变体参考：\n" + "\n".join(f"  - {m}" for m in mirrors)

    prompt = f"""
你是《{article_name}》的创作顾问。这篇文章缺少母题「{target_motif['title']}」（定义：{target_motif.get('description','')}）。
已识别的原因：{', '.join(gap_types)}

{mirror_text}

请从以下 6 个方向各生成一条改进建议（每条 80-150 字）：
1. 增强 - 强化已存在但偏弱的母题
2. 引入 - 添加一个完全缺失的母题
3. 借用 - 从上述变体参考借用（若无则从同系列其他场景）
4. 转化 - 将现有场景元素改造成母题载体
5. 克制 - 建议不做修改（仅当 weight≤6 或已有 2+ 高 weight 母题时有效）
6. 反向 - 有意违抗母题制造张力（附加风险等级 1-3）

输出 JSON：
{{
  "suggestions": [
    {{"direction": "amplify", "text": "建议内容...", "paragraph_ref": "第X段"}},
    ...
  ]
}}
其中"反向"方向额外含 "reverse_risk": 1-3

场景文本：{text_sample[:2500]}"""

    try:
        raw = call_llm(prompt, temperature=0.7)
        return json.loads(clean_json(raw)).get("suggestions", [])
    except Exception as e:
        print(f"✗ {e}")
        return []


def evaluate_suggestions(suggestions: list[dict], gap_title: str, article_name: str) -> list[dict]:
    items = "\n".join(f"[{s['direction']}] {s.get('text','')[:120]}" for s in suggestions)
    prompt = f"""评估以下针对文章《{article_name}》缺母题「{gap_title}」的改进建议。
每条建议从 4 维度评分（1-5）：
- feasibility: 是否可在不改动结构的情况下执行？
- motif_fit: 按建议修改后目标母题是否确实会增强？
- naturalness: 修改后的场景是否自然不刻意？
- actionable: 是否有明确执行步骤无须二次解读？

输出 JSON：{{"evaluations": [{{"direction": "...", "scores": {{"feasibility":4, "motif_fit":3, "naturalness":4, "actionable":5}} }}] }}

建议列表：{items}"""
    try:
        raw = call_llm(prompt, temperature=0.1)
        return json.loads(clean_json(raw)).get("evaluations", [])
    except Exception as e:
        print(f"✗ {e}")
        return []


def main():
    print("=" * 60)
    print("p08 — 母题缝隙分析与多向改进实验")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    urban_target = load_motif_yaml(GALLERY_ROOT / "urban-romance" / "motif.yaml")
    campus_target = load_motif_yaml(GALLERY_ROOT / "campus-romance" / "motif.yaml")

    all_gaps = {}
    all_suggestions = {}
    all_evaluations = {}

    for art in ARTICLES:
        series = art["series"]
        target = urban_target if series == "urban" else campus_target
        target_motifs = target.get("motifs", [])
        target_titles = [m["title"] for m in target_motifs]

        print(f"\n{'='*40}")
        print(f"{art['id']} {art['name']} ({series})")
        print(f"  目标母题: {', '.join(target_titles)}")

        text = read_article_text(art["path"])

        # Step 1: Extract + Gap Report
        cache = RESULTS_DIR / f"motif_report_{art['id']}.json"
        if cache.exists():
            gap_report = json.loads(cache.read_text("utf-8"))
            print("  ← 母题报告读取缓存")
        else:
            print("  提取母题...", end=" ", flush=True)
            extracted = extract_motifs(text, art["name"])
            gap_report = compute_gap_report(extracted, target_motifs)
            gap_report["extracted_motifs"] = extracted["motifs"]
            cache.write_text(json.dumps(gap_report, ensure_ascii=False, indent=2), "utf-8")
            print(f"✓ 覆盖{len(gap_report['covered'])} / 缺{len(gap_report['missing'])} / 弱{len(gap_report['weak'])}")

        all_gaps[art["id"]] = gap_report

        gaps_to_fix = gap_report["missing"] + gap_report["weak"]
        print(f"  缝隙数: {len(gaps_to_fix)}")

        art_suggestions = {}
        art_evaluations = {}

        for gap in gaps_to_fix:
            gt = gap["title"]
            print(f"    缺/弱: {gt} (weight={gap.get('target_weight','?')})")

            # Step 2: Attribution
            attr_cache = RESULTS_DIR / f"gap_attr_{art['id']}_{gt}.json"
            if attr_cache.exists():
                attr = json.loads(attr_cache.read_text("utf-8"))
                print("      ← 归因读取缓存")
            else:
                print("      归因...", end=" ", flush=True)
                attr = gap_attribution(art["name"], text, gap)
                attr_cache.write_text(json.dumps(attr, ensure_ascii=False, indent=2), "utf-8")
                print(f"✓ {attr.get('gap_types',[])}")

            # Step 3: Suggestions
            sugg_cache = RESULTS_DIR / f"suggestions_{art['id']}_{gt}.json"
            if sugg_cache.exists():
                suggestions = json.loads(sugg_cache.read_text("utf-8"))
                print("      ← 建议读取缓存")
            else:
                print("      生成 6 方向建议...", end=" ", flush=True)
                gap_types = attr.get("gap_types", [])
                target_motif = next((m for m in target_motifs if m["title"] == gt), {})
                suggestions = generate_suggestions(art["name"], text, gap, gap_types, target_motif, series)
                sugg_cache.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), "utf-8")
                names = [s["direction"] for s in suggestions]
                risks = [s.get("reverse_risk","") for s in suggestions if s["direction"] == "reverse"]
                print(f"✓ {len(suggestions)} 条 ({', '.join(names[:4])}...) {'risk:'+str(risks) if risks else ''}")

            art_suggestions[gt] = suggestions

            # Step 4: Evaluation
            eval_cache = RESULTS_DIR / f"evaluation_{art['id']}_{gt}.json"
            if eval_cache.exists():
                evals = json.loads(eval_cache.read_text("utf-8"))
                print("      ← 评估读取缓存")
            else:
                print("      评估中...", end=" ", flush=True)
                evals = evaluate_suggestions(suggestions, gt, art["name"])
                eval_cache.write_text(json.dumps(evals, ensure_ascii=False, indent=2), "utf-8")
                avg_feas = sum(e["scores"]["feasibility"] for e in evals) / len(evals) if evals else 0
                print(f"✓ avg feasibility={avg_feas:.1f}")

            art_evaluations[gt] = evals

        all_suggestions[art["id"]] = art_suggestions
        all_evaluations[art["id"]] = art_evaluations

    # Report
    print("\n" + "=" * 60)
    print("p08 分析报告")
    print("=" * 60)

    for art in ARTICLES:
        gap_report = all_gaps[art["id"]]
        print(f"\n## {art['id']} {art['name']}")
        print(f"  覆盖: {len(gap_report['covered'])} / 缺失: {len(gap_report['missing'])} / 弱化: {len(gap_report['weak'])}")
        for m in gap_report["missing"]:
            print(f"    缺 {m['title']} (target weight={m['target_weight']})")
        for w in gap_report["weak"]:
            print(f"    弱 {w['title']} (extracted={w['extracted_weight']} vs target={w['target_weight']})")

        evals = all_evaluations.get(art["id"], {})
        for gt, elist in evals.items():
            if not elist:
                continue
            print(f"\n  [{gt}] 各方向平均分:")
            for d in DIRECTIONS:
                de = [e for e in elist if e["direction"] == d["id"]]
                if de:
                    s = de[0]["scores"]
                    avg = sum(s.values()) / len(s)
                    print(f"    {d['name']:<4}: feas={s['feasibility']} fit={s['motif_fit']} nat={s['naturalness']} act={s['actionable']} avg={avg:.1f}")

    report_file = RESULTS_DIR / "full_report.json"
    report_file.write_text(json.dumps({
        "gaps": all_gaps,
        "suggestions": all_suggestions,
        "evaluations": all_evaluations,
    }, ensure_ascii=False, indent=2), "utf-8")

    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
