#!/usr/bin/env python3
"""Add domestic rows until 30 total (chinanews RSS)."""

from __future__ import annotations

import json
import sys
import time
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refetch_json_content import extract, fetch_html, matches_title

FEEDS = [
    "https://www.chinanews.com.cn/rss/scroll-news.xml",
    "https://www.chinanews.com.cn/rss/china.xml",
    "https://www.chinanews.com.cn/rss/importnews.xml",
]


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    seen = {x["url"].split("?")[0] for x in items}
    dom = [x for x in items if x["region"] == "domestic"]
    intl = [x for x in items if x["region"] == "international"]

    for feed in FEEDS:
        if len(dom) >= 30:
            break
        text = fetch_html(feed)
        if not text:
            continue
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            continue
        for item in root.findall(".//item"):
            title = unescape((item.findtext("title") or "").strip())
            link = (item.findtext("link") or "").strip()
            if not link or link.split("?")[0] in seen:
                continue
            html = fetch_html(link)
            body = extract(link, html) if html else None
            if not body or len(body) < 200 or not matches_title(body, title):
                continue
            seen.add(link.split("?")[0])
            dom.append(
                {
                    "title": title,
                    "source": "中国新闻网",
                    "region": "domestic",
                    "url": link,
                    "content": body[:20000],
                }
            )
            if len(dom) >= 30:
                break
            time.sleep(0.15)

    final = dom[:30] + intl[:20]
    for i, row in enumerate(final, 1):
        row["rank_no"] = i
    path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"quick backfill: total={len(final)} dom={len(dom[:30])} intl={len(intl[:20])}")
    return 0 if len(final) == 50 else 1


if __name__ == "__main__":
    raise SystemExit(main())
