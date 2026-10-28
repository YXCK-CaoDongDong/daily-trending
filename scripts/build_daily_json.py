#!/usr/bin/env python3
"""Assemble ~50 daily news items (60% domestic / 40% intl) into JSON."""

from __future__ import annotations

import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import calendar
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import feedparser
import requests
import trafilatura

TZ = ZoneInfo("Asia/Shanghai")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

SUBJECTIVE_RE = re.compile(
    r"天塌了|最惨|荒谬|震惊|泪目|绝了|炸裂|官宣恋情|离婚|出轨|八卦|"
    r"颜值|热搜第一|太绝了|惊呆|吓傻|泪崩|破防|社死",
    re.I,
)
COMMENT_TITLE_RE = re.compile(r"^[A-Za-z][^:]{0,40}:\s", re.I)
OPINION_MARKERS = ("记者观察", "评论", "社论", "视点", "漫谈", "智库")
STALE_RE = re.compile(r"科学防疫小贴士|新冠疫苗|疫情防控措施优化|复商复市进行时")
JUNK_CONTENT_RE = re.compile(
    r"正在加载|页面没有找到|Page not found|404 not found|"
    r"下载客户端|请先登录|Just a moment",
    re.I,
)

DOMESTIC_FEEDS = [
    ("新华网", "https://www.news.cn/politics/news_politics.xml"),
    ("新华网", "https://www.news.cn/world/news_world.xml"),
    ("人民网", "https://www.people.com.cn/rss/politics.xml"),
    ("人民网", "https://www.people.com.cn/rss/world.xml"),
    ("中国新闻网", "https://www.chinanews.com.cn/rss/scroll-news.xml"),
    ("中国新闻网", "https://www.chinanews.com.cn/rss/china.xml"),
]

