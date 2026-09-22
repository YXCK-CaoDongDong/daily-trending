#!/usr/bin/env python3
"""Build final daily news JSON: fetch each article individually."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_news_candidates import fetch, extract_article_text, JUNK_TEXT

SELECTED = [
    # domestic 1-30
    {
        "rank_no": 1,
        "title": "中共中央政治局召开会议，讨论拟提请二十届五中全会审议的文件",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34114731",
    },
    {
        "rank_no": 2,
        "title": "张又侠、刘振立严重违纪违法被开除党籍军籍",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700958.shtml",
    },
    {
        "rank_no": 3,
        "title": "广东省人大常委会党组成员覃伟中被查",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700846.shtml",
    },
    {
        "rank_no": 4,
        "title": "王毅同德国外长瓦德富尔通电话",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-22/10701192.shtml",
    },
    {
        "rank_no": 5,
        "title": "两部门紧急拨付2亿元支持4省自然灾害应急抢险救灾",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700953.shtml",
    },
    {
        "rank_no": 6,
        "title": "市场监管总局开展月饼专项抽检，安全状况总体稳定",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-21/10700801.shtml",
    },
    {
        "rank_no": 7,
        "title": "中国“快递进村”邮政兜底试点工作取得阶段性成效",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-21/10700956.shtml",
    },
    {
        "rank_no": 8,
        "title": "中国最高法：“先刑后民”并非适用于所有案件",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700798.shtml",
    },
    {
        "rank_no": 9,
        "title": "国家发展改革委印发石油天然气发展“十五五”规划",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-21/10700520.shtml",
    },
    {
        "rank_no": 10,
        "title": "国务院印发《教育发展“十五五”规划》",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700232.shtml",
    },
    {
        "rank_no": 11,
        "title": "住房公积金新政施行，提取场景由6种增至9种",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260920/1eec00f12b7b43de8072dc521118d86e/c.html",
    },
    {
        "rank_no": 12,
        "title": "国务院任免国家工作人员",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700173.shtml",
    },
    {
        "rank_no": 13,
        "title": "商务部：1至8月全国网上商品和服务零售额增长4.6%",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-20/10700213.shtml",
    },
    {
        "rank_no": 14,
        "title": "两部门：到2030年我国农作物耕种收综合机械化率将超80%",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700056.shtml",
    },
    {
        "rank_no": 15,
        "title": "我国发放首批数据产权“身份证”",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260921/0dc3ff66bbc048aaadeb6343f4de24f2/c.html",
    },
    {
        "rank_no": 16,
        "title": "重庆理工大学通报“廖某被我校原教师李某性侵后报警未立案”",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34117570",
    },
    {
        "rank_no": 17,
        "title": "咸阳一新生儿遭月子中心护工拍打案一审裁定涉嫌虐待移送公安",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34116356",
    },
    {
        "rank_no": 18,
        "title": "9月22日亚运会赛场将决出25枚金牌",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-22/10701207.shtml",
    },
    {
        "rank_no": 19,
        "title": "潘展乐以47秒61夺得亚运会男子100米自由泳金牌",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260920/d3f78040e18d4573afa0f0bfc5edad36/c.html",
    },
    {
        "rank_no": 20,
        "title": "13岁于子迪夺得亚运会女子200米蝶泳冠军并刷新赛会纪录",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260920/184db04580794448ab4b9c1578d9a9c4/c.html",
    },
    {
        "rank_no": 21,
        "title": "瓦卡金沙江大桥建成，红军长征入川地再增一座新桥",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260921/a1a747129da04d20bae93e4e763d3ec2/c.html",
    },
    {
        "rank_no": 22,
        "title": "中化集团原副总经理冯志斌一审被判十九年",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700839.shtml",
    },
    {
        "rank_no": 23,
        "title": "A股收评：超4500只个股飘红，三大指数集体收涨",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-21/10700781.shtml",
    },
    {
        "rank_no": 24,
        "title": "全国用电量连续两月突破万亿千瓦时大关",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34109982",
    },
    {
        "rank_no": 25,
        "title": "装修、交物业费可用住房公积金，“安居钱”越来越好用",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260920/41f50f1e87a440db91b2708fe253554a/c.html",
    },
    {
        "rank_no": 26,
        "title": "2026世界制造业大会在合肥开幕",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/photo/20260920/8f16624dff594e05a454ed515ff0fba7/c.html",
    },
    {
        "rank_no": 27,
        "title": "我国成功发射秦岭卫星01、02星等9颗卫星",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/tech/20260920/bfb42d6c5cfc4b9fa345f4c00ed823a7/c.html",
    },
    {
        "rank_no": 28,
        "title": "中办、国办印发《关于分类推进高校改革的意见》",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260920/a476a077ca5543e3b80da233c56ac0a8/c.html",
    },
    {
        "rank_no": 29,
        "title": "警惕高仿版证券交易App，多位股民被骗200万元",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-21/10700499.shtml",
    },
    {
        "rank_no": 30,
        "title": "市场监管总局发布《婴幼儿配方食品标签标识问答》",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700116.shtml",
    },
    # international 31-50
    {
        "rank_no": 31,
        "title": "英国将向沙特提供“防御性”军事支持",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cqlykpe4dk0yo",
    },
    {
        "rank_no": 32,
        "title": "也门人穿越红海逃离战争，胡塞武装与沙特支持力量冲突升级",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cw4gm7l742dmo",
    },
    {
        "rank_no": 33,
        "title": "CNN、MS NOW和Politico起诉特朗普政府白宫媒体禁令",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cm0e32rwvrryo",
    },
    {
        "rank_no": 34,
        "title": "德国总理默茨誓言为德国“民主未来”维持联合政府",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cqm27p8enwmko",
    },
    {
        "rank_no": 35,
        "title": "英国首次就1994年卢旺达种族灭绝提起指控",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cr2092216nywo",
    },
    {
        "rank_no": 36,
        "title": "强台风杜鹃袭击日本，数百万人被要求撤离",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cm3wj2lexl97o",
    },
    {
        "rank_no": 37,
        "title": "联合国专家称美国对所谓贩毒船只的打击可能构成反人类罪",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/ck5ye7v88qy7o",
    },
    {
        "rank_no": 38,
        "title": "谷歌因违反欧盟数据保护条例被爱尔兰监管机构罚款4.03亿欧元",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/ck1e52v16ngxo",
    },
    {
        "rank_no": 39,
        "title": "印尼性侵教师刑期未满即秘密提前获释",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c9zrz0nl4p70o",
    },
    {
        "rank_no": 40,
        "title": "南非警方调查多起女性遇害案，两人被控谋杀",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c617j2x01epjo",
    },
    {
        "rank_no": 41,
        "title": "美中在特朗普与习近平峰会前讨论人工智能安全计划",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c8vgyzn2d31yo",
    },
    {
        "rank_no": 42,
        "title": "美国主要机场航班延误，因施工人员切断电缆",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/ckvgyzzgvv4wo",
    },
    {
        "rank_no": 43,
        "title": "七个埃塞俄比亚反政府武装团体组成新联盟",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/ckp84pj8zpngo",
    },
    {
        "rank_no": 44,
        "title": "普京所在政党在俄罗斯议会选举中赢得绝对多数",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/20/polls-close-in-russian-wartime-election-with-ruling-party-set-to-dominate",
    },
    {
        "rank_no": 45,
        "title": "马克龙与加拿大总理卡尼宣布加强法加双边关系",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/21/france-canada-relations-eu-europe-macron-carney",
    },
    {
        "rank_no": 46,
        "title": "哥伦比亚宣布公共灾难状态，野火威胁热门旅游区",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/21/colombia-wildfire-villa-de-leyva",
    },
    {
        "rank_no": 47,
        "title": "联合国谴责胡塞武装试图袭击利雅得，也门流离失所者超13万人",
        "source": "联合国",
        "region": "international",
        "url": "https://news.un.org/feed/view/en/story/2026/09/1168387",
    },
    {
        "rank_no": 48,
        "title": "联合国人工智能小组呼吁加强保障措施",
        "source": "联合国",
        "region": "international",
        "url": "https://news.un.org/feed/view/en/story/2026/09/1168380",
    },
    {
        "rank_no": 49,
        "title": "尼日利亚监狱37名嫌疑人死亡，幸存者称难以呼吸",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/18/survivor-panic-struggle-breathe-nigeria-prison-cell-died-minna",
    },
    {
        "rank_no": 50,
        "title": "安大略犹太教堂附近发生枪战，一名男子和警察受伤",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/21/gunfire-belleville-ontario-synagogue-yom-kippur",
    },
]


def page_is_junk(html: str) -> bool:
    sample = html[:3000]
    if JUNK_TEXT.search(sample):
        if "bbc.co" in sample or "bbc.com" in sample:
            return False
        return True
    return False


def main() -> int:
    out = []
    for item in SELECTED:
        url = item["url"]
        html = fetch(url)
        content = ""
        if html and not page_is_junk(html):
            raw = extract_article_text(html, url)
            if raw and len(raw) >= 80 and not JUNK_TEXT.search(raw):
                content = raw[:20000]
        row = {
            "rank_no": item["rank_no"],
            "title": item["title"],
            "source": item["source"],
            "region": item["region"],
            "url": url,
            "content": content,
        }
        out.append(row)
        status = "OK" if content else "EMPTY"
        print(f"{item['rank_no']:2d} {status} {len(content):5d} {url}", file=sys.stderr)
        time.sleep(0.35)
    path = Path("/workspace/data/raw_fetched.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
