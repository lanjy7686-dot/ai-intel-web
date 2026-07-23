from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

html = INDEX.read_text(encoding="utf-8")

old_links = '''    <a class="search-link latest" data-group="income" href="#aiIncomeModule">AI赚钱与副业情报</a>
    <a class="search-link latest" data-group="income" data-income-quick="cases">AI副业 · 真实案例</a>
    <a class="search-link industry" data-group="income" data-income-quick="channels">AI变现 · 渠道机会</a>
    <a class="search-link fallback" data-group="income" data-income-quick="risk">AI副业 · 风险防骗</a>
'''
new_links = '''    <a class="search-link latest" data-group="income" data-platform="xhs" data-query="AI副业 AI赚钱 AI变现 真实案例">小红书 · AI副业案例</a>
    <a class="search-link latest" data-group="income" data-platform="douyin" data-query="AI副业 赚钱 变现 实操">抖音 · AI赚钱实操</a>
    <a class="search-link industry" data-group="income" data-platform="reddit" data-query="AI side hustle make money with AI monetization">Reddit · 海外副业讨论</a>
    <a class="search-link fallback" data-group="income" data-platform="news" data-query="AI副业 骗局 诈骗 培训 避坑">AI副业 · 风险防骗</a>
'''
html = html.replace(old_links, new_links)
html = html.replace('<button id="incomeSearchAll">全平台搜索</button>', '<button id="incomeSearchAll">跨平台搜索</button>')

old_listener = '''  document.getElementById("incomeSearchAll")?.addEventListener("click",()=>{["xhs","douyin","bilibili","zhihu","wechat-income","youtube","reddit-income","x-income","tiktok","linkedin"].forEach((platform,i)=>setTimeout(()=>openIncome(platform),i*180))});'''
new_listener = '''  document.getElementById("incomeSearchAll")?.addEventListener("click",()=>{
    const query=activeQuery();
    const sites='(site:xiaohongshu.com OR site:douyin.com OR site:bilibili.com OR site:zhihu.com OR site:mp.weixin.qq.com OR site:youtube.com OR site:reddit.com OR site:x.com OR site:tiktok.com OR site:linkedin.com)';
    window.open(`https://www.google.com/search?q=${encodeURIComponent(query.cn+" "+query.en+" "+sites)}`,"_blank","noopener");
  });'''
html = html.replace(old_listener, new_listener)

old_quick_handler = '''  document.querySelectorAll("[data-income-quick]").forEach(link=>link.addEventListener("click",event=>{event.preventDefault();currentTopic=link.dataset.incomeQuick||"all";document.getElementById("aiIncomeModule")?.scrollIntoView({behavior:"smooth"});document.querySelectorAll(".income-topic").forEach(x=>x.classList.toggle("active",x.dataset.incomeTopic===currentTopic))}));
'''
html = html.replace(old_quick_handler, "")

INDEX.write_text(html, encoding="utf-8")
print("AI income module compatibility fixes applied")
