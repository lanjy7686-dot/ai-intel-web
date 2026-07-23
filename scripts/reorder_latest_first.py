from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
MARKER = "<!-- LATEST_NEWS_FIRST_V1 -->"

html = INDEX.read_text(encoding="utf-8")

if MARKER in html:
    print("latest-news-first layout already applied")
    raise SystemExit(0)

watch_pattern = re.compile(
    r'\n*<section class="watch-panel panel" id="serenityWatch">.*?</section>\s*'
    r'<script async src="https://platform\.x\.com/widgets\.js" charset="utf-8"></script>\s*',
    re.S,
)
stats_pattern = re.compile(r'\n*<section class="stats">.*?</section>\s*', re.S)
main_pattern = re.compile(r'\n*<main class="layout">.*?</main>\s*', re.S)

watch_match = watch_pattern.search(html)
stats_match = stats_pattern.search(html)
main_match = main_pattern.search(html)

if not (watch_match and stats_match and main_match):
    raise RuntimeError("Could not locate Serenity, stats, or latest-news blocks")

watch_block = watch_match.group(0).strip()
stats_block = stats_match.group(0).strip()
main_block = main_match.group(0).strip()

# Remove the three movable blocks from their old locations.
for pattern in (watch_pattern, stats_pattern, main_pattern):
    html = pattern.sub("\n", html, count=1)

source_notice = '<div id="sourceNotice" class="notice" style="display:none"></div>'
if source_notice not in html:
    raise RuntimeError("Could not locate source notice insertion point")

new_order = (
    source_notice
    + "\n\n"
    + main_block
    + "\n\n"
    + stats_block
    + "\n\n"
    + watch_block
)
html = html.replace(source_notice, new_order, 1)
html = html.replace("<!-- SERENITY_X_WATCH_V1 -->", "<!-- SERENITY_X_WATCH_V1 -->\n" + MARKER, 1)
html = html.replace(
    '<div class="notice"><strong>最新规则：</strong>',
    '<div class="notice"><strong>首页顺序：</strong>最新资讯已置顶，重点博主与统计信息随后展示。<br><strong>最新规则：</strong>',
    1,
)

INDEX.write_text(html, encoding="utf-8")
print("latest news moved before Serenity and stats")
