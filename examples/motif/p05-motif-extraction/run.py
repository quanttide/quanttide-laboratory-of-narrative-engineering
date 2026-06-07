#!/usr/bin/env python3
"""
p05 — 母题可提取性实验

验证 LLM 能否从文本中提取母题，并与人工标注的 motif.yaml 对比。
"""
import json
import os
import sys
import random
from pathlib import Path
from collections import defaultdict

import requests
import yaml

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
    {"id": "U1", "series": "urban", "name": "深夜失眠",   "path": "职场言情/4_成稿/1_2_深夜失眠.md"},
    {"id": "U2", "series": "urban", "name": "便利店闲坐", "path": "职场言情/4_成稿/4_1_便利店闲坐.md"},
    {"id": "U3", "series": "urban", "name": "咖啡厅重逢", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md"},
    {"id": "U4", "series": "urban", "name": "酒吧表白",   "path": "职场言情/3_初稿/8_2_酒吧表白.md"},
    {"id": "U5", "series": "urban", "name": "书房陪伴",   "path": "职场言情/4_成稿/10_1_书房陪伴.md"},
    {"id": "C1", "series": "campus", "name": "第四章（论坛私信）", "path": "校园言情/3_初稿/4_第四章.md"},
    {"id": "C2", "series": "campus", "name": "第五章（危机公关）", "path": "校园言情/4_成稿/5_第五章.md"},
    {"id": "C3", "series": "campus", "name": "第十章（KTV表白）", "path": "校园言情/4_成稿/10_第十章.md"},
]


def read_article_text(path: str) -> str:
    full_path = FICTION_ROOT / path
    if not full_path.exists():
        raise FileNotFoundError(f"文件不存在: {full_path}")
    text = full_path.read_text("utf-8")
    lines = text.split("\n")
    body_lines = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body_lines).strip()


def load_motif_yaml(path: Path) -> dict:
    """加载 YAML，自动忽略 YAML 文档分隔符 `---`"""
    raw = path.read_text("utf-8")
    raw = "\n".join(line for line in raw.splitlines() if line.strip() and not line.strip().startswith("# ") and line.strip() != "---")
    return yaml.safe_load(raw)


def load_all_motif_ground_truth() -> dict:
    """加载三层 motif.yaml 作为 ground truth"""
    gt = {}

    shared = GALLERY_ROOT / "motif.yaml"
    if shared.exists():
        gt["shared"] = load_motif_yaml(shared)

    urban = GALLERY_ROOT / "urban-romance" / "motif.yaml"
    if urban.exists():
        gt["urban"] = load_motif_yaml(urban)

    campus = GALLERY_ROOT / "campus-romance" / "motif.yaml"
    if campus.exists():
        gt["campus"] = load_motif_yaml(campus)

    return gt


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


def extract_motifs(text: str, article_name: str) -> dict:
    """步骤 1：从单篇文章中提取母题"""
    sample = text[:3000]
    prompt = f"""分析下面名为《{article_name}》的文章，从中提取叙事母题（motif）。

母题定义：在叙事中反复出现的主题元素，包括具体意象、关系模式、行为习惯、
叙事惯例。母题与主题不同——主题是"说什么"（如"爱情"），母题是"怎么说"
（如"通过手势而非语言表达爱意"）。

要求：
- 提取 3-6 个母题
- 每个母题必须有来自原文的具体线索（2-3 条 evidence）
- weight 表示该母题在本文中的重要性（1-10）

输出格式（JSON）：
{{
  "motifs": [
    {{
      "title": "母题名（简短，2-6字）",
      "description": "一句话描述该母题在本文中的表现",
      "weight": 5,
      "evidence": ["原文引用1", "原文引用2"]
    }}
  ]
}}

文章内容：
{sample}"""

    raw = call_llm(prompt)
    return json.loads(clean_json(raw))


def extract_motifs_joint(texts: list[dict], series_name: str) -> dict:
    """步骤 2：从多篇合并文本中联合提取母题"""
    combined_parts = []
    for t in texts:
        combined_parts.append(f"--- 文章: {t['name']} ---\n{t['text'][:2000]}")
    combined = "\n\n".join(combined_parts)

    prompt = f"""以下是从《{series_name}》系列中抽取的多篇文章片段。请从这些合并文本中
提取该系列的共同叙事母题（motif）。

母题定义：在叙事中反复出现的主题元素，包括具体意象、关系模式、行为习惯、
叙事惯例。母题与主题不同——主题是"说什么"（如"爱情"），母题是"怎么说"
（如"通过手势而非语言表达爱意"）。

要求：
- 提取 4-6 个跨场景复现的母题
- 每个母题应有跨文章的证据支撑
- weight 表示该母题在整个系列中的重要性（1-10）

输出格式（JSON）：
{{
  "motifs": [
    {{
      "title": "母题名（简短，2-6字）",
      "description": "一句话描述该母题在系列中的表现",
      "weight": 5,
      "evidence": ["原文引用1（来自文章X）", "原文引用2（来自文章Y）"]
    }}
  ]
}}

{combined}"""

    raw = call_llm(prompt)
    return json.loads(clean_json(raw))


