#!/usr/bin/env python3
"""Build daily news JSON: fetch per-URL content, apply intl Chinese translations."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

ITEMS: list[dict] = [
    # --- domestic 1-30 ---
    {"rank_no": 1, "title": "两部门印发《医疗康复护理扩容提升工程实施方案》", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-08/10708882.shtml"},
    {"rank_no": 2, "title": "中国团队率先研制出核光钟，量子精密测量迈向原子核跃迁", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-08/10708921.shtml"},
    {"rank_no": 3, "title": "村田晃大对持刀非法入侵中国使馆罪行供认不讳，中方再次敦促日方严惩凶犯", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-08/10709146.shtml"},
    {"rank_no": 4, "title": "中国最高法等发布典型案例，聚焦解决拖欠企业账款纠纷", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-08/10709153.shtml"},
    {"rank_no": 5, "title": "新就业形态劳动者权益保障办法公开征求意见", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-08/10709310.shtml"},
    {"rank_no": 6, "title": "事关保健食品生产企业自查工作规范，国标公开征求意见", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-08/10709340.shtml"},
    {"rank_no": 7, "title": "国庆假期全社会跨区域人员流动量达21.42亿人次", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-08/10709006.shtml"},
    {"rank_no": 8, "title": "税收数据显示：中国国庆假期服务消费和部分商品消费态势良好", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10709295.shtml"},
    {"rank_no": 9, "title": "国庆节期间1546.2万人次出入境", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10709043.shtml"},
    {"rank_no": 10, "title": "10月8日人民币对美元中间价报6.7367，下调16个基点", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10708890.shtml"},
    {"rank_no": 11, "title": "国家税务总局：10月申报纳税期限顺延至10月26日", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10709014.shtml"},
    {"rank_no": 12, "title": "中国牵头制定的大型藻类固碳量测算国际标准发布", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10709008.shtml"},
    {"rank_no": 13, "title": "百强房企“交卷”：1至9月销售总额超2.25万亿元", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10708967.shtml"},
    {"rank_no": 14, "title": "国庆假期高速公路新能源汽车日均充电量同比增长51.42%", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10709013.shtml"},
    {"rank_no": 15, "title": "全国秋粮收获已过四成，各地保障颗粒归仓", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-07/10708786.shtml"},
    {"rank_no": 16, "title": "日均超3亿人次，国庆假期多项出行数据创新高", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10709007.shtml"},
    {"rank_no": 17, "title": "（粤港澳大湾区）国庆假期深圳出入境人员超620万人次", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/dwq/2026/10-08/10709155.shtml"},
    {"rank_no": 18, "title": "国庆假期经横琴口岸的港澳居民超23.6万人次", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/dwq/2026/10-08/10709257.shtml"},
    {"rank_no": 19, "title": "首届大湾区国际戏剧节在港启幕，百余场演出架起中外文化交流桥梁", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/dwq/2026/10-08/10709339.shtml"},
    {"rank_no": 20, "title": "特朗普称不会在11月美国中期选举前攻击伊朗", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/10-09/10709429.shtml"},
    {"rank_no": 21, "title": "两位科学家获得2026年诺贝尔化学奖", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/10-07/10708780.shtml"},
    {"rank_no": 22, "title": "泰国洪灾已影响55府4216家经营主体", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/10-03/10707615.shtml"},
    {"rank_no": 23, "title": "天津邮轮口岸国庆假期客流走高，外籍旅客同比增超6倍", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-08/10708947.shtml"},
    {"rank_no": 24, "title": "中外学者发现侏罗纪时期新型柱齿兽类哺乳型动物", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cul/2026/10-08/10709328.shtml"},
    {"rank_no": 25, "title": "国庆假期交通出行人数超21亿人次", "source": "中国政府网", "region": "domestic", "url": "https://www.gov.cn/lianbo/202610/content_7082728.htm"},
    {"rank_no": 26, "title": "国庆假期智能、绿色、健康商品需求旺盛", "source": "中国政府网", "region": "domestic", "url": "https://www.gov.cn/lianbo/202610/content_7082676.htm"},
    {"rank_no": 27, "title": "何立峰同英国财政大臣希利举行视频通话", "source": "中国政府网", "region": "domestic", "url": "https://www.gov.cn/yaowen/liebiao/202610/content_7082751.htm"},
    {"rank_no": 28, "title": "国务院关于《医疗康复护理扩容提升工程实施方案》的批复", "source": "中国政府网", "region": "domestic", "url": "https://www.gov.cn/zhengce/content/202609/content_7082378.htm"},
    {"rank_no": 29, "title": "国务院办公厅关于发展体育赛事激发消费活力的意见", "source": "中国政府网", "region": "domestic", "url": "https://www.gov.cn/zhengce/content/202609/content_7082492.htm"},
    {"rank_no": 30, "title": "国务院批复《国家残疾预防行动计划（2026—2030年）》", "source": "中国政府网", "region": "domestic", "url": "https://www.gov.cn/zhengce/content/202610/content_7082737.htm"},
    # --- international 31-50 ---
    {"rank_no": 31, "title": "五角大楼称胡德堡枪击案凶手将遭行刑队枪决并网络直播", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cmy0r96xygx6o"},
    {"rank_no": 32, "title": "官员称俄罗斯袭击乌克兰巴士致至少30人死亡", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c875pwq134l3o"},
    {"rank_no": 33, "title": "抗议者将西班牙住房危机归咎于“秃鹫基金”", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c3j4790elkx7o"},
    {"rank_no": 34, "title": "人权组织称美国向非洲国家遣返移民违法并加剧苦难", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c9p8gn55433jo"},
    {"rank_no": 35, "title": "加拿大诗人安妮·卡森获2026年诺贝尔文学奖", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cq4g1j54nepyo"},
    {"rank_no": 36, "title": "委内瑞拉前总统马杜罗被控共谋实施酷刑", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c5pvgn7xvxpzo"},
    {"rank_no": 37, "title": "研究人员在塞舌尔一岛发现约18万只巨龟", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/environment/2026/oct/08/researchers-find-180000-giant-tortoises-living-on-island-in-seychelles"},
    {"rank_no": 38, "title": "埃塞俄比亚对越境厄立特里亚军队发动无人机打击", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/oct/08/ethiopia-drone-attack-against-eritrean-troops-in-tigray"},
    {"rank_no": 39, "title": "韩国称若向俄罗斯运送燃料违法将采取法律行动", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/oct/08/south-korea-fuel-shipments-to-russia-domestic-law"},
    {"rank_no": 40, "title": "赫格塞思称胡德堡枪手行刑队处决将“公开”进行", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/8/hegseth-says-firing-squad-execution-of-fort-hood-shooter-will-be-public"},
    {"rank_no": 41, "title": "机构称停火以来以色列在加沙平均每90分钟杀伤一名巴勒斯坦人", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/8/israel-kills-or-wounds-palestinian-every-90-minutes-in-gaza-since-ceasefire"},
    {"rank_no": 42, "title": "普京承诺俄罗斯支持结束美国领导的伊朗战争", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/8/putin-pledges-russias-support-to-end-us-led-war-on-iran"},
    {"rank_no": 43, "title": "美国以欺诈指控为由暂停微软和Adobe参与H-1B签证项目", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/8/us-suspends-microsoft-and-adobe-from-visa-programme-amid-fraud-claims"},
    {"rank_no": 44, "title": "特朗普向马斯克等科技高管颁发美国最高科学奖", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/8/trump-gives-top-us-science-awards-to-elon-musk-and-other-tech-executives"},
    {"rank_no": 45, "title": "阿富汗：塔利班以新着装规定逮捕女性，难民返乡潮加剧困境", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168551"},
    {"rank_no": 46, "title": "达尔富尔：安理会延长制裁之际医疗需求超过资源", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168556"},
    {"rank_no": 47, "title": "缅甸：多重冲击下贫困加深，家庭资源有限", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168550"},
    {"rank_no": 48, "title": "乌克兰：联合国谴责最新袭击并呼吁保护平民", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168548"},
    {"rank_no": 49, "title": "俄罗斯向世卫组织表示西伯利亚未发现鼠疫病例", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168547"},
    {"rank_no": 50, "title": "摩纳哥炸弹案嫌疑人向BBC打破沉默", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/ckgel9044vqeo"},
]

JUNK = re.compile(
    r"页面没有找到|Page not found|404|access denied|请先登录|下载客户端|感谢您的浏览",
    re.I,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self._depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True
            self._depth += 1
        elif tag in ("p", "br", "div", "h1", "h2", "h3", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._depth -= 1
            if self._depth <= 0:
                self._skip = False
                self._depth = 0

    def handle_data(self, data: str) -> None:
        if not self._skip:
            t = data.strip()
            if t:
                self.parts.append(t)


def fetch_html(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc
    headers = {"User-Agent": UA, "Referer": f"https://{host}/"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def html_to_text(block: str) -> str:
    p = _TextExtractor()
    p.feed(block)
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(p.parts))
    return re.sub(r"[ \t]+", " ", text).strip()


def extract_body(url: str, html: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    patterns: list[str] = []
    if "chinanews" in host:
        patterns = [r'<div[^>]*class="[^"]*left_zw[^"]*"[^>]*>(.*?)</div>']
    elif "gov.cn" in host:
        patterns = [r'id="UCAP-CONTENT"[^>]*>(.*?)</div>', r'class="pages_content"[^>]*>(.*?)</div>']
    elif "bbc.co" in host:
        patterns = [r'<article[^>]*>(.*?)</article>', r'data-component="text-block"']
    elif "theguardian.com" in host:
        patterns = [r'<article[^>]*>(.*?)</article>']
    elif "aljazeera.com" in host:
        patterns = [r'<div[^>]*class="[^"]*wysiwyg[^"]*"[^>]*>(.*?)</div>']
    elif "news.un.org" in host:
        m = re.search(
            r'<h1[^>]*>.*?</h1>\s*<p[^>]*class="[^"]*meta[^"]*"[^>]*>.*?</p>\s*(.*?)</div>\s*<div[^>]*class="[^"]*share',
            html,
            re.S | re.I,
        )
        if m:
            return html_to_text(m.group(1))
        patterns = [r'<div[^>]*class="[^"]*story-content[^"]*"[^>]*>(.*?)</div>']
    for pat in patterns:
        m = re.search(pat, html, re.S | re.I)
        if m and m.lastindex:
            return html_to_text(m.group(1))
    if "bbc.co" in host:
        chunks = re.findall(r'data-component="text-block"[^>]*>(.*?)</div>', html, re.S)
        if chunks:
            return html_to_text("".join(chunks))
    return html_to_text(html)


def title_markers(title: str) -> list[str]:
    stop = {"正式", "通报", "关于", "今日", "消息", "报道", "宣布", "相关", "情况", "中国", "国庆", "假期"}
    tokens: list[str] = []
    for m in re.finditer(r"[\u4e00-\u9fff]{2,4}|[A-Za-z]{4,}|\d{2,}", title):
        t = m.group()
        if t not in stop:
            tokens.append(t)
    return tokens[:15]


def content_ok(content: str, title: str) -> bool:
    if not content or len(content) < 80:
        return False
    if JUNK.search(content[:800]):
        return False
    markers = title_markers(title)
    if markers and not any(m.casefold() in content.casefold() for m in markers[:6]):
        return False
    return True


def translate_intl(url: str, raw: str, title: str) -> str:
    """Map fetched English/plain text to Chinese for international items."""
    # Translations keyed by URL path suffix for stability
    key = urllib.parse.urlparse(url).path
    translations: dict[str, str] = {}
    trans_file = ROOT / "data" / "intl_zh_content.json"
    if trans_file.is_file():
        translations = json.loads(trans_file.read_text(encoding="utf-8"))
    if key in translations:
        return translations[key]
    if key in translations.get("by_url", {}):
        return translations["by_url"][path]
    # fallback: return raw if already mostly Chinese
    if sum(1 for c in raw if "\u4e00" <= c <= "\u9fff") > len(raw) * 0.3:
        return raw
    return ""


def main() -> int:
    out_path = ROOT / "data" / f"news_{sys.argv[1] if len(sys.argv) > 1 else '2026-10-09'}.json"
    trans_path = ROOT / "data" / "intl_zh_content.json"
    translations: dict[str, str] = {}
    if trans_path.is_file():
        translations = json.loads(trans_path.read_text(encoding="utf-8"))

    built: list[dict] = []
    for row in ITEMS:
        url = row["url"]
        title = row["title"]
        content = ""
        try:
            html = fetch_html(url)
            body = extract_body(url, html)
            if row["region"] == "international":
                key = urllib.parse.urlparse(url).path
                content = translations.get(key) or translations.get(url, "")
                if content and not content_ok(content, title):
                    content = ""
            else:
                content = body if content_ok(body, title) else ""
        except Exception as exc:
            print(f"fetch fail rank {row['rank_no']}: {exc}", file=sys.stderr)
            content = ""
        if len(content) > 20000:
            content = content[:20000]
        built.append(
            {
                "rank_no": row["rank_no"],
                "title": title,
                "source": row["source"],
                "region": row["region"],
                "url": url,
                "content": content,
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(built, ensure_ascii=False, indent=2), encoding="utf-8")
    filled = sum(1 for x in built if x["content"])
    print(f"wrote {out_path} items={len(built)} with_content={filled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
