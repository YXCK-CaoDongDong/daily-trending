#!/usr/bin/env python3
"""Verify MySQL env vars and connectivity before ingest."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import pymysql
except ImportError:
    print("FAIL: pymysql not installed. Run: python -m pip install -r requirements.txt")
    raise SystemExit(1)


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def main() -> int:
    load_env_file(Path(__file__).resolve().parents[1] / ".env")
    required = (
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE",
    )
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        print("FAIL: missing env:", ", ".join(missing))
        return 1

    host = os.environ["MYSQL_HOST"]
    port = int(os.environ["MYSQL_PORT"])
    user = os.environ["MYSQL_USER"]
    database = os.environ["MYSQL_DATABASE"]
    print(f"checking {host}:{port}/{database} as {user}")

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=os.environ["MYSQL_PASSWORD"],
            database=database,
            charset="utf8mb4",
            connect_timeout=10,
        )
    except Exception as exc:
        print(f"FAIL: cannot connect to MySQL: {exc}")
        return 1

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.execute("SELECT COUNT(*) FROM daily_trending_news")
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT run_date, COUNT(*) FROM daily_trending_news "
                "GROUP BY run_date ORDER BY run_date DESC LIMIT 1"
            )
            latest = cur.fetchone()
        print(f"OK: connected, total_rows={total}, latest={latest}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
