#!/usr/bin/env python3
"""Fetch and extract article text from news URLs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
TIMEOUT = 25
MAX_LEN = 20000
MIN_LEN = 80

JUNK_RE = re.compile(
    r"页面没有找到|将会带您进入新浪首页|page not found|404 not found|"
    r"access denied|403 forbidden|请先登录|登录后查看|找不到该页面",
    re.I,
)

NOISE_PATTERNS = [
    r"^分享到",
    r"^责任编辑",
    r"^来源[:：]",
    r"^原标题[:：]",
    r"^相关阅读",
    r"^推荐阅读",
    r"^点击收听",
    r"^扫码",
    r"^Copyright",
    r"^©",
    r"^更多",
    r"^上一篇",
    r"^下一篇",
    r"^返回首页",
    r"^下载客户端",
    r"^无障碍",
    r"^账号设置",
    r"^退出登录",
    r"^新华社北京",
    r"^人民日报",
    r"^央视网消息",
    r"^中新网",
    r"^编辑[:：]",
    r"^责编[:：]",
    r"^图/",
    r"^视频/",
    r"^\[",
    r"^【视频】",
    r"^【图片】",
]


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _clean_lines(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) < 4:
            continue
        if any(re.match(p, line) for p in NOISE_PATTERNS):
            continue
        if JUNK_RE.search(line):
            continue
        lines.append(line)
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def extract(soup: BeautifulSoup, url: str) -> str:
    host = _domain(url)

    selectors: list[str] = []
    if "news.cn" in host or "xinhuanet.com" in host:
        selectors = ["div#detail", "div.article", "span#detailContent", "div.main-article"]
    elif "people.com.cn" in host:
        selectors = ["div.box_con", "div.rmh_detail", "div.article"]
    elif "chinanews.com.cn" in host:
        selectors = ["div.left_zw", "div.content_maincontent_content"]
    elif "thepaper.cn" in host:
        selectors = ["div.news_txt", "div.index_cententWrap__Jv8P9"]
    elif "cctv.com" in host:
        selectors = ["div.content_area", "div.cnt_bd"]
    elif "gov.cn" in host:
        selectors = ["div.pages_content", "div.trs_editor_view"]
    elif "fmprc.gov.cn" in host:
        selectors = ["div.news-main", "div#News_Body_Txt_A"]
    elif "bbc.com" in host or "bbc.co.uk" in host:
        selectors = ["article", "div[data-component='text-block']"]
    elif "reuters.com" in host:
        selectors = ["div[data-testid='ArticleBody']", "article"]
    elif "apnews.com" in host:
        selectors = ["div.RichTextStoryBody", "article"]
    elif "theguardian.com" in host:
        selectors = ["div.article-body-commercial-selector", "article"]
    elif "huanqiu.com" in host:
        selectors = ["div.l-container", "div.article"]
    elif "caixin.com" in host:
        selectors = ["div#Main_Content_Val", "div.text"]
    elif "jiemian.com" in host:
        selectors = ["div.article-content", "article"]
    elif "stdaily.com" in host:
        selectors = ["div.content", "div.article"]
    elif "gmw.cn" in host:
        selectors = ["div.u-mainText", "div.content"]
    elif "chinadaily.com.cn" in host:
        selectors = ["div#Content", "div.article"]
    elif "nytimes.com" in host:
        selectors = ["section[name='articleBody']", "article"]
    elif "dw.com" in host:
        selectors = ["div.rich-text", "article"]
    elif "aljazeera.com" in host:
        selectors = ["div.wysiwyg", "article"]
    elif "scmp.com" in host:
        selectors = ["div.article-body", "article"]
    elif "ithome.com" in host:
        selectors = ["div.post_content", "div#paragraph"]
    else:
        selectors = ["article", "div.article", "div.content", "main"]

    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = _clean_lines(node.get_text("\n", strip=True))
            if len(text) >= MIN_LEN:
                return text[:MAX_LEN]

    for tag in soup.find_all(["p", "div"]):
        cls = " ".join(tag.get("class") or [])
        if any(k in cls for k in ("nav", "footer", "header", "comment", "related", "sidebar")):
            continue
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
    text = _clean_lines("\n".join(paras))
    return text[:MAX_LEN] if text else ""


def fetch(url: str) -> dict:
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or "utf-8"
        if _domain(url).endswith("chinanews.com.cn") and "charset=gb2312" in resp.text[:2000].lower():
            resp.encoding = "gb2312"
        if resp.status_code >= 400:
            return {"url": url, "ok": False, "error": f"HTTP {resp.status_code}", "content": ""}
        soup = BeautifulSoup(resp.text, "lxml")
        title = (soup.title.string or "").strip() if soup.title else ""
        content = extract(soup, url)
        if JUNK_RE.search(content) or len(content) < MIN_LEN:
            return {"url": url, "ok": False, "error": "junk or too short", "title": title, "content": ""}
        return {"url": url, "ok": True, "title": title, "content": content, "length": len(content)}
    except Exception as exc:
        return {"url": url, "ok": False, "error": str(exc), "content": ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", help="article URL")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    if not args.url:
        parser.error("url required")
    result = fetch(args.url)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result.get("content", ""))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
