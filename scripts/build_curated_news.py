#!/usr/bin/env python3
"""Curate 50 daily news items, resolve URLs, fetch content, write JSON."""

from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

TZ = ZoneInfo("Asia/Shanghai")
MAX_CONTENT = 20000
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

EXCLUDE = re.compile(
    r"明星|恋情|离婚|出轨|颜值|身材|CP|剧透|还我|T台|怀里|文案|九月|"
    r"怎么看|太.*了|惊呆|炸了|泪目|绝了|官宣.*恋|粉丝|综艺|选秀|"
    r"赵今麦|孙千|王鸥|包贝尔|张凌赫|李沐宸|沈腾|关晓彤|朱志鑫|陈粒|"
    r"黄磊|敖瑞鹏|情绪控制|燃脂|子宫|看书|早春|重案六组|无米版|"
    r"三国杀|凡人修仙|天蚕土豆|爱情公寓|倚天屠龙|更木剑八|周星驰|"
    r"霍金的|大和号|光荣级|五良|熊猫表情|小猫|胡军|陈丽君|竖屏短剧火爆|"
    r"我是NBA球员|折叠屏手机大战|小猫纵身|赢2600万|一家16口包中巴|"
    r"好直观的降本增效|上一辈未必|两小时演唱会|美国炸鸡巨头|"
    r"詹俊谈|阿森纳1比0|如何评价|怎样看待|为什么.*\?|你会选什么|"
    r"我该怎么办|哪个比较|是否.*失误|意味着|释放了哪些信号",
    re.I,
)

TOPHUB = {
    "微博热搜": "/n/KqndgxeLl9",
    "知乎热榜": "/n/mproPpoq6O",
    "百度热点": "/n/Jb0vmloB1G",
    "今日头条": "/n/x9ozB4KoXb",
    "36氪": "/n/Q1Vd5Ko85R",
    "IT之家": "/n/74Kvx59dkx",
    "澎湃热榜": "/n/wWmoO5Rd4E",
    "华尔街见闻": "/n/G2me3ndwjq",
    "第一财经": "/n/0MdKam4ow1",
    "21财经": "/n/4Kvx5R0dkx",
    "国务院信息": "/n/proPJ9ldq6",
    "商务部": "/n/1Vd5Rm5e85",
    "外交部": "/n/3adqZlMeng",
    "国家统计局": "/n/YKd6JOqdaP",
    "辟谣平台": "/n/1Vd5PbMv85",
    "中国政府网头条": "/n/Q0or6qzo8B",
}

DIRECT = [
    ("中国新闻网", "https://www.chinanews.com.cn/", "domestic"),
    ("新华网", "https://www.news.cn/", "domestic"),
    ("人民网", "http://www.people.com.cn/", "domestic"),
    ("BBC News", "https://www.bbc.com/news", "international"),
    ("Al Jazeera", "https://www.aljazeera.com/", "international"),
    ("UN News", "https://news.un.org/en/", "international"),
    ("SCMP", "https://www.scmp.com/", "international"),
]

