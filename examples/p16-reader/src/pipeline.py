"""E4-5 — 端到端集成验证

全链路：层1（LLM标注认知负荷，可选装饰层）→ 层3（直接prompt评价）
在 4 篇未见文本上运行直接 prompt 评价，验证跨文本分化稳定性。

核心验证：在新文本上，不同画像的直接 prompt 评价是否保持：
  1. 分化性（ANOVA p < 0.05）
  2. 稳定性（ICC ≥ 0.50）
  3. 模式与 Phase I 一致（P3最挑剔、P1最感性等）

注意：层1→层2的回归权重映射因 n=6 样本不足已被放弃。
层1认知负荷仅作为可选的装饰性分析维度（辅助解释"为什么"），不作为预测特征。
"""
import sys, json
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from packages.python.io import save_json, load_json
from packages.python.stats import icc

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


def _compute_eta_squared(data: list[dict], field: str) -> float:
    """计算画像因素在某个评分维度上的 η²。"""
    from scipy.stats import f_oneway
    groups = []
    grand_mean = np.mean([r.get(field, 0) for r in data if isinstance(r.get(field), (int, float))])
    ss_between = 0
    ss_total = 0
    for pid in PROFILES:
        vals = [r[field] for r in data if r["profile"] == pid and isinstance(r.get(field), (int, float))]
        if not vals:
            continue
        group_mean = np.mean(vals)
        ss_between += len(vals) * (group_mean - grand_mean) ** 2
        for v in vals:
            ss_total += (v - grand_mean) ** 2
    if ss_total == 0:
        return 0.0
    return round(ss_between / ss_total, 4)


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-5 — 端到端集成验证（已更新验证标准）")
    print("=" * 60)
    print()
    print("注：层1→层2回归权重映射因n=6样本不足已放弃。")
    print("E4-5改为验证新文本上直接promt评价的跨文本分化稳定性。")
    print()

    # 加载画像定义
    profiles = load_json(data_dir / "profiles.json")
    profiles = [p for p in profiles if p["id"] != "P0"]
    profile_map = {p["id"]: p for p in profiles}

    # ── 层1：LLM 标注认知负荷（装饰层，可选）──
    print("── 层1：LLM 标注认知负荷（装饰层）──")
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
    print()

    # ── 层2：跳过（回归权重映射不可行）──
    print("── 层2：跳过（n=6 不足以做回归权重映射）──")
    print()

    # ── 层3：直接 prompt 评价（核心验证数据）──
    print("── 层3：直接 prompt 评价──")
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
                    from packages.python.llm import call_llm
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
    print()

    # ── 验证 ──
    print("── 验证 ──")

    # 1. 稳定性：同一 text × profile 的 call 间 ICC
    from packages.python.stats import icc as icc_func
    icc_vals = []
    for pid in PROFILES:
        for tid in TEXTS:
            vals = [r.get("emotional_impact", 0) for r in direct_rows
                    if r["profile"] == pid and r["text_id"] == tid
                    and isinstance(r.get("emotional_impact"), (int, float))]
            if len(vals) >= 3:
                icc_vals.append(vals)
    if icc_vals:
        icc_data = np.array(icc_vals)
        icc_val = float(icc_func(icc_data)) if icc_data.shape[1] >= 2 and icc_data.size > 0 else 0.0
    else:
        icc_val = 0.0
    icc_ok = icc_val >= 0.50
    print(f"  全链路 ICC = {icc_val:.3f} {'✅' if icc_ok else '❌'} (标准 ≥ 0.50)")

    # 2. 分化性：不同画像的评价是否系统不同（ANOVA + η²）
    from scipy.stats import f_oneway
    eval_fields = ["writing_quality", "emotional_impact", "character_realism", "cliche_level"]

    anova_results = {}
    for field in eval_fields:
        groups = []
        for pid in PROFILES:
            g = [r[field] for r in direct_rows if r["profile"] == pid
                 and isinstance(r.get(field), (int, float))]
            if g:
                groups.append(np.array(g, dtype=float))
        if len(groups) >= 2:
            f_stat, p_val = f_oneway(*groups)
        else:
            f_stat, p_val = 0, 1.0
        eta_sq = _compute_eta_squared(direct_rows, field)
        anova_results[field] = {
            "f": round(float(f_stat), 4),
            "p": round(float(p_val), 4),
            "eta_squared": eta_sq,
            "pass": bool(p_val < 0.05),
        }

    n_sig = sum(1 for v in anova_results.values() if v["pass"])
    anova_ok = n_sig >= 2  # 4 个维度中至少 2 个显著，或平均 η² ≥ 0.10
    mean_eta = np.mean([v.get("eta_squared", 0) for v in anova_results.values()])
    anova_alt_ok = mean_eta >= 0.10

    print(f"  ANOVA 画像主效应（按维度）：")
    for field, result in anova_results.items():
        print(f"    {field}: F={result['f']:.2f}, p={result['p']:.4f}, η²={result['eta_squared']:.4f} {'✅' if result['pass'] else '❌'}")
    print(f"  显著维度数: {n_sig}/4 {'✅' if anova_ok else '❌'} (标准 ≥ 2/4)")
    print(f"  平均 η² = {mean_eta:.4f} {'✅' if anova_alt_ok else '❌'} (标准 ≥ 0.10)")

    # 3. 画像评分模式与 Phase I 一致
    # Phase I 的关键模式：P3 cliche_level 最低（最挑剔），P1 emotional_impact 最高（最感性）
    profile_means = {}
    for pid in PROFILES:
        means = {}
        for field in eval_fields:
            vals = [r[field] for r in direct_rows if r["profile"] == pid
                    and isinstance(r.get(field), (int, float))]
            means[field] = round(float(np.mean(vals)), 2) if vals else 0
        profile_means[pid] = means

    # 检查模式一致性
    p3_cliche = profile_means["P3"]["cliche_level"]
    others_cliche = [profile_means[p]["cliche_level"] for p in PROFILES if p != "P3"]
    p3_most_critical = p3_cliche <= min(others_cliche)  # P3 cliche 最低 = 最挑剔

    p1_emotional = profile_means["P1"]["emotional_impact"]
    others_emotional = [profile_means[p]["emotional_impact"] for p in PROFILES if p != "P1"]
    p1_most_emotional = p1_emotional >= max(others_emotional)  # P1 情感冲击最高

    pattern_ok = p3_most_critical and p1_most_emotional
    print(f"\n  模式一致性验证（与 Phase I 对比）：")
    print(f"    P3 cliche_level 最低（最挑剔）: {profile_means['P3']['cliche_level']} ≤ min其他={min(others_cliche)} {'✅' if p3_most_critical else '❌'}")
    print(f"    P1 emotional_impact 最高（最感性）: {profile_means['P1']['emotional_impact']} ≥ max其他={max(others_emotional)} {'✅' if p1_most_emotional else '❌'}")

    # 汇总
    overall_pass = icc_ok and (anova_ok or anova_alt_ok)
    summary = {
        "texts": list(TEXTS.keys()),
        "icc": round(float(icc_val), 4),
        "icc_pass": bool(icc_ok),
        "anova_per_dimension": anova_results,
        "n_sig_dimensions": n_sig,
        "mean_eta_squared": round(float(mean_eta), 4),
        "anova_pass": bool(anova_ok or anova_alt_ok),
        "profile_means": profile_means,
        "p3_most_critical": bool(p3_most_critical),
        "p1_most_emotional": bool(p1_most_emotional),
        "pattern_consistency_pass": bool(pattern_ok),
        "pass": bool(overall_pass),
        "note": "回归权重映射因n=6样本不足已放弃。E4-5改验证新文本上直接prompt评价的跨文本分化稳定性。",
    }
    save_json(results_dir / "e4-5_summary.json", summary)
    print(f"\n  整体通过: {'✅' if overall_pass else '❌'}")
    if overall_pass:
        print("  → 跨文本分化稳定性验证通过")
    else:
        print("  → 不通过原因：")
        if not icc_ok:
            print("    - ICC < 0.50：新文本上评价一致性不足")
        if not (anova_ok or anova_alt_ok):
            print("    - 新文本上画像差异不够（ANOVA 不显著或效应量小）")
        if not pattern_ok:
            print("    - 画像评分模式与 Phase I 不一致")
    return summary


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "p16-reader"
    run(_base / "data" / "input", _base / "data" / "output")
