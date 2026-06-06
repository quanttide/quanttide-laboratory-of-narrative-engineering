#!/usr/bin/env python3
"""
p13 — 极小概率→必然实验

生成巧合驱动的情节 → 识别内部巧合点 → 重写为人物驱动的必然
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
    {"id":"C1","name":"咖啡厅重逢","path":"职场言情/4_成稿/1_1_咖啡厅重逢.md"},
    {"id":"C2","name":"酒吧表白","path":"职场言情/4_成稿/8_2_酒吧表白.md"},
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
    return json.loads(call_llm(f"""{ctx}\n比较两个改写版在「{dim}」上谁更好：\nA:{ta[:200]}\nB:{tb[:200]}\nJSON:{{"winner":"A|B|tie","reason":".."}}""","叙事编辑。只输出 JSON。",0.1))

def main():
    print("="*60+"\np13 — 极小概率→必然\n"+"="*60)
    RESULTS_DIR.mkdir(exist_ok=True)

    for sc in SCENES:
        cid = sc["id"]
        print(f"\n{'='*40}\n{cid} {sc['name']}")
        text = read_scene(sc["path"])

        # 1. Generate a coincidence-driven plot direction
        dc = RESULTS_DIR/f"direction_{cid}.json"
        if dc.exists(): direction = json.loads(dc.read_text("utf-8"))
        else:
            direction = json.loads(call_llm(f"""写一个150-200字的场景延续，刻意让情节依赖巧合。使用"恰好"、"正巧"、"突然"等词。
约束：保持都市言情风格，不要引入反派、暴力、奇幻等元素。人物仍然是林远亭和陆知微。
场景原文：{text[:2000]}
JSON:{{"title":"..","what":"含巧合的情节走向","coincidence_elements":[]}}""","小说创作顾问。只输出 JSON。",0.7))
            dc.write_text(json.dumps(direction,ensure_ascii=False,indent=2),"utf-8")
        print(f"  ✓ 巧合驱动版: {direction.get('title','?')}")

        # 2. Identify coincidence points
        cc = RESULTS_DIR/f"coincidences_{cid}.json"
        if cc.exists(): coincidences = json.loads(cc.read_text("utf-8"))
        else:
            print("  识别巧合点...", end=" ", flush=True)
            coincidences = json.loads(call_llm(f"""识别这个情节走向中的所有"巧合点"——那些依赖偶然性而非人物性格推动的事件。
走向：{direction['what']}
对每个巧合点标注类型(spatial/temporal/informational)和为什么它不自然。
JSON:{{"coincidences":[{{"location":"..","type":"spatial|temporal|informational","why_improbable":".."}}]}}""","叙事编辑。只输出 JSON。",0.1))
            cc.write_text(json.dumps(coincidences,ensure_ascii=False,indent=2),"utf-8")
            print(f"✓ {len(coincidences.get('coincidences',[]))} 个巧合点")

        # 3. Rewrite: coincidence → inevitability
        rc = RESULTS_DIR/f"rewrites_{cid}.json"
        if rc.exists(): rewrites = json.loads(rc.read_text("utf-8"))
        else:
            print("  改写为必然...", end=" ", flush=True)
            coinc_list = "\n".join(f"- {c.get('location','')}: {c.get('why_improbable','')}" for c in coincidences.get("coincidences",[]))
            rewrites = json.loads(call_llm(f"""重写这个情节走向，消除所有巧合。不是"加解释"——是重构人物的行为链条，让每个事件都由人物性格和之前的行动自然推动。
原文：{direction['what']}
巧合点：{coinc_list}
约束：不能简单加"原来她早就知道"这类解释。必须通过人物的具体行为和选择链条来让事件变得必然。
JSON:{{"rewrites":[{{"title":"改写版1","what":"..","mechanism":"通过什么人物行为链条消除巧合","causal_chain":"A→B→C"}},{{"title":"改写版2","what":"..","mechanism":"..","causal_chain":".."}}]}}""","小说创作顾问。只输出 JSON。",0.7))
            rc.write_text(json.dumps(rewrites,ensure_ascii=False,indent=2),"utf-8")
            print(f"✓ {len(rewrites.get('rewrites',[]))} 个改写版")

        # 4. Pairwise: original vs rewrites
        if rewrites.get("rewrites"):
            for i, rw in enumerate(rewrites["rewrites"]):
                pc = RESULTS_DIR/f"pairwise_{cid}_rw{i}.json"
                if pc.exists(): continue
                print(f"    pairwise 初稿 vs 改写{i+1}...", end=" ", flush=True)
                pw = {}
                for dim in ["causal_logic","inevitability","character_depth"]:
                    r = pairwise(("初稿",direction["what"]),("改写",rw["what"]),dim,f"《{sc['name']}》")
                    pw[dim] = r
                pc.write_text(json.dumps(pw,ensure_ascii=False,indent=2),"utf-8")
                wins = sum(1 for d,r in pw.items() if r.get("winner")=="B")
                print(f"改写 wins {wins}/3")

    print(f"\n结果: {RESULTS_DIR}")

if __name__=="__main__": main()
