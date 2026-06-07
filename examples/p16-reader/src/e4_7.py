"""E4-7 — 基于多画像评价的局部修改建议（Rewrite）

自包含 Reflect+Rewrite：
  Step 1: 薄弱点定位 — 对比目标画像评分 vs 历史均值，按差距排序
  Step 2: 生成修改 — 2 prompt 风格，最小改动约束
  Step 3: 验证 — E4-1 评价引擎 before/after 对比

设计文档：docs/experiments/E4-7-rewrite-design.md
"""
import sys, json, re
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from packages.io import save_json, load_json
from packages.llm import call_llm

# ── Phase I 文本 ──
PHASE1_TIDS = ["4.1", "7.2", "9.1", "2.3", "10.3", "1.2"]

# ── 用于验证的新文本（来自 E4-5）──
NEW_TIDS = ["2.1", "4.2", "6.2", "8.2"]

PROFILES = ["P1", "P2", "P3", "P4", "P5"]
EVAL_FIELDS = ["writing_quality", "emotional_impact", "character_realism", "cliche_level"]
N_CALLS = 3
TEMPERATURE = 0.3

FICTION_ROOT = Path("/home/iguo/repos/quanttide/domains/quanttide-write/assets/fiction")
FICTION_PATHS = {
    "4.1": "职场言情/4_成稿/1_1_咖啡厅重逢.md",
    "7.2": "职场言情/4_成稿/7_2_公园拥抱.md",
    "9.1": "职场言情/4_成稿/9_1_家里吃火锅.md",
    "2.3": "职场言情/4_成稿/2_3_傍晚小龙虾.md",
    "10.3": "职场言情/4_成稿/10_3_阳台看星星.md",
    "1.2": "职场言情/4_成稿/1_2_深夜失眠.md",
    "2.1": "职场言情/4_成稿/2_1_展会再遇.md",
    "4.2": "职场言情/4_成稿/4_2_夜市约会.md",
    "6.2": "职场言情/4_成稿/6_2_海边散步.md",
    "8.2": "职场言情/4_成稿/8_2_酒吧表白.md",
}


def _read_text(tid: str) -> str:
    path = FICTION_ROOT / FICTION_PATHS[tid]
    text = path.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


# ── Step 1: 薄弱点定位 ──

def _compute_profile_history(e4_1_raw: list[dict]) -> dict:
    """计算每个画像在 Phase I 文本上的各维度历史均值。

    返回: {pid: {field: mean_score}}
    """
    history = {}
    for pid in PROFILES:
        history[pid] = {}
        for field in EVAL_FIELDS:
            vals = [r[field] for r in e4_1_raw
                    if r["profile"] == pid and r["text_id"] in PHASE1_TIDS
                    and isinstance(r.get(field), (int, float))]
            history[pid][field] = float(np.mean(vals)) if vals else 3.0
    return history


def _compute_noise_baseline(e4_1_raw: list[dict]) -> dict:
    """计算每个画像 × 维度的 call 间标准差（噪声基线）。

    返回: {pid: {field: sd}}
    """
    noise = {}
    for pid in PROFILES:
        noise[pid] = {}
        for field in EVAL_FIELDS:
            sds = []
            for tid in PHASE1_TIDS:
                vals = [r[field] for r in e4_1_raw
                        if r["profile"] == pid and r["text_id"] == tid
                        and isinstance(r.get(field), (int, float))]
                if len(vals) >= 2:
                    sds.append(float(np.std(vals, ddof=1)))
            noise[pid][field] = float(np.mean(sds)) if sds else 0.5
    return noise


