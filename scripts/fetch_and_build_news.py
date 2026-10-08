#!/usr/bin/env python3
"""Collect ~50 news items and fetch article bodies for daily ingest."""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass
from html import unescape

import requests
import trafilatura
from bs4 import BeautifulSoup

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None  # type: ignore

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
)
BAD_URL = re.compile(
    r"(baidu\.com/s\?|s\.weibo\.com|zhihu\.com|tophub\.today|"
    r"javascript:|\+ item\.|\+ v\.)",
    re.I,
)
COMMENT_TITLE = re.compile(r"马上评|旁白｜|奔赴“县”场｜|深度｜|社论")
JUNK_TITLE = re.compile(
    r"明星|八卦|恋爱|有孩子|憨态|打卡|小狗|吴奇隆|李现从歌迷|精致小狗|"
    r"苏轼墓前|超like|Walking a Trump|tightrope|Watch:",
    re.I,
)
INTL_OPINION = re.compile(
    r"tightrope|explainer|What we know|Watch:|opinion|analysis",
    re.I,
)


@dataclass
class Candidate:
    title: str
    url: str
    source: str
    region: str


def get_html(url: str, timeout: int = 25) -> str | None:
    try:
        r = SESSION.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400:
            return None
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except requests.RequestException:
        return None


def fetch_article_text(url: str, title: str) -> str | None:
    downloaded = trafilatura.fetch_url(url, no_ssl=True)
    if not downloaded:
        downloaded = get_html(url)
        if not downloaded:
            return None
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not text or len(text) < 80:
        return None
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    markers = [t for t in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}", title) if len(t) > 1][:6]
    if markers:
        hit = sum(1 for m in markers if m.casefold() in text.casefold())
        if hit < max(1, len(markers) // 3):
            return None
    if len(text) > 20000:
        text = text[:20000]
    return text


def parse_tophub(node_id: str, source_name: str, region: str = "domestic") -> list[Candidate]:
    html = get_html(f"https://tophub.today/n/{node_id}")
    if not html:
        return []
    out: list[Candidate] = []
    for m in re.finditer(
        r'<a href="(https?://[^"]+)"[^>]*>([^<]+)</a>',
        html,
    ):
        link, title = m.group(1), unescape(m.group(2).strip())
        if BAD_URL.search(link) or BAD_URL.search(title):
            continue
        if len(title) < 8 or COMMENT_TITLE.search(title) or JUNK_TITLE.search(title):
            continue
        out.append(Candidate(title, link, source_name, region))
    return out


def parse_chinanews_scroll() -> list[Candidate]:
    html = get_html("https://www.chinanews.com.cn/scroll-news/news1.html")
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out: list[Candidate] = []
    for li in soup.select("div.content_list li, .dd_bt a, li a"):
        a = li if li.name == "a" else li.find("a")
        if not a:
            continue
        href = a.get("href") or ""
        title = (a.get_text() or "").strip()
        if not re.search(r"2026/10-0[78]", href):
            continue
        if "shipin" in href or "/tp/hd" in href:
            continue
        if len(title) < 10 or COMMENT_TITLE.search(title) or JUNK_TITLE.search(title):
            continue
        if href.startswith("/"):
            href = "https://www.chinanews.com.cn" + href
        out.append(Candidate(title, href, "中国新闻网", "domestic"))
    return out


def parse_rss(url: str, source: str) -> list[Candidate]:
    html = get_html(url)
    if not html:
        return []
    out: list[Candidate] = []
    for m in re.finditer(
        r"<item>.*?<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>.*?<link>(.*?)</link>",
        html,
        re.S,
    ):
        title = unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip())
        link = m.group(2).strip()
        if len(title) < 12 or JUNK_TITLE.search(title) or INTL_OPINION.search(title):
            continue
        if "/videos/" in link:
            continue
        out.append(Candidate(title, link, source, "international"))
    return out


def translate_zh(text: str, max_chunk: int = 4500) -> str:
    if not text or GoogleTranslator is None:
        return text
    if re.search(r"[\u4e00-\u9fff]", text[:200]):
        return text
    tr = GoogleTranslator(source="auto", target="zh-CN")
    parts: list[str] = []
    for i in range(0, len(text), max_chunk):
        chunk = text[i : i + max_chunk]
        try:
            parts.append(tr.translate(chunk))
        except Exception:
            parts.append(chunk)
        time.sleep(0.15)
    return "".join(parts)


def dedupe(cands: list[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    out: list[Candidate] = []
    for c in cands:
        key = re.sub(r"\W+", "", c.title)[:36].casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def collect_candidates() -> tuple[list[Candidate], list[Candidate]]:
    domestic: list[Candidate] = []
    for node, name in [
        ("wWmoO5Rd4E", "澎湃新闻"),
        ("Q0or6qzo8B", "中国政府网"),
        ("74Kvx59dkx", "IT之家"),
        ("3adqZlMeng", "外交部"),
        ("YKd6JOqdaP", "国家统计局"),
        ("7GdabXpeQy", "中国地震局"),
        ("1Vd5PbMv85", "中国互联网联合辟谣平台"),
    ]:
        domestic.extend(parse_tophub(node, name))
        time.sleep(0.25)
    domestic.extend(parse_chinanews_scroll())

    # Weibo clues -> skip; use chinanews for hot topics already

    international: list[Candidate] = []
    for feed, name in [
        ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC News"),
        ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "UN News"),
        ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"),
        ("https://english.kyodonews.net/rss/news.xml", "Kyodo News"),
        ("https://en.yna.co.kr/rss/industry.xml", "Yonhap News"),
    ]:
        international.extend(parse_rss(feed, name))
        time.sleep(0.2)

    for page, name, pattern in [
        ("https://www.reuters.com/world/", "Reuters", r"reuters\.com/world/"),
        ("https://apnews.com/hub/ap-top-news", "Associated Press", r"apnews\.com/article/"),
    ]:
        html = get_html(page)
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        for a in soup.select("a[href]"):
            href = urllib.parse.urljoin(page, a.get("href") or "")
            title = (a.get_text() or "").strip()
            if len(title) < 18 or not re.search(pattern, href):
                continue
            if JUNK_TITLE.search(title) or INTL_OPINION.search(title):
                continue
            international.append(Candidate(title, href, name, "international"))

    domestic = dedupe(domestic)
    international = dedupe(international)
    return domestic, international


def main() -> int:
    domestic, international = collect_candidates()
    picked = domestic[:30] + international[:20]
    items: list[dict] = []
    for i, c in enumerate(picked, start=1):
        body = fetch_article_text(c.url, c.title)
        title = c.title
        content = body or ""
        if c.region == "international":
            title = translate_zh(title)
            if content:
                content = translate_zh(content)
        items.append(
            {
                "rank_no": i,
                "title": title,
                "source": c.source,
                "region": c.region,
                "url": c.url,
                "content": content,
            }
        )
        time.sleep(0.35)

    out = sys.argv[1] if len(sys.argv) > 1 else "/workspace/data/daily_news.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    filled = sum(1 for x in items if x.get("content"))
    print(f"wrote {len(items)} items ({filled} with content) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
