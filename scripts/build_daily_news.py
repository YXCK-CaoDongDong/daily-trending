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

import time

from deep_translator import GoogleTranslator, MyMemoryTranslator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_article import fetch  # noqa: E402

TZ = ZoneInfo("Asia/Shanghai")

ITEMS: list[dict] = [
    # --- domestic 30 ---
    {
        "rank_no": 1,
        "title": "郑钦文在美网女单第四轮以2比0击败斯瓦泰克晋级八强",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260908/29cd5d73c8f743a08f8dc6675f20643b/c.html",
    },
    {
        "rank_no": 2,
        "title": "中国女篮在世界杯小组赛以71比51战胜意大利队",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-08/10692321.shtml",
    },
    {
        "rank_no": 3,
        "title": "国家安全部披露偷拍未公开战机、擅闯军事禁区等多起案件详情",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692311.shtml",
    },
    {
        "rank_no": 4,
        "title": "8家中央金融企业计划共增资3600亿元用于补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/6445db11e5a048eb932ae3e120061502/c.html",
    },
    {
        "rank_no": 5,
        "title": "财政部将发行3000亿元特别国债支持8家中央金融企业补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/d8c683a121174577abbecd8106bfa2b7/c.html",
    },
    {
        "rank_no": 6,
        "title": "最高法发文明确“AI换脸拟声”等涉人工智能纠纷案件裁判规则",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/legal/20260907/ce0e6790833740d3901d2448e22557ff/c.html",
    },
    {
        "rank_no": 7,
        "title": "信息通信行业发展“十五五”规划发布并列出13个主要指标",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260907/def9a4d503584f3698586a89db9755a1/c.html",
    },
    {
        "rank_no": 8,
        "title": "平陆运河将于9月16日正式建成通航",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260907/a0d38cc5fd8349f48d66cde06539015a/c.html",
    },
    {
        "rank_no": 9,
        "title": "中国证监会原副主席王建军受贿案一审被判处无期徒刑",
        "source": "人民网",
        "region": "domestic",
        "url": "http://society.people.com.cn/n1/2026/0907/c1008-40794127.html",
    },
    {
        "rank_no": 10,
        "title": "六部门联合印发意见推动历史经典产业高质量发展",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-07/10691743.shtml",
    },
    {
        "rank_no": 11,
        "title": "华为发布麒麟9050 Pro芯片及多款终端产品",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://www.ithome.com/0/999/416.htm",
    },
    {
        "rank_no": 12,
        "title": "小米澎程N70 Pro中大型五座增程SUV起售价20.99万元",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://www.ithome.com/0/999/456.htm",
    },
    {
        "rank_no": 13,
        "title": "多地市场监管部门严查赵一鸣、好想来等量贩零食门店计量问题",
        "source": "新浪财经",
        "region": "domestic",
        "url": "https://finance.sina.com.cn/stock/marketresearch/2026-09-06/doc-iniqxiqn9841812.shtml",
    },
    {
        "rank_no": 14,
        "title": "胖东来要求供应商填报员工社保和工时信息作为招商初筛必填项",
        "source": "界面新闻",
        "region": "domestic",
        "url": "https://www.jiemian.com/article/15047448.html",
    },
    {
        "rank_no": 15,
        "title": "CHINA GT上海站赛车碰撞起火组委会致歉并将进一步调查",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34019796",
    },
    {
        "rank_no": 16,
        "title": "山东临清先锋大桥步道桥板脱落致22岁行人坠河身亡",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34016288",
    },
    {
        "rank_no": 17,
        "title": "官方通报江西低保家庭女孩赴港看演唱会被取消全家低保资格",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-07/10692076.shtml",
    },
    {
        "rank_no": 18,
        "title": "贵州中医药大学第二附属医院伤医案犯罪嫌疑人被刑事拘留",
        "source": "央广网",
        "region": "domestic",
        "url": "https://news.cnr.cn/native/gd/kx/20260906/t20260906_527805734.shtml",
    },
    {
        "rank_no": 19,
        "title": "西藏吉隆“8·26”泥石流灾害已致43人遇难519人失联",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/12341483ea9e456b9b7d8935873ac295/c.html",
    },
    {
        "rank_no": 20,
        "title": "教育部回应中小学是否一定要买校服称坚持自愿购买原则",
        "source": "新京报",
        "region": "domestic",
        "url": "https://www.bjnews.com.cn/detail/1788657399129092.html",
    },
    {
        "rank_no": 21,
        "title": "延安至瑞金高铁正式开通",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260907/88bb97a93459400198b4893824b45594/c.html",
    },
    {
        "rank_no": 22,
        "title": "中国人民解放军陆军将派兵力赴俄罗斯参加实兵演习",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "http://www.chinanews.com.cn/gn/2026/09-07/10691812.shtml",
    },
    {
        "rank_no": 23,
        "title": "市场监管总局公布3起经营者集中反垄断审查典型案例",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-07/10691713.shtml",
    },
    {
        "rank_no": 24,
        "title": "江西省公安厅原党委委员万秀奇接受纪律审查和监察调查",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-06/10691532.shtml",
    },
    {
        "rank_no": 25,
        "title": "财政部积极支持有关中央金融企业补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260907/37ee3e8c29be4a17a52cbe4715e5735f/c.html",
    },
    {
        "rank_no": 26,
        "title": "多家银行上半年集中核销不良资产",
        "source": "央视网",
        "region": "domestic",
        "url": "https://finance.cctv.com/2026/09/04/ARTIuz2PcpgZOtcBlvLXzKHC260904.shtml",
    },
    {
        "rank_no": 27,
        "title": "内蒙古贺兰山综合科考发现6个新物种",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/travel/20260904/da6481c3ea7c465880975d682f7ed44c/c.html",
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
        "title": "郑钦文在美网女单第四轮再度上演让5追7后击败斯瓦泰克",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-08/10692300.shtml",
    },
    {
        "rank_no": 30,
        "title": "华为鸿蒙7正式发布并升级与苹果设备互联能力",
        "source": "界面新闻",
        "region": "domestic",
        "url": "https://www.jiemian.com/article/15065503.html",
    },
    # --- international 20 ---
    {
        "rank_no": 31,
        "title": "德国选择党在萨克森-安哈尔特州地方选举中获胜并考验主流政党“防火墙”",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/germany-afd-saxony-anhalt-election-firewall-902f5d0f4e3181e6565ba29f43204",
    },
    {
        "rank_no": 32,
        "title": "亚马逊货机在迈阿密国际机场冲出跑道起火致至少5人死亡",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/cargo-plane-crash-miami-airport-amazon-prime-d5118998e880f380a3fd8786e35f",
    },
    {
        "rank_no": 33,
        "title": "特朗普威胁阻止加拿大庞巴迪公务机在美销售",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c4gj8xx5010o",
    },
    {
        "rank_no": 34,
        "title": "英国国王查尔斯三世明确哈里与梅根仍为非在职王室成员",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c20lpevv7jlo",
    },
    {
        "rank_no": 35,
        "title": "尼泊尔为泥石流洪灾遇难者举行全国哀悼日",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/nepal-holds-day-of-mourning-for-more-than-1300-killed-in-floods",
    },
    {
        "rank_no": 36,
        "title": "伊朗称改进型弹道导弹体现其将对威胁采取先发制人行动",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/iran-us-war-strait-hormuz-ship-attack-a52beec77dc90af3d040d0553837ad20",
    },
    {
        "rank_no": 37,
        "title": "捷豹路虎计划在未来两年裁员4000人",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c36lx560jjko",
    },
    {
        "rank_no": 38,
        "title": "OpenAI首席科学家警告无人准备好应对人工智能后果",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cwyzrrd0kp7o",
    },
    {
        "rank_no": 39,
        "title": "约旦河西岸家长担心定居者袭击威胁儿童在校安全",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c3wj45g73g1o",
    },
    {
        "rank_no": 40,
        "title": "塞尔维亚数千人出席前波黑塞族军事领导人姆拉迪奇葬礼",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cn5dkk7yw74o",
    },
    {
        "rank_no": 41,
        "title": "俄乌和谈象征意义丰富但双方根本分歧仍然存在",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c980j5m8mpro",
    },
    {
        "rank_no": 42,
        "title": "武装男子在俄亥俄州竞选活动中冲向民主党州长候选人后被捕",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/czezyr81g23o",
    },
    {
        "rank_no": 43,
        "title": "联合国投票通过采用更能反映非洲真实面积的新世界地图",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/04/un-vote-world-map-mercator-equal-earth-africa",
    },
    {
        "rank_no": 44,
        "title": "联合国呼吁停止让非洲在地图上显得更小",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168284",
    },
    {
        "rank_no": 45,
        "title": "联合国寻求近5000万美元用于尼泊尔洪灾救援",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168281",
    },
    {
        "rank_no": 46,
        "title": "以色列空袭黎巴嫩南部造成至少11人死亡",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/israeli-air-attack-kills-at-least-10-people-in-southern-lebanon",
    },
    {
        "rank_no": 47,
        "title": "美国劳动节汽油价格创该假日历史新高",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/labor-day-record-high-gas-prices-dffb7d3fa06ef930aaeebc380e5e4e0e",
    },
    {
        "rank_no": 48,
        "title": "选择党在萨克森-安哈尔特州历史性胜选对德国及欧洲意味着什么",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c986w38r4j5o",
    },
    {
        "rank_no": 49,
        "title": "联合国人权报告警告西岸三个难民营面临强制流离风险",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168282",
    },
    {
        "rank_no": 50,
        "title": "伊朗能否在霍尔木兹海峡实施限制通行区域",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/can-iran-enforce-a-restricted-zone-in-the-strait-of-hormuz",
    },
]

