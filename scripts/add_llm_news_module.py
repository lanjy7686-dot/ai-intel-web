from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.json"
INDEX = ROOT / "index.html"


def google_news(query: str, language: str) -> str:
    if language == "zh":
        params = {"q": f"({query}) when:1d", "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"}
    else:
        params = {"q": f"({query}) when:1d", "hl": "en-US", "gl": "US", "ceid": "US:en"}
    return "https://news.google.com/rss/search?" + urlencode(params)


LLM_SOURCES = [
    {
        "name": "国际大模型·模型发布",
        "url": google_news(
            '"large language model" OR "foundation model" OR OpenAI OR GPT OR Anthropic OR Claude OR Gemini OR Llama OR Grok OR Mistral OR Cohere OR "Amazon Nova" OR "Microsoft Phi" OR Nemotron',
            "en",
        ),
        "source_type": "大模型资讯",
        "language": "en",
        "enabled": True,
        "max_items": 70,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "国际大模型·开源评测",
        "url": google_news(
            '"open source model" OR "reasoning model" OR "multimodal model" OR "LLM benchmark" OR "model release" OR "model API"',
            "en",
        ),
        "source_type": "大模型资讯",
        "language": "en",
        "enabled": True,
        "max_items": 60,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "国内大模型·模型发布",
        "url": google_news(
            '大模型 发布 OR DeepSeek OR 通义千问 OR Qwen OR 文心一言 OR 腾讯混元 OR 豆包 OR 华为盘古 OR 智谱GLM OR Kimi OR 月之暗面 OR MiniMax OR 百川智能 OR 零一万物 OR 阶跃星辰 OR 书生浦语',
            "zh",
        ),
        "source_type": "大模型资讯",
        "language": "zh",
        "enabled": True,
        "max_items": 70,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "国内大模型·开源应用",
        "url": google_news(
            '国产大模型 OR 大模型开源 OR 大模型API OR 大模型智能体 OR 大模型价格 OR 大模型企业应用 OR 多模态大模型 OR 推理模型',
            "zh",
        ),
        "source_type": "大模型资讯",
        "language": "zh",
        "enabled": True,
        "max_items": 60,
        "require_date": True,
        "max_age_hours": 30,
    },
]


cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
rss = cfg.setdefault("rss", [])
by_name = {item.get("name"): item for item in rss}
for source in LLM_SOURCES:
    if source["name"] in by_name:
        by_name[source["name"]].update(source)
    else:
        rss.append(source)
cfg.setdefault("freshness", {})["max_output"] = max(1400, int(cfg.get("freshness", {}).get("max_output", 0)))
CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

