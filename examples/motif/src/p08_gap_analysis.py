#!/usr/bin/env python3
"""
p08 — 母题缝隙分析与多向改进实验

检测初稿中的母题缝隙，从 6 个方向生成差异化改进建议。
"""
import json
from pathlib import Path

from src.config import GALLERY_ROOT, DATA_DIR
from src.infra import call_llm, clean_json, cache_or_compute, read_article_text, load_motif_yaml
from src.prompts import load_prompt
from src.domain import DIRECTIONS, EvaluationScore, GapAttribution, Suggestion, Motif, GapItem, GapReport


def _to_motifs(items) -> list[Motif]:
    if not items:
        return []
    if isinstance(items[0], Motif):
        return items
    return [Motif(title=m["title"], description=m.get("description", ""), weight=m.get("weight", 5)) for m in items]


def _to_gap_report(data) -> GapReport:
    if isinstance(data, GapReport):
        return data
    def _items(items):
        if not items:
            return []
        if isinstance(items[0], GapItem):
            return items
        return [GapItem(title=i["title"], target_weight=i["target_weight"],
                        extracted_weight=i.get("extracted_weight"), description=i.get("description", ""),
                        matched_via=i.get("matched_via")) for i in items]
    return GapReport(covered=_items(data.get("covered", [])), missing=_items(data.get("missing", [])),
                     weak=_items(data.get("weak", [])),
                     extracted_motifs=_to_motifs(data.get("extracted_motifs", [])))


def _gap_report_to_dict(r: GapReport) -> dict:
    def _to_dict(items: list[GapItem]) -> list[dict]:
        return [{"title": i.title, "target_weight": i.target_weight, "extracted_weight": i.extracted_weight,
                 "description": i.description, "matched_via": i.matched_via} for i in items]
    return {"covered": _to_dict(r.covered), "missing": _to_dict(r.missing), "weak": _to_dict(r.weak),
            "extracted_motifs": [vars(m) for m in r.extracted_motifs]}

RESULTS_DIR = DATA_DIR / "p08"

ARTICLES = [
    {"id": "D1", "series": "urban", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md"},
    {"id": "D2", "series": "urban", "name": "酒吧表白",   "path": "职场言情/3_初稿/8_2_酒吧表白.md"},
    {"id": "D3", "series": "campus", "name": "第六章",     "path": "校园言情/3_初稿/6_第六章.md"},
    {"id": "D4", "series": "campus", "name": "第十章 KTV", "path": "校园言情/4_成稿/10_第十章.md"},
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


def extract_motifs(text: str, article_name: str) -> list[Motif]:
    sample = text[:3000]
    prompt = load_prompt("p08/extract_motifs_gap", article_name=article_name, sample=sample)
    raw = call_llm(prompt)
    items = json.loads(clean_json(raw)).get("motifs", [])
    return [Motif(title=m["title"], description=m.get("description", ""), weight=m.get("weight", 5)) for m in items]


def compute_gap_report(extracted: list[Motif], target_motifs: list[dict]) -> GapReport:
    extracted_titles = {m.title for m in extracted}
    covered, missing, weak = [], [], []
    for tm in target_motifs:
        t = tm["title"]
        if t in extracted_titles:
            ext = next(m for m in extracted if m.title == t)
            if ext.weight < tm.get("weight", 5) * 0.5:
                weak.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=ext.weight))
            else:
                covered.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=ext.weight))
        else:
            found = False
            for et in extracted:
                if t in et.title or et.title in t:
                    if et.weight < tm["weight"] * 0.5:
                        weak.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=et.weight, matched_via=et.title))
                    else:
                        covered.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=et.weight, matched_via=et.title))
                    found = True
                    break
            if not found:
                missing.append(GapItem(title=t, target_weight=tm["weight"], description=tm.get("description", "")))
    return GapReport(covered=covered, missing=missing, weak=weak, extracted_motifs=extracted)


def gap_attribution(article_name: str, text_sample: str, missing_motif: dict) -> GapAttribution:
    prompt = load_prompt("p08/gap_attribution",
        article_name=article_name, missing_title=missing_motif["title"],
        missing_description=missing_motif.get("description", ""), sample=text_sample[:2000])
    raw = call_llm(prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.2)
    result = json.loads(clean_json(raw))
    return GapAttribution(
        gap_types=result.get("gap_types"),
        alternative_motif=result.get("alternative_motif"),
        reasoning=result.get("reasoning", ""),
    )


