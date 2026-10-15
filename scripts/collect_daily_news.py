#!/usr/bin/env python3
"""Collect daily trending news from tophub.today and authoritative sources."""

from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import html2text
import requests
from bs4 import BeautifulSoup

TZ = ZoneInfo("Asia/Shanghai")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
MAX_CONTENT = 20000
MIN_CONTENT = 400

# Subjective / gossip patterns to exclude
EXCLUDE_PATTERNS = re.compile(
    r"天塌|最惨|荒谬|震惊|惊呆|炸了|泪目|太牛|绝了|官宣.*恋情|"
    r"分手|离婚|出轨|绯闻|八卦|明星.*恋爱|颜值|身材|"
    r"广告|推广|优惠券|限时|秒杀|直播带货|"
    r"你怎么看|网友.*怒|网友.*炸|网友.*哭|"
    r"太.*了！|竟然.*！$|居然.*！$",
    re.I,
)

TOPHUB_SOURCES = {
    "知乎热榜": "/n/mproPpoq6O",
    "微博热搜": "/n/KqndgxeLl9",
    "百度热点": "/n/Jb0vmloB1G",
    "今日头条": "/n/x9ozB4KoXb",
    "微信热文": "/n/WnBe01o371",
    "36氪": "/n/Q1Vd5Ko85R",
    "虎嗅": "/n/5VaobgvAj1",
    "IT之家": "/n/74Kvx59dkx",
    "Readhub": "/n/Y3QeLMPo7k",
    "科普中国": "/n/DgeyxkwdZq",
    "澎湃热榜": "/n/wWmoO5Rd4E",
    "中国政府网头条": "/n/Q0or6qzo8B",
    "政策解读": "/n/nBe0B3bv37",
    "国务院信息": "/n/proPJ9ldq6",
    "外交部": "/n/3adqZlMeng",
    "中央纪委": "/n/VaobMBMeAj",
    "教育部": "/n/12owqRJdNV",
    "国家统计局": "/n/YKd6JOqdaP",
    "商务部": "/n/1Vd5Rm5e85",
    "证监会": "/n/4MdAKwLoxD",
    "第一财经": "/n/0MdKam4ow1",
    "21财经": "/n/4Kvx5R0dkx",
    "华尔街见闻": "/n/G2me3ndwjq",
    "地震局": "/n/7GdabXpeQy",
    "应急广播": "/n/3QeLp7Ge7k",
    "辟谣平台": "/n/1Vd5PbMv85",
}

DIRECT_SOURCES = {
    "新华网": "https://www.news.cn/",
    "人民网": "http://www.people.com.cn/",
    "央视新闻": "https://news.cctv.com/",
    "中国新闻网": "https://www.chinanews.com.cn/",
    "光明网": "https://www.gmw.cn/",
    "中国日报": "https://cn.chinadaily.com.cn/",
    "中国政府网": "https://www.gov.cn/",
    "环球网": "https://www.huanqiu.com/",
    "BBC News": "https://www.bbc.com/news",
    "Reuters": "https://www.reuters.com/",
    "AP News": "https://apnews.com/",
    "Al Jazeera": "https://www.aljazeera.com/",
    "The Guardian": "https://www.theguardian.com/international",
    "Bloomberg": "https://www.bloomberg.com/",
    "UN News": "https://news.un.org/en/",
    "NHK World": "https://www3.nhk.or.jp/nhkworld/en/news/",
    "SCMP": "https://www.scmp.com/",
}


@dataclass
class NewsItem:
    title: str
    source: str
    url: str = ""
    region: str = "domestic"
    content: str = ""
    score: float = 0.0
    seen_on: list[str] = field(default_factory=list)


def fetch_url(url: str, timeout: int = 20) -> str | None:
    try:
        r = SESSION.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception:
        return None


