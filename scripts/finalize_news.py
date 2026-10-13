#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

from intl_zh_2026_10_13 import apply_intl_zh

SKIP_DOM = re.compile(r"AI浪潮下|网络金融营销这些坑|立人设|画大饼")


def main() -> int:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    data = json.loads(src.read_text(encoding="utf-8"))
    domestic = [x for x in data if x["region"] == "domestic" and not SKIP_DOM.search(x["title"])]
    intl = [x for x in data if x["region"] == "international"]
    domestic = domestic[:30]
    intl = intl[:20]
    merged = domestic + intl
    merged = apply_intl_zh(merged)
    out = []
    for i, row in enumerate(merged, start=1):
        out.append(
            {
                "rank_no": i,
                "title": row["title"],
                "source": row["source"],
                "region": row["region"],
                "url": row["url"],
                "content": row.get("content") or "",
            }
        )
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"final {len(out)} items -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