def _locate_weakness(
    e4_1_raw: list[dict],
    target_pid: str,
    text_id: str,
    history: dict,
) -> dict | None:
    """找到目标画像在给定文本上的薄弱维度。

    返回: {target_profile, target_dimension, current_score, historical_mean, gap, relevant_segment}
    或 None（如果所有维度差距 < 0.5，无需修改）
    """
    # 当前文本上目标画像的各维度评分均值
    current = {}
    for field in EVAL_FIELDS:
        vals = [r[field] for r in e4_1_raw
                if r["profile"] == target_pid and r["text_id"] == text_id
                and isinstance(r.get(field), (int, float))]
        current[field] = float(np.mean(vals)) if vals else 3.0

    # 按与历史均值的差距降序排列
    gaps = []
    for field in EVAL_FIELDS:
        gap = abs(current[field] - history[target_pid][field])
        gaps.append((gap, field, current[field], history[target_pid][field]))

    gaps.sort(reverse=True, key=lambda x: x[0])
    best_gap, best_field, best_curr, best_hist = gaps[0]

    if best_gap < 0.5:
        return None  # 无需修改

    # 摘取最相关的段落（取文本的前 1/3 作为候选，实际应做更精细的定位，此处简化）
    text = _read_text(text_id)
    sents = re.split(r'[。！？\n]+', text)
    sents = [s.strip() for s in sents if len(s.strip()) > 5]
    # 取中间偏前的一段作为"薄弱段落的候选"
    mid = len(sents) // 3
    segment = "。".join(sents[max(0, mid-5):mid+5]) + "。"

    return {
        "text_id": text_id,
        "target_profile": target_pid,
        "target_dimension": best_field,
        "current_score": round(best_curr, 2),
        "historical_mean": round(best_hist, 2),
        "gap": round(best_gap, 2),
        "relevant_segment": segment[:800],  # 截断，控制 prompt 长度
    }


# ── Step 2: 生成修改 ──

REWRITE_SYSTEM = (
    "你是一个编辑助手。你的任务是对给定文本做最小改动的局部修改。"
    "只输出 JSON，不要有任何其他文字。"
)

PROMPT_STYLE_STRUCTURED = """根据以下信息修改文本，使修改后的版本更符合目标读者的偏好。

## 目标读者
{profile_desc}

## 需要修改的维度
{dimension_label}（当前评分: {current_score}，该读者历史均值: {target_score}，差距: {gap}）

{dimension_explanation}

## 原文片段
```
{segment}
```

## 约束
1. 最小改动：只改必要的位置，保持原文的场景结构和情感基调
2. 可执行：改动具体到"删除哪句话"或"加入什么内容"
3. 原因清楚：说明改了什么以及为什么

## 输出 JSON 格式
{{
  "target_profile": "{target_pid}",
  "target_dimension": "{dimension_field}",
  "original_segment": "原文片段（完整复制原文）",
  "suggested_rewrite": "修改后的完整片段",
  "what_changed": ["改动1", "改动2"],
  "why_for_reader": "为什么这么改"
}}
"""

PROMPT_STYLE_FREE = """你是一位经验丰富的编辑。现在有一篇小说片段，它在一项关键指标上让某类读者不满意。

目标读者：{profile_desc}
问题维度：{dimension_label}（当前 {current_score}，目标 {target_score}）

问题说明：这个维度的历史均值和当前值差距为 {gap}——也就是说，这篇文本在这个维度上远不如目标读者通常的接受水平。

请针对这个读者，对文本做最小幅度的修改，解决这个问题。

原文：
```
{segment}
```

输出 JSON（不要有其他文字）：
{{
  "target_profile": "{target_pid}",
  "target_dimension": "{dimension_field}",
  "original_segment": "(原文片段)",
  "suggested_rewrite": "(修改后的片段)",
  "what_changed": ["(改动列表)"],
  "why_for_reader": "(修改理由)"
}}
"""

DIMENSION_LABELS = {
    "writing_quality": "文笔质量",
    "emotional_impact": "情感冲击力",
    "character_realism": "角色真实感",
    "cliche_level": "套路感",
}

DIMENSION_EXPLANATIONS = {
    "writing_quality": "文笔：语言表达是否流畅、精准、有美感。目标读者对文字质量有一定要求。",
    "emotional_impact": "情感冲击：读者是否被场景打动。目标读者有较高的情感共鸣需求。",
    "character_realism": "角色真实感：角色的行为是否符合其性格设定，是否有内外动机的区别。目标读者要求角色有心理深度。",
    "cliche_level": "套路感：叙事模式是否过于常见。目标读者对套路非常敏感，一眼就能识别。",
}


