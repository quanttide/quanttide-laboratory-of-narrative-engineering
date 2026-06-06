#!/usr/bin/env python3
"""
p11 — 情节方向生成实验

生成 → 风格自评审 → 内部情节校验 → pairwise 盲评
"""
import json, os, sys, random
from pathlib import Path
import requests, yaml

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY","")
if not DEEPSEEK_API_KEY: sys.exit("请设置 DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
REPO_ROOT = Path(__file__).resolve().parents[4]
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction"
RESULTS_DIR = Path(__file__).parent / "results"

SCENES = [
    {"id":"S1","name":"咖啡厅重逢后","path":"职场言情/4_成稿/1_1_咖啡厅重逢.md",
     "state":"林远亭刚递了毛巾擦了她头发，回过神来赶紧停下。她接过毛巾，手指碰到他的手，心弦拨动。两人坐在咖啡厅，空气里弥漫着尴尬和期待。"},
    {"id":"S2","name":"酒吧表白前一刻","path":"职场言情/4_成稿/8_2_酒吧表白.md",
     "state":"两人都喝了酒。她回忆大四聚餐——只记得他白衬衣黑裤子。他顿了顿说当然，一直记着。她看着他的眼睛，那句'你喜不喜欢我'已经到了嘴边。"},
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
    return json.loads(call_llm(f"""{ctx}\n比较两个情节走向在「{dim}」上谁更好：\nA:{ta[:200]}\nB:{tb[:200]}\nJSON:{{"winner":"A|B|tie","reason":".."}}""","叙事编辑。只输出 JSON。",0.1))

def main():
    print("="*60+"\np11 — 情节方向生成\n"+"="*60)
    RESULTS_DIR.mkdir(exist_ok=True)

    # Load style
    style = yaml.safe_load((GALLERY_ROOT/"urban-romance"/"style.yaml").read_text("utf-8"))
    dims_txt = "\n".join(f"【{d['title']}】{d.get('description','')[:120]}" for d in style.get("dimensions",[]))

    for sc in SCENES:
        sid = sc["id"]
        print(f"\n{'='*40}\n{sid} {sc['name']}")
        text = read_scene(sc["path"])

        # 1. Generate 5 directions
        dc = RESULTS_DIR/f"directions_{sid}.json"
        if dc.exists(): dirs=json.loads(dc.read_text("utf-8"))
        else:
            dirs = json.loads(call_llm(f"""场景《{sc['name']}》之后。{sc['state']}
生成5个不同的情节走向(每个80-150字)。必须具体：谁做了什么、导致什么变化。5个走向必须真正不同。
JSON:{{"directions":[{{"title":"..","what":"..","motivation":"..","consequence":".."}}]}}
场景原文：{text[:2000]}""","小说创作顾问。只输出 JSON。",0.8)).get("directions",[])
            dc.write_text(json.dumps(dirs,ensure_ascii=False,indent=2),"utf-8")
        print(f"  ✓ {len(dirs)} 个走向")

        # 2. Internal plot validation (NEW: check consistency within each direction)
        vc = RESULTS_DIR/f"validate_{sid}.json"
        if vc.exists(): validations = json.loads(vc.read_text("utf-8"))
        else:
            print("  内部情节校验...", end=" ", flush=True)
            validations = []
            for i,d in enumerate(dirs):
                v = json.loads(call_llm(f"""验证这个情节走向的内部一致性：
走向：{d['what']}
检查项：
1. 人物动机→行动→后果的因果链是否完整？
2. 是否有内部矛盾（角色前一句和后一句性格不一致）？
3. 是否与系列母题(手势优先于语言、日常的缝隙)相容？

JSON:{{"causal_chain_ok":true/false,"internal_contradiction":null,"motif_compatible":true/false,"issues":["如果有什么问题"]}}""","叙事编辑。只输出 JSON。",0.1))
                validations.append(v)
            vc.write_text(json.dumps(validations,ensure_ascii=False,indent=2),"utf-8")
            ok = sum(1 for v in validations if v.get("causal_chain_ok")) 
            print(f"✓ {ok}/{len(dirs)} 因果链完整")

        # 3. Style self-review (p09 method)
        rc = RESULTS_DIR/f"style_review_{sid}.json"
        if rc.exists(): reviews = json.loads(rc.read_text("utf-8"))
        else:
            print("  风格自评审...", end=" ", flush=True)
            reviews = []
            for i,d in enumerate(dirs[:3]):
                r = json.loads(call_llm(f"""{dims_txt}
评审这个情节走向，逐维度评分(1-10)+证据。
走向：{d['what']}
JSON:{{"scores":[{{"dimension":"..","score":8,"note":".."}}]}}""","文学评审。只输出 JSON。",0.0))
                reviews.append({"title":d.get("title","?"),"scores":r.get("scores",[])})
            rc.write_text(json.dumps(reviews,ensure_ascii=False,indent=2),"utf-8")
            avgs = [sum(s["score"] for s in r["scores"])/len(r["scores"]) if r.get("scores") else 0 for r in reviews]
            print(f"✓ avg scores: {[f'{a:.1f}' for a in avgs]}")

        # 4. Pairwise blind ranking (p10 method)
        pc = RESULTS_DIR/f"pairwise_{sid}.json"
        if pc.exists(): pw_results = json.loads(pc.read_text("utf-8"))
        else:
            print("  pairwise 盲评...")
            dims_pw = ["rationality","creativity","motif_fit","narrative_value"]
            pw = {}
            wins = {i:{d:0 for d in dims_pw} for i in range(len(dirs))}
            for dim in dims_pw:
                for i in range(len(dirs)):
                    for j in range(i+1,len(dirs)):
                        r = pairwise((f"走向{i}",dirs[i]["what"]),(f"走向{j}",dirs[j]["what"]),dim,f"场景《{sc['name']}》")
                        w = r["winner"]
                        if w=="A": wins[i][dim]+=1
                        elif w=="B": wins[j][dim]+=1
                        else: wins[i][dim]+=0.5; wins[j][dim]+=0.5
            pc.write_text(json.dumps({"wins":wins},ensure_ascii=False,indent=2),"utf-8")
            pw_results = {"wins":wins}
            print("  ✓")
            for i in range(len(dirs)):
                w = wins[i]
                total = sum(w.values())
                print(f"    {dirs[i].get('title','?'):<12} total_wins={total:.0f}")

        # Report
        print(f"\n## {sid}")
        for i,d in enumerate(dirs):
            v = validations[i] if i<len(validations) else {}
            ok = "✓" if v.get("causal_chain_ok") else "✗"
            issue = v.get("issues",[])
            print(f"  {ok} {d.get('title','?'):<12} {d.get('what','')[:60]}...")
            if issue: print(f"     issues: {'; '.join(issue[:2])}")

    (RESULTS_DIR/"full_report.json").write_text(json.dumps({
        "directions": {s["id"]: [d for d in all_dirs.get(s["id"],[])] for s in SCENES},
        "validations": {s["id"]: json.loads((RESULTS_DIR/f"validate_{s['id']}.json").read_text("utf-8")) 
                        if (RESULTS_DIR/f"validate_{s['id']}.json").exists() else [] 
                        for s in SCENES},
        "style_reviews": {s["id"]: json.loads((RESULTS_DIR/f"style_review_{s['id']}.json").read_text("utf-8"))
                         if (RESULTS_DIR/f"style_review_{s['id']}.json").exists() else []
                         for s in SCENES},
        "pairwise": {s["id"]: json.loads((RESULTS_DIR/f"pairwise_{s['id']}.json").read_text("utf-8"))
                    if (RESULTS_DIR/f"pairwise_{s['id']}.json").exists() else {}
                    for s in SCENES},
    }, ensure_ascii=False, indent=2), "utf-8")
    print(f"\n结果: {RESULTS_DIR}")

if __name__=="__main__": main()
