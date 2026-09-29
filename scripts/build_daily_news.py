#!/usr/bin/env python3
"""Fetch article content and build daily news JSON."""

from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen

MIN_CONTENT = 80
MAX_CONTENT = 20000

JUNK_RE = re.compile(
    r"页面没有找到|404|Page not found|登录|下载客户端|账号设置",
    re.I,
)


def fetch_url(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; daily-trending/1.0)"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def extract_news_cn(html: str) -> tuple[str, str]:
    title_m = re.search(r"<title>([^<]+)</title>", html)
    title = title_m.group(1).strip() if title_m else ""
    body_m = re.search(r'id="detail"[^>]*>(.*)', html, re.S)
    if not body_m:
        body_m = re.search(r'<div class="article">(.*?)</div>', html, re.S)
    if not body_m:
        return title, ""
    chunk = body_m.group(1)
    chunk = re.split(r'<div class="editor"', chunk, maxsplit=1)[0]
    text = re.sub(r"<script[^>]*>.*?</script>", "", chunk, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(re.sub(r"\s+", " ", text)).strip()
    return title, text


def extract_chinanews(html: str) -> tuple[str, str]:
    title_m = re.search(r"<title>([^<]+)</title>", html)
    title = title_m.group(1).replace("-中新网", "").strip() if title_m else ""
    body_m = re.search(r'<div class="left_zw">(.*?)</div>\s*<div class="clear">', html, re.S)
    if not body_m:
        body_m = re.search(r'<div class="content_desc">(.*?)</div>', html, re.S)
    if not body_m:
        return title, ""
    text = re.sub(r"<script[^>]*>.*?</script>", "", body_m.group(1), flags=re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(re.sub(r"\s+", " ", text)).strip()
    text = re.sub(r"【编辑:.*?】$", "", text).strip()
    return title, text


def sanitize(content: str, title: str, strict_title: bool = True) -> str:
    if not content or len(content) < MIN_CONTENT:
        return ""
    if JUNK_RE.search(content):
        return ""
    if strict_title:
        markers = [t for t in re.findall(r"[\u4e00-\u9fff]{2,}", title) if len(t) >= 2][:5]
        if markers and not any(m in content for m in markers):
            return ""
    if len(content) > MAX_CONTENT:
        content = content[:MAX_CONTENT]
    return content


def process_item(item: dict) -> dict:
    preset = (item.get("content") or "").strip()
    content = preset
    if not content and item.get("url"):
        try:
            html = fetch_url(item["url"])
            if "chinanews.com" in item["url"]:
                fetched_title, fetched_content = extract_chinanews(html)
                if fetched_title:
                    item["_fetched_title"] = fetched_title.replace("-中新网", "").strip()
                content = fetched_content
            elif "news.cn" in item["url"]:
                fetched_title, fetched_content = extract_news_cn(html)
                if fetched_title:
                    item["_fetched_title"] = fetched_title.strip()
                content = fetched_content
            else:
                # strip tags for other sites if needed
                text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S)
                text = re.sub(r"<[^>]+>", " ", text)
                content = unescape(re.sub(r"\s+", " ", text)).strip()
        except Exception as exc:
            print(f"WARN fetch {item.get('rank_no')}: {exc}", file=sys.stderr)
    fetched_title = item.pop("_fetched_title", None)
    check_title = fetched_title or item.get("title", "")
    strict = not fetched_title and not (item.get("region") == "international" and preset)
    cleaned = sanitize(content, check_title, strict_title=strict)
    if not cleaned and preset:
        cleaned = sanitize(preset, check_title, strict_title=False)
    item["content"] = cleaned
    return item


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/news_items_seed.json")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/news_2026-09-29.json")
    items = json.loads(src.read_text(encoding="utf-8"))
    result = [process_item(dict(i)) for i in items]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    empty = sum(1 for r in result if not r.get("content"))
    print(f"wrote {len(result)} items to {out}, empty_content={empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
