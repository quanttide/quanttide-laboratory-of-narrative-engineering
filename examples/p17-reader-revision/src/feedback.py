"""Step 4: 作者反馈 — 生成独立 HTML 页面

用法：
    python -m src feedback       # 生成 feedback.html
    python -m src feedback send  # + 将已保存的反馈写回 JSON 文件
"""
import json, webbrowser
from pathlib import Path
from datetime import datetime
from packages.io import save_json
from src.config import TEXT_POINTS, DATA_OUTPUT


FEEDBACK_KEYS = {
    "accurate": "准确——契约解读与我想的一致",
    "inaccurate": "不准确——契约解读偏离了我的本意",
}


def _load_all():
    """加载所有已保存的结构化数据。"""
    data = {}
    for tp in TEXT_POINTS:
        tid = tp["id"]
        entry = {"point": tp}
        for key in ("contract", "reader", "side_by_side"):
            f = DATA_OUTPUT / f"{tid}_{key}.json"
            if f.exists():
                entry[key] = json.loads(f.read_text("utf-8"))
        # 已有反馈
        f = DATA_OUTPUT / f"{tid}_feedback.json"
        if f.exists():
            entry["feedback"] = json.loads(f.read_text("utf-8"))
        data[tid] = entry
    return data


def _build_html(data):
    """生成独立 HTML（数据通过 JSON script 标签嵌入，JS 逻辑独立）。"""
    json_str = json.dumps(data, ensure_ascii=False)
    # 替换 </script> 防止 HTML 解析中断
    json_str = json_str.replace("</script>", "<\\/script>")
    server_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:#f5f5f5; color:#222; padding:20px; }
