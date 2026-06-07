"""p17 实验管线 — 写作契约 vs 读者回响

脚本流程：
1. 加载文本点定义、写作契约、p16 读者数据、画像定义
2. 对每个文本点：
   a. Step 1: 契约标注（LLM）
   b. Step 2: 读者回响映射（数据处理）
   c. Step 3: 材料并排（LLM，无分析句）
   d. Step 4: 作者反馈（交互式）
3. 运行验证
4. 输出结果
"""
import sys, json, re
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from packages.io import save_json, load_yaml
from config import TEXT_POINTS, FICTION_ROOT, P16_OUTPUT, DATA_OUTPUT
from contract import load_contracts, annotate as contract_annotate
from reader_mapping import load_p16_data, load_profiles, map_reader_response
from side_by_side import generate_side_by_side
from feedback import collect_feedback


def read_scene_text(scene_file):
    """读取场景文本."""
    path = FICTION_ROOT / scene_file
    if not path.exists():
        print(f"  [警告] 场景文件不存在: {path}")
        return ""
    text = path.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def check_no_overstepping(text):
    """检查输出是否包含越界句（分析/建议/结论句式）。

    注意：排除以下情况：
    - 固定结尾句"这是作者需要自己看的东西"
    - 直接引用的契约原文（如 style.yaml 中的"可以"/"需要"/"应该"）
    """
    # 排除固定结尾
    _cleaned = text.replace("这是作者需要自己看的东西", "")

    # 核心禁止句式：分析、总结、建议
    forbidden_patterns = [
        r"这意味着",
        r"这说明",
        r"因此[^,]",
        r"所以[^,]",
        r"建议",
        r"总之[,，]",
        r"综上所述",
    ]
    violations = []
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, _cleaned)
        for m in matches:
            violations.append(m)
    return violations


def compute_statistics(reader_response):
    """计算读者回响的统计摘要。"""
    ratings = reader_response.get("scene_ratings", {})
    if not ratings:
        return {}

    stats = {}
    fields = ["writing_quality", "emotional_impact", "character_realism", "cliche_level"]
    for f in fields:
        vals = []
        for pid in ratings:
            v = ratings[pid].get(f)
            if v is not None:
                vals.append(v)
        if vals:
            import numpy as np
            stats[f] = {
                "mean": round(float(np.mean(vals)), 2),
                "std": round(float(np.std(vals)), 2),
                "min": min(vals),
                "max": max(vals),
            }
    return stats


