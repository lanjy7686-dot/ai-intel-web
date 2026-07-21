from pathlib import Path

path = Path(__file__).resolve().parents[1] / "index.html"
text = path.read_text(encoding="utf-8")
marker = "<!-- FRESHNESS_UI_V2 -->"
if marker in text:
    print("freshness UI already applied")
    raise SystemExit(0)

text = text.replace("</title>", "</title>\n" + marker, 1)
text = text.replace(
    '<span id="scopeStatus" class="pill">扩大范围：加载中</span>',
    '<span id="freshStatus" class="pill">近24小时：加载中</span>',
)
text = text.replace(
    '<option value="1">近24小时</option><option value="3">近3天</option><option value="7" selected>近7天</option>',
    '<option value="1" selected>近24小时</option><option value="3">近3天</option><option value="7">近7天</option>',
)
text = text.replace(
    '<div><h2>重点赛道实时搜索</h2><div class="sub">新增全球/国内AI巨头、芯片算力、数据中心、具身智能与前沿模型专题。</div></div>',
    '<div><h2>最新专题搜索</h2><div class="sub">专题搜索默认限定近24小时；切换时间后会自动加入时间条件。</div></div>',
)
text = text.replace(
    '紫色边框打开Google新闻专题搜索；绿色/黄色按钮用于微信公众号。网页自动聚合与实时搜索互为补充。',
    '紫色按钮会在Google新闻查询中加入 when:1d/3d 等时间限定；绿色/黄色按钮用于微信公众号。没有可靠发布时间的旧内容不再进入最新列表。',
)

old_news = 'if(platform==="news")url=`https://news.google.com/search?q=${q}&hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans`;'
new_news = 'if(platform==="news")url=`https://news.google.com/search?q=${encodeURIComponent(`(${raw}) when:${Math.max(1,Number(days)||1)}d`)}&hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans`;'
if old_news not in text:
    raise RuntimeError("Google News URL pattern not found")
text = text.replace(old_news, new_news)

old_format = 'function formatTime(iso){const d=new Date(iso);if(Number.isNaN(d.getTime()))return"";return new Intl.DateTimeFormat("zh-CN",{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}).format(d)}'
new_format = old_format + '\nfunction relativeTime(iso){const d=new Date(iso),seconds=Math.max(0,(Date.now()-d.getTime())/1000);if(Number.isNaN(d.getTime()))return"时间未知";if(seconds<300)return"刚刚";if(seconds<3600)return`${Math.floor(seconds/60)}分钟前`;if(seconds<86400)return`${Math.floor(seconds/3600)}小时前`;return`${Math.floor(seconds/86400)}天前`}'
if old_format not in text:
    raise RuntimeError("formatTime pattern not found")
text = text.replace(old_format, new_format)

text = text.replace(
    '<span>· ${formatTime(a.published_at)}</span>',
    '<span>· 发布时间 <strong title="${escapeHtml(formatTime(a.published_at))}">${escapeHtml(relativeTime(a.published_at))}</strong></span>',
)

old_load = 'const expanded=store.filter(a=>["巨头企业","产业链","新技术"].includes(a.source_type)).length;el("scopeStatus").textContent=`重点专题：${expanded} 条`'
new_load = 'const fp=data.freshness_policy||{};el("freshStatus").textContent=`近24小时：${fp.last_24h||0} 条`'
if old_load not in text:
    raise RuntimeError("loadData status pattern not found")
text = text.replace(old_load, new_load)
text = text.replace(
    'el("scopeStatus").textContent="扩大范围：待更新"',
    'el("freshStatus").textContent="近24小时：待更新"',
)

toolbar_end = '</section>\n\n<section class="search-panel">'
notice = '''</section>

<div class="notice show"><strong>最新规则：</strong>默认只看近24小时；缺少真实发布时间、发布时间异常或超过来源时间窗口的内容会被剔除，不再把旧文章显示成最新。</div>

<section class="search-panel">'''
if toolbar_end not in text:
    raise RuntimeError("toolbar insertion point not found")
text = text.replace(toolbar_end, notice, 1)

path.write_text(text, encoding="utf-8")
print("freshness UI applied")
