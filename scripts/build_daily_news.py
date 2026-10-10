#!/usr/bin/env python3
"""Build daily news JSON (30 domestic + 20 international) for cron ingest."""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import trafilatura
from deep_translator import GoogleTranslator

TZ = ZoneInfo("Asia/Shanghai")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MIN_CONTENT = 80
MAX_CONTENT = 20000

DOMESTIC_SKIP_RE = re.compile(
    r"shipin|/tp/hd|/video/|养生|好处|打卡|可以不|被骗|妖精|红毯步|方艳华逝世|"
    r"郭麒麟|刘震云|三体|不要回答|补肝|牙齿老化|厨房中常见"
)
INTL_SKIP_RE = re.compile(
    r"/video/|/videos/|Celebrity Traitors|hit song|Boots has|sports/|/sport/|"
    r"Premier League|Manchester United vs|AFCON|podcast|recipe|fashion|lingerie"
)

JUNK_RE = re.compile(
    r"页面没有找到|Page not found|404|access denied|请先登录|下载客户端",
    re.I,
)


def fetch_url(url: str, timeout: int = 35) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


TOPHUB_DOMESTIC_IDS = (
    "Jb0vmloB1G",
    "Q0or6qzo8B",
    "3adqZlMeng",
    "YKd6JOqdaP",
    "4MdAKwLoxD",
    "7GdabXpeQy",
    "74Kvx59dkx",
    "wWmoO5Rd4E",
    "1Vd5Rm5e85",
    "G2me3ndwjq",
)

CHINANEWS_RSS = (
    ("https://www.chinanews.com.cn/rss/scroll-news.xml", "中国新闻网"),
    ("https://www.chinanews.com.cn/rss/importnews.xml", "中国新闻网"),
    ("https://www.chinanews.com.cn/rss/china.xml", "中国新闻网"),
    ("https://www.chinanews.com.cn/rss/society.xml", "中国新闻网"),
    ("https://www.chinanews.com.cn/rss/finance.xml", "中国新闻网"),
)


def source_for_url(url: str) -> str:
    host = re.sub(r"^www\.", "", re.search(r"https?://([^/]+)", url).group(1))  # type: ignore[union-attr]
    if "chinanews" in host:
        return "中国新闻网"
    if host == "gov.cn":
        return "中国政府网"
    if "mfa.gov.cn" in host:
        return "外交部"
    if "ithome.com" in host:
        return "IT之家"
    return host


def domestic_candidates() -> list[tuple[str, str, str]]:
    """Return (title, url, source) tuples."""
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    for rss_url, source in CHINANEWS_RSS:
        try:
            raw = fetch_url(rss_url)
            root = ET.fromstring(raw)
            for item in root.findall(".//item"):
                link_el = item.find("link")
                title_el = item.find("title")
                if link_el is None or title_el is None:
                    continue
                link = (link_el.text or "").strip().replace("http://", "https://")
                title = html.unescape((title_el.text or "").strip())
                if not link or not title or link in seen:
                    continue
                if DOMESTIC_SKIP_RE.search(link + title) or "/iframe/" in link or "/tp/hd" in link:
                    continue
                if len(title) < 10:
                    continue
                seen.add(link)
                out.append((title, link, source))
        except Exception as exc:
            print(f"cn rss fail {rss_url}: {exc}", file=sys.stderr)

    for node_id in TOPHUB_DOMESTIC_IDS:
        try:
            page = fetch_url(f"https://tophub.today/n/{node_id}")
        except Exception:
            continue
        for m in re.finditer(
            r'href="(https?://(?:www\.gov\.cn|www\.mfa\.gov\.cn|www\.chinanews\.com\.cn|www\.ithome\.com)[^"]+)"',
            page,
        ):
            url = m.group(1).replace("http://", "https://")
            if url in seen or "/home/20" in url:
                continue
            seen.add(url)
            out.append(("", url, source_for_url(url)))

    return out


def extract_domestic(url: str) -> tuple[str, str]:
    raw = fetch_url(url)
    title_m = re.search(r"<title>([^<]+)</title>", raw)
    page_title = html.unescape(title_m.group(1).split("-")[0].strip()) if title_m else ""
    m = re.search(r'<div class="left_zw">(.*?)</div>\s*<div class="clear">', raw, re.S)
    if m:
        text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip())
    else:
        gm = re.search(r'<div class="pages_content"[^>]*>(.*?)</div>', raw, re.S)
        if gm:
            text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", gm.group(1))).strip())
        else:
            text = trafilatura.extract(raw) or ""
    return page_title, text


def parse_rss(url: str, source: str, limit: int = 40) -> list[dict]:
    raw = fetch_url(url)
    root = ET.fromstring(raw)
    items: list[dict] = []
    for item in root.findall(".//item"):
        link_el = item.find("link")
        title_el = item.find("title")
        if link_el is None or title_el is None:
            continue
        link = (link_el.text or "").strip()
        title = html.unescape((title_el.text or "").strip())
        if not link or not title or INTL_SKIP_RE.search(link + " " + title):
            continue
        items.append({"title_en": title, "url": link, "source": source})
        if len(items) >= limit:
            break
    return items


