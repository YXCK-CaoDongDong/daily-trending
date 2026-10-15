#!/usr/bin/env python3
"""Fetch and extract article text from news URLs."""

from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
JUNK_RE = re.compile(
    r"页面没有找到|将会带您进入新浪首页|page not found|"
    r"sorry,\s*we can't find the page|404 not found|access denied|"
    r"请先登录|登录后查看|下载客户端|无障碍",
    re.I,
)
TITLE_STOP = {
    "正式", "通报", "处理", "结果", "关于", "今日", "今天", "最新",
    "消息", "报道", "新闻", "宣布", "确认", "相关", "情况", "问题",
}


def _pick_encoding(raw: bytes, declared: str | None) -> str:
    for enc in (declared, "utf-8", "gb2312", "gbk", "gb18030"):
        if not enc:
            continue
        try:
            text = raw.decode(enc, errors="strict")
            cn = len(re.findall(r"[\u4e00-\u9fff]", text[:8000]))
            if cn >= 20 or enc == "utf-8":
                return enc
        except UnicodeDecodeError:
            continue
    return declared or "utf-8"


def _markers(title: str) -> list[str]:
    out: list[str] = []
    for seq in re.findall(r"[\u4e00-\u9fff]{4,}", title):
        for i in range(len(seq) - 1):
            bg = seq[i : i + 2]
            if bg not in TITLE_STOP:
                out.append(bg)
    for tok in re.findall(r"[\u4e00-\u9fff]{2,3}|[A-Za-z]{3,}|\d{2,}", title):
        if tok not in TITLE_STOP:
            out.append(tok)
    seen: set[str] = set()
    deduped: list[str] = []
    for m in out:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped


def _match_title(content: str, title: str) -> bool:
    markers = _markers(title)
    if not markers:
        return True
    low = content.casefold()
    hits = sum(1 for m in markers if m.casefold() in low)
    return hits >= min(2, len(markers))


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
        tag.decompose()

    host = urlparse(url).netloc
    selectors: list[str] = []

    if "news.cn" in host or "xinhuanet.com" in host:
        selectors = ["#detail", ".article", "#detailContent", ".main-article"]
    elif "people.com.cn" in host:
        selectors = [".rm_txt_con", "#rwb_zw", ".article-content", ".box_con"]
    elif "thepaper.cn" in host:
        selectors = [".news_txt", ".index_txt", "article"]
    elif "chinanews.com.cn" in host:
        selectors = [".left_zw", ".content_desc", "#cont_1_1_2"]
    elif "cctv.com" in host:
        selectors = [".content_area", "#content_area", ".cnt_bd"]
    elif "gov.cn" in host:
        selectors = [".pages_content", "#UCAP-CONTENT", ".article"]
    elif "huanqiu.com" in host:
        selectors = [".article", ".la_con"]
    elif "caixin.com" in host:
        selectors = [".text-box", ".content", "article"]
    elif "bbc.com" in host or "bbc.co.uk" in host:
        selectors = ["article", "[data-component='text-block']", ".ssrcss-11r1y41-RichTextComponentWrapper"]
    elif "reuters.com" in host:
        selectors = ["[data-testid='paragraph']", "article", ".article-body__content"]
    elif "apnews.com" in host:
        selectors = [".RichTextStoryBody", "article", ".Page-content"]
    elif "aljazeera.com" in host:
        selectors = [".wysiwyg", "article"]
    elif "theguardian.com" in host:
        selectors = ["#maincontent", "article", ".article-body-commercial-selector"]
    elif "news.un.org" in host:
        selectors = [".field-name-body", ".story-content", "article", ".content"]
    elif "cnr.cn" in host:
        selectors = [".article-content", ".TRS_Editor", "article"]
    elif "bjnews.com.cn" in host:
        selectors = [".article", ".content", "article"]
    elif "jiemian.com" in host:
        selectors = [".article-content", ".article", "article"]
    elif "jcrb.com" in host:
        selectors = [".article", ".content", "article"]
    elif "eeo.com.cn" in host:
        selectors = [".article", ".content", "article"]
    elif "ce.cn" in host:
        selectors = [".article", ".content", "article"]
    elif "china.com" in host:
        selectors = [".article", ".content", "article"]
    elif "yangtse.com" in host:
        selectors = [".article", ".content", "article"]
    else:
        selectors = ["article", ".article", ".content", ".post-content", "main"]

    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            paras = [p.get_text(" ", strip=True) for p in node.find_all(["p", "div"]) if p.get_text(strip=True)]
            if not paras:
                paras = [node.get_text("\n", strip=True)]
            body = _clean("\n\n".join(p for p in paras if len(p) > 15))
            if len(body) >= 80:
                return body[:20000]

    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]
    return _clean("\n\n".join(paras))[:20000]


def fetch(url: str, title: str = "") -> dict:
    result = {"url": url, "content": "", "error": None}
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
        enc = _pick_encoding(r.content, r.encoding)
        html = r.content.decode(enc, errors="replace")
        if JUNK_RE.search(html[:5000]):
            result["error"] = "junk_page"
            return result
        content = extract(html, url)
        if len(content) < 80:
            result["error"] = "too_short"
            return result
        if title and not _match_title(content, title):
            result["error"] = "title_mismatch"
            return result
        result["content"] = content
    except Exception as e:
        result["error"] = str(e)
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fetch_article.py <url> [title]", file=sys.stderr)
        return 1
    url = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else ""
    print(json.dumps(fetch(url, title), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
