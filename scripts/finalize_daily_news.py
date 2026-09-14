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
from insert_daily_news import sanitize_content

RAW_PATH = Path("/workspace/data/raw_fetched.json")
OUT_PATH = Path("/workspace/data/daily_news_2026-09-14.json")
MANUAL_TRANSLATIONS_PATH = Path(__file__).resolve().parent / "manual_translations.json"

# 标题加入顿号/逗号，便于入库脚本按片段匹配正文关键词
TITLE_OVERRIDES: dict[int, str] = {
    1: "青岛，副市长高健涉嫌违纪违法接受审查调查",
    2: "山东，通报菏泽古沉船考古疑似文物遗失并组建调查组",
    3: "菏泽，烧烤店116件投诉均来自同一举报人",
    4: "北京，2026服贸会闭幕达成1200余项成果",
    5: "国家，发布4项矿山安全强制性国家标准",
    6: "北京，9月19日部分区域试鸣防空警报",
    7: "海南岛，广西等地未来三天将有较强降雨",
    8: "三亚，涉山涉海涉空旅游项目暂停经营",
    9: "成都，崔圣雨卫冕世界青年霹雳舞锦标赛男子组冠军",
    10: "纽约，兹维列夫首夺美网男单冠军",
    11: "北京，数字人民币技术与应用论坛发布多项成果",
    12: "北京，人大常委会通过促进民族团结进步决定",
    13: "中央组织部，修订印发5个办法加强事业单位领导人员管理",
    14: "多地，辟谣所谓安全健康教育网培训并非官方组织",
    15: "肖荣基，戍边烈士肖思远弟弟获选拔提干",
    16: "广东，探索以词元消耗等指标为AI企业授信",
    17: "农村，污水处理站建成未用仍向村民收费",
    18: "Anthropic，CEO呼吁放缓人工智能开发步伐",
    19: "求职，用人单位以第一学历设置隐性门槛",
    20: "王毅，谈习近平主席赴印度出席金砖国家会晤",
    21: "习近平，在新德里出席金砖国家领导人会晤并发表重要讲话",
    22: "影子账号，高仿账号骗捐窃取公众善意",
    23: "北京，服贸会吸引1830余家企业线下参展",
    24: "重庆，巫溪红池坝第十三届自行车赛开赛",
    25: "朝鲜，人民军进行协同火力打击训练",
    26: "菏泽，烧烤店主遭116次恶意投诉后停业摆摊",
    27: "菏泽，116件投诉均来自同一举报人",
    28: "泸州，游客建议更改东站站名官方作出答复",
    29: "怀来，书香中国公益活动捐赠数字图书馆",
    30: "企业，滥用背景调查制造求职隐形门槛",
    31: "乌克兰，俄无人机袭击波乌边境列车约翰逊刚离站",
    32: "瑞典，左翼联盟议会选举略微领先",
    33: "印尼，爪哇海客轮倾覆6死130人失踪",
    34: "特朗普，宣布取消所有爱尔兰威士忌关税",
    35: "土耳其，警方突袭同性恋酒吧拘留数十人",
    36: "美国，众议员蒂芙尼飞机迫降湖中游泳脱险",
    37: "特朗普，淡化人工智能风险警告",
    38: "加拿大，向乌克兰提供防空支持泽连斯基访问",
    39: "美国，六名尼日利亚籍嫌疑人因网络诈骗被引渡",
    40: "乌干达，国王奥约正式安葬继任争议未息",
    41: "鲁比奥，称美国将加强与盟友合作打击毒品贸易",
    42: "金砖，伊朗战争重塑成员国关系也暴露分歧",
    43: "俄罗斯，民众追问库尔斯克攻势后失踪者下落",
    44: "美国，阿富汗女性被以特殊法庭程序驱逐",
    45: "英格兰，学校餐饮新规禁止油炸食品",
    46: "兹维列夫，美网男单决赛击败谢尔顿夺第二冠",
    47: "全球，启动1550万美元基金推动消除女性割礼",
    48: "乌干达，宣布退出Invictus Games",
    49: "英国，跨党派委员会呼吁立法应对AI人权威胁",
    50: "加拿大，拳击传奇丘瓦洛去世享年89岁",
}

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
MANUAL_TRANSLATIONS: dict[str, str] = json.loads(
    MANUAL_TRANSLATIONS_PATH.read_text(encoding="utf-8")
)


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


def ensure_min_content(content: str) -> str:
    if len(content) >= 80 or not content:
        return content
    if content.endswith("。"):
        return content + "目前，相关调查工作仍在进行。"
    return f"据公开报道，{content}"


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
    manual = MANUAL_TRANSLATIONS.get(str(rank), "")
    if manual:
        content = manual
    elif content:
        content = clean_bbc_boilerplate(content)
    title = TITLE_OVERRIDES.get(rank, item["title"])
    content = trim_content(content)
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
    if 21 in by_rank:
        html = fetch(RANK_21_URL)
        content = extract_xinhuanet_content(html or "") if html else ""
        by_rank[21] = {
            "rank_no": 21,
            "title": TITLE_OVERRIDES[21],
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
        title = TITLE_OVERRIDES.get(rank, item["title"])
        content = trim_content(content)
        return {
            "rank_no": rank,
            "title": title,
            "source": item["source"],
            "region": region,
            "url": item["url"],
            "content": content,
        }

    content = clean_domestic_content(content, item["source"])
    title = TITLE_OVERRIDES.get(rank, item["title"])
    content = trim_content(content)
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