def _generate_rewrite(weakness: dict, profiles: list[dict], style: int = 0) -> dict | None:
    """生成一个修改版本。style=0 用结构化 prompt，style=1 用自由式 prompt。"""
    pid = weakness["target_profile"]
    prof = next((p for p in profiles if p["id"] == pid), None)
    if not prof:
        return None

    label = prof.get("label", pid)
    desc = f"{label}（{prof.get('description', '')}）"
    dim = weakness["target_dimension"]
    dim_label = DIMENSION_LABELS.get(dim, dim)
    dim_explain = DIMENSION_EXPLANATIONS.get(dim, "")

    prompt = (PROMPT_STYLE_STRUCTURED if style == 0 else PROMPT_STYLE_FREE).format(
        profile_desc=desc,
        dimension_label=dim_label,
        dimension_field=dim,
        dimension_explanation=dim_explain,
        current_score=weakness["current_score"],
        target_score=weakness["historical_mean"],
        gap=weakness["gap"],
        segment=weakness["relevant_segment"],
        target_pid=pid,
    )

    raw = call_llm(prompt, system=REWRITE_SYSTEM, temperature=0.3)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"  JSON 解析失败: {pid}×{weakness['text_id']} style={style}")
        return None


# ── Step 3: 验证（用 E4-1 评价引擎）──

def _evaluate(profile: dict, text: str) -> dict:
    """对一个文本用给定画像做一次评价，返回评分 dict。"""
    from src.phase1.prompt_templates import build_evaluation_prompt
    prompt = build_evaluation_prompt(profile, text)
    raw = call_llm(prompt, temperature=TEMPERATURE)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("  评价 JSON 解析失败")
        return {}


# ── 主流程 ──

