#!/usr/bin/env python3
"""
p06 — 母题跨作品识别实验

验证 LLM 能否识别同一母题在不同作品中的不同变体，建立跨作品关联。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import json
import random
from pathlib import Path

from src.config import FICTION_ROOT, GALLERY_ROOT, DATA_DIR
from src.infra import call_llm, clean_json, cache_or_compute
from src.prompts import load_prompt
from src.models import Variant, MotifSimilarityPair


def _to_pairs(data: list) -> list[MotifSimilarityPair]:
    if not data:
        return []
    if isinstance(data[0], MotifSimilarityPair):
        return data
    return [MotifSimilarityPair(**d) for d in data]

RESULTS_DIR = DATA_DIR / "p06"

CROSS_WORK_MOTIFS = [
    {
        "motif": "手势先于语言",
        "variants": [
            {"series": "urban", "scene": "便利店闲坐", "desc": "毛巾擦头发：他掏出毛巾轻擦她的头发→回过神来赶快递给她"},
            {"series": "campus", "scene": "医院初遇", "desc": "纸巾擦眼泪：他掏四五个口袋找纸巾→拆开→鬼使神差地擦上去"},
        ],
    },
    {
        "motif": "手势先于语言",
        "variants": [
            {"series": "urban", "scene": "酒吧表白", "desc": "拥抱：他把她拉进怀里→她捶他→他拍着哄→揽入怀中"},
            {"series": "campus", "scene": "KTV表白", "desc": "披外套：他把外套披上→尝试扣扣子→拉进怀里"},
        ],
    },
    {
        "motif": "日常的缝隙",
        "variants": [
            {"series": "urban", "scene": "书房陪伴", "desc": "她在旁边旁听产品会议，他边开会边敲她脑袋"},
            {"series": "campus", "scene": "危机公关", "desc": "一起吃火锅→一起写联合声明→她润色温度"},
        ],
    },
    {
        "motif": "双向奔赴",
        "variants": [
            {"series": "urban", "scene": "咖啡厅重逢", "desc": "他的日记写满十年→她翻到他的信→原来你也在等我"},
            {"series": "campus", "scene": "论坛隔空喊话", "desc": "他发帖→她回应→有缘再见→互关"},
        ],
    },
    {
        "motif": "温和的善良人",
        "variants": [
            {"series": "urban", "scene": "书房陪伴", "desc": "我更心疼在风暴中孤独无助的你"},
            {"series": "campus", "scene": "写声明", "desc": "可是你没有任何错啊——双方都抢着承担责任"},
        ],
    },
    {
        "motif": "旁观者的缺席与在场",
        "variants": [
            {"series": "urban", "scene": "便利店闲坐", "desc": "两个人的封闭空间，只有雨声和对话，无旁观者"},
            {"series": "campus", "scene": "论坛评论区", "desc": "CP粉回复'眼神拉丝了''铁树开花'——情感被所有人见证"},
        ],
    },
    {
        "motif": "时间的两种用法",
        "variants": [
            {"series": "urban", "scene": "咖啡厅重逢", "desc": "他看着她十年前的照片→这条路我已独自走了十年"},
            {"series": "campus", "scene": "KTV表白", "desc": "从第一章到第十章，时间跨度仅一周——事件高密度"},
        ],
    },
]

SCENE_PARAGRAPH_MAP: dict[str, dict[str, str]] = {
    "便利店闲坐": {"file": "职场言情/4_成稿/4_1_便利店谈心.md", "keyword": "便利店"},
    "酒吧表白": {"file": "职场言情/4_成稿/8_2_酒吧表白.md", "keyword": "表白"},
    "书房陪伴": {"file": "职场言情/4_成稿/10_1_书房陪伴.md", "keyword": "旁听"},
    "咖啡厅重逢": {"file": "职场言情/4_成稿/1_1_咖啡厅重逢.md", "keyword": "日记"},
    "医院初遇": {"file": "校园言情/3_初稿/1_第一章.md", "keyword": "扶住"},
    "KTV表白": {"file": "校园言情/4_成稿/10_第十章.md", "keyword": "外套"},
    "危机公关": {"file": "校园言情/4_成稿/5_第五章.md", "keyword": "火锅"},
    "写声明": {"file": "校园言情/4_成稿/5_第五章.md", "keyword": "声明"},
    "论坛隔空喊话": {"file": "校园言情/3_初稿/2_第二章.md", "keyword": "有缘再见"},
    "论坛评论区": {"file": "校园言情/3_初稿/6_第六章.md", "keyword": "火锅"},
}


def load_full_paragraph_fragments() -> list[Variant]:
    fragments = collect_scene_fragments()
    for i, f in enumerate(fragments):
        info = SCENE_PARAGRAPH_MAP.get(f.scene)
        if info:
            path = FICTION_ROOT / info["file"]
            if path.exists():
                text = path.read_text("utf-8")
                body = [l for l in text.split("\n") if not l.startswith("# ")]
                full = "\n".join(body)
                kw = info.get("keyword", "")
                if kw and kw in full:
                    idx = full.index(kw)
                    start = max(0, idx - 250)
                    fragments[i] = Variant(motif=f.motif, series=f.series, scene=f.scene, description=full[start:start + 500].strip())
                else:
                    fragments[i] = Variant(motif=f.motif, series=f.series, scene=f.scene, description=full[:500].strip())
    return fragments


def collect_scene_fragments() -> list[Variant]:
    fragments = []
    for m in CROSS_WORK_MOTIFS:
        for v in m["variants"]:
            fragments.append(Variant(motif=m["motif"], series=v["series"], scene=v["scene"], description=v["desc"]))
    return fragments


def cross_work_similarity_matrix(fragments: list[Variant]) -> list[MotifSimilarityPair]:
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
            same_gt = a.motif == b.motif
            if a.series != b.series and a.motif == b.motif:
                pt = "cross-series_same-motif"
            elif a.series != b.series:
                pt = "cross-series_diff-motif"
            else:
                pt = "intra-series_diff-motif"
            results.append(MotifSimilarityPair(
                pair_a=pair_a, pair_b=pair_b,
                same_motif=data.get("same_motif", False), same_gt_motif=same_gt,
                similarity=data.get("similarity", 0.0),
                shared_pattern=data.get("shared_pattern", ""),
                reasoning=data.get("reasoning", ""), pair_type=pt,
            ))
        except Exception as e:
            print(f"    ✗ {a.scene} vs {b.scene}: {e}")
    return results


def motif_chain_reconstruction(fragments: list[Variant]) -> dict:
    descriptions = "\n".join(f"场景 {i+1}: {f.description}" for i, f in enumerate(fragments))
    prompt = load_prompt("p06/motif_chain_reconstruction", n=len(fragments), descriptions=descriptions)
    try:
        raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
        return json.loads(clean_json(raw))
    except Exception as e:
        print(f"    ✗ {e}")
        return {"clusters": []}


def blind_pairing(fragments: list[Variant], n_motifs: int = 4) -> dict:
    unique_motifs = list(dict.fromkeys(f.motif for f in fragments))
    selected = random.sample(unique_motifs, min(n_motifs, len(unique_motifs)))
    test_items = []
    for motif in selected:
        urban_variants = [f for f in fragments if f.motif == motif and f.series == "urban"]
        campus_variants = [f for f in fragments if f.motif == motif and f.series == "campus"]
        if urban_variants and campus_variants:
            test_items.append(random.choice(urban_variants))
            test_items.append(random.choice(campus_variants))
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
        result["test_items"] = [{"id": i + 1, "motif": f.motif, "series": f.series} for i, f in enumerate(test_items)]
        return result
    except Exception as e:
        return {"accuracy": 0, "error": str(e)}


def report(similarity_results: list[MotifSimilarityPair], reconstruction: dict, blind_results: list[dict]):
    print("\n" + "=" * 60)
    print("p06 分析报告：母题跨作品识别")
    print("=" * 60)

    cross_same = [r for r in similarity_results if r.pair_type == "cross-series_same-motif"]
    cross_diff = [r for r in similarity_results if r.pair_type == "cross-series_diff-motif"]
    intra_diff = [r for r in similarity_results if r.pair_type == "intra-series_diff-motif"]

    avg_same = sum(r.similarity for r in cross_same) / len(cross_same) if cross_same else 0
    avg_cross = sum(r.similarity for r in cross_diff) / len(cross_diff) if cross_diff else 0
    avg_intra = sum(r.similarity for r in intra_diff) / len(intra_diff) if intra_diff else 0

    print(f"\n## 相似度矩阵")
    print(f"  A) 跨作品·同母题: {avg_same:.3f} ({len(cross_same)} 对)")
    print(f"  B) 跨作品·异母题: {avg_cross:.3f} ({len(cross_diff)} 对)")
    print(f"  C) 同作品·异母题: {avg_intra:.3f} ({len(intra_diff)} 对)")
    print(f"  差异 A-C: {avg_same - avg_intra:+.3f}")
    print(f"  差异 B-C: {avg_cross - avg_intra:+.3f}")
    if avg_same > avg_intra > avg_cross:
        print(f"  ✅ 三组关系符合预期")
    elif avg_same > avg_cross > avg_intra:
        print(f"  ⚠️ 同作品风格基线 > 跨作品不同母题——风格元素贡献显著")
    else:
        print(f"  ❌ 关系不符合预期")

    for mn in sorted(set(r.pair_a.split("_")[0] for r in cross_same)):
        mp = [r for r in cross_same if r.pair_a.startswith(mn)]
        if mp:
            print(f"    {mn}: avg={sum(r.similarity for r in mp)/len(mp):.2f}")

    print(f"\n## 母题链重构")
    clusters = reconstruction.get("clusters", [])
    print(f"  LLM 自由聚类: {len(clusters)} 类")
    for c in clusters:
        print(f"    {c.get('motif_name', '?')}: {c.get('members', [])}")
        print(f"      理由: {c.get('reason', '')[:80]}")

    print(f"\n## 配对盲测（{len(blind_results)} 轮）")
    total = 0
    for i, r in enumerate(blind_results):
        acc = r.get("accuracy", 0) * 100
        total += acc
        print(f"  第 {i+1} 轮: {r.get('correct', 0)}/{r.get('total_pairs', 0)} = {acc:.0f}%")
    print(f"\n  平均准确率: {total / len(blind_results):.0f}%" if blind_results else "")


def main():
    print("=" * 60)
    print("p06 — 母题跨作品识别实验")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    fragments = collect_scene_fragments()
    print(f"\n共 {len(fragments)} 个场景片段（{len(CROSS_WORK_MOTIFS)} 个母题）")

    similarity_raw = cache_or_compute(
        RESULTS_DIR / "similarity_matrix.json",
        lambda: [vars(p) for p in cross_work_similarity_matrix(fragments)],
        "相似度矩阵",
    )
    similarity_results = _to_pairs(similarity_raw)

    reconstruction = cache_or_compute(
        RESULTS_DIR / "motif_chain_reconstruction.json",
        lambda: motif_chain_reconstruction(fragments),
        "母题链重构",
    )

    blind_results = []
    for r in range(3):
        result = cache_or_compute(
            RESULTS_DIR / f"blind_pairing_r{r+1}.json",
            lambda: blind_pairing(fragments),
            f"配对盲测第 {r+1} 轮",
        )
        blind_results.append(result)

    report(similarity_results, reconstruction, blind_results)

    # 完整段落版对照
    print("\n" + "=" * 40)
    print("完整段落版对照")
    full_fragments = load_full_paragraph_fragments()
    if full_fragments:
        full_reconstruction = cache_or_compute(
            RESULTS_DIR / "motif_chain_reconstruction_full.json",
            lambda: motif_chain_reconstruction(full_fragments),
            "母题链重构（完整段落）",
        )
        full_blind = []
        for r in range(3):
            result = cache_or_compute(
                RESULTS_DIR / f"blind_pairing_full_r{r+1}.json",
                lambda: blind_pairing(full_fragments),
                f"配对盲测第 {r+1} 轮",
            )
            full_blind.append(result)

        old_clusters = len(reconstruction.get("clusters", []))
        new_clusters = len(full_reconstruction.get("clusters", []))
        old_acc = sum(r.get("accuracy", 0) for r in blind_results) / len(blind_results) * 100
        new_acc = sum(r.get("accuracy", 0) for r in full_blind) / len(full_blind) * 100
        print(f"\n  类数: {old_clusters} → {new_clusters}")
        print(f"  配对准确率: {old_acc:.0f}% → {new_acc:.0f}%")
        print(f"  {'✅ 显著提升' if new_acc > 50 else '⚠️ 未超过随机基线'}")

    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
