#!/usr/bin/env python3
"""
p06 — 母题跨作品识别实验

验证 LLM 能否识别同一母题在不同作品中的不同变体，建立跨作品关联。
依赖 p05 步骤 1 的产物（单篇母题提取结果）。
"""
import json
import os
import sys
import random
from pathlib import Path

import requests
import yaml

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[4]
P05_RESULTS = REPO_ROOT / "examples" / "default" / "examples" / "p05-motif-extraction" / "results"
GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

# 跨作品母题镜像对（来自 gallery fiction/motif.yaml）
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


def call_llm(prompt: str, system: str = "你是一个专业的叙事学分析助手。只输出 JSON。") -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()


def collect_scene_fragments() -> list[dict]:
    """步骤 1：从 p05 产物收集场景片段"""
    fragments = []

    for m in CROSS_WORK_MOTIFS:
        for v in m["variants"]:
            fragments.append({
                "motif": m["motif"],
                "series": v["series"],
                "scene": v["scene"],
                "description": v["desc"],
            })

    return fragments


def cross_work_similarity_matrix(fragments: list[dict]) -> list[dict]:
    """步骤 2：跨作品相似度矩阵
    对 14 个片段两两配对（91 对），用 LLM 判定是否体现同一母题。
    注意：本实现对所有对做 LLM 判定。
    生产环境建议：先做 embedding 预筛选，仅对模糊边界对（cos 0.5-0.8）做 LLM 判定。
    """
    pairs = []
    for i in range(len(fragments)):
        for j in range(i + 1, len(fragments)):
            a, b = fragments[i], fragments[j]
            if a["series"] == b["series"]:
                continue  # 只看跨作品对
            if a["motif"] == b["motif"]:
                continue  # 同一母题内的对，用 LLM 直接判定
            # 跨作品且不同母题的对
            pairs.append((a, b))

    # 同母题对也在列表中
    same_motif_pairs = []
    for i in range(len(fragments)):
        for j in range(i + 1, len(fragments)):
            a, b = fragments[i], fragments[j]
            if a["series"] != b["series"] and a["motif"] == b["motif"]:
                same_motif_pairs.append((a, b))

    all_pairs = same_motif_pairs + pairs

    results = []
    for a, b in all_pairs:
        prompt = f"""判断以下两个来自不同小说的场景描述是否体现了同一叙事母题（motif）。

场景 A：
  作品: {'都市言情' if a['series'] == 'urban' else '校园言情'}
  母题: {a['motif']}
  描述: {a['description']}

场景 B：
  作品: {'都市言情' if b['series'] == 'urban' else '校园言情'}
  母题: {b['motif']}
  描述: {b['description']}

输出格式（JSON）：
{{"same_motif": true/false, "similarity": 0.0-1.0, "shared_pattern": "共同结构（如有）", "reasoning": "判断理由"}}"""

        try:
            raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
            result = json.loads(clean_json(raw))
            result["pair_a"] = f"{a['motif']}_{a['series']}_{a['scene']}"
            result["pair_b"] = f"{b['motif']}_{b['series']}_{b['scene']}"
            result["same_gt_motif"] = a["motif"] == b["motif"]
            results.append(result)
        except Exception as e:
            print(f"    ✗ {a['scene']} vs {b['scene']}: {e}")

    return results


def motif_chain_reconstruction(fragments: list[dict]) -> dict:
    """步骤 3：母题链重构——LLM 自由聚类 14 个片段"""
    descriptions = "\n".join(
        f"[{f['motif']}] {f['series']}-{f['scene']}: {f['description']}"
        for f in fragments
    )

    prompt = f"""以下 14 个来自两部小说的场景片段。请将它们按体现的母题分组成若干类。
每个类内部应有相同的叙事模式或主题结构。

输出格式（JSON）：
{{
  "clusters": [
    {{"motif_name": "你自行为这个母题命名", "members": ["场景标识A", "场景标识D", ...], "reason": "为什么这些属于同一母题"}}
  ]
}}

场景片段：
{descriptions}"""

    try:
        raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
        return json.loads(clean_json(raw))
    except Exception as e:
        print(f"    ✗ {e}")
        return {"clusters": []}


def blind_pairing(fragments: list[dict], n_motifs: int = 4) -> dict:
    """步骤 4：配对盲测
    随机选 4 个母题，每个取都市和校园变体（共 8 个），
    打乱后让 LLM 两两配对。
    """
    # 选 4 个不同的母题
    unique_motifs = list(dict.fromkeys(f["motif"] for f in fragments))
    selected = random.sample(unique_motifs, min(n_motifs, len(unique_motifs)))

    # 为每个选中的母题，取都市和校园变体各 1 个
    test_items = []
    for motif in selected:
        urban_variants = [f for f in fragments if f["motif"] == motif and f["series"] == "urban"]
        campus_variants = [f for f in fragments if f["motif"] == motif and f["series"] == "campus"]
        if urban_variants and campus_variants:
            test_items.append(random.choice(urban_variants))
            test_items.append(random.choice(campus_variants))

    random.shuffle(test_items)

    items_text = "\n".join(
        f"[{i+1}] 系列: {'都市' if f['series']=='urban' else '校园'}\n    描述: {f['description']}"
        for i, f in enumerate(test_items)
    )

    prompt = f"""以下 8 个场景描述来自两部不同的小说。请将它们两两配对——每组 2 个场景
应当体现同一叙事母题（一个来自都市言情，一个来自校园言情）。

输出格式（JSON）：
{{
  "pairs": [
    {{"pair": [1, 5], "motif_reason": "它们共享了什么母题"}},
    ...
  ]
}}

场景描述：
{items_text}"""

    try:
        raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
        result = json.loads(clean_json(raw))
        # 计算准确率
        correct = 0
        for pair in result.get("pairs", []):
            ids = pair["pair"]
            s1 = test_items[ids[0] - 1]["motif"]
            s2 = test_items[ids[1] - 1]["motif"]
            if s1 == s2:
                correct += 1
        result["accuracy"] = correct / len(result.get("pairs", [])) if result.get("pairs") else 0
        result["total_pairs"] = len(result.get("pairs", []))
        result["correct"] = correct
        result["test_items"] = [
            {"id": i + 1, "motif": f["motif"], "series": f["series"]}
            for i, f in enumerate(test_items)
        ]
        return result
    except Exception as e:
        print(f"    ✗ {e}")
        return {"accuracy": 0, "error": str(e)}


