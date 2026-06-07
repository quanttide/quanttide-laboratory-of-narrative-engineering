#!/usr/bin/env python3
"""
p07 — 母题一致性检验实验

验证以母题为约束生成多场景文本时，母题能否保持一致性和连贯性。
"""
import json
import os
import sys
import random
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import REPO_ROOT, GALLERY_ROOT, DATA_DIR

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
RESULTS_DIR = DATA_DIR / "p07"

TEMPERATURE = 0.8  # 生成与检测统一使用

SCENE_TEMPLATES = [
    {"id": "scene1", "name": "咖啡厅初遇", "type": "静态室内", "desc": "一个下雨的傍晚，主角走进一家安静的咖啡厅避雨。在靠窗的位置，她看到了一个熟悉的身影——是多年前有过一面之缘的人。"},
    {"id": "scene2", "name": "雨天再次相遇", "type": "动态室外", "desc": "又下雨了。主角在街角避雨，恰好遇到上次在咖啡厅见过的那个人。两人一起等雨停。"},
    {"id": "scene3", "name": "日常帮忙", "type": "静态室内", "desc": "主角在办公室加班，那个人来帮忙整理文件或处理工作。两人在安静的空间里共处。"},
    {"id": "scene4", "name": "夜晚散步", "type": "动态室外", "desc": "工作结束后，两人一起在夜色中散步。路灯下，影子被拉得很长。"},
    {"id": "scene5", "name": "表白时刻", "type": "任意", "desc": "在某个安静的地方，主角终于鼓起勇气，说出了藏在心里的话。"},
]


def load_motif_yaml(path: Path) -> dict:
    raw = path.read_text("utf-8")
    raw = "\n".join(line for line in raw.splitlines() if line.strip() and not line.strip().startswith("# ") and line.strip() != "---")
    return yaml.safe_load(raw)


def call_llm(prompt: str, system: str = "你是一个专业的叙事学分析助手。只输出 JSON。", temperature: float = 0.3) -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()


def build_motif_description(motifs: list[dict]) -> str:
    """将母题列表格式化为一句话描述，用于 prompt 约束"""
    lines = []
    for i, m in enumerate(motifs):
        lines.append(f"{i+1}. {m['title']}：{m.get('description', '')}")
    return "\n".join(lines)


def generate_scene(scene: dict, motifs: list[dict] | None, style: str) -> str:
    """生成一个场景（带或不带母题约束）"""
    motif_text = ""
    if motifs:
        motif_desc = build_motif_description(motifs)
        motif_text = f"\n请在写作中自然体现以下母题：\n{motif_desc}\n母题是贯穿叙事的重复性主题元素，而非需要逐字逐句插入的标签。不要刻意提及母题名称本身，而是通过角色行为、对话和细节来体现。\n"

    prompt = f"""请以都市言情风格写一个约 500 字的场景。

场景描述：{scene['desc']}
{motif_text}
只输出场景正文，不要标题、不要说明文字。"""

    raw = call_llm(prompt, "你是一个专业的小说作家。只输出正文。", temperature=TEMPERATURE)
    return raw.strip()


def extract_motifs_from_text(text: str) -> list[dict]:
    """使用 p05 的母题提取 prompt"""
    sample = text[:2000]
    prompt = f"""分析以下场景文本，从中提取叙事母题（motif）。

母题定义：在叙事中反复出现的主题元素，包括具体意象、关系模式、行为习惯、叙事惯例。

要求：提取 3-6 个母题，每个母题须有原文线索支撑。

输出格式（JSON）：
{{
  "motifs": [
    {{
      "title": "母题名（简短）",
      "description": "一句话描述",
      "weight": 5,
      "evidence": ["原文引用"]
    }}
  ]
}}

场景文本：
{sample}"""

    raw = call_llm(prompt, "你是一个专业的叙事学分析助手。只输出 JSON。", temperature=0.3)
    return json.loads(clean_json(raw)).get("motifs", [])


