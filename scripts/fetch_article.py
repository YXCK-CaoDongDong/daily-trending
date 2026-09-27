#!/usr/bin/env python3
"""Fetch and extract article text from news URLs."""

from __future__ import annotations

import re
import sys
from html import unescape
from urllib.request import Request, urlopen

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch(url: str, timeout: int = 25) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")


def strip_html(html: str) -> str:
    html = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    text = unescape(html)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_chinanews(html: str) -> str:
    m = re.search(r'<div class="left_zw">([\s\S]*?)</div>', html)
    if m:
        return strip_html(m.group(1))
    m = re.search(r'<div class="content_maincontent_content">([\s\S]*?)</div>', html)
    if m:
        return strip_html(m.group(1))
    return ""


def extract_thepaper(html: str) -> str:
    m = re.search(r'"content":"((?:\\.|[^"\\])*)"', html)
    if m:
        import json
        try:
            return json.loads('"' + m.group(1) + '"')
        except json.JSONDecodeError:
            pass
    for pat in (r'<div class="index_cententWrap__Jv8jK">([\s\S]*?)</div>',
                r'<article[^>]*>([\s\S]*?)</article>'):
        m = re.search(pat, html)
        if m:
            return strip_html(m.group(1))
    return ""


def extract_bbc(html: str) -> str:
    parts = re.findall(r'"text":"((?:\\.|[^"\\])*)"', html)
    paras = []
    for p in parts:
        import json
        try:
            paras.append(json.loads('"' + p + '"'))
        except json.JSONDecodeError:
            continue
    return "\n\n".join(paras)


def extract_guardian(html: str) -> str:
    parts = re.findall(r'<p class="[^"]*article-body[^"]*">([\s\S]*?)</p>', html)
    if parts:
        return "\n\n".join(strip_html(p) for p in parts if len(strip_html(p)) > 20)
    return extract_bbc(html) or strip_html(html)[:3000]


def extract_aljazeera(html: str) -> str:
    parts = re.findall(r'<p[^>]*>([\s\S]*?)</p>', html)
    paras = [strip_html(p) for p in parts if len(strip_html(p)) > 40]
    return "\n\n".join(paras[:30])


def extract_un(html: str) -> str:
    m = re.search(r'<div class="content">([\s\S]*?)</div>', html)
    if m:
        return strip_html(m.group(1))
    parts = re.findall(r'<p[^>]*>([\s\S]*?)</p>', html)
    paras = [strip_html(p) for p in parts if len(strip_html(p)) > 40]
    return "\n\n".join(paras[:25])


def extract_yna(html: str) -> str:
    m = re.search(r'<article[^>]*id="article-body"[^>]*>([\s\S]*?)</article>', html)
    if m:
        return strip_html(m.group(1))
    parts = re.findall(r'<p[^>]*class="[^"]*story-news[^"]*"[^>]*>([\s\S]*?)</p>', html)
    if parts:
        return "\n\n".join(strip_html(p) for p in parts)
    return ""


def extract_generic(html: str) -> str:
    for host_fn in (extract_chinanews, extract_thepaper, extract_bbc,
                    extract_guardian, extract_aljazeera, extract_un, extract_yna):
        text = host_fn(html)
        if len(text) > 200:
            return text
    return strip_html(html)[:5000]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_article.py <url>", file=sys.stderr)
        return 1
    url = sys.argv[1]
    html = fetch(url)
    text = extract_generic(html)
    if len(text) > 20000:
        text = text[:20000]
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
