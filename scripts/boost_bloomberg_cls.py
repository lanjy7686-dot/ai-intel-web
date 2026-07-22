from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.json"
FETCH = ROOT / "scripts" / "fetch_news.py"
INDEX = ROOT / "index.html"


def gnews(query: str, language: str) -> str:
    if language == "en":
        params = {"q": f"({query}) when:1d", "hl": "en-US", "gl": "US", "ceid": "US:en"}
    else:
        params = {"q": f"({query}) when:1d", "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"}
    return "https://news.google.com/rss/search?" + urlencode(params)


PRIORITY_SOURCES = [
    {
        "name": "彭博社·AI巨头与模型",
        "url": gnews('site:bloomberg.com ("artificial intelligence" OR OpenAI OR Anthropic OR DeepSeek OR Gemini OR Claude OR xAI)', "en"),
        "source_type": "主流媒体",
        "language": "en",
        "enabled": True,
        "max_items": 80,
        "require_date": True,
        "max_age_hours": 30,
        "priority": 18,
    },
    {
        "name": "彭博社·芯片算力与数据中心",
        "url": gnews('site:bloomberg.com (NVIDIA OR AMD OR TSMC OR ASML OR HBM OR semiconductor OR "AI chip" OR "data center")', "en"),
        "source_type": "主流媒体",
        "language": "en",
        "enabled": True,
        "max_items": 80,
        "require_date": True,
        "max_age_hours": 30,
        "priority": 18,
    },
    {
        "name": "彭博社·AI资本市场",
        "url": gnews('site:bloomberg.com (AI funding OR AI investment OR valuation OR earnings OR IPO OR acquisition)', "en"),
        "source_type": "主流媒体",
        "language": "en",
        "enabled": True,
        "max_items": 80,
        "require_date": True,
        "max_age_hours": 30,
        "priority": 18,
    },
    {
        "name": "财联社·AI产业快讯",
        "url": gnews('site:cls.cn (人工智能 OR 大模型 OR DeepSeek OR 智能体 OR 具身智能 OR 人形机器人)', "zh"),
        "source_type": "主流媒体",
        "language": "zh",
        "enabled": True,
        "max_items": 80,
        "require_date": True,
        "max_age_hours": 30,
        "priority": 18,
    },
    {
        "name": "财联社·芯片算力产业链",
        "url": gnews('site:cls.cn (AI芯片 OR 算力 OR 英伟达 OR 华为昇腾 OR 寒武纪 OR 光模块 OR CPO OR 液冷 OR 数据中心)', "zh"),
        "source_type": "主流媒体",
        "language": "zh",
        "enabled": True,
        "max_items": 80,
        "require_date": True,
        "max_age_hours": 30,
        "priority": 18,
    },
    {
        "name": "财联社·AI资本市场",
        "url": gnews('site:cls.cn (人工智能 融资 OR AI投资 OR 大模型 估值 OR AI概念股 OR 并购 OR IPO OR 财报)', "zh"),
        "source_type": "主流媒体",
        "language": "zh",
        "enabled": True,
        "max_items": 80,
        "require_date": True,
        "max_age_hours": 30,
        "priority": 18,
    },
]


cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
rss = cfg.setdefault("rss", [])
by_name = {item.get("name"): item for item in rss}
for item in PRIORITY_SOURCES:
    if item["name"] in by_name:
        by_name[item["name"]].update(item)
    else:
        rss.append(item)
cfg.setdefault("freshness", {})["max_output"] = max(1200, int(cfg.get("freshness", {}).get("max_output", 800)))
CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

fetch_text = FETCH.read_text(encoding="utf-8")
marker = "# PRIORITY_MEDIA_SCORING_V1"
if marker not in fetch_text:
    fetch_text = fetch_text.replace("# FRESHNESS_PATCH_V2", "# FRESHNESS_PATCH_V2\n" + marker, 1)
    fetch_text = fetch_text.replace(
        'engagement = min(15, int(article.get("engagement", 0) or 0) // 20)\n    article["relevance_score"] = min(100, 20 + min(30, core_hits * 6) + min(25, sum(scores.values()) * 3) + freshness + engagement)',
        'engagement = min(15, int(article.get("engagement", 0) or 0) // 20)\n    source_bonus = min(15, max(0, int(article.get("source_priority", 0) or 0)))\n    article["relevance_score"] = min(100, 20 + min(30, core_hits * 6) + min(25, sum(scores.values()) * 3) + freshness + engagement + source_bonus)',
        1,
    )
    fetch_text = fetch_text.replace(
        '"date_verified": True,\n            })',
        '"date_verified": True,\n                "source_priority": int(source.get("priority", 0) or 0),\n            })',
        1,
    )
    fetch_text = fetch_text.replace(
        'source_status["来源统计"] = source_counts',
        'source_status["来源统计"] = source_counts\n    source_status["重点媒体"] = {\n        "彭博社": sum(1 for item in output if "彭博" in str(item.get("source", "")) or "Bloomberg" in str(item.get("source", ""))),\n        "财联社": sum(1 for item in output if "财联社" in str(item.get("source", "")) or "cls.cn" in str(item.get("url", ""))),\n    }',
        1,
    )
    FETCH.write_text(fetch_text, encoding="utf-8")

html = INDEX.read_text(encoding="utf-8")
html_marker = "<!-- BLOOMBERG_CLS_FOCUS_V1 -->"
if html_marker not in html:
    html = html.replace("<!-- MAINSTREAM_MEDIA_V1 -->", "<!-- MAINSTREAM_MEDIA_V1 -->\n" + html_marker, 1)
    links = '''    <a class="search-link media" data-group="media" data-platform="news" data-query="site:bloomberg.com artificial intelligence OpenAI NVIDIA data center funding" data-days="1">彭博社 · AI最新</a>
    <a class="search-link media" data-group="media" data-platform="news" data-query="site:cls.cn 人工智能 大模型 AI芯片 算力 机器人 融资" data-days="1">财联社 · AI最新</a>
'''
    html = html.replace('  <div class="search-grid">\n', '  <div class="search-grid">\n' + links, 1)
    html = html.replace(
        "主流媒体 · 巨头企业 · 产业链 · 新技术 · 投资 · 论文",
        "彭博社 · 财联社 · 主流媒体 · 巨头企业 · 产业链 · 新技术",
        1,
    )
    html = html.replace(
        "新增“主流媒体”频道；默认只看近24小时",
        "彭博社、财联社已设为重点媒体并提高抓取上限；默认只看近24小时",
        1,
    )
    INDEX.write_text(html, encoding="utf-8")

print("Bloomberg and CLS priority sources applied")
