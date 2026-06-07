#!/usr/bin/env python3
"""
p10 — 母题驱动的风格改进实验

风格诊断维度弱点 → 母题根因分析 → 三组改法对比。
"""
import json
import os
import sys
from pathlib import Path

import requests
import yaml

import random

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[5]
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

ARTICLES = [
    {"id": "T1", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md", "type": "初稿"},
    {"id": "T2", "name": "酒吧表白",   "path": "职场言情/3_初稿/8_2_酒吧表白.md", "type": "初稿"},
    {"id": "T3", "name": "深夜失眠",   "path": "职场言情/4_成稿/1_2_深夜失眠.md", "type": "成稿"},
    {"id": "T4", "name": "赏雪谈心",   "path": "职场言情/3_初稿/赏雪谈心.md", "type": "盲测初稿"},
]

STYLE_DIM_NAMES = [
    "叙事母题与核心矛盾", "叙事视角", "时间结构", "语言风格", "情感表达",
    "细节美学", "人物塑造", "对话模式", "叙事节奏", "时代质感", "美学关键词",
]

HUMAN_STYLE_MOTIF_MAP = {
    "情感表达": ["手势", "十年"],
    "时间结构": ["十年"],
    "细节美学": ["手势"],
    "叙事节奏": ["孤独"],
    "时代质感": ["歌声"],
}


def call_llm_text(prompt: str, system: str = "你是一个创作顾问。", temperature: float = 0.3) -> str:
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
    return resp.json()["choices"][0]["message"]["content"]


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


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text("utf-8")) or {}


def build_style_prompt(style: dict, samples_dir: Path) -> str:
    parts = []
    dims = style.get("dimensions", [])
    parts.append(f"风格框架「{style.get('title','')}」——{style.get('description','')}")
    parts.append(f"共 {len(dims)} 个评价维度：\n")
    for d in dims:
        parts.append(f"【{d['title']}】(confidence={d.get('confidence','?')})")
        parts.append(f"  {d.get('description','')}")
        if d.get("clues"):
            parts.append(f"  clues: {'; '.join(d['clues'][:2])}")
        if d.get("tensions"):
            parts.append(f"  tensions: {'; '.join(d['tensions'][:2])}")
        parts.append("")

    if samples_dir.exists():
        sample_files = sorted(samples_dir.glob("sample*.md"))[:3]
        parts.append(f"\n参考场景（{len(sample_files)} 篇）：")
        for sf in sample_files:
            parts.append(f"\n--- {sf.stem} ---\n{sf.read_text('utf-8')[:800]}\n")
    return "\n".join(parts)


def style_review(text: str, article_name: str, style_prompt: str) -> dict:
    sample = text[:2500]
    prompt = f"""{style_prompt}

请用以上审美框架评审下面名为《{article_name}》的场景。
严格评分标准：
- 8-10分：该场景在此维度上执行出色，明显超越系列平均水平
- 5-7分：场景符合维度定义，但只是"执行了"而非"执行好了"
- 1-4分：场景在此维度上明显不足
请对每个维度评分（1-10），必须附原文引用作为证据，指出好在哪里或差在哪里。
只输出 JSON：{{"dimension_scores": [{{"dimension":"维度名","score":8,"evidence":["原文"],"note":"理由"}}]}}
场景文本：{sample}"""
    raw = call_llm(prompt, temperature=0.0)
    return json.loads(clean_json(raw))


def extract_motifs(text: str, article_name: str) -> dict:
    sample = text[:3000]
    prompt = f"""分析《{article_name}》提取叙事母题（3-6个）。
母题定义：叙事中反复出现的主题元素（意象、关系模式、行为习惯、叙事惯例）。
每个母题须有原文线索。
输出JSON：{{"motifs":[{{"title":"母题名","description":"描述","weight":5,"evidence":["线索"]}}]}}
文章：{sample}"""
    raw = call_llm(prompt)
    return json.loads(clean_json(raw))


