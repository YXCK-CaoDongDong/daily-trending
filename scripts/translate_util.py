#!/usr/bin/env python3
import time
import requests


def translate_en_to_zh(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    out: list[str] = []
    step = 450
    for i in range(0, min(len(text), 4000), step):
        chunk = text[i : i + step]
        for attempt in range(4):
            try:
                r = requests.get(
                    "https://api.mymemory.translated.net/get",
                    params={"q": chunk, "langpair": "en|zh-CN"},
                    timeout=45,
                )
                r.raise_for_status()
                part = r.json().get("responseData", {}).get("translatedText", "")
                if part:
                    out.append(part)
                    break
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        time.sleep(1.1)
    return "".join(out)
