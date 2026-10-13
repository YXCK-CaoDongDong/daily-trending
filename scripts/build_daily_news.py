#!/usr/bin/env python3
"""Build daily news JSON: ~30 domestic + ~20 international factual items."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_CONTENT = 20000
MIN_CONTENT = 400
TARGET_DOMESTIC = 30
TARGET_INTL = 20

JUNK_RE = re.compile(
    r"页面没有找到|page not found|404|access denied|请先登录|下载客户端",
    re.I,
)

SUBJECTIVE_RE = re.compile(
    r"天塌了|最惨|荒谬|震惊|炸裂|泪目|破防|绝了|太牛|惊呆|"
    r"明星|八卦|绯闻|离婚|恋情|出轨|综艺|饭圈|热搜第一",
)

ENTERTAINMENT_RE = re.compile(
    r"明星|偶像|选秀|饭圈|八卦|绯闻|恋情|离婚|出轨|"
    r"演唱会门票|粉丝应援|网红打卡",
)


@dataclass
class Candidate:
    title: str
    url: str
    source: str
    region: str
    content: str = ""


def fetch(url: str, timeout: int = 35) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(1.5 * (attempt + 1))
    return None


def strip_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def trim_content(text: str) -> str:
    text = text.strip()
    if len(text) > MAX_CONTENT:
        text = text[:MAX_CONTENT]
    return text


def ok_title(title: str) -> bool:
    t = title.strip()
    if len(t) < 12 or len(t) > 200:
        return False
    if SUBJECTIVE_RE.search(t) or ENTERTAINMENT_RE.search(t):
        return False
    return True


def parse_rss(url: str, source: str, region: str, limit: int = 40) -> list[Candidate]:
    xml = fetch(url)
    if not xml:
        return []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    channel = root.find("channel")
    items = root.findall(".//item") if channel is not None else root.findall(".//{http://www.w3.org/2005/Atom}entry")
    out: list[Candidate] = []
    for item in items:
        title_el = item.find("title")
        link_el = item.find("link")
        if link_el is None:
            link_el = item.find("atom:link", ns)
        title = (title_el.text or "").strip() if title_el is not None else ""
        link = ""
        if link_el is not None:
            link = (link_el.text or link_el.get("href") or "").strip()
        desc_el = item.find("description") or item.find("{http://purl.org/rss/1.0/}description")
        desc = strip_html(desc_el.text or "") if desc_el is not None and desc_el.text else ""
        if not title or not link or not ok_title(title):
            continue
        out.append(Candidate(title=title, url=link, source=source, region=region, content=desc))
        if len(out) >= limit:
            break
    return out


def extract_chinanews(html: str) -> str:
    m = re.search(r'<div class="left_zw"[^>]*>(.*?)</div>\s*<!--正文end', html, re.S)
    if m:
        return trim_content(strip_html(m.group(1)))
    m = re.search(r'<div class="left_zw"[^>]*>(.*?)</div>', html, re.S)
    if m:
        return trim_content(strip_html(m.group(1)))
    m = re.search(r'<div class="content_desc"[^>]*>(.*?)</div>', html, re.S)
    if m:
        return strip_html(m.group(1))
    return ""


def extract_xinhua(html: str) -> str:
    for pat in (
        r'id="detail"[^>]*>(.*?)</div>',
        r'class="article"[^>]*>(.*?)</div>',
        r'<div id="p-detail">(.*?)</div>',
    ):
        m = re.search(pat, html, re.S)
        if m:
            return trim_content(strip_html(m.group(1)))
    return ""


def extract_gov_cn(html: str) -> str:
    m = re.search(r'class="pages_content"[^>]*>(.*?)</div>', html, re.S)
    if m:
        return trim_content(strip_html(m.group(1)))
    return ""


def extract_cctv(html: str) -> str:
    m = re.search(r'class="content_area"[^>]*>(.*?)</div>', html, re.S)
    if m:
        return trim_content(strip_html(m.group(1)))
    m = re.search(r'id="content_area"[^>]*>(.*?)</div>', html, re.S)
    if m:
        return trim_content(strip_html(m.group(1)))
    return ""


def extract_article(url: str, region: str) -> str:
    html = fetch(url)
    if not html or JUNK_RE.search(html[:2000]):
        return ""
    host = re.sub(r"^www\.", "", urllib.parse.urlparse(url).hostname or "")
    if "chinanews.com" in host:
        return trim_content(extract_chinanews(html))
    if "news.cn" in host or "xinhuanet.com" in host:
        return trim_content(extract_xinhua(html))
    if host.endswith("gov.cn"):
        return trim_content(extract_gov_cn(html))
    if "cctv.com" in host:
        return trim_content(extract_cctv(html))
    # international: article body heuristics
    for pat in (
        r'<article[^>]*>(.*?)</article>',
        r'property="article:body"[^>]*content="([^"]+)"',
        r'data-component="text-block"[^>]*>(.*?)</div>',
        r'class="article__body[^"]*"[^>]*>(.*?)</div>',
        r'class="ssrcss-11r1m41-RichTextComponentWrapper[^"]*"[^>]*>(.*?)</div>',
    ):
        m = re.search(pat, html, re.S | re.I)
        if m:
            t = trim_content(strip_html(m.group(1)))
            if len(t) >= MIN_CONTENT:
                return t
    # fallback: largest paragraph block
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.S | re.I)
    chunks = [strip_html(p) for p in paras if len(strip_html(p)) > 40]
    if chunks:
        t = trim_content("\n\n".join(chunks[:12]))
        if len(t) >= MIN_CONTENT:
            return t
    return ""


import urllib.parse  # noqa: E402


def enrich_content(c: Candidate) -> Candidate:
    if c.content and len(c.content) >= MIN_CONTENT and not JUNK_RE.search(c.content):
        c.content = trim_content(c.content)
        return c
    body = extract_article(c.url, c.region)
    if body and not JUNK_RE.search(body):
        c.content = body
    else:
        c.content = ""
    return c


def title_markers(title: str) -> list[str]:
    return [t for t in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}", title) if len(t) >= 2][:6]


def content_matches_title(title: str, content: str) -> bool:
    if not content:
        return True
    markers = title_markers(title)
    if not markers:
        return True
    low = content.casefold()
    return any(m.casefold() in low for m in markers[:3])


def translate_en_to_zh(title: str, content: str) -> tuple[str, str]:
    """Lightweight rule-based placeholder; real translation done in agent pass for intl."""
    return title, content


def collect_domestic() -> list[Candidate]:
    feeds = [
        ("https://www.chinanews.com.cn/rss/china.xml", "中国新闻网"),
        ("https://www.chinanews.com.cn/rss/scroll-news.xml", "中国新闻网"),
        ("https://www.chinanews.com.cn/rss/finance.xml", "中国新闻网"),
        ("https://www.chinanews.com.cn/rss/society.xml", "中国新闻网"),
    ]
    seen: set[str] = set()
    pool: list[Candidate] = []
    for url, src in feeds:
        for c in parse_rss(url, src, "domestic", limit=25):
            key = c.url.split("?")[0]
            if key in seen:
                continue
            seen.add(key)
            pool.append(c)
    # gov.cn headlines from homepage links
    html = fetch("https://www.gov.cn/xinwen/index.htm") or fetch("https://www.gov.cn/")
    if html:
        for m in re.finditer(r'href="(https?://www\.gov\.cn/[^"]+\.htm)"[^>]*>([^<]{15,120})</a>', html):
            link, title = m.group(1), strip_html(m.group(2))
            if ok_title(title) and link not in seen:
                seen.add(link)
                pool.append(Candidate(title=title, url=link, source="中国政府网", region="domestic"))
    return pool


def collect_international() -> list[Candidate]:
    feeds = [
        ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC"),
        ("https://feeds.bbci.co.uk/news/rss.xml", "BBC"),
        ("https://www.theguardian.com/world/rss", "The Guardian"),
        ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "UN News"),
        ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"),
        ("https://rsshub.app/apnews/topics/apf-topnews", "Associated Press"),
    ]
    seen: set[str] = set()
    pool: list[Candidate] = []
    for url, src in feeds:
        for c in parse_rss(url, src, "international", limit=20):
            key = c.url.split("?")[0]
            if key in seen:
                continue
            seen.add(key)
            pool.append(c)
    return pool


def select_and_fill(pool: Iterable[Candidate], target: int, region: str) -> list[Candidate]:
    out: list[Candidate] = []
    for c in pool:
        if c.region != region:
            continue
        if not ok_title(c.title):
            continue
        c = enrich_content(c)
        if c.content and not content_matches_title(c.title, c.content):
            c.content = ""
        out.append(c)
        if len(out) >= target:
            break
        time.sleep(0.3)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--domestic", type=int, default=TARGET_DOMESTIC)
    parser.add_argument("--intl", type=int, default=TARGET_INTL)
    args = parser.parse_args()

    domestic_pool = collect_domestic()
    intl_pool = collect_international()
    print(f"pool domestic={len(domestic_pool)} intl={len(intl_pool)}", file=sys.stderr)

    domestic = select_and_fill(domestic_pool, args.domestic, "domestic")
    international = select_and_fill(intl_pool, args.intl, "international")

    # backfill if short
    if len(domestic) < args.domestic:
        for c in domestic_pool:
            if c in domestic or c.region != "domestic":
                continue
            c = enrich_content(c)
            domestic.append(c)
            if len(domestic) >= args.domestic:
                break
    if len(international) < args.intl:
        for c in intl_pool:
            if c in international:
                continue
            c = enrich_content(c)
            international.append(c)
            if len(international) >= args.intl:
                break

    combined = domestic[: args.domestic] + international[: args.intl]
    items = []
    for i, c in enumerate(combined, start=1):
        items.append(
            {
                "rank_no": i,
                "title": c.title,
                "source": c.source,
                "region": c.region,
                "url": c.url,
                "content": c.content or "",
            }
        )
    Path(args.output).write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    filled = sum(1 for x in items if x["content"])
    print(f"wrote {len(items)} items ({filled} with content) -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
