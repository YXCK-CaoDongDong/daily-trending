#!/usr/bin/env python3
"""Refetch international article bodies and translate to Chinese in small chunks."""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refetch_json_content import extract, fetch_html, matches_title

CHUNK = 450


def tr_chunk(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    q = urllib.parse.quote(text)
    url = f"https://api.mymemory.translated.net/get?q={q}&langpair=en|zh-CN"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        out = data.get("responseData", {}).get("translatedText", "")
        if "QUERY LENGTH" in out or "MYMEMORY WARNING" in out:
            return ""
        return out
    except Exception:
        return ""


def translate_long(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text) and len(re.findall(r"[\u4e00-\u9fff]", text)) > len(text) * 0.3:
        return text
    parts: list[str] = []
    for i in range(0, min(len(text), 3600), CHUNK):
        piece = text[i : i + CHUNK]
        zh = tr_chunk(piece)
        if zh:
            parts.append(zh)
        time.sleep(0.45)
    return "".join(parts)


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    for row in items:
        if row.get("region") != "international":
            continue
        url = row["url"]
        title = row["title"]
        html = fetch_html(url)
        body = extract(url, html) if html else None
        if not body or len(body) < 200:
            row["content"] = ""
            continue
        zh = translate_long(body)
        if len(zh) < 200:
            row["content"] = ""
        else:
            body_zh = f"{title}\n\n{zh}"
            if not matches_title(body_zh, title):
                row["content"] = ""
            else:
                row["content"] = body_zh[:20000]
        time.sleep(0.2)

    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    empty = sum(1 for x in items if x.get("region") == "international" and len(x.get("content") or "") < 80)
    print(f"fixed intl content; intl_empty={empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
