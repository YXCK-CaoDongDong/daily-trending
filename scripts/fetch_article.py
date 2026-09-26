#!/usr/bin/env python3
"""Fetch and extract article text from a news URL."""

from __future__ import annotations

import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

JUNK_PATTERNS = re.compile(
    r"页面没有找到|Page not found|404|access denied|登录|sign in|subscribe to read|"
    r"enable javascript|security verification|cookie",
    re.I,
)


def fetch_html(url: str, timeout: int = 25) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code >= 400:
            return None
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    except Exception:
        return None


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_content(html: str, url: str) -> str | None:
    if not html or JUNK_PATTERNS.search(html[:3000]):
        return None
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    host = (urlparse(url).hostname or "").lower()

    selectors: list[str] = []
    if "reuters.com" in host:
        selectors = ["div[data-testid='paragraph']", "article p"]
    elif "bbc.com" in host or "bbc.co.uk" in host:
        selectors = ["article p", "div[data-component='text-block'] p"]
    elif "theguardian.com" in host:
        selectors = ["div.article-body-viewer p", "article p"]
    elif "aljazeera.com" in host:
        selectors = ["div.wysiwyg p", "article p"]
    elif "dw.com" in host:
        selectors = ["div.rich-text p", "div[itemprop='articleBody'] p", "article p", "p"]
    elif "news.un.org" in host:
        selectors = ["div.field-item p", "article p"]
    elif "yna.co.kr" in host:
        selectors = ["article p", "div.story-news p"]
    elif "chinanews.com.cn" in host:
        selectors = ["div.left_zw p", "div.left_zw"]
    elif any(x in host for x in ("news.cn", "xinhuanet", "people.com.cn", "cctv.com", "gov.cn")):
        selectors = ["div#detail p", "div.detail p", "div.left_zw p", "div.content p", "article p", "p"]
    else:
        selectors = ["article p", "div.article p", "div.content p", "p"]

    paragraphs: list[str] = []
    for sel in selectors:
        nodes = soup.select(sel)
        if len(nodes) >= 2:
            paragraphs = [_clean_text(n.get_text(" ", strip=True)) for n in nodes]
            break

    if not paragraphs:
        paragraphs = [_clean_text(p.get_text(" ", strip=True)) for p in soup.find_all("p")]

    junk_line_re = re.compile(
        r"欢迎习近平|当AI重新定义|不是中国的四大发明|从北美红杉|许绍理：|美国地名|李子柒：|"
        r"新疆这座小城|比了76年|品美食|当户外茶会|人体也能带电|开学第一天|名字里带"
    )
    paragraphs = [p for p in paragraphs if len(p) > 20 and not junk_line_re.search(p)]
    if not paragraphs:
        return None
    text = "\n".join(paragraphs)
    if len(text) < 60:
        return None
    if len(text) > 20000:
        text = text[:20000]
    return text


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_article.py <url>", file=sys.stderr)
        return 1
    url = sys.argv[1]
    html = fetch_html(url)
    if not html:
        print("FETCH_FAILED", file=sys.stderr)
        return 2
    content = extract_content(html, url)
    if not content:
        print("EXTRACT_FAILED", file=sys.stderr)
        return 3
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
