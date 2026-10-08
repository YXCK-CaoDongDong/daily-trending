#!/usr/bin/env python3
"""Build daily trending news JSON (50 items) and optionally insert."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from deep_translator import GoogleTranslator, MyMemoryTranslator

# Allow importing fetch_article from same directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_article import fetch  # noqa: E402

TZ = ZoneInfo("Asia/Shanghai")

# rank_no, title, source, region, url, optional manual_content
ITEMS: list[dict] = [
    # --- domestic 30 ---
    {
        "rank_no": 1,
        "title": "8家中央金融企业计划共增资3600亿元用于补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/6445db11e5a048eb932ae3e120061502/c.html",
    },
    {
        "rank_no": 2,
        "title": "财政部将发行3000亿元特别国债支持8家中央金融企业补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/d8c683a121174577abbecd8106bfa2b7/c.html",
    },
    {
        "rank_no": 3,
        "title": "中国工商银行拟向特定对象发行A股募资不超过1000亿元用于补充资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260906/7a17cb99f69d4ab6b095ec18bdbea07d/c.html",
    },
    {
        "rank_no": 4,
        "title": "中国农业银行拟向特定对象发行A股募资不超过1600亿元用于补充资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260906/e4c83df5a832487faa94d0313189ecf7/c.html",
    },
    {
        "rank_no": 5,
        "title": "财政部将向中国进出口银行注资300亿元",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260906/b9b5ae6a01bb4933a8279d74e66c2c6f/c.html",
    },
    {
        "rank_no": 6,
        "title": "西藏吉隆“8·26”泥石流灾害已致43人遇难519人失联",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/12341483ea9e456b9b7d8935873ac295/c.html",
    },
    {
        "rank_no": 7,
        "title": "救援人员在西藏吉隆核心区域开展地毯式搜寻发现遗物993件",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-06/10691499.shtml",
    },
    {
        "rank_no": 8,
        "title": "中国女篮世界杯加时74比70逆转捷克队取得首胜",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260906/9a83cef143694ab2bc4d517eed4baa83/c.html",
    },
    {
        "rank_no": 9,
        "title": "中国选手郑钦文晋级美网女单16强",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-06/10691266.shtml",
    },
    {
        "rank_no": 10,
        "title": "贵州中医药大学第二附属医院伤医案犯罪嫌疑人胡某某被刑拘",
        "source": "央广网",
        "region": "domestic",
        "url": "https://news.cnr.cn/native/gd/kx/20260906/t20260906_527805734.shtml",
    },
    {
        "rank_no": 11,
        "title": "多地市场监管部门严查赵一鸣、好想来等量贩零食门店计量问题",
        "source": "北京日报",
        "region": "domestic",
        "url": "https://finance.sina.com.cn/stock/marketresearch/2026-09-06/doc-iniqxiqn9841812.shtml",
    },
    {
        "rank_no": 12,
        "title": "江西低保家庭女生赴港看演唱会被取消低保资格，赣州民政局称正在核查",
        "source": "中华网",
        "region": "domestic",
        "url": "https://news.china.com/socialgd/10000169/20260906/49722571.html",
    },
    {
        "rank_no": 13,
        "title": "CHINA GT上海站赛车碰撞起火，组委会致歉并将进一步调查",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34019796",
    },
    {
        "rank_no": 14,
        "title": "山东临清先锋大桥步道桥板脱落致22岁行人坠河身亡",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34016288",
    },
    {
        "rank_no": 15,
        "title": "江西省公安厅原党委委员万秀奇接受纪律审查和监察调查",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-06/10691532.shtml",
    },
    {
        "rank_no": 16,
        "title": "广东湛江5岁女童电子病历被医生标注“刁蛮”，涉事医生被立案调查",
        "source": "光明网",
        "region": "domestic",
        "url": "https://news.china.com/socialgd/10000169/20260906/49722169.html",
    },
    {
        "rank_no": 17,
        "title": "山西阳高县7个村庄地下水监测井采样造假，饮用水冒充地下水",
        "source": "央视财经",
        "region": "domestic",
        "url": "https://news.china.com/socialgd/10000169/20260906/49722768.html",
    },
    {
        "rank_no": 18,
        "title": "福州永泰县同安镇房屋坍塌4名失联人员经27小时营救全部脱险",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/b8c6bd335e944960939df01a68b669e7/c.html",
        "manual_content": (
            "新华社北京9月6日电 9月4日，福建省福州市永泰县同安镇一处房屋发生坍塌，"
            "造成4人失联。当地消防救援力量随即赶赴现场开展搜救。经过连续27个多小时的"
            "昼夜奋战，4名被困人员全部被成功救出，生命体征平稳。目前，有关部门正就"
            "坍塌原因开展调查，并对周边区域开展安全排查。"
        ),
    },
    {
        "rank_no": 19,
        "title": "内蒙古贺兰山综合科考发现6个新物种",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/travel/20260904/da6481c3ea7c465880975d682f7ed44c/c.html",
    },
    {
        "rank_no": 20,
        "title": "教育部回应中小学是否一定要买校服：坚持自愿购买原则",
        "source": "新京报",
        "region": "domestic",
        "url": "https://www.bjnews.com.cn/detail/1788657399129092.html",
    },
    {
        "rank_no": 21,
        "title": "胖东来要求供应商填报员工社保和工时信息作为招商初筛必填项",
        "source": "界面新闻",
        "region": "domestic",
        "url": "https://www.jiemian.com/article/15047448.html",
    },
    {
        "rank_no": 22,
        "title": "多家银行集中清淤不良，工商银行上半年核销819亿元",
        "source": "央视网",
        "region": "domestic",
        "url": "https://finance.cctv.com/2026/09/04/ARTIuz2PcpgZOtcBlvLXzKHC260904.shtml",
    },
    {
        "rank_no": 23,
        "title": "最高法发文明确“AI换脸拟声”等涉人工智能纠纷案件裁判规则",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/legal/20260907/ce0e6790833740d3901d2448e22557ff/c.html",
    },
    {
        "rank_no": 24,
        "title": "信息通信行业发展“十五五”规划发布，列出13个主要指标",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260907/def9a4d503584f3698586a89db9755a1/c.html",
    },
    {
        "rank_no": 25,
        "title": "六部门联合印发意见，推动历史经典产业高质量发展",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-07/10691743.shtml",
    },
    {
        "rank_no": 26,
        "title": "平陆运河将于9月16日建成通航",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260907/a0d38cc5fd8349f48d66cde06539015a/c.html",
    },
    {
        "rank_no": 27,
        "title": "财政部积极支持有关中央金融企业补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260907/37ee3e8c29be4a17a52cbe4715e5735f/c.html",
    },
    {
        "rank_no": 28,
        "title": "最高法发文规制“大数据杀熟”“仿冒名人带货”等不正当竞争行为",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-07/10691956.shtml",
    },
    {
        "rank_no": 29,
        "title": "中国证监会原副主席王建军受贿案一审被判处无期徒刑",
        "source": "人民网",
        "region": "domestic",
        "url": "http://society.people.com.cn/n1/2026/0907/c1008-40794127.html",
    },
    {
        "rank_no": 30,
        "title": "华为发布麒麟9050Pro芯片及多款终端产品",
        "source": "央视新闻",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "9月7日，华为在深圳举行秋季全场景新品发布会，正式发布麒麟9050Pro"
            "高性能芯片及多款终端产品，涵盖手机、折叠屏、平板及穿戴设备等。"
            "发布会引发广泛关注，麒麟9050Pro被视为华为时隔六年再次推出的"
            "高性能自研芯片。华为还公布了鸿蒙7系统适配机型范围。多家媒体"
            "及社交平台对新品性能、售价及供应链自主化进展进行报道。"
        ),
    },
    # --- international 20 (ranks 31-50), foreign sources only ---
    {
        "rank_no": 31,
        "title": "德国选择党在萨克森-安哈尔特州地方选举中以约44%得票率成为第一大党",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/germany-saxony-anhalt-election-far-right-afd-c538060710a2495c72425b6468df0d40",
    },
    {
        "rank_no": 32,
        "title": "亚马逊货机在迈阿密国际机场冲出跑道起火，至少5人死亡",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/amazon-cargo-plane-miami-airport-47411c751782887757922efa5f634aa5",
    },
    {
        "rank_no": 33,
        "title": "印尼喀拉喀托之子火山喷发致27万人受困，多座机场延长关闭",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/czezydp4l97o",
    },
    {
        "rank_no": 34,
        "title": "泽连斯基称与美特使会谈后预计俄乌战争将持续至冬季",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c6248nvqy8po",
    },
    {
        "rank_no": 35,
        "title": "美国特使维特科夫和库什纳在乌克兰与泽连斯基举行会谈",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/russia-ukraine-war-witkoff-kushner-zelenskyy-putin-44bba3b57b480560d9f48dba7d28534e",
    },
    {
        "rank_no": 36,
        "title": "伊朗称将在霍尔木兹海峡附近宣布新的“禁区”",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/iran-us-war-strait-hormuz-ship-attack-a52beec77dc90af3d040d0553837ad20",
    },
    {
        "rank_no": 37,
        "title": "印度新德里一栋多层建筑倒塌致至少6人死亡",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/india-teams-search-for-survivors-after-delhi-building-collapse-kills-six",
    },
    {
        "rank_no": 38,
        "title": "牙买加政府将在访英期间递交奴隶制赔偿请愿书",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/jamaica-to-file-slavery-reparations-petition-during-uk-visit",
    },
    {
        "rank_no": 39,
        "title": "飓风“玛丽”在南加州引发巨浪和危险海流",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/hurricane-marie-california-beaches-waves-flooding-9a57a27e84cc48fefb90c10baa499cfe",
    },
    {
        "rank_no": 40,
        "title": "武装男子在俄亥俄州竞选活动中袭击民主党州长候选人",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/election-2026-ohio-acton-attack-92abb7d809134b43630e01e25b3b9125",
    },
    {
        "rank_no": 41,
        "title": "以色列空袭黎巴嫩南部村庄造成至少11人死亡",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/israeli-air-attack-kills-at-least-10-people-in-southern-lebanon",
    },
    {
        "rank_no": 42,
        "title": "也门政府军在胡塞武装冲突中宣称控制一战略地区",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/6/yemeni-forces-claim-strategic-district-amid-intensified-houthi-clashes",
    },
    {
        "rank_no": 43,
        "title": "奥地利14岁以下女生返校首日全面执行伊斯兰头巾禁令",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cwyz74xn8q8o",
    },
    {
        "rank_no": 44,
        "title": "埃及电视主持人莎拉·哈利法等12人因毒品案被判处死刑",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/6/egyptian-tv-presenter-sentenced-to-death-in-major-drug-case",
    },
    {
        "rank_no": 45,
        "title": "联合国投票通过采用反映非洲真实面积的新世界地图决议",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/04/un-vote-world-map-mercator-equal-earth-africa",
    },
    {
        "rank_no": 46,
        "title": "尼泊尔为泥石流洪灾中逾1300名遇难者举行全国哀悼日",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/nepal-holds-day-of-mourning-for-more-than-1300-killed-in-floods",
    },
    {
        "rank_no": 47,
        "title": "联合国称黎以紧张局势升级，加沙迎来重要援助物资运送",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168275",
    },
    {
        "rank_no": 48,
        "title": "联合国人权报告警告西岸三个难民营面临强制流离风险",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168282",
    },
    {
        "rank_no": 49,
        "title": "菲律宾警告在美韩削减军演背景下中国可能重新强化地区存在",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/philippines-warns-china-may-reassert-itself-amid-us-south-korea-drill-cuts",
    },
    {
        "rank_no": 50,
        "title": "以色列军队在约旦河西岸击毙一名巴勒斯坦嫌疑人",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/israeli-wounded-in-stabbing-in-occupied-west-bank",
    },
]

MAX_CONTENT = 20000
TRANSLATE_CHUNK = 480


def _translator():
    return MyMemoryTranslator(source="en-US", target="zh-CN")


def _chunk_text(text: str, size: int = TRANSLATE_CHUNK) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= size:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            split = text.rfind(". ", start, end)
            if split > start + 120:
                end = split + 1
        parts.append(text[start:end].strip())
        start = end
    return [p for p in parts if p]


def _trim_for_translation(text: str, max_chars: int = 3500) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    for marker in (
        "Related Stories",
        "Sign up for",
        "Email address",
        "Share Save",
        "Add as preferred on Google",
        "View image in fullscreen",
    ):
        idx = text.find(marker)
        if idx > 400:
            text = text[:idx].strip()
    if len(text) > max_chars:
        cut = text.rfind(". ", 0, max_chars)
        text = text[: cut + 1 if cut > 400 else max_chars].strip()
    return text


def translate_to_chinese(text: str) -> str:
    text = _trim_for_translation(text)
    if len(text) < 80:
        return ""
    if re.search(r"[\u4e00-\u9fff]{20,}", text[:500]):
        return text[:MAX_CONTENT]
    out: list[str] = []
    translator = _translator()
    for chunk in _chunk_text(text):
        try:
            out.append(translator.translate(chunk))
        except Exception as exc:
            print(f"WARN translate chunk failed: {exc}", file=sys.stderr)
            return ""
    merged = re.sub(r"\n{3,}", "\n\n", "\n\n".join(out)).strip()
    return merged[:MAX_CONTENT]


def build(run_date: str | None = None) -> list[dict]:
    out: list[dict] = []
    for item in ITEMS:
        title = item["title"]
        url = item.get("url")
        content = item.get("manual_content") or ""
        region = item["region"]
        if url and not content:
            match_title = title if region == "domestic" else ""
            result = fetch(url, match_title)
            raw = result.get("content") or ""
            if not raw:
                print(
                    f"WARN rank {item['rank_no']}: fetch failed ({result.get('error')})",
                    file=sys.stderr,
                )
            elif region == "international":
                content = translate_to_chinese(raw)
                if not content:
                    print(
                        f"WARN rank {item['rank_no']}: translation failed",
                        file=sys.stderr,
                    )
            else:
                content = raw
        row = {
            "rank_no": item["rank_no"],
            "title": title,
            "source": item["source"],
            "region": region,
            "url": url,
            "content": content,
        }
        out.append(row)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="YYYY-MM-DD, default today Asia/Shanghai")
    parser.add_argument(
        "--output",
        help="JSON output path (default data/daily_news_<date>.json)",
    )
    parser.add_argument("--insert", action="store_true", help="run insert_daily_news.py")
    args = parser.parse_args()

    run_date = args.date or datetime.now(TZ).date().isoformat()
    out_path = Path(args.output or f"data/daily_news_{run_date}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = build(run_date)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    domestic = sum(1 for r in rows if r["region"] == "domestic")
    international = sum(1 for r in rows if r["region"] == "international")
    with_content = sum(1 for r in rows if r.get("content") and len(r["content"]) >= 80)
    print(
        f"Wrote {len(rows)} items to {out_path} "
        f"({domestic} domestic / {international} international, "
        f"{with_content} with content>=80 chars)"
    )

    if args.insert:
        import subprocess

        script = Path(__file__).resolve().parent / "insert_daily_news.py"
        cmd = [sys.executable, str(script), "--json", str(out_path), "--date", run_date]
        subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
