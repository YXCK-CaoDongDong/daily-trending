#!/usr/bin/env python3
"""Build curated daily_news.json with Chinese text and article bodies."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests
import trafilatura
from bs4 import BeautifulSoup

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

LIFE_RE = re.compile(r"养生|散步|头痛|贴秋膘|菊势|食蟹|高血压|寒露时节|刷屏扶贫")
SKIP_TITLE = re.compile(r"API 开放|微博、微信|邵佳一|视频丨|纪录片《|深陷信任|旁白｜")


def get_html(url: str) -> str | None:
    try:
        r = SESSION.get(url, timeout=25)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except requests.RequestException:
        return None


def extract_body(url: str, title: str) -> str:
    html = get_html(url)
    if not html:
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        html = downloaded or ""
    if not html:
        return ""
    if "gov.cn" in url:
        soup = BeautifulSoup(html, "lxml")
        node = soup.select_one("#UCAP-CONTENT, .pages_content, .article-content")
        if node:
            text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
            if len(text) >= 80:
                return text[:20000]
    text = trafilatura.extract(html, favor_precision=True) or ""
    text = text.strip()
    if len(text) < 80:
        return ""
    markers = [t for t in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}", title) if len(t) > 1][:5]
    if markers:
        hit = sum(1 for m in markers if m.casefold() in text.casefold())
        if hit < max(1, len(markers) // 3):
            return ""
    return text[:20000]


def chinanews_candidates() -> list[tuple[str, str, str]]:
    html = get_html("https://www.chinanews.com.cn/scroll-news/news1.html")
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out: list[tuple[str, str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not re.search(r"2026/10-0[78]", href):
            continue
        if any(x in href for x in ("shipin", "/tp/hd", "/tp/2026")):
            continue
        title = a.get_text(strip=True)
        if len(title) < 12 or LIFE_RE.search(title) or SKIP_TITLE.search(title):
            continue
        if href.startswith("/"):
            href = "https://www.chinanews.com.cn" + href
        out.append((title, href, "中国新闻网"))
    # dedupe
    seen: set[str] = set()
    deduped = []
    for t, u, s in out:
        if t in seen:
            continue
        seen.add(t)
        deduped.append((t, u, s))
    return deduped


def thepaper_candidates() -> list[tuple[str, str, str]]:
    html = get_html("https://tophub.today/n/wWmoO5Rd4E")
    if not html:
        return []
    out = []
    for m in re.finditer(
        r'href="(https://www\.thepaper\.cn/newsDetail_forward_\d+)"[^>]*>([^<]+)</a>',
        html,
    ):
        url, title = m.group(1), m.group(2)
        if SKIP_TITLE.search(title) or "马上评" in title or "奔赴" in title:
            continue
        out.append((title, url, "澎湃新闻"))
    return out


INTL_ITEMS = [
    (
        "西班牙养老金领取人因遭驱逐引发全国性抗议，政府宣布暂停相关驱逐行动",
        "Spanish pensioner whose eviction sparked nationwide protests dies, union says",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/c6e3x21ev9wwo",
    ),
    (
        "以色列举行仪式悼念2023年10月7日袭击遇难者，已过去三年",
        "Israelis mourn 7 October attack victims three years after",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/cwkgj0g30m5jo",
    ),
    (
        "以色列民众要求就10月7日安全失败追究政府责任",
        "Israelis demand accountability over 7 October failures",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/c5zjx7xx3487o",
    ),
    (
        "法国在男孩被震撼弹炸伤后暂停警方使用震撼弹",
        "France halts use of stun grenades after boy's hand blown off",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/cqzjx7z2r4gko",
    ),
    (
        "加拿大暂停将协助死亡扩大至精神疾病患者的计划",
        "Canada suspends plans to expand assisted dying to people with mental illness",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/cqd09g0gj50ko",
    ),
    (
        "特朗普称将就鼠疫实验室工作人员死亡事件与普京通话",
        "Trump to speak to Putin about plague lab worker's death",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/cqgm0vrl3xp7o",
    ),
    (
        "俄罗斯导弹袭击乌克兰哈尔科夫，造成儿童在内多人死亡",
        "Children killed while they slept as Russian missile hits Kharkiv",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/ckr5ym098vdeo",
    ),
    (
        "斯里兰卡前总统夫人因涉嫌挪用公款被捕",
        "Sri Lanka's ex-first lady arrested over alleged misuse of funds",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/ck0e0n3xzvp4o",
    ),
    (
        "中国选手在马拉松比赛中骑自行车遭赞助商解约",
        "Chinese runner dropped by sponsor after riding bike during marathon",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/c3y0enr9e078o",
    ),
    (
        "诺贝尔化学奖授予揭示生命手性之谜的科学家",
        "Chemistry Nobel awarded for solving mystery of life's asymmetry",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/c6ly038jg0d4o",
    ),
    (
        "肯尼亚首例埃博拉病例相关十人被隔离观察",
        "Ten people linked to Kenya's first-ever Ebola case quarantined",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/c6eq3x3v11d5o",
    ),
    (
        "日本啤酒巨头遭突击搜查，涉嫌价格操纵",
        "Japan beer giants raided over alleged price-fixing cartel",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/cm5yn3592xk9o",
    ),
    (
        "鼠疫如何传播？专家称肺鼠疫可通过飞沫在人际传播",
        "What is pneumonic plague and how does it spread?",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/cxdd8035jzn3o",
    ),
    (
        "美国田纳西州女囚克里斯塔·派克行刑失败，引发司法争议",
        "What happened in the failed execution of Christa Pike",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/ckge4eql4q7eo",
    ),
    (
        "尼泊尔洪灾遇难者中许多人尚未被官方统计确认",
        "Many Nepalis swept away in the floods aren't officially counted",
        "BBC News",
        "https://www.bbc.co.uk/news/articles/ck054zm1701qo",
    ),
    (
        "肯尼亚加紧追踪埃博拉病例所有密切接触者",
        "Kenya races to trace all contacts after first Ebola death, WHO officials say",
        "UN News",
        "https://news.un.org/feed/view/en/story/2026/10/1168542",
    ),
    (
        "联合国警告也门卫生应对因资金缺口面临严重威胁",
        "Critical funding gap threatens health response in Yemen",
        "UN News",
        "https://news.un.org/feed/view/en/story/2026/10/1168541",
    ),
    (
        "各国政府敦促联合国改革，否则将失去国际信任",
        "Reform, or lose trust: Governments press the UN to reflect the world as it is",
        "UN News",
        "https://news.un.org/feed/view/en/story/2026/10/1168540",
    ),
    (
        "联合国驻黎巴嫩维和部队称以色列边境哨所遭枪击",
        "UN peacekeeping force in Lebanon says shots fired at Israeli border post",
        "Al Jazeera",
        "https://www.aljazeera.com/news/2026/10/7/un-peacekeeping-force-in-lebanon-says-shots-fired-at-israeli-border-post",
    ),
    (
        "印度反对党领袖拉胡尔·甘地因抗议选举官员被拘留",
        "Indian opposition leader Rahul Gandhi detained over election chief protest",
        "Al Jazeera",
        "https://www.aljazeera.com/news/2026/10/7/indian-opposition-leader-rahul-gandhi-detained-over-election-chief-protest",
    ),
]


def translate_paragraphs(en: str) -> str:
    if not en:
        return ""
    if re.search(r"[\u4e00-\u9fff]{80,}", en):
        return en[:20000]
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return ""
    tr = GoogleTranslator(source="en", target="zh-CN")
    chunks: list[str] = []
    step = 3500
    for i in range(0, min(len(en), 12000), step):
        part = en[i : i + step]
        for attempt in range(4):
            try:
                chunks.append(tr.translate(part))
                break
            except Exception:
                time.sleep(2 * (attempt + 1))
        else:
            return ""
        time.sleep(1.2)
    return "".join(chunks)[:20000]


def main() -> int:
    domestic_raw = thepaper_candidates() + chinanews_candidates()
    seen: set[str] = set()
    domestic: list[tuple[str, str, str]] = []
    for t, u, s in domestic_raw:
        if t in seen:
            continue
        seen.add(t)
        domestic.append((t, u, s))
    domestic = domestic[:30]

    items = []
    rank = 1
    for title, url, source in domestic:
        content = extract_body(url, title)
        items.append(
            {
                "rank_no": rank,
                "title": title,
                "source": source,
                "region": "domestic",
                "url": url,
                "content": content,
            }
        )
        rank += 1
        time.sleep(0.25)

    for zh_title, en_title, source, url in INTL_ITEMS:
        en_body = extract_body(url, en_title)
        content = translate_paragraphs(en_body)
        items.append(
            {
                "rank_no": rank,
                "title": zh_title,
                "source": source,
                "region": "international",
                "url": url,
                "content": content,
            }
        )
        rank += 1
        time.sleep(0.3)

    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/data/daily_news.json")
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"items={len(items)} with_content={sum(1 for x in items if x['content'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
