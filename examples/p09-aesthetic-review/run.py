#!/usr/bin/env python3
"""
p09 — 复刻作者审美评审实验

验证 LLM 能否内化 style.yaml 中的审美框架，以该审美标准评审新场景。
"""
import json
import os
import sys
from pathlib import Path
from collections import defaultdict

import requests
import yaml

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[4]
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

ARTICLES = [
    {"id": "T1", "series": "urban", "path": "职场言情/4_成稿/1_2_深夜失眠.md", "type": "成稿"},
    {"id": "T2", "series": "urban", "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md", "type": "初稿"},
    {"id": "T3", "series": "urban", "path": "职场言情/4_成稿/10_1_书房陪伴.md", "type": "成稿"},
    {"id": "T4", "series": "urban", "path": "职场言情/3_初稿/赏雪谈心.md", "type": "盲测初稿"},
    {"id": "T5", "series": "campus", "path": "校园言情/4_成稿/5_第五章.md", "type": "跨系列"},
]

GROUPS = [
    {"id": "aesthetic", "label": "作者审美", "use_style": True, "use_samples": True, "n_samples": 3},
    {"id": "general", "label": "通用评审", "use_style": False, "use_samples": False, "n_samples": 0},
    {"id": "blind3", "label": "盲审(3)", "use_style": False, "use_samples": True, "n_samples": 3},
    {"id": "blind6", "label": "盲审(6)", "use_style": False, "use_samples": True, "n_samples": 6},
]


def call_llm(prompt: str, system: str = "你是一个专业的文学评审。只输出 JSON。", temperature: float = 0.3) -> str:
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


def build_style_prompt(style: dict, samples_dir: Path, n_samples: int = 3, include_dimensions: bool = True) -> str:
    parts = []
    if include_dimensions:
        dims = style.get("dimensions", [])
        parts.append(f"风格框架「{style.get('title','')}」——{style.get('description','')}")
        parts.append(f"共 {len(dims)} 个评价维度：\n")
        for d in dims:
            parts.append(f"【{d['title']}】(confidence={d.get('confidence','?')})")
            parts.append(f"  {d.get('description','')}")
            if d.get("clues"):
                parts.append(f"  线索: {'; '.join(d['clues'][:2])}")
            if d.get("tensions"):
                parts.append(f"  内部张力: {'; '.join(d['tensions'][:2])}")
            parts.append("")

    if n_samples > 0 and samples_dir.exists():
        sample_files = sorted(samples_dir.glob("sample*.md"))[:n_samples]
        parts.append(f"\n参考场景（{len(sample_files)} 篇）：")
        for sf in sample_files:
            sample_text = sf.read_text("utf-8")[:800]
            parts.append(f"\n--- {sf.stem} ---\n{sample_text}\n")

    return "\n".join(parts)


def aesthetic_review(text: str, article_name: str, style_prompt: str) -> dict:
    sample = text[:2500]
    prompt = f"""{style_prompt}

请用以上审美框架评审下面名为《{article_name}》的场景。
对每个维度评分（1-10），附原文证据、反例（如有）、一句话理由。

输出 JSON：
{{"dimension_scores": [
  {{"dimension": "维度名", "score": 8, "evidence": ["原文引用"], "tension": null, "note": "一句话理由"}}
]}}

场景文本：{sample}"""

    raw = call_llm(prompt, temperature=0.0)
    result = json.loads(clean_json(raw))

    # 检测独立发现的 tensions
    found_tensions = []
    for ds in result.get("dimension_scores", []):
        if ds.get("tension"):
            found_tensions.append({"dimension": ds["dimension"], "tension": ds["tension"]})
    result["_found_tensions"] = found_tensions

    return result


