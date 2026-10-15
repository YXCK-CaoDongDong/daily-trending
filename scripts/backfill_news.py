#!/usr/bin/env python3
"""Backfill JSON to 50 items (30 domestic / 20 intl) from RSS when slots are missing."""

from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Reuse refetch extractors
sys.path.insert(0, str(Path(__file__).resolve().parent))
from refetch_json_content import (  # noqa: E402
    JUNK_TITLE_RE,
    extract,
    fetch_html,
    matches_title,
    translate,
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

DOMESTIC_RSS = [
    ("中国新闻网", "https://www.chinanews.com.cn/rss/importnews.xml"),
    ("新华网", "https://www.news.cn/rss/politics.xml"),
    ("人民网", "https://www.people.com.cn/rss/politics.xml"),
]
INTL_RSS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("The Guardian", "https://www.theguardian.com/international/rss"),
    ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("Associated Press", "https://rsshub.app/apnews/topics/apf-topnews"),
    ("Deutsche Welle", "https://rss.dw.com/rdf/rss-en-all"),
    ("Kyodo News", "https://english.kyodonews.net/rss/news.xml"),
    ("NHK World", "https://www3.nhk.or.jp/rss/news/nhkworld/english.xml"),
]
MIN_CONTENT = 300


def rss_items(source: str, url: str, region: str):
    text = fetch_html(url)
    if not text:
        return
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return
    for item in root.findall(".//item"):
        t = unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        if not t or not link or JUNK_TITLE_RE.search(t):
            continue
        if "/news/videos/" in link or "/video/" in link:
            continue
        host = urlparse(link).hostname or ""
        if region == "international" and (host.endswith(".cn") or "xinhuanet" in host):
            continue
        if region == "domestic" and not (host.endswith(".cn") or "chinanews" in host or "people.com" in host):
            continue
        yield {"title": t, "source": source, "url": link, "region": region}


def fill_body(row: dict) -> None:
    html = fetch_html(row["url"])
    if not html:
        return
    body = extract(row["url"], html)
    if not body:
        return
    title = row["title"]
    if row["region"] == "international":
        title = translate(title)
        if not re.search(r"[\u4e00-\u9fff]", body[:200]):
            body = translate(body)
    elif not re.search(r"[\u4e00-\u9fff]", title):
        title = translate(title)
    if matches_title(body, title):
        row["title"] = title
        row["content"] = body[:20000]


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    seen = {x["url"].split("?")[0] for x in items}
    dom = sum(1 for x in items if x["region"] == "domestic")
    intl = sum(1 for x in items if x["region"] == "international")

    pools = []
    for s, u in DOMESTIC_RSS:
        pools.extend(list(rss_items(s, u, "domestic")))
    for s, u in INTL_RSS:
        pools.extend(list(rss_items(s, u, "international")))

    rank = max(x["rank_no"] for x in items) if items else 0

    def need_dom():
        return sum(1 for x in items if x["region"] == "domestic") < 30

    def need_intl():
        return sum(1 for x in items if x["region"] == "international") < 20

    for cand in pools:
        if cand["url"].split("?")[0] in seen:
            continue
        if cand["region"] == "domestic" and not need_dom():
            continue
        if cand["region"] == "international" and not need_intl():
            continue
        row = {**cand, "content": "", "rank_no": 0}
        fill_body(row)
        if len(row.get("content") or "") < MIN_CONTENT:
            continue
        rank += 1
        row["rank_no"] = rank
        items.append(row)
        seen.add(cand["url"].split("?")[0])
        if not need_dom() and not need_intl():
            break
        time.sleep(0.25)

    # refill empty content slots
    for row in items:
        if row.get("content") and len(row["content"]) >= MIN_CONTENT:
            continue
        if JUNK_TITLE_RE.search(row.get("title", "")):
            continue
        fill_body(row)
        time.sleep(0.2)

    items = [x for x in items if x.get("title") and not JUNK_TITLE_RE.search(x["title"])]
    items.sort(key=lambda x: (0 if x["region"] == "domestic" else 1, x.get("rank_no", 999)))
    for i, row in enumerate(items[:50], start=1):
        row["rank_no"] = i
    items = items[:50]

    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"final {len(items)} domestic={sum(1 for x in items if x['region']=='domestic')} "
        f"intl={sum(1 for x in items if x['region']=='international')} "
        f"empty={sum(1 for x in items if not x.get('content'))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
