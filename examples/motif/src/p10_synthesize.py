#!/usr/bin/env python3
"""
p10 — 母题驱动的风格改进实验

风格诊断维度弱点 → 母题根因分析 → 三组改法对比。
"""
import json
import random
from pathlib import Path

from src.config import FICTION_ROOT, GALLERY_ROOT, DATA_DIR
from src.infra import call_llm, call_llm_text, clean_json, cache_or_compute, cache_or_compute_text, read_article_text, load_yaml
from src.domain import FixGroup, Motif, StyleReview, StyleDimension


def _to_motifs(items) -> list[Motif]:
    if not items:
        return []
    if isinstance(items[0], Motif):
        return items
    return [Motif(title=m["title"], description=m.get("description", ""), weight=m.get("weight", 5)) for m in items]
from src.prompts import load_prompt

RESULTS_DIR = DATA_DIR / "p10"
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
ARTICLES = [
    {"id": "T1", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md", "type": "初稿"},
    {"id": "T2", "name": "酒吧表白",   "path": "职场言情/3_初稿/8_2_酒吧表白.md", "type": "初稿"},
    {"id": "T3", "name": "深夜失眠",   "path": "职场言情/4_成稿/1_2_深夜失眠.md", "type": "成稿"},
    {"id": "T4", "name": "赏雪谈心",   "path": "职场言情/3_初稿/赏雪谈心.md", "type": "盲测初稿"},
]


def build_style_prompt(style: dict, samples_dir: Path) -> str:
    parts = [f"风格框架「{style.get('title','')}」——{style.get('description','')}"]
    dims = style.get("dimensions", [])
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


def style_review(text: str, article_name: str, style_prompt: str) -> StyleReview:
    sample = text[:2500]
    prompt = load_prompt("p10/style_review", style_prompt=style_prompt, article_name=article_name, sample=sample)
    raw = call_llm(prompt, temperature=0.0)
    items = json.loads(clean_json(raw)).get("dimension_scores", [])
    dims = [StyleDimension(title=d["dimension"], score=d.get("score", 5),
                           evidence=d.get("evidence", []), note=d.get("note", ""))
            for d in items]
    return StyleReview(dimension_scores=dims)


def extract_motifs(text: str, article_name: str) -> list[Motif]:
    sample = text[:3000]
    prompt = load_prompt("p10/extract_motifs_style", article_name=article_name, sample=sample)
    raw = call_llm(prompt)
    items = json.loads(clean_json(raw)).get("motifs", [])
    return [Motif(title=m["title"], description=m.get("description", ""), weight=m.get("weight", 5)) for m in items]


def diagnose_style_motif_links(style_scores: list[dict], extracted_motifs: list[dict], target_motifs: list[dict], article_name: str) -> dict:
    weak_dims = [d for d in style_scores if d.get("score", 10) <= 7]
    if not weak_dims:
        return {"links": []}

    wd_text = "\n".join(f"- {d['dimension']} (score={d['score']}): {d.get('note','')}" for d in weak_dims)
    free_prompt = load_prompt("p10/free_diagnosis", article_name=article_name, wd_text=wd_text)
    raw = call_llm(free_prompt, "你是一个叙事诊断专家。只输出 JSON。", temperature=0.2)
    free_analysis = json.loads(clean_json(raw))

    pool = "\n".join(f"- {m['title']}: {m.get('description','')}" for m in target_motifs)
    hypotheses = "\n".join(f"- {d['weak_dimension']}: {d['root_cause_hypothesis']}" for d in free_analysis.get("free_analysis", []))
    match_prompt = load_prompt("p10/diagnosis_match", hypotheses=hypotheses, target_motif_pool=pool)
    raw = call_llm(match_prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.2)
    return json.loads(clean_json(raw))


def generate_combined_fix(article_name: str, text_sample: str, weak_dim: str, related_motif: str, motif_desc: str, dim_desc: str) -> str:
    prompt = load_prompt("p10/fix_combined",
        article_name=article_name, weak_dim=weak_dim, dim_desc=dim_desc,
        related_motif=related_motif, motif_desc=motif_desc, sample=text_sample[:2000])
    return call_llm_text(prompt, "你是一个创作顾问。只输出建议文本，不要JSON包装。", temperature=0.3).strip()


def generate_style_only_fix(article_name: str, text_sample: str, weak_dim: str, dim_desc: str) -> str:
    prompt = load_prompt("p10/fix_style_only", article_name=article_name, weak_dim=weak_dim, dim_desc=dim_desc, sample=text_sample[:2000])
    return call_llm_text(prompt, "你是一个创作顾问。只输出建议文本。", temperature=0.3).strip()


def evaluate_pairwise(fix_a: tuple, fix_b: tuple, weak_dim: str, related_motif: str) -> dict:
    label_a, text_a = fix_a
    label_b, text_b = fix_b
    if random.random() < 0.5:
        label_a, label_b, text_a, text_b = label_b, label_a, text_a, text_b
    prompt = load_prompt("p10/evaluate_pairwise",
        weak_dim=weak_dim, text_a=text_a[:400], text_b=text_b[:400], related_motif=related_motif)
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

    all_diagnoses, all_fixes, all_evaluations = {}, {}, {}

    for art in ARTICLES:
        aid = art["id"]
        print(f"\n{'='*40}\n{aid} {art['name']} ({art['type']})")
        text = read_article_text(art["path"])

        style_raw = cache_or_compute(RESULTS_DIR / f"style_review_{aid}.json",
            lambda: [vars(d) for d in style_review(text, art["name"], style_prompt).dimension_scores],
            f"风格评审 {aid}")
        dimension_scores = _to_dims(style_raw)

        motif_result = cache_or_compute(RESULTS_DIR / f"motif_extract_{aid}.json",
            lambda: [vars(m) for m in extract_motifs(text, art["name"])], f"母题提取 {aid}")
        motif_list = _to_motifs(motif_result)

        diagnoses = cache_or_compute(RESULTS_DIR / f"diagnosis_{aid}.json",
            lambda: diagnose_style_motif_links(
                [{"dimension": d.title, "score": d.score, "note": d.note} for d in dimension_scores if d.score <= 7],
                motif_list, target_motifs, art["name"]),
            f"诊断 {aid}")
        all_diagnoses[aid] = diagnoses

        weak_dims = [d for d in dimension_scores if d.score <= 7]
        art_fixes, art_evals = {}, {}

        for wd in weak_dims[:3]:
            dim_name = wd.title
            dim_desc = dim_descs.get(dim_name, "")
            links = diagnoses.get("links", [])
            related = next((l for l in links if l.get("weak_dimension") == dim_name), None)
            related_motif = related.get("related_missing_motif") if related else "手势"
            motif_desc = motif_descs.get(related_motif, "")

            comb_fix = cache_or_compute_text(RESULTS_DIR / f"fix_combined_{aid}_{dim_name}.txt",
                lambda: generate_combined_fix(art["name"], text, dim_name, related_motif, motif_desc, dim_desc),
                verbose=False)

            style_fix = cache_or_compute_text(RESULTS_DIR / f"fix_style_{aid}_{dim_name}.txt",
                lambda: generate_style_only_fix(art["name"], text, dim_name, dim_desc), verbose=False)

            motif_fix_prompt = load_prompt("p10/fix_motif_only",
                article_name=art["name"], related_motif=related_motif, motif_desc=motif_desc, sample=text[:2000])
            motif_fix = cache_or_compute_text(RESULTS_DIR / f"fix_motif_{aid}_{dim_name}.txt",
                lambda: call_llm_text(motif_fix_prompt, "你是一个创作顾问。只输出建议文本。", temperature=0.3).strip(),
                verbose=False)

            pairwise_data = cache_or_compute(RESULTS_DIR / f"eval_{aid}_{dim_name}.json",
                lambda: _run_pairwise(comb_fix, style_fix, motif_fix, dim_name, related_motif), f"评估 {aid}/{dim_name}")

            art_fixes[dim_name] = FixGroup(combined=comb_fix, style_only=style_fix, motif_only=motif_fix)
            art_evals[dim_name] = pairwise_data

        all_fixes[aid] = art_fixes
        all_evaluations[aid] = art_evals

    _print_matrix(all_diagnoses)
    _print_report(all_evaluations)
    _save_report(all_diagnoses, all_fixes, all_evaluations)


def _run_pairwise(comb_fix: str, style_fix: str, motif_fix: str, dim_name: str, related_motif: str) -> dict:
    pairs = [
        (("A", comb_fix), ("B", style_fix)),
        (("A", comb_fix), ("B", motif_fix)),
        (("A", style_fix), ("B", motif_fix)),
    ]
    group_names = ["combined", "style_only", "motif_only"]
    scores = {g: {d: 0 for d in ["specific", "root_cause", "motif_fit", "natural", "style_cover"]} for g in group_names}

    for fix_a, fix_b in pairs:
        result = evaluate_pairwise(fix_a, fix_b, dim_name, related_motif)
        winners = result.get("winners", {})
        for dim in ["specific", "root_cause", "motif_fit", "natural", "style_cover"]:
            w = winners.get(dim, "tie")
            if w == fix_a[0]:
                scores[fix_a[0]][dim] += 1
            elif w == fix_b[0]:
                scores[fix_b[0]][dim] += 1
            else:
                scores[fix_a[0]][dim] += 0.5
                scores[fix_b[0]][dim] += 0.5

    return {"aggregated_scores": scores}


def _print_matrix(all_diagnoses: dict):
    print(f"\n{'='*40}\n风格-母题映射矩阵\n{'='*40}")
    llm_inferred = {}
    for diag in all_diagnoses.values():
        for link in diag.get("links", []):
            wd = link["weak_dimension"]
            rm = link.get("related_missing_motif", "")
            llm_inferred.setdefault(wd, set())
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


def _print_report(all_evaluations: dict):
    print(f"\n{'='*60}")
    print("p10 分析报告：三组改法对比")
    totals = {g: {"specific": 0, "root_cause": 0, "motif_fit": 0, "natural": 0, "style_cover": 0, "n_dims": 0}
              for g in ["combined", "style_only", "motif_only"]}

    for aid, evals_by_dim in all_evaluations.items():
        print(f"\n## {aid}")
        for dim_name, eval_data in evals_by_dim.items():
            scores = eval_data.get("aggregated_scores", {})
            for group in ["combined", "style_only", "motif_only"]:
                if group in scores and scores[group]:
                    total = sum(scores[group].values())
                    print(f"  [{dim_name}] {group:<12}: wins={total:.1f} ({scores[group]})")
                    for k in scores[group]:
                        totals[group][k] += scores[group][k]
                    totals[group]["n_dims"] += 1

    print(f"\n## 总体对比")
    for group in ["combined", "style_only", "motif_only"]:
        gt = totals[group]
        if gt["n_dims"]:
            print(f"  {group}: {', '.join(f'{k}={gt[k]:.1f}' for k in ['specific', 'root_cause', 'motif_fit', 'natural', 'style_cover'])}")


def _save_report(all_diagnoses: dict, all_fixes: dict, all_evaluations: dict):
    llm_inferred = {}
    for diag in all_diagnoses.values():
        for link in diag.get("links", []):
            rm = link.get("related_missing_motif", "")
            if rm:
                llm_inferred.setdefault(link["weak_dimension"], set()).add(rm)

    report = {
        "diagnoses": all_diagnoses, "fixes": all_fixes, "evaluations": all_evaluations,
        "style_motif_mapping": {
            "human": {k: list(v) for k, v in HUMAN_STYLE_MOTIF_MAP.items()},
            "llm_inferred": {k: list(v) for k, v in llm_inferred.items()},
        },
    }
    cache_or_compute(RESULTS_DIR / "full_report.json", lambda: report, verbose=False)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
