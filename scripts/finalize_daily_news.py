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
OUT_PATH = Path("/workspace/data/daily_news_2026-09-21.json")
MANUAL_TRANSLATIONS_PATH = Path(__file__).resolve().parent / "manual_translations.json"

TITLE_OVERRIDES: dict[int, str] = {
    1: "潘展乐，以47秒61夺得亚运会男子100米自由泳金牌",
    2: "中国队，亚运会开幕后首个比赛日夺得11枚金牌",
    3: "中国队，获亚运会女子4×100米自由泳接力冠军",
    4: "于子迪，13岁夺得亚运会女子200米蝶泳冠军",
    5: "李刘畅，逆转夺得亚运会现代五项男子个人赛金牌",
    6: "中美经贸，磋商在美国纽约开始举行",
    7: "中办国办，印发关于分类推进高校改革的意见",
    8: "2026世界制造业大会，在合肥开幕",
    9: "秦岭卫星，我国成功发射01、02星等9颗卫星",
    10: "住房公积金，新政施行提取场景由6种增至9种",
    11: "安居钱，装修交物业费可用住房公积金",
    12: "证券交易App，高仿版以假乱真股民被骗200万",
    13: "国务院，任免国家工作人员",
    14: "商务部，1至8月全国网上零售额增长4.6%",
    15: "科普人员，2025年全国超225万人",
    16: "机械化率，2030年农作物耕种收综合机械化将超80%",
    17: "市场监管总局，发布婴幼儿配方食品标签标识问答",
    18: "董建华，公祭仪式在香港举行",
    19: "石油天然气，国家发展改革委印发十五五规划",
    20: "第一学历歧视，卡第一学历成部分企业招聘潜规则",
    21: "骗保产业链，央视起底明码标价灰色链条",
    22: "全国用电量，连续两月突破万亿千瓦时大关",
    23: "最高检抗诉，工伤职工连续抢救后获赔92万元",
    24: "网络安全宣传周，强调防范网络风险",
    25: "国务院，印发教育发展十五五规划",
    26: "税收收入，专家称与经济增长基本相匹配",
    27: "海南环岛高铁，推出自行车随身行服务",
    28: "城市联合招聘，2026年高校毕业生秋季专项启动",
    29: "市场监管，国新办介绍十五五时期工作",
    30: "全球鹰无人机，日本海保发现疑似失联残骸",
    31: "德国选举，默茨称州选结果对基民盟是灾难",
    32: "胡塞武装，称以弹道导弹袭击沙特首都利雅得",
    33: "莫斯科，乌克兰发动大规模无人机袭击",
    34: "特朗普，签署全面俄罗斯制裁法案",
    35: "特朗普，宣布美国将组建人工智能部队",
    36: "格陵兰岛，北约欢迎协议特朗普称获永久安全控制",
    37: "巴基斯坦，前总理伊姆兰·汗之妹被捕",
    38: "印尼，性侵教师刑期未满即秘密提前获释",
    39: "南非，连续发现遇害女性遗体引发社会恐惧",
    40: "白宫，特朗普禁止部分媒体后记者被拒通行",
    41: "俄罗斯，战时选举投票结束执政党预计将占主导",
    42: "法国，将召见伊朗大使因德黑兰关闭法语中心",
    43: "卡塔尔，首相称美以与伊朗冲突余波如地震",
    44: "美中，在特朗普与习近平峰会前开启高层会谈",
    45: "马克龙，与加拿大总理卡尼宣布加强双边关系",
    46: "海地，18名嫌疑人被引渡至美国涉总统遇刺案",
    47: "尼泊尔洪水，联合国称破坏警示喜马拉雅气候威胁",
    48: "巴切莱特，退出联合国秘书长竞选",
    49: "尼日利亚，监狱37名嫌疑人死亡幸存者称难以呼吸",
    50: "朝鲜，在特朗普与习近平峰会前发射两枚短程弹道导弹",
}

BBC_REFETCH_RANKS = {31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
GUARDIAN_CLEAN_RANKS = {46, 48, 49}
YONHAP_CLEAN_RANKS = {50}

GUARDIAN_BOILERPLATE_RE = [
    re.compile(r"View image in fullscreen\s*", re.I),
    re.compile(r"Photograph:\s*[^.]+\.\s*", re.I),
    re.compile(r"skip past newsletter promotion[\s\S]*?after newsletter promotion\s*", re.I),
    re.compile(r"Explore more on these topics[\s\S]*$", re.I),
    re.compile(r"Most viewed[\s\S]*$", re.I),
]

YONHAP_BOILERPLATE_RE = [
    re.compile(r"Facebook X More Pinterest[\s\S]*?OK\s*", re.I),
    re.compile(r"Related Articles[\s\S]*$", re.I),
    re.compile(r"Most Viewed[\s\S]*$", re.I),
    re.compile(r"Most Liked[\s\S]*?Most Saved[\s\S]*?Most Viewed[\s\S]*$", re.I),
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
    re.compile(r"Updated \d{1,2} hour ago\s*", re.I),
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


def clean_yonhap_boilerplate(text: str) -> str:
    text = clean_text(text)
    for pattern in YONHAP_BOILERPLATE_RE:
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
    if rank in YONHAP_CLEAN_RANKS and content:
        content = clean_yonhap_boilerplate(content)
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
