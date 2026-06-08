#!/usr/bin/env python3
"""
p07 — 母题一致性检验实验

验证以母题为约束生成多场景文本时，母题能否保持一致性和连贯性。
"""
import json
from pathlib import Path

from src.config import GALLERY_ROOT, DATA_DIR
from src.infra import call_llm, call_llm_openai, clean_json, cache_or_compute, cache_or_compute_text, load_motif_yaml
from src.prompts import load_prompt

RESULTS_DIR = DATA_DIR / "p07"
TEMPERATURE = 0.8

SCENE_TEMPLATES = [
    {"id": "scene1", "name": "咖啡厅初遇", "type": "静态室内", "desc": "一个下雨的傍晚，主角走进一家安静的咖啡厅避雨。在靠窗的位置，她看到了一个熟悉的身影——是多年前有过一面之缘的人。"},
    {"id": "scene2", "name": "雨天再次相遇", "type": "动态室外", "desc": "又下雨了。主角在街角避雨，恰好遇到上次在咖啡厅见过的那个人。两人一起等雨停。"},
    {"id": "scene3", "name": "日常帮忙", "type": "静态室内", "desc": "主角在办公室加班，那个人来帮忙整理文件或处理工作。两人在安静的空间里共处。"},
    {"id": "scene4", "name": "夜晚散步", "type": "动态室外", "desc": "工作结束后，两人一起在夜色中散步。路灯下，影子被拉得很长。"},
    {"id": "scene5", "name": "表白时刻", "type": "任意", "desc": "在某个安静的地方，主角终于鼓起勇气，说出了藏在心里的话。"},
    {"id": "scene6", "name": "KTV 唱歌", "type": "动态室内", "desc": "朋友们约了一间 KTV 包厢。麦克风传到主角手中，她犹豫了一下，点了一首对他们有特殊意义的歌。音乐响起时，两个人的眼神在昏暗的灯光下交汇。"},
    {"id": "scene7", "name": "共同起草声明", "type": "静态室内", "desc": "主角和那个人需要一起起草一份公开声明。两人坐在电脑前，一个打字一个在旁边看着，反复修改措辞。不知不觉，窗外的天已经黑了。"},
    {"id": "scene8", "name": "朋友们的反应", "type": "任意", "desc": "主角的朋友们发现了她和那个人的事情。闺蜜拉着她追问细节，同事在茶水间窃窃私语，论坛上出现了匿名的讨论帖——所有旁观者都成了这段关系的见证者和评论者。"},
    {"id": "scene9", "name": "独自加班到深夜", "type": "静态室内", "desc": "办公室只剩主角一个人。窗外的城市灯火通明，她打开手机相册，翻到一张旧照片。她放下手机，揉了揉太阳穴，给自己倒了杯水，却端着杯子发呆了好几分钟。"},
]

ABSTRACT_MOTIF_ACTIONS: dict[str, str] = {
    "孤独": "写一段内心独白，让角色觉得无人可说、说不出来——手势和沉默比台词承载更多情感",
    "旁观者": "在场景中插入一个第三方角色的评论或反应（闺蜜/室友/同事/论坛网友）",
    "旁观者的缺席与在场": "在场景中插入一个第三方角色的评论或反应（闺蜜/室友/同事/论坛网友）",
    "歌声": "让一首具体的歌成为情感载体——点歌、听到某首歌、歌词引起回忆或对话",
    "随身携带的温柔": "让一个角色在另一个角色需要时恰好掏出某个随身物品（纸巾/毛巾/外套/创可贴）",
    "协作书写": "让两个角色一起修改同一份文本（声明/文档/帖子/信件），在文字修改中推进情感",
}


def build_motif_description(motifs: list[dict]) -> str:
    lines = []
    for i, m in enumerate(motifs):
        lines.append(f"{i+1}. {m['title']}：{m.get('description', '')}")
        action = ABSTRACT_MOTIF_ACTIONS.get(m["title"])
        if action:
            lines.append(f"   → 写作建议：{action}")
    return "\n".join(lines)