MAX_CONTENT = 20000
TRANSLATE_CHUNK = 480


def _translators():
    return [
        MyMemoryTranslator(source="en-US", target="zh-CN"),
        GoogleTranslator(source="en", target="zh-CN"),
    ]


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
        "Most read",
        "Most watched",
    ):
        idx = text.find(marker)
        if idx > 400:
            text = text[:idx].strip()
    if len(text) > max_chars:
        cut = text.rfind(". ", 0, max_chars)
        text = text[: cut + 1 if cut > 400 else max_chars].strip()
    return text


def _translate_chunk(chunk: str) -> str:
    last_exc: Exception | None = None
    for translator in _translators():
        for attempt in range(3):
            try:
                time.sleep(0.35)
                return translator.translate(chunk)
            except Exception as exc:
                last_exc = exc
                time.sleep(1.5 * (attempt + 1))
    raise last_exc or RuntimeError("translation failed")


def translate_to_chinese(text: str) -> str:
    text = _trim_for_translation(text)
    if len(text) < 80:
        return ""
    if re.search(r"[\u4e00-\u9fff]{20,}", text[:500]):
        return text[:MAX_CONTENT]
    out: list[str] = []
    for chunk in _chunk_text(text):
        try:
            out.append(_translate_chunk(chunk))
        except Exception as exc:
            print(f"WARN translate chunk failed: {exc}", file=sys.stderr)
            return ""
    merged = re.sub(r"\n{3,}", "\n\n", "\n\n".join(out)).strip()
    return merged[:MAX_CONTENT]


def build() -> list[dict]:
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
        out.append(
            {
                "rank_no": item["rank_no"],
                "title": title,
                "source": item["source"],
                "region": region,
                "url": url,
                "content": content,
            }
        )
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

    rows = build()
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