def extract_intl(url: str) -> str:
    downloaded = trafilatura.fetch_url(url, no_ssl=True)
    if not downloaded:
        try:
            downloaded = fetch_url(url)
        except Exception:
            return ""
    text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
    return (text or "").strip()


_translator = GoogleTranslator(source="auto", target="zh-CN")


def translate(text: str) -> str:
    if not text:
        return ""
    # chunk for API limits
    if len(text) <= 4500:
        try:
            return _translator.translate(text)
        except Exception:
            return text
    parts = []
    for i in range(0, len(text), 4000):
        chunk = text[i : i + 4000]
        try:
            parts.append(_translator.translate(chunk))
        except Exception:
            parts.append(chunk)
        time.sleep(0.3)
    return "".join(parts)


def sanitize_content(content: str, title: str) -> str:
    if not content or JUNK_RE.search(content):
        return ""
    if len(content) < MIN_CONTENT:
        return ""
    markers = [
        t
        for t in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}|\d{2,}", title)
        if t not in {"正式", "通报", "消息", "报道", "新闻", "中国", "美国"}
    ]
    if markers and not any(m.lower() in content.lower() for m in markers[:8]):
        return ""
    if len(content) > MAX_CONTENT:
        content = content[:MAX_CONTENT]
    return content


def pick_domestic(candidates: list[tuple[str, str, str]], n: int = 30) -> list[dict]:
    picked: list[dict] = []
    used_urls: set[str] = set()
    priority_kw = (
        "厄尔尼诺", "卫星", "何立峰", "证监会", "商务部", "暴雨", "地震", "巴拿马",
        "飞天奖", "郑钦文", "谌贻琴", "彭丽媛", "范光明", "人民币", "无障碍",
        "国庆", "出游", "中欧", "检验检测", "海南", "自贡", "云南", "重庆",
        "东博会", "邮轮", "NBA", "环崇明", "王曼昱", "德约", "吴易昺", "十五五",
        "外交部", "发言人", "受贿", "发射", "预警", "国新办",
    )

    def score(title: str) -> int:
        s = 0
        for kw in priority_kw:
            if kw in title:
                s += 3
        if re.search(r"涉嫌|被开|发布|成功发射|预警|回应|答记者问|强震|制裁", title):
            s += 2
        return s

    ranked = sorted(candidates, key=lambda x: score(x[0]), reverse=True)
    for title_hint, url, source in ranked:
        if len(picked) >= n or url in used_urls:
            continue
        used_urls.add(url)
        try:
            page_title, content = extract_domestic(url)
            use_title = page_title if page_title and len(page_title) > 10 else title_hint
            if not use_title or len(use_title) < 10:
                continue
            if DOMESTIC_SKIP_RE.search(use_title):
                continue
            content = sanitize_content(content, use_title)
            picked.append(
                {
                    "title": use_title,
                    "source": source,
                    "region": "domestic",
                    "url": url,
                    "content": content,
                }
            )
            time.sleep(0.12)
        except Exception as exc:
            print(f"domestic skip {url}: {exc}", file=sys.stderr)
    return picked


def pick_international(feeds: list[tuple[str, str]], n: int = 20) -> list[dict]:
    pool: list[dict] = []
    for rss_url, source in feeds:
        try:
            pool.extend(parse_rss(rss_url, source, limit=25))
        except Exception as exc:
            print(f"rss fail {rss_url}: {exc}", file=sys.stderr)

    # dedupe by url
    seen: set[str] = set()
    unique: list[dict] = []
    for row in pool:
        if row["url"] in seen:
            continue
        seen.add(row["url"])
        unique.append(row)

    picked: list[dict] = []
    for row in unique:
        if len(picked) >= n:
            break
        url = row["url"]
        try:
            body_en = extract_intl(url)
            if JUNK_RE.search(body_en):
                body_en = ""
            title_zh = translate(row["title_en"])
            content_zh = sanitize_content(translate(body_en) if body_en else "", title_zh)
            picked.append(
                {
                    "title": title_zh,
                    "source": row["source"],
                    "region": "international",
                    "url": url,
                    "content": content_zh,
                }
            )
            time.sleep(0.4)
        except Exception as exc:
            print(f"intl skip {url}: {exc}", file=sys.stderr)
    return picked


def main() -> int:
    run_date = datetime.now(TZ).date()
    out_path = Path(__file__).resolve().parents[1] / "data" / f"news_{run_date.isoformat()}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    domestic_cands = domestic_candidates()
    domestic = pick_domestic(domestic_cands, 30)

    feeds = [
        ("https://feeds.bbci.co.uk/news/rss.xml", "BBC"),
        ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"),
        ("https://www.theguardian.com/world/rss", "The Guardian"),
        ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "UN News"),
    ]
    international = pick_international(feeds, 20)

    items = domestic + international
    # pad if short — shouldn't happen often
    if len(items) < 50:
        print(f"WARNING: only {len(items)} items", file=sys.stderr)

    payload = []
    for i, row in enumerate(items[:50], start=1):
        payload.append({"rank_no": i, **row})

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload)} items to {out_path}")
    print(f"domestic={sum(1 for x in payload if x['region']=='domestic')} international={sum(1 for x in payload if x['region']=='international')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
