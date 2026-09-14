#!/usr/bin/env python3
"""Finalize daily news JSON from raw_fetched.json."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argostranslate.package
import argostranslate.translate
from bs4 import BeautifulSoup

from fetch_news_candidates import clean_text, extract_article_text, fetch

RAW_PATH = Path("/workspace/data/raw_fetched.json")
OUT_PATH = Path("/workspace/data/daily_news_2026-09-14.json")

BBC_REFETCH_RANKS = {31, 33, 34, 37}
RANK_21_URL = (
    "https://www.news.cn/politics/leaders/20260913/"
    "18e89880065048d19dc273c81c119999/c.html"
)
RANK_21_TITLE = (
    "习近平在新德里出席金砖国家领导人第十八次会晤第二阶段会议并发表重要讲话"
)

CHINANEWS_META_RE = re.compile(
    r"(?:^|\s)(?:"
    r"来源[：:][^。；\n]{0,80}|"
    r"作者[：:][^。；\n]{0,40}|"
    r"责任编辑[：:][^。；\n]{0,40}|"
    r"分享到[：:][^。；\n]{0,20}|"
    r"大字体\s*小字体|"
    r"【编辑[:：][^】]+】|"
    r"更多精彩内容请进入.*|"
    r"发表评论.*|"
    r"文明上网理性发言.*|"
    r"国内新闻精选[：:].*|"
    r"换一批"
    r")",
    re.S,
)
THEPAPER_FOOTER_RE = re.compile(
    r"(?:"
    r"责任编辑[：:].*|"
    r"澎湃[，,].*未经许可.*|"
    r"点击进入专题.*|"
    r"下载客户端.*|"
    r"©\s*20\d{2}.*澎湃新闻.*|"
    r"本文来源[：:].*"
    r")$",
    re.S,
)
BBC_BOILERPLATE_RE = [
    re.compile(r"To play this video you need to enable JavaScript in your browser\..*?(?=By |Published |\w)", re.I | re.S),
    re.compile(r"This video can not be played\s*", re.I),
    re.compile(r"(?:Image source|Image caption|Figure caption),?\s*[^.]*\.\s*", re.I),
    re.compile(r"Photograph:\s*[^.]+\.\s*", re.I),
    re.compile(r"View image in fullscreen\s*", re.I),
    re.compile(
        r"By [A-Z][^.]*?(?:Published|Updated) \d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}[^.]*\.\s*",
        re.I,
    ),
    re.compile(r"Published \d{1,2} (?:hours? )?ago\s*", re.I),
    re.compile(r"Updated \d{1,2} hour ago\s*", re.I),
    re.compile(r"Related topics[\s\S]*$", re.I),
    re.compile(r"More on this story[\s\S]*$", re.I),
    re.compile(r"Explore more on these topics[\s\S]*$", re.I),
    re.compile(r"Share Reuse this content\s*$", re.I),
    re.compile(r"skip past newsletter promotion[\s\S]*?after newsletter promotion\s*", re.I),
    re.compile(r"Read more\s*$", re.I),
]
ENGLISHISH_RE = re.compile(r"[A-Za-z]{4,}")
_ARGOS_READY = False


def ensure_argos_translator() -> None:
    global _ARGOS_READY
    if _ARGOS_READY:
        return
    try:
        argostranslate.translate.translate("test", "en", "zh")
    except Exception:
        argostranslate.package.update_package_index()
        pkg = next(
            p
            for p in argostranslate.package.get_available_packages()
            if p.from_code == "en" and p.to_code == "zh"
        )
        argostranslate.package.install_from_path(pkg.download())
    _ARGOS_READY = True


def extract_xinhuanet_content(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    best = ""
    for el in soup.find_all(["div", "p"]):
        text = clean_text(el.get_text(" ", strip=True))
        if "习近平" in text and "金砖" in text and len(text) > len(best):
            best = text
    return clean_xinhuanet_content(best)


def fetch_bbc_content(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        html = fetch(url)
        if html:
            content = extract_article_text(html, url)
            cleaned = clean_bbc_boilerplate(content)
            if cleaned:
                return cleaned
        if attempt + 1 < retries:
            time.sleep(1.5 * (attempt + 1))
    return ""


def clean_bbc_boilerplate(text: str) -> str:
    text = clean_text(text)
    for pattern in BBC_BOILERPLATE_RE:
        text = pattern.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_xinhuanet_content(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"新华社记者[^。；]{0,40}摄\s*", "", text)
    text = re.sub(r"责任编辑[：:][^。；\n]{0,40}", "", text)
    m = re.search(r"新华社[^。]+电[（(][^）)]*[）)]\s*", text)
    if m:
        text = text[m.end() :]
    half = len(text) // 2
    if half > 200 and text[:half] in text[half : half + len(text[:half]) + 5]:
        text = text[half:]
    return re.sub(r"\s+", " ", text).strip()


def clean_chinanews_content(text: str) -> str:
    text = clean_text(text)
    for marker in ("中新网", "中新社"):
        pos = text.find(marker)
        if 0 <= pos <= 200:
            text = text[pos:]
            break
    else:
        text = re.sub(
            r"^.{0,160}?(?:\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*)+",
            "",
            text,
            count=1,
        )
    text = CHINANEWS_META_RE.sub("", text)
    text = re.sub(r"【编辑[:：][^】]+】", "", text)
    text = re.sub(r"来源[：:][^。；\n]{0,80}", "", text)
    text = re.sub(r"作者[：:][^。；\n]{0,40}", "", text)
    text = re.sub(r"责任编辑[：:][^。；\n]{0,40}", "", text)
    text = re.sub(r"分享到[：:][^。；\n]{0,20}", "", text)
    text = re.sub(r"大字体\s*小字体", "", text)
    text = re.sub(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*", "", text)
    text = re.sub(r"^\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2}\s*", "", text)
    text = re.sub(r"国内新闻精选[：:][\s\S]*?(?:换一批|$)", "", text)
    text = re.sub(r"更多精彩内容请进入[\s\S]*$", "", text)
    text = re.sub(r"发表评论[\s\S]*$", "", text)
    text = re.sub(r"换一批\s*$", "", text)
    text = re.sub(
        r"(?:本报|中新网)[^。]{0,80}(?:记者|见习记者|通讯员)[^。]{0,120}\s*$",
        "",
        text,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_thepaper_content(text: str) -> str:
    text = clean_text(text)
    text = THEPAPER_FOOTER_RE.sub("", text)
    text = re.sub(r"图\s*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_domestic_content(text: str, source: str) -> str:
    if not text:
        return ""
    if "中新网" in source or "中国新闻网" in source:
        return clean_chinanews_content(text)
    if "澎湃" in source:
        return clean_thepaper_content(text)
    return clean_text(text)


def translate_sentences(sentences: list[str]) -> str:
    ensure_argos_translator()
    parts: list[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if ENGLISHISH_RE.search(sentence):
            parts.append(argostranslate.translate.translate(sentence, "en", "zh"))
        else:
            parts.append(sentence)
    return clean_text("".join(parts))


def translate_blocks(text: str, block_size: int = 180) -> str:
    ensure_argos_translator()
    parts: list[str] = []
    for idx in range(0, len(text), block_size):
        block = text[idx : idx + block_size].strip()
        if block:
            parts.append(argostranslate.translate.translate(block, "en", "zh"))
    return clean_text("".join(parts))


def translate_en_to_zh(text: str) -> str:
    text = clean_text(text)
    if not text or not ENGLISHISH_RE.search(text):
        return text
    source = text[:4500]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", source) if s.strip()]
    translated = translate_sentences(sentences)
    if len(translated) < 400:
        translated = translate_blocks(source)
    return translated


def trim_content(text: str, min_len: int = 400, max_len: int = 2000) -> str:
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for sep in ("。", "！", "？", ". ", "! ", "? "):
        pos = cut.rfind(sep)
        if pos >= min_len:
            return cut[: pos + len(sep)].strip()
    return cut.strip()


def process_international_item(item: dict, content: str) -> dict:
    url = item["url"]
    if not content:
        if "bbc.co" in url:
            content = fetch_bbc_content(url)
        else:
            html = fetch(url)
            if html:
                content = extract_article_text(html, url)
        time.sleep(0.3)
    content = clean_bbc_boilerplate(content)
    if ENGLISHISH_RE.search(content):
        print(f"translate rank {item['rank_no']}...", file=sys.stderr)
        content = translate_en_to_zh(content)
    content = trim_content(content, 400, 2000)
    return {
        "rank_no": item["rank_no"],
        "title": item["title"],
        "source": item["source"],
        "region": item["region"],
        "url": item["url"],
        "content": content,
    }


def apply_special_fixes(items: list[dict]) -> list[dict]:
    by_rank = {item["rank_no"]: item for item in items}
    if 21 in by_rank:
        html = fetch(RANK_21_URL)
        content = extract_xinhuanet_content(html or "") if html else ""
        by_rank[21] = {
            "rank_no": 21,
            "title": RANK_21_TITLE,
            "source": "新华网",
            "region": "domestic",
            "url": RANK_21_URL,
            "content": content,
        }
        time.sleep(0.35)
    for rank in BBC_REFETCH_RANKS:
        if rank not in by_rank:
            continue
        item = by_rank[rank]
        content = fetch_bbc_content(item["url"])
        by_rank[rank] = {**item, "content": content}
        time.sleep(0.35)
    return [by_rank[i] for i in sorted(by_rank)]


def finalize_item(item: dict) -> dict:
    rank = item["rank_no"]
    region = item["region"]
    content = item.get("content") or ""

    if region == "international":
        return process_international_item(item, content)

    if rank in (18, 26):
        content = clean_domestic_content(content, item["source"])
        return {
            "rank_no": rank,
            "title": item["title"],
            "source": item["source"],
            "region": region,
            "url": item["url"],
            "content": content,
        }

    content = clean_domestic_content(content, item["source"])
    return {
        "rank_no": rank,
        "title": item["title"],
        "source": item["source"],
        "region": region,
        "url": item["url"],
        "content": content,
    }


def verify_output(items: list[dict]) -> None:
    if len(items) != 50:
        raise SystemExit(f"expected 50 items, got {len(items)}")
    domestic = sum(1 for x in items if x["region"] == "domestic")
    international = sum(1 for x in items if x["region"] == "international")
    if domestic != 30 or international != 20:
        raise SystemExit(
            f"expected 30 domestic + 20 international, got {domestic}+{international}"
        )
    required = {"rank_no", "title", "source", "region", "url", "content"}
    for item in items:
        missing = required - set(item)
        if missing:
            raise SystemExit(f"rank {item.get('rank_no')} missing fields: {missing}")


def main() -> int:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    if len(raw) != 50:
        raise SystemExit(f"raw_fetched.json must contain 50 items, got {len(raw)}")

    items = apply_special_fixes(raw)
    finalized = [finalize_item(item) for item in items]
    finalized.sort(key=lambda x: x["rank_no"])
    verify_output(finalized)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(finalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    domestic = sum(1 for x in finalized if x["region"] == "domestic")
    international = sum(1 for x in finalized if x["region"] == "international")
    print(f"Wrote {OUT_PATH} ({len(finalized)} items: {domestic} domestic, {international} international)")
    for item in finalized:
        clen = len(item.get("content") or "")
        print(
            f"{item['rank_no']:2d} {item['region'][:4]:4s} {clen:5d} {item['title'][:40]}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
