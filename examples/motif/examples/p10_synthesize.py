#!/usr/bin/env python3
"""
p10 — 母题驱动的风格改进实验

风格诊断维度弱点 → 母题根因分析 → 三组改法对比。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from src.config import FICTION_ROOT, GALLERY_ROOT, DATA_DIR
from src.services import (
    cache_or_compute, cache_or_compute_text, read_article_text, load_yaml,
    load_gallery, build_style_prompt,
    extract_motifs, style_review, diagnose_style_motif_links,
    generate_combined_fix, generate_style_only_fix, evaluate_pairwise,
    to_motifs, to_dims, dims_to_dicts, motifs_to_dicts,
)
from src.models import StyleDimension

RESULTS_DIR = DATA_DIR / "p10"
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
            if w == fix_a[0]: scores[fix_a[0]][dim] += 1
            elif w == fix_b[0]: scores[fix_b[0]][dim] += 1
            else: scores[fix_a[0]][dim] += 0.5; scores[fix_b[0]][dim] += 0.5
    return {"aggregated_scores": scores}


def main():
    print("=" * 60)
    print("p10 — 母题驱动的风格改进实验")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    from src.prompts import load_prompt
    urban_style = load_yaml(GALLERY_ROOT / "urban-romance" / "style.yaml")
    urban_motif = load_yaml(GALLERY_ROOT / "urban-romance" / "motif.yaml")
    target_motifs = urban_motif.get("motifs", [])
    samples_dir = GALLERY_ROOT / "urban-romance" / "samples"
    style_prompt = build_style_prompt(urban_style, samples_dir)
    dims_data = urban_style.get("dimensions", [])
    dim_descs = {d["title"]: d.get("description", "") for d in dims_data}
    motif_descs = {m["title"]: m.get("description", "") for m in target_motifs}

    all_diagnoses, all_fixes, all_evaluations = {}, {}, {}

    for art in ARTICLES:
        aid = art["id"]
        print(f"\n{'='*40}\n{aid} {art['name']} ({art['type']})")
        text = read_article_text(art["path"])

        style_raw = cache_or_compute(RESULTS_DIR / f"style_review_{aid}.json",
            lambda: dims_to_dicts(style_review(text, art["name"], style_prompt).dimension_scores),
            f"风格评审 {aid}")
        dimension_scores = to_dims(style_raw)

        motif_raw = cache_or_compute(RESULTS_DIR / f"motif_extract_{aid}.json",
            lambda: motifs_to_dicts(extract_motifs(text, art["name"])), f"母题提取 {aid}")
        motif_list = to_motifs(motif_raw)

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
                lambda: generate_combined_fix(art["name"], text, dim_name, related_motif, motif_desc, dim_desc), verbose=False)
            style_fix = cache_or_compute_text(RESULTS_DIR / f"fix_style_{aid}_{dim_name}.txt",
                lambda: generate_style_only_fix(art["name"], text, dim_name, dim_desc), verbose=False)
            motif_fix_prompt = load_prompt("p10/fix_motif_only",
                article_name=art["name"], related_motif=related_motif, motif_desc=motif_desc, sample=text[:2000])
            from src.infra import call_llm_text
            motif_fix = cache_or_compute_text(RESULTS_DIR / f"fix_motif_{aid}_{dim_name}.txt",
                lambda: call_llm_text(motif_fix_prompt, "你是一个创作顾问。只输出建议文本。", temperature=0.3).strip(), verbose=False)

            from src.models import FixGroup
            art_fixes[dim_name] = FixGroup(combined=comb_fix, style_only=style_fix, motif_only=motif_fix)

            pairwise_data = cache_or_compute(RESULTS_DIR / f"eval_{aid}_{dim_name}.json",
                lambda: _run_pairwise(comb_fix, style_fix, motif_fix, dim_name, related_motif), f"评估 {aid}/{dim_name}")
            art_evals[dim_name] = pairwise_data

        all_fixes[aid] = art_fixes
        all_evaluations[aid] = art_evals

    # Mapping matrix
    print(f"\n{'='*40}\n风格-母题映射矩阵\n{'='*40}")
    llm_inferred = {}
    for diag in all_diagnoses.values():
        for link in diag.get("links", []):
            rm = link.get("related_missing_motif", "")
            if rm:
                llm_inferred.setdefault(link["weak_dimension"], set()).add(rm)
    for dim_name in sorted(set(list(HUMAN_STYLE_MOTIF_MAP.keys()) + list(llm_inferred.keys()))):
        human = set(HUMAN_STYLE_MOTIF_MAP.get(dim_name, []))
        llm = llm_inferred.get(dim_name, set())
        shared = human & llm; llm_new = llm - human; human_missed = human - llm
        jaccard = len(shared) / len(human | llm) if (human | llm) else 0
        print(f"  {dim_name}: human={human} LLM={llm} shared={shared} new={llm_new} missed={human_missed} J={jaccard:.2f}")

    # Report
    print(f"\n{'='*60}\np10 分析报告：三组改法对比\n{'='*60}")
    totals = {g: {d: 0 for d in ["specific", "root_cause", "motif_fit", "natural", "style_cover"]} | {"n_dims": 0}
              for g in ["combined", "style_only", "motif_only"]}
    for aid, evals_by_dim in all_evaluations.items():
        print(f"\n## {aid}")
        for dim_name, eval_data in evals_by_dim.items():
            scores = eval_data.get("aggregated_scores", {})
            for group in ["combined", "style_only", "motif_only"]:
                if group in scores and scores[group]:
                    total = sum(scores[group].values())
                    print(f"  [{dim_name}] {group:<12}: wins={total:.1f} ({scores[group]})")
                    for k in scores[group]: totals[group][k] += scores[group][k]
                    totals[group]["n_dims"] += 1

    print(f"\n## 总体对比")
    for group in ["combined", "style_only", "motif_only"]:
        gt = totals[group]
        if gt["n_dims"]:
            print(f"  {group}: {', '.join(f'{k}={gt[k]:.1f}' for k in ['specific', 'root_cause', 'motif_fit', 'natural', 'style_cover'])}")

    cache_or_compute(RESULTS_DIR / "full_report.json", lambda: {
        "diagnoses": all_diagnoses, "fixes": all_fixes, "evaluations": all_evaluations}, verbose=False)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
