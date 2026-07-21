from __future__ import annotations

import concurrent.futures as cf
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/sources.json"
OUTPUT = ROOT / "data/articles.json"
UA = "AI-Intel-Web/2.0 (free public information dashboard)"

CATEGORY_KEYWORDS = {
    "投资商业": [
        "funding", "raised", "valuation", "invest", "investment", "venture capital",
        "ipo", "acquisition", "merger", "revenue", "earnings", "stock", "shares",
        "融资", "估值", "投资", "并购", "收购", "上市", "财报", "营收", "利润", "股价", "商业化", "资本",
    ],
    "技术研究": [
        "model", "benchmark", "paper", "research", "dataset", "training", "inference",
        "architecture", "open source", "github", "api", "agent", "multimodal", "reasoning",
        "robotics", "chip", "gpu", "论文", "模型", "基准", "数据集", "训练", "推理",
        "架构", "开源", "智能体", "多模态", "机器人", "芯片", "算法", "大模型",
    ],
    "产品应用": [
        "launch", "release", "product", "feature", "assistant", "copilot", "app", "tool",
        "platform", "enterprise", "发布", "上线", "产品", "功能", "助手", "工具", "平台", "应用", "落地",
    ],
    "政策治理": [
        "regulation", "policy", "law", "act", "safety", "governance", "copyright",
        "privacy", "antitrust", "监管", "政策", "法律", "法案", "安全", "治理", "版权", "隐私", "反垄断", "合规", "标准",
    ],
    "产业动态": [
        "partnership", "partner", "industry", "market", "company", "hiring", "layoff",
        "data center", "cloud", "合作", "产业", "市场", "公司", "招聘", "裁员", "数据中心", "云计算", "供应链", "生态",
    ],
}
CORE_TERMS = [
    "artificial intelligence", "generative ai", "genai", "large language model", "llm",
    "machine learning", "deep learning", "openai", "anthropic", "deepseek", "gemini",
    "claude", "nvidia", "人工智能", "生成式ai", "大模型", "机器学习", "深度学习", "智能体", "aigc",
]


def clean(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_dt(value):
    try:
        parsed = dateparser.parse(str(value))
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def canonical_url(url):
    try:
        parts = urlsplit(url.strip())
        tracking = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "spm", "ref", "source", "from", "share",
        }
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in tracking]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))
    except Exception:
        return url


def load_previous_payload():
    try:
        return json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    except Exception:
        return {}


def classify(article):
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('content', '')}".lower()
    scores = {}
    tags = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            if keyword.lower() in text:
                count += 1
                if len(tags) < 10:
                    tags.append(keyword)
        scores[category] = count

    article["category"] = max(scores, key=scores.get) if max(scores.values(), default=0) > 0 else "产业动态"
    core_hits = sum(1 for term in CORE_TERMS if term in text)
    age_hours = max(0, (datetime.now(timezone.utc) - parse_dt(article.get("published_at"))).total_seconds() / 3600)
    freshness = max(0, 25 - int(age_hours / 4))
    article["relevance_score"] = min(100, 20 + min(30, core_hits * 6) + min(25, sum(scores.values()) * 3) + freshness)
    article["tags"] = list(dict.fromkeys(tags))
    article["summary"] = clean(article.get("summary") or article.get("content") or article.get("title"))[:300]
    article.pop("content", None)
    return article


def rss_collect(cfg):
    articles = []
    for source in cfg.get("rss", []):
        if not source.get("enabled", True):
            continue
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:50]:
            title = clean(entry.get("title"))
            url = entry.get("link", "")
            if not title or not url:
                continue
            content = clean(entry.get("summary") or entry.get("description") or "")
            if entry.get("content"):
                content = clean(" ".join(item.get("value", "") for item in entry.get("content", [])))
            articles.append({
                "title": title,
                "url": url,
                "source": source.get("name", "RSS"),
                "source_type": source.get("source_type", "RSS"),
                "published_at": parse_dt(entry.get("published") or entry.get("updated")).isoformat(),
                "content": content,
            })
    return articles


def gdelt_collect(cfg):
    source = cfg.get("gdelt", {})
    if not source.get("enabled", False):
        return []
    response = requests.get(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={
            "query": source["query"], "mode": "ArtList", "format": "json",
            "maxrecords": source.get("max_items", 40), "sort": "HybridRel", "timespan": source.get("timespan", "3d"),
        },
        headers={"User-Agent": UA}, timeout=35,
    )
    response.raise_for_status()
    return [{
        "title": clean(item.get("title")), "url": item.get("url", ""),
        "source": item.get("domain", "GDELT"), "source_type": "全球新闻",
        "published_at": parse_dt(item.get("seendate")).isoformat(), "content": "",
    } for item in response.json().get("articles", []) if item.get("title") and item.get("url")]