def semantic_similarity(desc_a: str, desc_b: str) -> float:
    """用 LLM 判断两个母题描述之间的语义相似度（0-1）。
    TODO: 优先使用 embedding 模型（如 text-embedding-3）代替 LLM 避免循环论证。
    """
    prompt = f"""判断以下两个母题描述的语义相似度，输出一个 0-1 之间的数字。

母题 A: {desc_a}
母题 B: {desc_b}

只输出数字，不要其他文字。"""
    try:
        raw = call_llm(prompt, "你是一个语义分析助手。只输出一个 0-1 的数字。")
        val = float(raw.strip())
        return max(0.0, min(1.0, val))
    except Exception:
        return 0.0


def compare_with_ground_truth(single_results: dict, joint_results: dict, gt: dict) -> dict:
    """步骤 3：与人工标注对比"""
    report = {}

    for level_name, level_data in [("urban", gt.get("urban", {})), ("campus", gt.get("campus", {}))]:
        gt_motifs = level_data.get("motifs", [])
        if not gt_motifs:
            continue

        gt_titles = {m["title"] for m in gt_motifs}
        gt_descs = {m["title"]: m.get("description", "") for m in gt_motifs}

        # 单篇覆盖率
        single_coverage = {}
        for art in ARTICLES:
            if art["series"] != level_name:
                continue
            aid = art["id"]
            extracted = single_results.get(aid, {}).get("motifs", [])
            matched = []
            for e in extracted:
                for g_title, g_desc in gt_descs.items():
                    sim = semantic_similarity(e.get("description", ""), g_desc)
                    if sim > 0.7:
                        matched.append((e["title"], g_title, sim))
                        break
            single_coverage[aid] = {
                "extracted_count": len(extracted),
                "matched_count": len(matched),
                "coverage": len(matched) / len(gt_motifs) if gt_motifs else 0,
                "matches": [{"extracted": m[0], "gt": m[1], "similarity": m[2]} for m in matched],
            }

        # 联合覆盖率
        joint = joint_results.get(level_name, {}).get("motifs", [])
        joint_matched = []
        for e in joint:
            for g_title, g_desc in gt_descs.items():
                sim = semantic_similarity(e.get("description", ""), g_desc)
                if sim > 0.7:
                    joint_matched.append((e["title"], g_title, sim))
                    break

        report[level_name] = {
            "single_coverage": single_coverage,
            "single_avg_coverage": sum(c["coverage"] for c in single_coverage.values()) / len(single_coverage)
            if single_coverage else 0,
            "joint_coverage": len(joint_matched) / len(gt_motifs) if gt_motifs else 0,
            "joint_matches": [{"extracted": m[0], "gt": m[1], "similarity": m[2]} for m in joint_matched],
            "gt_motif_count": len(gt_motifs),
        }

    return report


def blind_clustering(motif_descriptions: dict) -> list[dict]:
    """步骤 4：盲品归因——将母题描述按系列聚类"""
    items = []
    for aid, data in motif_descriptions.items():
        motifs = data.get("motifs", [])
        desc = " | ".join(m.get("description", "") for m in motifs[:4])
        items.append({"id": aid, "description": desc})

    random.shuffle(items)
    profiles = "\n\n".join(f"[文章 {it['id']}]\n{it['description']}" for it in items)

    prompt = f"""以下 8 篇文章的母题描述已去掉作者信息。请按母题相似度将它们分成 2 组。

输出格式（JSON）：
{{
  "groups": [
    {{"members": ["文章ID1", "文章ID3", ...], "reason": "共同母题特征"}},
    ...
  ]
}}

母题描述：
{profiles}"""

    raw = call_llm(prompt, "你是一个叙事学分析专家。只输出 JSON。")
    return json.loads(clean_json(raw))


