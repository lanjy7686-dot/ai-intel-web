from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

html = INDEX.read_text(encoding="utf-8")
marker = "<!-- ROBUST_SEARCH_LINKS_V1 -->"

if marker not in html:
    anchor = "<!-- LLM_NEWS_MODULE_V1 -->"
    if anchor in html:
        html = html.replace(anchor, anchor + "\n" + marker, 1)
    else:
        html = html.replace("</head>", marker + "\n</head>", 1)

old_function = '''function openPlatformSearch(platform,query,days=1){const raw=(query||"人工智能").trim(),q=encodeURIComponent(raw);let url="";if(platform==="news")url=`https://news.google.com/search?q=${encodeURIComponent(`(${raw}) when:${Math.max(1,Number(days)||1)}d`)}&hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans`;else if(platform==="wechat")url=wechatSogouUrl(raw,days);else if(platform==="wechat-special")url=wechatSpecialUrl(raw);else if(platform==="xhs")url=`https://www.xiaohongshu.com/search_result?keyword=${q}&source=web_search_result_notes`;else if(platform==="douyin")url=`https://www.douyin.com/search/${q}?type=general`;else if(platform==="reddit")url=`https://www.reddit.com/search/?q=${q}&sort=new`;else if(platform==="x")url=`https://x.com/search?q=${q}&src=typed_query&f=live`;else url=`https://www.baidu.com/s?wd=${q}`;window.open(url,"_blank","noopener")}'''

new_function = '''function searchAfterDate(days){const d=new Date();d.setUTCDate(d.getUTCDate()-Math.max(1,Number(days)||1));return d.toISOString().slice(0,10)}
function normalizeNewsQuery(raw){
  const original=(raw||"人工智能").trim();
  if(/\\bOR\\b|[()\"]/i.test(original))return original;
  const phrases=["artificial intelligence","large language model","data center","Financial Times","Wall Street Journal","New York Times","Associated Press","AI for Science","reasoning model","multimodal model","open source","model release","model API","supply chain"];
  let work=original;const saved=[];
  phrases.forEach(phrase=>{const re=new RegExp(phrase.replace(/[.*+?^${}()|[\\]\\\\]/g,"\\\\$&"),"ig");work=work.replace(re,match=>{saved.push(`\"${match}\"`);return `__PHRASE_${saved.length-1}__`})});
  const tokens=(work.match(/site:[^\\s]+|-?[^\\s]+/g)||[]).map(token=>{const m=token.match(/^__PHRASE_(\\d+)__$/);return m?saved[Number(m[1])]:token}).filter(Boolean);
  const site=tokens.filter(token=>token.startsWith("site:"));
  const terms=[...new Set(tokens.filter(token=>!token.startsWith("site:")))];
  const body=terms.length>1?`(${terms.join(" OR ")})`:(terms[0]||"");
  return [...site,body].filter(Boolean).join(" ");
}
function openPlatformSearch(platform,query,days=1){
  const raw=(query||"人工智能").trim(),q=encodeURIComponent(raw);let url="";
  if(platform==="news"){
    const searchQuery=`${normalizeNewsQuery(raw)} after:${searchAfterDate(days)}`;
    url=`https://www.google.com/search?q=${encodeURIComponent(searchQuery)}&tbm=nws`;
  }else if(platform==="bing-news"){
    url=`https://www.bing.com/news/search?q=${encodeURIComponent(normalizeNewsQuery(raw))}`;
  }else if(platform==="wechat")url=wechatSogouUrl(raw,days);
  else if(platform==="wechat-special")url=wechatSpecialUrl(raw);
  else if(platform==="xhs")url=`https://www.xiaohongshu.com/search_result?keyword=${q}&source=web_search_result_notes`;
  else if(platform==="douyin")url=`https://www.douyin.com/search/${q}?type=general`;
  else if(platform==="reddit")url=`https://www.reddit.com/search/?q=${q}&sort=new`;
  else if(platform==="x")url=`https://x.com/search?q=${q}&src=typed_query&f=live`;
  else url=`https://www.baidu.com/s?wd=${q}`;
  window.open(url,"_blank","noopener");
}'''

if old_function in html:
    html = html.replace(old_function, new_function, 1)
elif "function normalizeNewsQuery(raw)" not in html:
    raise RuntimeError("Search function insertion point not found")

html = html.replace(
    '<option value="news">Google新闻</option>',
    '<option value="news">Google新闻（兼容搜索）</option><option value="bing-news">Bing新闻（备用）</option>',
    1,
)

html = html.replace(
    '<div class="search-note">自动聚合覆盖国际综合媒体、财经媒体、国内权威媒体、国内财经媒体、亚洲媒体及科学政策媒体；按钮用于补充实时搜索。</div>',
    '<div class="search-note">快捷按钮已改为“任一关键词匹配”，并使用兼容性更好的新闻搜索；本站聚合列表仍可直接查看，无需跳转。</div>',
    1,
)

INDEX.write_text(html, encoding="utf-8")
print("robust search links applied")
