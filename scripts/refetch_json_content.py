#!/usr/bin/env python3
"""Refetch empty content fields in daily news JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from build_daily_json import Candidate, enrich

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    args = p.parse_args()
    path = Path(args.json)
    items = json.loads(path.read_text(encoding="utf-8"))
    updated = 0
    for row in items:
        if (row.get("content") or "").strip():
            continue
        c = Candidate(
            title=row["title"],
            source=row.get("source") or "",
            url=row.get("url") or "",
            region=row.get("region") or "domestic",
        )
        if not c.url:
            continue
        try:
            ec = enrich(c)
        except Exception as exc:
            print(f"rank {row.get('rank_no')}: {exc}", file=sys.stderr)
            continue
        if ec.content:
            row["content"] = ec.content
            if ec.title and ec.region == "international":
                row["title"] = ec.title
            updated += 1
            print(f"filled rank {row.get('rank_no')}", file=sys.stderr)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    with_content = sum(1 for x in items if (x.get("content") or "").strip())
    print(f"updated {updated}, total with content {with_content}/{len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
