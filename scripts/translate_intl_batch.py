#!/usr/bin/env python3
import json
import re
import sys
import time
from pathlib import Path

from deep_translator import GoogleTranslator


def clean_en(text: str) -> str:
    text = re.sub(r"Image source,.*?\n", "", text)
    text = re.sub(r"Figure caption,.*?\n", "", text)
    text = re.sub(r"Published \d+.*?\n", "", text)
    text = re.sub(r"Related topics.*", "", text, flags=re.S)
    text = re.sub(r"More on this story.*", "", text, flags=re.S)
    text = re.sub(r"To play this video.*?\n", "", text)
    return text.strip()


def tr(text: str) -> str:
    if not text:
        return ""
    if len(re.findall(r"[\u4e00-\u9fff]", text)) > len(text) * 0.15:
        return text
    tr_obj = GoogleTranslator(source="en", target="zh-CN")
    out = []
    chunk = clean_en(text)[:5500]
    for i in range(0, len(chunk), 4000):
        piece = chunk[i : i + 4000]
        for attempt in range(6):
            try:
                out.append(tr_obj.translate(piece))
                time.sleep(3)
                break
            except Exception:
                time.sleep(6 * (attempt + 1))
        else:
            out.append(piece)
    return "\n\n".join(out)


def main() -> int:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data:
        if row["region"] != "international":
            continue
        if re.match(r"^[A-Za-z]", row["title"]):
            row["title"] = tr(row["title"])
            time.sleep(2)
        if row.get("content"):
            row["content"] = tr(row["content"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("translated international items in", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
