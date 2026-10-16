#!/usr/bin/env python3
"""Translate international rows in daily JSON to Chinese (title + content)."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from refetch_json_content import translate  # noqa: E402

DROP_TITLE = re.compile(
    r"天塌了|最惨|荒谬|八卦|明星离婚|演唱会门票|"
    r"高钾食物|流感疫苗如何打|深海鱼还能不能吃|"
    r"一种容易让牙齿掉光的病|关节疼痛，补充氨糖",
    re.I,
)


def needs_zh(text: str) -> bool:
    if not text:
        return False
    zh = len(re.findall(r"[\u4e00-\u9fff]", text))
    return zh < len(text) * 0.2


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    items = [x for x in items if not DROP_TITLE.search(x.get("title", ""))]

    for row in items:
        if row.get("region") != "international":
            continue
        title = row.get("title", "")
        if needs_zh(title):
            row["title"] = translate(title)
            time.sleep(0.8)
        content = row.get("content") or ""
        if needs_zh(content):
            row["content"] = translate(content)
            time.sleep(1.0)

    dom = [x for x in items if x["region"] == "domestic"][:30]
    intl = [x for x in items if x["region"] == "international"][:20]
    final = dom + intl
    for i, row in enumerate(final, 1):
        row["rank_no"] = i

    path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"translated intl; total={len(final)} dom={len(dom)} intl={len(intl)}")
    return 0 if len(final) == 50 else 1


if __name__ == "__main__":
    raise SystemExit(main())
