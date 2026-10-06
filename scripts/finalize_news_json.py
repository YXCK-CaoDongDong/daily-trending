#!/usr/bin/env python3
"""Build final news JSON from fetched draft (translate international bodies to Chinese)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTL_ZH = Path(ROOT / "data" / "intl_zh_content.json")


def clean_domestic(text: str) -> str:
    text = re.sub(r"【编辑[:：][^】]+】\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:20000]


def main() -> int:
    fetched = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    intl_map = json.loads(INTL_ZH.read_text(encoding="utf-8")) if INTL_ZH.is_file() else {}
    out = []
    for row in fetched:
        item = {
            "rank_no": row["rank_no"],
            "title": row["title"],
            "source": row["source"],
            "region": row["region"],
            "url": row["url"],
            "content": "",
        }
        raw = (row.get("content_raw") or "").strip()
        if row["region"] == "international":
            item["content"] = (intl_map.get(str(row["rank_no"])) or "").strip()
        else:
            item["content"] = clean_domestic(raw) if raw else ""
        out.append(item)
    dest = Path(sys.argv[2])
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
