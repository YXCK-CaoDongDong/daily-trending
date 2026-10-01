#!/usr/bin/env python3
"""Refetch and translate international items in daily JSON with rate limiting."""
import json
import re
import sys
import time
from pathlib import Path

from build_daily_json import normalize_content, fetch_content
from translate_util import translate_en_to_zh as translate_en


def main() -> int:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data:
        if item.get("region") != "international":
            continue
        url = item["url"]
        raw = fetch_content(url)
        if not raw:
            print("fetch fail", url, file=sys.stderr)
            continue
        zh = translate_en(raw)
        item["content"] = normalize_content(zh, item["title"])
        print(item["rank_no"], len(item["content"]), url, file=sys.stderr)
        time.sleep(1)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
