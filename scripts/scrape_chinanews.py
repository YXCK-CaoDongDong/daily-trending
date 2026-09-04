#!/usr/bin/env python3
"""Scrape recent chinanews.com.cn article links from listing pages."""

from __future__ import annotations

import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

PAGES = [
    "https://www.chinanews.com.cn/gn/",
    "https://www.chinanews.com.cn/sh/",
    "https://www.chinanews.com.cn/cj/",
    "https://www.chinanews.com.cn/gj/",
    "https://www.chinanews.com.cn/scroll-news/news.html",
]


def scrape() -> list[tuple[str, str]]:
    seen: set[str] = set()
    results: list[tuple[str, str]] = []
    for page in PAGES:
        try:
            resp = requests.get(page, headers={"User-Agent": UA}, timeout=20)
            resp.encoding = "gb2312"
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if not re.search(r"/20\d{2}/\d{2}-\d{2}/\d+\.shtml", href):
                    continue
                url = urljoin("https://www.chinanews.com.cn/", href)
                if url in seen:
                    continue
                title = a.get_text(strip=True)
                if len(title) < 8:
                    continue
                seen.add(url)
                results.append((title, url))
        except Exception as exc:
            print(f"ERR {page}: {exc}", file=sys.stderr)
    return results


if __name__ == "__main__":
    for title, url in scrape():
        print(f"{title}\t{url}")
