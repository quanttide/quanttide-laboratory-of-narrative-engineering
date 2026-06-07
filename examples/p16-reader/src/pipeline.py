"""E4-5 — 端到端集成验证

全链路：层1（LLM标注认知负荷）→ 层2（E4-4权重加权预测评分）→ 层3（直接prompt评价对照）
在 4 篇未见文本上运行，验证全链路输出稳定性、与直接 prompt 一致性、画像分化能力。
"""
import sys, json
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from packages.io import save_json, load_json
from packages.stats import icc, spearman_rho

FICTION_ROOT = REPO_ROOT / "assets" / "fiction"

# 4 篇未见文本（非 Phase I 用过的 6 篇）
TEXTS = {
    "2.1": "职场言情/4_成稿/2_1_展会再遇.md",
    "4.2": "职场言情/4_成稿/4_2_夜市约会.md",
    "6.2": "职场言情/4_成稿/6_2_海边散步.md",
    "8.2": "职场言情/4_成稿/8_2_酒吧表白.md",
}

PROFILES = ["P1", "P2", "P3", "P4", "P5"]
N_CALLS = 3
TEMPERATURE = 0.3


def _read_text(path: str) -> str:
    full = FICTION_ROOT / path
    text = full.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-5 — 端到端集成验证")
    print("=" * 60)

    # 加载画像定义
    profiles = load_json(data_dir / "profiles.json")
    profiles = [p for p in profiles if p["id"] != "P0"]
    profile_map = {p["id"]: p for p in profiles}

    # 加载 E4-4 权重
    weights = load_json(results_dir / "e4-4_summary.json")["weight_ratios"]
    # weights: {"P1": [w_inference, w_working_memory, w_backtracking], ...}
    WEIGHT_FIELDS = ["inference_demand", "working_memory", "backtracking"]

    # ── 层1：LLM 标注认知负荷（复用 layer1 模块）──
    print("\n── 层1：LLM 标注认知负荷 ──")
    from src.layer1.inference_demand import inference_demand
    from src.layer1.working_memory import working_memory_load
    from src.layer1.backtracking import backtracking_prediction
    from src.layer1.situation_model import situation_model
    import re

    l1_cache = results_dir / "e4-5_l1_cache.json"
    if l1_cache.exists():
        l1_results = load_json(l1_cache)
        print("← 读取层1缓存")
    else:
        l1_results = {}
        for tid, path in TEXTS.items():
            text = _read_text(path)
            sents = re.split(r'[。！？\n]+', text)
            sents = [s.strip() for s in sents if len(s.strip()) > 2]
            print(f"  {tid}: {len(sents)} 句 → LLM 标注中...")
            l1_results[tid] = {
                "inference_demand": inference_demand(sents),
                "working_memory": working_memory_load(sents),
                "backtracking": backtracking_prediction(sents),
                "n_sentences": len(sents),
            }
            save_json(l1_cache, l1_results)
            print(f"    → 已保存进度")
        print("  层1标注完成")

    # ── 层2：权重加权预测评分 ──
    print("\n── 层2：权重加权预测 ──")
    pipe_pred = {}  # {tid: {pid: score}}
    for tid in TEXTS:
        l1 = l1_results[tid]
        # 对每个画像，计算加权预测：权重 · 层1指标均值
        pipe_pred[tid] = {}
        for pid in PROFILES:
            w = np.array(weights[pid])  # [w_inf, w_wm, w_bt]
            # 层1各指标均值
            x = np.array([float(np.mean(l1[f])) for f in WEIGHT_FIELDS])
            score = float(np.dot(w, x))  # 加权和
            pipe_pred[tid][pid] = round(score, 4)

    # ── 层3：直接 prompt 评价 ──
    print("\n── 层3：直接 prompt 评价 ──")
    from src.phase1.prompt_templates import build_evaluation_prompt

    l3_cache = results_dir / "e4-5_l3_cache.json"
    if l3_cache.exists():
        direct_rows = load_json(l3_cache)
        print("← 读取直接评价缓存")
    else:
        direct_rows = []
        for pid in PROFILES:
            prof = profile_map[pid]
            for tid, path in TEXTS.items():
                text = _read_text(path)
                for c in range(N_CALLS):
                    prompt = build_evaluation_prompt(prof, text)
                    from packages.llm import call_llm
                    raw = call_llm(prompt, temperature=TEMPERATURE)
                    try:
                        resp = json.loads(raw)
                    except json.JSONDecodeError:
                        print(f"    {pid}×{tid} call {c}: JSON 解析失败")
                        continue
                    resp["profile"] = pid
                    resp["text_id"] = tid
                    resp["call"] = c
                    direct_rows.append(resp)
                    print(f"  {pid}×{tid} call {c}: 文笔={resp.get('writing_quality','?')}")
                save_json(l3_cache, direct_rows)
                print(f"    → 已保存进度")
        print("  直接评价完成")

    # ── 验证 ──
    print("\n── 验证 ──")

    # 1. 全链路稳定性（ICC）：同一 text × profile 的层级2预测（跨call无变化，所以用层3）
    # 直接评价的 call 间 ICC
    icc_vals = []
    for pid in PROFILES:
        for tid in TEXTS:
            vals = [r.get("emotional_impact", 0) for r in direct_rows if r["profile"] == pid and r["text_id"] == tid and isinstance(r.get("emotional_impact"), (int, float))]
            if len(vals) >= 3:
                icc_vals.append(vals)
    if icc_vals:
        icc_data = np.array(icc_vals)
        icc_val = icc(icc_data) if icc_data.shape[1] >= 2 else 0
    else:
        icc_val = 0
    icc_ok = icc_val >= 0.50
    print(f"  全链路 ICC = {icc_val:.3f} {'✅' if icc_ok else '❌'} (标准 ≥ 0.50)")

    # 2. 与直接 prompt 一致性：层2预测 vs 层3直接评价的 Spearman ρ
    # 对每个 text × profile 组合，取层3均值 vs 层2预测值
    l3_means = {}
    for pid in PROFILES:
        l3_means[pid] = {}
        for tid in TEXTS:
            vals = [r.get("emotional_impact", 3) for r in direct_rows if r["profile"] == pid and r["text_id"] == tid and isinstance(r.get("emotional_impact"), (int, float))]
            l3_means[pid][tid] = float(np.mean(vals)) if vals else 3.0

    pipe_vals = [pipe_pred[t][p] for p in PROFILES for t in TEXTS]
    direct_vals = [l3_means[p][t] for p in PROFILES for t in TEXTS]
    rho = spearman_rho(pipe_vals, direct_vals)
    rho_ok = rho >= 0.60
    print(f"  与直接 prompt ρ = {rho:.3f} {'✅' if rho_ok else '❌'} (标准 ≥ 0.60)")

    # 3. ANOVA 画像主效应：不同画像的层3评价是否显著不同
    from scipy.stats import f_oneway
    groups = []
    for pid in PROFILES:
        g = [r.get("emotional_impact", 3) for r in direct_rows if r["profile"] == pid and isinstance(r.get("emotional_impact"), (int, float))]
        if g:
            groups.append(np.array(g, dtype=float))
    if len(groups) >= 2:
        f_stat, p_val = f_oneway(*groups)
        anova_ok = p_val < 0.05
    else:
        f_stat, p_val = 0, 1
        anova_ok = False
    print(f"  ANOVA F={f_stat:.2f}, p={p_val:.4f} {'✅' if anova_ok else '❌'} (标准 p<0.05)")

    # 汇总
    passed = icc_ok and rho_ok and anova_ok
    summary = {
        "texts": list(TEXTS.keys()),
        "icc": round(float(icc_val), 4),
        "icc_pass": bool(icc_ok),
        "spearman_rho_vs_direct": round(float(rho), 4) if rho is not None else None,
        "spearman_pass": bool(rho_ok),
        "anova_f": round(float(f_stat), 4),
        "anova_p": round(float(p_val), 4),
        "anova_pass": bool(anova_ok),
        "pass": bool(passed),
    }
    save_json(results_dir / "e4-5_summary.json", summary)
    print(f"\n  整体通过: {'✅' if passed else '❌'}")
    if passed:
        print("  → p16-reader 全部实验完成")
    return summary


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "p16-reader"
    run(_base / "data" / "input", _base / "data" / "output")