def parse_tophub(html: str, source_name: str) -> list[NewsItem]:
    items: list[NewsItem] = []
    if not html:
        return items
    soup = BeautifulSoup(html, "lxml")
    for row in soup.select("table tbody tr, .cc-dc-content .cc-cd, .cc-cd"):
        title_el = row.select_one("a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        if not title or len(title) < 6:
            continue
        if href and not href.startswith("http"):
            href = urljoin("https://tophub.today", href)
        # Skip tophub redirect links - try to get actual URL from data attribute
        actual_url = href
        if "tophub.today/link" in href or "tophub.today/n/" in href:
            # Look for external link in same row
            ext = row.select_one("a[href^='http']:not([href*='tophub.today'])")
            if ext:
                actual_url = ext.get("href", href)
        region = classify_region(title, source_name, actual_url)
        items.append(
            NewsItem(
                title=title,
                source=source_name,
                url=actual_url,
                region=region,
                score=1.0,
                seen_on=[source_name],
            )
        )
    # Fallback: any links in main content
    if not items:
        for a in soup.select(".cc-cd-lb a, .cc-cd-cb-lb a, .item-title a, h3 a"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if title and len(title) >= 6 and href:
                if not href.startswith("http"):
                    href = urljoin("https://tophub.today", href)
                items.append(
                    NewsItem(
                        title=title,
                        source=source_name,
                        url=href,
                        region=classify_region(title, source_name, href),
                        score=1.0,
                        seen_on=[source_name],
                    )
                )
    return items


def parse_homepage(html: str, source_name: str, base_url: str) -> list[NewsItem]:
    items: list[NewsItem] = []
    if not html:
        return items
    soup = BeautifulSoup(html, "lxml")
    seen_titles: set[str] = set()
    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]
        if not title or len(title) < 8 or len(title) > 120:
            continue
        if href.startswith("#") or href.startswith("javascript"):
            continue
        if not href.startswith("http"):
            href = urljoin(base_url, href)
        # Skip nav/footer links
        if any(x in href for x in ["login", "register", "subscribe", "video/list", "/tag/"]):
            continue
        key = title[:30]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        region = classify_region(title, source_name, href)
        items.append(
            NewsItem(
                title=title,
                source=source_name,
                url=href,
                region=region,
                score=0.8,
                seen_on=[source_name],
            )
        )
        if len(items) >= 30:
            break
    return items


def classify_region(title: str, source: str, url: str) -> str:
    intl_sources = {
        "BBC", "Reuters", "AP", "Al Jazeera", "Guardian", "Bloomberg",
        "UN", "NHK", "SCMP", "DW", "NYT", "WSJ", "FT", "Economist",
        "华尔街见闻",
    }
    for s in intl_sources:
        if s.lower() in source.lower():
            return "international"
    intl_domains = [
        "reuters.com", "bbc.com", "bbc.co.uk", "apnews.com", "aljazeera.com",
        "theguardian.com", "bloomberg.com", "nytimes.com", "wsj.com", "ft.com",
        "economist.com", "dw.com", "nhk.or.jp", "scmp.com", "un.org",
        "cnn.com", "washingtonpost.com", "politico.com",
    ]
    if url:
        domain = urlparse(url).netloc.lower()
        for d in intl_domains:
            if d in domain:
                return "international"
    # China-related international events still count as international if from intl source
    return "domestic"


def should_exclude(title: str) -> bool:
    if EXCLUDE_PATTERNS.search(title):
        return True
    if len(title) < 8:
        return True
    # Pure entertainment
    ent_keywords = ["明星", "综艺", "选秀", "粉丝", "CP", "剧透", "票房破"]
    if any(k in title for k in ent_keywords) and not any(
        k in title for k in ["政策", "经济", "外交", "法律", "事故", "地震", "战争"]
    ):
        return True
    return False


def normalize_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title.strip())
    title = re.sub(r"^\d+[\.\、]\s*", "", title)
    title = re.sub(r"[#【】\[\]]", "", title)
    return title


def title_similarity(a: str, b: str) -> float:
    a, b = normalize_title(a), normalize_title(b)
    if a == b:
        return 1.0
    # Simple character overlap
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    overlap = len(set_a & set_b) / max(len(set_a), len(set_b))
    # Also check substring
    if a in b or b in a:
        overlap = max(overlap, 0.8)
    return overlap


def merge_items(all_items: list[NewsItem]) -> list[NewsItem]:
    merged: list[NewsItem] = []
    for item in all_items:
        if should_exclude(item.title):
            continue
        item.title = normalize_title(item.title)
        found = False
        for m in merged:
            if title_similarity(m.title, item.title) > 0.55:
                m.score += item.score
                m.seen_on.extend(item.seen_on)
                if item.url and ("tophub" not in item.url or not m.url):
                    if "tophub" in (m.url or ""):
                        m.url = item.url
                    elif not m.url:
                        m.url = item.url
                found = True
                break
        if not found:
            merged.append(item)
    merged.sort(key=lambda x: x.score, reverse=True)
    return merged


