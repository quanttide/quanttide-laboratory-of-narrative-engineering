#!/usr/bin/env python3
"""
p05 — 母题可提取性实验

验证 LLM 能否从文本中提取母题，并与人工标注的 motif.yaml 对比。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import json
import os
import random
from collections import defaultdict
from pathlib import Path

import requests

from src.config import FICTION_ROOT, GALLERY_ROOT, DATA_DIR
from src.infra import call_llm, clean_json, cache_or_compute, read_article_text, load_motif_yaml, semantic_similarity
from src.prompts import load_prompt
from src.models import MatchItem, Motif, MotifProfile, CoverageReport

RESULTS_DIR = DATA_DIR / "p05"

ARTICLES = [
    {"id": "U1", "series": "urban", "name": "深夜失眠",   "path": "职场言情/4_成稿/1_2_深夜失眠.md"},
    {"id": "U2", "series": "urban", "name": "便利店闲坐", "path": "职场言情/4_成稿/4_1_便利店闲坐.md"},
    {"id": "U3", "series": "urban", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md"},
    {"id": "U4", "series": "urban", "name": "酒吧表白",   "path": "职场言情/3_初稿/8_2_酒吧表白.md"},
    {"id": "U5", "series": "urban", "name": "书房陪伴",   "path": "职场言情/4_成稿/10_1_书房陪伴.md"},
    {"id": "C1", "series": "campus", "name": "第四章（论坛私信）", "path": "校园言情/3_初稿/4_第四章.md"},
    {"id": "C2", "series": "campus", "name": "第五章（危机公关）", "path": "校园言情/4_成稿/5_第五章.md"},
    {"id": "C3", "series": "campus", "name": "第十章（KTV表白）", "path": "校园言情/4_成稿/10_第十章.md"},
]


def load_all_motif_ground_truth() -> dict:
    gt = {}
    for level in ["shared", "urban", "campus"]:
        path = GALLERY_ROOT / ("motif.yaml" if level == "shared" else f"{level}-romance/motif.yaml")
        if path.exists():
            gt[level] = load_motif_yaml(path)
    return gt


def load_motif_profile() -> MotifProfile:
    """从 YAML 加载三层母题库，返回类型安全的 MotifProfile。"""
    raw = load_all_motif_ground_truth()
    def _to_motifs(data: dict) -> list[Motif]:
        return [Motif(title=m["title"], description=m.get("description", ""), weight=m.get("weight", 5))
                for m in data.get("motifs", [])]
    return MotifProfile(
        shared=_to_motifs(raw.get("shared", {})),
        urban=_to_motifs(raw.get("urban", {})),
        campus=_to_motifs(raw.get("campus", {})),
    )


def extract_motifs(text: str, article_name: str) -> dict:
    sample = text[:3000]
    prompt = load_prompt("p05/extract_single_motif", article_name=article_name, sample=sample)
    raw = call_llm(prompt)
    return json.loads(clean_json(raw))


def extract_motifs_joint(texts: list[dict], series_name: str) -> dict:
    combined_parts = [f"--- 文章: {t['name']} ---\n{t['text'][:2000]}" for t in texts]
    combined = "\n\n".join(combined_parts)
    prompt = load_prompt("p05/extract_joint_motif", series_name=series_name, combined=combined)
    raw = call_llm(prompt)
    return json.loads(clean_json(raw))


def compare_with_ground_truth(single_results: dict, joint_results: dict, gt: dict) -> dict:
    """步骤 3：与人工标注对比（覆盖率基于 unique GT 母题去重）"""
    report = {}
    for level_name in ["urban", "campus"]:
        level_data = gt.get(level_name, {})
        gt_motifs = level_data.get("motifs", [])
        if not gt_motifs:
            continue

        gt_descs = {m["title"]: m.get("description", "") for m in gt_motifs}

        single_coverage = {}
        for art in ARTICLES:
            if art["series"] != level_name:
                continue
            aid = art["id"]
            extracted = single_results.get(aid, {}).get("motifs", [])
            matched_gt = set()
            match_details = []
            for e in extracted:
                for g_title, g_desc in gt_descs.items():
                    sim = semantic_similarity(e.get("description", ""), g_desc)
                    if sim > 0.7 and g_title not in matched_gt:
                        matched_gt.add(g_title)
                        match_details.append(MatchItem(extracted=e["title"], gt=g_title, similarity=sim))
                        break
            cr = CoverageReport(
                extracted_count=len(extracted),
                matched_count=len(matched_gt),
                coverage=len(matched_gt) / len(gt_motifs) if gt_motifs else 0,
                matches=match_details,
            )
            single_coverage[aid] = {
                "extracted_count": cr.extracted_count,
                "matched_count": cr.matched_count,
                "coverage": cr.coverage,
                "matches": [{"extracted": m.extracted, "gt": m.gt, "similarity": m.similarity} for m in cr.matches],
            }

        joint = joint_results.get(level_name, {}).get("motifs", [])
        joint_matched_gt = set()
        joint_match_details = []
        for e in joint:
            for g_title, g_desc in gt_descs.items():
                sim = semantic_similarity(e.get("description", ""), g_desc)
                if sim > 0.7 and g_title not in joint_matched_gt:
                    joint_matched_gt.add(g_title)
                    joint_match_details.append(MatchItem(extracted=e["title"], gt=g_title, similarity=sim))
                    break

        report[level_name] = {
            "single_coverage": single_coverage,
            "single_avg_coverage": sum(c["coverage"] for c in single_coverage.values()) / len(single_coverage)
            if single_coverage else 0,
            "joint_coverage": len(joint_matched_gt) / len(gt_motifs) if gt_motifs else 0,
            "joint_matches": [{"extracted": m.extracted, "gt": m.gt, "similarity": m.similarity} for m in joint_match_details],
            "gt_motif_count": len(gt_motifs),
        }
    return report


def blind_clustering(motif_descriptions: dict) -> list[dict]:
    items = []
    for aid, data in motif_descriptions.items():
        descs = [m.get("description", "") for m in data.get("motifs", [])[:4]]
        items.append({"id": aid, "description": " | ".join(descs)})

    random.shuffle(items)
    profiles = "\n\n".join(f"[文章 {it['id']}]\n{it['description']}" for it in items)
    prompt = load_prompt("p05/blind_clustering", profiles=profiles)
    raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
    return json.loads(clean_json(raw))


def report(gt: dict, single_results: dict, joint_results: dict, comparison: dict, clusterings: list[dict]):
    series_map = {a["id"]: a["series"] for a in ARTICLES}
    series_names = {"urban": "都市言情", "campus": "校园言情"}

    print("\n" + "=" * 60)
    print("p05 分析报告：母题可提取性")
    print("=" * 60)
    print("\n## Ground Truth（人工标注）")
    for level in ["shared", "urban", "campus"]:
        motifs = gt.get(level, {}).get("motifs", [])
        if motifs:
            print(f"  {level}: {len(motifs)} 个母题 — {', '.join(m['title'] for m in motifs)}")

    print("\n## 母题提取质量对比")
    for level_name in ["urban", "campus"]:
        c = comparison.get(level_name, {})
        if not c:
            continue
        print(f"\n  {series_names.get(level_name, level_name)} ({c['gt_motif_count']} 个人工标注母题):")
        print(f"    单篇平均覆盖率: {c['single_avg_coverage']*100:.0f}%")
        print(f"    多篇联合覆盖率: {c['joint_coverage']*100:.0f}%")
        for aid, sc in c.get("single_coverage", {}).items():
            name = next(a["name"] for a in ARTICLES if a["id"] == aid)
            print(f"      {aid} {name:<14} {sc['extracted_count']} 个提取 / {sc['matched_count']} 个匹配 = {sc['coverage']*100:.0f}%")

    print(f"\n## 盲品归因（{len(clusterings)} 次独立运行）")
    total_accuracy = 0
    for r_idx, clustering in enumerate(clusterings):
        correct = 0
        for g in clustering.get("groups", []):
            members = g["members"]
            series_in_group = [series_map.get(m, "?") for m in members]
            counts = {}
            for s in series_in_group:
                counts[s] = counts.get(s, 0) + 1
            max_count = max(counts.values())
            if list(counts.values()).count(max_count) > 1:
                correct += max_count
            else:
                majority = max(set(series_in_group), key=series_in_group.count)
                correct += sum(1 for s in series_in_group if s == majority)
        acc = correct / len(ARTICLES) * 100 if ARTICLES else 0
        total_accuracy += acc
        print(f"  第 {r_idx+1} 轮: 同系列聚类率 {correct}/{len(ARTICLES)} = {acc:.0f}%")
    print(f"\n  平均聚类率: {total_accuracy / len(clusterings):.0f}%" if clusterings else "")


def main():
    print("=" * 60)
    print("p05 — 母题可提取性实验")
    print("=" * 60)

    RESULTS_DIR.mkdir(exist_ok=True)

    print("\n加载 Gallery 母题标注...")
    gt = load_all_motif_ground_truth()
    for level, data in gt.items():
        print(f"  {level}: {len(data.get('motifs', []))} 个母题")

    print("\n步骤 1: 单篇母题提取")
    single_results = {}
    for art in ARTICLES:
        result = cache_or_compute(
            RESULTS_DIR / f"motif_{art['id']}.json",
            lambda a=art: extract_motifs(read_article_text(a["path"]), a["name"]),
            f"{art['id']} {art['name']}",
        )
        single_results[art["id"]] = result

    print("\n步骤 2: 多篇联合提取")
    joint_results = {}
    series_articles = defaultdict(list)
    for art in ARTICLES:
        try:
            series_articles[art["series"]].append({"name": art["name"], "text": read_article_text(art["path"])})
        except Exception:
            continue

    for series, texts in series_articles.items():
        series_name = "都市言情" if series == "urban" else "校园言情"
        result = cache_or_compute(
            RESULTS_DIR / f"motif_{series}_joint.json",
            lambda t=texts, s=series_name: extract_motifs_joint(t, s),
            f"{series} 联合提取 ({len(texts)} 篇)",
        )
        joint_results[series] = result

    print("\n步骤 3: 与人工标注对比")
    comparison = compare_with_ground_truth(single_results, joint_results, gt)

    print("\n步骤 4: 盲品归因")
    clusterings = []
    for r in range(3):
        result = cache_or_compute(
            RESULTS_DIR / f"blind_clustering_r{r+1}.json",
            lambda: blind_clustering(single_results),
            f"第 {r+1} 轮",
        )
        clusterings.append(result)

    cache_or_compute(RESULTS_DIR / "comparison.json", lambda: comparison, verbose=False)
    report(gt, single_results, joint_results, comparison, clusterings)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
