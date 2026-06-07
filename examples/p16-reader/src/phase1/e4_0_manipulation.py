"""E4-0 — Prompt 操控性检验

验证 LLM 能否理解并区分不同读者画像。
方法：画像 prompt → LLM 生成读者自述 → embedding 聚类 → 轮廓系数。
"""
import sys
from pathlib import Path

import numpy as np

# ── git root ──────────────────────────────────────────────
GIT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GIT_ROOT))

from packages.llm import call_llm
from packages.io import save_json, load_json


def load_profiles(data_dir: Path) -> list[dict]:
    return load_json(data_dir / "profiles.json")


def _run_try(data_dir: Path, results_dir: Path, prompt_type: str, temperature: float) -> dict | None:
    """用指定 prompt 类型跑一轮 E4-0。通过返回 result，不通过返回 None。"""
    from .prompt_templates import (
        build_reader_self_description,
        build_self_description_behavioral_anchor,
    )

    profiles = load_profiles(data_dir)
    builder = (
        build_reader_self_description
        if prompt_type == "numeric"
        else build_self_description_behavioral_anchor
    )

    tag = f"e4-0_raw_{prompt_type}.json"
    cache = results_dir / tag
    if cache.exists():
        raw = load_json(cache)
        print(f"  ← 读取缓存 {tag}")
    else:
        raw = []
        for p in profiles:
            print(f"  {p['id']} ({p['label']}) [{prompt_type}]...")
            for i in range(3):
                prompt = builder(p)
                text = call_llm(prompt, system="请用中文回答，不要输出 JSON。", temperature=temperature)
                raw.append({"profile": p["id"], "call": i, "prompt_type": prompt_type, "text": text})
        save_json(cache, raw)
        print(f"  已保存 {tag}")

    return _analyze(raw, results_dir, prompt_type)


def _analyze(raw: list[dict], results_dir: Path, prompt_type: str) -> dict:
    """对一批读者自述做 embedding 聚类分析，返回 result dict。"""
    from sklearn.metrics import silhouette_score
    from sklearn.metrics.pairwise import cosine_distances
    from fastembed import TextEmbedding

    texts = [r["text"] for r in raw]
    labels = [r["profile"] for r in raw]
    n_total = len(texts)
    profile_ids = sorted(set(labels))

    print("  生成 embedding（fastembed BAAI/bge-small-zh-v1.5）...")
    model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    embeddings = np.array(list(model.embed(texts)))
    print(f"    shape: {embeddings.shape}")

    # ── 指标 1：轮廓系数 ──
    sil = silhouette_score(embeddings, labels)
    print(f"   轮廓系数: {sil:.4f}  (≥0.25)")

    # ── 指标 2：P0 vs P1 距离 ──
    dist_matrix = cosine_distances(embeddings)
    p0_idx = [i for i, l in enumerate(labels) if l == "P0"]
    p1_idx = [i for i, l in enumerate(labels) if l == "P1"]
    p0_p1_dist = float(np.mean([dist_matrix[i, j] for i in p0_idx for j in p1_idx]))
    print(f"   P0 vs P1: {p0_p1_dist:.4f}  (≥0.1)")

    # ── 指标 3：最近邻一致性 ──
    np.fill_diagonal(dist_matrix, np.inf)  # 排除自身
    nn_label = [labels[np.argmin(dist_matrix[i])] for i in range(n_total)]
    nn_hits = sum(1 for i in range(n_total) if nn_label[i] == labels[i])
    nn_accuracy = nn_hits / n_total
    baseline = 1.0 / len(profile_ids)
    print(f"   最近邻一致性: {nn_accuracy:.1%} ({nn_hits}/{n_total})  (基线 {baseline:.0%}, 标准 ≥30%)")

    # ── 类内距离（辅助诊断） ──
    within = {}
    for pid in profile_ids:
        idx = [i for i, l in enumerate(labels) if l == pid]
        if len(idx) > 1:
            d = np.mean([dist_matrix[i, j] for i in idx for j in idx if i != j])
            within[pid] = round(float(d), 4)
    print(f"   类内距离: {within}")

    # ── 门控判定 ──
    passed_sil = sil >= 0.25
    passed_dist = p0_p1_dist >= 0.1
    passed_nn = nn_accuracy >= 0.30
    overall = passed_sil and passed_dist and passed_nn

    result = {
        "prompt_type": prompt_type,
        "silhouette_score": round(float(sil), 4),
        "silhouette_pass": bool(passed_sil),
        "p0_vs_p1_cosine_dist": round(p0_p1_dist, 4),
        "p0_vs_p1_pass": bool(passed_dist),
        "nn_accuracy": round(float(nn_accuracy), 4),
        "nn_baseline": round(float(baseline), 4),
        "nn_pass": bool(passed_nn),
        "within_profile_distances": within,
        "overall_pass": bool(overall),
    }
    save_json(results_dir / f"e4-0_result_{prompt_type}.json", result)

    print(f"   通过: {'✅' if overall else '❌'}")
    return result


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-0 — Prompt 操控性检验")
    print("=" * 60)

    profiles = load_profiles(data_dir)
    print(f"已加载 {len(profiles)} 个画像: {[p['id'] for p in profiles]}")

    # 第一轮：数值 prompt
    print("\n── 第一轮：数值 prompt ──")
    r1 = _run_try(data_dir, results_dir, "numeric", temperature=0.7)

    if r1["overall_pass"]:
        print("\n  ✅ 数值 prompt 通过 → 进入 E4-1")
        save_json(results_dir / "e4-0_result.json", r1)
        return r1

    # 第二轮：行为锚定 prompt（降低 temperature 提高稳定性）
    print("\n── 第二轮：行为锚定 prompt ──")
    r2 = _run_try(data_dir, results_dir, "behavioral_anchor", temperature=0.3)

    if r2["overall_pass"]:
        print("\n  ✅ 行为锚定 prompt 通过 → 进入 E4-1")
        save_json(results_dir / "e4-0_result.json", r2)
        return r2

    # 两轮均不通过 → 项目终止
    print("\n  ❌ 两轮均不通过 → 项目终止")
    save_json(results_dir / "e4-0_result.json", r2)
    return r2


if __name__ == "__main__":
    # 独立运行：uv run python -m src.phase1.e4_0_manipulation
    _root = Path(__file__).resolve().parents[3]
    _data = _root / "data" / "input"
    _results = _root / "data" / "output"
    run(_data, _results)
