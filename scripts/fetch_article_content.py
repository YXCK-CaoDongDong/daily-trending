#!/usr/bin/env python3
"""Fetch article text from URLs (stdlib only). Used by daily cron."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from typing import Any

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
JUNK = re.compile(
    r"页面没有找到|Page not found|404|access denied|请先登录|下载客户端",
    re.I,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self._depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True
            self._depth += 1
        elif tag in ("p", "br", "div", "h1", "h2", "h3", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._depth -= 1
            if self._depth <= 0:
                self._skip = False
                self._depth = 0

    def handle_data(self, data: str) -> None:
        if not self._skip:
            t = data.strip()
            if t:
                self.parts.append(t)


def fetch_url(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def extract_chinanews(html: str) -> str:
    m = re.search(
        r'<div[^>]*class="[^"]*left_zw[^"]*"[^>]*>(.*?)</div>\s*<div',
        html,
        re.S | re.I,
    )
    if m:
        block = m.group(1)
        p = _TextExtractor()
        p.feed(block)
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(p.parts))
        return re.sub(r"[ \t]+", " ", text).strip()
    # fallback: all paragraphs in content area
    p = _TextExtractor()
    p.feed(html)
    text = "\n".join(p.parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def extract_generic(html: str) -> str:
    # BBC article body
    for pat in (
        r'<article[^>]*>(.*?)</article>',
        r'data-component="text-block"[^>]*>(.*?)</',
        r'<div[^>]*class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>',
    ):
        m = re.search(pat, html, re.S | re.I)
        if m:
            p = _TextExtractor()
            p.feed(m.group(1))
            text = re.sub(r"\n{3,}", "\n\n", "\n".join(p.parts))
            return re.sub(r"[ \t]+", " ", text).strip()
    p = _TextExtractor()
    p.feed(html)
    text = "\n".join(p.parts)
    return re.sub(r"\s+", " ", text).strip()


def extract_content(url: str, html: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if "chinanews" in host or "news.cn" in host:
        return extract_chinanews(html)
    return extract_generic(html)


import urllib.parse  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fetch_article_content.py <url> [url ...]", file=sys.stderr)
        return 1
    out: list[dict[str, Any]] = []
    for url in sys.argv[1:]:
        try:
            html = fetch_url(url)
            content = extract_content(url, html)
            if JUNK.search(content[:500]):
                content = ""
            if len(content) > 20000:
                content = content[:20000]
            out.append({"url": url, "content": content, "len": len(content)})
        except Exception as exc:  # noqa: BLE001
            out.append({"url": url, "content": "", "error": str(exc)})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