def compute_alignment(scores_by_article: dict, style: dict) -> dict:
    dims = style.get("dimensions", [])
    dim_conf = {d["title"]: d.get("confidence", 0.5) for d in dims}
    sorted_dims = sorted(dim_conf, key=dim_conf.get, reverse=True)
    top3_dims = sorted_dims[:3]

    direction_match = 0
    rho_parts = []
    for aid, result in scores_by_article.items():
        scores = {ds["dimension"]: ds["score"] for ds in result.get("dimension_scores", [])}
        if len(scores) < 3:
            continue
        sorted_scores = sorted(scores, key=scores.get, reverse=True)
        top3_scores = sorted_scores[:3]
        match = sum(1 for d in top3_scores if d in top3_dims)
        if match >= 2:
            direction_match += 1

        # ρ 近似
        conf_vals = [dim_conf.get(d, 0.5) for d in scores]
        score_vals = [scores[d] for d in scores]
        n = len(conf_vals)
        if n > 2 and len(set(score_vals)) > 1:
            try:
                # Manual Spearman's ρ (scipy not available)
                def rankdata(vals):
                    sorted_vals = sorted((v, i) for i, v in enumerate(vals))
                    ranks = [0] * len(vals)
                    i = 0
                    while i < len(sorted_vals):
                        j = i
                        while j < len(sorted_vals) and sorted_vals[j][0] == sorted_vals[i][0]:
                            j += 1
                        avg_rank = (i + j - 1) / 2 + 1
                        for k in range(i, j):
                            ranks[sorted_vals[k][1]] = avg_rank
                        i = j
                    return ranks
                rank_c = rankdata(conf_vals)
                rank_s = rankdata(score_vals)
                n = len(rank_c)
                d2 = sum((rc - rs) ** 2 for rc, rs in zip(rank_c, rank_s))
                rho = 1 - (6 * d2) / (n * (n * n - 1))
                rho_parts.append(rho)
            except Exception:
                pass

    avg_rho = sum(rho_parts) / len(rho_parts) if rho_parts else 0

    all_tensions = []
    for aid, result in scores_by_article.items():
        all_tensions.extend(result.get("_found_tensions", []))

    return {"direction_match_rate": direction_match_rate / len(scores_by_article) if scores_by_article else 0,
            "avg_rho": avg_rho, "found_tensions": all_tensions}


def check_draft_gradient(scores_by_article: dict) -> dict:
    draft_scores = {}
    final_scores = {}
    for aid, result in scores_by_article.items():
        art = next(a for a in ARTICLES if a["id"] == aid)
        dims = {ds["dimension"]: ds["score"] for ds in result.get("dimension_scores", [])}
        if art["type"] in ("初稿", "盲测初稿"):
            for d, s in dims.items():
                draft_scores.setdefault(d, []).append(s)
        else:
            for d, s in dims.items():
                final_scores.setdefault(d, []).append(s)

    gradient = {}
    for d in draft_scores:
        draft_avg = sum(draft_scores[d]) / len(draft_scores[d])
        final_avg = sum(final_scores.get(d, [0])) / max(1, len(final_scores.get(d, [])))
        gradient[d] = {"draft_avg": draft_avg, "final_avg": final_avg, "diff": draft_avg - final_avg}

    return gradient