def arxiv_collect(cfg):
    source = cfg.get("arxiv", {})
    if not source.get("enabled", True):
        return []
    url = "https://export.arxiv.org/api/query?" + urlencode({
        "search_query": source["query"], "start": 0, "max_results": source.get("max_items", 40),
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    feed = feedparser.parse(url)
    return [{
        "title": clean(entry.get("title")), "url": entry.get("link", ""),
        "source": "arXiv", "source_type": "论文",
        "published_at": parse_dt(entry.get("published")).isoformat(), "content": clean(entry.get("summary")),
    } for entry in feed.entries if entry.get("title") and entry.get("link")]


def hackernews_collect(cfg):
    source = cfg.get("hackernews", {})
    if not source.get("enabled", True):
        return []
    story_ids = requests.get("https://hacker-news.firebaseio.com/v0/newstories.json", timeout=25).json()[:source.get("scan_items", 200)]
    keywords = [item.lower() for item in source.get("keywords", [])]

    def fetch_item(item_id):
        try:
            return requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=12).json() or {}
        except Exception:
            return {}

    articles = []
    with cf.ThreadPoolExecutor(max_workers=12) as executor:
        for item in executor.map(fetch_item, story_ids):
            title = item.get("title", "")
            if not title or not any(keyword in f"{title} {item.get('text', '')}".lower() for keyword in keywords):
                continue
            articles.append({
                "title": title,
                "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
                "source": "Hacker News", "source_type": "技术社区",
                "published_at": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc).isoformat(),
                "content": clean(item.get("text", "")),
            })
    return articles[:source.get("max_items", 40)]


def wechat_collect(cfg):
    path = ROOT / cfg.get("wechat_urls_file", "config/wechat_urls.txt")
    if not path.exists():
        return []
    articles = []
    urls = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    for url in urls:
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 Chrome/124 Safari/537.36"}, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            meta = soup.select_one("meta[property='og:title']")
            title = (meta.get("content") if meta else "") or clean(soup.select_one("#activity-name").get_text(" ", strip=True) if soup.select_one("#activity-name") else "")
            author = clean(soup.select_one("#js_name").get_text(" ", strip=True) if soup.select_one("#js_name") else "")
            body = clean(soup.select_one("#js_content").get_text(" ", strip=True) if soup.select_one("#js_content") else "")
            if title:
                articles.append({
                    "title": title, "url": url, "source": author or "微信公众号",
                    "source_type": "微信公众号", "published_at": datetime.now(timezone.utc).isoformat(), "content": body,
                })
        except Exception:
            continue
    return articles


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    previous = load_previous_payload()
    collectors = [
        ("RSS", rss_collect),
        ("arXiv", arxiv_collect),
        ("Hacker News", hackernews_collect),
        ("微信", wechat_collect),
    ]
    if cfg.get("gdelt", {}).get("enabled", False):
        collectors.append(("GDELT", gdelt_collect))

    all_articles = []
    errors = []
    source_status = {
        "X": {
            "enabled": False,
            "state": "free_search_only",
            "count": 0,
            "message": "完全免费模式：不调用X API，网页提供一键X实时搜索。",
        }
    }

    with cf.ThreadPoolExecutor(max_workers=5) as executor:
        jobs = {executor.submit(function, cfg): name for name, function in collectors}
        for future, name in jobs.items():
            try:
                items = future.result()
                all_articles.extend(items)
                source_status[name] = {"state": "fetched", "count": len(items)}
            except Exception as exc:
                errors.append(f"{name}: {exc}")
                source_status[name] = {"state": "error", "count": 0, "message": str(exc)}

    seen = set()
    output_articles = []
    for article in all_articles:
        key = hashlib.sha256((re.sub(r"\W+", "", article.get("title", "").lower()) + "|" + canonical_url(article.get("url", ""))).encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        output_articles.append(classify(article))

    output_articles.sort(key=lambda item: (item.get("relevance_score", 0), parse_dt(item.get("published_at"))), reverse=True)
    payload = {
        "mode": "free",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(output_articles),
        "errors": errors,
        "source_status": source_status,
        "articles": output_articles[:500],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mode": "free", "count": len(output_articles), "errors": errors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