def report(similarity_results: list[dict], reconstruction: dict, blind_results: list[dict]):
    print("\n" + "=" * 60)
    print("p06 分析报告：母题跨作品识别")
    print("=" * 60)

    # 相似度矩阵
    print("\n## 跨作品相似度")
    same_motif_pairs = [r for r in similarity_results if r.get("same_gt_motif")]
    diff_motif_pairs = [r for r in similarity_results if not r.get("same_gt_motif")]

    same_motif_sim = [r["similarity"] for r in same_motif_pairs]
    diff_motif_sim = [r["similarity"] for r in diff_motif_pairs]

    avg_same = sum(same_motif_sim) / len(same_motif_sim) if same_motif_sim else 0
    avg_diff = sum(diff_motif_sim) / len(diff_motif_sim) if diff_motif_sim else 0

    print(f"  同母题对平均相似度: {avg_same:.3f} ({len(same_motif_pairs)} 对)")
    print(f"  不同母题对平均相似度: {avg_diff:.3f} ({len(diff_motif_pairs)} 对)")
    print(f"  差异: {avg_same - avg_diff:+.3f}")

    # 逐个母题
    motif_names = sorted(set(r.get("pair_a", "").split("_")[0] for r in same_motif_pairs))
    for mn in motif_names:
        m_pairs = [r for r in same_motif_pairs if r.get("pair_a", "").startswith(mn)]
        if m_pairs:
            avg = sum(r["similarity"] for r in m_pairs) / len(m_pairs)
            print(f"    {mn}: avg={avg:.2f}")

    # 母题链重构
    print("\n## 母题链重构")
    clusters = reconstruction.get("clusters", [])
    print(f"  LLM 自由聚类: {len(clusters)} 类")
    for c in clusters:
        print(f"    {c.get('motif_name', '?')}: {c.get('members', [])}")
        print(f"      理由: {c.get('reason', '')[:80]}")

    # 配对盲测
    print(f"\n## 配对盲测（{len(blind_results)} 轮）")
    total_acc = 0
    for i, r in enumerate(blind_results):
        acc = r.get("accuracy", 0) * 100
        total_acc += acc
        print(f"  第 {i+1} 轮: {r.get('correct', 0)}/{r.get('total_pairs', 0)} = {acc:.0f}%")
        for p in r.get("pairs", []):
            print(f"    {p['pair']} → {p.get('motif_reason', '')[:60]}")
    avg = total_acc / len(blind_results) if blind_results else 0
    print(f"\n  平均准确率: {avg:.0f}%（随机基线 25%）")


def main():
    print("=" * 60)
    print("p06 — 母题跨作品识别实验")
    print("=" * 60)

    RESULTS_DIR.mkdir(exist_ok=True)

    # 步骤 1: 收集场景片段
    print("\n步骤 1: 收集场景片段")
    fragments = collect_scene_fragments()
    print(f"  共 {len(fragments)} 个场景片段（{len(CROSS_WORK_MOTIFS)} 个母题）")

    # 步骤 2: 跨作品相似度矩阵
    print("\n步骤 2: 跨作品相似度矩阵")
    cache_file = RESULTS_DIR / "similarity_matrix.json"
    if cache_file.exists():
        similarity_results = json.loads(cache_file.read_text("utf-8"))
        print(f"  ← 读取缓存 ({len(similarity_results)} 对)")
    else:
        print(f"  计算中...")
        similarity_results = cross_work_similarity_matrix(fragments)
        cache_file.write_text(json.dumps(similarity_results, ensure_ascii=False, indent=2), "utf-8")
        print(f"  ✓ ({len(similarity_results)} 对)")

    # 步骤 3: 母题链重构
    print("\n步骤 3: 母题链重构")
    cache_file = RESULTS_DIR / "motif_chain_reconstruction.json"
    if cache_file.exists():
        reconstruction = json.loads(cache_file.read_text("utf-8"))
        print(f"  ← 读取缓存 ({len(reconstruction.get('clusters', []))} 类)")
    else:
        print("  重构中...")
        reconstruction = motif_chain_reconstruction(fragments)
        cache_file.write_text(json.dumps(reconstruction, ensure_ascii=False, indent=2), "utf-8")
        print(f"  ✓ ({len(reconstruction.get('clusters', []))} 类)")

    # 步骤 4: 配对盲测（3 轮）
    print("\n步骤 4: 配对盲测")
    blind_results = []
    for r in range(3):
        cache_file = RESULTS_DIR / f"blind_pairing_r{r+1}.json"
        if cache_file.exists():
            blind_results.append(json.loads(cache_file.read_text("utf-8")))
            print(f"  第 {r+1} 轮 ← 读取缓存")
            continue

        print(f"  第 {r+1} 轮...", end=" ", flush=True)
        result = blind_pairing(fragments)
        blind_results.append(result)
        cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
        print(f"✓ ({result.get('correct', 0)}/{result.get('total_pairs', 0)})")

    report(similarity_results, reconstruction, blind_results)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