html = INDEX.read_text(encoding="utf-8")
marker = "<!-- LLM_NEWS_MODULE_V1 -->"
if marker not in html:
    html = html.replace("<!-- SERENITY_X_WATCH_V1 -->", "<!-- SERENITY_X_WATCH_V1 -->\n" + marker, 1)

    html = html.replace(
        '<select id="sourceType"><option>全部来源</option><option>主流媒体</option>',
        '<select id="sourceType"><option>全部来源</option><option>大模型资讯</option><option>主流媒体</option>',
        1,
    )
    html = html.replace(
        '<button class="platform-tab" data-filter="media">主流媒体</button>',
        '<button class="platform-tab" data-filter="llm">大模型资讯</button>\n    <button class="platform-tab" data-filter="media">主流媒体</button>',
        1,
    )

    llm_search_links = '''    <a class="search-link latest" data-group="llm" data-platform="news" data-query="OpenAI GPT Anthropic Claude Gemini Llama Grok Mistral large language model" data-days="1">国外大模型 · 最新发布</a>
    <a class="search-link latest" data-group="llm" data-platform="news" data-query="DeepSeek 通义千问 Qwen 文心一言 腾讯混元 豆包 华为盘古 智谱GLM Kimi MiniMax" data-days="1">国内大模型 · 最新发布</a>
    <a class="search-link industry" data-group="llm" data-platform="news" data-query="reasoning model multimodal model open source LLM benchmark model API" data-days="1">大模型 · 开源评测</a>
    <a class="search-link industry" data-group="llm" data-platform="news" data-query="大模型 智能体 API 企业应用 多模态 推理模型" data-days="1">大模型 · 应用落地</a>
'''
    html = html.replace('  <div class="search-grid">\n', '  <div class="search-grid">\n' + llm_search_links, 1)

    css = '''
.llm-panel{padding:18px;margin:18px 0}.llm-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:14px}.llm-head h2{margin:0;font-size:20px}.llm-summary{display:flex;gap:8px;flex-wrap:wrap}.llm-pill{padding:5px 9px;border:1px solid var(--line);border-radius:999px;background:#0a1728;color:#cfe9ff;font-size:12px}.llm-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.llm-column{border:1px solid var(--line);border-radius:14px;background:#091727;overflow:hidden}.llm-column-head{display:flex;justify-content:space-between;align-items:center;padding:13px 14px;border-bottom:1px solid var(--line)}.llm-column-head h3{margin:0;font-size:15px}.llm-list{display:grid}.llm-item{display:block;padding:12px 14px;border-bottom:1px solid rgba(29,54,83,.72);text-decoration:none}.llm-item:last-child{border-bottom:0}.llm-item:hover{background:#0c1d31}.llm-title{font-size:14px;font-weight:700;line-height:1.5}.llm-meta{font-size:11px;color:var(--muted);margin-top:5px}.llm-empty{padding:28px 14px;text-align:center;color:var(--muted);font-size:13px}.llm-models{display:flex;gap:7px;flex-wrap:wrap;margin-top:13px}.llm-model{padding:5px 8px;border:1px solid var(--line);border-radius:999px;background:#081523;color:#bdd2ea;font-size:11px}@media(max-width:860px){.llm-grid{grid-template-columns:1fr}.llm-head{display:block}.llm-summary{margin-top:10px}}
'''
    html = html.replace("</style>", css + "</style>", 1)

    module = '''
<section class="llm-panel panel" id="llmNewsModule">
  <div class="llm-head">
    <div>
      <h2>国内外大模型资讯</h2>
      <div class="sub">聚合模型发布、开源、评测、API、智能体、多模态与产业应用，按真实发布时间排序。</div>
    </div>
    <div class="llm-summary">
      <span class="llm-pill">国外 <strong id="llmGlobalCount">0</strong></span>
      <span class="llm-pill">国内 <strong id="llmDomesticCount">0</strong></span>
      <span class="llm-pill">近24小时</span>
    </div>
  </div>
  <div class="llm-grid">
    <section class="llm-column">
      <div class="llm-column-head"><h3>国外大模型</h3><span class="sub">GPT · Claude · Gemini · Llama · Grok</span></div>
      <div class="llm-list" id="llmGlobalList"><div class="llm-empty">正在加载国外大模型资讯…</div></div>
    </section>
    <section class="llm-column">
      <div class="llm-column-head"><h3>国内大模型</h3><span class="sub">DeepSeek · Qwen · Kimi · GLM · 豆包</span></div>
      <div class="llm-list" id="llmDomesticList"><div class="llm-empty">正在加载国内大模型资讯…</div></div>
    </section>
  </div>
  <div class="llm-models">
    <span class="llm-model">OpenAI / GPT</span><span class="llm-model">Anthropic / Claude</span><span class="llm-model">Google / Gemini</span><span class="llm-model">Meta / Llama</span><span class="llm-model">xAI / Grok</span><span class="llm-model">Mistral</span><span class="llm-model">DeepSeek</span><span class="llm-model">通义千问 / Qwen</span><span class="llm-model">文心</span><span class="llm-model">腾讯混元</span><span class="llm-model">豆包</span><span class="llm-model">华为盘古</span><span class="llm-model">智谱GLM</span><span class="llm-model">Kimi</span><span class="llm-model">MiniMax</span>
  </div>
</section>
'''
    latest_end = "</main>\n\n<section class=\"stats\">"
    if latest_end not in html:
        raise RuntimeError("Latest-news insertion point not found")
    html = html.replace(latest_end, "</main>\n" + module + "\n<section class=\"stats\">", 1)

    script = '''
<script>
(function(){
  const domesticTerms=["deepseek","通义","qwen","文心","混元","豆包","盘古","智谱","glm","kimi","月之暗面","minimax","百川","零一万物","阶跃星辰","书生浦语","国产大模型"];
  const globalTerms=["openai","gpt","anthropic","claude","gemini","deepmind","llama","meta ai","grok","xai","mistral","cohere","amazon nova","microsoft phi","nemotron"];
  function region(article){const text=[article.source,article.title,article.summary,(article.tags||[]).join(" ")].join(" ").toLowerCase();if(String(article.source||"").startsWith("国内大模型")||domesticTerms.some(x=>text.includes(x)))return"domestic";if(String(article.source||"").startsWith("国际大模型")||globalTerms.some(x=>text.includes(x)))return"global";return article.language==="zh"?"domestic":"global"}
  function itemHtml(a){return `<a class="llm-item" href="${escapeHtml(a.url||"#")}" target="_blank" rel="noopener"><div class="llm-title">${escapeHtml(a.title||"")}</div><div class="llm-meta">${escapeHtml(a.source||"")} · ${escapeHtml(relativeTime(a.published_at))}</div></a>`}
  function renderLLMNews(){
    if(typeof store==="undefined")return;
    const cutoff=Date.now()-24*60*60*1000;
    const terms=[...domesticTerms,...globalTerms,"large language model","foundation model","reasoning model","multimodal model","大模型"];
    const rows=store.filter(a=>{const t=new Date(a.published_at).getTime(),text=[a.title,a.summary,a.source,(a.tags||[]).join(" ")].join(" ").toLowerCase();return !Number.isNaN(t)&&t>=cutoff&&(a.source_type==="大模型资讯"||terms.some(x=>text.includes(x)))}).sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
    const domestic=rows.filter(a=>region(a)==="domestic"),global=rows.filter(a=>region(a)==="global");
    const domesticList=document.getElementById("llmDomesticList"),globalList=document.getElementById("llmGlobalList");
    if(domesticList)domesticList.innerHTML=domestic.length?domestic.slice(0,8).map(itemHtml).join(""):'<div class="llm-empty">近24小时暂无国内大模型资讯</div>';
    if(globalList)globalList.innerHTML=global.length?global.slice(0,8).map(itemHtml).join(""):'<div class="llm-empty">近24小时暂无国外大模型资讯</div>';
    const dc=document.getElementById("llmDomesticCount"),gc=document.getElementById("llmGlobalCount");if(dc)dc.textContent=domestic.length;if(gc)gc.textContent=global.length;
  }
  let tries=0;const timer=setInterval(()=>{renderLLMNews();tries+=1;if(tries>=12)clearInterval(timer)},500);
  document.getElementById("refreshBtn")?.addEventListener("click",()=>setTimeout(renderLLMNews,1000));
})();
</script>
'''
    html = html.replace("</body>", script + "</body>", 1)
    INDEX.write_text(html, encoding="utf-8")

print("domestic and global LLM news module applied")
