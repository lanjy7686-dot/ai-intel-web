from pathlib import Path
import re

path = Path(__file__).with_name("fetch_news.py")
text = path.read_text(encoding="utf-8")
marker = "# FRESHNESS_PATCH_V2"
if marker in text:
    print("freshness patch already applied")
    raise SystemExit(0)

# 1) 让 default=None 真正返回 None，避免缺失日期被误当成“现在”。
old_dt = '''def dt(value, default=None):
    try:
        parsed = dateparser.parse(str(value))
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return default or datetime.now(timezone.utc)
'''
new_dt = '''_DATE_DEFAULT = object()


def dt(value, default=_DATE_DEFAULT):
    try:
        if value in (None, "", 0):
            raise ValueError("missing date")
        parsed = dateparser.parse(str(value))
        if not parsed:
            raise ValueError("invalid date")
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc) if default is _DATE_DEFAULT else default


def is_fresh(published, max_age_hours=168, future_tolerance_hours=6):
    if not published:
        return False
    now = datetime.now(timezone.utc)
    if published > now + __import__("datetime").timedelta(hours=future_tolerance_hours):
        return False
    return published >= now - __import__("datetime").timedelta(hours=max_age_hours)
'''
if old_dt not in text:
    raise RuntimeError("dt function pattern not found")
text = text.replace(old_dt, new_dt)

# 2) RSS只接收有可靠发布时间、且处于来源时间窗口内的文章。
rss_pattern = re.compile(r"def rss_collect\(config\):.*?\n\n\ndef reddit_collect", re.S)
new_rss = '''def rss_collect(config):
    articles = []
    default_max_age = int(config.get("freshness", {}).get("default_rss_max_age_hours", 168))
    for source in config.get("rss", []):
        if not source.get("enabled", True):
            continue
        try:
            feed = request_feed(source["url"])
        except Exception:
            feed = feedparser.parse(source["url"])
        max_age = int(source.get("max_age_hours", default_max_age))
        for entry in feed.entries[: int(source.get("max_items", 50))]:
            title, url = clean(entry.get("title")), entry.get("link", "")
            raw_date = entry.get("published") or entry.get("updated") or entry.get("created")
            published = dt(raw_date, default=None)
            if not title or not url or not is_fresh(published, max_age):
                continue
            content = clean(entry.get("summary") or entry.get("description") or "")
            if entry.get("content"):
                content = clean(" ".join(item.get("value", "") for item in entry.get("content", [])))
            articles.append({
                "title": title,
                "url": url,
                "source": source.get("name", "RSS"),
                "source_type": source.get("source_type", "RSS"),
                "published_at": published.isoformat(),
                "content": content,
                "language": source.get("language", ""),
                "date_verified": True,
            })
    return articles


def reddit_collect'''
text, count = rss_pattern.subn(new_rss, text, count=1)
if count != 1:
    raise RuntimeError("rss_collect pattern not found")

# 3) 所有来源进入最终列表前，再做一次日期真实性和30天保留期检查。
loop_old = '''    for article in all_items:
        key = hashlib.sha256'''
loop_new = '''    for article in all_items:
        published = dt(article.get("published_at"), default=None)
        if not is_fresh(published, int(config.get("freshness", {}).get("retention_hours", 720))):
            continue
        article["published_at"] = published.isoformat()
        article["date_verified"] = True
        key = hashlib.sha256'''
if loop_old not in text:
    raise RuntimeError("final article loop pattern not found")
text = text.replace(loop_old, loop_new)

# 4) 输出近24小时/72小时统计，并把展示上限降为500条。
payload_pattern = re.compile(
    r'    payload = \{"mode": "free", "updated_at": datetime\.now\(timezone\.utc\)\.isoformat\(\), "count": len\(output\), "errors": errors, "source_status": source_status, "articles": output\[:700\]\}'
)
payload_new = '''    now = datetime.now(timezone.utc)
    last_24h = sum(
        1 for item in output
        if (dt(item.get("published_at"), default=None) or datetime(1970, 1, 1, tzinfo=timezone.utc))
        >= now - __import__("datetime").timedelta(hours=24)
    )
    last_72h = sum(
        1 for item in output
        if (dt(item.get("published_at"), default=None) or datetime(1970, 1, 1, tzinfo=timezone.utc))
        >= now - __import__("datetime").timedelta(hours=72)
    )
    max_output = int(config.get("freshness", {}).get("max_output", 500))
    payload = {
        "mode": "free",
        "updated_at": now.isoformat(),
        "count": len(output),
        "errors": errors,
        "freshness_policy": {
            "undated_items": "discarded",
            "last_24h": last_24h,
            "last_72h": last_72h,
        },
        "source_status": source_status,
        "articles": output[:max_output],
    }'''
text, count = payload_pattern.subn(payload_new, text, count=1)
if count != 1:
    raise RuntimeError("payload pattern not found")

text = text.replace('UA = "AI-Intel-Radar/1.4', marker + '\nUA = "AI-Intel-Radar/1.5')
path.write_text(text, encoding="utf-8")
print("freshness patch applied")
