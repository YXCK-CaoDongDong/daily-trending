#!/usr/bin/env python3
"""Translate international rows with offline Argos (en→zh). Refetch body if stub."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import argostranslate.translate as at

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from refetch_json_content import extract, fetch_html, matches_title  # noqa: E402


def needs_zh(text: str) -> bool:
    if not text:
        return False
    zh = len(re.findall(r"[\u4e00-\u9fff]", text))
    return zh < len(text) * 0.15


def tr(text: str) -> str:
    text = text.strip()
    if not text or not needs_zh(text):
        return text
    out: list[str] = []
    for i in range(0, len(text), 1000):
        out.append(at.translate(text[i : i + 1000], "en", "zh"))
    return "".join(out)


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    for row in items:
        if row.get("region") != "international":
            continue
        url = row["url"]
        title_en = row.get("title", "")
        c = row.get("content") or ""
        if len(c) < 200 or (needs_zh(c) and len(c) < 500):
            html = fetch_html(url)
            body = extract(url, html) if html else None
            if body and len(body) >= 200:
                c = body
        if needs_zh(title_en):
            row["title"] = tr(title_en)
        if c and needs_zh(c):
            row["content"] = tr(c)
        elif c and not needs_zh(c):
            row["content"] = c
        else:
            row["content"] = ""
        if len(row.get("content") or "") > 20000:
            row["content"] = row["content"][:20000]

    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    intl_bad = sum(
        1
        for x in items
        if x.get("region") == "international"
        and needs_zh((x.get("title", "") + (x.get("content") or "")[:400]))
    )
    empty = sum(1 for x in items if len(x.get("content") or "") < 80)
    print(f"argos_zh intl_still_en={intl_bad} empty={empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
