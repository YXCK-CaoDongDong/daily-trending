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
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

try:
    import pymysql
except ImportError as exc:
    raise SystemExit(
        "pymysql is not installed. Run: python -m pip install -r requirements.txt"
    ) from exc

TZ = ZoneInfo("Asia/Shanghai")
MAX_CONTENT_LEN = 20000
MIN_CONTENT_LEN = 80
LINE_RE = re.compile(
    r"^\s*(\d+)\.\s*(.+?)(?:（([^）]+)）|\(([^)]+)\))\s*$"
)
JUNK_CONTENT_RE = re.compile(
    r"页面没有找到|将会带您进入新浪首页|page not found|"
    r"sorry,\s*we can't find the page|"
    r"the page you're looking for can't be found|"
    r"404 not found|access denied|403 forbidden|"
    r"下载客户端|无障碍|账号设置|我的关注|我的收藏|退出登录|"
    r"请先登录|登录后查看|个人中心|"
    r"找不到该页面|无法找到该页面|页面未找到",
    re.IGNORECASE,
)
TITLE_STOPWORDS = {
    "正式", "通报", "处理", "结果", "关于", "今日", "今天", "最新",
    "消息", "报道", "新闻", "宣布", "确认", "相关", "情况", "问题",
}
DOMESTIC_HOST_SUFFIXES = (
    ".cn",
    "news.cn",
    "xinhuanet.com",
    "people.com.cn",
    "cctv.com",
    "chinanews.com",
    "chinanews.com.cn",
    "huanqiu.com",
    "cankaoxiaoxi.com",
    "caixin.com",
    "jiemian.com",
    "thepaper.cn",
    "guancha.cn",
    "yicai.com",
    "21jingji.com",
    "weibo.com",
    "zhihu.com",
    "baidu.com",
    "toutiao.com",
    "163.com",
    "qq.com",
    "sina.com.cn",
    "sina.cn",
    "chinadaily.com.cn",
    "chinapress.com.my",
    "tophub.today",
)
DOMESTIC_SOURCE_MARKERS = (
    "新华",
    "人民网",
    "人民日报",
    "观察者",
    "澎湃",
    "环球",
    "参考消息",
    "中国日报",
    "央视",
    "中新网",
    "光明网",
    "中国政府",
    "商务部",
    "百度",
    "知乎",
    "微博",
    "网易",
    "经济观察",
    "中国报",
    "36氪",
    "虎嗅",
    "今日头条",
)


def _optional_str(row: dict[str, Any], key: str, max_len: int | None = None) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if max_len is not None and len(text) > max_len:
        return text[:max_len]
    return text


def _title_markers(title: str) -> list[str]:
    markers: list[str] = []
    for token in re.findall(r"[\u4e00-\u9fff]{2,4}|[A-Za-z]{3,}|\d{2,}", title):
        if token in TITLE_STOPWORDS:
            continue
        markers.append(token)
    return list(dict.fromkeys(markers))


def is_junk_content(content: str | None, title: str | None = None) -> bool:
    if not content:
        return False
    text = content.strip()
    if len(text) < MIN_CONTENT_LEN:
        return True
    if JUNK_CONTENT_RE.search(text):
        return True
    if title:
        markers = _title_markers(title)
        if markers and not any(marker.casefold() in text.casefold() for marker in markers):
            return True
    return False


def _host_from_url(url: str | None) -> str | None:
    if not url:
        return None
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def is_domestic_origin(url: str | None, source: str | None = None) -> bool:
    host = _host_from_url(url)
    if host:
        if host.endswith(".cn"):
            return True
        for suffix in DOMESTIC_HOST_SUFFIXES:
            suffix = suffix.lstrip(".")
            if host == suffix or host.endswith("." + suffix):
                return True
    if source:
        return any(marker in source for marker in DOMESTIC_SOURCE_MARKERS)
    return False


def sanitize_content(content: str | None, title: str | None = None) -> str | None:
    if not content:
        return None
    text = content.strip()
    if is_junk_content(text, title):
        return None
    if len(text) > MAX_CONTENT_LEN:
        return text[:MAX_CONTENT_LEN]
    return text


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


def require_mysql_env() -> None:
    required = (
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE",
    )
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise SystemExit(
            "missing MySQL env: " + ", ".join(missing)
            + ". Set them in Cloud Agents Secrets."
        )
    print(
        "mysql target "
        f"{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/"
        f"{os.environ['MYSQL_DATABASE']} user={os.environ['MYSQL_USER']}",
        file=sys.stderr,
    )


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
                "url": None,
                "region": None,
                "raw_line": line.strip(),
                "content": None,
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
        source = _optional_str(row, "source")
        url = _optional_str(row, "url", 2048)
        region = _optional_str(row, "region")
        if region == "international" and is_domestic_origin(url, source):
            print(
                f"skip international item {i}: domestic origin {source or ''} {url or ''}",
                file=sys.stderr,
            )
            continue
        items.append(
            {
                "run_date": str(row.get("run_date") or run_date.isoformat()),
                "rank_no": int(row.get("rank_no") or i),
                "title": title,
                "source": source,
                "url": url,
                "region": region,
                "raw_line": _optional_str(row, "raw_line"),
                "content": sanitize_content(
                    _optional_str(row, "content", MAX_CONTENT_LEN),
                    title,
                ),
            }
        )
    return items


UPSERT_SQL = """
INSERT INTO daily_trending_news
  (run_date, rank_no, title, source, url, region, raw_line, content)
VALUES
  (%(run_date)s, %(rank_no)s, %(title)s, %(source)s, %(url)s, %(region)s, %(raw_line)s, %(content)s)
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  source = VALUES(source),
  region = VALUES(region),
  raw_line = VALUES(raw_line),
  url = COALESCE(NULLIF(VALUES(url), ''), url),
  content = COALESCE(NULLIF(VALUES(content), ''), content)
"""


def clean_junk_rows(run_date: date | None = None) -> int:
    sql = "SELECT id, title, content FROM daily_trending_news WHERE content IS NOT NULL"
    params: tuple[Any, ...] = ()
    if run_date is not None:
        sql += " AND run_date = %s"
        params = (run_date.isoformat(),)
    cleared = 0
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            for row_id, title, content in rows:
                if is_junk_content(content, title):
                    cur.execute(
                        "UPDATE daily_trending_news SET content = NULL WHERE id = %s",
                        (row_id,),
                    )
                    cleared += 1
        conn.commit()
    return cleared


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
    require_mysql_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="run_date YYYY-MM-DD, default today Asia/Shanghai")
    parser.add_argument("--json", help="path to JSON file")
    parser.add_argument("--text", help="path to plain text list (SKILL output style)")
    parser.add_argument(
        "--clean-junk",
        action="store_true",
        help="set existing junk/mismatched content to NULL and exit",
    )
    args = parser.parse_args()

    run_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(TZ).date()
    )

    if args.clean_junk:
        n = clean_junk_rows(run_date if args.date else None)
        print(f"cleared {n} junk content rows")
        return 0

    if args.json:
        payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
        items = normalize_items(payload, run_date)
    elif args.text:
        items = parse_text(Path(args.text).read_text(encoding="utf-8"), run_date)
    else:
        payload = json.load(sys.stdin)
        items = normalize_items(payload, run_date)

    if not items:
        print(f"ERROR: no items to upsert for {run_date.isoformat()}", file=sys.stderr)
        return 1
    n = upsert(items)
    print(f"upserted {n} rows for {run_date.isoformat()}")
    if n == 0:
        print("ERROR: upsert wrote 0 rows", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
