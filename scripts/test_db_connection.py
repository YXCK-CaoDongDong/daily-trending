#!/usr/bin/env python3
"""Test MySQL connectivity using environment variables."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pymysql


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
    required = ("MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}", file=sys.stderr)
        return 1
    port = int(os.environ.get("MYSQL_PORT", "3306"))
    try:
        conn = pymysql.connect(
            host=os.environ["MYSQL_HOST"],
            port=port,
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            database=os.environ["MYSQL_DATABASE"],
            charset="utf8mb4",
            connect_timeout=10,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        print(
            f"OK: connected to {os.environ['MYSQL_HOST']}:{port}/"
            f"{os.environ['MYSQL_DATABASE']}"
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
