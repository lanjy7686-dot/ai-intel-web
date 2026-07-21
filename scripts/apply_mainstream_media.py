from pathlib import Path
import json
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.json"
INDEX = ROOT / "index.html"
FETCH = ROOT / "scripts" / "fetch_news.py"


def gnews(query: str, language: str = "zh") -> str:
    if language == "en":
        params = {"q": f"({query}) when:1d", "hl": "en-US", "gl": "US", "ceid": "US:en"}
    else:
        params = {"q": f"({query}) when:1d", "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"}
    return "https://news.google.com/rss/search?" + urlencode(params)


MEDIA_SOURCES = [
    {
        "name": "主流媒体·国际综合",
        "url": gnews('(\"artificial intelligence\" OR \"generative AI\" OR OpenAI OR Anthropic OR DeepSeek OR NVIDIA) (Reuters OR \"Associated Press\" OR BBC OR Bloomberg OR CNBC OR \"Financial Times\" OR \"Wall Street Journal\" OR \"New York Times\" OR Guardian)', "en"),
        "source_type": "主流媒体",
        "language": "en",
        "enabled": True,
        "max_items": 45,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "主流媒体·国际财经",
        "url": gnews('(AI OR \"artificial intelligence\" OR semiconductor OR \"data center\" OR robotics) (Reuters OR Bloomberg OR CNBC OR \"Financial Times\" OR \"Wall Street Journal\" OR Nikkei)', "en"),
        "source_type": "主流媒体",
        "language": "en",
        "enabled": True,
        "max_items": 45,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "主流媒体·国内权威",
        "url": gnews('(人工智能 OR 大模型 OR AIGC OR DeepSeek OR AI芯片 OR 具身智能) (新华社 OR 人民日报 OR 央视新闻 OR 中国新闻网 OR 经济日报 OR 科技日报)'),
        "source_type": "主流媒体",
        "language": "zh",
        "enabled": True,
        "max_items": 45,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "主流媒体·国内财经",
        "url": gnews('(人工智能 OR 大模型 OR AI芯片 OR 算力 OR 机器人 OR 融资) (财联社 OR 第一财经 OR 证券时报 OR 上海证券报 OR 中国证券报 OR 经济观察报)'),
        "source_type": "主流媒体",
        "language": "zh",
        "enabled": True,
        "max_items": 45,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "主流媒体·亚洲科技财经",
        "url": gnews('(\"artificial intelligence\" OR \"AI chip\" OR robotics OR \"data center\") (\"Nikkei Asia\" OR \"South China Morning Post\" OR \"The Straits Times\" OR \"Korea Times\")', "en"),
        "source_type": "主流媒体",
        "language": "en",
        "enabled": True,
        "max_items": 35,
        "require_date": True,
        "max_age_hours": 30,
    },
    {
        "name": "主流媒体·科学与政策",
        "url": gnews('(\"artificial intelligence\" OR \"AI safety\" OR \"AI regulation\" OR \"AI research\") (Nature OR Science OR \"IEEE Spectrum\" OR \"MIT Technology Review\")', "en"),
        "source_type": "主流媒体",
        "language": "en",
        "enabled": True,
        "max_items": 35,
        "require_date": True,
        "max_age_hours": 30,
    },
]

cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
rss = cfg.setdefault("rss", [])
by_name = {item.get("name"): item for item in rss}
for item in MEDIA_SOURCES:
    if item["name"] in by_name:
        by_name[item["name"]].update(item)
    else:
        rss.append(item)
cfg.setdefault("freshness", {})["max_output"] = 800
CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

# Google News RSS条目通常包含原始媒体名称，优先显示原媒体而不是聚合专题名。
fetch_text = FETCH.read_text(encoding="utf-8")
fetch_marker = "# MAINSTREAM_PUBLISHER_V1"
if fetch_marker not in fetch_text:
    fetch_text = fetch_text.replace("# FRESHNESS_PATCH_V2", "# FRESHNESS_PATCH_V2\n" + fetch_marker, 1)
    old = 'articles.append({"title": title, "url": url, "source": source.get("name", "RSS"), "source_type": source.get("source_type", "RSS"),'
    new = 'entry_source = entry.get("source") or {}\n            publisher = clean(entry_source.get("title", "")) if isinstance(entry_source, dict) else ""\n            articles.append({"title": title, "url": url, "source": publisher or source.get("name", "RSS"), "source_type": source.get("source_type", "RSS"),'
    if old not in fetch_text:
        raise RuntimeError("RSS publisher insertion point not found")
    fetch_text = fetch_text.replace(old, new, 1)
    FETCH.write_text(fetch_text, encoding="utf-8")

