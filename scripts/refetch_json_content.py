#!/usr/bin/env python3
"""Per-item refetch article bodies; clear junk/duplicate/mismatch content."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
)

JUNK_CONTENT_RE = re.compile(
    r"页面没有找到|Page not found|404|can't find the page|"
    r"下载客户端|请先登录|立即注册|Sign up|Subscribe now|"
    r"access denied|Cookie settings",
    re.I,
)
JUNK_TITLE_RE = re.compile(
    r"立即注册|新闻早报|蛋白粉|明星|演唱会门票|天价黄牛|"
    r"性掠夺者|Kelly Clarkson|机械鸟|年度动物|海呕吐物|"
    r"我12岁了|每四分钟就有一辆车被盗",
    re.I,
)


def fetch_html(url: str) -> str | None:
    try:
        r = SESSION.get(url, timeout=30, allow_redirects=True)
        if r.status_code >= 400:
            return None
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except requests.RequestException:
        return None


def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract(url: str, html: str) -> str | None:
    host = (urlparse(url).hostname or "").lower()
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    selectors: list[str] = []
    if "chinanews.com.cn" in host:
        start = html.find("<!--正文start-->")
        end = html.find("<!--正文end-->")
        if start != -1 and end != -1:
            chunk = html[start:end]
            t = BeautifulSoup(chunk, "html.parser").get_text("\n", strip=True)
            if len(t) > 80:
                return clean_text(t)
        selectors = ["div.left_zw", "div.content"]
    elif host.endswith("gov.cn"):
        selectors = [".pages_content", "#UCAP-CONTENT", ".article-content"]
    elif "bbc.com" in host or "bbc.co.uk" in host:
        selectors = ["article", "[data-component='text-block']", "div[data-component='text-block']"]
    elif "theguardian.com" in host:
        selectors = ["#maincontent", "article"]
    elif "aljazeera.com" in host:
        selectors = ["main article", "div.article-p-wrapper", "article"]
    elif "apnews.com" in host:
        selectors = ["div.RichTextStoryBody", "article"]
    elif "reuters.com" in host:
        selectors = ["div[data-testid='paragraph']", "article"]
    elif "news.un.org" in host:
        selectors = ["div.field-item", "article"]
    elif "nhk.or.jp" in host:
        selectors = ["#maincol", "article", ".content--detail-body"]
    elif "yna.co.kr" in host:
        selectors = ["article", ".story-news"]
    elif "dw.com" in host:
        selectors = ["article", ".longText"]
    else:
        selectors = ["article", "main", ".article-content", ".content"]

    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = node.get_text("\n", strip=True)
            if len(text) > 120:
                return clean_text(text)

    paras = [p.get_text(strip=True) for p in soup.find_all("p")]
    paras = [p for p in paras if len(p) > 35]
    if len(paras) >= 4:
        return clean_text("\n".join(paras[:40]))
    return None


def title_markers(title: str) -> list[str]:
    stop = {"正式", "通报", "关于", "今日", "报道", "新闻", "宣布"}
    out = []
    for t in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}|\d{2,}", title):
        if t in stop:
            continue
        out.append(t)
    return out[:10]


def matches_title(content: str, title: str) -> bool:
    if re.search(r"[\u4e00-\u9fff]", title) and re.search(r"[\u4e00-\u9fff]", content):
        chunks = re.findall(r"[\u4e00-\u9fff]{4,}", title)
        if chunks and any(c in content for c in chunks[:6]):
            return True
    markers = title_markers(title)
    if not markers:
        return True
    hits = sum(1 for m in markers if m.casefold() in content.casefold())
    return hits >= max(1, len(markers) // 4)


def translate(text: str) -> str:
    if not text:
        return text
    if re.search(r"[\u4e00-\u9fff]", text) and len(re.findall(r"[\u4e00-\u9fff]", text)) > len(text) * 0.25:
        return text
    try:
        from deep_translator import GoogleTranslator  # type: ignore

        chunks = [text[i : i + 3500] for i in range(0, len(text), 3500)]
        out: list[str] = []
        tr = GoogleTranslator(source="auto", target="zh-CN")
        for chunk in chunks:
            for attempt in range(4):
                try:
                    out.append(tr.translate(chunk))
                    break
                except Exception:
                    time.sleep(2 + attempt * 2)
            else:
                out.append(chunk)
            time.sleep(1.2)
        return "".join(out)
    except Exception:
        return text


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    content_hashes: dict[str, int] = {}

    for row in items:
        title = row.get("title", "")
        url = row.get("url", "")
        if JUNK_TITLE_RE.search(title):
            row["title"] = ""
            row["content"] = ""
            continue
        html = fetch_html(url) if url else None
        body = extract(url, html) if html else None
        prev = row.get("content") or ""
        if not body or JUNK_CONTENT_RE.search(body) or not matches_title(body, title):
            row["content"] = prev if prev else ""
        else:
            if row.get("region") == "international" and not re.search(r"[\u4e00-\u9fff]", body[:300]):
                body = translate(body)
            if len(body) > 20000:
                body = body[:20000]
            row["content"] = body
        time.sleep(0.2)

    # drop junk titles
    items = [x for x in items if x.get("title")]

    # duplicate content -> clear later duplicates
    for row in items:
        c = row.get("content") or ""
        if len(c) < 200:
            continue
        h = hashlib.sha256(c.encode()).hexdigest()
        if h in content_hashes:
            row["content"] = ""
        else:
            content_hashes[h] = row["rank_no"]

    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    empty = sum(1 for x in items if not x.get("content"))
    print(f"refetched {len(items)} items, empty_content={empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
