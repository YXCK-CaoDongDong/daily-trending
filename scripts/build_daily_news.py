#!/usr/bin/env python3
"""Collect candidate articles from RSS and fetch full text."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FETCH = ROOT / "scripts" / "fetch_article_content.py"


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; daily-trending/1.0)"})
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_rss(url: str, limit: int = 80) -> list[dict]:
    raw = fetch_bytes(url)
    root = ET.fromstring(raw)
    items: list[dict] = []
    for item in root.findall(".//item")[:limit]:
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        if title_el is None or link_el is None:
            continue
        title = (title_el.text or "").strip()
        link = (link_el.text or "").strip()
        link = re.sub(r"&amp;", "&", link)
        desc = (desc_el.text or "").strip() if desc_el is not None else ""
        desc = re.sub(r"<[^>]+>", "", desc)
        items.append({"title": title, "url": link, "description": desc})
    return items


def article_text(url: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(FETCH), url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def main() -> int:
    feeds = {
        "chinanews": "https://www.chinanews.com.cn/rss/scroll-news.xml",
        "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "bbc_uk": "https://feeds.bbci.co.uk/news/uk/rss.xml",
        "aljazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "guardian_world": "https://www.theguardian.com/world/rss",
        "un_news": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    }
    out: dict[str, list] = {}
    for name, url in feeds.items():
        try:
            out[name] = parse_rss(url, 60)
        except Exception as e:
            out[name] = [{"error": str(e), "url": url}]
    Path(ROOT / "data").mkdir(exist_ok=True)
    Path(ROOT / "data" / "rss_candidates.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("wrote data/rss_candidates.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
