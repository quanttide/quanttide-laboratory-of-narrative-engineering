#!/usr/bin/env python3
"""
p15 — 叙事约束矩阵（Direction C）

基于 story.yaml 的 clue/tension 构建 14 plots × K 维度的约束矩阵，
运行三种异常检测规则，与 p12 诊断对比验证。
"""
import json, sys, math, re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
STORY_FILE = REPO_ROOT / "docs" / "gallery" / "fiction" / "urban-romance" / "story.yaml"
RESULTS_DIR = Path(__file__).parent / "results"
P12_DIR = Path(__file__).parent.parent / "p12-plot-structure" / "results"


def load_story():
    import yaml
    with open(STORY_FILE) as f:
        return yaml.safe_load(f)


# Dimension definitions
DIMENSIONS = {
    "social_distance": {
        "desc": "社交距离，0=陌生人 5=恋人",
        "values": list(range(6)),
    },
    "tension_type": {
        "desc": "张力方向: approach/retreat/mutual/avoid",
        "values": ["approach", "retreat", "mutual", "avoid"],
    },
    "action_dominant": {
        "desc": "主导行为: internal/dialogue/physical/mixed",
        "values": ["internal", "dialogue", "physical", "mixed"],
    },
    "info_revealed": {
        "desc": "信息释放: none/hint/partial/full",
        "values": ["none", "hint", "partial", "full"],
    },
    "core_tension": {
        "desc": "核心约束强度，0=无 5=极强",
        "values": list(range(6)),
    },
}


def build_matrix(data):
    """人工标注的约束矩阵（14 plots × 5 维度）。"""
    # 人工标注值：基于 story.yaml 的 clue/tension 原文确定
    HAND_CODED = {
        "1_1":  {"social_distance": 2, "tension_type": "approach", "action_dominant": "mixed",    "info_revealed": "partial", "core_tension": 5},
        "1_2":  {"social_distance": 1, "tension_type": "retreat",  "action_dominant": "internal", "info_revealed": "none",    "core_tension": 4},
        "2_1":  {"social_distance": 2, "tension_type": "mutual",   "action_dominant": "dialogue", "info_revealed": "partial", "core_tension": 4},
        "2_3":  {"social_distance": 3, "tension_type": "approach", "action_dominant": "dialogue", "info_revealed": "partial", "core_tension": 3},
        "4_1":  {"social_distance": 3, "tension_type": "approach", "action_dominant": "mixed",    "info_revealed": "hint",    "core_tension": 5},
        "4_2":  {"social_distance": 3, "tension_type": "mutual",   "action_dominant": "mixed",    "info_revealed": "partial", "core_tension": 4},
        "4_3":  {"social_distance": 3, "tension_type": "approach", "action_dominant": "dialogue", "info_revealed": "hint",    "core_tension": 3},
        "6_2":  {"social_distance": 4, "tension_type": "mutual",   "action_dominant": "mixed",    "info_revealed": "partial", "core_tension": 4},
        "7_2":  {"social_distance": 4, "tension_type": "approach", "action_dominant": "physical", "info_revealed": "hint",    "core_tension": 3},
        "8_2":  {"social_distance": 4, "tension_type": "mutual",   "action_dominant": "dialogue", "info_revealed": "full",    "core_tension": 5},
        "9_1":  {"social_distance": 5, "tension_type": "mutual",   "action_dominant": "mixed",    "info_revealed": "none",    "core_tension": 1},
        "10_1": {"social_distance": 5, "tension_type": "mutual",   "action_dominant": "mixed",    "info_revealed": "full",    "core_tension": 2},
        "10_2": {"social_distance": 5, "tension_type": "mutual",   "action_dominant": "mixed",    "info_revealed": "none",    "core_tension": 1},
        "10_3": {"social_distance": 5, "tension_type": "mutual",   "action_dominant": "dialogue", "info_revealed": "none",    "core_tension": 1},
    }

    matrix = []
    for p in data["plots"]:
        tid = p["id"]
        row = {"id": tid, "title": p["title"]}
        if tid in HAND_CODED:
            row.update(HAND_CODED[tid])
        else:
            row.update({"social_distance": 2, "tension_type": "mutual",
                        "action_dominant": "mixed", "info_revealed": "none",
                        "core_tension": 3})
        matrix.append(row)
    return matrix


