#!/usr/bin/env python3
"""Fetch and extract article text from news URLs."""

from __future__ import annotations

import json
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

JUNK_RE = re.compile(
    r"页面没有找到|将会带您进入新浪首页|page not found|"
    r"sorry,\s*we can't find the page|404 not found|access denied|"
    r"下载客户端|请先登录|登录后查看|找不到该页面",
    re.I,
)

NOISE_PATTERNS = [
    re.compile(r"^(来源|责任编辑|分享|打印|字体|阅读下一篇|相关阅读|延伸阅读|"
               r"Copyright|Skip to|Site search|Most read|Also in news|"
               r"【责任编辑|阅读下一篇|新华网>)", re.I),
]


def fetch_html(url: str, timeout: int = 25) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return None
        resp.encoding = resp.apparent_encoding or "utf-8"
        text = resp.text
        if JUNK_RE.search(text[:3000]):
            return None
        final = resp.url.lower()
        if "sina.com.cn" in final and "404" in text[:5000].lower():
            return None
        return text
    except requests.RequestException:
        return None


def _clean_lines(lines: list[str]) -> str:
    out: list[str] = []
    for line in lines:
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 8:
            continue
        if any(p.search(line) for p in NOISE_PATTERNS):
            continue
        if line in {"小", "中", "大", "正文"}:
            continue
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _node_text(node) -> str:
    paras = [p.get_text(" ", strip=True) for p in node.find_all("p")]
    if paras:
        return _clean_lines(paras)
    return _clean_lines([node.get_text(" ", strip=True)])


def extract_chinanews(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for sel in ["div.left_zw", "div.content_maincontent_content", "div.content", "article"]:
        node = soup.select_one(sel)
        if node:
            text = _node_text(node)
            if len(text) >= 40:
                return text
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return _clean_lines(paras)


def extract_xinhua(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for sel in ["span#detailContent", "div#detail", "div.article", "article"]:
        node = soup.select_one(sel)
        if node:
            text = _node_text(node)
            if len(text) >= 40:
                return text
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return _clean_lines(paras)


def extract_thepaper(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    node = soup.select_one("div.index_centent, div.news_txt, article")
    if node:
        paras = [p.get_text(" ", strip=True) for p in node.find_all("p")]
        text = _clean_lines(paras)
        if len(text) >= 80:
            return text
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return _clean_lines(paras)


def extract_bbc(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    node = soup.select_one("article") or soup.select_one("main")
    if not node:
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        return _clean_lines(paras)
    paras = [p.get_text(" ", strip=True) for p in node.find_all("p")]
    return _clean_lines(paras)


def extract_ap(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    node = soup.select_one("div.RichTextStoryBody") or soup.select_one("article")
    if node:
        paras = [p.get_text(" ", strip=True) for p in node.find_all("p")]
        text = _clean_lines(paras)
        if len(text) >= 80:
            return text
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return _clean_lines(paras)


def extract_generic(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    article = soup.find("article")
    if article:
        paras = [p.get_text(" ", strip=True) for p in article.find_all("p")]
        text = _clean_lines(paras)
        if len(text) >= 80:
            return text
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return _clean_lines(paras)


def extract_content(html: str, url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "chinanews.com" in host:
        return extract_chinanews(html)
    if "news.cn" in host or "xinhuanet.com" in host:
        return extract_xinhua(html)
    if "thepaper.cn" in host:
        return extract_thepaper(html)
    if "bbc.com" in host or "bbc.co.uk" in host:
        return extract_bbc(html)
    if "apnews.com" in host:
        return extract_ap(html)
    if "ce.cn" in host:
        return extract_generic(html)
    return extract_generic(html)


def fetch_article(url: str) -> dict:
    html = fetch_html(url)
    if not html:
        return {"url": url, "content": "", "ok": False}
    content = extract_content(html, url)
    min_len = 40 if any(h in urlparse(url).netloc for h in ("chinanews.com", "news.cn", "xinhuanet.com")) else 80
    if JUNK_RE.search(content) or len(content) < min_len:
        return {"url": url, "content": "", "ok": False}
    if len(content) > 20000:
        content = content[:20000]
    return {"url": url, "content": content, "ok": True, "length": len(content)}


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else ""
    if not url:
        print("usage: fetch_article.py <url>", file=sys.stderr)
        return 1
    result = fetch_article(url)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
