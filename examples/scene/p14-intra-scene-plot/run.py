#!/usr/bin/env python3
"""
p14 — 片段内部情节建议（修复版）

步骤拆分为：链标注(含示例) → 诊断 → 3类建议
"""
import json, os, sys
from pathlib import Path
import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[5]
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction" / "urban-romance"

SCENES = [
    {"id": "S1", "name": "咖啡厅重逢", "path": "职场言情/4_成稿/1_1_咖啡厅重逢.md"},
    {"id": "S2", "name": "酒吧表白", "path": "职场言情/4_成稿/8_2_酒吧表白.md"},
]


def load_yamls():
    """Read story.yaml, motif.yaml, style.yaml as raw text."""
    texts = {}
    for name in ("story", "motif", "style"):
        fpath = GALLERY_ROOT / f"{name}.yaml"
        if fpath.exists():
            texts[name] = fpath.read_text("utf-8")
    return texts


def call_llm(prompt, system="只输出 JSON。", temp=0.3):
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
            try:
                json.loads(raw)
                return raw
            except:
                continue
        except:
            continue
    return raw


def read_scene(path):
    t = (FICTION_ROOT / path).read_text("utf-8")
    return "\n".join(l for l in t.split("\n") if not l.startswith("# "))


def main():
    print("=" * 60 + "\np14 — 片段内部情节建议\n" + "=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    yamls = load_yamls()
    motif_text = yamls.get("motif", "")[:2000]
    style_text = yamls.get("style", "")[:2000]
    story_text = yamls.get("story", "")[:2000]
    print(f"已加载: story.yaml + motif.yaml + style.yaml")

    for sc in SCENES:
        sid = sc["id"]
        print(f"\n{'='*40}\n{sid} {sc['name']}")
        text = read_scene(sc["path"])

        # Step 1: Chain annotation (separate call, with examples)
        cc = RESULTS_DIR / f"chain_{sid}.json"
        if cc.exists():
            chain = json.loads(cc.read_text("utf-8"))
        else:
            print("  Step 1: 行为链标注...", end=" ", flush=True)
            raw = call_llm(
                f"""分解以下场景为"行为-反应"序列。

每个节点标注：

- actor: 谁在行动
- action: 做了什么/说了什么
- outward_motivation: 出行动机（给别人看的理由）
- inward_motivation: 内隐动机（真实的内心理由）
- tension: 两个动机是否冲突？是张力所在还是无冲突？
- reaction: 对方怎么回应
- chain_status: "完整" | "有意断裂" | "无意断裂"

## 三值链状态区分示例

以「咖啡厅重逢」场景的具体行为为例：

| 行为 | 正确状态 | 为什么 |
|------|---------|--------|
| 他看到窗外身影→认出是陆知微→怔住 | 完整 | 文本有支撑：先望见身影→渐近→看清→怔住，因果链完整 |
| 他掏出毛巾擦她头发→擦了两下突然缩回 | 有意断裂 | 文本没写"他意识到越界"——但缩回本身就是张力，不需要解释。链断裂是设计意图 |
| 他直接帮她点焦糖玛奇朵（没问口味） | 无意断裂 | 文本没说他为什么知道她爱喝这个。作为社交陌生人，他不该知道。这是真缺失 |
| 她冒雨赶来→在门口合上伞→买关东煮挨着他坐下 | 完整 | 各行为之间有因果顺序联系 |

判断三值的规则：
- 完整：动机→行动的因果链在文本内有明确支撑
- 有意断裂：链看起来断了（动机不完全明确），但断裂本身就是文本的设计——制造张力、留白、人物性格使然
- 无意断裂：链断裂，且文本没有提供任何合理解释——读者会问"为什么会这样"

场景全文：
{text}

输出JSON格式：
{{"chain": [
  {{"seq": 1, "actor": "", "action": "", "outward_motivation": "", "inward_motivation": "", "tension": "", "reaction": "", "chain_status": "完整|有意断裂|无意断裂"}}
]}}""",
                "叙事分析专家。只输出 JSON。",
                0.2,
            )
            chain = json.loads(raw)
            cc.write_text(json.dumps(chain, ensure_ascii=False, indent=2), "utf-8")

            nodes = chain.get("chain", [])
            print(f"✓ {len(nodes)} 个节点")
            for c in nodes:
                s = c.get("chain_status", "?")
                m = {"完整": " ", "有意断裂": "▸", "无意断裂": "▴"}.get(s, "?")
                print(f"    [{m} {s}] {c.get('action', '')[:55]}")

        # Step 2: Weak point diagnosis (separate call)
        dc = RESULTS_DIR / f"diagnosis_{sid}.json"
        if dc.exists():
            diagnosis = json.loads(dc.read_text("utf-8"))
        else:
            print("  Step 2: 薄弱点诊断...", end=" ", flush=True)
            chain_json = json.dumps(chain.get("chain", []), ensure_ascii=False)
            raw = call_llm(
                f"""基于行为链标注，诊断薄弱点。4种类型：

- causal_gap: 行为A→行为B缺少逻辑过渡
- motivation_blind: 人物做了某事，文本未提供动机支撑
- emotional_jump: 情感状态变化跳过中间态
- boundary_shift: 行为在"社交陌生人"/"心理熟人"边界上偏移（亲密度过高或过低）

重点检查 chain_status="无意断裂" 的节点——它们是最可能的薄弱点。

chain_status="有意断裂" 的节点通常不是问题，但如果你认为断裂程度超出了设计意图（断裂变成了困惑），也可以标注。

场景行为链：
{chain_json}

输出JSON格式：
{{"weak_points": [
  {{"location": "seq X: 行为描述", "issue_type": "causal_gap|motivation_blind|emotional_jump|boundary_shift", "severity": 1-3, "reasoning": ""}}
]}}""",
                "叙事结构诊断。只输出 JSON。",
                0.2,
            )
            diagnosis = json.loads(raw)
            dc.write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2), "utf-8")
            wps = diagnosis.get("weak_points", [])
            print(f"✓ {len(wps)} 个薄弱点")
            for w in wps:
                print(f"    [{w.get('issue_type','?')}] {w.get('location','')[:50]} severity={w.get('severity','?')}")

        # Step 3: Generate 3 types of suggestions
        wps = diagnosis.get("weak_points", [])
        if wps:
            sc = RESULTS_DIR / f"suggestions_{sid}.json"
            if sc.exists():
                suggestions = json.loads(sc.read_text("utf-8"))
            else:
                print("  Step 3: 生成建议 (注入所有YAML上下文)...", end=" ", flush=True)
                wp_json = json.dumps(wps, ensure_ascii=False, indent=2)
                raw = call_llm(
                    f"""为每个薄弱点生成修改建议。要求：每个薄弱点至少给2条，让创作者有选择余地。

三种策略方向（可任意组合使用）：
A. 在行为前后加一个短暂的动作/停顿，让转换更自然
B. 保留行为，用具体的感官触发（看到/听到/想起）解释动机
C. 换一种不同的行为来表达同样的情感

注意：这个故事的审美是克制浪漫——靠近比后退好，具体比抽象好，本能比计算好。

## 作品的审美框架
{style_text}

## 作品的母题结构
{motif_text}

## 作品的故事模型
{story_text}

## 场景前情
{text[:500]}

## 薄弱点
{wp_json}

输出JSON：
{{"suggestions": [
  {{"location": "", "issue_type": "",
    "fix_A": null或{{"description": "", "expected_effect": ""}},
    "fix_B": null或{{"description": "", "expected_effect": ""}},
    "fix_C": null或{{"description": "", "expected_effect": ""}}
  }}
]}}""",
                    "叙事编辑顾问。只输出 JSON。",
                    0.4,
                )
                suggestions = json.loads(raw)
                sc.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), "utf-8")
                nf = len(suggestions.get("suggestions", []))
                print(f"✓ {nf} 条建议")
                for s in suggestions.get("suggestions", []):
                    loc = s.get("location", "")[:40]
                    for t in ["fix_A", "fix_B", "fix_C"]:
                        if s.get(t) and s[t].get("description"):
                            d = s[t].get("description", "")[:55]
                            print(f"    {t}: {d}")

    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