def detect_anomalies(matrix):
    """Run three detection rules on the constraint matrix."""
    anomalies = []

    # Rule 1: Causal gap - social_distance jump >= 2 between adjacent scenes
    for i in range(len(matrix) - 1):
        curr = matrix[i]
        next_p = matrix[i + 1]
        d_jump = abs(next_p["social_distance"] - curr["social_distance"])
        if d_jump >= 2:
            anomalies.append({
                "rule": "causal_gap",
                "location": f"{curr['id']} → {next_p['id']}",
                "detail": f"social_distance从 {curr['social_distance']} 跳到 {next_p['social_distance']}（跳级{d_jump}）",
                "severity": min(d_jump, 3),
                "narrative_meaning": "",
            })

    # Rule 2: Pacing imbalance - same tension_type for 3+ consecutive scenes
    prev_type = None
    streak_start = None
    streak_len = 0
    for i, p in enumerate(matrix):
        t = p["tension_type"]
        if t == prev_type:
            streak_len += 1
        else:
            if streak_len >= 3 and streak_start is not None:
                anomaly = {
                    "rule": "pacing_imbalance",
                    "location": f"{matrix[streak_start]['id']} → {matrix[i-1]['id']}",
                    "detail": f"tension_type='{t}' 连续出现 {streak_len} 场",
                    "severity": min(streak_len - 2, 3),
                    "narrative_meaning": "",
                }
                anomalies.append(anomaly)
            prev_type = t
            streak_start = i
            streak_len = 1

    # Check last streak
    if streak_len >= 3 and streak_start is not None:
        anomalies.append({
            "rule": "pacing_imbalance",
            "location": f"{matrix[streak_start]['id']} → {matrix[-1]['id']}",
            "detail": f"tension_type='{prev_type}' 连续出现 {streak_len} 场",
            "severity": min(streak_len - 2, 3),
            "narrative_meaning": "",
        })

    # Rule 3: Motivation unclear - physical action at social_distance <= 1
    for p in matrix:
        if p["action_dominant"] == "physical" and p["social_distance"] <= 1:
            anomalies.append({
                "rule": "motivation_unclear",
                "location": p["id"],
                "detail": f"行为类型=physical 但社交距离={p['social_distance']}（陌生人状态下的亲密动作，动机缺解释）",
                "severity": 2,
                "narrative_meaning": "",
            })

    return anomalies


def interpret_anomalies(anomalies):
    """Add narrative interpretation to each anomaly."""
    for a in anomalies:
        if a["rule"] == "causal_gap":
            a["narrative_meaning"] = f"关系跳过了一个中间阶段——从{a['detail'].split('从')[1].split('跳到')[0].strip()}级的社交距离直接跳到{a['detail'].split('跳到')[1].strip().split('）')[0]}级。读者可能会问：中间发生了什么？"
        elif a["rule"] == "pacing_imbalance":
            a["narrative_meaning"] = f"连续 {a['detail'].replace('tension_type=','').replace(' 连续出现 ','')} 场戏都在做同一种情感动作——张力方向没有变化，可能会让读者感到节奏重复。"
        elif a["rule"] == "motivation_unclear":
            a["narrative_meaning"] = f"在社交距离为{a['detail'].split('社交距离=')[1].split('）')[0]}的状态下出现了身体主导的行为——这个行为缺乏社交层面的动机支撑。"
    return anomalies


