"""E4-1 — 读者画像分化验证

5 画像 × 6 文本 × n_calls 次调用。
分析：判别效度、稳定效度、客观基线。
"""
import sys, json
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[5]
REPO_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from packages.python.llm import call_llm
from packages.python.io import save_json, load_json
from packages.python.stats import cohens_d, icc, spearman_rho

FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
TEXT_IDS = ["4.1", "7.2", "9.1", "2.3", "10.3", "1.2"]
TEXT_PATHS = {
    "4.1": "职场言情/4_成稿/1_1_咖啡厅重逢.md",
    "7.2": "职场言情/4_成稿/7_2_公园拥抱.md",
    "9.1": "职场言情/4_成稿/9_1_家里吃火锅.md",
    "2.3": "职场言情/4_成稿/2_3_傍晚小龙虾.md",
    "10.3": "职场言情/4_成稿/10_3_阳台看星星.md",
    "1.2": "职场言情/4_成稿/1_2_深夜失眠.md",
}


def read_text(path: str) -> str:
    full = FICTION_ROOT / path
    text = full.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def call_once(profile: dict, text: str) -> dict | None:
    from .prompt_templates import build_evaluation_prompt
    prompt = build_evaluation_prompt(profile, text)
    raw = call_llm(prompt, temperature=0.5)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-1 — 读者画像分化验证")
    print("=" * 60)

    profiles = load_json(data_dir / "profiles.json")
    profiles = [p for p in profiles if p["id"] != "P0"]
    labels = [p["id"] for p in profiles]
    print(f"画像: {labels}")
    print(f"文本: {TEXT_IDS}")

    # 读取 pilot 确定 n_calls
    pilot = load_json(results_dir / "e4-1_pilot_result.json")
    n_calls = pilot.get("recommended_n_calls", 3)
    print(f"n_calls = {n_calls} (来自 pilot)")

    # ── 执行 ──
    cache = results_dir / "e4-1_raw.json"
    if cache.exists():
        rows = load_json(cache)
        print("← 读取缓存")
    else:
        rows = []
        for pid, prof in zip(labels, profiles):
            for tid in TEXT_IDS:
                text = read_text(TEXT_PATHS[tid])
                for c in range(n_calls):
                    resp = call_once(prof, text)
                    if resp is None:
                        print(f"  {pid} × {tid} call {c}: JSON 解析失败")
                        continue
                    resp["profile"] = pid
                    resp["text_id"] = tid
                    resp["call"] = c
                    rows.append(resp)
                    print(f"  {pid} × {tid} call {c}: 文笔={resp.get('writing_quality','?')}, 情感={resp.get('emotional_impact','?')}")
        save_json(cache, rows)
        print("  已保存")

    # ── 分析 ──
    # 判别效度（无方向检验）：画像是否影响了评分模式？
    def mean_for(pid, field):
        vals = [r[field] for r in rows if r["profile"] == pid and isinstance(r.get(field), (int, float))]
        return float(np.mean(vals)) if vals else 0.0

    FIELDS = ["writing_quality", "emotional_impact", "character_realism", "cliche_level"]
    print("\n── 判别效度（无方向检验）──")
    print("\n  各画像评分均值:")
    header = "字段".ljust(20) + "".join(f"{p:>10}" for p in labels)
    print(f"  {header}")
    for field in FIELDS:
        vals = "".join(f"{mean_for(p, field):>10.2f}" for p in labels)
        print(f"  {field:<20}{vals}")

    # eta-squared：画像解释了多少评分方差
    from scipy.stats import f_oneway
    eta_sq_list = []
    for field in FIELDS:
        groups = [np.array([r[field] for r in rows if r["profile"] == p and isinstance(r.get(field), (int, float))], dtype=float) for p in labels]
        all_vals = np.concatenate(groups)
        grand_mean = all_vals.mean()
        ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
        ss_within = sum(((g - g.mean()) ** 2).sum() for g in groups)
        eta_sq = ss_between / (ss_between + ss_within) if (ss_between + ss_within) > 0 else 0
        eta_sq_list.append(eta_sq)
        # 单因素 ANOVA 方向检验
        f_stat, p_val = f_oneway(*groups)
        sig = "显著" if p_val < 0.05 else "不显著"
        print(f"  {field:<25} η²={eta_sq:.3f}  F={f_stat:.2f}  p={p_val:.4f} {sig}")

    mean_eta = float(np.mean(eta_sq_list))
    n_sig = sum(1 for f in FIELDS for g in [np.array([r[f] for r in rows if r["profile"] == p and isinstance(r.get(f), (int, float))], dtype=float) for p in labels] if len(g) > 1)
    print(f"\n  平均 η² = {mean_eta:.3f}  (标准 ≥ 0.10)")
    disc_ok = mean_eta >= 0.10
    print(f"  {'✅' if disc_ok else '❌'} 判别效度通过")

    # 稳定效度
    print("\n── 稳定效度 ──")
    icc_vals = []
    for pid in labels:
        for tid in TEXT_IDS:
            vals = [r["emotional_impact"] for r in rows if r["profile"] == pid and r["text_id"] == tid and isinstance(r.get("emotional_impact"), (int, float))]
            if len(vals) >= 3:
                icc_vals.append(vals)
    if icc_vals:
        icc_data = np.array(icc_vals)
        icc_val = icc(icc_data) if icc_data.shape[1] >= 2 else 0
    else:
        icc_val = 0
    icc_ok = icc_val >= 0.50
    print(f"  ICC = {icc_val:.3f} {'✅' if icc_ok else '❌'} (标准 ≥ 0.50)")

    # 汇总
    overall = disc_ok and icc_ok

    summary = {
        "eta_squared_per_field": {f: round(float(e), 3) for f, e in zip(FIELDS, eta_sq_list)},
        "mean_eta_squared": round(float(mean_eta), 3),
        "discriminant_pass": bool(disc_ok),
        "icc": round(float(icc_val), 3),
        "icc_pass": bool(icc_ok),
        "overall_pass": bool(overall),
    }
    save_json(results_dir / "e4-1_summary.json", summary)

    print(f"\n  → 整体通过: {'✅' if overall else '❌'}")
    if overall:
        print("  → 进入 E4-2")
    else:
        print("  → 项目终止")

    return summary


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "review"
    run(_base / "data" / "input", _base / "data" / "output")
