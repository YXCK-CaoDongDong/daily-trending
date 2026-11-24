#!/usr/bin/env python3
"""Assemble exactly 50 items (30 domestic chinanews + 20 intl RSS) with per-URL fetch."""

from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from refetch_json_content import extract, fetch_html, matches_title, translate  # noqa: E402

TZ = ZoneInfo("Asia/Shanghai")
JUNK = re.compile(r"明星|八卦|演唱会|蛋白粉|立即注册|性掠夺|Kelly Clarkson", re.I)

DOMESTIC_FEEDS = [
    "https://www.chinanews.com.cn/rss/scroll-news.xml",
    "https://www.chinanews.com.cn/rss/importnews.xml",
    "https://www.chinanews.com.cn/rss/china.xml",
]
MIN_DOM = 200
MIN_INTL = 200
INTL_FEEDS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("Deutsche Welle", "https://rss.dw.com/rdf/rss-en-all"),
    ("NHK World", "https://www3.nhk.or.jp/rss/news/nhkworld/english.xml"),
]


def rss_pairs(url: str, limit: int = 80):
    text = fetch_html(url)
    if not text:
        return
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return
    n = 0
    for item in root.findall(".//item"):
        title = unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        if not title or not link or JUNK.search(title):
            continue
        if "/news/videos/" in link or "/video/" in link:
            continue
        yield title, link
        n += 1
        if n >= limit:
            break


def body_for(url: str, title: str, region: str) -> tuple[str, str]:
    html = fetch_html(url)
    if not html:
        return title, ""
    raw = extract(url, html) or ""
    if not raw or not matches_title(raw, title):
        return title, ""
    t = title
    c = raw
    if region == "international":
        pass  # translated in merge step (external APIs rate-limited)
    if len(c) > 20000:
        c = c[:20000]
    return t, c


def main() -> int:
    run_date = datetime.now(TZ).date()
    out = ROOT / "data" / f"daily_news_{run_date.isoformat()}.json"
    seen: set[str] = set()
    rows: list[dict] = []

    for feed in DOMESTIC_FEEDS:
        if sum(1 for r in rows if r["region"] == "domestic") >= 30:
            break
        for title, link in rss_pairs(feed, 120):
            key = link.split("?")[0]
            if key in seen or "chinanews.com.cn" not in link:
                continue
            t, c = body_for(link, title, "domestic")
            if len(c) < MIN_DOM:
                continue
            seen.add(key)
            rows.append(
                {
                    "title": t,
                    "source": "中国新闻网",
                    "region": "domestic",
                    "url": link,
                    "content": c,
                }
            )
            if sum(1 for r in rows if r["region"] == "domestic") >= 30:
                break
            time.sleep(0.12)

    for source, feed in INTL_FEEDS:
        if sum(1 for r in rows if r["region"] == "international") >= 20:
            break
        for title, link in rss_pairs(feed, 60):
            key = link.split("?")[0]
            if key in seen:
                continue
            host = urlparse(link).hostname or ""
            if host.endswith(".cn"):
                continue
            t, c = body_for(link, title, "international")
            if len(c) < MIN_INTL:
                continue
            seen.add(key)
            rows.append(
                {
                    "title": t,
                    "source": source,
                    "region": "international",
                    "url": link,
                    "content": c,
                }
            )
            if sum(1 for r in rows if r["region"] == "international") >= 20:
                break
            time.sleep(0.2)

    domestic = [r for r in rows if r["region"] == "domestic"][:30]
    intl = [r for r in rows if r["region"] == "international"][:20]
    final = domestic + intl
    for i, r in enumerate(final, 1):
        r["rank_no"] = i

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"wrote {out} count={len(final)} dom={len(domestic)} intl={len(intl)} "
        f"empty={sum(1 for x in final if not x.get('content'))}"
    )
    return 0 if len(final) == 50 else 1


if __name__ == "__main__":
    raise SystemExit(main())
