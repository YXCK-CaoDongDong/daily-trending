#!/usr/bin/env python3
"""Generate daily news JSON for 2026-09-09 and optionally insert."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_daily_news import build as fetch_and_translate  # noqa: E402

TZ = ZoneInfo("Asia/Shanghai")

ITEMS = [
    # domestic 30
    {
        "rank_no": 1,
        "title": "习近平同英国首相伯纳姆通电话",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692823.shtml",
    },
    {
        "rank_no": 2,
        "title": "香港首任特首董建华逝世，享年89岁",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-09/10692991.shtml",
    },
    {
        "rank_no": 3,
        "title": "《焦点访谈》曝光黑加油点后安徽、山东、河南连夜核查",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-09/10692997.shtml",
    },
    {
        "rank_no": 4,
        "title": "上海10月1日起实现生育保障个人无自付",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260908/cbb7adfb18bc41db878e87f1b75a043d/c.html",
    },
    {
        "rank_no": 5,
        "title": "武汉通报非法辅助生殖地下实验室已查封，8名涉案人员被控制",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-08/10692706.shtml",
    },
    {
        "rank_no": 6,
        "title": "高一女生在学校组织军训中遭强制猥亵，涉事教官有犯罪记录被刑拘",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34029849",
    },
    {
        "rank_no": 7,
        "title": "太子奶创始人李途纯在北京去世",
        "source": "第一财经",
        "region": "domestic",
        "url": "https://www.yicai.com/news/103356662.html",
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
        "title": "郑钦文第三次闯入美网女单八强",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260908/52bf371f372f464e90970e19fa3a8819/c.html",
    },
    {
        "rank_no": 10,
        "title": "女篮世界杯中国队大比分击败意大利队",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-08/10692321.shtml",
    },
    {
        "rank_no": 11,
        "title": "应急管理部原党委书记、部长王祥喜严重违纪违法被双开",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692684.shtml",
    },
    {
        "rank_no": 12,
        "title": "受贿1.48亿余元，山西省原省长金湘军一审被判死缓",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692685.shtml",
    },
    {
        "rank_no": 13,
        "title": "前8个月我国外贸增长17.6%，延续快速增长态势",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-08/10692686.shtml",
    },
    {
        "rank_no": 14,
        "title": "李强主持国务院第二十一次专题学习",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692820.shtml",
    },
    {
        "rank_no": 15,
        "title": "王毅同卡塔尔首相兼外交大臣穆罕默德会谈",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692839.shtml",
    },
    {
        "rank_no": 16,
        "title": "多部门印发通知持续扩大灵活就业人员等群体基本医保参保规模",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-08/10692597.shtml",
    },
    {
        "rank_no": 17,
        "title": "市场监管总局提出到2030年培育5000个以上放心消费集聚区",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-08/10692658.shtml",
    },
    {
        "rank_no": 18,
        "title": "西渝高铁朱家山隧道顺利贯通",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-08/10692628.shtml",
    },
    {
        "rank_no": 19,
        "title": "中国对尼泊尔第四批紧急援助物资启运",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692603.shtml",
    },
    {
        "rank_no": 20,
        "title": "江西遂川高坪镇泥石流已致12人遇难，仍有1人失联",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-08/10692924.shtml",
    },
    {
        "rank_no": 21,
        "title": "中国男足公布新一期集训名单，高中生球员赵松源入选",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-08/10692942.shtml",
    },
    {
        "rank_no": 22,
        "title": "DeepSeek官宣调整Flash系列模型定价",
        "source": "界面新闻",
        "region": "domestic",
        "url": "https://www.jiemian.com/article/15071191.html",
    },
    {
        "rank_no": 23,
        "title": "华为鸿蒙7发布24小时后升级终端设备数突破500万",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://www.ithome.com/0/999/895.htm",
    },
    {
        "rank_no": 24,
        "title": "华为Pura X View阔直板手机正式上市，起售价5999元",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://www.ithome.com/0/999/348.htm",
    },
    {
        "rank_no": 25,
        "title": "检察机关依法对李百安涉嫌受贿案提起公诉",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-08/10692583.shtml",
    },
    {
        "rank_no": 26,
        "title": "10家航空公司和5家线上售票平台完成机票超售整改",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-08/10692676.shtml",
    },
    {
        "rank_no": 27,
        "title": "美国虹吸全球铜库存，伦敦铜价再创新高",
        "source": "第一财经",
        "region": "domestic",
        "url": "https://www.yicai.com/news/103356634.html",
    },
    {
        "rank_no": 28,
        "title": "紫金矿业半年报出现“人民币政府”“新熊源”等低级错误并道歉",
        "source": "央视网",
        "region": "domestic",
        "url": "https://finance.cctv.com/2026/09/07/ARTImHdSHOQIXFmohts8nhr5260907.shtml",
    },
    {
        "rank_no": 29,
        "title": "1公里国道上扎堆近20家黑加油点，为何屡禁不绝",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-08/10692900.shtml",
    },
    {
        "rank_no": 30,
        "title": "安徽蚌埠一公司厂房发生火灾，暂未发现人员伤亡",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-08/10692334.shtml",
    },
    # international 20
    {
        "rank_no": 31,
        "title": "英国宣布对约旦河西岸定居点商品实施制裁，引发以色列强烈反应",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c4g7zen0vveo",
    },
    {
        "rank_no": 32,
        "title": "美国对加拿大酒类等商品实施进口禁令",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c99dm1000p7o",
    },
    {
        "rank_no": 33,
        "title": "OpenAI称在88小时内取得纳维-斯托克斯方程相关研究突破",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cy7zygy3rl2o",
    },
    {
        "rank_no": 34,
        "title": "俄罗斯无人机袭击基辅致5人死亡，乌克兰电视台大楼受损",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cn8m1k7p3v7o",
    },
    {
        "rank_no": 35,
        "title": "迈阿密货机冲出跑道起火，地面5人遇难",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/amazon-cargo-plane-crash-miami-airport-victims-6c23909e94ea2faedd28071749fc00e3",
    },
    {
        "rank_no": 36,
        "title": "14人因英吉利海峡最致命偷渡船难案受审",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cd94jn72w2yo",
    },
    {
        "rank_no": 37,
        "title": "苏丹医疗体系在援助削减后濒临崩溃，慈善组织发出警告",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c62m8247yleo",
    },
    {
        "rank_no": 38,
        "title": "尼泊尔为泥石流洪灾遇难者举行全国哀悼日",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/7/nepal-holds-day-of-mourning-for-more-than-1300-killed-in-floods",
    },
    {
        "rank_no": 39,
        "title": "加拿大价值200亿美元反制关税正式生效",
        "source": "Associated Press",
        "region": "international",
        "url": "https://apnews.com/article/canada-trump-carney-trade-war-tariffs-4620ffb5ecc029322217207fa6758431",
    },
    {
        "rank_no": 40,
        "title": "法国博物馆发生盗窃案，雷诺阿画作失窃",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c70drp0pyw2o",
    },
    {
        "rank_no": 41,
        "title": "安理会讨论叙利亚化学武器遗留问题",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168271",
    },
    {
        "rank_no": 42,
        "title": "联合国报告称外部势力加剧苏丹战争",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168270",
    },
    {
        "rank_no": 43,
        "title": "联合国秘书长要求以色列从黎巴嫩撤军",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168298",
    },
    {
        "rank_no": 44,
        "title": "第81届联合国大会新会期开幕",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168293",
    },
    {
        "rank_no": 45,
        "title": "英国禁止进口约旦河西岸定居点商品",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/8/uk-bans-goods-from-israeli-west-bank-settlements-what-that-really-means",
    },
    {
        "rank_no": 46,
        "title": "纽约官员称9·11袭击后有毒空气问题被长期误导",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cjdvyk3pm27o",
    },
    {
        "rank_no": 47,
        "title": "关税将对加拿大和美国民众造成何种经济代价",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cx2z4dv6vn2o",
    },
    {
        "rank_no": 48,
        "title": "美国称摧毁多艘伊朗油轮，伊朗革命卫队反击约旦美军基地",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/liveblog/2026/9/9/iran-war-live-us-hits-iranian-tankers-irgc-attacks-us-base-in-jordan",
    },
    {
        "rank_no": 49,
        "title": "赫格塞思调整五角大楼人事引发美国军政界争议",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cd94j8e9n12o",
    },
    {
        "rank_no": 50,
        "title": "研究线索显示地球升温速度可能快于此前估计",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c20917w25n4o",
    },
]


def main() -> int:
    import build_daily_news as bdn

    bdn.ITEMS = ITEMS
    run_date = datetime.now(TZ).date().isoformat()
    out_path = Path(__file__).resolve().parents[1] / "data" / f"daily_news_{run_date}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = bdn.build()
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    domestic = sum(1 for r in rows if r["region"] == "domestic")
    international = sum(1 for r in rows if r["region"] == "international")
    with_content = sum(1 for r in rows if r.get("content") and len(r["content"]) >= 80)
    print(
        f"Wrote {len(rows)} items to {out_path} "
        f"({domestic} domestic / {international} international, "
        f"{with_content} with content>=80 chars)"
    )

    script = Path(__file__).resolve().parent / "insert_daily_news.py"
    subprocess.run(
        [sys.executable, str(script), "--json", str(out_path), "--date", run_date],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