def validate_against_p12(anomalies):
    """Compare constraint matrix anomalies against p12 diagnosis results."""
    p12_files = [
        ("S1", P12_DIR / "diagnosis_S1.json"),
        ("S2", P12_DIR / "diagnosis_S2.json"),
    ]

    p12_weak = {}
    for sid, fpath in p12_files:
        if fpath.exists():
            data = json.loads(fpath.read_text("utf-8"))
            p12_weak[sid] = data.get("weak_points", [])
        else:
            p12_weak[sid] = []

    # Map anomalies to plot IDs
    anomaly_plots = []
    for a in anomalies:
        loc = a["location"]
        plots = re.findall(r"\d+_\d+", loc)
        anomaly_plots.extend(plots)

    # Check overlap: are the anomaly-detected plots also flagged by p12?
    # This is approximate since p12 analyzed generated directions, not actual plots
    validation = {
        "p12_s1_weak_points": len(p12_weak.get("S1", [])),
        "p12_s2_weak_points": len(p12_weak.get("S2", [])),
        "matrix_anomalies_total": len(anomalies),
        "matrix_anomaly_plots": sorted(set(anomaly_plots)),
        "note": "p12 诊断的是虚构走向而非实际场景文本，重叠比对仅供参考",
    }

    return validation


def format_matrix(matrix):
    """Print the constraint matrix as a table."""
    header = f"{'ID':<6} {'标题':<12} {'SD':<3} {'TT':<10} {'AD':<10} {'IR':<8} {'CT':<3}"
    sep = "-" * len(header)
    lines = [header, sep]
    for p in matrix:
        lines.append(
            f"{p['id']:<6} {p['title']:<12} {p['social_distance']:<3} {p['tension_type']:<10} {p['action_dominant']:<10} {p['info_revealed']:<8} {p['core_tension']:<3}"
        )
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("p15 — 叙事约束矩阵（Direction C）")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    # Load story
    data = load_story()
    print(f"\n加载 story.yaml: {len(data['plots'])} 个 plot")

    # Step 1: Build constraint matrix
    mc = RESULTS_DIR / "constraint_matrix.json"
    if mc.exists():
        matrix = json.loads(mc.read_text("utf-8"))
        print("  约束矩阵已存在（读取缓存）")
    else:
        print("  构建约束矩阵...")
        matrix = build_matrix(data)
        mc.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), "utf-8")

    print(f"\n约束矩阵（{len(matrix)} plots × {len(DIMENSIONS)} 维度）:")
    print(format_matrix(matrix))

    # Step 2: Detect anomalies
    ac = RESULTS_DIR / "anomalies.json"
    if ac.exists():
        anomalies = json.loads(ac.read_text("utf-8"))
    else:
        print("\n运行异常检测...")
        anomalies = detect_anomalies(matrix)
        anomalies = interpret_anomalies(anomalies)
        ac.write_text(json.dumps(anomalies, ensure_ascii=False, indent=2), "utf-8")

    print(f"\n检测到 {len(anomalies)} 个结构异常:")
    for a in anomalies:
        print(f"  [{a['rule']}] {a['location']} (severity={a['severity']})")
        print(f"    细节: {a['detail']}")
        print(f"    叙事含义: {a['narrative_meaning']}")

    # Step 3: Validate against p12
    vc = RESULTS_DIR / "validation.json"
    if vc.exists():
        validation = json.loads(vc.read_text("utf-8"))
    else:
        print("\n与 p12 诊断对比...")
        validation = validate_against_p12(anomalies)
        vc.write_text(json.dumps(validation, ensure_ascii=False, indent=2), "utf-8")

    print(f"\np12 S1 薄弱点: {validation['p12_s1_weak_points']}")
    print(f"p12 S2 薄弱点: {validation['p12_s2_weak_points']}")
    print(f"矩阵异常涉及的 plot: {validation['matrix_anomaly_plots']}")

    # Print matrix stats
    sd_vals = [p["social_distance"] for p in matrix]
    ct_vals = [p["core_tension"] for p in matrix]
    print(f"\n维度统计:")
    print(f"  social_distance: 均值={sum(sd_vals)/len(sd_vals):.2f} 范围={min(sd_vals)}-{max(sd_vals)}")
    print(f"  core_tension:    均值={sum(ct_vals)/len(ct_vals):.2f} 范围={min(ct_vals)}-{max(ct_vals)}")

    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
