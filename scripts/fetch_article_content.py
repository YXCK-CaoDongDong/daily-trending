#!/usr/bin/env python3
"""Fetch article text from a news URL (stdlib only)."""

from __future__ import annotations

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from urllib.request import Request, urlopen

MAX_LEN = 20000
TIMEOUT = 25


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._chunks: list[str] = []
        self.SKIP_TAGS = frozenset(
            {"script", "style", "noscript", "nav", "header", "footer", "aside"}
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip:
            self._skip -= 1
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3", "article") and not self._skip:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        t = data.strip()
        if t:
            self._chunks.append(t + " ")

    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = html.unescape(raw)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def fetch_url(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; daily-trending-bot/1.0; +https://github.com/)"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
    charset = "utf-8"
    m = re.search(rb"charset=['\"]?([\w-]+)", data[:4096], re.I)
    if m:
        charset = m.group(1).decode("ascii", "ignore")
    try:
        return data.decode(charset, errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def extract_main(html_text: str) -> str:
    # chinanews
    m = re.search(
        r'<div class="left_zw">(.*?)</div>\s*<!--.*?left_zw',
        html_text,
        re.DOTALL | re.I,
    )
    if m:
        return TextExtractor().unescape_and_parse(m.group(1))
    m = re.search(r'<div class="left_zw">(.*?)</div>', html_text, re.DOTALL | re.I)
    if m:
        return TextExtractor().unescape_and_parse(m.group(1))
    # news.cn
    m = re.search(r'id="detail"[^>]*>(.*?)</div>', html_text, re.DOTALL | re.I)
    if m:
        return TextExtractor().unescape_and_parse(m.group(1))
    # generic article / main
    m = re.search(
        r"field--name-field-text-column.*?field__item[^>]*>(.*?)</div>",
        html_text,
        re.DOTALL | re.I,
    )
    if m and len(m.group(1)) > 100:
        return TextExtractor().unescape_and_parse(m.group(1))
    for pat in (
        r'<article[^>]*>(.*?)</article>',
        r'role="main"[^>]*>(.*?)</div>',
        r'class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>',
        r'class="[^"]*story-body[^"]*"[^>]*>(.*?)</div>',
        r'data-component="text-block"[^>]*>(.*?)</div>',
        r'id="maincontent"[^>]*>(.*?)</div>',
    ):
        m = re.search(pat, html_text, re.DOTALL | re.I)
        if m and len(m.group(1)) > 200:
            return TextExtractor().unescape_and_parse(m.group(1))
    p = TextExtractor()
    p.feed(html_text)
    return p.text()


def unescape_and_parse(self: TextExtractor, fragment: str) -> str:
    p = TextExtractor()
    p.feed(fragment)
    return p.text()


TextExtractor.unescape_and_parse = unescape_and_parse  # type: ignore[method-assign]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--max", type=int, default=MAX_LEN)
    args = parser.parse_args()
    try:
        html_text = fetch_url(args.url)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    junk = re.search(
        r"page not found|404 not found|页面没有找到|找不到该页面",
        html_text[:5000],
        re.I,
    )
    if junk:
        print("ERROR: page not found", file=sys.stderr)
        return 1
    text = extract_main(html_text)
    if len(text) > args.max:
        text = text[: args.max]
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
