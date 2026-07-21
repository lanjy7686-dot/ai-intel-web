from __future__ import annotations

import concurrent.futures as cf
import hashlib
import html
import json
import re
import time
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
UA = "AI-Intel-Radar/1.4 (free public-feed dashboard; contact via GitHub repository)"

CATEGORY_KEYWORDS = {
    "投资商业": ["funding", "raised", "valuation", "invest", "investment", "venture capital", "ipo", "acquisition", "merger", "revenue", "earnings", "stock", "shares", "融资", "估值", "投资", "并购", "收购", "上市", "财报", "营收", "利润", "股价", "商业化", "资本", "创业", "募资"],
    "技术研究": ["model", "benchmark", "paper", "research", "dataset", "training", "inference", "architecture", "open source", "github", "api", "agent", "multimodal", "reasoning", "robotics", "chip", "gpu", "论文", "模型", "基准", "数据集", "训练", "推理", "架构", "开源", "智能体", "多模态", "机器人", "芯片", "算法", "大模型", "算力"],
    "产品应用": ["launch", "release", "product", "feature", "assistant", "copilot", "app", "tool", "platform", "enterprise", "发布", "上线", "产品", "功能", "助手", "工具", "平台", "应用", "落地", "教程", "测评"],
    "政策治理": ["regulation", "policy", "law", "act", "safety", "governance", "copyright", "privacy", "antitrust", "监管", "政策", "法律", "法案", "安全", "治理", "版权", "隐私", "反垄断", "合规", "标准"],
    "产业动态": ["partnership", "partner", "industry", "market", "company", "hiring", "layoff", "data center", "cloud", "合作", "产业", "市场", "公司", "招聘", "裁员", "数据中心", "云计算", "供应链", "生态"],
}
CORE_TERMS = ["artificial intelligence", "generative ai", "genai", "large language model", "llm", "machine learning", "deep learning", "openai", "anthropic", "deepseek", "gemini", "claude", "nvidia", "人工智能", "生成式ai", "大模型", "机器学习", "深度学习", "智能体", "aigc", "ai工具", "ai应用"]


def clean(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def dt(value):
    try:
        parsed = dateparser.parse(str(value))
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def canonical(url):
    try:
        parts = urlsplit(url.strip())
        bad = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "spm", "ref", "source", "from", "share"}
        query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key.lower() not in bad]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))
    except Exception:
        return url


def classify(article):
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('content', '')}".lower()
    scores, tags = {}, []
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
    age_hours = max(0, (datetime.now(timezone.utc) - dt(article.get("published_at"))).total_seconds() / 3600)
    freshness = max(0, 25 - int(age_hours / 4))
    engagement = min(15, int(article.get("engagement", 0) or 0) // 20)
    domestic_bonus = 5 if article.get("source_type") in {"国内资讯", "微信公众号", "小红书", "抖音"} else 0
    article["relevance_score"] = min(100, 20 + min(30, core_hits * 6) + min(25, sum(scores.values()) * 3) + freshness + engagement + domestic_bonus)
    article["tags"] = list(dict.fromkeys(tags))
    article["summary"] = clean(article.get("summary") or article.get("content") or article.get("title"))[:320]
    article.pop("content", None)
    return article


def request_feed(url, *, user_agent=UA, timeout=30):
    response = requests.get(
        url,
        headers={"User-Agent": user_agent, "Accept": "application/atom+xml,application/rss+xml,application/xml,text/xml,*/*;q=0.5"},
        timeout=timeout,
    )
    response.raise_for_status()
    return feedparser.parse(response.content)


def rss_collect(config):
    articles = []
    for source in config.get("rss", []):
        if not source.get("enabled", True):
            continue
        try:
            feed = request_feed(source["url"])
        except Exception:
            feed = feedparser.parse(source["url"])
        for entry in feed.entries[: int(source.get("max_items", 50))]:
            title, url = clean(entry.get("title")), entry.get("link", "")
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
                "published_at": dt(entry.get("published") or entry.get("updated")).isoformat(),
                "content": content,
                "language": source.get("language", ""),
            })
    return articles