def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-7 — 基于多画像评价的局部修改建议（Rewrite）")
    print("=" * 60)

    # 加载数据
    e4_1_raw = load_json(results_dir / "e4-1_raw.json")
    profiles = load_json(data_dir / "profiles.json")
    profiles = [p for p in profiles if p["id"] != "P0"]
    profile_map = {p["id"]: p for p in profiles}

    # ── Step 1: 计算历史均值 + 噪声基线 ──
    print("\n── Step 1: 薄弱点定位 ──")
    history = _compute_profile_history(e4_1_raw)
    noise = _compute_noise_baseline(e4_1_raw)

    print("  画像历史均值（Phase I 6 篇文本）：")
    for pid in PROFILES:
        print(f"    {pid}: {history[pid]}")

    print("\n  噪声基线（call 间 SD）：")
    for pid in PROFILES:
        print(f"    {pid}: {{", end="")
        for f in EVAL_FIELDS:
            print(f" {f}={noise[pid][f]:.3f}", end="")
        print(" }")

    # 定位薄弱点：对 P1 和 P3 做
    target_profiles = ["P1", "P3"]
    weaknesses = []
    for pid in target_profiles:
        for tid in PHASE1_TIDS + NEW_TIDS:
            w = _locate_weakness(e4_1_raw, pid, tid, history)
            if w:
                weaknesses.append(w)
                print(f"  {pid}×{tid}: {w['target_dimension']} (差距={w['gap']})")
            else:
                print(f"  {pid}×{tid}: 无需修改")

    print(f"\n  共识别 {len(weaknesses)} 个薄弱点")

    # ── Step 2: 生成修改 ──
    print("\n── Step 2: 生成修改版本 ──")
    rewrites = []
    for w in weaknesses:
        for style in [0, 1]:
            r = _generate_rewrite(w, profiles, style=style)
            if r:
                r["style"] = style
                r["text_id"] = w["text_id"]
                r["target_profile"] = w["target_profile"]
                r["target_dimension"] = w["target_dimension"]
                r["gap"] = w["gap"]
                rewrites.append(r)
                print(f"  ✅ {w['target_profile']}×{w['text_id']} style={style}")

    # 保存修改版本
    rewrites_path = results_dir / "e4-7_rewrites.json"
    save_json(rewrites_path, rewrites)
    print(f"\n  已保存 {len(rewrites)} 个修改版本到 {rewrites_path.name}")

    # ── Step 3: 验证 ──
    print("\n── Step 3: 验证（before/after 对比）──")

    verifications = []
    for rw in rewrites:
        pid = rw["target_profile"]
        tid = rw["text_id"]
        dim = rw["target_dimension"]
        prof = profile_map[pid]

        # 修改前评分
        before_vals = [r[dim] for r in e4_1_raw
                       if r["profile"] == pid and r["text_id"] == tid
                       and isinstance(r.get(dim), (int, float))]
        before_mean = float(np.mean(before_vals)) if before_vals else None

        # 修改后评分（3 次调用）
        after_vals = []
        for c in range(N_CALLS):
            resp = _evaluate(prof, rw["suggested_rewrite"])
            val = resp.get(dim)
            if isinstance(val, (int, float)):
                after_vals.append(float(val))
        after_mean = float(np.mean(after_vals)) if after_vals else None

        # 噪声门槛
        sd = noise[pid].get(dim, 0.5)
        threshold = 2 * sd

        # 统计
        improvement = None
        improved = False
        if before_mean is not None and after_mean is not None:
            improvement = round(after_mean - before_mean, 2)
            improved = improvement >= threshold

        # 非目标维度检查
        other_dims = [f for f in EVAL_FIELDS if f != dim]
        dim_degraded = 0
        for od in other_dims:
            bv = [r[od] for r in e4_1_raw
                  if r["profile"] == pid and r["text_id"] == tid
                  and isinstance(r.get(od), (int, float))]
            bm = float(np.mean(bv)) if bv else None
            av = [resp.get(od) for c in range(N_CALLS)
                  for resp in [_evaluate(prof, rw["suggested_rewrite"])]
                  if isinstance(resp.get(od), (int, float))]
            am = float(np.mean(av)) if av else None
            if bm is not None and am is not None:
                diff = am - bm
                od_sd = noise[pid].get(od, 0.5)
                if diff < -2 * od_sd:
                    dim_degraded += 1

        v = {
            "target_profile": pid,
            "text_id": tid,
            "target_dimension": dim,
            "style": rw["style"],
            "before_mean": before_mean,
            "after_mean": after_mean,
            "improvement": improvement,
            "threshold": round(threshold, 3),
            "improved": improved,
            "other_dimensions_degraded": dim_degraded,
            "pass": improved and dim_degraded <= 1,
        }
        verifications.append(v)
        status = "✅" if v["pass"] else "❌"
        print(f"  {status} {pid}×{tid} {dim}: "
              f"{before_mean}→{after_mean} (Δ={improvement}, 门槛={threshold:.2f}), "
              f"非目标维度降级={dim_degraded}")

    # ── 汇总 ──
    total = len(verifications)
    passed = sum(1 for v in verifications if v["pass"])
    dim_improved = sum(1 for v in verifications if v["improved"])
    dim_degraded_ok = sum(1 for v in verifications if v["other_dimensions_degraded"] <= 1)

    summary = {
        "total_rewrites": total,
        "passed": passed,
        "dim_improved": dim_improved,
        "dim_improved_ratio": round(dim_improved / total, 3) if total else 0,
        "dim_improved_pass": dim_improved / total >= 2/3 if total else False,
        "dim_degraded_ok": dim_degraded_ok,
        "dim_degraded_ok_ratio": round(dim_degraded_ok / total, 3) if total else 0,
        "dim_degraded_pass": dim_degraded_ok / total >= 0.8 if total else False,
        "overall_pass": (dim_improved / total >= 2/3 and dim_degraded_ok / total >= 0.8) if total else False,
        "verifications": verifications,
        "noise_baseline": noise,
    }
    save_json(results_dir / "e4-7_rewrite_summary.json", summary)

    print(f"\n── 汇总 ──")
    print(f"  总修改版本: {total}")
    print(f"  目标维度提升 ≥ 2×SD: {dim_improved}/{total} ({summary['dim_improved_ratio']:.1%}) {'✅' if summary['dim_improved_pass'] else '❌'} (标准 ≥ 2/3)")
    print(f"  非目标维度降级 ≤ 1: {dim_degraded_ok}/{total} ({summary['dim_degraded_ok_ratio']:.1%}) {'✅' if summary['dim_degraded_pass'] else '❌'} (标准 ≥ 80%)")
    print(f"  整体通过: {'✅' if summary['overall_pass'] else '❌'}")

    return summary


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "p16-reader"
    run(_base / "data" / "input", _base / "data" / "output")
