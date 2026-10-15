#!/usr/bin/env python3
"""Generate daily news JSON for 2026-09-10 and insert into database."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")

ITEMS = [
    # domestic 30
    {
        "rank_no": 1,
        "title": "在第四十二个教师节到来之际，习近平向全国广大教师和教育工作者致以节日祝贺和诚挚问候",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34037833",
    },
    {
        "rank_no": 2,
        "title": "香港特区首任行政长官董建华逝世，享年89岁",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34036031",
    },
    {
        "rank_no": 3,
        "title": "“梅姨”真人照首次曝光，系2010年登记照",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34038961",
    },
    {
        "rank_no": 4,
        "title": "郑钦文不敌2号种子莱巴金娜，止步美网女单八强",
        "source": "央广网",
        "region": "domestic",
        "url": "https://www.cnr.cn/newscenter/native/gd/20260910/t20260910_527809542.shtml",
    },
    {
        "rank_no": 5,
        "title": "中国女篮以75比72险胜波多黎各队，晋级女篮世界杯八强",
        "source": "新浪新闻",
        "region": "domestic",
        "url": "https://news.sina.com.cn/zx/2026-09-10/doc-inirhezn8280930.shtml",
    },
    {
        "rank_no": 6,
        "title": "孙绍骋严重违纪违法被开除党籍和公职",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-09/10693549.shtml",
    },
    {
        "rank_no": 7,
        "title": "苹果发布首款折叠屏手机iPhone Duo，国行起售价15999元",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://m.ithome.com/html/1000514.htm",
    },
    {
        "rank_no": 8,
        "title": "苹果iPhone 18 Pro和Pro Max国行起售价分别为9999元和10999元",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://m.ithome.com/html/1000515.htm",
    },
    {
        "rank_no": 9,
        "title": "DeepSeek拟登陆科创板，已聘请中信证券筹备IPO",
        "source": "新浪财经",
        "region": "domestic",
        "url": "https://finance.sina.com.cn/stock/vcpe/2026-09-10/doc-inirhvxa5400039.shtml",
    },
    {
        "rank_no": 10,
        "title": "上交所向星宇股份下发监管工作函，公司同日致歉更正年报错误",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34038580",
    },
    {
        "rank_no": 11,
        "title": "清华附中赵松源破格入选成年国足，为职业化以来首位在读高中生",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34036390",
    },
    {
        "rank_no": 12,
        "title": "张新当选中国羽毛球协会主席",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260908/321964e70440456cb007e7a8b3ea96a2/c.html",
    },
    {
        "rank_no": 13,
        "title": "上海10月1日起实现生育保障个人无自付",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34036322",
    },
    {
        "rank_no": 14,
        "title": "西安31岁女护士遭男友杀害案二审宣判维持死刑判决",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34037543",
    },
    {
        "rank_no": 15,
        "title": "重庆酉阳通报高一新生报到次日坠楼，排除刑案可能",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34039322",
    },
    {
        "rank_no": 16,
        "title": "宁夏7人因假借应聘实施“劳务碰瓷”软暴力敲诈勒索获刑",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/legal/20260908/e621d03ebd5b428da848ed6f9c6dc07e/c.html",
    },
    {
        "rank_no": 17,
        "title": "8月新能源乘用车零售100.5万辆，同比下降10.1%",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-08/10692760.shtml",
    },
    {
        "rank_no": 18,
        "title": "2026年8月份居民消费价格同比上涨0.8%",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-09/10693027.shtml",
    },
    {
        "rank_no": 19,
        "title": "美国指责中国AI公司蒸馏美企技术，外交部称中国AI发展是高水平科技自立自强成果",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34037416",
    },
    {
        "rank_no": 20,
        "title": "2026年服贸会开幕",
        "source": "网易新闻",
        "region": "domestic",
        "url": "https://www.163.com/dy/article/L6D2NAHH05346RC6.html",
    },
    {
        "rank_no": 21,
        "title": "起底年售3.9亿元“神药”直播间：假专家、假神药，卖货全靠演",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34024472",
    },
    {
        "rank_no": 22,
        "title": "《焦点访谈》曝光黑加油点后，多地连夜开展核查整治",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34036774",
    },
    {
        "rank_no": 23,
        "title": "华为发布麒麟9050 Pro芯片",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://m.ithome.com/html/999970.htm",
    },
    {
        "rank_no": 24,
        "title": "宇树科技宣布全球首次实现世界模型实时驱动全自主人形机器人格斗",
        "source": "IT之家",
        "region": "domestic",
        "url": "https://www.ithome.com/0/999/432.htm",
    },
    {
        "rank_no": 25,
        "title": "89岁时尚博主康康爷爷在睡梦中离世",
        "source": "网易新闻",
        "region": "domestic",
        "url": "https://www.163.com/dy/article/L6DN7PMP0537B1I5.html",
    },
    {
        "rank_no": 26,
        "title": "宁德时代回应网传宜宾基地员工过激行为称非本公司并已报警",
        "source": "新浪财经",
        "region": "domestic",
        "url": "https://finance.sina.com.cn/jjxw/2026-09-09/doc-inirfqcu3672181.shtml",
    },
    {
        "rank_no": 27,
        "title": "理想等车企“去宁化”加速，宁德时代股价创年内新低",
        "source": "新浪财经",
        "region": "domestic",
        "url": "https://finance.sina.com.cn/jjxw/2026-09-09/doc-inirfivw8605047.shtml",
    },
    {
        "rank_no": 28,
        "title": "美日韩在东海举行联合演习",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34038787",
    },
    {
        "rank_no": 29,
        "title": "多地鼓励高校租购存量商品房，补齐床位短板并助力去库存",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34030852",
    },
    {
        "rank_no": 30,
        "title": "俄罗斯外交部敦促日本全面承认二战结果并停止美化侵略历史",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/08-21/10681577.shtml",
    },
    # international 20
    {
        "rank_no": 31,
        "title": "苹果新任CEO以首款折叠iPhone开启重大设计变革",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/clyjd1jnd03o",
    },
    {
        "rank_no": 32,
        "title": "英国西岸岸制裁后，美国反应克制或反映双方分歧",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cevw2lxnwk9o",
    },
    {
        "rank_no": 33,
        "title": "公开记录显示特朗普向三名助手各赠送4.5万美元现金",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c046rxw93xlo",
    },
    {
        "rank_no": 34,
        "title": "美胡塞冲突后国际油价首次突破每桶100美元",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cyvznqypz0yo",
    },
    {
        "rank_no": 35,
        "title": "西班牙情报部门在大批移民涌入休达前已收到预警",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/ced7vj2gv82o",
    },
    {
        "rank_no": 36,
        "title": "德国极右翼在萨克森-安哈尔特州选举获胜后，默茨在辩论中抨击选择党",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c98679wr78do",
    },
    {
        "rank_no": 37,
        "title": "伊朗因核不履约被提交联合国安理会审议",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/ckgwj4kl5lno",
    },
    {
        "rank_no": 38,
        "title": "俄乌无人机战持续，摩尔多瓦边境冲突致2人死亡",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cvgyvpxe3yjo",
    },
    {
        "rank_no": 39,
        "title": "特朗普称伊朗战争将在美国中期选举后立即结束",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/9/trump-says-iran-war-will-end-immediately-after-us-midterm-elections",
    },
    {
        "rank_no": 40,
        "title": "美伊霍尔木兹海峡冲突威胁海湾水域安全",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/9/why-us-iran-war-over-hormuz-is-threatening-the-gulfs-waters",
    },
    {
        "rank_no": 41,
        "title": "挪威首相称泽连斯基专机赴奥斯陆途中险些被无人机击中",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/9/zelenskyys-plane-almost-hit-by-drone-on-way-to-oslo-norwegian-pm-says",
    },
    {
        "rank_no": 42,
        "title": "人工智能正变得更难控制，人类能否继续主导",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c74edv9887eo",
    },
    {
        "rank_no": 43,
        "title": "泰特兄弟在美羁押期间继续抗辩，拒绝英国引渡",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cp849rlrrmlo",
    },
    {
        "rank_no": 44,
        "title": "波兰平交道口火车撞卡车事故致1名乘客死亡",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cp30el2dkdlo",
    },
    {
        "rank_no": 45,
        "title": "乌干达宣布退出哈里王子发起的“不可征服运动会”",
        "source": "BBC News",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/c3d7pzyjzllo",
    },
    {
        "rank_no": 46,
        "title": "全球基金警告针对教育的袭击创纪录新高",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168300",
    },
    {
        "rank_no": 47,
        "title": "联合国人权高专蒂尔克呼吁在AI成为人类生存风险前采取行动",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168288",
    },
    {
        "rank_no": 48,
        "title": "尼泊尔洪灾后呼吁气候正义与补偿",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168305",
    },
    {
        "rank_no": 49,
        "title": "联合国报告指外部势力加剧苏丹战争",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168270",
    },
    {
        "rank_no": 50,
        "title": "联合国警告船舶和船员日益卷入无关冲突交火",
        "source": "UN News",
        "region": "international",
        "url": "https://news.un.org/en/story/2026/09/1168297",
    },
]


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
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
