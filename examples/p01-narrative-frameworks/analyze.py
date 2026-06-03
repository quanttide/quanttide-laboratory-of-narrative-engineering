#!/usr/bin/env python3
"""
分析 p01 实验结果：比较三个框架的叙事弧线是否对齐。
"""

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

# 框架角色到叙事阶段的数值映射（数值越大越接近"结束"）
FRAMEWORK_MAPS = {
    "起承转合": {"起": 0, "承": 1, "转": 2, "合": 3},
    "三幕结构": {"Setup": 0, "Confrontation": 1, "Resolution": 2},
    "情感曲线": {"常态": 0, "触发": 1, "爬升": 2, "峰值": 3, "回落": 4},
}

ARTICLES = ["A", "B", "C"]
ART_NAMES = {"A": "咖啡厅重逢", "B": "酒吧表白", "C": "第六章（论坛热搜）"}

NORM_TARGET = 10  # 统一归算到 10 阶段，方便比较


def load_labels(art_id: str) -> dict:
    """加载一篇文章的所有框架标注"""
    labels = {}
    for fw_id in ["qczh", "three_act", "emotion_curve"]:
        f = RESULTS_DIR / f"{art_id}_{fw_id}.json"
        if f.exists():
            data = json.loads(f.read_text("utf-8"))
            labels[data["framework"]] = [l["role"] for l in data["labels"]]
    return labels


def normalize_curve(roles: list[str], role_map: dict) -> list[float]:
    """将角色序列归算到 0-1 的连续曲线"""
    mapped = [role_map[r] for r in roles]
    max_val = max(mapped) if mapped else 1
    return [v / max_val for v in mapped]


def find_transitions(roles: list[str]) -> list[int]:
    """找出角色发生转换的段落位置"""
    return [i for i in range(1, len(roles)) if roles[i] != roles[i - 1]]


def find_half_points(roles: list[str], role_map: dict) -> dict:
    """找每个角色首次出现和末次出现的位置"""
    first, last = {}, {}
    for i, r in enumerate(roles):
        if r in role_map:
            if r not in first:
                first[r] = i
            last[r] = i
    return {"first": first, "last": last}


def analyze():
    print("=" * 70)
    print("p01 分析报告：叙事框架对比")
    print("=" * 70)

    for art_id in ARTICLES:
        labels = load_labels(art_id)
        if not labels:
            continue

        name = ART_NAMES[art_id]
        num_paras = max(len(v) for v in labels.values())
        print(f"\n## {name}（{num_paras} 段）\n")

        # --- 每个框架的转换点 ---
        print("### 叙事弧线转换位置")
        print()
        print(f"{'框架':<12} {'段落数':>6} {'转换次数':>6}  转换段落")
        print("-" * 60)

        for fw_name in ["起承转合", "三幕结构", "情感曲线"]:
            if fw_name not in labels:
                continue
            roles = labels[fw_name]
            trans = find_transitions(roles)
            trans_desc = ", ".join(
                f"L{t+1}({roles[t]})→({roles[t]})" for t in trans[:5]
            )
            if len(trans) > 5:
                trans_desc += "…"
            elif not trans:
                trans_desc = "无转换"
            print(f"{fw_name:<12} {len(roles):>6} {len(trans):>6}  {trans_desc}")

        # --- 半段标记位置对比 ---
        print()
        print("### 各阶段覆盖的段落范围（first → last）")
        print()

        for fw_name in ["起承转合", "三幕结构", "情感曲线"]:
            if fw_name not in labels:
                continue
            roles = labels[fw_name]
            role_map = FRAMEWORK_MAPS[fw_name]
            hp = find_half_points(roles, role_map)
            print(f"**{fw_name}**")
            for role, val in sorted(role_map.items(), key=lambda x: x[1]):
                f = hp["first"].get(role, "-")
                l = hp["last"].get(role, "-")
                if f != "-":
                    pct_f = f / num_paras * 100
                    pct_l = l / num_paras * 100
                    print(f"  {role:<6} L{f:>3}({pct_f:>4.0f}%) → L{l:>3}({pct_l:>4.0f}%)  宽度={pct_l-pct_f:>4.0f}%")
                else:
                    print(f"  {role:<6} 未出现")
            print()

        # --- 关键叙事 beat 对齐度 ---
        print("### 关键叙事 Beat 对齐度")
        print()
        print('测量三个框架在"文章前 25%、中段 50%、后 25%"的角色分布偏差。')
        print()

        quarter = max(num_paras // 4, 1)
        for fw_name in ["起承转合", "三幕结构", "情感曲线"]:
            if fw_name not in labels:
                continue
            roles = labels[fw_name]
            role_map = FRAMEWORK_MAPS[fw_name]
            q1 = roles[:quarter]
            q2 = roles[quarter : 3 * quarter]
            q3 = roles[3 * quarter :]
            avg1 = sum(role_map.get(r, 0) for r in q1) / len(q1) if q1 else 0
            avg2 = sum(role_map.get(r, 0) for r in q2) / len(q2) if q2 else 0
            avg3 = sum(role_map.get(r, 0) for r in q3) / len(q3) if q3 else 0
            max_val = max(role_map.values())
            print(
                f"{fw_name:<12} 前25%={avg1/max_val:.2f}  中50%={avg2/max_val:.2f}  后25%={avg3/max_val:.2f}"
            )

        print("\n" + "=" * 70)


if __name__ == "__main__":
    analyze()
