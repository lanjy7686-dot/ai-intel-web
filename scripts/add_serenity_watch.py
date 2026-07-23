from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
MARKER = "<!-- SERENITY_X_WATCH_V1 -->"

html = INDEX.read_text(encoding="utf-8")
if MARKER in html:
    print("Serenity watch panel already installed")
    raise SystemExit(0)

html = html.replace(
    "<!-- BLOOMBERG_CLS_FOCUS_V1 -->",
    "<!-- BLOOMBERG_CLS_FOCUS_V1 -->\n" + MARKER,
    1,
)

html = html.replace(
    "彭博社 · 财联社 · 主流媒体 · 巨头企业 · 产业链 · 新技术",
    "Serenity · 彭博社 · 财联社 · 主流媒体 · 巨头企业 · 产业链 · 新技术",
    1,
)

style_patch = """
.watch-panel{padding:18px;margin-bottom:18px}.watch-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:14px}.watch-head h2{margin:0;font-size:19px}.watch-handle{color:var(--accent);font-weight:700}.watch-actions{display:flex;gap:8px;flex-wrap:wrap}.watch-btn{display:inline-flex;align-items:center;justify-content:center;padding:9px 12px;border:1px solid var(--line);border-radius:11px;background:#0a1728;text-decoration:none;font-size:12px}.watch-btn:hover{border-color:var(--accent);color:var(--accent)}.watch-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(280px,.55fr);gap:16px}.watch-timeline{min-height:560px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#081523}.watch-info{display:grid;gap:10px;align-content:start}.watch-card{padding:14px;border:1px solid var(--line);border-radius:13px;background:#0a1728}.watch-card h3{font-size:14px;margin:0 0 8px}.watch-card p{margin:0;color:#c8d6e7;font-size:13px;line-height:1.7}.watch-searches{display:grid;gap:8px}.watch-searches a{display:block;padding:10px 11px;border:1px solid var(--line);border-radius:10px;text-decoration:none;font-size:12px;background:#081523}.watch-searches a:hover{border-color:var(--accent);color:var(--accent)}
"""
html = html.replace(
    "@media(max-width:1180px)",
    style_patch + "@media(max-width:1180px)",
    1,
)
html = html.replace(
    "@media(max-width:980px){.layout{grid-template-columns:1fr}",
    "@media(max-width:980px){.watch-grid{grid-template-columns:1fr}.layout{grid-template-columns:1fr}",
    1,
)
html = html.replace(
    "@media(max-width:680px){header{align-items:flex-start}",
    "@media(max-width:680px){.watch-head{display:block}.watch-actions{margin-top:10px}.watch-timeline{min-height:500px}header{align-items:flex-start}",
    1,
)

html = html.replace(
    '<button class="platform-tab" data-filter="x">X</button>',
    '<button class="platform-tab" data-filter="watcher">重点博主</button>\n    <button class="platform-tab" data-filter="x">X</button>',
    1,
)

watch_links = '''    <a class="search-link latest" data-group="watcher" data-platform="x" data-query="from:aleabitoreddit -filter:replies" data-days="1">Serenity · 仅原创动态</a>
    <a class="search-link latest" data-group="watcher" data-platform="x" data-query="from:aleabitoreddit (AI OR semiconductor OR supply chain)" data-days="1">Serenity · AI供应链</a>
    <a class="search-link latest" data-group="watcher" data-platform="x" data-query="from:aleabitoreddit (NVIDIA OR AMD OR HBM OR memory OR photonics OR datacenter)" data-days="1">Serenity · 芯片算力</a>
'''
html = html.replace(
    '    <a class="search-link" data-group="x" data-platform="x" data-query="AI chips datacenter robotics agent model release">X AI产业动态</a>',
    watch_links + '    <a class="search-link" data-group="x" data-platform="x" data-query="AI chips datacenter robotics agent model release">X AI产业动态</a>',
    1,
)

panel = '''
<section class="watch-panel panel" id="serenityWatch">
  <div class="watch-head">
    <div>
      <h2>重点博主｜Serenity <span class="watch-handle">@aleabitoreddit</span></h2>
      <div class="sub">AI与半导体供应链研究。下方使用X官方公开时间线，博主发帖后会自动更新，不调用付费API。</div>
    </div>
    <div class="watch-actions">
      <a class="watch-btn" href="https://x.com/aleabitoreddit" target="_blank" rel="noopener">打开X主页</a>
      <a class="watch-btn" href="https://x.com/search?q=from%3Aaleabitoreddit%20-filter%3Areplies&src=typed_query&f=live" target="_blank" rel="noopener">只看原创帖</a>
    </div>
  </div>
  <div class="watch-grid">
    <div class="watch-timeline">
      <a class="twitter-timeline" data-theme="dark" data-height="620" data-dnt="true" data-chrome="noheader nofooter noborders transparent" href="https://x.com/aleabitoreddit">Serenity 的最新公开动态</a>
    </div>
    <div class="watch-info">
      <div class="watch-card">
        <h3>关注重点</h3>
        <p>AI算力、GPU、HBM与存储、光通信、数据中心、电力能源、半导体供应链及相关公司动态。内容仅作信息跟踪，不构成投资建议。</p>
      </div>
      <div class="watch-card">
        <h3>快捷查看</h3>
        <div class="watch-searches">
          <a href="https://x.com/search?q=from%3Aaleabitoreddit%20(AI%20OR%20semiconductor%20OR%20%22supply%20chain%22)&src=typed_query&f=live" target="_blank" rel="noopener">AI与半导体供应链</a>
          <a href="https://x.com/search?q=from%3Aaleabitoreddit%20(NVIDIA%20OR%20AMD%20OR%20HBM%20OR%20memory)&src=typed_query&f=live" target="_blank" rel="noopener">芯片、HBM与存储</a>
          <a href="https://x.com/search?q=from%3Aaleabitoreddit%20(photonics%20OR%20datacenter%20OR%20power%20OR%20energy)&src=typed_query&f=live" target="_blank" rel="noopener">光通信、数据中心与能源</a>
        </div>
      </div>
      <div class="watch-card">
        <h3>显示说明</h3>
        <p>时间线由X官方组件提供。浏览器拦截第三方Cookie、网络限制或未登录时可能不显示，可使用上方“打开X主页”查看。</p>
      </div>
    </div>
  </div>
</section>
<script async src="https://platform.x.com/widgets.js" charset="utf-8"></script>
'''
html = html.replace(
    '<div id="sourceNotice" class="notice" style="display:none"></div>',
    panel + '\n<div id="sourceNotice" class="notice" style="display:none"></div>',
    1,
)

INDEX.write_text(html, encoding="utf-8")
print("Serenity X watch panel installed")
