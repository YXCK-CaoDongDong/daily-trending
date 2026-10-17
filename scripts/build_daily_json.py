#!/usr/bin/env python3
"""Build daily news JSON: ~30 domestic + ~20 international from SKILL sources."""

from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

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

JUNK_TITLE_RE = re.compile(
    r"天塌了|最惨|荒谬|震惊|泪目|破防|绝了|吃瓜|八卦|明星离婚|恋情曝光|"
    r"广告|推广|优惠券|下载客户端|免费领取",
    re.I,
)
JUNK_URL_PARTS = (
    "tophub.today",
    "weibo.com",
    "zhihu.com/question",
    "baidu.com/s?",
    "/search?",
    "login",
    "signin",
)
JUNK_CONTENT_RE = re.compile(
    r"页面没有找到|Page not found|404|can't find the page|"
    r"下载客户端|请先登录|access denied",
    re.I,
)

TOPHUB_PATHS = [
    "/n/KqndgxeLl9",  # 微博
    "/n/mproPpoq6O",  # 知乎
    "/n/Jb0vmloB1G",  # 百度
    "/n/x9ozB4KoXb",  # 头条
    "/n/74Kvx59dkx",  # IT之家
    "/n/Q0or6qzo8B",  # 政府网头条
    "/n/3adqZlMeng",  # 外交部
    "/n/YKd6JOqdaP",  # 统计局
    "/n/7GdabXpeQy",  # 地震局
    "/n/1Vd5PbMv85",  # 辟谣
]

INTL_RSS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("Associated Press", "https://rsshub.app/apnews/topics/apf-topnews"),
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("NHK World", "https://www3.nhk.or.jp/rss/news/nhkworld/english.xml"),
    ("Yonhap News", "https://www.yna.co.kr/rss/english.xml"),
    ("Deutsche Welle", "https://rss.dw.com/rdf/rss-en-all"),
]

DOMESTIC_RSS = [
    ("中国新闻网", "https://www.chinanews.com.cn/rss/scroll-news.xml"),
    ("新华网", "https://www.news.cn/rss/world.xml"),
]

GOV_HOSTS = ("gov.cn", "news.cn", "people.com.cn", "cctv.com", "chinanews.com.cn")


@dataclass
class Candidate:
    title: str
    source: str
    url: str
    region: str
    content: str = ""


def fetch_html(url: str, timeout: int = 25) -> str | None:
    try:
        r = SESSION.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400:
            return None
        ct = r.headers.get("content-type", "")
        if "text" not in ct and "html" not in ct and "xml" not in ct:
            return None
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except requests.RequestException:
        return None


def fetch_rss(source: str, url: str, limit: int = 40) -> list[Candidate]:
    text = fetch_html(url)
    if not text:
        return []
    items: list[Candidate] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    for item in root.findall(".//item")[:limit]:
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        if title_el is None or link_el is None:
            continue
        title = unescape((title_el.text or "").strip())
        link = (link_el.text or "").strip()
        if not title or not link:
            continue
        desc = unescape((desc_el.text or "") if desc_el is not None else "")
        desc = BeautifulSoup(desc, "html.parser").get_text(" ", strip=True)
        host = urlparse(link).hostname or ""
        region = "international"
        if host.endswith(".cn") or any(h in host for h in GOV_HOSTS):
            region = "domestic"
        items.append(Candidate(title=title, source=source, url=link, region=region, content=desc))
    return items


