"""E4-3 — 层1认知负荷指标验证

对 Phase I 的 6 篇文本，每句运行 4 个公式计算 + LLM 标注，
计算 Spearman ρ（公式 vs LLM），取平均 ≥ 0.60 为通过。
"""
import sys, re
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from packages.io import save_json, load_json
from packages.stats import spearman_rho
from packages.llm import call_llm

FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
TEXT_PATHS = {
    "4.1": "职场言情/4_成稿/1_1_咖啡厅重逢.md",
    "7.2": "职场言情/4_成稿/7_2_公园拥抱.md",
    "9.1": "职场言情/4_成稿/9_1_家里吃火锅.md",
    "2.3": "职场言情/4_成稿/2_3_傍晚小龙虾.md",
    "10.3": "职场言情/4_成稿/10_3_阳台看星星.md",
    "1.2": "职场言情/4_成稿/1_2_深夜失眠.md",
}

SAMPLE_SIZE = 10  # 每篇文本采 10 句用于 LLM 验证


def _read_text(path: str) -> str:
    full = FICTION_ROOT / path
    text = full.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'[。！？\n]+', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _validate_module(
    name: str,
    formula_fn,
    llm_fn,
    texts: dict[str, str],
    sentences: dict[str, list[str]],
    results_dir: Path,
) -> dict:
    """验证一个模块的公式 vs LLM 一致性。"""
    per_text_rho = {}
    llm_cache = results_dir / f"e4-3_{name}_llm.json"

    for tid, sents in sentences.items():
        # 公式计算
        formula_scores = formula_fn(texts[tid])
        scores_by_sent = formula_scores[: len(sents)]

        # LLM 标注（缓存）
        if llm_cache.exists():
            llm_data = load_json(llm_cache)
        else:
            llm_data = {}
        if tid not in llm_data:
            llm_data[tid] = []
            sample = sents[:SAMPLE_SIZE]
            for i, s in enumerate(sample):
                prev = sents[i - 1] if i > 0 else ""
                if "backtracking" in name:
                    val = llm_fn(s, prev)
                elif "situation" in name:
                    val = llm_fn(texts[tid][:500], s)
                else:
                    val = llm_fn(s)
                llm_data[tid].append(val if val is not None else 0)
            save_json(llm_cache, llm_data)

        llm_scores = llm_data[tid]

        # 对齐长度
        n = min(len(scores_by_sent), len(llm_scores), SAMPLE_SIZE)
        if n < 3:
            per_text_rho[tid] = 0.0
            continue
        rho = spearman_rho(scores_by_sent[:n], llm_scores[:n])
        per_text_rho[tid] = round(rho, 4)

    rho_vals = [v for v in per_text_rho.values() if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not rho_vals:
        mean_rho = 0.0
    else:
        mean_rho = round(float(np.mean(rho_vals)), 4)
    passed = mean_rho >= 0.60

    print(f"  {name}: 各文本 ρ = {per_text_rho}, 均值 = {mean_rho} {'✅' if passed else '❌'}")
    def _clean(v):
        if v is None:
            return 0.0
        try:
            fv = float(v)
            return round(fv, 4) if not np.isnan(fv) else 0.0
        except (TypeError, ValueError):
            return 0.0
    return {"per_text_rho": {k: _clean(v) for k, v in per_text_rho.items()}, "mean_rho": mean_rho, "pass": bool(passed)}


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-3 — 层1认知负荷指标验证")
    print("=" * 60)

    # 读取文本
    texts = {}
    sentences = {}
    for tid, path in TEXT_PATHS.items():
        t = _read_text(path)
        texts[tid] = t
        sentences[tid] = _split_sentences(t)
        print(f"  {tid}: {len(sentences[tid])} 句")

    # 导入模块
    from .inference_demand import inference_demand
    from .working_memory import working_memory_load
    from .backtracking import backtracking_prediction
    from .situation_model import situation_model
    from .llm_labels import (
        llm_label_inference_demand,
        llm_label_working_memory,
        llm_label_backtracking,
        llm_label_situation_model,
    )

    # 逐个验证
    print("\n── 验证模块 ──")
    results = {}

    results["inference_demand"] = _validate_module(
        "inference_demand", inference_demand, llm_label_inference_demand,
        texts, sentences, results_dir,
    )
    results["working_memory"] = _validate_module(
        "working_memory", working_memory_load, llm_label_working_memory,
        texts, sentences, results_dir,
    )
    results["backtracking"] = _validate_module(
        "backtracking", backtracking_prediction, llm_label_backtracking,
        texts, sentences, results_dir,
    )

    # 情境模型是全文级别，用 5 个维度做样本
    print("  situation_model: 全文五维度（LLM 标注）...")
    dims = ["时间连贯性", "空间连贯性", "人物连贯性", "因果连贯性", "意图连贯性"]
    sm_cache = results_dir / "e4-3_situation_llm.json"
    if sm_cache.exists():
        sm_llm = load_json(sm_cache)
    else:
        sm_llm = {}
    per_text_rho_sm = {}
    for tid in texts:
        formula_dict = situation_model(texts[tid])
        formula_vals = [formula_dict.get(d, 0) for d in dims]
        if tid not in sm_llm:
            sm_llm[tid] = []
            for dim in dims:
                val = llm_label_situation_model(texts[tid][:300], dim)
                sm_llm[tid].append(val if val is not None else 3)
            save_json(sm_cache, sm_llm)
        llm_vals = sm_llm[tid]
        rho = spearman_rho(formula_vals, llm_vals)
        per_text_rho_sm[tid] = round(float(rho), 4) if not np.isnan(float(rho)) else 0.0
    sm_rho_vals = [v for v in per_text_rho_sm.values() if not np.isnan(v)]
    mean_rho_sm = round(float(np.mean(sm_rho_vals)), 4) if sm_rho_vals else 0.0
    results["situation_model"] = {
        "per_text_rho": per_text_rho_sm,
        "mean_rho": mean_rho_sm,
        "pass": bool(mean_rho_sm >= 0.60),
    }
    print(f"  situation_model: 各文本 ρ = {per_text_rho_sm}, 均值 = {mean_rho_sm}")

    # 汇总
    rho_all = [
        r for k in ["inference_demand", "working_memory", "backtracking", "situation_model"]
        if (r := results[k]["mean_rho"]) is not None and not (isinstance(r, float) and np.isnan(r))
    ]
    mean_all = round(float(np.mean(rho_all)), 4) if rho_all else 0.0
    all_pass = all(results[k]["pass"] for k in results)
    results["mean_rho"] = mean_all
    results["pass"] = bool(all_pass)

    save_json(results_dir / "e4-3_summary.json", results)
    print(f"\n  平均 ρ = {mean_all} {'✅' if all_pass else '❌'}")
    if all_pass:
        print("  → 层1验证通过，进入 E4-4")
    else:
        print("  → 未通过，需修复公式")

    return results


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "p16-reader"
    run(_base / "data" / "input", _base / "data" / "output")
