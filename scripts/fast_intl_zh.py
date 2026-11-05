#!/usr/bin/env python3
"""Fast Chinese for international rows via MyMemory API + backfill."""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

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
    return zh < len(text) * 0.15


def tr_en_zh(text: str, max_len: int = 4500) -> str:
    text = text.strip()
    if not text or not needs_zh(text):
        return text
    text = text[:max_len]
    try:
        q = urllib.parse.quote(text[:2000])
        url = f"https://api.mymemory.translated.net/get?q={q}&langpair=en|zh-CN"
        with urllib.request.urlopen(url, timeout=45) as resp:
            data = json.loads(resp.read().decode())
        out = data.get("responseData", {}).get("translatedText", "")
        if out and "MYMEMORY WARNING" not in out:
            return out
    except Exception:
        pass
    return text


def main() -> int:
    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    items = [x for x in items if not DROP_TITLE.search(x.get("title", ""))]

    for row in items:
        if row.get("region") != "international":
            continue
        if needs_zh(row.get("title", "")):
            row["title"] = tr_en_zh(row["title"], 500)
            time.sleep(0.35)
        c = row.get("content") or ""
        if needs_zh(c):
            # translate in two chunks if long
            if len(c) > 1800:
                a = tr_en_zh(c[:1800], 1800)
                time.sleep(0.5)
                b = tr_en_zh(c[1800:3600], 1800)
                row["content"] = (a + "\n" + b).strip()
            else:
                row["content"] = tr_en_zh(c)
            time.sleep(0.5)

    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"fast_zh done, items={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