def diagnose_style_motif_links(style_scores: list[dict], extracted_motifs: list[dict], target_motifs: list[dict], article_name: str) -> dict:
    """Two-step diagnosis: free inference first, then match against known motifs."""
    weak_dims = [d for d in style_scores if d.get("score", 10) <= 7]
    if not weak_dims:
        return {"links": []}

    ext_titles = [m["title"] for m in extracted_motifs]
    ext_descs = [m.get("description", "") for m in extracted_motifs]
    target_titles = [m["title"] for m in target_motifs]

    # Step A: free inference
    wd_text = "\n".join(f"- {d['dimension']} (score={d['score']}): {d.get('note','')}" for d in weak_dims)
    free_prompt = f"""场景《{article_name}》风格评审中以下维度偏低：
{wd_text}

请分析每个弱维度的根因可能是什么（自由文本，不要参考任何预定义母题列表）。
对每个弱维度，描述"该维度偏弱最可能是因为缺少什么叙事元素"。
如果某个弱维度与叙事元素缺失无关（如纯技巧问题），说明原因。

输出JSON：{{"free_analysis":[{{"weak_dimension":"情感表达","root_cause_hypothesis":"场景缺乏非言语的情感动作——角色说了很多但身体没有表达","confidence":"high|medium|low"}}]}}"""
    raw = call_llm(free_prompt, "你是一个叙事诊断专家。只输出 JSON。", temperature=0.2)
    free_analysis = json.loads(clean_json(raw))

    # Step B: match hypotheses against known motif pool
    target_motif_pool = "\n".join(f"- {m['title']}: {m.get('description','')}" for m in target_motifs)
    hypotheses = "\n".join(f"- {d['weak_dimension']}: {d['root_cause_hypothesis']}" for d in free_analysis.get("free_analysis", []))
    match_prompt = f"""以下是叙事元素缺失假设：
{hypotheses}

已知该系列的母题库：
{target_motif_pool}

对每个假设，判断它最接近哪个已知母题（如有）。
如果假设与任何已知母题都不匹配，related_missing_motif 留空。
约束：每个母题在一篇文章中最多关联 2 个弱维度——避免过度泛化。
输出JSON：{{"links":[{{"weak_dimension":"情感表达","related_missing_motif":"手势","confidence":"high","hypothesis":"..."}}]}}"""

    raw = call_llm(match_prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.2)
    return json.loads(clean_json(raw))


def generate_combined_fix(article_name: str, text_sample: str, weak_dim: str, related_motif: str, motif_desc: str, dim_desc: str) -> str:
    prompt = f"""场景《{article_name}》在「{weak_dim}」维度偏低。
该维度描述：{dim_desc}
根因：缺少母题「{related_motif}」——{motif_desc}

请给出一条具体的改写建议（80-150字）：明确指出在哪个段落、加入什么动作/细节/对话来引入该母题，从而提升该风格维度。不要泛泛而谈。

场景文本：{text_sample[:2000]}"""
    raw = call_llm_text(prompt, "你是一个创作顾问。只输出建议文本，不要JSON包装。", temperature=0.3)
    return raw.strip()


def generate_style_only_fix(article_name: str, text_sample: str, weak_dim: str, dim_desc: str) -> str:
    prompt = f"""场景《{article_name}》在「{weak_dim}」维度偏低。
该维度描述：{dim_desc}
请给出一条具体的改写建议（80-150字）来加强这个维度。不要泛泛而谈。
约束：不要提及任何母题名称（如"手势""十年""雨""歌声"等）——只从风格角度诊断弱点并提出改写方案。
场景文本：{text_sample[:2000]}"""
    raw = call_llm_text(prompt, "你是一个创作顾问。只输出建议文本。", temperature=0.3)
    return raw.strip()


def evaluate_pairwise(fix_a: str, fix_b: str, weak_dim: str, related_motif: str) -> dict:
    """Pairwise comparison: which fix is better? Blind to group identity."""
    label_a, text_a = fix_a
    label_b, text_b = fix_b
    # shuffle order to avoid position bias
    if random.random() < 0.5:
        label_a, label_b, text_a, text_b = label_b, label_a, text_a, text_b

    prompt = f"""比较下面两条针对「{weak_dim}」维度的改写建议，从 5 个维度各选赢家（或平局）。

建议 A：{text_a[:400]}
建议 B：{text_b[:400]}

五个维度：
1. specific: 谁给出了更具体的、可执行的文本操作？
2. root_cause: 谁更对准了风格问题的真实原因？
3. motif_fit: 谁更会增强母题「{related_motif}」？
4. natural: 谁的修改更自然、不刻意？
5. style_cover: 谁的修改更能提升「{weak_dim}」维度？

对每个维度输出 winner: "A" / "B" / "tie"。
输出JSON：{{"winners":{{"specific":"A","root_cause":"B","motif_fit":"tie","natural":"A","style_cover":"B"}}}}"""
    raw = call_llm(prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.1)
    return json.loads(clean_json(raw))


