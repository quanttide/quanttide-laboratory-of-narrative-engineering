"""权重比推断 — 对每个画像，回归层1指标→E4-1评分，得到权重向量。"""

import sys, json
from pathlib import Path
GIT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(GIT_ROOT))
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from packages.python.io import load_json

LAYER1_FIELDS = ["inference_demand", "working_memory", "backtracking"]
EVAL_FIELDS = ["writing_quality", "emotional_impact", "character_realism", "cliche_level"]
PROFILES = ["P1", "P2", "P3", "P4", "P5"]
TEXT_IDS = ["4.1", "7.2", "9.1", "2.3", "10.3", "1.2"]


def _build_avgs(results_dir: Path) -> tuple[dict, dict]:
    """构建层1均值（文本级别）和 E4-1 评分均值（画像×文本级别）。

    返回 (l1_avg, eval_avg)。
    l1_avg: {tid: {field: float}}
    eval_avg: {pid: {tid: {field: float}}}
    """
    layer1 = load_json(results_dir / "e4-3_layer1_cache.json")
    e4_1 = load_json(results_dir / "e4-1_raw.json")

    l1_avg = {}
    for tid in TEXT_IDS:
        l1 = layer1.get(tid, {})
        n = len(l1.get("inference_demand", []))
        l1_avg[tid] = {
            f: float(np.mean(l1.get(f, [0]))) if n > 0 else 0.0
            for f in LAYER1_FIELDS
        }

    eval_avg = {}
    for pid in PROFILES:
        eval_avg[pid] = {}
        for tid in TEXT_IDS:
            rows = [r for r in e4_1 if r["profile"] == pid and r["text_id"] == tid]
            if not rows:
                eval_avg[pid][tid] = {f: 0.0 for f in EVAL_FIELDS}
                continue
            eval_avg[pid][tid] = {
                f: float(np.mean([r.get(f, 0) for r in rows if isinstance(r.get(f), (int, float))]))
                for f in EVAL_FIELDS
            }

    return l1_avg, eval_avg


def compute_weight_ratios(results_dir: Path) -> dict:
    """返回 {profile: {field: [w1,w2,w3,w4], weights: [w1,w2,w3,w4]}}"""
    l1_avg, eval_avg = _build_avgs(results_dir)    # 对每个画像做回归
    result = {}
    for pid in PROFILES:
        # 构建 X (6 texts × 3 features), Y (6 texts × 4 DVs)
        X = np.array([[l1_avg[t][f] for f in LAYER1_FIELDS] for t in TEXT_IDS])
        Y = np.array([[eval_avg[pid][t][f] for f in EVAL_FIELDS] for t in TEXT_IDS])

        # 标准化
        scaler_x = StandardScaler()
        Xs = scaler_x.fit_transform(X)

        weights_per_field = {}
        field_weights = []
        for fi, field in enumerate(EVAL_FIELDS):
            y = Y[:, fi]
            scaler_y = StandardScaler()
            ys = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

            reg = LinearRegression()
            reg.fit(Xs, ys)
            w = reg.coef_  # 标准化回归系数
            weights_per_field[field] = [round(float(v), 4) for v in w]
            field_weights.append(w)

        # 平均权重（带符号归一化）
        avg_w = np.mean(field_weights, axis=0)
        w_abs_sum = np.abs(avg_w).sum()
        if w_abs_sum > 0:
            norm_w = [round(float(v / w_abs_sum), 4) for v in avg_w]
        else:
            norm_w = [0.3333, 0.3333, 0.3333]

        result[pid] = {
            "weights_per_field": weights_per_field,
            "weights": norm_w,
        }

    return result
