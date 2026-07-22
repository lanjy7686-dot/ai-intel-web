from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "articles.json"
UA = "AI-Intel-Radar/1.6 (priority public news feeds)"


def clean(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(value: object) -> datetime | None:
    try:
        parsed = dateparser.parse(str(value))
        if not parsed:
            return None
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def canonical(url: str) -> str:
    try:
        parts = urlsplit(url)
        ignored = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "source", "from"}
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in ignored]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))
    except Exception:
        return url


def gnews(query: str, language: str) -> str:
    if language == "en":
        params = {"q": f"({query}) when:1d", "hl": "en-US", "gl": "US", "ceid": "US:en"}
    else:
        params = {"q": f"({query}) when:1d", "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"}
    return "https://news.google.com/rss/search?" + urlencode(params)


FEEDS = [
    ("彭博社", "en", 'site:bloomberg.com (artificial intelligence OR generative AI OR OpenAI OR Anthropic OR DeepSeek OR Gemini OR Claude OR xAI)'),
    ("彭博社", "en", 'site:bloomberg.com (NVIDIA OR AMD OR TSMC OR ASML OR HBM OR semiconductor OR AI chip OR data center)'),
    ("彭博社", "en", 'site:bloomberg.com (AI funding OR AI investment OR valuation OR earnings OR IPO OR acquisition)'),
    ("彭博社", "en", 'Bloomberg (artificial intelligence OR AI chip OR data center OR robotics OR AI investment)'),
    ("财联社", "zh", 'site:cls.cn (人工智能 OR 大模型 OR DeepSeek OR 智能体 OR 具身智能 OR 人形机器人)'),
    ("财联社", "zh", 'site:cls.cn (AI芯片 OR 算力 OR 英伟达 OR 华为昇腾 OR 寒武纪 OR 光模块 OR CPO OR 液冷 OR 数据中心)'),
    ("财联社", "zh", 'site:cls.cn (AI融资 OR 人工智能投资 OR 大模型估值 OR AI概念股 OR 并购 OR IPO OR 财报)'),
    ("财联社", "zh", '财联社 (人工智能 OR 大模型 OR AI芯片 OR 算力 OR 机器人 OR 融资)'),
]


def classify(text: str) -> tuple[str, list[str]]:
    lowered = text.lower()
    if any(k in lowered for k in ["funding", "valuation", "investment", "earnings", "ipo", "acquisition", "融资", "估值", "投资", "财报", "并购", "股价"]):
        return "投资商业", ["重点媒体", "资本市场"]
    if any(k in lowered for k in ["chip", "gpu", "semiconductor", "hbm", "data center", "芯片", "算力", "光模块", "液冷", "数据中心"]):
        return "产业动态", ["重点媒体", "产业链"]
    if any(k in lowered for k in ["model", "agent", "robot", "research", "模型", "智能体", "机器人", "技术"]):
        return "技术研究", ["重点媒体", "新技术"]
    return "产业动态", ["重点媒体"]


def collect() -> list[dict]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=30)
    rows: list[dict] = []
    for focus, language, query in FEEDS:
        url = gnews(query, language)
        try:
            response = requests.get(url, headers={"User-Agent": UA}, timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception:
            continue
        for entry in feed.entries[:100]:
            title = clean(entry.get("title"))
            link = str(entry.get("link") or "")
            published = parse_date(entry.get("published") or entry.get("updated"))
            source_obj = entry.get("source") or {}
            publisher = clean(source_obj.get("title", "")) if isinstance(source_obj, dict) else ""
            publisher_lower = publisher.lower()
            is_match = (
                (focus == "彭博社" and ("bloomberg" in publisher_lower or "bloomberg" in title.lower()))
                or (focus == "财联社" and ("财联社" in publisher or "cls.cn" in link.lower()))
            )
            if not title or not link or not published or published < cutoff or published > now + timedelta(hours=6) or not is_match:
                continue
            summary = clean(entry.get("summary") or entry.get("description") or title)[:320]
            category, tags = classify(f"{title} {summary}")
            age_hours = max(0.0, (now - published).total_seconds() / 3600)
            score = max(70, min(98, 96 - int(age_hours / 2)))
            rows.append({
                "title": title,
                "url": link,
                "source": focus,
                "source_type": "主流媒体",
                "published_at": published.isoformat(),
                "language": language,
                "date_verified": True,
                "category": category,
                "relevance_score": score,
                "tags": tags + [focus],
                "summary": summary,
                "source_priority": 18,
            })
    return rows


def item_key(item: dict) -> str:
    normalized_title = re.sub(r"\W+", "", str(item.get("title", "")).lower())
    return hashlib.sha256(f"{normalized_title}|{canonical(str(item.get('url', '')))}".encode()).hexdigest()


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"articles": []}
    existing = list(payload.get("articles") or [])
    priority = collect()
    seen: set[str] = set()
    merged: list[dict] = []
    for item in priority + existing:
        key = item_key(item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    merged.sort(
        key=lambda item: (
            parse_date(item.get("published_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc),
            int(item.get("source_priority", 0) or 0),
            int(item.get("relevance_score", 0) or 0),
        ),
        reverse=True,
    )
    now = datetime.now(timezone.utc)
    payload["updated_at"] = now.isoformat()
    payload["articles"] = merged[:1200]
    payload["count"] = len(merged)
    policy = payload.setdefault("freshness_policy", {})
    policy["undated_items"] = "discarded"
    policy["last_24h"] = sum(1 for item in merged if (parse_date(item.get("published_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc)) >= now - timedelta(hours=24))
    policy["last_72h"] = sum(1 for item in merged if (parse_date(item.get("published_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc)) >= now - timedelta(hours=72))
    status = payload.setdefault("source_status", {})
    source_counts: dict[str, int] = {}
    for item in merged:
        source_type = str(item.get("source_type") or "其他")
        source_counts[source_type] = source_counts.get(source_type, 0) + 1
    status["来源统计"] = source_counts
    status["重点媒体"] = {
        "彭博社": sum(1 for item in merged if item.get("source") == "彭博社"),
        "财联社": sum(1 for item in merged if item.get("source") == "财联社"),
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"added": len(priority), "focus": status["重点媒体"], "count": len(merged)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
