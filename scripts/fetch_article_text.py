#!/usr/bin/env python3
"""Fetch article plain text via trafilatura."""
import sys
import trafilatura

def main():
    url = sys.argv[1]
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        print("", end="")
        return 1
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not text:
        print("", end="")
        return 1
    print(text.strip())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