def reddit_collect(config):
    settings = config.get("reddit", {})
    if not settings.get("enabled", True):
        return []
    articles = []
    per_community = max(5, min(30, int(settings.get("max_items_per_community", 12))))
    for community in settings.get("communities", []):
        community = re.sub(r"[^A-Za-z0-9_]", "", str(community))
        if not community:
            continue
        urls = [
            f"https://www.reddit.com/r/{community}/new/.rss?limit={per_community}",
            f"https://old.reddit.com/r/{community}/new/.rss?limit={per_community}",
        ]
        feed = None
        for url in urls:
            try:
                feed = request_feed(url, user_agent="AIIntelRadar/1.4 by u/lanjy7686-dot (public RSS reader)")
                if feed.entries:
                    break
            except Exception:
                feed = None
        if not feed:
            time.sleep(0.8)
            continue
        for entry in feed.entries[:per_community]:
            title, url = clean(entry.get("title")), entry.get("link", "")
            if not title or not url:
                continue
            author = clean(entry.get("author", "")).replace("/u/", "u/")
            content_value = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            summary = clean(entry.get("summary") or content_value)
            articles.append({
                "title": title,
                "url": url,
                "source": f"Reddit · r/{community}",
                "source_type": "Reddit",
                "published_at": dt(entry.get("published") or entry.get("updated")).isoformat(),
                "author": author,
                "content": summary,
                "reddit_community": community,
            })
        time.sleep(0.8)
    return articles


def gdelt_collect(config):
    settings = config.get("gdelt", {})
    if not settings.get("enabled", False):
        return []
    response = requests.get(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={"query": settings["query"], "mode": "ArtList", "format": "json", "maxrecords": settings.get("max_items", 50), "sort": "HybridRel", "timespan": settings.get("timespan", "1d")},
        headers={"User-Agent": UA},
        timeout=35,
    )
    response.raise_for_status()
    return [{
        "title": clean(item.get("title")),
        "url": item.get("url", ""),
        "source": item.get("domain", "GDELT"),
        "source_type": "全球新闻",
        "published_at": dt(item.get("seendate")).isoformat(),
        "content": "",
    } for item in response.json().get("articles", []) if item.get("title") and item.get("url")]


def arxiv_collect(config):
    settings = config.get("arxiv", {})
    if not settings.get("enabled", True):
        return []
    url = "https://export.arxiv.org/api/query?" + urlencode({
        "search_query": settings["query"],
        "start": 0,
        "max_results": settings.get("max_items", 50),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    feed = feedparser.parse(url)
    return [{
        "title": clean(entry.get("title")),
        "url": entry.get("link", ""),
        "source": "arXiv",
        "source_type": "论文",
        "published_at": dt(entry.get("published")).isoformat(),
        "author": ", ".join(a.get("name", "") for a in entry.get("authors", [])),
        "content": clean(entry.get("summary")),
    } for entry in feed.entries if entry.get("title") and entry.get("link")]


def hackernews_collect(config):
    settings = config.get("hackernews", {})
    if not settings.get("enabled", True):
        return []
    ids = requests.get("https://hacker-news.firebaseio.com/v0/newstories.json", timeout=25).json()[: int(settings.get("scan_items", 250))]
    keywords = [word.lower() for word in settings.get("keywords", [])]

    def fetch_item(item_id):
        try:
            return requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=12).json() or {}
        except Exception:
            return {}

    articles = []
    with cf.ThreadPoolExecutor(max_workers=12) as executor:
        for item in executor.map(fetch_item, ids):
            title = item.get("title", "")
            text = f"{title} {item.get('text', '')}".lower()
            if not title or not any(keyword in text for keyword in keywords):
                continue
            articles.append({
                "title": title,
                "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
                "source": "Hacker News",
                "source_type": "技术社区",
                "published_at": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc).isoformat(),
                "author": item.get("by", ""),
                "content": clean(item.get("text", "")),
                "engagement": int(item.get("score", 0) or 0) + int(item.get("descendants", 0) or 0),
            })
    return articles[: int(settings.get("max_items", 50))]


def parse_link_line(line):
    parts = [part.strip() for part in line.split("|")]
    return {
        "url": parts[0] if parts else "",
        "title": parts[1] if len(parts) > 1 else "",
        "author": parts[2] if len(parts) > 2 else "",
        "summary": parts[3] if len(parts) > 3 else "",
    }


def extract_public_page(url):
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
        },
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    def meta_content(selector):
        node = soup.select_one(selector)
        return clean(node.get("content", "")) if node else ""

    title = meta_content("meta[property='og:title']") or meta_content("meta[name='twitter:title']")
    description = meta_content("meta[property='og:description']") or meta_content("meta[name='description']")
    author = meta_content("meta[name='author']")
    if not title and soup.title:
        title = clean(soup.title.get_text(" ", strip=True))
    return title, author, description


