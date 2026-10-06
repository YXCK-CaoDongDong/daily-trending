#!/usr/bin/env python3
"""Fetch article bodies for a list of {url, title, ...} items."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FETCH = ROOT / "scripts" / "fetch_article_content.py"


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    for row in items:
        url = row.get("url") or ""
        if not url:
            row["content_raw"] = ""
            continue
        proc = subprocess.run(
            [sys.executable, str(FETCH), url],
            capture_output=True,
            text=True,
            timeout=90,
        )
        row["content_raw"] = proc.stdout.strip() if proc.returncode == 0 else ""
        row["fetch_ok"] = bool(row["content_raw"]) and len(row["content_raw"]) >= 80
        print(
            f"rank {row.get('rank_no')}: {len(row['content_raw'])} chars ok={row.get('fetch_ok')}",
            file=sys.stderr,
        )
    out = path.with_suffix(".fetched.json")
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
