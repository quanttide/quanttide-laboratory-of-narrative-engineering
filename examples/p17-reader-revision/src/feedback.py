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
.stitle { font-size:12px; font-weight:600; color:#888; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px; }
.tag { display:inline-block; font-size:11px; padding:1px 8px; border-radius:10px; margin:2px 4px 2px 0; }
.tag.ok { background:#dcfce7; color:#166534; }
.tag.err { background:#fee2e2; color:#991b1b; }
.tag.warn { background:#fef9c3; color:#854d0e; }
.signal { font-size:13px; color:#444; line-height:1.6; }
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
  var p = d.point||{{}}, c = d.contract||{{}}, r = d.reader||{{}};
  var dims = c.style&&c.style.touched_dimensions||[];
  var keeps = dims.filter(function(v){{return v.nature==='遵守'||v.nature==='对齐';}});
  var breaks = dims.filter(function(v){{return v.nature==='违反'||v.nature==='偏离';}});
  var mids = dims.filter(function(v){{return v.nature!=='遵守'&&v.nature!=='违反'&&v.nature!=='对齐'&&v.nature!=='偏离';}});

  // 一句话结论
  var verdict = '';
  if (breaks.length>0) {{
    verdict = '<div style="margin-bottom:12px;padding:8px 12px;border-radius:6px;background:#fef2f2;color:#991b1b;font-size:13px;font-weight:500">⚠️ 契约判定：存在 '+breaks.length+' 处偏离/违反</div>';
  }} else if (mids.length>0) {{
    verdict = '<div style="margin-bottom:12px;padding:8px 12px;border-radius:6px;background:#fffbeb;color:#854d0e;font-size:13px;font-weight:500">📐 契约判定：边缘情况，需作者自行判断</div>';
  }} else {{
    verdict = '<div style="margin-bottom:12px;padding:8px 12px;border-radius:6px;background:#f0fdf4;color:#166534;font-size:13px;font-weight:500">✅ 契约判定：全部遵守</div>';
  }}

  function _tag(arr, cls) {{ return arr.map(function(v){{return '<span class="tag '+cls+'">'+v.dimension+'</span>';}}).join(''); }}

  var tags = '';
  if (breaks.length) tags += '<div style="margin-bottom:4px">'+_tag(breaks,'err')+'</div>';
  if (mids.length) tags += '<div style="margin-bottom:4px">'+_tag(mids,'warn')+'</div>';
  if (keeps.length) tags += '<div>'+_tag(keeps,'ok')+'</div>';

  // 母题简化为一行
  var ms = (c.motif&&c.motif.touched_motifs||[]);
  var mtxt = ms.length ? '<div style="font-size:12px;color:#666;margin-top:6px">母题：'+ms.map(function(m){{return m.motif+'→'+m.alignment;}}).join('、')+'</div>' : '';

  // 读者信号：只列最关键的一条
  var sig = '';
  var ks = r.key_signals||{{}};
  var pair = ks.max_divergence_pair;
  if (pair) {{
    var colors = {{P1:'#e8d5f5',P2:'#d5e8f5',P3:'#f5d5d5',P4:'#d5f5e8',P5:'#f5e8d5'}};
    sig += '<div style="font-size:13px;line-height:1.6;padding:8px 0"><span style="font-weight:500">读者分歧</span>：'+pair[0]+' 和 '+pair[1]+' 在「'+pair[2]+'」上差距 <strong>'+pair[3]+'</strong></div>';
  }}
  var anom = ks.anomalies||[];
  if (anom.length) {{
    var a=anom[0];
    sig += '<div style="font-size:13px;color:#666">最异常：'+a.profile+' 给 '+a.field+' 打 '+a.value+'（均值 '+a.mean+'）</div>';
  }}

  var fv = FB[id]||'';
  return '<div class="card'+(idx===0?' active':'')+'" id="cd-'+idx+'">'+
    '<div class="meta">'+id+' '+p.location+'（'+p.type+'）</div>'+
    '<div class="quote">'+p.quote+'</div>'+
    verdict+
    (tags?'<div style="margin-bottom:8px">'+tags+mtxt+'</div>':'')+
    (sig?'<div style="border-top:1px solid #eee;padding-top:8px;margin-top:8px">'+sig+'</div>':'')+
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
