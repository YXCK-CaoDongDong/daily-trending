#!/usr/bin/env python3
"""Search chinanews.com.cn for article URLs by keyword."""
import re
import sys
import urllib.parse
import urllib.request

def search(keyword: str, limit: int = 5) -> list[tuple[str, str]]:
    q = urllib.parse.urlencode({"keyword": keyword})
    url = f"https://sou.chinanews.com.cn/search/news?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="replace")
    # links like https://www.chinanews.com.cn/gn/2026/10-03/1070xxxx.shtml
    pat = re.compile(
        r'href="(https?://www\.chinanews\.com\.cn/[^"]+\.shtml)"[^>]*>([^<]{8,120})',
        re.I,
    )
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for m in pat.finditer(html):
        link, title = m.group(1), re.sub(r"\s+", "", m.group(2))
        if link in seen:
            continue
        seen.add(link)
        out.append((title, link))
        if len(out) >= limit:
            break
    return out


if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "国庆"
    for t, u in search(kw):
        print(t[:80], u)
