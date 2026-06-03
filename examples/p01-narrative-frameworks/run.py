#!/usr/bin/env python3
"""
p01 — 叙事框架对比实验
对 3 篇文章分别用 3 种叙事框架标注段落角色，输出对比结果。
"""

import json
import os
import sys
from pathlib import Path

import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"

# 案例库根路径（相对于实验室）
FICTION_ROOT = Path(__file__).resolve().parents[4] / "assets" / "fiction"

# 实验数据
ARTICLES = [
    {
        "id": "A",
        "name": "咖啡厅重逢",
        "path": "职场言情/3_初稿/1_1_咖啡厅重逢.md",
        "type": "情绪积累型",
    },
    {
        "id": "B",
        "name": "酒吧表白",
        "path": "职场言情/3_初稿/8_2_酒吧表白.md",
        "type": "情感释放型",
    },
    {
        "id": "C",
        "name": "第六章（论坛热搜）",
        "path": "校园言情/3_初稿/6_第六章.md",
        "type": "事件驱动型",
    },
]

FRAMEWORKS = [
    {
        "id": "qczh",
        "name": "起承转合",
        "roles": [
            ("起", "引入人物、场景、情绪基调", "段落开头，环境描写，人物出场"),
            ("承", "展开关系，铺垫矛盾", "对话展开，细节积累，情绪递进"),
            ("转", "关键变化，情感转折", "意外事件，告白，决定，冲突爆发"),
            ("合", "收束，新的状态", "结局，反思，情绪落定，新常态"),
        ],
    },
    {
        "id": "three_act",
        "name": "三幕结构",
        "roles": [
            ("Setup", "建立人物、情境、冲突种子", "引入角色，展示日常，隐含矛盾"),
            ("Confrontation", "冲突升级，障碍出现", "矛盾表面化，角色被迫行动，张力上升"),
            ("Resolution", "高潮到结局", "关键对决/告白，冲突解决，新平衡"),
        ],
    },
    {
        "id": "emotion_curve",
        "name": "情感曲线",
        "roles": [
            ("常态", "情绪基线", "日常描写，平静状态"),
            ("触发", "情绪偏离的起点", "意外相遇，消息到来，回忆触发"),
            ("爬升", "情绪积累", "内心独白，细节堆叠，张力渐强"),
            ("峰值", "情绪释放", "告白，哭泣，拥抱，冲突爆发"),
            ("回落", "情绪余韵", "安静对话，身体放松，场景收束"),
        ],
    },
]

RESULTS_DIR = Path(__file__).parent / "results"


def read_article(path: str) -> str:
    full_path = FICTION_ROOT / path
    if not full_path.exists():
        raise FileNotFoundError(f"文件不存在: {full_path}")
    text = full_path.read_text(encoding="utf-8")
    # 去掉 front matter / markdown 标题行，保留空行段落分割
    lines = text.split("\n")
    body_lines = ["" if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body_lines).strip()


def split_paragraphs(text: str) -> list[str]:
    """按空行分割段落，过滤太短的片段"""
    paras = []
    for block in text.split("\n\n"):
        block = block.strip()
        if len(block) > 10:
            paras.append(block)
    return paras


def build_prompt(framework: dict, paras: list[str]) -> str:
    roles_desc = "\n".join(
        f"  - {role}：{desc}（{anchor}）"
        for role, desc, anchor in framework["roles"]
    )

    paras_text = "\n\n".join(f"[段落 {i+1}]\n{p}" for i, p in enumerate(paras))

    return f"""你是一个专业的叙事结构分析助手。

请使用「{framework['name']}」框架对下面的文章进行段落角色标注。

框架角色定义：
{roles_desc}

输出格式（JSON 数组）：
[
  {{
    "para": 段落编号,
    "role": "角色名",
    "reason": "判断理由（一句话）"
  }}
]

只输出 JSON，不要额外文字。

文章段落：
{paras_text}"""


def call_llm(prompt: str) -> str:
    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的叙事结构分析助手。只输出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def run_experiment():
    RESULTS_DIR.mkdir(exist_ok=True)

    for art in ARTICLES:
        print(f"\n{'='*60}")
        print(f"文章 {art['id']}: {art['name']} ({art['type']})")
        print(f"{'='*60}")

        text = read_article(art["path"])
        paras = split_paragraphs(text)
        print(f"  段落数: {len(paras)}")

        for fw in FRAMEWORKS:
            print(f"\n  框架: {fw['name']}...", end=" ", flush=True)
            prompt = build_prompt(fw, paras)

            try:
                raw = call_llm(prompt)
                # 清理可能的 markdown 代码块
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw.rsplit("```", 1)[0]
                raw = raw.strip()

                result = json.loads(raw)
                print(f"✓ {len(result)} 段标注完成")

                # 保存
                fname = f"{art['id']}_{fw['id']}.json"
                out = {
                    "article": art["name"],
                    "framework": fw["name"],
                    "paragraphs": paras,
                    "labels": result,
                }
                (RESULTS_DIR / fname).write_text(
                    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
                )

            except Exception as e:
                print(f"✗ 失败: {e}")


def analyze_results():
    """生成对比分析报告"""
    print(f"\n\n{'='*60}")
    print("分析报告")
    print(f"{'='*60}\n")

    for art in ARTICLES:
        print(f"\n--- {art['name']} ---")

        # 读取三个框架的标注结果
        all_labels = {}
        for fw in FRAMEWORKS:
            fname = RESULTS_DIR / f"{art['id']}_{fw['id']}.json"
            if fname.exists():
                data = json.loads(fname.read_text(encoding="utf-8"))
                all_labels[fw["name"]] = data["labels"]

        if len(all_labels) < 2:
            print("  数据不足，跳过")
            continue

        # 段落数
        num_paras = max(len(v) for v in all_labels.values())

        # 对比表
        print(f"\n  段落角色对比（共 {num_paras} 段）：")
        print(f"  {'段号':>4}  {'起承转合':<10} {'三幕结构':<14} {'情感曲线':<10} {'一致性'}")
        print(f"  {'-'*50}")

        agreements = []
        for i in range(num_paras):
            roles = {}
            for fw_name, labels in all_labels.items():
                if i < len(labels):
                    roles[fw_name] = labels[i].get("role", "?")
                else:
                    roles[fw_name] = "-"

            # 判断一致性：三个角色名是否指向同一叙事概念
            # 简化：如果三个标注不全是不同的，就算一致
            unique = set(roles.values())
            consistent = len(unique) <= 2  # 如果有2个相同也算部分一致

            if consistent:
                agreements.append(1)
            else:
                agreements.append(0)

            marker = "✓" if consistent else "✗"
            print(
                f"  {i+1:>4}  {roles.get('起承转合', '-'):<10} {roles.get('三幕结构', '-'):<14} {roles.get('情感曲线', '-'):<10} {marker}"
            )

        agree_rate = sum(agreements) / len(agreements) * 100 if agreements else 0
        print(f"\n  一致性: {agree_rate:.0f}%（{sum(agreements)}/{len(agreements)} 段部分一致）")


def main():
    print("=" * 60)
    print("p01 — 叙事框架对比实验")
    print("=" * 60)

    run_experiment()
    analyze_results()

    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
