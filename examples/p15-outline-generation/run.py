#!/usr/bin/env python3
"""
p15 — 提纲生成实验
YAML + p14 JSON → 场景写作备忘 md
"""
import json, os, sys
from pathlib import Path
import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[4]
GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction" / "urban-romance"
P14_RESULTS = (
    Path(__file__).parent.parent
    / "p14-intra-scene-plot"
    / "results"
)
RESULTS_DIR = Path(__file__).parent / "results"

SCENES = [
    {
        "id": "1_1",
        "title": "咖啡厅重逢",
        "story_key": "1_1",
        "p14_prefix": "S1",
    },
    {
        "id": "8_2",
        "title": "酒吧表白",
        "story_key": "8_2",
        "p14_prefix": "S2",
    },
]


def call_llm(prompt, system="只输出 md。", temp=0.3):
    for _ in range(3):
        try:
            r = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temp,
                },
                timeout=180,
            )
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"].strip()
            raw = raw[raw.find("\n") + 1 :] if raw.startswith("```") else raw
            raw = raw[:-3].strip() if raw.endswith("```") else raw
            return raw
        except:
            continue
    return ""


def read_file(path):
    if path.exists():
        return path.read_text("utf-8")
    return ""


def main():
    print("=" * 60 + "\np15 — 提纲生成\n" + "=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    # Load YAMLs
    style_text = read_file(GALLERY_ROOT / "style.yaml")[:3000]
    motif_text = read_file(GALLERY_ROOT / "motif.yaml")[:2000]
    story_text = read_file(GALLERY_ROOT / "story.yaml")[:5000]

    for sc in SCENES:
        sid = sc["id"]
        title = sc["title"]
        prefix = sc["p14_prefix"]
        print(f"\n{'='*40}\n{sid} {title}")

        out_path = RESULTS_DIR / f"outline_{sid.replace('_','')}.md"
        if out_path.exists():
            print(f"  已存在，跳过")
            continue

        # Load p14 outputs
        chain = read_file(P14_RESULTS / f"chain_{prefix}.json")[:2000]
        diagnosis = read_file(P14_RESULTS / f"diagnosis_{prefix}.json")[:2000]
        suggestions = read_file(P14_RESULTS / f"suggestions_{prefix}.json")[:3000]

        # Extract scene-specific story data
        import yaml

        story_all = yaml.safe_load(story_text)
        scene_data = None
        for p in story_all.get("plots", []):
            if p["id"] == sc["story_key"]:
                scene_data = p
                break
        scene_desc = scene_data.get("description", "") if scene_data else ""
        scene_tensions = (
            "\n".join(scene_data.get("tensions", [])) if scene_data else ""
        )

        print("  生成提纲...", end=" ", flush=True)
        md = call_llm(
            f"""基于以下数据，生成一份写作备忘 md 格式提纲。

## 模板

# {sid} {title} — 写作备忘

## 行为序列

[→ 连接的完整行为链，从 chain 中提取]

## 结构难点

[从 story.tensions 中提取结构层面条目，每条约50字]
- 标注来源（哪条 tension）
- 说明该难点在当前场景中的具体表现

## 边界提醒

[从 style.boundaries 中聚合适用的规则]
- 每条标注维度名
- 语言为执行式： "注意：……" "不要……"

## 薄弱点与建议

[从 p14 diagnosis + suggestions 合并]
各条展开：位置 → 问题（类型+严重度） → 策略A / 策略B / 策略C

---

## 输入数据

### scene story.yaml
{scene_desc[:800]}

### scene tensions
{scene_tensions[:800]}

### style.yaml boundaries
{style_text[:2000]}

### motif.yaml
{motif_text[:1500]}

### chain（行为链）
{chain[:1500]}

### diagnosis（薄弱点）
{diagnosis[:1500]}

### suggestions（建议）
{suggestions[:2500]}

生成上述模板格式的完整 md 内容。语言简洁、执行式、面向写作者。""",
            "叙事编辑。生成写作备忘 md，只输出 md 正文。",
            0.3,
        )

        out_path.write_text(md, "utf-8")
        print(f"✓ {out_path.name}")

    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