def main():
    print("=" * 60)
    print("p09 — 复刻作者审美评审实验")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    urban_style = load_yaml(GALLERY_ROOT / "urban-romance" / "style.yaml")
    campus_style = load_yaml(GALLERY_ROOT / "campus-romance" / "style.yaml")
    urban_samples = GALLERY_ROOT / "urban-romance" / "samples"
    campus_samples = GALLERY_ROOT / "campus-romance" / "samples"

    all_scores = {}

    for group in GROUPS:
        print(f"\n{'='*40}")
        print(f"组: {group['label']}")
        use_style = group["use_style"]
        n = group["n_samples"]

        if use_style:
            print(f"  含维度定义 + {n} 篇 samples")
        elif n > 0:
            print(f"  仅 {n} 篇 samples（无维度定义）")
        else:
            print("  无约束（通用评审）")

        group_scores = {}
        for art in ARTICLES:
            if art["series"] != "urban":
                continue
            aid = art["id"]

            cache_file = RESULTS_DIR / f"scores_{group['id']}_{aid}.json"
            if cache_file.exists():
                result = json.loads(cache_file.read_text("utf-8"))
                group_scores[aid] = result
                print(f"  {aid} {art['type']} ← 读取缓存")
                continue

            print(f"  {aid} {art['type']}...", end=" ", flush=True)
            text = read_article_text(art["path"])
            style_prompt = build_style_prompt(urban_style, urban_samples, n_samples=n, include_dimensions=use_style)
            result = aesthetic_review(text, art["id"], style_prompt)
            group_scores[aid] = result
            cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")

            dims = result.get("dimension_scores", [])
            avg = sum(d["score"] for d in dims) / len(dims) if dims else 0
            tensions_count = len(result.get("_found_tensions", []))
            print(f"✓ avg={avg:.1f} tensions={tensions_count}")

        all_scores[group["id"]] = group_scores

    # Cross-series (T5)
    print(f"\n{'='*40}")
    print("跨系列: 都市审美评校园 T5")
    art = next(a for a in ARTICLES if a["id"] == "T5")
    cache_urban = RESULTS_DIR / "scores_cross_urban_T5.json"
    cache_campus = RESULTS_DIR / "scores_cross_campus_T5.json"

    text = read_article_text(art["path"])

    if cache_urban.exists():
        cs_urban = json.loads(cache_urban.read_text("utf-8"))
        print("  都市审美评 T5 ← 读取缓存")
    else:
        prompt = build_style_prompt(urban_style, urban_samples, n_samples=3, include_dimensions=True)
        cs_urban = aesthetic_review(text, "T5", prompt)
        cache_urban.write_text(json.dumps(cs_urban, ensure_ascii=False, indent=2), "utf-8")
        print(f"  都市审美评 T5 ✓")

    if cache_campus.exists():
        cs_campus = json.loads(cache_campus.read_text("utf-8"))
        print("  校园审美评 T5 ← 读取缓存")
    else:
        prompt = build_style_prompt(campus_style, campus_samples, n_samples=2, include_dimensions=True)
        cs_campus = aesthetic_review(text, "T5", prompt)
        cache_campus.write_text(json.dumps(cs_campus, ensure_ascii=False, indent=2), "utf-8")
        print(f"  校园审美评 T5 ✓")

    # Genre fit
    genre_fits = {
        "总体风格定位": 1, "叙事视角": 2, "时间结构": 1, "语言风格": 2, "情感表达": 1,
        "细节美学": 3, "人物塑造": 2, "叙事节奏": 2, "流行文化嵌入": 3, "整体美学": 3,
    }

    cross_diffs = []
    for du in cs_urban.get("dimension_scores", []):
        dc = next((d for d in cs_campus.get("dimension_scores", []) if d["dimension"] == du["dimension"]), None)
        if dc:
            diff = abs(du["score"] - dc["score"])
            gf = genre_fits.get(du["dimension"], 2)
            cross_diffs.append({"dimension": du["dimension"], "urban_score": du["score"],
                                "campus_score": dc["score"], "diff": diff, "genre_fit": gf})

    # Report
    print("\n" + "=" * 60)
    print("p09 分析报告")
    print("=" * 60)

    for group in GROUPS:
        if group["id"] not in all_scores:
            continue
        scores = all_scores[group["id"]]
        print(f"\n## {group['label']}")
        alignment = compute_alignment(scores, urban_style)
        print(f"  方向匹配率: {alignment['direction_match_rate']*100:.0f}%")
        print(f"  平均 ρ: {alignment['avg_rho']:.3f}")
        tensions = alignment["found_tensions"]
        print(f"  独立发现 tension: {len(tensions)} 个")
        for c in tensions:
            print(f"    [{c.get('dimension','?')}] {c.get('tension','')[:80]}")

        gradient = check_draft_gradient(scores)
        print(f"  初稿→成稿梯度:")
        for d, g in sorted(gradient.items()):
            arrow = "↑" if g["diff"] > 0 else "↓"
            print(f"    {d}: 初稿={g['draft_avg']:.1f} 成稿={g['final_avg']:.1f} ({arrow} {abs(g['diff']):.1f})")

    # Cross-series
    print(f"\n## 跨系列转移 (都市审美 vs 校园审美评 T5)")
    gf3 = [d for d in cross_diffs if d["genre_fit"] == 3]
    gf1 = [d for d in cross_diffs if d["genre_fit"] == 1]
    if gf3:
        avg3 = sum(d["diff"] for d in gf3) / len(gf3)
        print(f"  genre_fit=3 维度平均分差: {avg3:.1f}")
    if gf1:
        avg1 = sum(d["diff"] for d in gf1) / len(gf1)
        print(f"  genre_fit=1 维度平均分差: {avg1:.1f}")
    for d in cross_diffs:
        print(f"    [{d['genre_fit']}] {d['dimension']}: 都市={d['urban_score']} 校园={d['campus_score']} diff={d['diff']}")

    # Ablation summary
    print(f"\n## 消融对比")
    for g in ["aesthetic", "blind6", "blind3", "general"]:
        if g in all_scores:
            a = compute_alignment(all_scores[g], urban_style)
            label = next(gr["label"] for gr in GROUPS if gr["id"] == g)
            print(f"  {label}: direction_match={a['direction_match_rate']*100:.0f}% ρ={a['avg_rho']:.3f} tensions={len(a['found_tensions'])}")

    # Save full report
    report = {
        "scores": all_scores,
        "cross_series": {"urban": cs_urban, "campus": cs_campus, "diffs": cross_diffs},
    }
    (RESULTS_DIR / "full_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
