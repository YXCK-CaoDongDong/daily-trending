#!/usr/bin/env python3
"""Post-process daily news JSON: dedupe, filter, refetch content, translate intl."""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from html import unescape
from pathlib import Path

# reuse extractors from build
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_daily_news import (  # noqa: E402
    SUBJECTIVE_RE,
    ENTERTAINMENT_RE,
    extract_article,
    fetch,
    ok_title,
    trim_content,
)

SKIP_TITLE_RE = re.compile(
    r"立人设|画大饼|套路三步|Breaking Bad|Tom Cruise film Digger|"
    r"bedbug|Qantas flight grounded after bedbug|Women's billion-dollar boom",
    re.I,
)


def translate_zh(text: str, max_chunk: int = 4500) -> str:
    if not text or re.search(r"[\u4e00-\u9fff]", text[:200]):
        return text
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return text
    tr = GoogleTranslator(source="auto", target="zh-CN")
    parts: list[str] = []
    chunk = text[:8000]
    for i in range(0, len(chunk), max_chunk):
        piece = chunk[i : i + max_chunk]
        for attempt in range(5):
            try:
                parts.append(tr.translate(piece))
                time.sleep(2.5)
                break
            except Exception:
                time.sleep(5 * (attempt + 1))
        else:
            parts.append(piece)
    return trim_content("\n\n".join(parts))


def refetch_item(item: dict) -> dict:
    body = extract_article(item["url"], item["region"])
    if body and len(body) >= 200:
        item["content"] = body
    return item


def dedupe_key(item: dict) -> str:
    t = re.sub(r"\s+", "", item["title"])[:40]
    return t


def main() -> int:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    data = json.loads(src.read_text(encoding="utf-8"))

    seen: set[str] = set()
    cleaned: list[dict] = []
    for row in data:
        if SKIP_TITLE_RE.search(row["title"]):
            continue
        if not ok_title(row["title"]) and row["region"] == "domestic":
            continue
        key = dedupe_key(row)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(row)

    domestic = [x for x in cleaned if x["region"] == "domestic"]
    intl = [x for x in cleaned if x["region"] == "international"]

    # backfill domestic from RSS if short
    if len(domestic) < 30:
        extra_xml = fetch("https://www.chinanews.com.cn/rss/china.xml") or ""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(extra_xml)
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title or not link or not ok_title(title):
                continue
            k = dedupe_key({"title": title})
            if k in seen:
                continue
            seen.add(k)
            domestic.append(
                {
                    "title": title,
                    "source": "中国新闻网",
                    "region": "domestic",
                    "url": link,
                    "content": "",
                }
            )
            if len(domestic) >= 30:
                break

    domestic = domestic[:30]
    intl = intl[:20]

    out: list[dict] = []
    for block in (domestic, intl):
        for item in block:
            item = refetch_item(dict(item))
            if item["region"] == "international":
                if re.search(r"^[A-Za-z]", item["title"]):
                    item["title"] = translate_zh(item["title"])
                if item.get("content") and not re.search(r"[\u4e00-\u9fff]{20}", item["content"][:500]):
                    # strip boilerplate lines before translate
                    raw = item["content"]
                    raw = re.sub(r"Image source,.*?\n", "", raw)
                    raw = re.sub(r"Published \d+.*?ago\n", "", raw)
                    raw = re.sub(r"Related topics.*", "", raw, flags=re.S)
                    item["content"] = translate_zh(raw[:6000])
            out.append(item)
            time.sleep(0.4)

    final = []
    for i, row in enumerate(out, start=1):
        final.append(
            {
                "rank_no": i,
                "title": row["title"],
                "source": row["source"],
                "region": row["region"],
                "url": row["url"],
                "content": row.get("content") or "",
            }
        )

    dst.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    filled = sum(1 for x in final if x["content"])
    print(f"postprocess: {len(final)} items, {filled} with content -> {dst}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