html = INDEX.read_text(encoding="utf-8")
marker = "<!-- MAINSTREAM_MEDIA_V1 -->"
if marker not in html:
    html = html.replace("<!-- FRESHNESS_UI_V2 -->", "<!-- FRESHNESS_UI_V2 -->\n" + marker, 1)
    html = html.replace("巨头企业 · 产业链 · 新技术 · 投资 · 论文 · 国内外社区", "主流媒体 · 巨头企业 · 产业链 · 新技术 · 投资 · 论文")
    html = html.replace(".stats{display:grid;grid-template-columns:repeat(5,1fr)", ".stats{display:grid;grid-template-columns:repeat(6,1fr)")
    html = html.replace(".source-frontier{color:#64e8d8}", ".source-frontier{color:#64e8d8}.source-mainstream{color:#ff9eaa}")
    html = html.replace('<select id="sourceType"><option>全部来源</option>', '<select id="sourceType"><option>全部来源</option><option>主流媒体</option>')
    html = html.replace('<button class="platform-tab" data-filter="industry">产业专题</button>', '<button class="platform-tab" data-filter="media">主流媒体</button>\n    <button class="platform-tab" data-filter="industry">产业专题</button>')
    media_links = '''    <a class="search-link industry" data-group="media" data-platform="news" data-query="artificial intelligence Reuters Associated Press BBC Bloomberg CNBC Financial Times Wall Street Journal New York Times Guardian" data-days="1">国际主流媒体 · AI</a>
    <a class="search-link industry" data-group="media" data-platform="news" data-query="AI semiconductor data center robotics Reuters Bloomberg CNBC Financial Times Nikkei" data-days="1">国际财经媒体 · AI产业</a>
    <a class="search-link industry" data-group="media" data-platform="news" data-query="人工智能 大模型 DeepSeek AI芯片 具身智能 新华社 人民日报 央视新闻 中国新闻网 经济日报 科技日报" data-days="1">国内权威媒体 · AI</a>
    <a class="search-link industry" data-group="media" data-platform="news" data-query="人工智能 大模型 AI芯片 算力 机器人 融资 财联社 第一财经 证券时报 上海证券报 中国证券报" data-days="1">国内财经媒体 · AI</a>
'''
    html = html.replace('  <div class="search-grid">\n', '  <div class="search-grid">\n' + media_links, 1)
    html = html.replace('<div class="stat panel"><div class="label">当前结果</div><div class="value" id="sTotal">0</div></div>', '<div class="stat panel"><div class="label">当前结果</div><div class="value" id="sTotal">0</div></div>\n  <div class="stat panel"><div class="label">主流媒体</div><div class="value" id="sMedia">0</div></div>')
    html = html.replace('if(type==="新技术")return"source-frontier";return""', 'if(type==="新技术")return"source-frontier";if(type==="主流媒体")return"source-mainstream";return""')
    html = html.replace('el("sGiants").textContent=countType("巨头企业");', 'el("sMedia").textContent=countType("主流媒体");el("sGiants").textContent=countType("巨头企业");')
    html = html.replace('["巨头企业","产业链","新技术"].includes(selected)', '["主流媒体","巨头企业","产业链","新技术"].includes(selected)')
    html = html.replace('最新专题搜索</h2><div class="sub">专题搜索默认限定近24小时；切换时间后会自动加入时间条件。</div>', '最新专题搜索</h2><div class="sub">新增国内外主流媒体频道；所有专题默认限定近24小时。</div>')
    html = html.replace('自动来源包括官方博客、新闻RSS、论文与公开社区', '自动来源包括主流媒体、官方博客、新闻RSS、论文与公开社区')
    INDEX.write_text(html, encoding="utf-8")

print("mainstream media sources and UI applied")
