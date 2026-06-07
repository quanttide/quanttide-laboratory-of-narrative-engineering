"""p17 实验管线 — 写作契约 vs 读者回响

批处理模式（run_batch）：
  加载数据 → Step 1-3 → 保存 → 验证

反馈模式（run_feedback）：
  加载已保存的材料并排输出 → Step 4 逐点收集作者反馈
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
    path = FICTION_ROOT / scene_file
    if not path.exists():
        return ""
    text = path.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def check_no_overstepping(text):
    _cleaned = text.replace("这是作者需要自己看的东西", "")
    forbidden_patterns = [
        r"这意味着", r"这说明", r"因此[^,]", r"所以[^,]",
        r"建议", r"总之[,，]", r"综上所述",
    ]
    violations = []
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, _cleaned)
        for m in matches:
            violations.append(m)
    return violations


def compute_statistics(reader_response):
    ratings = reader_response.get("scene_ratings", {})
    if not ratings:
        return {}
    stats = {}
    fields = ["writing_quality", "emotional_impact", "character_realism", "cliche_level"]
    for f in fields:
        vals = [ratings[pid].get(f) for pid in ratings if ratings[pid].get(f) is not None]
        if vals:
            import numpy as np
            stats[f] = {
                "mean": round(float(np.mean(vals)), 2),
                "std": round(float(np.std(vals)), 2),
                "min": min(vals), "max": max(vals),
            }
    return stats


def run_batch():
    """Step 1-3: 契约标注 + 读者回响映射 + 材料并排（无交互）"""
    print("=" * 60)
    print("p17 — 写作契约 vs 读者回响：单点反思（批处理）")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)

    print("\n── 加载数据 ──")
    contracts = load_contracts()
    print(f"  style.yaml: {len(contracts['style_yaml'].get('styles', []))} 个维度")
    print(f"  motif.yaml: {len(contracts['motif_yaml'].get('motifs', []))} 个母题")
    print(f"  story.yaml: {len(contracts['story_yaml'].get('characters', []))} 个角色")

    p16_data = load_p16_data(P16_OUTPUT / "e4-1_raw.json")
    print(f"  p16 评价数据: {len(p16_data)} 条记录")

    profile_map = load_profiles(P16_OUTPUT.parent / "input" / "profiles.json")
    print(f"  画像定义: {len(profile_map)} 个")

    all_verifications = []

    for tp in TEXT_POINTS:
        print(f"\n{'─' * 50}")
        print(f"处理: {tp['id']} — {tp['location']} ({tp['type']})")
        print(f"  原文: {tp['quote'][:50]}...")

        # Step 1
        print(f"  Step 1: 契约标注...")
        contract_result = contract_annotate(tp, contracts)
        if "error" in contract_result:
            print(f"  [错误] {contract_result['error']}")
        else:
            s = len(contract_result.get("style", {}).get("touched_dimensions", []))
            m = len(contract_result.get("motif", {}).get("touched_motifs", []))
            c = len(contract_result.get("story", {}).get("touched_characters", []))
            t = len(contract_result.get("story", {}).get("touched_tensions", []))
            print(f"    style: {s} 维度, motif: {m}, 角色: {c}, tension: {t}")
        save_json(DATA_OUTPUT / f"{tp['id']}_contract.json", contract_result)

        # Step 2
        print(f"  Step 2: 读者回响...")
        reader_response = map_reader_response(tp, p16_data, profile_map)
        stats = compute_statistics(reader_response)
        if stats:
            for f, s in stats.items():
                print(f"    {f}: mean={s['mean']}, std={s['std']}, range=[{s['min']}, {s['max']}]")
        save_json(DATA_OUTPUT / f"{tp['id']}_reader.json", reader_response)

        # Step 3
        print(f"  Step 3: 材料并排...")
        side_by_side_output = generate_side_by_side(
            tp, contract_result, reader_response, profile_map
        )
        print(f"    输出: {len(side_by_side_output)} 字符")

        violations = check_no_overstepping(side_by_side_output)
        if violations:
            print(f"  ⚠️  越界检测: {violations}")
        else:
            print(f"  ✅ 不越界通过")

        save_json(DATA_OUTPUT / f"{tp['id']}_side_by_side.json", {
            "text_point_id": tp["id"], "output": side_by_side_output,
            "no_overstepping": len(violations) == 0, "violations": violations,
        })

        all_verifications.append({
            "text_point": tp["id"], "type": tp["type"],
            "contract_annotation_success": "error" not in contract_result,
            "reader_data_available": bool(reader_response.get("scene_ratings")),
            "no_overstepping": len(violations) == 0,
            "overstepping_violations": violations,
        })

    # 汇总
    total = len(TEXT_POINTS)
    ok = lambda k: sum(1 for v in all_verifications if v[k])
    print(f"\n{'=' * 60}")
    print("验证汇总")
    print(f"{'=' * 60}")
    print(f"  契约标注: {ok('contract_annotation_success')}/{total}")
    print(f"  读者数据: {ok('reader_data_available')}/{total}")
    print(f"  不越界:   {ok('no_overstepping')}/{total}")
    for v in all_verifications:
        ok3 = v["contract_annotation_success"] and v["reader_data_available"] and v["no_overstepping"]
        print(f"  {'✅' if ok3 else '⚠️'} {v['text_point']} ({v['type']}): "
              f"契约={'✅' if v['contract_annotation_success'] else '❌'} "
              f"数据={'✅' if v['reader_data_available'] else '❌'} "
              f"不越界={'✅' if v['no_overstepping'] else '❌'}")

    save_json(DATA_OUTPUT / "summary.json", {
        "experiment": "p17 — 写作契约 vs 读者回响",
        "timestamp": datetime.now().isoformat(),
        "text_points": len(TEXT_POINTS),
        "verification": {
            "contract": f"{ok('contract_annotation_success')}/{total}",
            "reader_data": f"{ok('reader_data_available')}/{total}",
            "no_overstepping": f"{ok('no_overstepping')}/{total}",
        },
        "per_point": all_verifications,
    })
    print(f"\n已保存到: {DATA_OUTPUT}")
    print("要逐点反馈，运行: python -m src feedback")


def run_feedback():
    """Step 4: 逐点展示已保存的材料并收集作者反馈。"""
    print("=" * 60)
    print("p17 — Step 4: 作者反馈")
    print("=" * 60)
    print()

    feedback_results = []
    for tp in TEXT_POINTS:
        f = DATA_OUTPUT / f"{tp['id']}_side_by_side.json"
        if not f.exists():
            print(f"⚠️ {tp['id']} 材料并排未找到，先运行 python -m src")
            continue

        data = json.loads(f.read_text())
        output = data["output"]

        feedback = collect_feedback(tp, output, DATA_OUTPUT / f"{tp['id']}_feedback.json")
        feedback_results.append(feedback)
        print()

    # 汇总
    total = len(feedback_results)
    submitted = [f for f in feedback_results if not f.get("skipped", True)]
    print("=" * 60)
    print("反馈汇总")
    print("=" * 60)
    print(f"  已反馈: {len(submitted)}/{total}")
    for f in feedback_results:
        if f.get("skipped"):
            print(f"  ⏭️ {f['text_point_id']}: 跳过")
        else:
            print(f"  ✅ {f['text_point_id']}: {f['choice']} — {f['choice_label']}")
    print()

    if len(submitted) < total:
        remaining = [tp["id"] for tp in TEXT_POINTS
                     if not any(f.get("text_point_id") == tp["id"] and not f.get("skipped")
                               for f in feedback_results)]
        if remaining:
            print(f"  未反馈: {', '.join(remaining)}")
            print(f"  再次运行: python -m src feedback")


if __name__ == "__main__":
    run_batch()
