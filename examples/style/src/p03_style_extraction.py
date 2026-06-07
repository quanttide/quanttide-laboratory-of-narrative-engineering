#!/usr/bin/env python3
"""
p03 — 风格可提取性实验

验证同一作者的文章是否共享可识别的风格特征，以及 LLM 能否聚类和归因。
"""

import json
import os
import sys
import random
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import FICTION_ROOT, DATA_DIR

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
    sys.exit(1)

API_URL = "https://api.deepseek.com/chat/completions"
RESULTS_DIR = DATA_DIR / "p03"

ARTICLES = [
    # 作者 A：职场言情
    {"id": "A1", "author": "职场言情", "name": "深夜失眠", "path": "职场言情/4_成稿/1_2_深夜失眠.md"},
    {"id": "A2", "author": "职场言情", "name": "傍晚小龙虾", "path": "职场言情/4_成稿/2_3_傍晚小龙虾.md"},
    {"id": "A3", "author": "职场言情", "name": "便利店闲坐", "path": "职场言情/4_成稿/4_1_便利店闲坐.md"},
    {"id": "A4", "author": "职场言情", "name": "书房陪伴", "path": "职场言情/4_成稿/10_1_书房陪伴.md"},
    {"id": "A5", "author": "职场言情", "name": "阳台看星星", "path": "职场言情/4_成稿/10_3_阳台看星星.md"},
    # 作者 B：校园言情
    {"id": "B1", "author": "校园言情", "name": "第四章（论坛私信）", "path": "校园言情/4_成稿/4_第四章.md"},
    {"id": "B2", "author": "校园言情", "name": "第五章（危机公关）", "path": "校园言情/4_成稿/5_第五章.md"},
    {"id": "B3", "author": "校园言情", "name": "第六章（论坛热搜）", "path": "校园言情/3_初稿/6_第六章.md"},
]

STYLE_GUIDE_PATH = FICTION_ROOT / ".quanttide" / "write" / "style.md"


def read_article_text(path: str) -> str:
    full_path = FICTION_ROOT / path
    if not full_path.exists():
        raise FileNotFoundError(f"文件不存在: {full_path}")
    text = full_path.read_text("utf-8")
    lines = text.split("\n")
    body_lines = ["" if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body_lines).strip()


def read_style_guide() -> str:
    return STYLE_GUIDE_PATH.read_text("utf-8") if STYLE_GUIDE_PATH.exists() else ""


def call_llm(prompt: str, system: str = "你是一个专业的文学风格分析助手。只输出 JSON。") -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_style(text: str, article_name: str) -> dict:
    """步骤 1：提取单篇文章的风格特征"""
    # 取前 2000 字作为样本
    sample = text[:2000]
    prompt = f"""分析下面这篇名为《{article_name}》的文章的风格特征。

只描述模式，不说好坏，不评价内容。请从以下维度分析：

{{
  "总括": "一句话风格定位（10-20字）",
  "句式特征": ["短句为主", "长句铺陈", ...],
  "用词偏好": ["日常口语", "文学色彩", ...],
  "情绪表达方式": ["含蓄内敛", "直白热烈", ...],
  "细节使用模式": ["物象锚点", "环境渲染", ...],
  "叙事视角特点": ["第三人称限知", "第一人称内心", ...],
  "节奏感": "舒缓 / 紧凑 / 张弛交替"
}}

文章内容：
{sample}"""
    raw = call_llm(prompt)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def cluster_articles(style_profiles: dict[str, dict]) -> dict:
    """步骤 2：blinded 聚类"""
    items = [{"id": aid, "profile": p} for aid, p in style_profiles.items()]
    random.shuffle(items)
    profiles_text = "\n\n".join(
        f"[文章 {it['id']}]\n{json.dumps(it['profile'], ensure_ascii=False, indent=2)}"
        for it in items
    )
    prompt = f"""以下 8 篇文章的风格特征描述已去掉作者信息。请将它们分成 2-3 组，每组内文章风格显著相似。

输出格式（JSON）：
{{
  "groups": [
    {{"id": "组1", "members": ["A1", "A3", ...], "reason": "共同风格特征"}},
    ...
  ]
}}

风格特征：
{profiles_text}"""
    raw = call_llm(prompt, "你是一个文学风格分析专家。只输出 JSON。")
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def attribute_article(
    target_id: str, target_text: str, style_profiles: dict[str, dict]
) -> str:
    """步骤 3：归因——将目标文章匹配到最相似的组"""
    profiles_prompt = "\n\n".join(
        f"[文章 {aid}]\n{json.dumps(p, ensure_ascii=False, indent=2)}"
        for aid, p in style_profiles.items()
        if aid != target_id
    )
    sample = target_text[:1500]
    prompt = f"""以下是一组已知风格的文章特征库，以及一篇新文章。请判断新文章与哪篇文章的风格最接近。

已知文章风格特征：
{profiles_prompt}

新文章《{target_id}》：
{sample}

输出格式（只输出最接近的文章 ID，如"A3"）："""
    raw = call_llm(prompt, "你是一个文学风格分析专家。只输出文章 ID。")
    return raw.strip()


