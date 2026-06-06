#!/usr/bin/env python3
"""
p14 — 片段内部情节建议

行为链标注（双层动机 + 三值链状态）→ 薄弱点诊断 → 3类建议生成
"""
import json, os, sys, random
from pathlib import Path
import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[4]
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

SCENES = [
    {"id": "S1", "name": "咖啡厅重逢", "path": "职场言情/4_成稿/1_1_咖啡厅重逢.md"},
    {"id": "S2", "name": "酒吧表白", "path": "职场言情/4_成稿/8_2_酒吧表白.md"},
]


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

    for sc in SCENES:
        sid = sc["id"]
        print(f"\n{'='*40}\n{sid} {sc['name']}")
        text = read_scene(sc["path"])

        # Step 1+2: Chain annotation + weak point diagnosis (combined)
        dc = RESULTS_DIR / f"chain_{sid}.json"
        if dc.exists():
            chain_data = json.loads(dc.read_text("utf-8"))
        else:
            print("  行为链标注 + 薄弱点诊断...", end=" ", flush=True)
            raw = call_llm(
                f"""分析以下场景全文，完成两件事：

## 任务A：行为链标注
将场景分解为"行为-反应"序列。对每个序列节点标注：

- actor: 谁在行动
- action: 做了什么/说了什么
- outward_motivation: 出行动机（露给别人看的理由）
- inward_motivation: 内隐动机（真实内心，可能未说出口）
- tension: 两个动机之间是否有冲突/张力
- reaction: 对方的反应
- chain_status: "完整"（因果链在文本内有支撑）| "有意断裂"（链断裂但这是设计意图）| "无意断裂"（链断裂且无合理支撑，是真薄弱点）

## 任务B：薄弱点诊断
基于行为链标注，识别薄弱点。4种类型：
- causal_gap: 行为A→行为B缺少逻辑过渡
- motivation_blind: 人物做了某事，文本未提供动机支撑
- emotional_jump: 情感状态变化跳过中间态
- boundary_shift: 行为在"社交陌生人"/"心理熟人"边界上偏移（亲密度过高或过低）

场景全文：
{text}

JSON格式：
{{
  "chain": [
    {{
      "seq": 1, "actor": "", "action": "",
      "outward_motivation": "", "inward_motivation": "",
      "tension": "", "reaction": "", "chain_status": "完整|有意断裂|无意断裂"
    }}
  ],
  "weak_points": [
    {{
      "location": "", "issue_type": "causal_gap|motivation_blind|emotional_jump|boundary_shift",
      "severity": 1,
      "reasoning": ""
    }}
  ]
}}""",
                "叙事分析专家。只输出 JSON。",
                0.2,
            )
            chain_data = json.loads(raw)
            dc.write_text(
                json.dumps(chain_data, ensure_ascii=False, indent=2), "utf-8"
            )
            n_chain = len(chain_data.get("chain", []))
            n_wp = len(chain_data.get("weak_points", []))
            print(f"✓ {n_chain} 个行为节点, {n_wp} 个薄弱点")

            # Print chain summary
            for c in chain_data.get("chain", []):
                status = c.get("chain_status", "?")
                marker = {"完整": " ", "有意断裂": "▸", "无意断裂": "▴"}.get(status, "?")
                print(f"    [{marker} {status}] {c.get('action', '')[:50]}")

        # Step 3: Generate 3 types of suggestions
        if chain_data.get("weak_points"):
            diag_c = RESULTS_DIR / f"diagnosis_{sid}.json"
            if diag_c.exists():
                diagnosis = json.loads(diag_c.read_text("utf-8"))
            else:
                print("  生成修改建议 (3类)...", end=" ", flush=True)
                wp_list = json.dumps(chain_data["weak_points"], ensure_ascii=False, indent=2)
                raw = call_llm(
                    f"""基于以下薄弱点，为每个生成3类修改建议。

## 建议类型说明

类型A - 因果补链：不改变行为本身，补一个中间环节（动作/念头/外部事件）让因果链闭合。适用：无意断裂。

类型B - 动机刻深：改写行为本身，让动机来源从"恰好"变为"性格驱动"。适用：motivation_blind。

类型C - 边界校准：保留行为链结构，调整该行为的"社交距离"（调远/调近）。适用：boundary_shift——行为在陌生人/熟人边界上偏移，链完整但亲密度不对。

## 场景上下文
{text[:1000]}

## 薄弱点
{wp_list}

JSON格式：
{{
  "suggestions": [
    {{
      "location": "",
      "issue_type": "",
      "chain_status": "",
      "fix_A": null或{{"category": "因果补链", "description": "", "expected_effect": ""}},
      "fix_B": null或{{"category": "动机刻深", "description": "", "expected_effect": ""}},
      "fix_C": null或{{"category": "边界校准", "direction": "调远|调近", "description": "", "expected_effect": ""}}
    }}
  ]
}}""",
                    "叙事编辑顾问。只输出 JSON。",
                    0.3,
                )
                diagnosis = json.loads(raw)
                diag_c.write_text(
                    json.dumps(diagnosis, ensure_ascii=False, indent=2), "utf-8"
                )
                n_fix = len(diagnosis.get("suggestions", []))
                print(f"✓ {n_fix} 条建议")

                for s in diagnosis.get("suggestions", []):
                    loc = s.get("location", "")[:40]
                    for t in ["fix_A", "fix_B", "fix_C"]:
                        if s.get(t):
                            desc = s[t].get("description", "")[:50]
                            print(f"    {t}: {desc}")

    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
