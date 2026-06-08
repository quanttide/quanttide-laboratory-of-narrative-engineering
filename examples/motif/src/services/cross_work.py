"""跨作品分析服务 — 相似度矩阵、母题链重构、配对盲测"""

import json
import random

from src.infra import call_llm, clean_json
from src.prompts import load_prompt
from src.services.converter import pairs_to_dicts
from src.models import Variant, MotifSimilarityPair


def cross_work_similarity_matrix(fragments: list[Variant]) -> list[MotifSimilarityPair]:
    """跨作品相似度矩阵 — 对所有跨作品片段对做 LLM 判定。"""
    n = len(fragments)
    cross_same, cross_diff, intra_diff = [], [], []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = fragments[i], fragments[j]
            if a.series != b.series and a.motif == b.motif:
                cross_same.append((a, b))
            elif a.series != b.series:
                cross_diff.append((a, b))
            else:
                intra_diff.append((a, b))

    results = []
    for a, b in cross_same + cross_diff + intra_diff:
        series_name = lambda s: "都市言情" if s == "urban" else "校园言情"
        prompt = load_prompt("p06/similarity_judgment",
            series_a=series_name(a.series), motif_a=a.motif, desc_a=a.description,
            series_b=series_name(b.series), motif_b=b.motif, desc_b=b.description)
        try:
            raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
            data = json.loads(clean_json(raw))
            pair_a = f"{a.motif}_{a.series}_{a.scene}"
            pair_b = f"{b.motif}_{b.series}_{b.scene}"
            if a.series != b.series and a.motif == b.motif:
                pt = "cross-series_same-motif"
            elif a.series != b.series:
                pt = "cross-series_diff-motif"
            else:
                pt = "intra-series_diff-motif"
            results.append(MotifSimilarityPair(
                pair_a=pair_a, pair_b=pair_b,
                same_motif=data.get("same_motif", False),
                same_gt_motif=a.motif == b.motif,
                similarity=data.get("similarity", 0.0),
                shared_pattern=data.get("shared_pattern", ""),
                reasoning=data.get("reasoning", ""), pair_type=pt,
            ))
        except Exception as e:
            print(f"    ✗ {a.scene} vs {b.scene}: {e}")
    return results


def motif_chain_reconstruction(fragments: list[Variant]) -> dict:
    """母题链重构 — LLM 自由聚类（BLINDED）。"""
    descriptions = "\n".join(f"场景 {i+1}: {f.description}" for i, f in enumerate(fragments))
    prompt = load_prompt("p06/motif_chain_reconstruction", n=len(fragments), descriptions=descriptions)
    try:
        raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
        return json.loads(clean_json(raw))
    except Exception as e:
        print(f"    ✗ {e}")
        return {"clusters": []}


def blind_pairing(fragments: list[Variant], n_motifs: int = 4) -> dict:
    """配对盲测 — 随机选母题、打乱、LLM 配对。"""
    unique_motifs = list(dict.fromkeys(f.motif for f in fragments))
    selected = random.sample(unique_motifs, min(n_motifs, len(unique_motifs)))
    test_items = []
    for motif in selected:
        urban = [f for f in fragments if f.motif == motif and f.series == "urban"]
        campus = [f for f in fragments if f.motif == motif and f.series == "campus"]
        if urban and campus:
            test_items.append(random.choice(urban))
            test_items.append(random.choice(campus))
    random.shuffle(test_items)

    items_text = "\n".join(f"场景 {i+1}: {f.description}" for i, f in enumerate(test_items))
    prompt = load_prompt("p06/blind_pairing", n=len(test_items), pairs=len(test_items) // 2, items_text=items_text)
    try:
        raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
        result = json.loads(clean_json(raw))
        correct = sum(1 for pair in result.get("pairs", [])
                      if test_items[pair["pair"][0] - 1].motif == test_items[pair["pair"][1] - 1].motif)
        result["accuracy"] = correct / len(result.get("pairs", [])) if result.get("pairs") else 0
        result["total_pairs"] = len(result.get("pairs", []))
        result["correct"] = correct
        result["test_items"] = [{"id": i + 1, "motif": f.motif, "series": f.series}
                                for i, f in enumerate(test_items)]
        return result
    except Exception as e:
        return {"accuracy": 0, "error": str(e)}