def step1_extract_all() -> dict[str, dict]:
    """对所有 8 篇文章提取风格特征"""
    RESULTS_DIR.mkdir(exist_ok=True)
    profiles = {}

    for art in ARTICLES:
        result_file = RESULTS_DIR / f"style_{art['id']}.json"
        if result_file.exists():
            profiles[art["id"]] = json.loads(result_file.read_text("utf-8"))
            print(f"  {art['id']} {art['name']} ← 读取缓存")
            continue

        print(f"  {art['id']} {art['name']}...", end=" ", flush=True)
        text = read_article_text(art["path"])
        try:
            profile = extract_style(text, art["name"])
            profiles[art["id"]] = profile
            result_file.write_text(json.dumps(profile, ensure_ascii=False, indent=2), "utf-8")
            print("✓")
        except Exception as e:
            print(f"✗ {e}")

    return profiles


def step2_clustering(profiles: dict[str, dict]) -> dict:
    """对风格特征进行 blinded 聚类"""
    print("\n  聚类中...", end=" ", flush=True)
    try:
        result = cluster_articles(profiles)
        (RESULTS_DIR / "clustering.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), "utf-8"
        )
        print("✓")
        return result
    except Exception as e:
        print(f"✗ {e}")
        return {}


def step3_attribution(profiles: dict[str, dict]) -> dict:
    """留一法归因测试"""
    attributions = {}
    for art in ARTICLES:
        result_file = RESULTS_DIR / f"attr_{art['id']}.json"
        if result_file.exists():
            attr = json.loads(result_file.read_text("utf-8"))
            attributions[art["id"]] = attr
            continue

        print(f"  归因 {art['id']} {art['name']}...", end=" ", flush=True)
        text = read_article_text(art["path"])
        try:
            predicted = attribute_article(art["id"], text, profiles)
            attributions[art["id"]] = {"actual": art["author"], "predicted": predicted}
            result_file.write_text(
                json.dumps(attributions[art["id"]], ensure_ascii=False, indent=2), "utf-8"
            )
            print(f"→ {predicted}")
        except Exception as e:
            print(f"✗ {e}")

    return attributions


def report(profiles: dict, clustering: dict, attributions: dict):
    """生成分析报告"""
    print("\n" + "=" * 60)
    print("p03 分析报告：风格可提取性")
    print("=" * 60)

    # 聚类结果
    print("\n## 聚类结果")
    if clustering.get("groups"):
        member_list = {}
        author_map = {a["id"]: a["author"] for a in ARTICLES}
        for g in clustering["groups"]:
            members = ", ".join(g["members"])
            print(f"  {g['id']}: [{members}] ({g.get('reason', '')[:60]})")
            for m in g["members"]:
                member_list[m] = g["id"]

        # 计算同作者聚类率
        correct = 0
        total = 0
        for a in ARTICLES:
            total += 1
            same_group_members = [
                o["id"] for o in ARTICLES
                if member_list.get(o["id"]) == member_list.get(a["id"])
            ]
            same_author_in_group = [
                o for o in same_group_members if author_map[o] == author_map[a["id"]]
            ]
            if len(same_author_in_group) > 1:
                correct += 1
        rate = correct / total * 100 if total else 0
        print(f"\n  同作者聚类率: {correct}/{total} = {rate:.0f}%")

    # 归因结果
    print("\n## 归因结果")
    if attributions:
        author_map = {a["id"]: a["author"] for a in ARTICLES}
        correct = 0
        for art in ARTICLES:
            attr = attributions.get(art["id"], {})
            actual = art["author"]
            predicted = attr.get("predicted", "?")
            pred_author = author_map.get(predicted, "?")
            ok = actual == pred_author
            if ok:
                correct += 1
            marker = "✓" if ok else "✗"
            print(f"  {marker} {art['id']} {art['name']:>12} 实际={actual:<6} 预测→{predicted}({pred_author})")

        total = len(ARTICLES)
        print(f"\n  归因准确率: {correct}/{total} = {correct/total*100:.0f}%")
        print(f"  随机基线: ~50%")

    # 风格指南校准
    print("\n## 风格指南校准")
    style_guide = read_style_guide()
    if style_guide:
        guide_keywords = ["克制", "深情", "细节", "时间", "双向", "遗憾", "陪伴", "日常", "温柔", "诚实"]
        extracted_keywords = set()
        for pid, p in profiles.items():
            summary = p.get("总括", "")
            for kw in guide_keywords:
                if kw in summary or any(kw in str(v) for v in p.values()):
                    extracted_keywords.add(kw)
        matched = len(extracted_keywords)
        print(f"  style.md 关键词: {', '.join(guide_keywords)}")
        print(f"  LLM 自主覆盖:   {', '.join(sorted(extracted_keywords))}")
        print(f"  吻合度: {matched}/{len(guide_keywords)} = {matched/len(guide_keywords)*100:.0f}%")


def main():
    print("=" * 60)
    print("p03 — 风格可提取性实验")
    print("=" * 60)

    print("\n步骤 1：风格特征提取")
    profiles = step1_extract_all()

    print("\n步骤 2：Blinded 聚类")
    clustering = step2_clustering(profiles)

    print("\n步骤 3：留一法归因")
    attributions = step3_attribution(profiles)

    report(profiles, clustering, attributions)


if __name__ == "__main__":
    main()