def generate_suggestions(article_name: str, text_sample: str, gap: dict, gap_types: list[str], target_motif: dict, series: str) -> list[Suggestion]:
    mirrors = CROSS_WORK_MIRRORS.get(target_motif["title"], [])
    mirror_text = "跨作品/跨场景变体参考：\n" + "\n".join(f"  - {m}" for m in mirrors) if mirrors else ""
    prompt = load_prompt("p08/generate_suggestions",
        article_name=article_name, target_title=target_motif["title"],
        target_description=target_motif.get("description", ""),
        gap_types_str=", ".join(gap_types), mirror_text=mirror_text,
        sample=text_sample[:2500])
    try:
        raw = call_llm(prompt, temperature=0.7)
        items = json.loads(clean_json(raw)).get("suggestions", [])
        return [Suggestion(direction=s["direction"], text=s.get("text", ""),
                           paragraph_ref=s.get("paragraph_ref", ""),
                           reverse_risk=s.get("reverse_risk"))
                for s in items]
    except Exception:
        return []


def evaluate_suggestions(suggestions: list[Suggestion], gap_title: str, article_name: str) -> list[dict]:
    items = "\n".join(f"[{s.direction}] {s.text[:120]}" for s in suggestions)
    prompt = load_prompt("p08/evaluate_suggestions", article_name=article_name, gap_title=gap_title, items=items)
    try:
        raw = call_llm(prompt, temperature=0.1)
        return json.loads(clean_json(raw)).get("evaluations", [])
    except Exception:
        return []


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

        # lazily convert cached data to typed gap report
        gap_report_raw = cache_or_compute(
            RESULTS_DIR / f"motif_report_{art['id']}.json",
            lambda: _gap_report_to_dict(compute_gap_report(extract_motifs(text, art["name"]), target_motifs)),
            f"母题报告 {art['id']}",
        )
        gap_report = _to_gap_report(gap_report_raw)
        all_gaps[art["id"]] = gap_report

        gaps_to_fix = gap_report.missing + gap_report.weak
        print(f"  缝隙数: {len(gaps_to_fix)} ({len(gap_report.covered)} 覆盖 / {len(gap_report.missing)} 缺失 / {len(gap_report.weak)} 弱化)")

        art_suggestions, art_evaluations = {}, {}
        for gap in gaps_to_fix:
            gt = gap.title
            attr = cache_or_compute(
                RESULTS_DIR / f"gap_attr_{art['id']}_{gt}.json",
                lambda g=gap: gap_attribution(art["name"], text, g),
            )
            if not isinstance(attr, GapAttribution):
                attr = GapAttribution(gap_types=attr.get("gap_types"), alternative_motif=attr.get("alternative_motif"), reasoning=attr.get("reasoning", ""))
            suggestions = cache_or_compute(
                RESULTS_DIR / f"suggestions_{art['id']}_{gt}.json",
                lambda: generate_suggestions(art["name"], text, gap, attr.gap_types or [],
                    next((m for m in target_motifs if m["title"] == gt), {}), series),
            )
            if suggestions and not isinstance(suggestions[0], Suggestion):
                suggestions = [Suggestion(direction=s["direction"], text=s.get("text", ""),
                    paragraph_ref=s.get("paragraph_ref", ""), reverse_risk=s.get("reverse_risk")) for s in suggestions]
            art_suggestions[gt] = suggestions

            evals = cache_or_compute(
                RESULTS_DIR / f"evaluation_{art['id']}_{gt}.json",
                lambda: evaluate_suggestions(suggestions, gt, art["name"]),
            )
            art_evaluations[gt] = evals

        all_suggestions[art["id"]] = art_suggestions
        all_evaluations[art["id"]] = art_evaluations

    print(f"\n{'='*60}\np08 分析报告\n{'='*60}")
    for art in ARTICLES:
        gr = _to_gap_report(all_gaps.get(art["id"], {}))
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
        lambda: {"gaps": all_gaps, "suggestions": all_suggestions, "evaluations": all_evaluations}, verbose=False)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
