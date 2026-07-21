from pathlib import Path
import json
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

path = Path(__file__).resolve().parents[1] / "config" / "sources.json"
cfg = json.loads(path.read_text(encoding="utf-8"))

cfg["freshness"] = {
    "default_rss_max_age_hours": 168,
    "manual_max_age_hours": 720,
    "retention_hours": 720,
    "future_tolerance_hours": 6,
    "max_output": 500,
}
cfg.setdefault("arxiv", {})["max_age_hours"] = 168
cfg.setdefault("hackernews", {})["max_age_hours"] = 72
cfg.setdefault("reddit", {})["max_age_hours"] = 72

official = {
    "OpenAI News", "Google AI Blog", "Google DeepMind", "Microsoft Official Blog",
    "AWS Artificial Intelligence", "NVIDIA Blog", "GitHub AI & ML", "Hugging Face Blog",
}
for source in cfg.get("rss", []):
    source["require_date"] = True
    name = source.get("name", "")
    url = source.get("url", "")
    if "news.google.com/rss/search" in url:
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        q = query.get("q", [""])[0]
        if "when:" not in q:
            # 聚合新闻只保留近3天；中文综合资讯进一步限制为近1天。
            window = "1d" if name in {"中文AI新闻聚合", "中文AI今日资讯"} else "3d"
            q = f"({q}) when:{window}"
        query["q"] = [q]
        flat = [(k, v) for k, values in query.items() for v in values]
        source["url"] = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(flat), parts.fragment))
        source["max_age_hours"] = 30 if "when:1d" in q else 78
        source["max_items"] = min(int(source.get("max_items", 50)), 50)
    elif name in official:
        source["max_age_hours"] = 168
    else:
        source["max_age_hours"] = 72

path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("source freshness policy applied")
