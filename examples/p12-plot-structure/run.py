#!/usr/bin/env python3
"""
p12 — 情节结构优化实验

生成情节走向 → 诊断内部结构薄弱点 → 生成结构改法 → pairwise 对比
"""
import json, os, sys, random
from pathlib import Path
import requests, yaml

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY","")
if not DEEPSEEK_API_KEY: sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[4]
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

SCENES = [
    {"id":"S1","name":"咖啡厅重逢","path":"职场言情/4_成稿/1_1_咖啡厅重逢.md"},
    {"id":"S2","name":"酒吧表白","path":"职场言情/4_成稿/8_2_酒吧表白.md"},
]

def call_llm(prompt, system="只输出 JSON。", temp=0.3):
    for _ in range(3):
        r = requests.post(API_URL, headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"},
            json={"model":"deepseek-chat","messages":[{"role":"system","content":system},{"role":"user","content":prompt}],"temperature":temp}, timeout=180)
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw[raw.find("\n")+1:] if raw.startswith("```") else raw
        raw = raw[:-3].strip() if raw.endswith("```") else raw
        try: json.loads(raw); return raw
        except: pass
    return raw

def read_scene(path):
    t = (FICTION_ROOT/path).read_text("utf-8")
    return "\n".join(l for l in t.split("\n") if not l.startswith("# "))

def pairwise(a,b,dim,ctx=""):
    la,ta = a; lb,tb = b
    if random.random()<0.5: la,lb,ta,tb = lb,la,tb,ta
    return json.loads(call_llm(f"""{ctx}\n比较两个改法在「{dim}」上谁更好：\nA:{ta[:200]}\nB:{tb[:200]}\nJSON:{{"winner":"A|B|tie","reason":".."}}""","叙事编辑。只输出 JSON。",0.1))

def main():
    print("="*60+"\np12 — 情节结构优化\n"+"="*60)
    RESULTS_DIR.mkdir(exist_ok=True)

    for sc in SCENES:
        sid = sc["id"]
        print(f"\n{'='*40}\n{sid} {sc['name']}")
        text = read_scene(sc["path"])

        # 1. Generate a plot direction then diagnose its structure
        dc = RESULTS_DIR/f"direction_{sid}.json"
        if dc.exists(): direction = json.loads(dc.read_text("utf-8"))
        else:
            direction = json.loads(call_llm(f"""基于《{sc['name']}》，生成一个合理的情节延续(150-200字)：
场景原文：{text[:2000]}
JSON:{{"title":"..","what":"..","motivation":"..","consequence":".."}}""","小说创作顾问。只输出 JSON。",0.7))
            dc.write_text(json.dumps(direction,ensure_ascii=False,indent=2),"utf-8")
        print(f"  ✓ 生成走向: {direction.get('title','?')}")

        # 2. Diagnose internal structure weaknesses
        diag_c = RESULTS_DIR/f"diagnosis_{sid}.json"
        if diag_c.exists(): diagnosis = json.loads(diag_c.read_text("utf-8"))
        else:
            print("  结构诊断...", end=" ", flush=True)
            diagnosis = json.loads(call_llm(f"""分析这个情节走向的内部结构薄弱点：
走向：{direction['what']}

检查：
1. 因果跳跃(causal_gap)：动机→行动→后果的链有没有断裂？
2. 节奏失衡(pacing)：事件密度是否均匀？高潮前的铺垫是否充分？
3. 动机不明(motivation_unclear)：人物的行为理由是否清晰？

对每个薄弱点标注类型和严重程度(1-3)并给出结构改法建议。
JSON:{{"weak_points":[{{"location":"..","issue_type":"causal_gap|pacing|motivation_unclear","severity":1-3,"reasoning":"..","structural_fix":"具体的结构改法(怎么调整叙事结构，不是改措辞)"}}]}}""","叙事编辑。只输出 JSON。",0.1))
            diag_c.write_text(json.dumps(diagnosis,ensure_ascii=False,indent=2),"utf-8")
            wp = diagnosis.get("weak_points",[])
            print(f"✓ {len(wp)} 个薄弱点")
            for w in wp: print(f"    [{w.get('issue_type','?')}] {w.get('location','?')[:50]} severity={w.get('severity','?')}")

        # 3. Pairwise: structural fix vs surface fix
        for i, wp in enumerate(diagnosis.get("weak_points",[])):
            pc = RESULTS_DIR/f"pairwise_{sid}_wp{i}.json"
            if pc.exists(): continue
            sf = wp.get("structural_fix","")
            # Generate surface fix counterpart
            sfx = json.loads(call_llm(f"""这个情节走向有一个薄弱点：{wp.get('reasoning','')}
生成一条"表面改法"作为对照——只改措辞和细节描写，不改叙事结构。
JSON:{{"surface_fix":"具体的改法建议(80-150字)"}}""","叙事编辑。只输出 JSON。",0.1))
            surface_fix = sfx.get("surface_fix","")

            print(f"    wp{i}: pairwise structural vs surface...", end=" ", flush=True)
            pw = {}
            for dim in ["causal_improvement","pacing_improvement","actionable"]:
                r = pairwise(("structural",sf),("surface",surface_fix),dim,f"走向《{direction.get('title','?')}》薄弱点: {wp.get('location','')}")
                pw[dim] = r
            pc.write_text(json.dumps({"structural_fix":sf,"surface_fix":surface_fix,"pairwise":pw},ensure_ascii=False,indent=2),"utf-8")
            wins = sum(1 for d,r in pw.items() if r.get("winner")=="A")
            print(f"structural wins {wins}/3")

    print(f"\n结果: {RESULTS_DIR}")

if __name__=="__main__": main()