def generate_scene(scene: dict, motifs: list[dict] | None, style: str) -> str:
    motif_text = ""
    if motifs:
        motif_desc = build_motif_description(motifs)
        motif_text = f"\n请在写作中自然体现以下母题：\n{motif_desc}\n母题是贯穿叙事的重复性主题元素，而非需要逐字逐句插入的标签。不要刻意提及母题名称本身，而是通过角色行为、对话和细节来体现。\n"
    prompt = load_prompt("p07/generate_scene", style_name=style, scene_desc=scene["desc"], motif_text=motif_text)
    raw = call_llm(prompt, "你是一个专业的小说作家。只输出正文。", temperature=TEMPERATURE)
    return raw.strip()


def extract_motifs_from_text(text: str) -> list[dict]:
    sample = text[:2000]
    prompt = load_prompt("p07/extract_motifs_scene", sample=sample)
    raw = call_llm(prompt, "你是一个专业的叙事学分析助手。只输出 JSON。", temperature=0.3)
    return json.loads(clean_json(raw)).get("motifs", [])


def extract_motifs_cross_validate(text: str) -> list[dict]:
    sample = text[:2000]
    prompt = load_prompt("p07/extract_motifs_scene", sample=sample)
    try:
        raw = call_llm_openai(prompt, "你是一个专业的叙事学分析助手。只输出 JSON。", temperature=0.3)
        return json.loads(clean_json(raw)).get("motifs", [])
    except Exception:
        return []


def llm_motif_match(detected_title: str, target_title: str, target_description: str) -> bool:
    prompt = load_prompt("p07/llm_motif_match",
        detected_title=detected_title, target_title=target_title, target_description=target_description)
    try:
        raw = call_llm(prompt, "你是一个叙事学分析助手。只输出 yes 或 no。", temperature=0.1)
        return raw.strip().lower() == "yes"
    except Exception:
        return False


def compute_alignment(detected: list[dict], target_titles: set[str], target_motifs: list[dict] | None = None) -> float:
    if not target_titles:
        return 0.0
    target_map = {m["title"]: m.get("description", "") for m in (target_motifs or [])}
    detected_titles = [m["title"] for m in detected]
    matched = 0
    for target in target_titles:
        desc = target_map.get(target, "")
        if any(llm_motif_match(dt, target, desc) for dt in detected_titles):
            matched += 1
    return min(matched / len(target_titles), 1.0)


