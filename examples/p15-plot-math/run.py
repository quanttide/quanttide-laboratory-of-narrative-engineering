#!/usr/bin/env python3
"""
p15 — 情节结构的数学形式化

因果图提取 → 图编辑距离(GED) → 事件密度函数 d(k) → 贝叶斯惊奇度
"""
import json, os, sys, math, statistics
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

WINDOW_LEN = 200  # characters per window for d(k)


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


def compute_density(text, window_len=WINDOW_LEN):
    """Compute event density function d(k)."""
    # Split text into windows
    chars = list(text)
    windows = []
    for start in range(0, len(chars), window_len):
        windows.append("".join(chars[start : start + window_len]))

    # Count common punctuation as proxy for event boundaries
    # 句号、问号、感叹号、省略号、引号内的独立对话视为事件边界
    density = []
    for w in windows:
        events = 0
        for c in w:
            if c in "。！？…\n":
                events += 1
        density.append(events / window_len)

    return {"windows": len(density), "d_k": density, "mean": statistics.mean(density) if density else 0, "variance": statistics.variance(density) if len(density) > 1 else 0}


def main():
    print("=" * 60 + "\np15 — 情节结构的数学形式化\n" + "=" * 60)
    RESULTS_DIR.mkdir(exist_ok=True)

    for sc in SCENES:
        sid = sc["id"]
        print(f"\n{'='*40}\n{sid} {sc['name']}")
        text = read_scene(sc["path"])

        # Step 1: LLM-extracted causal graph
        gc = RESULTS_DIR / f"graph_llm_{sid}.json"
        if gc.exists():
            graph_data = json.loads(gc.read_text("utf-8"))
        else:
            print("  因果图提取...", end=" ", flush=True)
            raw = call_llm(
                f"""从以下场景文本中提取因果图。

将每个独立事件作为节点，事件之间的因果关系作为有向边。
事件包括：外部事件（下雨、音乐响起）、人物动作（递毛巾、点单）、内部事件（想起、决定）。

对每个节点标注：
- id: 节点编号
- event: 事件描述
- actor: 发起者（人物名或"外部"）
- type: "action"|"internal"|"external"
- text_window: 该事件在文本中的大致位置（字符偏移）

对每条边标注：
- source: 前因节点id
- target: 后果节点id
- relation: "direct"（直接导致）|"enable"（使可能）|"inhibit"（阻止）

场景全文：
{text}

JSON格式：
{{
  "nodes": [
    {{"id": 1, "event": "", "actor": "", "type": "action|internal|external", "text_window": ""}}
  ],
  "edges": [
    {{"source": 1, "target": 2, "relation": "direct|enable|inhibit"}}
  ]
}}""",
                "叙事分析专家。只输出 JSON。",
                0.2,
            )
            graph_data = json.loads(raw)
            gc.write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), "utf-8")
            n_nodes = len(graph_data.get("nodes", []))
            n_edges = len(graph_data.get("edges", []))
            print(f"✓ {n_nodes} 节点, {n_edges} 边")

        # Graph metrics
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        node_ids = {n["id"] for n in nodes}
        in_degree = {nid: 0 for nid in node_ids}
        out_degree = {nid: 0 for nid in node_ids}
        for e in edges:
            src = e.get("source")
            tgt = e.get("target")
            if tgt in in_degree:
                in_degree[tgt] = in_degree.get(tgt, 0) + 1
            if src in out_degree:
                out_degree[src] = out_degree.get(src, 0) + 1

        causal_gaps = []
        for n in nodes:
            nid = n["id"]
            if nid in in_degree and in_degree[nid] == 0 and n.get("type") != "external":
                causal_gaps.append(
                    {
                        "id": nid,
                        "event": n.get("event", ""),
                        "in_degree": 0,
                        "reasoning": f"节点 '{n.get('event','')}' 入度为0（无前因事件指向它），但它是人物行为而非外部事件——可能是因果跳跃",
                    }
                )

        print(f"  入度分析: {len(causal_gaps)} 个潜在因果跳跃")

        # Store graph metrics
        g_metrics = RESULTS_DIR / f"graph_metrics_{sid}.json"
        if not g_metrics.exists():
            metrics = {
                "n_nodes": n_nodes,
                "n_edges": n_edges,
                "in_degree": {str(k): v for k, v in in_degree.items()},
                "out_degree": {str(k): v for k, v in out_degree.items()},
                "causal_gaps": causal_gaps,
                "avg_in_degree": sum(in_degree.values()) / max(len(in_degree), 1),
                "density": n_edges / max(n_nodes * (n_nodes - 1), 1),
            }
            g_metrics.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), "utf-8")

        # Step 2: Event density function d(k)
        dc = RESULTS_DIR / f"density_{sid}.json"
        if dc.exists():
            density_data = json.loads(dc.read_text("utf-8"))
        else:
            print("  事件密度函数 d(k)...", end=" ", flush=True)
            density_data = compute_density(text)
            dc.write_text(json.dumps(density_data, ensure_ascii=False, indent=2), "utf-8")

            d = density_data["d_k"]
            mean = density_data["mean"]
            var = density_data["variance"]
            peaks = [
                {"window": i, "value": v}
                for i, v in enumerate(d)
                if v > mean + math.sqrt(var) * 1.5
            ]
            troughs = [
                {"window": i, "value": v}
                for i, v in enumerate(d)
                if v < mean - math.sqrt(var) * 0.5
            ]
            print(f"✓ {density_data['windows']} 个窗口, σ²={var:.4f}")
            if peaks:
                print(f"    峰值窗口: {[p['window'] for p in peaks]}")
            if troughs:
                print(f"    谷值窗口: {[t['window'] for t in troughs]}")

        # Step 3: Bayesian surprise
        sc = RESULTS_DIR / f"surprise_{sid}.json"
        if sc.exists():
            surprise_data = json.loads(sc.read_text("utf-8"))
        else:
            print("  贝叶斯惊奇度...", end=" ", flush=True)
            # Pick key action nodes from the graph for surprise estimation
            action_nodes = [
                n for n in nodes if n.get("type") in ("action",)
            ]
            surprises = []
            for n in action_nodes[:6]:  # limit to first 6 action nodes
                raw2 = call_llm(
                    f"""给定前文所有事件，事件 E 发生的概率有多高？

前文（到目前为止发生的事件）：
{text[:text.find(n.get('text_window', n['event']))][:800]}

事件 E：{n['event']}（由 {n.get('actor','?')} 执行）

打分规则：
- P=0.9-1.0: 几乎必然发生，人物性格和前文强烈指向这个结果
- P=0.6-0.9: 很可能发生，有合理铺垫
- P=0.3-0.6: 可能但不必然，缺少明确指向
- P=0.0-0.3: 意外，读者会问"为什么会这样"

输出 JSON：
{{"event": "{n['event']}", "probability": 0.0, "surprise": 0.0, "reasoning": ""}}

surprise = -log(probability)，注意勿取log 0 或log 1。""",
                    "叙事概率评估。只输出 JSON。",
                    0.1,
                )
                try:
                    sr = json.loads(raw2)
                    surprises.append(sr)
                except:
                    pass

            surprise_data = {
                "scene": sid,
                "surprises": surprises,
                "high_surprise_nodes": [
                    s
                    for s in surprises
                    if s.get("surprise", 0) > 1.0  # -log(0.37) ≈ 1.0
                ],
            }
            sc.write_text(json.dumps(surprise_data, ensure_ascii=False, indent=2), "utf-8")
            high = len(surprise_data["high_surprise_nodes"])
            print(f"✓ {len(surprises)} 节点已评估, {high} 个高惊奇度")

            for s in surprises:
                marker = "▴" if s.get("surprise", 0) > 1.0 else " "
                print(f"    [{marker}] P={s.get('probability',0):.2f} S={s.get('surprise',0):.2f} {s.get('event','')[:40]}")

    # Generate comparative report
    print(f"\n{'='*40}\n交叉对比: p15 发现 vs p12 诊断")
    print("(p12 诊断数据来自虚构走向，非实际场景文本，不做定量对比)")
    print(f"\n结果: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