def compute_alignment(detected: list[dict], target_titles: set[str]) -> float:
    """计算母题吻合度（基于 keywords 匹配）。
    TODO: 生产环境应使用 embedding 模型或 LLM 语义匹配，而非基于子串。
    """
    if not target_titles:
        return 0.0

    # 对每个目标母题定义 keyword aliases
    keyword_map = {
        "十年": ["十年", "时间", "回忆", "往事", "暗恋", "等待", "漫长", "岁月", "错过"],
        "手势": ["手势", "手", "触碰", "拥抱", "抱", "拉", "握", "擦", "递", "动作", "肢体", "身体", "接触"],
        "雨": ["雨", "雨夜", "雨天", "雨水", "雨声"],
        "孤独": ["孤独", "孤单", "独自", "一个人", "内心", "独白", "脆弱"],
        "歌声": ["歌", "音乐", "歌曲", "唱"],
        "论坛": ["论坛", "帖子", "回复", "评论", "评论区", "发帖", "网络", "系统提示"],
        "协作书写": ["协作", "共同", "一起", "写", "声明", "编辑", "文档", "配合"],
        "旁观者": ["旁观", "围观", "CP", "粉丝", "见证", "评论", "闺蜜", "室友", "朋友", "路人"],
        "随身携带的温柔": ["随身", "温柔", "关怀", "准备", "纸巾", "外套", "披", "细心", "体贴", "照顾"],
    }

    detected_titles = [m["title"] for m in detected]

    matched = 0
    for target in target_titles:
        aliases = keyword_map.get(target, [target])
        for dt in detected_titles:
            used = False
            for alias in aliases:
                if alias in dt or dt in alias:
                    matched += 1
                    used = True
                    break
            if used:
                break

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

    # 加载母题约束
    print("\n加载母题约束...")
    urban_motifs = load_motif_yaml(GALLERY_ROOT / "urban-romance" / "motif.yaml")
    campus_motifs = load_motif_yaml(GALLERY_ROOT / "campus-romance" / "motif.yaml")

    urban_motif_list = urban_motifs.get("motifs", [])
    campus_motif_list = campus_motifs.get("motifs", [])

    urban_titles = {m["title"] for m in urban_motif_list}
    campus_titles = {m["title"] for m in campus_motif_list}

    print(f"  都市言情母题: {len(urban_motif_list)} — {', '.join(urban_titles)}")
    print(f"  校园言情母题: {len(campus_motif_list)} — {', '.join(campus_titles)}")

    # 步骤 1-3: 生成 + 交叉验证
    all_results = []
    configs = [
        ("urban", urban_motif_list, urban_titles, "都市言情"),
        ("campus", campus_motif_list, campus_titles, "校园言情"),
    ]

    for series, motif_list, target_titles, style_name in configs:
        print(f"\n{'='*40}")
        print(f"约束组: {style_name} ({len(motif_list)} 个母题)")
        print(f"{'='*40}")

        # 带约束生成
        print(f"\n  步骤 1: 带母题约束生成 (5 个场景)")
        for scene in SCENE_TEMPLATES:
            cache_file = generated_dir / f"constrained_{series}_{scene['id']}.txt"
            if cache_file.exists():
                text = cache_file.read_text("utf-8")
                print(f"    {scene['name']} ← 读取缓存")
            else:
                print(f"    {scene['name']}...", end=" ", flush=True)
                text = generate_scene(scene, motif_list, style_name)
                cache_file.write_text(text, "utf-8")
                print(f"✓ ({len(text)} 字)")

            # 检测母题
            detect_cache = detection_dir / f"constrained_{series}_{scene['id']}.json"
            if detect_cache.exists():
                detected = json.loads(detect_cache.read_text("utf-8")).get("motifs", [])
            else:
                detected = extract_motifs_from_text(text)
                detect_cache.write_text(json.dumps({"motifs": detected}, ensure_ascii=False, indent=2), "utf-8")

            alignment = compute_alignment(detected, target_titles)
            all_results.append({
                "group": f"constrained_{series}",
                "scene": scene["name"],
                "alignment": alignment,
                "detected_count": len(detected),
                "target_count": len(target_titles),
                "detected_titles": [m["title"] for m in detected],
            })
            print(f"      吻合度: {alignment*100:.0f}% ({len(detected)} 个检测 / {len(target_titles)} 个目标)")

        # 无约束对照组
        print(f"\n  步骤 2: 无母题约束生成 (对照组, 5 个场景)")
        for scene in SCENE_TEMPLATES:
            cache_file = generated_dir / f"control_{series}_{scene['id']}.txt"
            if cache_file.exists():
                text = cache_file.read_text("utf-8")
                print(f"    {scene['name']} ← 读取缓存")
            else:
                print(f"    {scene['name']}...", end=" ", flush=True)
                text = generate_scene(scene, None, style_name)
                cache_file.write_text(text, "utf-8")
                print(f"✓ ({len(text)} 字)")

            detect_cache = detection_dir / f"control_{series}_{scene['id']}.json"
            if detect_cache.exists():
                detected = json.loads(detect_cache.read_text("utf-8")).get("motifs", [])
            else:
                detected = extract_motifs_from_text(text)
                detect_cache.write_text(json.dumps({"motifs": detected}, ensure_ascii=False, indent=2), "utf-8")

            alignment = compute_alignment(detected, target_titles)
            all_results.append({
                "group": f"control_{series}",
                "scene": scene["name"],
                "alignment": alignment,
                "detected_count": len(detected),
                "target_count": len(target_titles),
                "detected_titles": [m["title"] for m in detected],
            })
            print(f"      吻合度: {alignment*100:.0f}% ({len(detected)} 个检测 / {len(target_titles)} 个目标)")

    # 步骤 4-6: 对比分析
    print("\n" + "=" * 60)
    print("p07 分析报告：母题一致性检验")
    print("=" * 60)

    for series, target_titles, style in [("urban", urban_titles, "都市言情"), ("campus", campus_titles, "校园言情")]:
        constrained = [r for r in all_results if r["group"] == f"constrained_{series}"]
        control = [r for r in all_results if r["group"] == f"control_{series}"]

        avg_constrained = sum(r["alignment"] for r in constrained) / len(constrained) if constrained else 0
        avg_control = sum(r["alignment"] for r in control) / len(control) if control else 0
        diff = avg_constrained - avg_control

        print(f"\n## {style}")
        print(f"  约束组平均吻合度: {avg_constrained*100:.0f}%")
        print(f"  对照组平均吻合度: {avg_control*100:.0f}%")
        print(f"  提升: {diff*100:+.0f} 百分点")

        # 单母题覆盖率
        print(f"\n  母题约束力分析:")
        for title in sorted(target_titles):
            coverage = sum(1 for r in constrained if title in str(r.get("detected_titles", []))) / len(constrained) if constrained else 0
            bar = "█" * int(coverage * 10)
            print(f"    {title:<10}: {coverage*100:3.0f}% {bar}")

    # 保存完整报告
    report_data = {
        "results": all_results,
        "urban_avg": {
            "constrained": sum(r["alignment"] for r in all_results if r["group"] == "constrained_urban")
            / max(1, len([r for r in all_results if r["group"] == "constrained_urban"])),
            "control": sum(r["alignment"] for r in all_results if r["group"] == "control_urban")
            / max(1, len([r for r in all_results if r["group"] == "control_urban"])),
        },
        "campus_avg": {
            "constrained": sum(r["alignment"] for r in all_results if r["group"] == "constrained_campus")
            / max(1, len([r for r in all_results if r["group"] == "constrained_campus"])),
            "control": sum(r["alignment"] for r in all_results if r["group"] == "control_campus")
            / max(1, len([r for r in all_results if r["group"] == "control_campus"])),
        },
    }
    (RESULTS_DIR / "consistency_report.json").write_text(
        json.dumps(report_data, ensure_ascii=False, indent=2), "utf-8"
    )

    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
