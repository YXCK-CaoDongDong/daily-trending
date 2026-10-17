#!/usr/bin/env python3
"""Fetch up to 20 international articles (English body) from allowed RSS feeds."""

from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refetch_json_content import extract, fetch_html, matches_title  # noqa: E402

FEEDS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("Deutsche Welle", "https://rss.dw.com/rdf/rss-en-all"),
    ("NHK World", "https://www3.nhk.or.jp/rss/news/nhkworld/english.xml"),
]
JUNK = re.compile(r"Kelly Clarkson|protein powder|Dog named|animal of the year", re.I)


def items(feed: str):
    text = fetch_html(feed)
    if not text:
        return
    root = ET.fromstring(text)
    for it in root.findall(".//item"):
        title = unescape((it.findtext("title") or "").strip())
        link = (it.findtext("link") or "").strip()
        if not title or not link or JUNK.search(title):
            continue
        if "/news/videos/" in link or "/video/" in link:
            continue
        yield title, link


def main() -> int:
    out: list[dict] = []
    seen: set[str] = set()
    for source, feed in FEEDS:
        for title, link in items(feed):
            key = link.split("?")[0]
            if key in seen:
                continue
            html = fetch_html(link)
            body = extract(link, html) if html else ""
            if len(body) < 400 or not matches_title(body, title):
                continue
            seen.add(key)
            out.append(
                {
                    "title_en": title,
                    "source": source,
                    "url": link,
                    "body_en": body[:8000],
                }
            )
            if len(out) >= 20:
                break
            time.sleep(0.15)
        if len(out) >= 20:
            break
    Path("/workspace/data/intl_english.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"intl {len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
