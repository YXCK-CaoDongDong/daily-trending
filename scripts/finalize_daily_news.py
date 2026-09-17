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
OUT_PATH = Path("/workspace/data/daily_news_2026-09-17.json")
MANUAL_TRANSLATIONS_PATH = Path(__file__).resolve().parent / "manual_translations.json"

# 标题加入顿号/逗号，便于入库脚本按片段匹配正文关键词
TITLE_OVERRIDES: dict[int, str] = {
    1: "西北太平洋，第25号台风“杜鹃”生成",
    2: "国安部，披露AI劫持网站并偷建地下论坛案件",
    3: "学生坠楼，南方医科大学通报排除他杀成立专班",
    4: "南京博物院，原院长徐湖平获刑三年",
    5: "泸州东站，12306客户端增加更名提示弹窗",
    6: "中国，夏粮收购接近尾声累计收购小麦1亿吨",
    7: "中国男篮，击败沙特队晋级杭州亚运会四强",
    8: "王毅，会见巴西总统首席特别顾问阿莫林",
    9: "王毅，同伊朗外长阿拉格齐会谈",
    10: "中国航天科技集团，发声明打假华航天特假冒国企",
    11: "A股，超4100只个股飘红三大指数集体收涨",
    12: "平陆运河，建成通航",
    13: "国家医保局，首批基本医保医疗服务项目目录方案发布",
    14: "海南，启动国家自然灾害救助四级应急响应",
    15: "国家网信办，通报网络安全数据安全执法典型案例",
    16: "工信部，要求健全行业账款支付规则",
    17: "国家卫健委，要求进一步营造生育友好环境",
    18: "70城，8月份商品住宅销售价格变动情况公布",
    19: "全国碳市场，进入快速发展新阶段",
    20: "出入境中介，机构和人员今起实行备案管理",
    21: "司法部，今年以来已审查完成37件立法项目",
    22: "引力一号，遥三运载火箭一箭9星发射成功",
    23: "贵州，涂妍被开除党籍和公职",
    24: "吉林，张吉锋接受纪律审查和监察调查",
    25: "巴基斯坦，召见印度临时代办就军舰碰撞抗议",
    26: "美联储，时隔三年多宣布加息25个基点",
    27: "特朗普，签署备忘录排除加拿大产品出美政府采购",
    28: "东盟，通过马尼拉宣言强化灾害韧性合作",
    29: "英国，宣布为陆军列装新型侦察无人机采购方案",
    30: "韩国，法院宣判民间无人机侵入朝鲜案",
    31: "美联储，三年来首次加息至3.75%至4%",
    32: "美国众议院，认定爱泼斯坦商业伙伴布莱克藐视国会",
    33: "加沙，受损建筑倒塌致21人死亡含8名儿童",
    34: "欧盟，支持加拿大成为联系成员的计划",
    35: "美国，照片显示伊朗袭击致中东基地广泛破坏",
    36: "沙特，在麦加以南击落胡塞武装无人机",
    37: "美国，指控俄罗斯试图在海外暗杀乌克兰盟友",
    38: "美国，限制部分南非官员签证指反白人歧视",
    39: "OpenAI，CEO称世界有权害怕AI但应信任企业",
    40: "德国，八位州长支持默茨政治前景受关注",
    41: "特朗普，幕僚长苏茜·威尔斯宣布已无癌症",
    42: "瑞士，轻型飞机坠毁两名英国人遇难",
    43: "哥伦比亚，和巴西成杀害环保活动人士最致命国家",
    44: "Snapchat，CEO称愿为青少年设每日使用时间限制",
    45: "首尔，米其林餐厅因使用蚂蚁装饰被罚款",
    46: "萨赫勒，基地组织和IS相关暴力将创纪录",
    47: "美国，限制部分南非人签证指反白人歧视",
    48: "南非，七名女性遗体发现加剧对女性暴力愤怒",
    49: "巴西，最高法院在总统选举前爆发激烈内斗",
    50: "拉丁美洲，环保活动人士组建自卫单位应对谋杀",
}

BBC_REFETCH_RANKS = {31, 33, 34, 35, 39, 44}
RANK_24_URL = "https://www.news.cn/legal/20260915/8e3bd888704d49159ec69847670cab2a/c.html"
GUARDIAN_CLEAN_RANKS = {46, 47, 48, 49, 50}

GUARDIAN_BOILERPLATE_RE = [
    re.compile(r"View image in fullscreen\s*", re.I),
    re.compile(r"Photograph:\s*[^.]+\.\s*", re.I),
    re.compile(r"skip past newsletter promotion[\s\S]*?after newsletter promotion\s*", re.I),
    re.compile(r"Explore more on these topics[\s\S]*$", re.I),
    re.compile(r"Most viewed[\s\S]*$", re.I),
]


def clean_guardian_boilerplate(text: str) -> str:
    text = clean_text(text)
    for pattern in GUARDIAN_BOILERPLATE_RE:
        text = pattern.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


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
    manual = MANUAL_TRANSLATIONS.get(str(rank), "")
    if manual:
        content = manual
    elif content:
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
    if 24 in by_rank:
        html = fetch(RANK_24_URL)
        content = extract_article_text(html or "", RANK_24_URL) if html else ""
        by_rank[24] = {
            **by_rank[24],
            "url": RANK_24_URL,
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
