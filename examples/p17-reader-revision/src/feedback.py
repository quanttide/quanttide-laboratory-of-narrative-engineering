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
    """生成独立 HTML（所有数据内嵌，无外部依赖）。"""
    tp_ids = [tp["id"] for tp in TEXT_POINTS]
    json_data = json.dumps(data, ensure_ascii=False)
    server_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>p17 作者反馈</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f5f5; color: #222; padding: 20px; }}
  .container {{ max-width: 720px; margin: 0 auto; }}
  h1 {{ font-size: 18px; margin-bottom: 4px; }}
  .sub {{ color: #666; font-size: 13px; margin-bottom: 20px; }}
  .nav {{ display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }}
  .nav button {{ padding: 6px 16px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }}
  .nav button.active {{ background: #0066cc; color: #fff; border-color: #0066cc; }}
  .nav button.done {{ border-color: #22c55e; }}
  .nav button .badge {{ font-size: 11px; margin-left: 4px; color: #22c55e; }}
  .card {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 16px; display: none; }}
  .card.active {{ display: block; }}
  .meta {{ font-size: 13px; color: #666; margin-bottom: 12px; }}
  .quote {{ background: #f8f8f8; border-left: 3px solid #0066cc; padding: 12px 16px; margin-bottom: 16px; font-size: 14px; line-height: 1.7; border-radius: 0 6px 6px 0; }}
  .section {{ margin-bottom: 12px; }}
  .section-title {{ font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
  .tag {{ display: inline-block; font-size: 11px; padding: 1px 8px; border-radius: 10px; margin: 2px 4px 2px 0; }}
  .tag.compliant {{ background: #dcfce7; color: #166534; }}
  .tag.violation {{ background: #fee2e2; color: #991b1b; }}
  .tag.borderline {{ background: #fef9c3; color: #854d0e; }}
  .tag.aligned {{ background: #dcfce7; color: #166534; }}
  .tag.deviated {{ background: #fee2e2; color: #991b1b; }}
  .signal {{ font-size: 13px; color: #444; line-height: 1.6; }}
  .feedback-area {{ margin-top: 16px; padding-top: 16px; border-top: 1px solid #eee; }}
  .feedback-btn {{ padding: 8px 24px; border: 2px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; margin-right: 8px; }}
  .feedback-btn.selected {{ border-color: #0066cc; background: #e8f0fe; font-weight: 600; }}
  .feedback-btn.saved {{ border-color: #22c55e; }}
  .status {{ font-size: 13px; color: #22c55e; margin-top: 8px; display: none; }}
  .actions {{ margin-top: 20px; text-align: center; }}
  .actions button {{ padding: 8px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }}
  .btn-export {{ background: #0066cc; color: #fff; }}
  .btn-reset {{ background: #eee; color: #666; margin-left: 8px; }}
  #all-done {{ text-align: center; padding: 40px; color: #22c55e; display: none; }}
  #all-done.show {{ display: block; }}
</style>
</head>
<body>
<div class="container">
  <h1>p17 写作契约 vs 读者回响</h1>
  <p class="sub">对每个文本点判断：契约解读是否准确？</p>

  <div class="nav" id="nav"></div>
  <div id="all-done">🎉 所有文本点已反馈完毕</div>
  <div id="cards"></div>

  <div class="actions">
    <button class="btn-export" onclick="exportFeedback()">⬇ 导出反馈</button>
    <button class="btn-reset" onclick="resetAll()">重置</button>
  </div>
  <p class="sub" style="margin-top:12px">服务器数据时间：{server_ts}</p>
</div>

<script>
var ALL_DATA = {json_data};
var TP_IDS = {json.dumps(tp_ids, ensure_ascii=False)};
var FEEDBACK = {{}};

// 初始化：从 localStorage 恢复
try {{
  var saved = localStorage.getItem('p17_feedback');
  if (saved) FEEDBACK = JSON.parse(saved);
}} catch(e) {{}}

function init() {{
  var nav = document.getElementById('nav');
  var cards = document.getElementById('cards');
  var htmlNav = '', htmlCards = '';
  TP_IDS.forEach(function(id, i) {{
    var d = ALL_DATA[id];
    if (!d) return;
    var fb = FEEDBACK[id] || null;
    var doneClass = fb ? 'done' : '';
    var badge = fb ? '✓' : '';
    htmlNav += '<button class="' + doneClass + '" onclick="showCard(' + i + ')" id="nav-' + i + '">' + id + ' <span class="badge">' + badge + '</span></button>';
    htmlCards += buildCard(id, d, i, fb);
  }});
  nav.innerHTML = htmlNav;
  cards.innerHTML = htmlCards;
  showCard(0);
  updateAllDone();
}}

function buildCard(id, d, idx, fb) {{
  var c = d.contract || {{}};
  var r = d.reader || {{}};
  var s = d.side_by_side || {{}};
  var p = d.point || {{}};

  // 契约标签
  var tags = '';
  var dims = (c.style && c.style.touched_dimensions) || [];
  dims.forEach(function(dim) {{
    var n = dim.nature || '';
    var cls = n === '遵守' ? 'compliant' : n === '违反' ? 'violation' : 'borderline';
    tags += '<span class="tag ' + cls + '">' + dim.dimension + ' → ' + n + '</span>';
  }});
  var motifs = (c.motif && c.motif.touched_motifs) || [];
  motifs.forEach(function(m) {{
    var a = m.alignment || '';
    var cls = a === '对齐' ? 'aligned' : a === '偏离' ? 'deviated' : 'borderline';
    tags += '<span class="tag ' + cls + '">' + m.motif + ' → ' + a + '</span>';
  }});

  // 读者信号
  var signals = '';
  var ks = (r.key_signals) || {{}};
  if (ks.max_variance_dimension && ks.max_variance_dimension[0]) {{
    signals += '<div class="signal">读者分歧最大维度：' + ks.max_variance_dimension[0] + '（方差 ' + ks.max_variance_dimension[1] + '）</div>';
  }}
  if (ks.max_divergence_pair) {{
    var pair = ks.max_divergence_pair;
    signals += '<div class="signal">最分歧画像对：' + pair[0] + ' vs ' + pair[1] + '（' + pair[2] + ' 差距 ' + pair[3] + '）</div>';
  }}
  (ks.anomalies || []).forEach(function(a) {{
    signals += '<div class="signal">异常：' + a.profile + ' ' + a.field + '=' + a.value + '（偏差 ' + a.deviation + '）</div>';
  }});

  var fbVal = FEEDBACK[id] || '';
  var selA = fbVal === 'accurate' ? 'selected' : '';
  var selB = fbVal === 'inaccurate' ? 'selected' : '';
  var saved = fbVal ? 'saved' : '';

  return '<div class="card' + (idx===0?' active':'') + '" id="card-' + idx + '">' +
    '<div class="meta">' + id + ' ' + p.location + '（' + p.type + '）</div>' +
    '<div class="quote">' + p.quote + '</div>' +
    '<div class="section"><div class="section-title">契约判断</div>' + tags + '</div>' +
    (signals ? '<div class="section"><div class="section-title">读者回响</div>' + signals + '</div>' : '') +
    '<div class="feedback-area">' +
      '<button class="feedback-btn ' + selA + ' ' + saved + '" onclick="setFeedback(\'' + id + '\',\'accurate\')">✅ 准确</button>' +
      '<button class="feedback-btn ' + selB + ' ' + saved + '" onclick="setFeedback(\'' + id + '\',\'inaccurate\')">❌ 不准确</button>' +
      '<div class="status" id="status-' + id + '">已保存 ✓</div>' +
    '</div>' +
  '</div>';
}}

function showCard(idx) {{
  document.querySelectorAll('.card').forEach(function(c, i) {{ c.classList.toggle('active', i===idx); }});
  document.querySelectorAll('.nav button').forEach(function(b, i) {{ b.classList.toggle('active', i===idx); }});
}}

function setFeedback(id, val) {{
  FEEDBACK[id] = val;
  try {{ localStorage.setItem('p17_feedback', JSON.stringify(FEEDBACK)); }} catch(e) {{}}
  // 刷新当前卡片
  var idx = TP_IDS.indexOf(id);
  if (idx >= 0) {{
    var card = document.getElementById('card-' + idx);
    var navBtn = document.getElementById('nav-' + idx);
    if (card) {{
      card.querySelectorAll('.feedback-btn').forEach(function(b) {{
        b.classList.remove('selected', 'saved');
        if (b.textContent.includes('准确') && val === 'accurate') b.classList.add('selected', 'saved');
        if (b.textContent.includes('不准确') && val === 'inaccurate') b.classList.add('selected', 'saved');
      }});
      var st = card.querySelector('.status');
      if (st) st.style.display = 'block';
    }}
    if (navBtn) {{
      navBtn.classList.add('done');
      var badge = navBtn.querySelector('.badge');
      if (!badge) {{ badge = document.createElement('span'); badge.className = 'badge'; navBtn.appendChild(badge); }}
      badge.textContent = '✓';
    }}
    updateAllDone();
  }}
}}

function updateAllDone() {{
  var done = Object.keys(FEEDBACK).length;
  var el = document.getElementById('all-done');
  if (el) el.classList.toggle('show', done >= TP_IDS.length);
}}

function exportFeedback() {{
  var output = {{}};
  TP_IDS.forEach(function(id) {{
    if (FEEDBACK[id]) {{
      output[id] = {{ text_point_id: id, choice: FEEDBACK[id], timestamp: new Date().toISOString() }};
    }}
  }});
  var blob = new Blob([JSON.stringify(output, null, 2)], {{type: 'application/json'}});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'p17_feedback_export.json';
  a.click();
}}

function resetAll() {{
  if (!confirm('重置所有反馈？')) return;
  FEEDBACK = {{}};
  try {{ localStorage.removeItem('p17_feedback'); }} catch(e) {{}}
  TP_IDS.forEach(function(id, i) {{
    var card = document.getElementById('card-' + i);
    if (card) {{
      card.querySelectorAll('.feedback-btn').forEach(function(b) {{ b.classList.remove('selected', 'saved'); }});
      var st = card.querySelector('.status');
      if (st) st.style.display = 'none';
    }}
    var navBtn = document.getElementById('nav-' + i);
    if (navBtn) navBtn.classList.remove('done');
  }});
  updateAllDone();
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