def main():
    print("=" * 60)
    print("p10 — 母题驱动的风格改进实验")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    urban_style = load_yaml(GALLERY_ROOT / "urban-romance" / "style.yaml")
    urban_motif = load_yaml(GALLERY_ROOT / "urban-romance" / "motif.yaml")
    target_motifs = urban_motif.get("motifs", [])
    samples_dir = GALLERY_ROOT / "urban-romance" / "samples"

    style_prompt = build_style_prompt(urban_style, samples_dir)
    dims = urban_style.get("dimensions", [])
    dim_descs = {d["title"]: d.get("description", "") for d in dims}
    motif_descs = {m["title"]: m.get("description", "") for m in target_motifs}

    all_diagnoses = {}
    all_fixes = {}
    all_evaluations = {}

    for art in ARTICLES:
        aid = art["id"]
        print(f"\n{'='*40}")
        print(f"{aid} {art['name']} ({art['type']})")

        text = read_article_text(art["path"])

        # Step 1a: Style review
        review_cache = RESULTS_DIR / f"style_review_{aid}.json"
        if review_cache.exists():
            style_result = json.loads(review_cache.read_text("utf-8"))
            print("  ← 风格评审读取缓存")
        else:
            print("  风格评审...", end=" ", flush=True)
            style_result = style_review(text, art["name"], style_prompt)
            review_cache.write_text(json.dumps(style_result, ensure_ascii=False, indent=2), "utf-8")
            scores = style_result.get("dimension_scores", [])
            avg = sum(d["score"] for d in scores) / len(scores) if scores else 0
            print(f"✓ avg={avg:.1f}")

        # Step 1b: Motif extraction
        motif_cache = RESULTS_DIR / f"motif_extract_{aid}.json"
        if motif_cache.exists():
            motif_result = json.loads(motif_cache.read_text("utf-8"))
            print("  ← 母题提取读取缓存")
        else:
            print("  母题提取...", end=" ", flush=True)
            motif_result = extract_motifs(text, art["name"])
            motif_cache.write_text(json.dumps(motif_result, ensure_ascii=False, indent=2), "utf-8")
            print(f"✓ {len(motif_result.get('motifs',[]))} 个母题")

        # Step 1c: Diagnosis
        diag_cache = RESULTS_DIR / f"diagnosis_{aid}.json"
        if diag_cache.exists():
            diagnosis = json.loads(diag_cache.read_text("utf-8"))
            print("  ← 诊断读取缓存")
        else:
            print("  风格-母题关联诊断...", end=" ", flush=True)
            diag_input_scores = [d for d in style_result.get("dimension_scores", []) if d["score"] <= 7]
            diagnosis = diagnose_style_motif_links(
                diag_input_scores,
                motif_result.get("motifs", []),
                target_motifs,
                art["name"],
            )
            diag_cache.write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2), "utf-8")
            n = len(diagnosis.get("links", []))
            print(f"✓ {n} 条关联")

        all_diagnoses[aid] = diagnosis

        # Step 2: Generate fixes for weak dimensions
        weak_dims = [d for d in style_result.get("dimension_scores", []) if d.get("score", 10) <= 7]
        print(f"  弱维度: {', '.join(d['dimension'] for d in weak_dims) if weak_dims else '无'}")

        art_fixes = {}
        art_evals = {}

        for wd in weak_dims[:3]:  # limit to top 3 weak dims per article
            dim_name = wd["dimension"]
            dim_desc = dim_descs.get(dim_name, "")

            # Find related motif from diagnosis
            links = diagnosis.get("links", [])
            related = next((l for l in links if l.get("weak_dimension") == dim_name), None)
            related_motif = related.get("related_missing_motif") if related else None
            if not related_motif:
                related_motif = "手势"  # default fallback
            motif_desc = motif_descs.get(related_motif, "")

            print(f"    [{dim_name} score={wd['score']}] → related_motif={related_motif}")

            fix_key = f"{aid}_{dim_name}"

            # Combined
            comb_cache = RESULTS_DIR / f"fix_combined_{aid}_{dim_name}.txt"
            if comb_cache.exists():
                comb_fix = comb_cache.read_text("utf-8")
            else:
                print(f"      组合改法...", end=" ", flush=True)
                comb_fix = generate_combined_fix(art["name"], text, dim_name, related_motif, motif_desc, dim_desc)
                comb_cache.write_text(comb_fix, "utf-8")
                print(f"✓ ({len(comb_fix)}字)")

            # Style only
            style_cache = RESULTS_DIR / f"fix_style_{aid}_{dim_name}.txt"
            if style_cache.exists():
                style_fix = style_cache.read_text("utf-8")
            else:
                print(f"      风格单层...", end=" ", flush=True)
                style_fix = generate_style_only_fix(art["name"], text, dim_name, dim_desc)
                style_cache.write_text(style_fix, "utf-8")
                print(f"✓ ({len(style_fix)}字)")

            # Motif only (reuse p08 pattern)
            motif_cache_fix = RESULTS_DIR / f"fix_motif_{aid}_{dim_name}.txt"
            if motif_cache_fix.exists():
                motif_fix = motif_cache_fix.read_text("utf-8")
            else:
                print(f"      母题单层...", end=" ", flush=True)
                prompt = f"""场景《{art['name']}》缺少母题「{related_motif}」——{motif_desc}。
给出一条具体的引入该母题的改写建议（80-150字）：
场景文本：{text[:2000]}"""
                raw = call_llm_text(prompt, "你是一个创作顾问。只输出建议文本。", temperature=0.3)
                motif_fix = raw.strip()
                motif_cache_fix.write_text(motif_fix, "utf-8")
                print(f"✓ ({len(motif_fix)}字)")

            # Evaluate (pairwise, blind, shuffled)
            eval_cache = RESULTS_DIR / f"eval_{aid}_{dim_name}.json"
            if eval_cache.exists():
                pairwise_data = json.loads(eval_cache.read_text("utf-8"))
            else:
                print(f"      评估(blind pairwise)...", end=" ", flush=True)
                # Three pairwise comparisons
                pairs = [
                    (("A", comb_fix), ("B", style_fix), "combined", "style_only", "A", "B"),
                    (("A", comb_fix), ("B", motif_fix), "combined", "motif_only", "A", "B"),
                    (("A", style_fix), ("B", motif_fix), "style_only", "motif_only", "A", "B"),
                ]
                pairwise = {}
                scores = {"combined": {}, "style_only": {}, "motif_only": {}}
                for fix_a, fix_b, ga, gb, la, lb in pairs:
                    result = evaluate_pairwise(fix_a, fix_b, dim_name, related_motif)
                    result["mapping"] = [{"group": ga, "label": la}, {"group": gb, "label": lb}]
                    pair_key = f"{ga}_vs_{gb}"
                    pairwise[pair_key] = result
                    winners = result.get("winners", {})
                    for dim in ["specific", "root_cause", "motif_fit", "natural", "style_cover"]:
                        if dim not in scores[ga]:
                            scores[ga][dim] = 0
                            scores[gb][dim] = 0
                        w = winners.get(dim, "tie")
                        if w == la:
                            scores[ga][dim] = scores[ga].get(dim, 0) + 1
                        elif w == lb:
                            scores[gb][dim] = scores[gb].get(dim, 0) + 1
                        else:
                            scores[ga][dim] = scores[ga].get(dim, 0) + 0.5
                            scores[gb][dim] = scores[gb].get(dim, 0) + 0.5

                pairwise_data = {"pairwise": pairwise, "aggregated_scores": scores}
                eval_cache.write_text(json.dumps(pairwise_data, ensure_ascii=False, indent=2), "utf-8")
                wins_summary = {g: sum(v for k, v in scores[g].items()) for g in scores}
                print(f"✓ wins: comb={wins_summary['combined']:.0f} style={wins_summary['style_only']:.0f} motif={wins_summary['motif_only']:.0f}")

            art_fixes[dim_name] = {"combined": comb_fix, "style_only": style_fix, "motif_only": motif_fix}
            art_evals[dim_name] = pairwise_data

        all_fixes[aid] = art_fixes
        all_evaluations[aid] = art_evals

    # Step 4: Style-motif mapping matrix
    print(f"\n{'='*40}")
    print("风格-母题映射矩阵")
    print(f"{'='*40}")

    llm_inferred = {}
    for aid, diag in all_diagnoses.items():
        for link in diag.get("links", []):
            wd = link["weak_dimension"]
            rm = link.get("related_missing_motif", "")
            if wd not in llm_inferred:
                llm_inferred[wd] = set()
            if rm:
                llm_inferred[wd].add(rm)

    for dim_name in sorted(set(list(HUMAN_STYLE_MOTIF_MAP.keys()) + list(llm_inferred.keys()))):
        human = set(HUMAN_STYLE_MOTIF_MAP.get(dim_name, []))
        llm = llm_inferred.get(dim_name, set())
        shared = human & llm
        llm_new = llm - human
        human_missed = human - llm
        jaccard = len(shared) / len(human | llm) if (human | llm) else 0
        print(f"  {dim_name}:")
        print(f"    human: {human}")
        print(f"    LLM:   {llm}")
        print(f"    shared: {shared} | LLM新发现: {llm_new} | 人类未匹配: {human_missed} | Jaccard={jaccard:.2f}")

    # Report
    print(f"\n{'='*60}")
    print("p10 分析报告：三组改法对比")
    print(f"{'='*60}")

    group_totals = {"combined": {"specific": 0, "root_cause": 0, "motif_fit": 0, "natural": 0, "style_cover": 0, "n_dims": 0},
                    "style_only": {"specific": 0, "root_cause": 0, "motif_fit": 0, "natural": 0, "style_cover": 0, "n_dims": 0},
                    "motif_only": {"specific": 0, "root_cause": 0, "motif_fit": 0, "natural": 0, "style_cover": 0, "n_dims": 0}}

    for aid, evals_by_dim in all_evaluations.items():
        print(f"\n## {aid}")
        for dim_name, eval_data in evals_by_dim.items():
            scores = eval_data.get("aggregated_scores", {})
            pairwise = eval_data.get("pairwise", {})
            print(f"  [{dim_name}]")
            for group in ["combined", "style_only", "motif_only"]:
                if group in scores and scores[group]:
                    gs = scores[group]
                    total = sum(gs.values())
                    print(f"    {group:<12}: wins={total:.1f} ({gs})")
                    for k in gs:
                        group_totals[group][k] += gs[k]
                    group_totals[group]["n_dims"] += 1
            # Show pairwise results
            for pk, pr in pairwise.items():
                w = pr.get("winners", {})
                print(f"    {pk}: {w}")

    print(f"\n## 总体对比（pairwise win counts, max=3 per dimension）")
    for group in ["combined", "style_only", "motif_only"]:
        gt = group_totals[group]
        if gt["n_dims"] == 0:
            continue
        print(f"  {group}: ", end="")
        parts = []
        for k in ["specific", "root_cause", "motif_fit", "natural", "style_cover"]:
            parts.append(f"{k}={gt[k]:.1f}")
        print(", ".join(parts))

    # Save full report
    report = {
        "diagnoses": all_diagnoses,
        "fixes": all_fixes,
        "evaluations": all_evaluations,
        "style_motif_mapping": {
            "human": {k: list(v) for k, v in HUMAN_STYLE_MOTIF_MAP.items()},
            "llm_inferred": {k: list(v) for k, v in llm_inferred.items()},
        },
        "group_totals": {g: {k: v for k, v in gt.items()} for g, gt in group_totals.items()},
    }
    (RESULTS_DIR / "full_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    (RESULTS_DIR / "style_motif_mapping.json").write_text(json.dumps({
        "human_annotated": {k: list(v) for k, v in HUMAN_STYLE_MOTIF_MAP.items()},
        "llm_inferred": {k: list(v) for k, v in llm_inferred.items()},
        "llm_discoveries": {k: list(v) for k, v in llm_inferred.items()
                           if k not in HUMAN_STYLE_MOTIF_MAP or v - set(HUMAN_STYLE_MOTIF_MAP.get(k, []))},
    }, ensure_ascii=False, indent=2), "utf-8")
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
