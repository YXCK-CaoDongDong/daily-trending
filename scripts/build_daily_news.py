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
        "title": "潘展乐以47秒61夺得亚运会男子100米自由泳金牌",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260920/d3f78040e18d4573afa0f0bfc5edad36/c.html",
    },
    {
        "rank_no": 2,
        "title": "中国队在亚运会开幕后首个比赛日夺得11枚金牌",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-20/10700494.shtml",
    },
    {
        "rank_no": 3,
        "title": "中国队获亚运会女子4×100米自由泳接力冠军并创赛会纪录",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260920/7905f466227947ccae9beb6b9ed2a1b8/c.html",
    },
    {
        "rank_no": 4,
        "title": "13岁于子迪夺得亚运会女子200米蝶泳冠军并刷新赛会纪录",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260920/184db04580794448ab4b9c1578d9a9c4/c.html",
    },
    {
        "rank_no": 5,
        "title": "李刘畅逆转夺得亚运会现代五项男子个人赛金牌",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260920/d4309f1692b949279d3d75516966bb7f/c.html",
    },
    {
        "rank_no": 6,
        "title": "中美经贸磋商在美国纽约开始举行",
        "source": "人民网",
        "region": "domestic",
        "url": "http://world.people.com.cn/n1/2026/0921/c1002-40802269.html",
    },
    {
        "rank_no": 7,
        "title": "中办、国办印发《关于分类推进高校改革的意见》",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260920/a476a077ca5543e3b80da233c56ac0a8/c.html",
    },
    {
        "rank_no": 8,
        "title": "2026世界制造业大会在合肥开幕",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/photo/20260920/8f16624dff594e05a454ed515ff0fba7/c.html",
    },
    {
        "rank_no": 9,
        "title": "我国成功发射秦岭卫星01、02星等9颗卫星",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/tech/20260920/bfb42d6c5cfc4b9fa345f4c00ed823a7/c.html",
    },
    {
        "rank_no": 10,
        "title": "住房公积金新政施行，提取场景由6种增至9种",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260920/1eec00f12b7b43de8072dc521118d86e/c.html",
    },
    {
        "rank_no": 11,
        "title": "装修、交物业费可用住房公积金，“安居钱”越来越好用",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260920/41f50f1e87a440db91b2708fe253554a/c.html",
    },
    {
        "rank_no": 12,
        "title": "警惕高仿版证券交易App，多位股民被骗200万元",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-21/10700499.shtml",
    },
    {
        "rank_no": 13,
        "title": "国务院任免国家工作人员",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700173.shtml",
    },
    {
        "rank_no": 14,
        "title": "商务部：1至8月全国网上商品和服务零售额增长4.6%",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-20/10700213.shtml",
    },
    {
        "rank_no": 15,
        "title": "中国2025年科普专兼职人员超225万人",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700419.shtml",
    },
    {
        "rank_no": 16,
        "title": "两部门：到2030年我国农作物耕种收综合机械化率将超80%",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700056.shtml",
    },
    {
        "rank_no": 17,
        "title": "市场监管总局发布《婴幼儿配方食品标签标识问答》",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700116.shtml",
    },
    {
        "rank_no": 18,
        "title": "董建华先生公祭仪式在香港举行",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700067.shtml",
    },
    {
        "rank_no": 19,
        "title": "国家发展改革委印发石油天然气发展“十五五”规划",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-21/10700520.shtml",
    },
    {
        "rank_no": 20,
        "title": "人民日报评“第一学历歧视”：卡第一学历成部分企业招聘潜规则",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-15/10696493.shtml",
    },
    {
        "rank_no": 21,
        "title": "央视起底明码标价的骗保灰色产业链",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34111108",
    },
    {
        "rank_no": 22,
        "title": "全国用电量连续两月突破万亿千瓦时大关",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34109982",
    },
    {
        "rank_no": 23,
        "title": "最高检抗诉厘清“连续抢救”，工伤职工获赔92万元",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34108151",
    },
    {
        "rank_no": 24,
        "title": "2026年国家网络安全宣传周强调防范网络风险",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ll/2026/09-20/10700477.shtml",
    },
    {
        "rank_no": 25,
        "title": "国务院印发《教育发展“十五五”规划》",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-20/10700232.shtml",
    },
    {
        "rank_no": 26,
        "title": "财税专家称中国税收收入与经济增长基本相匹配",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-20/10700161.shtml",
    },
    {
        "rank_no": 27,
        "title": "海南环岛高铁推出“自行车随身行”服务",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-20/10700096.shtml",
    },
    {
        "rank_no": 28,
        "title": "2026年全国城市联合招聘高校毕业生秋季专项活动启动",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260920/e20d42a72077475f8c31d8143c9d42c7/c.html",
    },
    {
        "rank_no": 29,
        "title": "国新办发布会介绍“十五五”时期市场监管工作",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260920/790d4ba31ea6456b9ff4f31d73ebb4ed/c.html",
    },
    {
        "rank_no": 30,
        "title": "日本海上保安厅发现疑似失联“全球鹰”无人机残骸",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/09-15/10697054.shtml",
    },
    # international 31-50
    {
        "rank_no": 31,
        "title": "德国总理默茨称州选举结果对基民盟是“灾难”",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cvwyz29n0nn2o",
    },
    {
        "rank_no": 32,
        "title": "胡塞武装称以弹道导弹袭击沙特首都利雅得",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cwly5d9v7r43o",
    },
    {
        "rank_no": 33,
        "title": "乌克兰向莫斯科发动大规模无人机袭击",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c34gdjk1ne8yo",
    },
    {
        "rank_no": 34,
        "title": "特朗普签署全面俄罗斯制裁法案",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cqvgy34ndj4eo",
    },
    {
        "rank_no": 35,
        "title": "特朗普宣布美国将组建“人工智能部队”",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cqlykr2vrv04o",
    },
    {
        "rank_no": 36,
        "title": "北约欢迎格陵兰岛协议，特朗普称将获“永久安全控制”",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c63d7lexyym1o",
    },
    {
        "rank_no": 37,
        "title": "巴基斯坦前总理伊姆兰·汗之妹被捕",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cm36l2pye2kwo",
    },
    {
        "rank_no": 38,
        "title": "印尼性侵教师刑期未满即秘密提前获释",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c9zrz0nl4p70o",
    },
    {
        "rank_no": 39,
        "title": "南非连续发现遇害女性遗体引发社会恐惧",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cjkg71e67k17o",
    },
    {
        "rank_no": 40,
        "title": "特朗普禁止部分媒体后记者被拒白宫通行",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cj4gklz9dxplo",
    },
    {
        "rank_no": 41,
        "title": "俄罗斯战时选举投票结束，执政党预计将占主导",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/20/polls-close-in-russian-wartime-election-with-ruling-party-set-to-dominate",
    },
    {
        "rank_no": 42,
        "title": "法国将召见伊朗大使，因德黑兰关闭法语中心",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/20/france-to-summon-iran-envoy-after-language-centre-closure-in-tehran",
    },
    {
        "rank_no": 43,
        "title": "卡塔尔首相称美以与伊朗冲突余波如“地震”",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/20/qatari-pm-warns-against-cycles-of-escalation-in-the-middle-east",
    },
    {
        "rank_no": 44,
        "title": "美中在特朗普与习近平峰会前开启高层会谈",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/economy/2026/9/20/us-china-open-high-level-talks-ahead-of-trump-xi-summit",
    },
    {
        "rank_no": 45,
        "title": "马克龙与加拿大总理卡尼宣布加强双边关系",
        "source": "Al Jazeera",
        "region": "international",
        "url": "https://www.aljazeera.com/news/2026/9/20/frances-macron-and-canadas-carney-announce-plans-to-build-stronger-ties",
    },
    {
        "rank_no": 46,
        "title": "18名嫌疑人被引渡至美国，涉2021年海地总统遇刺案",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/20/more-than-a-dozen-arrested-in-connection-with-assassination-of-haitian-president",
    },
    {
        "rank_no": 47,
        "title": "联合国：尼泊尔洪水“毁灭性”破坏警示喜马拉雅气候威胁",
        "source": "联合国",
        "region": "international",
        "url": "https://news.un.org/feed/view/en/story/2026/09/1168365",
    },
    {
        "rank_no": 48,
        "title": "智利前总统巴切莱特退出联合国秘书长竞选",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/20/former-president-of-chile-withdraws-from-race-to-become-un-secretary-general",
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
        "title": "朝鲜在特朗普与习近平峰会前发射两枚短程弹道导弹",
        "source": "韩联社",
        "region": "international",
        "url": "https://en.yna.co.kr/view/AEN20250920002700315?section=nk-nk",
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
