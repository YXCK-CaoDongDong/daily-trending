#!/usr/bin/env python3
"""Fetch news candidates from domestic and international sources."""

from __future__ import annotations

import json
import re
import sys
import time
from html import unescape
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
TIMEOUT = 20

JUNK_URL = re.compile(
    r"(tophub\.today|weibo\.com|zhihu\.com|baidu\.com|search|/tag/|"
    r"/topic/|login|signup|download|/app$|javascript:)",
    re.I,
)
JUNK_TEXT = re.compile(
    r"页面没有找到|page not found|404|access denied|请先登录|下载客户端|"
    r"Performing security verification|Enable JavaScript",
    re.I,
)


def fetch(url: str) -> str | None:
    try:
        r = SESSION.get(url, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            return None
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception as exc:
        print(f"fetch error {url}: {exc}", file=sys.stderr)
        return None


def clean_text(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_article_text(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    host = (urlparse(url).hostname or "").lower()
    selectors = []
    if "chinanews" in host:
        selectors = [".left_zw", ".content", "article", ".article"]
    elif "news.cn" in host or "xinhuanet" in host:
        selectors = ["#detail", ".article", ".content", "article"]
    elif "thepaper.cn" in host:
        selectors = [".news_txt", ".index_text", "article"]
    elif "people.com.cn" in host:
        selectors = [".rm_txt_con", ".box_con", "article"]
    elif "cctv.com" in host:
        selectors = [".content_area", ".cnt_bd", "article"]
    elif "gov.cn" in host:
        selectors = [".pages_content", ".article", "#UCAP-CONTENT"]
    elif "bbc.com" in host or "bbc.co.uk" in host:
        selectors = ["article", "[data-component='text-block']", ".ssrcss-11r1m41-RichTextComponentWrapper"]
    elif "reuters.com" in host:
        selectors = ["article", "[data-testid='paragraph']"]
    elif "theguardian.com" in host:
        selectors = ["article", ".article-body-commercial-selector"]
    elif "aljazeera.com" in host:
        selectors = ["article", ".wysiwyg", ".article__body"]
    elif "un.org" in host:
        selectors = [".content", "article", ".field-name-body"]
    elif "dw.com" in host:
        selectors = ["article", ".longText"]
    elif "yna.co.kr" in host:
        selectors = ["article", ".story-news"]
    elif "nhk.or.jp" in host:
        selectors = ["article", ".content--detail-body"]
    else:
        selectors = ["article", "main", ".article", ".content", ".post-content"]
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = clean_text(node.get_text(" ", strip=True))
            if len(text) >= 120:
                return text[:20000]
    paras = [clean_text(p.get_text(" ", strip=True)) for p in soup.find_all("p")]
    paras = [p for p in paras if len(p) > 30]
    if paras:
        return clean_text(" ".join(paras))[:20000]
    return ""


def parse_rss(url: str, region: str, source: str, limit: int = 15) -> list[dict]:
    out: list[dict] = []
    try:
        feed = feedparser.parse(url, request_headers=SESSION.headers)
    except Exception as exc:
        print(f"rss error {url}: {exc}", file=sys.stderr)
        return out
    for entry in feed.entries[:limit]:
        link = getattr(entry, "link", "") or ""
        title = clean_text(getattr(entry, "title", "") or "")
        if not link or not title or JUNK_URL.search(link):
            continue
        summary = clean_text(getattr(entry, "summary", "") or "")
        out.append(
            {
                "title": title,
                "url": link,
                "source": source,
                "region": region,
                "summary": summary,
            }
        )
    return out


def parse_tophub(node_id: str, limit: int = 30) -> list[dict]:
    url = f"https://tophub.today/n/{node_id}"
    html = fetch(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    for a in soup.select("table tbody tr td a"):
        href = a.get("href", "")
        title = clean_text(a.get_text())
        if not title or len(title) < 6:
            continue
        if href.startswith("/"):
            href = urljoin("https://tophub.today", href)
        if JUNK_URL.search(href):
            continue
        out.append({"title": title, "url": href, "source": "tophub", "region": "domestic"})
        if len(out) >= limit:
            break
    return out


def search_chinanews(keyword: str) -> str | None:
    q = requests.utils.quote(keyword[:20])
    search_url = f"https://sou.chinanews.com.cn/search.do?q={q}"
    html = fetch(search_url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    for a in soup.select("a"):
        href = a.get("href", "")
        if "/cns/" in href or "/shipin/" in href:
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = "https://www.chinanews.com.cn" + href
            return href
    return None


def enrich_with_content(items: list[dict]) -> list[dict]:
    enriched = []
    for item in items:
        url = item.get("url") or ""
        if not url or JUNK_URL.search(url):
            item["content"] = ""
            enriched.append(item)
            continue
        html = fetch(url)
        if not html or JUNK_TEXT.search(html[:3000]):
            item["content"] = ""
            enriched.append(item)
            time.sleep(0.3)
            continue
        content = extract_article_text(html, url)
        if JUNK_TEXT.search(content) or len(content) < 80:
            item["content"] = ""
        else:
            item["content"] = content[:20000]
        enriched.append(item)
        time.sleep(0.3)
    return enriched


def main() -> int:
    domestic: list[dict] = []
    international: list[dict] = []

    # Domestic RSS / listings
    domestic.extend(parse_rss("https://www.chinanews.com.cn/rss/scroll-news.xml", "domestic", "中国新闻网", 20))
    domestic.extend(parse_rss("https://www.chinanews.com.cn/rss/importnews.xml", "domestic", "中国新闻网", 15))

    for node in ["wWmoO5Rd4E", "Q0or6qzo8B", "3adqZlMeng", "KqndgxeLl9", "Q1Vd5Ko85R"]:
        domestic.extend(parse_tophub(node, 15))

    # International RSS / listings
    international.extend(parse_rss("https://feeds.bbci.co.uk/news/world/rss.xml", "international", "BBC", 15))
    international.extend(parse_rss("https://feeds.bbci.co.uk/news/rss.xml", "international", "BBC", 10))
    international.extend(parse_rss("https://www.theguardian.com/world/rss", "international", "The Guardian", 12))
    international.extend(parse_rss("https://www.aljazeera.com/xml/rss/all.xml", "international", "Al Jazeera", 12))
    international.extend(parse_rss("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "international", "联合国", 10))
    international.extend(parse_rss("https://www.dw.com/en/rss/rss-top/rss.xml", "international", "德国之声", 10))

    # Dedupe by URL
    seen = set()
    domestic = [x for x in domestic if not (x["url"] in seen or seen.add(x["url"]))]
    seen.clear()
    international = [x for x in international if not (x["url"] in seen or seen.add(x["url"]))]

    print(f"domestic candidates: {len(domestic)}", file=sys.stderr)
    print(f"international candidates: {len(international)}", file=sys.stderr)

    payload = {"domestic": domestic[:40], "international": international[:30]}
    out_path = "/workspace/data/candidates.json"
    import os

    os.makedirs("/workspace/data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
