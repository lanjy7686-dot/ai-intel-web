from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
CONFIG = ROOT / "config" / "sources.json"


def google_news_rss(query: str, language: str) -> str:
    if language == "zh":
        params = {
            "q": f"({query}) when:3d",
            "hl": "zh-CN",
            "gl": "CN",
            "ceid": "CN:zh-Hans",
        }
    else:
        params = {
            "q": f"({query}) when:3d",
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
    return "https://news.google.com/rss/search?" + urlencode(params)


INCOME_SOURCES = [
    {
        "name": "AI副业·国内机会与案例",
        "url": google_news_rss(
            'AI副业 OR AI赚钱 OR AI变现 OR AIGC副业 OR AI接单 OR AI自媒体 OR AI工具变现 OR AI创业',
            "zh",
        ),
        "source_type": "副业情报",
        "language": "zh",
        "enabled": True,
        "max_items": 60,
        "require_date": True,
        "max_age_hours": 78,
    },
    {
        "name": "AI副业·海外渠道与方法",
        "url": google_news_rss(
            '"AI side hustle" OR "make money with AI" OR "AI freelancing" OR "AI agency" OR "AI consulting" OR "AI monetization" OR "AI creator business"',
            "en",
        ),
        "source_type": "副业情报",
        "language": "en",
        "enabled": True,
        "max_items": 60,
        "require_date": True,
        "max_age_hours": 78,
    },
    {
        "name": "AI副业·风险与骗局识别",
        "url": google_news_rss(
            'AI副业 骗局 OR AI赚钱 培训 骗局 OR AI项目 诈骗 OR "AI side hustle scam" OR "make money with AI scam"',
            "zh",
        ),
        "source_type": "副业情报",
        "language": "zh",
        "enabled": True,
        "max_items": 35,
        "require_date": True,
        "max_age_hours": 168,
    },
]

cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
rss = cfg.setdefault("rss", [])
by_name = {item.get("name"): item for item in rss}
for source in INCOME_SOURCES:
    if source["name"] in by_name:
        by_name[source["name"]].update(source)
    else:
        rss.append(source)
cfg.setdefault("freshness", {})["max_output"] = max(
    1600, int(cfg.get("freshness", {}).get("max_output", 0))
)
CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

html = INDEX.read_text(encoding="utf-8")
marker = "<!-- AI_INCOME_MODULE_V1 -->"
if marker not in html:
    anchor = "<!-- ROBUST_SEARCH_LINKS_V1 -->"
    if anchor in html:
        html = html.replace(anchor, anchor + "\n" + marker, 1)
    else:
        html = html.replace("</head>", marker + "\n</head>", 1)

    html = html.replace(
        '<select id="sourceType"><option>全部来源</option>',
        '<select id="sourceType"><option>全部来源</option><option>副业情报</option>',
        1,
    )
    html = html.replace(
        '<button class="platform-tab" data-filter="llm">大模型资讯</button>',
        '<button class="platform-tab" data-filter="income">AI赚钱副业</button>\n    <button class="platform-tab" data-filter="llm">大模型资讯</button>',
        1,
    )

    quick_links = '''    <a class="search-link latest" data-group="income" href="#aiIncomeModule">AI赚钱与副业情报</a>
    <a class="search-link latest" data-group="income" data-income-quick="cases">AI副业 · 真实案例</a>
    <a class="search-link industry" data-group="income" data-income-quick="channels">AI变现 · 渠道机会</a>
    <a class="search-link fallback" data-group="income" data-income-quick="risk">AI副业 · 风险防骗</a>
'''
    html = html.replace('  <div class="search-grid">\n', '  <div class="search-grid">\n' + quick_links, 1)

    css = '''
.income-panel{padding:18px;margin:18px 0}.income-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:14px}.income-head h2{margin:0;font-size:20px}.income-badges{display:flex;gap:8px;flex-wrap:wrap}.income-badge{padding:5px 9px;border:1px solid rgba(67,209,122,.42);border-radius:999px;background:rgba(67,209,122,.08);color:#bdf4d0;font-size:12px}.income-topics{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.income-topic{border:1px solid var(--line);background:#081523;color:#c8d6e7;padding:8px 11px;border-radius:999px;font-size:12px}.income-topic.active{background:linear-gradient(135deg,var(--accent),var(--accent2));border-color:transparent;color:white}.income-custom{display:grid;grid-template-columns:1fr auto;gap:10px;margin-bottom:14px}.income-platforms{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.income-platform{display:flex;flex-direction:column;align-items:flex-start;gap:5px;padding:13px;border:1px solid var(--line);border-radius:13px;background:#091727;color:var(--text);text-align:left}.income-platform:hover{border-color:var(--accent);transform:translateY(-1px)}.income-platform strong{font-size:14px}.income-platform span{font-size:11px;color:var(--muted);font-weight:400}.income-grid{display:grid;grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr);gap:14px;margin-top:14px}.income-guide,.income-latest{border:1px solid var(--line);border-radius:14px;background:#091727;padding:14px}.income-guide h3,.income-latest h3{margin:0 0 10px;font-size:15px}.income-paths{display:grid;grid-template-columns:1fr 1fr;gap:8px}.income-path{padding:10px;border:1px solid rgba(29,54,83,.85);border-radius:10px;background:#081523}.income-path strong{font-size:13px}.income-path p{margin:5px 0 0;color:var(--muted);font-size:11px;line-height:1.55}.income-list{display:grid}.income-item{display:block;padding:10px 0;border-bottom:1px solid rgba(29,54,83,.72);text-decoration:none}.income-item:last-child{border-bottom:0}.income-item:hover .income-title{color:var(--accent)}.income-title{font-size:13px;font-weight:700;line-height:1.5}.income-meta{font-size:11px;color:var(--muted);margin-top:4px}.income-empty{padding:24px 8px;text-align:center;color:var(--muted);font-size:12px}.income-warning{margin-top:13px;padding:11px 13px;border:1px solid rgba(255,184,77,.38);border-radius:11px;background:rgba(255,184,77,.07);color:#ffdca7;font-size:12px;line-height:1.7}@media(max-width:1100px){.income-platforms{grid-template-columns:repeat(3,1fr)}}@media(max-width:860px){.income-grid{grid-template-columns:1fr}.income-platforms{grid-template-columns:repeat(2,1fr)}.income-head{display:block}.income-badges{margin-top:10px}}@media(max-width:560px){.income-platforms,.income-paths,.income-custom{grid-template-columns:1fr}}
'''
    html = html.replace("</style>", css + "</style>", 1)

    module = '''
<section class="income-panel panel" id="aiIncomeModule">
  <div class="income-head">
    <div>
      <h2>AI赚钱与副业情报</h2>
      <div class="sub">一键搜索国内外主流社交平台上的真实案例、变现渠道、实操方法、工具售卖、接单服务与风险提醒。</div>
    </div>
    <div class="income-badges"><span class="income-badge">10个平台</span><span class="income-badge">近7天聚合</span><span class="income-badge">公开搜索</span></div>
  </div>
  <div class="income-topics">
    <button class="income-topic active" data-income-topic="all">综合机会</button>
    <button class="income-topic" data-income-topic="cases">真实案例</button>
    <button class="income-topic" data-income-topic="channels">渠道与项目</button>
    <button class="income-topic" data-income-topic="content">自媒体内容</button>
    <button class="income-topic" data-income-topic="service">接单与服务</button>
    <button class="income-topic" data-income-topic="products">数字产品</button>
    <button class="income-topic" data-income-topic="risk">风险防骗</button>
  </div>
  <div class="income-custom">
    <input id="incomeKeyword" placeholder="补充关键词，如：AI老年人教程、AI绘图接单、提示词模板、智能体服务、AI带货">
    <button id="incomeSearchAll">全平台搜索</button>
  </div>
  <div class="income-platforms">
    <button class="income-platform" data-income-platform="xhs"><strong>小红书</strong><span>案例、工具、课程、带货</span></button>
    <button class="income-platform" data-income-platform="douyin"><strong>抖音</strong><span>短视频、直播、带货、教程</span></button>
    <button class="income-platform" data-income-platform="bilibili"><strong>哔哩哔哩</strong><span>长教程、实操复盘</span></button>
    <button class="income-platform" data-income-platform="zhihu"><strong>知乎</strong><span>方法讨论、经验与避坑</span></button>
    <button class="income-platform" data-income-platform="wechat-income"><strong>微信公众号</strong><span>深度文章、项目拆解</span></button>
    <button class="income-platform" data-income-platform="youtube"><strong>YouTube</strong><span>海外案例与教程</span></button>
    <button class="income-platform" data-income-platform="reddit-income"><strong>Reddit</strong><span>社区复盘与真实讨论</span></button>
    <button class="income-platform" data-income-platform="x-income"><strong>X</strong><span>最新机会与创业动态</span></button>
    <button class="income-platform" data-income-platform="tiktok"><strong>TikTok</strong><span>海外短视频与创作者变现</span></button>
    <button class="income-platform" data-income-platform="linkedin"><strong>LinkedIn</strong><span>自由职业、咨询与B2B服务</span></button>
  </div>
  <div class="income-grid">
    <section class="income-guide">
      <h3>重点变现路径</h3>
      <div class="income-paths">
        <div class="income-path"><strong>内容变现</strong><p>图文、短视频、公众号、教程、广告与带货。</p></div>
        <div class="income-path"><strong>数字产品</strong><p>提示词、模板、工作流、资料包、智能体和小工具。</p></div>
        <div class="income-path"><strong>技能接单</strong><p>文案、设计、视频、PPT、数据处理、自动化搭建。</p></div>
        <div class="income-path"><strong>企业服务</strong><p>AI培训、流程改造、知识库、客服和营销自动化。</p></div>
        <div class="income-path"><strong>课程社群</strong><p>细分人群教学、训练营、咨询和会员服务。</p></div>
        <div class="income-path"><strong>联盟与渠道</strong><p>软件推广、工具测评、渠道佣金和海外联盟营销。</p></div>
      </div>
    </section>
    <section class="income-latest">
      <h3>本站近7天副业资讯 <span class="sub" id="incomeCount">0条</span></h3>
      <div class="income-list" id="incomeLatest"><div class="income-empty">正在加载AI副业相关资讯…</div></div>
    </section>
  </div>
  <div class="income-warning"><strong>风险提示：</strong>“保收益、零门槛暴利、先交高额培训费、代投代运营、拉人头返佣”等信息需要重点核验。搜索结果仅用于发现线索，应核对原作者、发布时间、成本、收入证据和平台规则。</div>
</section>
'''

    llm_start = html.find('<section class="llm-panel panel" id="llmNewsModule">')
    stats_start = html.find('<section class="stats">', llm_start)
    if llm_start == -1 or stats_start == -1:
        raise RuntimeError("Income module insertion point not found")
    html = html[:stats_start] + module + "\n" + html[stats_start:]

    script = '''
<script>
(function(){
  const topics={
    all:{cn:"AI副业 AI赚钱 AI变现 实操 案例 渠道 方法",en:'("AI side hustle" OR "make money with AI" OR "AI monetization" OR "AI business")'},
    cases:{cn:"AI副业 真实案例 收入复盘 实操",en:'("AI side hustle" OR "AI business") (case study OR revenue OR results)'},
    channels:{cn:"AI变现 渠道 项目 机会 平台",en:'("AI monetization" OR "AI business opportunity" OR "AI agency")'},
    content:{cn:"AI自媒体 图文 短视频 公众号 带货 变现",en:'("AI content creator" OR "faceless channel" OR "AI affiliate marketing")'},
    service:{cn:"AI接单 自由职业 企业服务 自动化 咨询",en:'("AI freelancing" OR "AI consulting" OR "AI automation agency")'},
    products:{cn:"AI数字产品 提示词 模板 工作流 智能体 工具 售卖",en:'("AI digital products" OR prompts OR templates OR agents OR workflows)'},
    risk:{cn:"AI副业 骗局 诈骗 培训 避坑",en:'("AI side hustle scam" OR "make money with AI scam" OR fraud)'}
  };
  let currentTopic="all";
  function activeQuery(){
    const base=topics[currentTopic]||topics.all;
    const extra=(document.getElementById("incomeKeyword")?.value||"").trim();
    return {cn:[base.cn,extra].filter(Boolean).join(" "),en:[base.en,extra].filter(Boolean).join(" ")};
  }
  function incomeUrl(platform,query){
    const cn=encodeURIComponent(query.cn),en=encodeURIComponent(query.en);
    if(platform==="xhs")return `https://www.xiaohongshu.com/search_result?keyword=${cn}&source=web_search_result_notes`;
    if(platform==="douyin")return `https://www.douyin.com/search/${cn}?type=general`;
    if(platform==="bilibili")return `https://search.bilibili.com/all?keyword=${cn}&order=pubdate`;
    if(platform==="zhihu")return `https://www.zhihu.com/search?type=content&q=${cn}`;
    if(platform==="wechat-income")return wechatSpecialUrl(query.cn);
    if(platform==="youtube")return `https://www.youtube.com/results?search_query=${en}`;
    if(platform==="reddit-income")return `https://www.reddit.com/search/?q=${en}&sort=new&t=week`;
    if(platform==="x-income")return `https://x.com/search?q=${en}&src=typed_query&f=live`;
    if(platform==="tiktok")return `https://www.tiktok.com/search?q=${en}`;
    if(platform==="linkedin")return `https://www.linkedin.com/search/results/content/?keywords=${en}`;
    return `https://www.google.com/search?q=${encodeURIComponent(query.cn+" "+query.en)}`;
  }
  function openIncome(platform){window.open(incomeUrl(platform,activeQuery()),"_blank","noopener")}
  document.querySelectorAll(".income-topic").forEach(btn=>btn.addEventListener("click",()=>{document.querySelectorAll(".income-topic").forEach(x=>x.classList.remove("active"));btn.classList.add("active");currentTopic=btn.dataset.incomeTopic||"all"}));
  document.querySelectorAll(".income-platform").forEach(btn=>btn.addEventListener("click",()=>openIncome(btn.dataset.incomePlatform)));
  document.getElementById("incomeSearchAll")?.addEventListener("click",()=>{["xhs","douyin","bilibili","zhihu","wechat-income","youtube","reddit-income","x-income","tiktok","linkedin"].forEach((platform,i)=>setTimeout(()=>openIncome(platform),i*180))});
  document.getElementById("incomeKeyword")?.addEventListener("keydown",event=>{if(event.key==="Enter")document.getElementById("incomeSearchAll")?.click()});
  document.querySelectorAll("[data-income-quick]").forEach(link=>link.addEventListener("click",event=>{event.preventDefault();currentTopic=link.dataset.incomeQuick||"all";document.getElementById("aiIncomeModule")?.scrollIntoView({behavior:"smooth"});document.querySelectorAll(".income-topic").forEach(x=>x.classList.toggle("active",x.dataset.incomeTopic===currentTopic))}));
  function renderIncome(){
    if(typeof store==="undefined")return;
    const cutoff=Date.now()-7*86400000;
    const terms=["副业","赚钱","变现","接单","自由职业","数字产品","带货","创业","side hustle","make money","monetization","freelance","creator business","ai agency"];
    const rows=store.filter(a=>{const t=new Date(a.published_at).getTime(),text=[a.title,a.summary,a.source,(a.tags||[]).join(" ")].join(" ").toLowerCase();return !Number.isNaN(t)&&t>=cutoff&&(a.source_type==="副业情报"||terms.some(term=>text.includes(term)))}).sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
    const target=document.getElementById("incomeLatest"),count=document.getElementById("incomeCount");
    if(count)count.textContent=`${rows.length}条`;
    if(target)target.innerHTML=rows.length?rows.slice(0,10).map(a=>`<a class="income-item" href="${escapeHtml(a.url||"#")}" target="_blank" rel="noopener"><div class="income-title">${escapeHtml(a.title||"")}</div><div class="income-meta">${escapeHtml(a.source||"")} · ${escapeHtml(relativeTime(a.published_at))}</div></a>`).join(""):'<div class="income-empty">近7天暂未抓到副业相关资讯，可使用上方平台搜索。</div>';
  }
  let tries=0;const timer=setInterval(()=>{renderIncome();tries+=1;if(tries>=12)clearInterval(timer)},500);
  document.getElementById("refreshBtn")?.addEventListener("click",()=>setTimeout(renderIncome,1000));
})();
</script>
'''
    html = html.replace("</body>", script + "</body>", 1)
    INDEX.write_text(html, encoding="utf-8")

print("AI income and side-hustle module applied")