def run():
    print("=" * 60)
    print("p17 — 写作契约 vs 读者回响：单点反思")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)

    # 加载数据
    print("\n── 加载数据 ──")
    contracts = load_contracts()
    print(f"  style.yaml: {len(contracts['style_yaml'].get('styles', []))} 个维度")
    print(f"  motif.yaml: {len(contracts['motif_yaml'].get('motifs', []))} 个母题")
    print(f"  story.yaml: {len(contracts['story_yaml'].get('characters', []))} 个角色")

    p16_raw_path = P16_OUTPUT / "e4-1_raw.json"
    p16_data = load_p16_data(p16_raw_path)
    print(f"  p16 评价数据: {len(p16_data)} 条记录")

    profiles_path = P16_OUTPUT.parent / "input" / "profiles.json"
    profile_map = load_profiles(profiles_path)
    print(f"  画像定义: {len(profile_map)} 个")

    # 逐文本点执行
    results = []
    all_verifications = []

    for tp in TEXT_POINTS:
        print(f"\n{'─' * 50}")
        print(f"处理文本点: {tp['id']} — {tp['location']}")
        print(f"  类型: {tp['type']}")
        print(f"  原文: {tp['quote'][:50]}...")

        # Step 1: 契约标注（LLM）
        print(f"\n  Step 1: 契约标注...")
        contract_result = contract_annotate(tp, contracts)
        if "error" in contract_result:
            print(f"  [错误] 契约标注失败: {contract_result['error']}")
        else:
            style_touched = len(contract_result.get("style", {}).get("touched_dimensions", []))
            motif_touched = len(contract_result.get("motif", {}).get("touched_motifs", []))
            story_touched = len(contract_result.get("story", {}).get("touched_characters", []))
            tensions = len(contract_result.get("story", {}).get("touched_tensions", []))
            print(f"    style: {style_touched} 个维度, motif: {motif_touched} 个, "
                  f"角色: {story_touched} 个, tension: {tensions} 个")
        # 缓存
        save_json(DATA_OUTPUT / f"{tp['id']}_contract.json", contract_result)

        # Step 2: 读者回响映射
        print(f"  Step 2: 读者回响映射（p16 text_id={tp['p16_text_id']}）...")
        reader_response = map_reader_response(tp, p16_data, profile_map)
        stats = compute_statistics(reader_response)
        if stats:
            for f, s in stats.items():
                print(f"    {f}: mean={s['mean']}, std={s['std']}, range=[{s['min']}, {s['max']}]")
        save_json(DATA_OUTPUT / f"{tp['id']}_reader.json", reader_response)

        # Step 3: 材料并排（LLM，核心步骤）
        print(f"  Step 3: 材料并排...")
        scene_text = read_scene_text(tp["scene_file"])
        side_by_side_output = generate_side_by_side(
            tp, contract_result, reader_response, profile_map
        )
        print(f"    输出长度: {len(side_by_side_output)} 字符")

        # 验证：不越界检查
        violations = check_no_overstepping(side_by_side_output)
        if violations:
            print(f"  ⚠️  越界句式检测: {violations}")
        else:
            print(f"  ✅ 不越界检查通过")

        # 保存输出
        save_json(DATA_OUTPUT / f"{tp['id']}_side_by_side.json", {
            "text_point_id": tp["id"],
            "output": side_by_side_output,
            "no_overstepping": len(violations) == 0,
            "violations": violations,
        })

        # Step 4: 作者反馈（交互式）
        feedback = collect_feedback(
            tp, side_by_side_output,
            DATA_OUTPUT / f"{tp['id']}_feedback.json"
        )

        # 收集验证结果
        verification = {
            "text_point": tp["id"],
            "type": tp["type"],
            "contract_annotation_success": "error" not in contract_result,
            "reader_data_available": bool(reader_response.get("scene_ratings")),
            "no_overstepping": len(violations) == 0,
            "overstepping_violations": violations,
        }
        all_verifications.append(verification)
        results.append({
            "id": tp["id"],
            "location": tp["location"],
            "type": tp["type"],
            "contract": contract_result,
            "reader_response": reader_response,
            "side_by_side": side_by_side_output,
            "verification": verification,
        })

    # 汇总验证
    print(f"\n{'=' * 60}")
    print("验证汇总")
    print(f"{'=' * 60}")

    total = len(TEXT_POINTS)
    contract_ok = sum(1 for v in all_verifications if v["contract_annotation_success"])
    reader_ok = sum(1 for v in all_verifications if v["reader_data_available"])
    no_overstep = sum(1 for v in all_verifications if v["no_overstepping"])

    print(f"  契约标注成功: {contract_ok}/{total}")
    print(f"  读者数据可用: {reader_ok}/{total}")
    print(f"  不越界通过: {no_overstep}/{total}")

    for v in all_verifications:
        status = "✅" if (v["contract_annotation_success"] and v["reader_data_available"] and v["no_overstepping"]) else "⚠️"
        print(f"  {status} {v['text_point']} ({v['type']}): "
              f"契约={'✅' if v['contract_annotation_success'] else '❌'} "
              f"数据={'✅' if v['reader_data_available'] else '❌'} "
              f"不越界={'✅' if v['no_overstepping'] else '❌'}")

    # 输出完整结果
    summary = {
        "experiment": "p17 — 写作契约 vs 读者回响：单点反思",
        "timestamp": datetime.now().isoformat(),
        "text_points": len(TEXT_POINTS),
        "verification": {
            "contract_annotation_success": f"{contract_ok}/{total}",
            "reader_data_available": f"{reader_ok}/{total}",
            "no_overstepping": f"{no_overstep}/{total}",
        },
        "per_point": all_verifications,
    }
    save_json(DATA_OUTPUT / "summary.json", summary)

    print(f"\n结果已保存到: {DATA_OUTPUT}")
    print("完成。")

    return results, summary


if __name__ == "__main__":
    run()