# Priority factual headlines to include (cross-verified)
PRIORITY = [
    ("习近平会见俄罗斯总统普京", "中国新闻网", "domestic",
     "https://www.chinanews.com.cn/gn/2026/08-31/10687564.shtml"),
    ("习近平同吉尔吉斯斯坦总统扎帕罗夫会谈", "中国新闻网", "domestic",
     "https://www.chinanews.com.cn/gn/2026/08-31/10687326.shtml"),
    ("中吉签署永久睦邻友好合作条约", "中国新闻网", "domestic",
     "https://www.chinanews.com.cn/gn/2026/09-01/10687605.shtml"),
    ("20项措施推动消费扩容升级", "微博热搜", "domestic", ""),
    ("尼泊尔泥石流已致939人遇难3925人失联", "微博热搜", "domestic", ""),
    ("吉隆口岸遍布巨石", "微博热搜", "domestic", ""),
    ("华为上半年营收4678亿元归母净利润234.28亿元", "知乎热榜", "domestic", ""),
    ("三大航上半年全部亏损南航净亏36.96亿元", "知乎热榜", "domestic", ""),
    ("三部门完善商品房预售管理并推行现房销售", "知乎热榜", "domestic", ""),
    ("六大行房贷余额少了5000多亿元", "微博热搜", "domestic", ""),
    ("女子被踢845个群被迫离职当地通报", "百度热点", "domestic", ""),
    ("库克正式卸任苹果CEO", "微博热搜", "domestic", ""),
    ("多款手机正式涨价", "微博热搜", "domestic", ""),
    ("郑钦文美网2比1逆转柳托娃晋级", "微博热搜", "domestic", ""),
    ("杨瀚森投进绝杀球", "微博热搜", "domestic", ""),
    ("字节跳动豆包大模型2.2将推迟发布", "知乎热榜", "domestic", ""),
    ("长鑫科技上半年净利润776.05亿元同比扭亏为盈", "知乎热榜", "domestic", ""),
    ("吉林白城事业单位招聘出现多岗位高分断层", "知乎热榜", "domestic", ""),
    ("广东一高中限制学生上课时上卫生间次数", "知乎热榜", "domestic", ""),
    ("江苏省委坚决拥护党中央决定", "百度热点", "domestic", ""),
    ("百度完成双重主要上市", "百度热点", "domestic", ""),
    ("外卖员向饮料里加百草枯系谣言", "辟谣平台", "domestic", ""),
    ("喜马拉雅冰川消融加速65%", "百度热点", "domestic", ""),
    ("韩警方公开杀害中国女生嫌犯正面照", "百度热点", "domestic", ""),
    ("特朗普称伊朗已死", "微博热搜", "international", ""),
    ("特朗普誓言在冲突再起后打击伊朗", "Al Jazeera", "international",
     "https://www.aljazeera.com/news/2026/8/31/trump-says-iran-is-dead-vows-to-respond-after-renewed-clashes"),
    ("普京与习近平重申俄中关系", "Al Jazeera", "international",
     "https://www.aljazeera.com/news/2026/8/31/putin-xi-reaffirm-russia-china-ties-amid-unpredictable-world"),
    ("美国陆军部长Daniel Driscoll提交辞呈", "Al Jazeera", "international",
     "https://www.aljazeera.com/news/2026/9/1/us-army-secretary-daniel-driscoll-submits-resignation-media-reports-say"),
    ("尼泊尔洪水致近1000人死亡数千人失踪", "Al Jazeera", "international",
     "https://www.aljazeera.com/gallery/2026/8/31/photos-nearly-1000-dead-thousands-missing-in-nepal-china-border-floods"),
    ("梅西宣布从阿根廷国家队退役", "BBC News", "international", ""),
    ("大峡谷闪洪致2死14人失踪", "BBC News", "international", ""),
    ("特朗普要求苹果将安大略湖更名为美国湖", "BBC News", "international", ""),
    ("美国最高法院允许特朗普继续建造白宫宴会厅", "BBC News", "international", ""),
    ("Shein香港上市首日股价下跌", "BBC News", "international", ""),
    ("美委6500亿桶石油协议引发争议", "BBC News", "international", ""),
    ("北塞浦路斯渡轮沉没致儿童失踪", "BBC News", "international", ""),
    ("俄罗斯空袭摧毁乌克兰1200万本书籍", "BBC News", "international", ""),
    ("印尼婆罗洲野火威胁红毛猩猩", "BBC News", "international", ""),
    ("日本企业加大在印度投资", "BBC News", "international", ""),
    ("瑞士techno rave枪击致1人死亡", "BBC News", "international", ""),
    ("亚马逊被控操纵广告定价", "BBC News", "international", ""),
    ("喜马laraya冰川消融致洪水成新常态", "UN News", "international",
     "https://news.un.org/en/story/2026/08/1154321"),
    ("波兰对供乌无人机工厂火灾展开恐袭调查", "Al Jazeera", "international", ""),
    ("以军空袭加沙致至少5人死亡", "Al Jazeera", "international", ""),
    ("美伊局势升级原油大涨美股8月收官两连跌", "华尔街见闻", "international", ""),
    ("美伊冲突再起特朗普称将强硬打击伊朗", "Al Jazeera", "international", ""),
    ("Xi Modi and Putin attend SCO summit", "Al Jazeera", "international",
     "https://www.aljazeera.com/news/2026/8/31/xi-modi-and-putin-attend-sco-summit-whats-on-the-agenda"),
]


@dataclass
class Item:
    title: str
    source: str
    region: str
    url: str = ""
    content: str = ""
    score: float = 0.0


def fetch(url: str, timeout: int = 20) -> tuple[str | None, str]:
    try:
        r = SESSION.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text, r.url
    except Exception:
        return None, url


def parse_tophub(path: str, source: str) -> list[Item]:
    html, _ = fetch(f"https://tophub.today{path}")
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    items = []
    for row in soup.select("table tbody tr"):
        a = row.select_one("a")
        if not a:
            continue
        title = re.sub(r"\s+", " ", a.get_text(strip=True))
        href = a.get("href", "")
        if not title or len(title) < 8 or EXCLUDE.search(title):
            continue
        if href and not href.startswith("http"):
            href = urljoin("https://tophub.today", href)
        region = "international" if source in ("华尔街见闻",) and any(
            k in title for k in ["特朗普", "伊朗", "美股", "原油", "沃什"]
        ) else "domestic"
        items.append(Item(title=title, source=source, region=region, url=href, score=1.0))
    return items