def wechat_collect(config):
    path = ROOT / config.get("domestic_platforms", {}).get("wechat_urls_file", "config/wechat_urls.txt")
    if not path.exists():
        return []
    articles = []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    for line in lines:
        item = parse_link_line(line)
        url = item["url"]
        if not url:
            continue
        title, author, body = item["title"], item["author"], item["summary"]
        if not title:
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 Chrome/126 Safari/537.36"}, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                meta = soup.select_one("meta[property='og:title']")
                title = (meta.get("content") if meta else "") or clean(soup.select_one("#activity-name").get_text(" ", strip=True) if soup.select_one("#activity-name") else "")
                author = author or clean(soup.select_one("#js_name").get_text(" ", strip=True) if soup.select_one("#js_name") else "")
                body = body or clean(soup.select_one("#js_content").get_text(" ", strip=True) if soup.select_one("#js_content") else "")
            except Exception:
                continue
        if title:
            articles.append({
                "title": clean(title),
                "url": url,
                "source": author or "微信公众号",
                "source_type": "微信公众号",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "author": author,
                "content": body,
                "language": "zh",
            })
    return articles


def manual_social_collect(config, platform_key, source_type, default_source):
    path_value = config.get("domestic_platforms", {}).get(platform_key)
    if not path_value:
        return []
    path = ROOT / path_value
    if not path.exists():
        return []
    articles = []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    for line in lines:
        item = parse_link_line(line)
        url = item["url"]
        if not url:
            continue
        title, author, summary = item["title"], item["author"], item["summary"]
        if not title:
            try:
                title, fetched_author, fetched_summary = extract_public_page(url)
                author = author or fetched_author
                summary = summary or fetched_summary
            except Exception:
                title = ""
        if not title:
            continue
        articles.append({
            "title": clean(title),
            "url": url,
            "source": author or default_source,
            "source_type": source_type,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "author": author,
            "content": summary,
            "language": "zh",
        })
    return articles


def xiaohongshu_collect(config):
    return manual_social_collect(config, "xiaohongshu_urls_file", "小红书", "小红书公开笔记")


def douyin_collect(config):
    return manual_social_collect(config, "douyin_urls_file", "抖音", "抖音公开内容")


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    collectors = [
        ("RSS", rss_collect),
        ("Reddit", reddit_collect),
        ("arXiv", arxiv_collect),
        ("Hacker News", hackernews_collect),
        ("微信公众号", wechat_collect),
        ("小红书", xiaohongshu_collect),
        ("抖音", douyin_collect),
    ]
    if config.get("gdelt", {}).get("enabled", False):
        collectors.append(("GDELT", gdelt_collect))

    all_items, errors = [], []
    source_status = {
        "X": {"enabled": False, "state": "free_search_only", "count": 0, "message": "完全免费模式：不调用X API，网页提供一键X实时搜索。"},
        "小红书搜索": {"enabled": True, "state": "free_search_only", "count": 0, "message": "通过站内搜索入口查看实时结果；公开链接可加入清单。"},
        "抖音搜索": {"enabled": True, "state": "free_search_only", "count": 0, "message": "通过站内搜索入口查看实时结果；公开链接可加入清单。"},
        "微信搜索": {"enabled": True, "state": "free_search_only", "count": 0, "message": "通过搜狗微信搜索入口查看公开文章；公开链接可加入清单。"},
    }

    with cf.ThreadPoolExecutor(max_workers=len(collectors)) as executor:
        jobs = {executor.submit(function, config): name for name, function in collectors}
        for future, name in [(future, name) for future, name in jobs.items()]:
            try:
                items = future.result()
                all_items.extend(items)
                source_status[name] = {"state": "fetched", "count": len(items)}
            except Exception as exc:
                errors.append(f"{name}: {exc}")
                source_status[name] = {"state": "error", "count": 0, "message": str(exc)}

    seen, output = set(), []
    for article in all_items:
        key = hashlib.sha256((re.sub(r"\W+", "", article.get("title", "").lower()) + "|" + canonical(article.get("url", ""))).encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        output.append(classify(article))

    output.sort(key=lambda item: (item.get("relevance_score", 0), item.get("engagement", 0), dt(item.get("published_at"))), reverse=True)
    type_counts = {}
    for article in output:
        source_type = article.get("source_type", "其他")
        type_counts[source_type] = type_counts.get(source_type, 0) + 1
    source_status["来源统计"] = type_counts

    payload = {
        "mode": "free",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(output),
        "errors": errors,
        "source_status": source_status,
        "articles": output[:900],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "count": len(output),
        "errors": errors,
        "domestic": type_counts.get("国内资讯", 0),
        "wechat": type_counts.get("微信公众号", 0),
        "xiaohongshu": type_counts.get("小红书", 0),
        "douyin": type_counts.get("抖音", 0),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