def main():
    print("=" * 60)
    print("p07 — 母题一致性检验实验")
    print("=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)
    generated_dir = RESULTS_DIR / "generated"
    detection_dir = RESULTS_DIR / "motif_detection"
    generated_dir.mkdir(exist_ok=True)
    detection_dir.mkdir(exist_ok=True)

    urban_motifs = load_motif_yaml(GALLERY_ROOT / "urban-romance" / "motif.yaml")
    campus_motifs = load_motif_yaml(GALLERY_ROOT / "campus-romance" / "motif.yaml")
    urban_list, campus_list = urban_motifs.get("motifs", []), campus_motifs.get("motifs", [])
    urban_titles = {m["title"] for m in urban_list}
    campus_titles = {m["title"] for m in campus_list}

    all_results = []
    configs = [("urban", urban_list, urban_titles, "都市言情"), ("campus", campus_list, campus_titles, "校园言情")]

    for series, motif_list, target_titles, style_name in configs:
        print(f"\n{'='*40}\n约束组: {style_name} ({len(motif_list)} 个母题)\n{'='*40}")
        for scene in SCENE_TEMPLATES:
            text = cache_or_compute_text(
                generated_dir / f"constrained_{series}_{scene['id']}.txt",
                lambda s=scene: generate_scene(s, motif_list, style_name),
                f"生成 {scene['name']}", verbose=True,
            )
            detected = cache_or_compute(
                detection_dir / f"constrained_{series}_{scene['id']}.json",
                lambda t=text: {"motifs": extract_motifs_from_text(t)},
                verbose=False,
            )
            alignment = compute_alignment(detected.get("motifs", []), target_titles, motif_list)
            all_results.append({"group": f"constrained_{series}", "scene": scene["name"], "alignment": alignment,
                "detected_count": len(detected.get("motifs", [])), "target_count": len(target_titles),
                "detected_titles": [m["title"] for m in detected.get("motifs", [])]})
            print(f"      吻合度: {alignment*100:.0f}%")

        for scene in SCENE_TEMPLATES:
            text = cache_or_compute_text(
                generated_dir / f"control_{series}_{scene['id']}.txt",
                lambda s=scene: generate_scene(s, None, style_name),
                f"生成对照 {scene['name']}", verbose=True,
            )
            detected = cache_or_compute(
                detection_dir / f"control_{series}_{scene['id']}.json",
                lambda t=text: {"motifs": extract_motifs_from_text(t)},
                verbose=False,
            )
            alignment = compute_alignment(detected.get("motifs", []), target_titles, motif_list)
            all_results.append({"group": f"control_{series}", "scene": scene["name"], "alignment": alignment,
                "detected_count": len(detected.get("motifs", [])), "target_count": len(target_titles),
                "detected_titles": [m["title"] for m in detected.get("motifs", [])]})

    # Cross-validation
    cross_validated = []
    if any(os.environ.get("OPENAI_API_KEY") for _ in [1]):
        for series, motif_list, target_titles, style_name in configs:
            for scene in SCENE_TEMPLATES:
                path = generated_dir / f"constrained_{series}_{scene['id']}.txt"
                if not path.exists():
                    continue
                text = path.read_text("utf-8")
                cv_detected = cache_or_compute(
                    detection_dir / f"crossval_{series}_{scene['id']}.json",
                    lambda: {"motifs": extract_motifs_cross_validate(text)},
                    verbose=False,
                )
                cv_alignment = compute_alignment(cv_detected.get("motifs", []), target_titles, motif_list)
                cross_validated.append({"series": series, "scene": scene["name"], "cv_alignment": cv_alignment})

        if cross_validated:
            avg_cv = sum(r["cv_alignment"] for r in cross_validated) / len(cross_validated)
            avg_p = sum(r["alignment"] for r in all_results if r["group"].startswith("constrained_")) / max(1, len([r for r in all_results if r["group"].startswith("constrained_")]))
            print(f"\n  交叉验证约束组: {avg_cv*100:.0f}% (DeepSeek: {avg_p*100:.0f}%, 差异: {abs(avg_cv-avg_p)*100:.0f}%)")
            print(f"  {'✅ 结果可信' if abs(avg_cv-avg_p)*100 <= 15 else '⚠️ 差异 > 15%，优先采信 GPT-4o-mini'}")

    print(f"\n{'='*60}\np07 分析报告：母题一致性检验\n{'='*60}")
    for series, target_titles, style in [("urban", urban_titles, "都市言情"), ("campus", campus_titles, "校园言情")]:
        constrained = [r for r in all_results if r["group"] == f"constrained_{series}"]
        control = [r for r in all_results if r["group"] == f"control_{series}"]
        avg_c = sum(r["alignment"] for r in constrained) / len(constrained) if constrained else 0
        avg_ct = sum(r["alignment"] for r in control) / len(control) if control else 0
        print(f"\n## {style}")
        print(f"  约束组平均吻合度: {avg_c*100:.0f}%")
        print(f"  对照组平均吻合度: {avg_ct*100:.0f}%")
        print(f"  提升: {(avg_c-avg_ct)*100:+.0f} 百分点")

    report_data = {
        "results": all_results,
        "cross_validation": {"cv_results": cross_validated,
            "avg_cv_alignment": sum(r["cv_alignment"] for r in cross_validated) / len(cross_validated) if cross_validated else 0},
    }
    cache_or_compute(RESULTS_DIR / "consistency_report.json", lambda: report_data, verbose=False)
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    import os
    main()