.container { max-width:720px; margin:0 auto; }
h1 { font-size:18px; margin-bottom:4px; }
.sub { color:#666; font-size:13px; margin-bottom:20px; }
.nav { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
.nav button { padding:6px 16px; border:1px solid #ccc; border-radius:6px; background:#fff; cursor:pointer; font-size:13px; }
.nav button.active { background:#0066cc; color:#fff; border-color:#0066cc; }
.nav button.done { border-color:#22c55e; }
.card { background:#fff; border-radius:8px; padding:20px; margin-bottom:16px; display:none; }
.card.active { display:block; }
.meta { font-size:13px; color:#666; margin-bottom:12px; }
.quote { background:#f8f8f8; border-left:3px solid #0066cc; padding:12px 16px; margin-bottom:16px; font-size:14px; line-height:1.7; border-radius:0 6px 6px 0; }
.section { margin-bottom:12px; }

.fb { margin-top:16px; padding-top:16px; border-top:1px solid #eee; display:flex; gap:12px; align-items:center; }
.fb button { padding:6px 20px; border:2px solid #ccc; border-radius:6px; background:#fff; cursor:pointer; font-size:14px; }
.fb button.sel { border-color:#0066cc; background:#e8f0fe; font-weight:600; }
.fb .saved { color:#22c55e; font-size:13px; display:none; }
.actions { margin-top:20px; text-align:center; display:flex; gap:8px; justify-content:center; }
.actions button { padding:8px 20px; border:none; border-radius:6px; cursor:pointer; font-size:13px; }
.btn1 { background:#0066cc; color:#fff; }
.btn2 { background:#eee; color:#666; }
#done-msg { text-align:center; padding:40px; color:#22c55e; display:none; }
#done-msg.show { display:block; }
"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>p17 作者反馈</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <h1>p17 写作契约 vs 读者回响</h1>
  <p class="sub">对每个文本点判断：契约解读是否准确？</p>
  <div class="nav" id="nav"></div>
  <div id="done-msg">所有文本点已反馈完毕</div>
  <div id="cards"></div>
  <div class="actions">
    <button class="btn1" onclick="doExport()">导出反馈</button>
    <button class="btn2" onclick="doReset()">重置</button>
  </div>
  <p class="sub" style="margin-top:12px">{server_ts}</p>
</div>
<script type="application/json" id="payload">{json_str}</script>
<script>
var ALL = JSON.parse(document.getElementById('payload').textContent);
var IDS = {json.dumps([tp["id"] for tp in TEXT_POINTS], ensure_ascii=False)};
var FB = {{}};

try {{ var s = localStorage.getItem('p17fb'); if (s) FB = JSON.parse(s); }} catch(e) {{}}

function init() {{
  var nav = document.getElementById('nav');
  var cards = document.getElementById('cards');
  var hn = '', hc = '';
  IDS.forEach(function(id, i) {{
    var d = ALL[id];
    if (!d) return;
    hn += '<button class="'+(FB[id]?'done':'')+'" onclick="go('+i+')" id="nb-'+i+'">'+id+(FB[id]?' ✓':'')+'</button>';
    hc += _card(id, d, i);
  }});
  nav.innerHTML = hn;
  cards.innerHTML = hc;
  go(0);
  _done();
}}

function _card(id, d, idx) {{
  var p = d.point||{{}};
  var r = d.reader||{{}};
  var ratings = r.scene_ratings||{{}};
  var ks = r.key_signals||{{}};

  // 从评分数据生成创作者可读的读者反馈
  function rd(pid, field) {{ var v=ratings[pid]; return v?v[field]:null; }}
  var p3cl = rd('P3','cliche_level');
  var p1cl = rd('P1','cliche_level');
  var p3cr = rd('P3','character_realism');
  var p1cr = rd('P1','character_realism');
  var pair = ks.max_divergence_pair||[];
  var anom = (ks.anomalies||[])[0]||{{}};

  var lines = [];
  // cliche 对比：最直观的维度
  if (p3cl!=null && p1cl!=null) {{
    var diff = Math.abs(p3cl - p1cl);
    lines.push('P3（老书虫）套路感='+p3cl.toFixed(1)+' — '+ (p3cl<2?'不太套路':p3cl<3?'中等':p3cl>=3?'觉得偏套路':''));
    lines.push('P1（甜宠）套路感='+p1cl.toFixed(1)+' — '+ (p1cl<2?'不太套路':p1cl<3?'中等':p1cl>=3?'觉得偏套路':''));
    if (diff>1) lines.push('差 '+diff.toFixed(1)+' 分，分歧明显');
  }}
  // 角色真实感对比
  if (p3cr!=null && p1cr!=null && Math.abs(p3cr-p1cr)>1.5) {{
    lines.push('角色真实感：P3打'+p3cr.toFixed(1)+' vs P1打'+p1cr.toFixed(1)+'，差 '+Math.abs(p3cr-p1cr).toFixed(1)+' 分');
  }}
  // 异常值
  if (anom.profile) {{
    lines.push(anom.profile+' 觉得「'+anom.field+'」='+anom.value+'（其余画像平均 '+anom.mean.toFixed(1)+'）');
  }}
  var readerHtml = lines.length ? lines.join('<br>') : '<span style="color:#999">评分数据加载中</span>';

  var fv = FB[id]||'';
  return '<div class="card'+(idx===0?' active':'')+'" id="cd-'+idx+'">'+
    '<div class="meta">'+id+' '+p.location+'（'+p.type+'）</div>'+
    '<div class="quote">'+p.quote+'</div>'+
    '<div style="background:#f5f5f5;border-radius:6px;padding:12px;margin-bottom:8px;font-size:13px;line-height:1.6">'+
      readerHtml+
    '</div>'+
    '<div class="fb">'+
    '<button class="'+(fv==='acc'?'sel':'')+'" onclick="fb(\\''+id+'\\',\\'acc\\')">准确</button>'+
    '<button class="'+(fv==='inacc'?'sel':'')+'" onclick="fb(\\''+id+'\\',\\'inacc\\')">不准确</button>'+
    '<span class="saved" id="ok-'+id+'" style="display:'+(fv?'inline':'none')+'">已保存</span>'+
    '</div></div>';
}}

function go(i) {{
  document.querySelectorAll('.card').forEach(function(c,j){{c.classList.toggle('active',j===i);}});
  document.querySelectorAll('.nav button').forEach(function(b,j){{b.classList.toggle('active',j===i);}});
}}

function fb(id, val) {{
  FB[id] = val;
  try {{ localStorage.setItem('p17fb', JSON.stringify(FB)); }} catch(e) {{}}
  var i = IDS.indexOf(id);
  if (i<0) return;
  var cd = document.getElementById('cd-'+i);
  if (cd) {{
    cd.querySelectorAll('.fb button').forEach(function(b){{b.classList.remove('sel');}});
    cd.querySelectorAll('.fb button').forEach(function(b){{
      if ((b.textContent.trim()==='准确'&&val==='acc')||(b.textContent.trim()==='不准确'&&val==='inacc')) b.classList.add('sel');
    }});
    var st = cd.querySelector('.saved');
    if (st) st.style.display = 'inline';
  }}
  var nb = document.getElementById('nb-'+i);
  if (nb) {{ nb.classList.add('done'); nb.textContent = id+' ✓'; }}
  _done();
}}

function _done() {{
  var el = document.getElementById('done-msg');
  if (el) el.classList.toggle('show', Object.keys(FB).length >= IDS.length);
}}

function doExport() {{
  var out = {{}};
  IDS.forEach(function(id) {{ if (FB[id]) out[id] = {{text_point_id:id, choice:FB[id], timestamp:new Date().toISOString()}}; }});
  var b = new Blob([JSON.stringify(out,null,2)], {{type:'application/json'}});
  var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'p17_feedback.json'; a.click();
}}

function doReset() {{
  if (!confirm('重置所有反馈？')) return;
  FB = {{}};
  try {{ localStorage.removeItem('p17fb'); }} catch(e) {{}}
  IDS.forEach(function(id,i){{
    var cd=document.getElementById('cd-'+i); if(cd){{cd.querySelectorAll('.fb button').forEach(function(b){{b.classList.remove('sel');}});var st=cd.querySelector('.saved');if(st)st.style.display='none';}}
    var nb=document.getElementById('nb-'+i); if(nb){{nb.classList.remove('done');nb.textContent=id;}}
  }});
  _done();
}}

window.onload = init;
</script>
</body>
</html>"""


def generate():
    """加载数据 → 生成 feedback.html"""
    data = _load_all()
    html = _build_html(data)
    path = DATA_OUTPUT / "feedback.html"
    path.write_text(html, encoding="utf-8")
    print(f"✅ 已生成: {path}")
    webbrowser.open(str(path))
    return path


def write_back():
    """将浏览器导出的反馈 JSON 写回 data/output 目录。"""
    import glob
    # 显示说明
    print("=" * 56)
    print("写回反馈")
    print("=" * 56)
    print()
    print("1. 在浏览器中完成反馈后，点击「导出反馈」下载 JSON 文件")
    print("2. 将下载的文件放到 data/output/ 目录下")
    print("3. 运行这个命令写回：python -m src feedback writeback <文件路径>")
    print()


def write_file(export_path):
    """将导出的反馈 JSON 写回单个 _feedback.json 文件。"""
    export = json.loads(Path(export_path).read_text("utf-8"))
    count = 0
    for tid, fb in export.items():
        path = DATA_OUTPUT / f"{tid}_feedback.json"
        save_json(path, {
            "text_point_id": tid,
            "choice": fb.get("choice"),
            "comment": None,
            "feedback_time": fb.get("timestamp", datetime.now().isoformat()),
        })
        count += 1
        print(f"  ✅ {tid} → {fb.get('choice')}")
    print(f"\n已写回 {count} 条反馈")
