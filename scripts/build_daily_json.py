#!/usr/bin/env python3
"""Build daily_news JSON from tophub, chinanews RSS, and international RSS."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data"

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

TOPHUB_NODES = [
    ("中国政府网头条", "https://tophub.today/n/Q0or6qzo8B"),
    ("国务院信息", "https://tophub.today/n/proPJ9ldq6"),
    ("外交部发言人", "https://tophub.today/n/3adqZlMeng"),
    ("国家统计局", "https://tophub.today/n/YKd6JOqdaP"),
    ("商务部政策", "https://tophub.today/n/1Vd5Rm5e85"),
    ("证监会", "https://tophub.today/n/4MdAKwLoxD"),
    ("中央纪委", "https://tophub.today/n/VaobMBMeAj"),
    ("教育部", "https://tophub.today/n/12owqRJdNV"),
    ("地震速报", "https://tophub.today/n/7GdabXpeQy"),
    ("应急广播", "https://tophub.today/n/3QeLp7Ge7k"),
    ("辟谣平台", "https://tophub.today/n/1Vd5PbMv85"),
    ("百度热点", "https://tophub.today/n/Jb0vmloB1G"),
    ("微博热搜", "https://tophub.today/n/KqndgxeLl9"),
    ("知乎热榜", "https://tophub.today/n/mproPpoq6O"),
    ("IT之家", "https://tophub.today/n/74Kvx59dkx"),
    ("36氪", "https://tophub.today/n/Q1Vd5Ko85R"),
    ("第一财经", "https://tophub.today/n/0MdKam4ow1"),
    ("华尔街见闻", "https://tophub.today/n/G2me3ndwjq"),
]

INTL_RSS = [
    ("BBC", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("Yonhap", "https://en.yna.co.kr/RSS/news.xml"),
    ("DW", "https://rss.dw.com/rdf/rss-en-all"),
    ("NHK", "https://www3.nhk.or.jp/rss/news/cat0.xml"),
]

SUBJECTIVE_RE = re.compile(
    r"天塌了|最惨|荒谬|震惊|吓傻|爆了|炸了|泪目|破防|妈见打|谁赢谁输|"
    r"千万别|一定要|如何越做越|沦为.*幌子",
    re.I,
)
GOSSIP_RE = re.compile(
    r"恋情|出轨|绯闻|八卦|爱豆|追星|免提.*男友|猥亵|昵称|卫衣配短裤|"
    r"霸王茶姬.*奥迪|机器狗.*哀牢山",
    re.I,
)
LIFESTYLE_RE = re.compile(
    r"自驾|阿禾公路|碳水节|烧烤节|舌尖上|电动牙刷|厚卫衣",
    re.I,
)
BAD_URL_HOSTS = (
    "tophub.today",
    "weibo.com",
    "zhihu.com",
    "baidu.com",
    "idaily.today",
)


@dataclass
class Candidate:
    title: str
    source: str
    url: str
    region: str
    content: str = ""


def fetch_bytes(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_text(url: str, timeout: int = 25) -> str:
    data = fetch_bytes(url, timeout=timeout)
    for enc in ("utf-8", "gbk", "gb2312"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def translate_en_zh(text: str, chunk: int = 450) -> str:
    if not text or re.search(r"[\u4e00-\u9fff]", text):
        return text.strip()
    parts: list[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    buf = ""
    for s in sentences:
        if len(buf) + len(s) < chunk:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                parts.append(buf)
            buf = s
    if buf:
        parts.append(buf)
    out: list[str] = []
    for p in parts:
        if not p.strip():
            continue
        q = urllib.parse.quote(p[:4800])
        api = f"https://api.mymemory.translated.net/get?q={q}&langpair=en|zh-CN"
        try:
            with urllib.request.urlopen(api, timeout=30) as r:
                d = json.loads(r.read())
            out.append(d.get("responseData", {}).get("translatedText", p))
        except Exception:
            out.append(p)
        time.sleep(0.35)
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def is_bad_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return True
    host = urllib.parse.urlparse(url).netloc.lower()
    return any(h in host for h in BAD_URL_HOSTS)


def title_ok(title: str) -> bool:
    if len(title) < 8 or len(title) > 120:
        return False
    if SUBJECTIVE_RE.search(title) or GOSSIP_RE.search(title) or LIFESTYLE_RE.search(title):
        return False
    return True


def parse_tophub(url: str, source_label: str) -> list[Candidate]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, "lxml")
    out: list[Candidate] = []
    for tr in soup.select("table tbody tr"):
        a = tr.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = (a.get("href") or "").strip()
        if not title_ok(title):
            continue
        if is_bad_url(href):
            continue
        out.append(Candidate(title=title, source=source_label, url=href, region="domestic"))
    return out


def parse_rss(url: str, source: str, region: str, limit: int = 40) -> list[Candidate]:
    raw = fetch_bytes(url)
    root = ET.fromstring(raw)
    channel = root.find("channel")
    items = root.findall(".//item") if channel is None else channel.findall("item")
    out: list[Candidate] = []
    for it in items[:limit]:
        title_el = it.find("title")
        link_el = it.find("link")
        if title_el is None or link_el is None:
            continue
        title = (title_el.text or "").strip()
        link = (link_el.text or "").strip()
        if not title or is_bad_url(link):
            continue
        if region == "domestic" and not title_ok(title):
            continue
        out.append(Candidate(title=title, source=source, url=link, region=region))
    return out


def extract_chinanews(html: str) -> str:
    m = re.search(r"<!--正文start-->(.*?)<!--正文end-->", html, re.DOTALL)
    if not m:
        return ""
    soup = BeautifulSoup(m.group(1), "lxml")
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    return "\n".join(paras)


def extract_govcn(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    div = soup.select_one(".pages_content") or soup.select_one("#UCAP-CONTENT")
    if not div:
        return ""
    paras = [p.get_text(strip=True) for p in div.find_all("p") if p.get_text(strip=True)]
    return "\n".join(paras)


def extract_generic(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for sel in (
        "article",
        "[role=main]",
        ".article-body",
        ".story-body",
        ".content",
        "[data-component='text-block']",
    ):
        node = soup.select_one(sel)
        if node:
            paras = [
                p.get_text(strip=True)
                for p in node.find_all("p")
                if len(p.get_text(strip=True)) > 25
            ]
            if paras:
                return "\n".join(paras)
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]
    return "\n".join(paras[:30])


def fetch_content(c: Candidate) -> str:
    try:
        html = fetch_text(c.url, timeout=30)
    except Exception:
        return ""
    low = html.lower()
    if re.search(
        r"(<title[^>]*>[^<]*(404|page not found|页面没有找到)[^<]*</title>|"
        r"we can't find the page|can't find the page you're looking for|"
        r"access denied</h1>)",
        low,
    ):
        return ""
    host = urllib.parse.urlparse(c.url).netloc
    if "chinanews.com.cn" in host:
        text = extract_chinanews(html)
    elif host.endswith("gov.cn"):
        text = extract_govcn(html)
    else:
        text = extract_generic(html)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 20000:
        text = text[:20000]
    return text


def content_matches_title(content: str, title: str) -> bool:
    if len(content) < 80:
        return False
    cl = content.casefold()
    for token in re.findall(r"[A-Za-z]{4,}|\d{2,}", title):
        if token.casefold() in cl:
            return True
    chars = re.sub(r"[^\u4e00-\u9fff]", "", title)
    stop = {"关于", "今日", "报道", "消息", "宣布", "相关", "情况", "这些", "如何"}
    for n in (6, 5, 4, 3):
        for i in range(len(chars) - n + 1):
            sub = chars[i : i + n]
            if sub in stop:
                continue
            if sub in content:
                return True
    return len(chars) < 4


def dedupe_key(c: Candidate) -> str:
    return re.sub(r"\W+", "", c.title)[:40]


def build_domestic(target: int) -> list[Candidate]:
    pool: list[Candidate] = []
    pool.extend(parse_rss("https://www.chinanews.com.cn/rss/scroll-news.xml", "中国新闻网", "domestic", 80))
    for label, url in TOPHUB_NODES:
        try:
            pool.extend(parse_tophub(url, label))
        except Exception:
            pass
        time.sleep(0.2)
    seen: set[str] = set()
    picked: list[Candidate] = []
    for c in pool:
        k = dedupe_key(c)
        if k in seen:
            continue
        seen.add(k)
        if not title_ok(c.title):
            continue
        picked.append(c)
        if len(picked) >= target * 3:
            break
    return picked[: target * 3]


def build_international(target: int) -> list[Candidate]:
    pool: list[Candidate] = []
    for source, url in INTL_RSS:
        try:
            pool.extend(parse_rss(url, source, "international", 35))
        except Exception:
            pass
        time.sleep(0.2)
    seen: set[str] = set()
    picked: list[Candidate] = []
    for c in pool:
        k = dedupe_key(c)
        if k in seen:
            continue
        seen.add(k)
        # skip obvious non-news
        if re.search(r"podcast|crossword|quiz|opinion", c.title, re.I):
            continue
        picked.append(c)
        if len(picked) >= target * 2:
            break
    return picked[: target * 2]


def enrich(c: Candidate) -> Candidate:
    raw = fetch_content(c)
    if c.region == "international":
        if raw and len(raw) < 80:
            raw = ""
        if re.search(r"[\u4e00-\u9fff]", c.title):
            title_zh = c.title
        else:
            title_zh = translate_en_zh(c.title)
        if raw:
            snippet = raw[:1800] if len(raw) > 1800 else raw
            content_zh = translate_en_zh(snippet)
        else:
            content_zh = ""
        c.title = title_zh or c.title
        c.content = content_zh if content_zh and len(content_zh) >= 80 else ""
    else:
        c.content = raw if content_matches_title(raw, c.title) else ""
    return c


def main() -> None:
    run_date = datetime.now(TZ).date()
    out_path = OUT_DIR / f"daily_news_{run_date.isoformat()}.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    domestic_pool = build_domestic(30)
    intl_pool = build_international(20)

    final_domestic: list[Candidate] = []
    for c in domestic_pool:
        if len(final_domestic) >= 30:
            break
        try:
            ec = enrich(c)
        except Exception:
            ec = c
        final_domestic.append(ec)
        time.sleep(0.15)

    final_intl: list[Candidate] = []
    for c in intl_pool:
        if len(final_intl) >= 20:
            break
        try:
            ec = enrich(c)
        except Exception:
            ec = c
        final_intl.append(ec)
        time.sleep(0.4)

    # pad if short
    while len(final_domestic) < 30 and domestic_pool:
        c = domestic_pool.pop(0)
        if c not in final_domestic:
            final_domestic.append(c)
    while len(final_intl) < 20 and intl_pool:
        c = intl_pool.pop(0)
        if c not in final_intl:
            final_intl.append(c)

    items: list[dict[str, Any]] = []
    rank = 1
    for c in final_domestic[:30]:
        items.append(
            {
                "rank_no": rank,
                "title": c.title,
                "source": c.source,
                "region": "domestic",
                "url": c.url,
                "content": c.content or "",
            }
        )
        rank += 1
    for c in final_intl[:20]:
        items.append(
            {
                "rank_no": rank,
                "title": c.title,
                "source": c.source,
                "region": "international",
                "url": c.url,
                "content": c.content or "",
            }
        )
        rank += 1

    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(items)} items to {out_path}")
    print(f"domestic={sum(1 for x in items if x['region']=='domestic')} intl={sum(1 for x in items if x['region']=='international')}")
    print(f"with_content={sum(1 for x in items if x.get('content'))}")


if __name__ == "__main__":
    main()