def parse_tophub(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[tuple[str, str]] = []
    for a in soup.select("table tbody tr td a[href]"):
        href = a.get("href", "").strip()
        title = a.get_text(strip=True)
        if not title or len(title) < 6:
            continue
        if href.startswith("/"):
            href = urljoin("https://tophub.today", href)
        if "tophub.today" in href and "/n/" in href:
            continue
        out.append((title, href))
    return out


def resolve_article_url(title: str, url: str) -> str | None:
    if any(p in url for p in JUNK_URL_PARTS):
        return None
    if url.startswith("http"):
        return url
    return None


def extract_chinanews_content(html: str) -> str | None:
    start = html.find("<!--正文start-->")
    end = html.find("<!--正文end-->")
    if start != -1 and end != -1 and end > start:
        chunk = html[start:end]
        text = BeautifulSoup(chunk, "html.parser").get_text("\n", strip=True)
        return clean_text(text)
    soup = BeautifulSoup(html, "html.parser")
    for sel in ("div.left_zw", "div.content", "article"):
        node = soup.select_one(sel)
        if node:
            text = node.get_text("\n", strip=True)
            if len(text) > 100:
                return clean_text(text)
    return None


def extract_gov_content(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for sel in (".pages_content", ".article-content", "#UCAP-CONTENT", ".content"):
        node = soup.select_one(sel)
        if node:
            text = node.get_text("\n", strip=True)
            if len(text) > 80:
                return clean_text(text)
    return None


def extract_generic_content(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    for sel in (
        "article",
        "[data-component='text-block']",
        ".story-body",
        ".article-body",
        ".content__article-body",
        ".Article__content",
        "main",
    ):
        node = soup.select_one(sel)
        if node:
            text = node.get_text("\n", strip=True)
            if len(text) > 120:
                return clean_text(text)
    paras = [p.get_text(strip=True) for p in soup.find_all("p")]
    paras = [p for p in paras if len(p) > 40]
    if len(paras) >= 3:
        return clean_text("\n".join(paras[:30]))
    return None


def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def fetch_article_content(url: str, title: str) -> str:
    html = fetch_html(url)
    if not html or JUNK_CONTENT_RE.search(html[:5000]):
        return ""
    host = urlparse(url).hostname or ""
    body: str | None = None
    if "chinanews.com.cn" in host:
        body = extract_chinanews_content(html)
    elif host.endswith("gov.cn"):
        body = extract_gov_content(html)
    else:
        body = extract_generic_content(html)
    if not body or len(body) < 80:
        return ""
    if JUNK_CONTENT_RE.search(body):
        return ""
    markers = [t for t in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}", title) if len(t) >= 2][:8]
    if markers:
        hit = sum(1 for m in markers if m.casefold() in body.casefold())
        if hit < max(1, len(markers) // 4):
            return ""
    if len(body) > 20000:
        body = body[:20000]
    return body


def translate_text(text: str, max_chunk: int = 4500) -> str:
    if not text:
        return ""
    if re.search(r"[\u4e00-\u9fff]", text) and len(re.findall(r"[\u4e00-\u9fff]", text)) > len(text) * 0.3:
        return text
    out_parts: list[str] = []
    chunks = [text[i : i + max_chunk] for i in range(0, len(text), max_chunk)]
    for chunk in chunks:
        try:
            r = SESSION.get(
                "https://api.mymemory.translated.net/get",
                params={"q": chunk, "langpair": "en|zh-CN"},
                timeout=30,
            )
            data = r.json()
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated:
                out_parts.append(translated)
            else:
                out_parts.append(chunk)
        except Exception:
            out_parts.append(chunk)
        time.sleep(0.3)
    return "".join(out_parts)


def title_ok(title: str) -> bool:
    if len(title) < 8 or len(title) > 200:
        return False
    if JUNK_TITLE_RE.search(title):
        return False
    return True


def url_ok(url: str) -> bool:
    if not url.startswith("http"):
        return False
    if any(p in url.lower() for p in JUNK_URL_PARTS):
        return False
    return True


def pick_unique(cands: list[Candidate], n: int, seen_urls: set[str], seen_titles: set[str]) -> list[Candidate]:
    picked: list[Candidate] = []
    for c in cands:
        key = c.url.split("?")[0]
        tkey = c.title[:40]
        if key in seen_urls or tkey in seen_titles:
            continue
        if not title_ok(c.title) or not url_ok(c.url):
            continue
        picked.append(c)
        seen_urls.add(key)
        seen_titles.add(tkey)
        if len(picked) >= n:
            break
    return picked


def enrich_tophub_domestic(limit: int = 35) -> list[Candidate]:
    out: list[Candidate] = []
    for path in TOPHUB_PATHS:
        html = fetch_html(f"https://tophub.today{path}")
        if not html:
            continue
        for title, link in parse_tophub(html)[:25]:
            if JUNK_TITLE_RE.search(title):
                continue
            art = resolve_article_url(title, link)
            if not art:
                continue
            host = urlparse(art).hostname or ""
            if not (host.endswith(".cn") or any(x in host for x in ("sina", "163", "qq", "sohu", "thepaper", "gmw", "cctv"))):
                continue
            out.append(Candidate(title=title, source=host, url=art, region="domestic"))
        time.sleep(0.2)
    return out[:limit]


def main() -> int:
    run_date = datetime.now(TZ).date()
    out_path = DATA_DIR / f"daily_news_{run_date.isoformat()}.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    domestic: list[Candidate] = []
    international: list[Candidate] = []

    for source, rss in DOMESTIC_RSS:
        domestic.extend(fetch_rss(source, rss, 35))
        time.sleep(0.2)
    domestic.extend(enrich_tophub_domestic(40))

    for source, rss in INTL_RSS:
        for c in fetch_rss(source, rss, 25):
            host = urlparse(c.url).hostname or ""
            if host.endswith(".cn"):
                continue
            c.region = "international"
            c.source = source
            international.append(c)
        time.sleep(0.2)

    domestic = pick_unique(domestic, 30, seen_urls, seen_titles)
    international = pick_unique(international, 20, seen_urls, seen_titles)

    # backfill if short
    if len(domestic) < 30:
        more = pick_unique(enrich_tophub_domestic(60), 30 - len(domestic), seen_urls, seen_titles)
        domestic.extend(more)
    if len(international) < 20:
        for source, rss in INTL_RSS:
            more = pick_unique(fetch_rss(source, rss, 40), 20 - len(international), seen_urls, seen_titles)
            international.extend(more)

    combined = domestic[:30] + international[:20]
    final: list[dict[str, Any]] = []

    for i, c in enumerate(combined, start=1):
        content = c.content
        if len(content) < 400:
            content = fetch_article_content(c.url, c.title)
        title = c.title
        if c.region == "international":
            title = translate_text(title)
            if content:
                content = translate_text(content)
        elif not re.search(r"[\u4e00-\u9fff]", title):
            title = translate_text(title)
        if content and len(content) < 400:
            extra = fetch_article_content(c.url, title)
            if len(extra) > len(content):
                content = extra
        if c.region == "international" and content and not re.search(r"[\u4e00-\u9fff]", content[:200]):
            content = translate_text(content)
        source = c.source
        if source.startswith("www."):
            source = source[4:]
        final.append(
            {
                "rank_no": i,
                "title": title.strip(),
                "source": source,
                "region": c.region,
                "url": c.url,
                "content": content.strip() if content else "",
            }
        )
        print(f"built {i}/50 {c.region} {title[:50]}...", file=sys.stderr)
        time.sleep(0.15)

    out_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path))
    print(f"domestic={sum(1 for x in final if x['region']=='domestic')} intl={sum(1 for x in final if x['region']=='international')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