def extract_article_content(html: str, url: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    # Remove noise
    for tag in soup.select(
        "script, style, nav, header, footer, aside, "
        ".ad, .advertisement, .comment, .comments, "
        ".related, .recommend, .sidebar, .share, "
        "[class*='comment'], [class*='sidebar'], [id*='comment']"
    ):
        tag.decompose()

    # Try common article selectors
    selectors = [
        "article", ".article-content", ".article", "#article_content",
        ".content", ".post-content", ".entry-content", ".main-content",
        "#content", ".TRS_Editor", ".Custom_UnionStyle",
        ".article-body", ".story-body", "[data-component='text-block']",
        ".RichText", ".detail-content", ".news-content",
    ]
    text = ""
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text("\n", strip=True)
            if len(text) > 200:
                break

    if len(text) < 200:
        # Fallback: largest text block
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.body_width = 0
        text = h.handle(str(soup.find("body") or soup))

    # Clean up
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > MAX_CONTENT:
        text = text[:MAX_CONTENT]
    return text.strip()


def fetch_article_content(url: str) -> str:
    if not url or "tophub.today" in url:
        return ""
    html = fetch_url(url, timeout=25)
    if not html:
        return ""
    return extract_article_content(html, url)


def resolve_tophub_url(url: str) -> str:
    """Follow tophub redirect to get actual article URL."""
    if not url or "tophub.today" not in url:
        return url
    html = fetch_url(url, timeout=15)
    if not html:
        return url
    # Look for meta refresh or redirect link
    soup = BeautifulSoup(html, "lxml")
    meta = soup.find("meta", attrs={"http-equiv": re.compile("refresh", re.I)})
    if meta and meta.get("content"):
        m = re.search(r"url=(.+?)(?:;|$)", meta["content"], re.I)
        if m:
            return m.group(1).strip("'\"")
    link = soup.select_one("a[href^='http']:not([href*='tophub.today'])")
    if link:
        return link["href"]
    return url


def select_final_items(merged: list[NewsItem], domestic: int = 30, intl: int = 20) -> list[NewsItem]:
    domestic_items = [i for i in merged if i.region == "domestic"]
    intl_items = [i for i in merged if i.region == "international"]
    selected: list[NewsItem] = []
    selected.extend(domestic_items[:domestic])
    selected.extend(intl_items[:intl])
    # Fill gaps if not enough
    if len(selected) < domestic + intl:
        remaining = [i for i in merged if i not in selected]
        selected.extend(remaining[: domestic + intl - len(selected)])
    return selected[: domestic + intl]


def collect_all() -> list[NewsItem]:
    all_items: list[NewsItem] = []

    def fetch_tophub(name: str, path: str) -> list[NewsItem]:
        url = f"https://tophub.today{path}"
        html = fetch_url(url)
        return parse_tophub(html or "", name)

    def fetch_direct(name: str, url: str) -> list[NewsItem]:
        html = fetch_url(url)
        return parse_homepage(html or "", name, url)

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = []
        for name, path in TOPHUB_SOURCES.items():
            futures.append(ex.submit(fetch_tophub, name, path))
        for name, url in DIRECT_SOURCES.items():
            futures.append(ex.submit(fetch_direct, name, url))
        for f in as_completed(futures):
            try:
                all_items.extend(f.result())
            except Exception:
                pass

    return merge_items(all_items)


def enrich_with_content(items: list[NewsItem]) -> list[NewsItem]:
    def enrich_one(item: NewsItem) -> NewsItem:
        url = item.url
        if url and "tophub.today" in url:
            url = resolve_tophub_url(url)
            item.url = url
        if url:
            content = fetch_article_content(url)
            if content:
                item.content = content
        return item

    with ThreadPoolExecutor(max_workers=6) as ex:
        enriched = list(ex.map(enrich_one, items))
    return enriched


def main() -> int:
    run_date = datetime.now(TZ).date().isoformat()
    print(f"Collecting news for {run_date}...", file=sys.stderr)

    merged = collect_all()
    print(f"Collected {len(merged)} unique items after merge", file=sys.stderr)

    selected = select_final_items(merged)
    print(f"Selected {len(selected)} items, fetching content...", file=sys.stderr)

    enriched = enrich_with_content(selected)

    output = []
    for i, item in enumerate(enriched, 1):
        output.append(
            {
                "rank_no": i,
                "title": item.title,
                "source": item.source,
                "region": item.region,
                "url": item.url or "",
                "content": item.content or "",
            }
        )

    out_path = f"/workspace/data/daily_news_{run_date}.json"
    import os
    os.makedirs("/workspace/data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    domestic = sum(1 for x in output if x["region"] == "domestic")
    intl = sum(1 for x in output if x["region"] == "international")
    with_content = sum(1 for x in output if x["content"])
    print(
        f"Wrote {out_path}: {len(output)} items "
        f"({domestic} domestic, {intl} intl, {with_content} with content)",
        file=sys.stderr,
    )
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
