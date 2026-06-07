"""Step 2: 读者回响映射

对每个文本点，提取 p16 评价数据中该场景的各画像评分，
计算关键信号（方差最大的维度、分歧最大的画像对、异常值）。
"""
import json
import numpy as np
from collections import defaultdict
from pathlib import Path

PROFILES_ORDER = ["P1", "P2", "P3", "P4", "P5"]
EVAL_FIELDS = ["writing_quality", "emotional_impact", "character_realism", "cliche_level"]


def load_p16_data(p16_raw_path: Path):
    """加载 p16 原始评价数据。"""
    return json.loads(p16_raw_path.read_text("utf-8"))


def load_profiles(p16_profiles_path: Path):
    """加载画像定义。"""
    profiles = json.loads(p16_profiles_path.read_text("utf-8"))
    return {p["id"]: p for p in profiles if p["id"] != "P0"}


def map_reader_response(text_point, p16_data, profile_map):
    """对单个文本点，映射 p16 读者回响数据。

    返回：
        dict: {
            "scene_ratings": {profile_id: {field: mean_value, ...}, ...},
            "key_signals": {
                "max_variance_dimension": (field, variance),
                "max_divergence_pair": (p1, p2, field, diff),
                "anomalies": [...],
            }
        }
    """
    text_id = text_point["p16_text_id"]
    # 筛选该场景的所有评价记录
    scene_records = [r for r in p16_data if r["text_id"] == text_id]

    if not scene_records:
        return {
            "scene_ratings": {},
            "key_signals": {
                "warning": f"p16 数据中无 text_id={text_id} 的记录",
                "max_variance_dimension": None,
                "max_divergence_pair": None,
                "anomalies": [],
            },
        }

    # 按画像分组计算均值
    profile_vals = defaultdict(lambda: {f: [] for f in EVAL_FIELDS})
    all_vals = {f: [] for f in EVAL_FIELDS}

    for r in scene_records:
        pid = r["profile"]
        for f in EVAL_FIELDS:
            v = r.get(f)
            if isinstance(v, (int, float)):
                profile_vals[pid][f].append(v)
                all_vals[f].append(v)

    scene_ratings = {}
    for pid in PROFILES_ORDER:
        if pid in profile_vals:
            means = {}
            for f in EVAL_FIELDS:
                vals = profile_vals[pid][f]
                means[f] = round(float(np.mean(vals)), 2) if vals else None
            scene_ratings[pid] = means

    # 关键信号分析
    # 1. 方差最大的维度（画像间）
    profile_means_by_field = {f: [] for f in EVAL_FIELDS}
    for pid in PROFILES_ORDER:
        if pid in scene_ratings:
            for f in EVAL_FIELDS:
                v = scene_ratings[pid].get(f)
                if v is not None:
                    profile_means_by_field[f].append(v)

    field_variances = {}
    for f in EVAL_FIELDS:
        vals = profile_means_by_field[f]
        field_variances[f] = round(float(np.var(vals)), 4) if vals else 0

    max_var_field = max(field_variances, key=field_variances.get) if field_variances else None
    max_var_value = field_variances.get(max_var_field, 0)

    # 2. 分歧最大的画像对
    max_diff = -1
    max_pair = None
    for i, p1 in enumerate(PROFILES_ORDER):
        for p2 in PROFILES_ORDER[i + 1:]:
            if p1 in scene_ratings and p2 in scene_ratings:
                for f in EVAL_FIELDS:
                    v1 = scene_ratings[p1].get(f)
                    v2 = scene_ratings[p2].get(f)
                    if v1 is not None and v2 is not None:
                        diff = abs(v1 - v2)
                        if diff > max_diff:
                            max_diff = round(diff, 2)
                            max_pair = (p1, p2, f, max_diff)

    # 3. 异常值检测（某画像的某维度评分偏离均值 > 1.5 std）
    anomalies = []
    for f in EVAL_FIELDS:
        vals = all_vals[f]
        if vals:
            mu = np.mean(vals)
            sigma = np.std(vals)
            for pid in PROFILES_ORDER:
                if pid in scene_ratings:
                    v = scene_ratings[pid].get(f)
                    if v is not None and sigma > 0 and abs(v - mu) > 1.5 * sigma:
                        anomalies.append({
                            "profile": pid,
                            "field": f,
                            "value": v,
                            "mean": round(float(mu), 2),
                            "deviation": round(float(v - mu), 2),
                        })

    key_signals = {
        "max_variance_dimension": (max_var_field, max_var_value),
        "max_divergence_pair": max_pair,
        "anomalies": anomalies,
    }

    return {
        "scene_ratings": scene_ratings,
        "key_signals": key_signals,
    }