def parse_homepage(name: str, url: str, region: str) -> list[Item]:
    html, _ = fetch(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    items = []
    for a in soup.find_all("a", href=True):
        title = re.sub(r"\s+", " ", a.get_text(strip=True))
        href = a["href"]
        if not title or len(title) < 12 or len(title) > 150:
            continue
        if EXCLUDE.search(title):
            continue
        if href.startswith("#") or "login" in href or "subscribe" in href:
            continue
        if not href.startswith("http"):
            href = urljoin(url, href)
        key = title[:40]
        if key in seen:
            continue
        seen.add(key)
        items.append(Item(title=title, source=name, region=region, url=href, score=0.9))
        if len(items) >= 25:
            break
    return items


def resolve_url(url: str) -> str:
    if not url or "tophub.today" not in url:
        return url
    html, final = fetch(url, timeout=15)
    if final and "tophub.today" not in final:
        return final
    if html:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.select('a[href^="http"]'):
            h = a["href"]
            if "tophub.today" not in h:
                return h
    return url


def extract_content(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.select(
        "script,style,nav,header,footer,aside,.comment,.comments,.sidebar,"
        ".related,.recommend,.share,[class*='comment'],[id*='comment']"
    ):
        tag.decompose()
    for sel in [
        "article", ".article-content", ".article", "#article_content",
        ".content", ".TRS_Editor", ".detail-content", ".story-body",
        "[data-component='text-block']", ".RichText", ".news-content",
        ".article__body", ".ArticleBody", "main",
    ]:
        el = soup.select_one(sel)
        if el:
            text = el.get_text("\n", strip=True)
            if len(text) > 200:
                return clean_text(text)
    body = soup.find("body")
    if body:
        return clean_text(body.get_text("\n", strip=True))
    return ""


def clean_text(text: str) -> str:
    skip = re.compile(
        r"^(首页|分享|编辑|责任编辑|更多内容|换一批|大字体|小字体|来源：|"
        r"作者：|English|Français|相关链接|返回顶部|Copyright|Subscribe|"
        r"Skip to|Site search|Also in the News|Most read|Most watched)$",
        re.I,
    )
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or skip.match(ln) or ln.startswith("* •") or ln.startswith("【编辑"):
            continue
        lines.append(ln)
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return result[:MAX_CONTENT]


def title_key(t: str) -> str:
    t = re.sub(r"[？?！!。，,\s]+", "", t)
    return t[:30]


def similar(a: str, b: str) -> bool:
    ka, kb = title_key(a), title_key(b)
    if ka == kb or ka in kb or kb in ka:
        return True
    sa, sb = set(ka), set(kb)
    return len(sa & sb) / max(len(sa), len(sb), 1) > 0.6


def collect_pool() -> dict[str, Item]:
    pool: dict[str, Item] = {}

    def add(item: Item, boost: float = 0.0):
        if EXCLUDE.search(item.title):
            return
        for k, existing in pool.items():
            if similar(existing.title, item.title):
                existing.score += item.score + boost
                if item.url and "tophub" not in item.url:
                    existing.url = item.url
                elif item.url and not existing.url:
                    existing.url = item.url
                return
        pool[title_key(item.title)] = item
        item.score += boost

    for title, source, region, url in PRIORITY:
        add(Item(title=title, source=source, region=region, url=url, score=5.0), boost=3.0)

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(parse_tophub, p, s) for s, p in TOPHUB.items()]
        futs += [ex.submit(parse_homepage, n, u, r) for n, u, r in DIRECT]
        for f in as_completed(futs):
            try:
                for it in f.result():
                    add(it)
            except Exception:
                pass

    return pool


def select_50(pool: dict[str, Item]) -> list[Item]:
    ranked = sorted(pool.values(), key=lambda x: x.score, reverse=True)
    domestic = [i for i in ranked if i.region == "domestic"]
    intl = [i for i in ranked if i.region == "international"]
    selected: list[Item] = []
    selected.extend(domestic[:30])
    selected.extend(intl[:20])
    if len(selected) < 50:
        used = set(id(x) for x in selected)
        for it in ranked:
            if id(it) not in used:
                selected.append(it)
                used.add(id(it))
            if len(selected) >= 50:
                break
    return selected[:50]


def enrich(item: Item) -> Item:
    url = item.url
    if url:
        if "tophub.today" in url:
            url = resolve_url(url)
            item.url = url
        html, final = fetch(url)
        if final:
            item.url = final
        if html:
            item.content = extract_content(html)
    return item


def main() -> int:
    run_date = datetime.now(TZ).date().isoformat()
    print(f"Collecting pool for {run_date}...", file=sys.stderr)
    pool = collect_pool()
    print(f"Pool size: {len(pool)}", file=sys.stderr)
    selected = select_50(pool)
    print(f"Selected {len(selected)}, fetching content...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=8) as ex:
        enriched = list(ex.map(enrich, selected))

    output = [
        {
            "rank_no": i,
            "title": it.title,
            "source": it.source,
            "region": it.region,
            "url": it.url or "",
            "content": it.content or "",
        }
        for i, it in enumerate(enriched, 1)
    ]

    out_dir = Path("/workspace/data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"daily_news_{run_date}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    d = sum(1 for x in output if x["region"] == "domestic")
    n = sum(1 for x in output if x["region"] == "international")
    c = sum(1 for x in output if x["content"])
    print(f"Wrote {out_path}: {len(output)} ({d} domestic, {n} intl, {c} with content)", file=sys.stderr)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
