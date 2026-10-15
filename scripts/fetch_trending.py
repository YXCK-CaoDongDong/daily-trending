#!/usr/bin/env python3
"""Fetch raw trending items from tophub.today and international news sites."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

TZ = ZoneInfo("Asia/Shanghai")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; daily-trending-bot/1.0)",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
TOPHUB_NODES: dict[str, str] = {
    "mproPpoq6O": "知乎热榜",
    "KqndgxeLl9": "微博热搜",
    "Jb0vmloB1G": "百度实时热点",
    "x9ozB4KoXb": "今日头条",
    "WnBe01o371": "微信24h热文",
    "Q1Vd5Ko85R": "36氪",
    "5VaobgvAj1": "虎嗅网",
    "74Kvx59dkx": "IT之家",
    "Y3QeLMPo7k": "Readhub",
    "DgeyxkwdZq": "科普中国",
    "wWmoO5Rd4E": "澎湃新闻",
    "NKGoRAzel6": "吾爱破解",
    "G47o8weMmN": "虎扑社区",
    "Q0or6qzo8B": "中国政府网头条",
    "nBe0B3bv37": "中国政府网政策解读",
    "proPJ9ldq6": "国务院信息",
    "3adqZlMeng": "外交部发言人",
    "VaobMBMeAj": "中央纪委",
    "12owqRJdNV": "教育部",
    "YKd6JOqdaP": "国家统计局",
    "1Vd5Rm5e85": "商务部",
    "4MdAKwLoxD": "证监会",
    "0MdKam4ow1": "第一财经",
    "4Kvx5R0dkx": "21财经",
    "G2me3ndwjq": "华尔街见闻",
    "7GdabXpeQy": "中国地震局",
    "3QeLp7Ge7k": "国家应急广播",
    "1Vd5PbMv85": "中国互联网联合辟谣平台",
}

ENTERTAINMENT_RE = re.compile(
    r"明星|八卦|恋情|离婚|出轨|综艺|选秀|粉丝|饭圈|演唱会|"
    r"孙宇晨.*景甜|景甜.*孙宇晨|管.*叫妈妈"
)
SUBJECTIVE_RE = re.compile(
    r"怎么看|如何看待|怎么评价|究竟|到底|震惊|炸裂|离谱|"
    r"天塌|最惨|荒谬|绝了|破防|泪目|哭死|太.*了$"
)


def today_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def fetch_tophub_node(session: requests.Session, hash_id: str, source: str, date: str) -> list[dict]:
    page_url = f"https://tophub.today/n/{hash_id}"
    try:
        page = session.get(page_url, timeout=25)
        page.raise_for_status()
    except requests.RequestException as exc:
        return [{"source": source, "title": f"[fetch failed: {exc}]", "extra": "", "url": page_url}]

    m = re.search(r'window\.nodeId\s*=\s*"(\d+)"', page.text)
    if not m:
        if "验证码" in page.text or "captcha" in page.text.lower():
            return [{"source": source, "title": "[CAPTCHA blocked]", "extra": "", "url": page_url}]
        return []

    node_id = m.group(1)
    try:
        resp = session.post(
            "https://tophub.today/node-items-by-date",
            data={"p": 1, "date": date, "nodeid": node_id},
            headers={**HEADERS, "Referer": page_url, "X-Requested-With": "XMLHttpRequest"},
            timeout=25,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return []

    if payload.get("error") or not isinstance(payload.get("data"), dict):
        return []

    items = payload["data"].get("items") or []
    out: list[dict] = []
    for it in items:
        title = (it.get("title") or "").strip()
        if not title or title.startswith("["):
            continue
        out.append(
            {
                "source": source,
                "title": title,
                "extra": (it.get("extra") or "").strip(),
                "url": (it.get("url") or "").strip(),
            }
        )
    return out


def fetch_rss_or_html(session: requests.Session, url: str, source: str, selector: str) -> list[dict]:
    try:
        resp = session.get(url, timeout=25)
        resp.raise_for_status()
    except requests.RequestException:
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    out: list[dict] = []
    for el in soup.select(selector)[:20]:
        title = el.get_text(" ", strip=True)
        if not title or len(title) < 8:
            continue
        href = el.get("href") or ""
        if href and not href.startswith("http"):
            href = urljoin(url, href)
        out.append({"source": source, "title": title, "extra": "", "url": href})
    return out


def fetch_international(session: requests.Session) -> list[dict]:
    feeds = [
        ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", "item > title"),
        ("Associated Press", "https://rsshub.app/apnews/topics/apf-topnews", "item > title"),
        ("The Guardian", "https://www.theguardian.com/world/rss", "item > title"),
        ("Deutsche Welle", "https://rss.dw.com/rdf/rss-en-world", "item > title"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "item > title"),
        ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "item > title"),
        ("NHK World", "https://www3.nhk.or.jp/nhkworld/en/news/rss/top.xml", "item > title"),
    ]
    items: list[dict] = []
    for source, url, sel in feeds:
        items.extend(fetch_rss_or_html(session, url, source, sel))
    # HTML fallbacks
    html_sources = [
        ("新华网", "https://www.news.cn/", "a"),
        ("人民网", "http://www.people.com.cn/", "a"),
        ("央视新闻", "https://news.cctv.com/", "h3 a, .title a"),
        ("中国新闻网", "https://www.chinanews.com.cn/", "a"),
    ]
    for source, url, sel in html_sources:
        for it in fetch_rss_or_html(session, url, source, sel):
            if len(it["title"]) >= 10 and not it["title"].startswith("http"):
                items.append(it)
    return items


def main() -> int:
    date = today_str()
    session = requests.Session()
    session.headers.update(HEADERS)

    all_items: list[dict] = []
    for hash_id, source in TOPHUB_NODES.items():
        all_items.extend(fetch_tophub_node(session, hash_id, source, date))
        print(f"tophub {source}: fetched", file=sys.stderr)

    all_items.extend(fetch_international(session))
    print(f"total raw items: {len(all_items)}", file=sys.stderr)

    json.dump({"date": date, "items": all_items}, sys.stdout, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
