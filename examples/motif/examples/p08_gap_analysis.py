#!/usr/bin/env python3
"""
p08 — 母题缝隙分析与多向改进实验

检测初稿中的母题缝隙，从 6 个方向生成差异化改进建议。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import dataclasses
from src.config import GALLERY_ROOT, DATA_DIR
from src.infra import cache_or_compute, read_article_text, load_motif_yaml
from src.services import (
    extract_motifs, compute_gap_report, gap_attribution,
    generate_suggestions, evaluate_suggestions,
    to_gap_report, to_motifs,
)
from src.models import DIRECTIONS, EvaluationScore, Article, ArticleAnalysis

RESULTS_DIR = DATA_DIR / "p08"

ARTICLES = [
    {"id": "D1", "series": "urban", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md"},
    {"id": "D2", "series": "urban", "name": "酒吧表白",   "path": "职场言情/3_初稿/8_2_酒吧表白.md"},
    {"id": "D3", "series": "campus", "name": "第六章",     "path": "校园言情/3_初稿/6_第六章.md"},
    {"id": "D4", "series": "campus", "name": "第十章 KTV", "path": "校园言情/4_成稿/10_第十章.md"},
]


def main():
    print("=" * 60)
    print("p08 — 母题缝隙分析与多向改进实验")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    urban_target = load_motif_yaml(GALLERY_ROOT / "urban-romance" / "motif.yaml")
    campus_target = load_motif_yaml(GALLERY_ROOT / "campus-romance" / "motif.yaml")

    all_gaps, all_suggestions, all_evaluations = {}, {}, {}

    for art in ARTICLES:
        series = art["series"]
        target = urban_target if series == "urban" else campus_target
        target_motifs = target.get("motifs", [])
        target_titles = [m["title"] for m in target_motifs]
        print(f"\n{'='*40}\n{art['id']} {art['name']} ({series})")
        print(f"  目标母题: {', '.join(target_titles)}")

        text = read_article_text(art["path"])

        gap_raw = cache_or_compute(
            RESULTS_DIR / f"motif_report_{art['id']}.json",
            lambda: dataclasses.asdict(compute_gap_report(
                extract_motifs(text, art["name"], "p08/extract_motifs_gap"), target_motifs)),
            f"母题报告 {art['id']}",
        )
        gap_report = to_gap_report(gap_raw)
        all_gaps[art["id"]] = gap_report

        gaps_to_fix = gap_report.fixable_gaps()
        print(f"  缝隙数: {len(gaps_to_fix)} ({gap_report.summary()})")

        art_suggestions, art_evaluations = {}, {}
        for gap_item in gaps_to_fix:
            gt = gap_item.title
            attr = cache_or_compute(
                RESULTS_DIR / f"gap_attr_{art['id']}_{gt}.json",
                lambda: gap_attribution(art["name"], text, {"title": gt, "description": "", **{}}),
            )
            suggestions = cache_or_compute(
                RESULTS_DIR / f"suggestions_{art['id']}_{gt}.json",
                lambda: [dataclasses.asdict(s) for s in generate_suggestions(art["name"], text, gap_item, attr.gap_types or [],
                    next((m for m in target_motifs if m["title"] == gt), {}))],
            )
            art_suggestions[gt] = suggestions

            evals = cache_or_compute(
                RESULTS_DIR / f"evaluation_{art['id']}_{gt}.json",
                lambda: evaluate_suggestions(suggestions, gt, art["name"]),
            )
            art_evaluations[gt] = evals

        all_suggestions[art["id"]] = art_suggestions
        all_evaluations[art["id"]] = art_evaluations

    # ─── 聚合出口：统一为 ArticleAnalysis ───
    analyses: dict[str, ArticleAnalysis] = {}
    for art in ARTICLES:
        aid = art["id"]
        article = Article(id=aid, series=art["series"], name=art["name"], path=art["path"])
        gr = to_gap_report(all_gaps.get(aid, {}))
        analyses[aid] = ArticleAnalysis(
            article=article,
            motifs=gr.extracted_motifs,
            gap_report=gr,
            suggestions=all_suggestions.get(aid, {}),
        )

    print(f"\n{'='*60}\np08 分析报告\n{'='*60}")
    for art in ARTICLES:
        analysis = analyses.get(art["id"])
        if not analysis or not analysis.gap_report:
            continue
        gr = analysis.gap_report
        print(f"\n## {art['id']} {art['name']}")
        print(f"  覆盖: {len(gr.covered)} / 缺失: {len(gr.missing)} / 弱化: {len(gr.weak)}")
        for m in gr.missing:
            print(f"    缺 {m.title} (target weight={m.target_weight})")
        for w in gr.weak:
            print(f"    弱 {w.title} (extracted={w.extracted_weight} vs target={w.target_weight})")
        evals = all_evaluations.get(art["id"], {})
        for gt, elist in evals.items():
            if not elist:
                continue
            print(f"\n  [{gt}] 各方向平均分:")
            for d in DIRECTIONS:
                de = [e for e in elist if e.get("direction") == d.id]
                if de:
                    scores = de[0].get("scores", {})
                    es = EvaluationScore(**{k: v for k, v in scores.items() if k in ["feasibility","motif_fit","naturalness","actionable"]})
                    avg = sum([es.feasibility, es.motif_fit, es.naturalness, es.actionable]) / 4
                    print(f"    {d.name:<4}: feas={es.feasibility} fit={es.motif_fit} nat={es.naturalness} act={es.actionable} avg={avg:.1f}")

    cache_or_compute(RESULTS_DIR / "full_report.json",
        lambda: {
            "analyses": {aid: {
                "article": dataclasses.asdict(a.article) if hasattr(a.article, 'id') else a.article,
                "gap_report": dataclasses.asdict(a.gap_report) if a.gap_report else None,
                "suggestions": a.suggestions,
            } for aid, a in analyses.items()},
            "evaluations": all_evaluations,
        }, verbose=False)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
