#!/usr/bin/env python3
"""Add url/content columns to daily_trending_news if they are missing."""

from __future__ import annotations

import os
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
    conn = pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DATABASE", "shell-updater"),
        charset="utf8mb4",
        connect_timeout=10,
        autocommit=False,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW COLUMNS FROM daily_trending_news")
            cols = [row[0] for row in cur.fetchall()]
            print("before:", ",".join(cols))
            alters: list[str] = []
            if "url" not in cols:
                alters.append(
                    "ADD COLUMN `url` varchar(2048) DEFAULT NULL "
                    "COMMENT '原文链接' AFTER `source`"
                )
            if "content" not in cols:
                after_col = "raw_line" if "raw_line" in cols else "source"
                alters.append(
                    "ADD COLUMN `content` mediumtext DEFAULT NULL "
                    f"COMMENT '新闻正文（纯文本）' AFTER `{after_col}`"
                )
            if alters:
                cur.execute("ALTER TABLE `daily_trending_news` " + ", ".join(alters))
                conn.commit()
                print("migrated")
            else:
                print("already_up_to_date")
            cur.execute("SHOW COLUMNS FROM daily_trending_news")
            cols = [row[0] for row in cur.fetchall()]
            print("after:", ",".join(cols))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
