#!/usr/bin/env python3
"""Build daily news JSON: 30 domestic + 20 international factual items."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from typing import Any

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MIN_CONTENT = 80
MAX_CONTENT = 20000
TOPHUB_UA = UA

GOSSIP_RE = re.compile(
    r"八卦|明星|恋情|离婚|出轨|黑粉|饭圈|颜值|怼|最惨|天塌|荒谬|"
    r"Blackpink|K-Pop| Ronaldo|利物浦|曼城|皇马|维尼修斯|"
    r"科普小知识|灯泡为何|牛奶为什么|点题·共同关注",
    re.I,
)
SUBJECTIVE_RE = re.compile(r"遭背叛|圈粉|焕新|解锁了哪些")

# url -> {title, content} Chinese (filled for international articles)
INTL_ZH: dict[str, dict[str, str]] = {}


def fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clamp_content(text: str | None) -> str | None:
    if not text:
        return None
    text = text.strip()
    if len(text) < MIN_CONTENT:
        return None
    if len(text) > MAX_CONTENT:
        return text[:MAX_CONTENT]
    return text


def parse_rss(url: str, source: str) -> list[dict[str, Any]]:
    try:
        raw = fetch(url)
    except Exception as exc:
        print(f"rss fail {url}: {exc}", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        print(f"rss parse {url}: {exc}", file=sys.stderr)
        return []
    channel = root.find("channel")
    if channel is None:
        channel = root
    items: list[dict[str, Any]] = []
    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        if title_el is None or link_el is None:
            continue
        title = (title_el.text or "").strip()
        link = (link_el.text or "").strip()
        if not title or not link:
            continue
        desc = strip_html(desc_el.text or "") if desc_el is not None else ""
        items.append(
            {"title": title, "url": link, "source": source, "rss_desc": desc}
        )
    return items


def fetch_chinanews(url: str) -> str | None:
    try:
        html = fetch(url)
    except Exception:
        return None
    m = re.search(
        r"<!--正文start-->\s*<div class=\"left_zw\">(.*?)<!--正文end-->",
        html,
        re.S,
    )
    if not m:
        m = re.search(r'<div class="left_zw">(.*?)</div>\s*<!--正文end-->', html, re.S)
    if not m:
        return None
    text = strip_html(m.group(1))
    text = re.sub(r"【编辑:.*?】$", "", text).strip()
    return clamp_content(text)


def fetch_bbc(url: str) -> str | None:
    try:
        html = fetch(url)
    except Exception:
        return None
    paras = re.findall(
        r'<p class="ssrcss-[^"]*-Paragraph[^"]*">(.*?)</p>', html, re.S
    )
    texts: list[str] = []
    for p in paras:
        t = strip_html(p)
        if len(t) > 25 and not t.startswith("Watch:"):
            texts.append(t)
    return clamp_content("\n".join(texts))


def fetch_aljazeera(url: str) -> str | None:
    try:
        html = fetch(url)
    except Exception:
        return None
    block = re.search(
        r'class="wysiwyg[^"]*"[^>]*>(.*?)</div>\s*<div', html, re.S
    )
    if not block:
        block = re.search(r'class="wysiwyg[^"]*"[^>]*>(.*)', html, re.S)
    if not block:
        return None
    paras = re.findall(r"<p[^>]*>(.*?)</p>", block.group(1), re.S)
    texts = [strip_html(p) for p in paras if len(strip_html(p)) > 30]
    return clamp_content("\n".join(texts))


def fetch_guardian(url: str) -> str | None:
    try:
        html = fetch(url)
    except Exception:
        return None
    article = re.search(r'<article[^>]*>(.*?)</article>', html, re.S)
    chunk = article.group(1) if article else html
    paras = re.findall(
        r'data-component="paragraph"[^>]*>.*?<p>(.*?)</p>', chunk, re.S
    )
    if not paras:
        paras = re.findall(r"<p>(.*?)</p>", chunk, re.S)
    texts: list[str] = []
    for p in paras:
        t = strip_html(p)
        if len(t) > 40 and "Continue reading" not in t:
            texts.append(t)
    return clamp_content("\n".join(texts))


def fetch_un(url: str) -> str | None:
    try:
        html = fetch(url)
    except Exception:
        return None
    paras = re.findall(
        r'<div class="field-item even">(.*?)</div>', html, re.S
    )
    if not paras:
        paras = re.findall(r"<p>(.*?)</p>", html, re.S)
    texts = [strip_html(p) for p in paras if len(strip_html(p)) > 40]
    return clamp_content("\n".join(texts))


def fetch_article(url: str) -> str | None:
    host = urllib.parse.urlparse(url).netloc.lower()
    if "chinanews.com" in host:
        return fetch_chinanews(url)
    if "bbc.co" in host:
        return fetch_bbc(url)
    if "aljazeera.com" in host:
        return fetch_aljazeera(url)
    if "theguardian.com" in host:
        return fetch_guardian(url)
    if "news.un.org" in host:
        return fetch_un(url)
    try:
        html = fetch(url)
    except Exception:
        return None
    return clamp_content(strip_html(html))


def tophub_baidu_titles() -> list[str]:
    try:
        req = urllib.request.Request(
            "https://tophub.today/n/Jb0vmloB1G",
            headers={"User-Agent": TOPHUB_UA},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    seen: set[str] = set()
    titles: list[str] = []
    for m in re.finditer(
        r'href="https://www\.baidu\.com/s\?wd=([^"]+)"[^>]*>([^<]*)', html
    ):
        label = unescape(urllib.parse.unquote(m.group(2).strip() or m.group(1)))
        label = urllib.parse.unquote(m.group(1)) if not label else label
        if label in seen or len(label) < 6:
            continue
        if GOSSIP_RE.search(label):
            continue
        seen.add(label)
        titles.append(label)
    return titles[:40]


def tophub_it_titles() -> list[tuple[str, str]]:
    try:
        req = urllib.request.Request(
            "https://tophub.today/n/74Kvx59dkx",
            headers={"User-Agent": TOPHUB_UA},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    out: list[tuple[str, str]] = []
    for m in re.finditer(
        r'<a[^>]+href="(https://www\.ithome\.com[^"]+)"[^>]*>([^<]+)</a>', html
    ):
        title = unescape(m.group(2).strip())
        if len(title) > 8 and not GOSSIP_RE.search(title):
            out.append((title, m.group(1)))
    return out[:15]


def score_domestic(title: str, path_hint: str) -> int:
    score = 0
    if "/gn/" in path_hint or "/sh/" in path_hint or "/cj/" in path_hint:
        score += 3
    if "/gj/" in path_hint:
        score += 2
    if "/ty/" in path_hint:
        score += 2
    if "/life/" in path_hint or "iframe" in path_hint:
        score -= 5
    if "新闻早报" in title:
        score -= 10
    if GOSSIP_RE.search(title) or SUBJECTIVE_RE.search(title):
        score -= 8
    return score


def pick_domestic() -> list[dict[str, Any]]:
    rss_items = parse_rss(
        "https://www.chinanews.com.cn/rss/scroll-news.xml", "中国新闻网"
    )
    hot = tophub_baidu_titles()
    hot_set = set(hot)

    candidates: list[dict[str, Any]] = []
    for it in rss_items:
        url = it["url"]
        if "iframe" in url:
            continue
        title = it["title"]
        if GOSSIP_RE.search(title) or SUBJECTIVE_RE.search(title):
            continue
        sc = score_domestic(title, url)
        for h in hot_set:
            if h[:8] in title or title[:8] in h:
                sc += 4
                break
        candidates.append(
            {
                "title": title,
                "url": url,
                "source": "中国新闻网",
                "region": "domestic",
                "score": sc,
            }
        )

    # IT之家 from tophub
    for title, url in tophub_it_titles():
        candidates.append(
            {
                "title": title,
                "url": url,
                "source": "IT之家",
                "region": "domestic",
                "score": 5,
            }
        )

    # dedupe by url
    by_url: dict[str, dict[str, Any]] = {}
    for c in sorted(candidates, key=lambda x: -x["score"]):
        by_url.setdefault(c["url"], c)

    picked: list[dict[str, Any]] = []
    for c in list(by_url.values()):
        if len(picked) >= 35:
            break
        picked.append(c)
    return picked[:30] if len(picked) >= 30 else picked


SOFT_INTL_RE = re.compile(
    r"student debt|Inside the room|AI is creating|Bake Off|Brummie accent|"
    r"horror film|YouTube to|saving £|Green Party MP|paralysed in 30ft|"
    r"working from Singapore|wins unfair dismissal|"
    r"depression for 14 years|Northern Lights stun|Why are they resuming",
    re.I,
)
HARD_NEWS_RE = re.compile(
    r"kill|attack|war|hurricane|sanction|ICC|UN |WHO |Gaza|Ukraine|Russia|"
    r"Houthi|Saudi|Trump|Zelensky|Nobel|plague|volcano|execution|Sudan|"
    r"Israel|Iran|Yemen|Mexico|Philippines|trade|Security Council",
    re.I,
)


def intl_article_ok(title: str, url: str) -> bool:
    if "/sports/" in url or "/sport/" in url:
        return False
    if "/video/" in url and "newsfeed" in url:
        return False
    if "liveblog" in url:
        return False
    if GOSSIP_RE.search(title):
        return False
    if SOFT_INTL_RE.search(title):
        return False
    return True


def intl_score(title: str, source: str) -> int:
    score = 0
    if HARD_NEWS_RE.search(title):
        score += 8
    if source in ("UN News", "Al Jazeera"):
        score += 2
    if source == "BBC":
        score += 1
    if re.search(r"How |Why |My ", title):
        score -= 4
    return score


def pick_international() -> list[dict[str, Any]]:
    feeds = [
        ("https://feeds.bbci.co.uk/news/rss.xml", "BBC"),
        ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"),
        ("https://www.theguardian.com/world/rss", "The Guardian"),
        ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "UN News"),
    ]
    candidates: list[dict[str, Any]] = []
    for rss_url, source in feeds:
        for it in parse_rss(rss_url, source):
            url = it["url"].split("#")[0]
            if not intl_article_ok(it["title"], url):
                continue
            candidates.append(
                {
                    "title_en": it["title"],
                    "url": url,
                    "source": source,
                    "region": "international",
                    "rss_desc": it.get("rss_desc", ""),
                    "score": intl_score(it["title"], source),
                }
            )

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for c in sorted(candidates, key=lambda x: -x["score"]):
        key = c["url"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)

    # diversify sources: at least 3 each for major outlets when possible
    by_source: dict[str, list[dict[str, Any]]] = {}
    for c in unique:
        by_source.setdefault(c["source"], []).append(c)
    picked: list[dict[str, Any]] = []
    quotas = {"Al Jazeera": 6, "BBC": 6, "The Guardian": 4, "UN News": 4}
    for src, limit in quotas.items():
        for c in by_source.get(src, [])[:limit]:
            if c not in picked:
                picked.append(c)
    for c in unique:
        if len(picked) >= 20:
            break
        if c not in picked:
            picked.append(c)
    return picked[:20]


def apply_intl_zh(item: dict[str, Any], content_en: str | None) -> dict[str, Any]:
    url = item["url"]
    zh = INTL_ZH.get(url, {})
    title = zh.get("title") or item.get("title_en", "")
    content = zh.get("content")
    if not content and content_en and zh.get("use_en_as_zh"):
        content = content_en
    return {
        "title": title,
        "source": item["source"],
        "region": "international",
        "url": url,
        "content": clamp_content(content),
    }


def build(output: Path, intl_zh_path: Path | None) -> list[dict[str, Any]]:
    global INTL_ZH
    if intl_zh_path and intl_zh_path.is_file():
        INTL_ZH = json.loads(intl_zh_path.read_text(encoding="utf-8"))

    domestic_raw = pick_domestic()
    intl_raw = pick_international()

    # pad domestic to 30 if needed from more rss
    if len(domestic_raw) < 30:
        extra = parse_rss(
            "https://www.chinanews.com.cn/rss/scroll-news.xml", "中国新闻网"
        )
        for it in extra:
            if len(domestic_raw) >= 30:
                break
            if it["url"] in {d["url"] for d in domestic_raw}:
                continue
            if GOSSIP_RE.search(it["title"]):
                continue
            domestic_raw.append(
                {
                    "title": it["title"],
                    "url": it["url"],
                    "source": "中国新闻网",
                    "region": "domestic",
                }
            )

    intl_raw = intl_raw[:20]
    domestic_raw = domestic_raw[:30]

    result: list[dict[str, Any]] = []
    rank = 1

    for d in domestic_raw:
        print(f"fetch domestic {rank}: {d['url']}", file=sys.stderr)
        content = fetch_article(d["url"])
        if not content and d.get("rss_desc"):
            content = clamp_content(d["rss_desc"])
        result.append(
            {
                "rank_no": rank,
                "title": d["title"],
                "source": d["source"],
                "region": "domestic",
                "url": d["url"],
                "content": content,
            }
        )
        rank += 1
        time.sleep(0.15)

    for it in intl_raw:
        print(f"fetch intl {rank}: {it['url']}", file=sys.stderr)
        content_en = fetch_article(it["url"])
        if not content_en:
            desc = it.get("rss_desc") or ""
            content_en = clamp_content(desc) if desc else None
        row = apply_intl_zh(it, content_en)
        row["rank_no"] = rank
        result.append(row)
        rank += 1
        time.sleep(0.15)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="data/news_{date}.json".format(
            date=__import__("datetime").datetime.now(
                __import__("zoneinfo").ZoneInfo("Asia/Shanghai")
            ).date().isoformat()
        ),
    )
    parser.add_argument("--intl-zh", help="JSON map url -> {title, content}")
    args = parser.parse_args()
    out = Path(args.output)
    intl_zh = Path(args.intl_zh) if args.intl_zh else Path(
        out.with_name(out.stem + "_intl_zh.json")
    )
    if not intl_zh.is_file():
        intl_zh = None
    build(out, intl_zh)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
