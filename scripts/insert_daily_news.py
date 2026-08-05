#!/usr/bin/env python3
"""Upsert daily trending news into shell-updater.daily_trending_news."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pymysql

TZ = ZoneInfo("Asia/Shanghai")
LINE_RE = re.compile(
    r"^\s*(\d+)\.\s*(.+?)(?:（([^）]+)）|\(([^)]+)\))\s*$"
)


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def db_conn():
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DATABASE", "shell-updater"),
        charset="utf8mb4",
        connect_timeout=10,
        read_timeout=60,
        write_timeout=60,
        autocommit=False,
    )


def parse_text(text: str, run_date: date) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in text.splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        rank_no = int(m.group(1))
        title = m.group(2).strip()
        source = (m.group(3) or m.group(4) or "").strip() or None
        items.append(
            {
                "run_date": run_date.isoformat(),
                "rank_no": rank_no,
                "title": title,
                "source": source,
                "region": None,
                "raw_line": line.strip(),
            }
        )
    return items


def normalize_items(raw: Any, run_date: date) -> list[dict[str, Any]]:
    if isinstance(raw, dict) and "items" in raw:
        raw = raw["items"]
    if not isinstance(raw, list):
        raise ValueError("JSON must be a list or {\"items\": [...]}")
    items: list[dict[str, Any]] = []
    for i, row in enumerate(raw, start=1):
        if isinstance(row, str):
            parsed = parse_text(f"{i}. {row}", run_date)
            if parsed:
                items.extend(parsed)
            continue
        if not isinstance(row, dict):
            raise ValueError(f"Invalid item at index {i}: {row!r}")
        title = str(row.get("title") or "").strip()
        if not title:
            raise ValueError(f"Missing title at index {i}")
        items.append(
            {
                "run_date": str(row.get("run_date") or run_date.isoformat()),
                "rank_no": int(row.get("rank_no") or i),
                "title": title,
                "source": (str(row["source"]).strip() if row.get("source") else None),
                "region": (str(row["region"]).strip() if row.get("region") else None),
                "raw_line": (str(row["raw_line"]).strip() if row.get("raw_line") else None),
            }
        )
    return items


UPSERT_SQL = """
INSERT INTO daily_trending_news
  (run_date, rank_no, title, source, region, raw_line)
VALUES
  (%(run_date)s, %(rank_no)s, %(title)s, %(source)s, %(region)s, %(raw_line)s)
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  source = VALUES(source),
  region = VALUES(region),
  raw_line = VALUES(raw_line)
"""


def upsert(items: list[dict[str, Any]]) -> int:
    if not items:
        return 0
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, items)
        conn.commit()
    return len(items)


def main() -> int:
    load_env_file(Path(__file__).resolve().parents[1] / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="run_date YYYY-MM-DD, default today Asia/Shanghai")
    parser.add_argument("--json", help="path to JSON file")
    parser.add_argument("--text", help="path to plain text list (SKILL output style)")
    args = parser.parse_args()

    run_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(TZ).date()
    )

    if args.json:
        payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
        items = normalize_items(payload, run_date)
    elif args.text:
        items = parse_text(Path(args.text).read_text(encoding="utf-8"), run_date)
    else:
        payload = json.load(sys.stdin)
        items = normalize_items(payload, run_date)

    n = upsert(items)
    print(f"upserted {n} rows for {run_date.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