def report(gt: dict, single_results: dict, joint_results: dict, comparison: dict, clusterings: list[dict]):
    print("\n" + "=" * 60)
    print("p05 分析报告：母题可提取性")
    print("=" * 60)

    series_map = {a["id"]: a["series"] for a in ARTICLES}
    series_names = {"urban": "都市言情", "campus": "校园言情"}

    # Ground truth
    print("\n## Ground Truth（人工标注）")
    for level in ["shared", "urban", "campus"]:
        data = gt.get(level, {})
        motifs = data.get("motifs", [])
        if motifs:
            names = ", ".join(m["title"] for m in motifs)
            print(f"  {level}: {len(motifs)} 个母题 — {names}")

    # 对比结果
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

        if c.get("joint_matches"):
            print(f"    联合提取匹配:")
            for m in c["joint_matches"]:
                print(f"      → {m['extracted']} ↔ {m['gt']} (sim={m['similarity']:.2f})")

    # 盲品归因
    print(f"\n## 盲品归因（{len(clusterings)} 次独立运行）")
    total_accuracy = 0
    for r_idx, clustering in enumerate(clusterings):
        groups = clustering.get("groups", [])
        correct = 0
        for g in groups:
            members = g["members"]
            series_in_group = [series_map.get(m, "?") for m in members]
            majority = max(set(series_in_group), key=series_in_group.count)
            correct += sum(1 for s in series_in_group if s == majority)

        acc = correct / len(ARTICLES) * 100 if ARTICLES else 0
        total_accuracy += acc
        print(f"  第 {r_idx+1} 轮: 同系列聚类率 {correct}/{len(ARTICLES)} = {acc:.0f}%")
        for g in groups:
            print(f"    {g['members']} — {g.get('reason', '')[:60]}")

    avg = total_accuracy / len(clusterings) if clusterings else 0
    print(f"\n  平均聚类率: {avg:.0f}%")


def main():
    print("=" * 60)
    print("p05 — 母题可提取性实验")
    print("=" * 60)

    RESULTS_DIR.mkdir(exist_ok=True)

    # 加载 ground truth
    print("\n加载 Gallery 母题标注...")
    gt = load_all_motif_ground_truth()
    for level, data in gt.items():
        n = len(data.get("motifs", []))
        print(f"  {level}: {n} 个母题")

    # 步骤 1: 单篇提取
    print("\n步骤 1: 单篇母题提取")
    single_results = {}
    for art in ARTICLES:
        cache_file = RESULTS_DIR / f"motif_{art['id']}.json"
        if cache_file.exists():
            single_results[art["id"]] = json.loads(cache_file.read_text("utf-8"))
            print(f"  {art['id']} {art['name']} ← 读取缓存")
            continue

        print(f"  {art['id']} {art['name']}...", end=" ", flush=True)
        try:
            text = read_article_text(art["path"])
            result = extract_motifs(text, art["name"])
            single_results[art["id"]] = result
            cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
            print(f"✓ ({len(result.get('motifs', []))} 个母题)")
        except Exception as e:
            print(f"✗ {e}")

    # 步骤 2: 多篇联合提取
    print("\n步骤 2: 多篇联合提取")
    joint_results = {}
    series_articles = defaultdict(list)
    for art in ARTICLES:
        try:
            text = read_article_text(art["path"])
            series_articles[art["series"]].append({"name": art["name"], "text": text})
        except Exception:
            continue

    for series, texts in series_articles.items():
        cache_file = RESULTS_DIR / f"motif_{series}_joint.json"
        if cache_file.exists():
            joint_results[series] = json.loads(cache_file.read_text("utf-8"))
            print(f"  {series} 联合 ← 读取缓存")
            continue

        series_name = "都市言情" if series == "urban" else "校园言情"
        print(f"  {series} 联合提取 ({len(texts)} 篇)...", end=" ", flush=True)
        try:
            result = extract_motifs_joint(texts, series_name)
            joint_results[series] = result
            cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
            print(f"✓ ({len(result.get('motifs', []))} 个母题)")
        except Exception as e:
            print(f"✗ {e}")

    # 步骤 3: 与人工标注对比
    print("\n步骤 3: 与人工标注对比")
    comparison = compare_with_ground_truth(single_results, joint_results, gt)

    # 步骤 4: 盲品归因（3 次独立运行）
    print("\n步骤 4: 盲品归因")
    clusterings = []
    for r in range(3):
        cache_file = RESULTS_DIR / f"blind_clustering_r{r+1}.json"
        if cache_file.exists():
            clusterings.append(json.loads(cache_file.read_text("utf-8")))
            print(f"  第 {r+1} 轮 ← 读取缓存")
            continue

        print(f"  第 {r+1} 轮...", end=" ", flush=True)
        try:
            result = blind_clustering(single_results)
            clusterings.append(result)
            cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
            print("✓")
        except Exception as e:
            print(f"✗ {e}")

    # 保存对比报告
    (RESULTS_DIR / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), "utf-8"
    )

    report(gt, single_results, joint_results, comparison, clusterings)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
