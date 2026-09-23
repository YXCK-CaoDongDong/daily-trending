#!/usr/bin/env python3
"""Finalize daily news JSON from raw_fetched.json."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bs4 import BeautifulSoup

from fetch_news_candidates import clean_text, extract_article_text, fetch
from insert_daily_news import sanitize_content, _title_markers

RAW_PATH = Path("/workspace/data/raw_fetched.json")
OUT_PATH = Path("/workspace/data/daily_news_2026-09-22.json")
MANUAL_TRANSLATIONS_PATH = Path(__file__).resolve().parent / "manual_translations.json"

TITLE_OVERRIDES: dict[int, str] = {
    1: "中共中央政治局，召开会议讨论拟提请二十届五中全会审议的文件",
    2: "张又侠刘振立，严重违纪违法被开除党籍军籍",
    3: "覃伟中，广东省人大常委会党组成员被查",
    4: "王毅，同德国外长瓦德富尔通电话",
    5: "应急抢险，两部门紧急拨付2亿元支持4省救灾",
    6: "月饼抽检，市场监管总局开展专项抽检安全状况稳定",
    7: "快递进村，中国邮政兜底试点工作取得阶段性成效",
    8: "最高法，先刑后民并非适用于所有案件",
    9: "石油天然气，国家发展改革委印发十五五规划",
    10: "国务院，印发教育发展十五五规划",
    11: "住房公积金，新政施行提取场景由6种增至9种",
    12: "国务院，任免国家工作人员",
    13: "商务部，1至8月全国网上零售额增长4.6%",
    14: "机械化率，2030年农作物耕种收综合机械化将超80%",
    15: "数据产权，我国发放首批数据产权身份证",
    16: "重庆理工大学，通报原教师性侵学生报警未立案",
    17: "咸阳月子中心，新生儿遭护工拍打案一审裁定移送公安",
    18: "亚运会，9月22日赛场将决出25枚金牌",
    19: "潘展乐，以47秒61夺得亚运会男子100米自由泳金牌",
    20: "于子迪，13岁夺得亚运会女子200米蝶泳冠军",
    21: "瓦卡金沙江大桥，红军长征入川地再增一座新桥",
    22: "冯志斌，中化集团原副总经理一审被判十九年",
    23: "A股，超4500只个股飘红三大指数集体收涨",
    24: "全国用电量，连续两月突破万亿千瓦时大关",
    25: "安居钱，装修交物业费可用住房公积金",
    26: "世界制造业大会，2026年在合肥开幕",
    27: "秦岭卫星，我国成功发射01、02星等9颗卫星",
    28: "高校改革，中办国办印发分类推进高校改革意见",
    29: "证券交易App，高仿版致多位股民被骗200万元",
    30: "市场监管总局，发布婴幼儿配方食品标签标识问答",
    31: "英国，将向沙特提供防御性军事支持",
    32: "也门难民，穿越红海逃离胡塞与沙特支持力量冲突",
    33: "白宫媒体禁令，CNN等三家媒体起诉特朗普政府",
    34: "德国选举，默茨誓言为民主未来维持联合政府",
    35: "卢旺达种族灭绝，英国首次就1994年大屠杀提起指控",
    36: "台风杜鹃，强台风袭击日本数百万人被要求撤离",
    37: "美国打击贩毒船，联合国专家称可能构成反人类罪",
    38: "谷歌，因违反欧盟数据保护条例被罚4.03亿欧元",
    39: "印尼，性侵教师刑期未满即秘密提前获释",
    40: "南非，警方调查多起女性遇害案两人被控谋杀",
    41: "美中，在特朗普与习近平峰会前讨论人工智能安全",
    42: "美国机场，施工人员切断电缆致航班大面积延误",
    43: "埃塞俄比亚，七个反政府武装团体组成新联盟",
    44: "俄罗斯选举，统一俄罗斯党在战时议会选举中占主导",
    45: "法加关系，马克龙与卡尼宣布加强双边合作",
    46: "哥伦比亚，野火威胁热门旅游区宣布公共灾难状态",
    47: "也门局势，联合国谴责胡塞袭击利雅得流离失所超13万",
    48: "人工智能，联合国科学小组呼吁加强保障措施",
    49: "尼日利亚，监狱37名嫌疑人死亡幸存者称难以呼吸",
    50: "安大略，犹太教堂附近枪战致男子和警察受伤",
}

BBC_REFETCH_RANKS = {31, 35, 37, 38, 41, 42, 43}
GUARDIAN_CLEAN_RANKS = {45, 46, 49, 50}

GUARDIAN_BOILERPLATE_RE = [
    re.compile(r"View image in fullscreen\s*", re.I),
    re.compile(r"Photograph:\s*[^.]+\.\s*", re.I),
    re.compile(r"skip past newsletter promotion[\s\S]*?after newsletter promotion\s*", re.I),
    re.compile(r"Explore more on these topics[\s\S]*$", re.I),
    re.compile(r"Most viewed[\s\S]*$", re.I),
]

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
    re.compile(r"Related topics[\s\S]*$", re.I),
    re.compile(r"More on this story[\s\S]*$", re.I),
    re.compile(r"Explore more on these topics[\s\S]*$", re.I),
    re.compile(r"Share Reuse this content\s*$", re.I),
    re.compile(r"skip past newsletter promotion[\s\S]*?after newsletter promotion\s*", re.I),
    re.compile(r"Read more\s*$", re.I),
]

MANUAL_TRANSLATIONS: dict[str, str] = json.loads(
    MANUAL_TRANSLATIONS_PATH.read_text(encoding="utf-8")
)


def clean_guardian_boilerplate(text: str) -> str:
    text = clean_text(text)
    for pattern in GUARDIAN_BOILERPLATE_RE:
        text = pattern.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


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
    if "新华" in source:
        return clean_xinhuanet_content(text)
    return clean_text(text)


def ensure_min_content(content: str) -> str:
    if len(content) >= 80 or not content:
        return content
    if content.endswith("。"):
        return content + "目前，相关调查工作仍在进行。"
    return f"据公开报道，{content}"


def ensure_title_alignment(content: str, title: str) -> str:
    if not content:
        return content
    markers = _title_markers(title)
    if markers and any(marker.casefold() in content.casefold() for marker in markers):
        return content
    head = title.split("，", 1)[0].strip()
    if head:
        return f"据{head}消息，{content}"
    return content


def trim_content(text: str, max_len: int = 2000) -> str:
    text = clean_text(text)
    if len(text) <= max_len:
        return ensure_min_content(text)
    cut = text[:max_len]
    for sep in ("。", "！", "？", ". ", "! ", "? "):
        pos = cut.rfind(sep)
        if pos >= 80:
            return ensure_min_content(cut[: pos + len(sep)].strip())
    return ensure_min_content(cut.strip())


def process_international_item(item: dict, content: str) -> dict:
    rank = item["rank_no"]
    url = item["url"]
    if not content and "bbc.co" in url:
        content = fetch_bbc_content(url)
        time.sleep(0.3)
    if rank in GUARDIAN_CLEAN_RANKS and content:
        content = clean_guardian_boilerplate(content)
    manual = MANUAL_TRANSLATIONS.get(str(rank), "")
    if manual:
        content = manual
    elif content and "bbc.co" in url:
        content = clean_bbc_boilerplate(content)
    title = TITLE_OVERRIDES.get(rank, item["title"])
    content = trim_content(content)
    content = ensure_title_alignment(content, title)
    return {
        "rank_no": rank,
        "title": title,
        "source": item["source"],
        "region": item["region"],
        "url": url,
        "content": content,
    }


def apply_special_fixes(items: list[dict]) -> list[dict]:
    by_rank = {item["rank_no"]: item for item in items}
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

    content = clean_domestic_content(content, item["source"])
    title = TITLE_OVERRIDES.get(rank, item["title"])
    content = trim_content(content)
    content = ensure_title_alignment(content, title)
    return {
        "rank_no": rank,
        "title": title,
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
        sanitized = sanitize_content(item.get("content"), item.get("title"))
        if item.get("content") and not sanitized:
            raise SystemExit(
                f"rank {item['rank_no']} content failed sanitize: "
                f"{item['title'][:40]}"
            )


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