INTL_FEEDS = [
    ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("半岛电视台", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("联合国新闻", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("德国之声", "https://rss.dw.com/rdf/rss-en-world"),
    ("卫报", "https://www.theguardian.com/world/rss"),
    ("韩联社", "https://en.yna.co.kr/RSS/news.xml"),
]

INTL_HOSTS = (
    "bbc.co.uk",
    "bbc.com",
    "reuters.com",
    "apnews.com",
    "aljazeera.com",
    "un.org",
    "dw.com",
    "theguardian.com",
    "yna.co.kr",
    "nhk.or.jp",
    "kyodonews.net",
    "afp.com",
    "nytimes.com",
    "washingtonpost.com",
    "economist.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    "scmp.com",
    "straitstimes.com",
    "abc.net.au",
    "who.int",
    "imf.org",
    "worldbank.org",
    "nasa.gov",
)

SOURCE_CAPS = {"央视新闻": 8}


@dataclass
class Candidate:
    title: str
    url: str
    source: str
    region: str
    snippet: str = ""


def _host(url: str) -> str:
    h = (urlparse(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def is_intl_url(url: str) -> bool:
    host = _host(url)
    return any(host == d or host.endswith("." + d) for d in INTL_HOSTS)


def needs_translation(text: str) -> bool:
    """Disabled external translation (rate limits); intl patched separately."""
    return False


def entry_recent(entry: object, max_days: int = 4) -> bool:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return True
    try:
        ts = datetime.fromtimestamp(calendar.timegm(parsed), tz=TZ)
        return ts >= datetime.now(TZ) - timedelta(days=max_days)
    except Exception:
        return True


def bad_title(title: str) -> bool:
    t = title.strip()
    if len(t) < 8:
        return True
    if SUBJECTIVE_RE.search(t):
        return True
    if COMMENT_TITLE_RE.match(t):
        return True
    if STALE_RE.search(t):
        return True
    for m in OPINION_MARKERS:
        if m in t:
            return True
    return False


def fetch_cctv_json() -> list[Candidate]:
    out: list[Candidate] = []
    url = "https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_1.jsonp"
    try:
        r = SESSION.get(url, timeout=20)
        r.encoding = r.apparent_encoding or "utf-8"
        r.raise_for_status()
        text = r.text
        if text.startswith("news("):
            text = text[5:-1]
        data = json.loads(text)
        for item in data.get("data", {}).get("list", [])[:25]:
            title = (item.get("title") or "").strip()
            link = (item.get("url") or "").strip()
            brief = (item.get("brief") or "").strip()
            if not title or not link:
                continue
            if not link.startswith("http"):
                link = "https:" + link if link.startswith("//") else "https://news.cctv.com/" + link.lstrip("/")
            out.append(Candidate(title, link, "央视新闻", "domestic", brief))
    except Exception as exc:
        print(f"warn cctv: {exc}", file=sys.stderr)
    return out


def parse_rss(source: str, url: str, region: str, limit: int = 60) -> list[Candidate]:
    out: list[Candidate] = []
    try:
        r = SESSION.get(url, timeout=25)
        r.raise_for_status()
        feed = feedparser.parse(r.content)
    except Exception as exc:
        print(f"warn feed {url}: {exc}", file=sys.stderr)
        return out
    for entry in feed.entries[: limit * 3]:
        if not entry_recent(entry):
            continue
        title = html.unescape((entry.get("title") or "").strip())
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        snippet = ""
        if entry.get("summary"):
            snippet = html.unescape(re.sub(r"<[^>]+>", "", entry.summary)).strip()
        if region == "international" and not is_intl_url(link):
            continue
        if region == "domestic" and is_intl_url(link):
            continue
        out.append(Candidate(title, link, source, region, snippet))
        if len(out) >= limit:
            break
    return out


def collect_candidates() -> tuple[list[Candidate], list[Candidate]]:
    domestic: list[Candidate] = []
    international: list[Candidate] = []

    domestic.extend(fetch_cctv_json())
    for source, url in DOMESTIC_FEEDS:
        domestic.extend(parse_rss(source, url, "domestic", limit=80))

    for source, url in INTL_FEEDS:
        international.extend(parse_rss(source, url, "international", limit=40))

    return domestic, international


def dedupe(cands: Iterable[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    out: list[Candidate] = []
    for c in cands:
        key = re.sub(r"\s+", "", c.title)[:40]
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def round_robin_pick(groups: dict[str, list[Candidate]], total: int, caps: dict[str, int] | None = None) -> list[Candidate]:
    caps = caps or {}
    counts: dict[str, int] = defaultdict(int)
    chosen: list[Candidate] = []
    keys = list(groups.keys())
    idx = 0
    while len(chosen) < total and keys:
        src = keys[idx % len(keys)]
        pool = groups[src]
        if pool:
            c = pool.pop(0)
            if counts[src] >= caps.get(src, 999):
                idx += 1
                if not pool:
                    keys = [k for k in keys if groups[k]]
                continue
            counts[src] += 1
            chosen.append(c)
        if not pool:
            keys = [k for k in keys if groups[k]]
        idx += 1
        if not keys:
            break
    return chosen


def pick_pool(domestic: list[Candidate], international: list[Candidate]) -> list[Candidate]:
    dom = [c for c in dedupe(domestic) if not bad_title(c.title)]
    intl = [c for c in dedupe(international) if not bad_title(c.title)]

    dom_groups: dict[str, list[Candidate]] = defaultdict(list)
    for c in dom:
        dom_groups[c.source].append(c)
    intl_groups: dict[str, list[Candidate]] = defaultdict(list)
    for c in intl:
        intl_groups[c.source].append(c)

    chosen = round_robin_pick(dom_groups, 30, SOURCE_CAPS)
    chosen.extend(round_robin_pick(intl_groups, 20))
    if len(chosen) < 50:
        seen = {x.url for x in chosen}
        for c in dom + intl:
            if len(chosen) >= 50:
                break
            if c.url not in seen:
                seen.add(c.url)
                chosen.append(c)
    return chosen[:50]


def translate_en_zh(text: str) -> str:
    if not text or not needs_translation(text):
        return text
    chunks: list[str] = []
    part = text[:4500]
    for i in range(0, len(part), 450):
        piece = part[i : i + 450]
        try:
            r = SESSION.get(
                "https://api.mymemory.translated.net/get",
                params={"q": piece, "langpair": "en|zh-CN"},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            tr = data.get("responseData", {}).get("translatedText", "")
            if tr and "QUERY LENGTH" not in tr.upper() and "MYMEMORY WARNING" not in tr.upper():
                chunks.append(tr)
            else:
                chunks.append(piece)
        except Exception:
            chunks.append(piece)
        time.sleep(0.3)
    return "".join(chunks)


def extract_article(url: str) -> str:
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        if r.encoding is None or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding or "utf-8"
        html_text = r.text
    except Exception:
        return ""
    if JUNK_CONTENT_RE.search(html_text[:5000]):
        return ""
    text = trafilatura.extract(html_text, include_comments=False, include_tables=False) or ""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if JUNK_CONTENT_RE.search(text):
        return ""
    return text


def title_markers(title: str) -> list[str]:
    stop = {"正式", "通报", "处理", "结果", "关于", "今日", "今天", "最新", "消息", "报道", "新闻", "宣布", "确认"}
    return [
        t
        for t in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}|\d{2,}", title)
        if t not in stop
    ]


def content_ok(content: str, title: str) -> bool:
    if len(content) < 80:
        return False
    if JUNK_CONTENT_RE.search(content):
        return False
    markers = title_markers(title)
    if not markers:
        return True
    low = content.casefold()
    return any(m.casefold() in low for m in markers[:6])


def clean_snippet(snippet: str) -> str:
    s = re.sub(r"\s+", " ", snippet).strip()
    s = re.sub(r"^[\s　]*", "", s)
    return s


def finalize_item(c: Candidate) -> dict:
    title_zh = c.title
    if needs_translation(c.title):
        title_zh = translate_en_zh(c.title)

    body = ""
    if c.snippet and len(clean_snippet(c.snippet)) >= 120:
        body = clean_snippet(c.snippet)
    if len(body) < 120:
        body = extract_article(c.url)
    if needs_translation(body):
        body = translate_en_zh(body)
    if body and not content_ok(body, title_zh):
        if c.snippet and content_ok(clean_snippet(c.snippet), title_zh):
            body = clean_snippet(c.snippet)
        else:
            body = ""
    if body and len(body) > 20000:
        body = body[:20000]
    return {
        "title": title_zh.strip(),
        "source": c.source,
        "region": c.region,
        "url": c.url,
        "content": body.strip() if body else "",
    }


def main() -> int:
    run_date = datetime.now(TZ).date().isoformat()
    out_path = Path(__file__).resolve().parents[1] / "data" / f"daily_news_{run_date}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    domestic, international = collect_candidates()
    pool = pick_pool(domestic, international)
    if len(pool) < 50:
        print(f"warn: only {len(pool)} candidates", file=sys.stderr)

    items: list[dict] = []
    for i, c in enumerate(pool, start=1):
        print(f"fetch {i}/50 {c.region} {c.source}", file=sys.stderr)
        row = finalize_item(c)
        row["rank_no"] = i
        items.append(row)
        time.sleep(0.12)

    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path))
    with_content = sum(1 for x in items if x.get("content") and len(x["content"]) >= 80)
    print(f"items={len(items)} with_content={with_content}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
