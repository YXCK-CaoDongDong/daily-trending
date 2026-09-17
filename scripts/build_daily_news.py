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
        "title": "今年第25号台风“杜鹃”在西北太平洋生成",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-17/10697969.shtml",
    },
    {
        "rank_no": 2,
        "title": "国家安全部披露AI“劫持”网站并偷建“地下论坛”案件细节",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-17/10697964.shtml",
    },
    {
        "rank_no": 3,
        "title": "南方医科大学通报学生坠楼事件，排除他杀并成立工作专班",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34082570",
    },
    {
        "rank_no": 4,
        "title": "受赠文物事件处理结果公布，南京博物院原院长徐湖平获刑三年",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34081492",
    },
    {
        "rank_no": 5,
        "title": "游客建议泸州东站更名，12306客户端已增加弹窗提示",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34082760",
    },
    {
        "rank_no": 6,
        "title": "中国夏粮收购接近尾声，累计收购小麦1亿吨",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-16/10697674.shtml",
    },
    {
        "rank_no": 7,
        "title": "中国男篮击败沙特队晋级杭州亚运会四强",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-16/10697633.shtml",
    },
    {
        "rank_no": 8,
        "title": "王毅会见巴西总统首席特别顾问阿莫林",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-16/10697932.shtml",
    },
    {
        "rank_no": 9,
        "title": "王毅同伊朗外长阿拉格齐会谈",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-16/10697597.shtml",
    },
    {
        "rank_no": 10,
        "title": "中国航天科技集团发声明打假，“华航天特”为假冒国企",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-16/10697524.shtml",
    },
    {
        "rank_no": 11,
        "title": "A股收评：超4100只个股飘红，三大指数集体收涨",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-16/10697581.shtml",
    },
    {
        "rank_no": 12,
        "title": "平陆运河建成通航",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260916/5234f5b980d545ff8d475273b99e6c67/c.html",
    },
    {
        "rank_no": 13,
        "title": "首批国家基本医保医疗服务项目目录制定方案发布",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260916/e0955995950d4d8a967fcb652ccbd5b1/c.html",
    },
    {
        "rank_no": 14,
        "title": "两部门对海南启动国家自然灾害救助四级应急响应",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260915/4ca21639d4894e06aaba070d0552478e/c.html",
    },
    {
        "rank_no": 15,
        "title": "国家网信办发布近期网络安全等领域执法典型案例",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/legal/20260915/3f7196f558fd45cc9165cd1cafa9246b/c.html",
    },
    {
        "rank_no": 16,
        "title": "工业和信息化部要求健全行业账款支付规则",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260914/250ef9aec34246eaa9d3cbe9746ac639/c.html",
    },
    {
        "rank_no": 17,
        "title": "国家卫健委要求进一步营造生育友好环境",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260914/148fd317428541bdb516c720d76a7802/c.html",
    },
    {
        "rank_no": 18,
        "title": "2026年8月份70个大中城市商品住宅销售价格变动情况公布",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260915/f3f1c5b1be9c4dd5917caed8851f0442/c.html",
    },
    {
        "rank_no": 19,
        "title": "全国碳市场进入快速发展新阶段",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260915/cd1edd3172b540f490215a4d81463233/c.html",
    },
    {
        "rank_no": 20,
        "title": "从事出境入境中介服务的机构和人员今起实行备案管理",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260915/dce22252d4e6442a98950c5cd0a208ce/c.html",
    },
    {
        "rank_no": 21,
        "title": "今年以来司法部已审查完成37件立法项目",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260916/0a7272a917f74573812c441d2f2040df/c.html",
    },
    {
        "rank_no": 22,
        "title": "一箭9星，引力一号遥三运载火箭发射成功",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/photo/20260916/3b3d6da83ed244efbb1745ae61eb1041/c.html",
    },
    {
        "rank_no": 23,
        "title": "贵州省妇联原党组书记、主席涂妍被开除党籍和公职",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260915/60cc357f5cfc49e5a6607e637c07d3f6/c.html",
    },
    {
        "rank_no": 24,
        "title": "吉林工商学院原党委书记张吉锋接受纪律审查和监察调查",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/legal/20260915/8e3bd888704d49159ec69847670cab2a/c.html",
    },
    {
        "rank_no": 25,
        "title": "巴基斯坦召见印度临时代办，就印巴军舰碰撞事件提出抗议",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/09-17/10697953.shtml",
    },
    {
        "rank_no": 26,
        "title": "时隔三年多，美联储宣布加息25个基点",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/09-17/10697952.shtml",
    },
    {
        "rank_no": 27,
        "title": "特朗普签署备忘录，要求将加拿大产品排除出美政府采购计划",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/09-17/10697959.shtml",
    },
    {
        "rank_no": 28,
        "title": "东盟通过《马尼拉宣言》，强化灾害韧性合作",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/09-17/10697949.shtml",
    },
    {
        "rank_no": 29,
        "title": "英国宣布采购方案，为陆军列装新型侦察无人机",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/09-17/10697950.shtml",
    },
    {
        "rank_no": 30,
        "title": "韩国法院宣判民间无人机“侵入朝鲜”案",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gj/2026/09-16/10697548.shtml",
    },
    # international 31-50
    {
        "rank_no": 31,
        "title": "美联储三年来首次加息",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cw4gmlyvj422o",
    },
    {
        "rank_no": 32,
        "title": "美国众议院投票认定爱泼斯坦商业伙伴布莱克藐视国会",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c62l8g8qlr0ko",
    },
    {
        "rank_no": 33,
        "title": "加沙一栋受损建筑倒塌致21人死亡，其中8名为儿童",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cvp8d00j9gg5o",
    },
    {
        "rank_no": 34,
        "title": "欧盟委员会主席支持加拿大成为欧盟“联系成员”的计划",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cjwyzrr9d3dko",
    },
    {
        "rank_no": 35,
        "title": "照片显示伊朗袭击在美国多处设施造成广泛破坏",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c8g49e0gwxeno",
    },
    {
        "rank_no": 36,
        "title": "沙特阿拉伯称在麦加以南击落胡塞武装无人机",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cr89jqd1w45eo",
    },
    {
        "rank_no": 37,
        "title": "美国指控俄罗斯试图在海外暗杀乌克兰盟友",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cjp3077led9qo",
    },
    {
        "rank_no": 38,
        "title": "美国限制部分南非官员签证，指其存在所谓反白人歧视",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cqy0z5y7wnp2o",
    },
    {
        "rank_no": 39,
        "title": "OpenAI首席执行官称世界“有权感到害怕”，但应信任AI企业",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cqx2zpj4y525o",
    },
    {
        "rank_no": 40,
        "title": "八位德国州长支持默茨，外界猜测其政治前景",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c6dj4nn0n97ro",
    },
    {
        "rank_no": 41,
        "title": "特朗普幕僚长苏茜·威尔斯宣布已无癌症",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c6j9xrx80ekro",
    },
    {
        "rank_no": 42,
        "title": "两名英国人在瑞士阿尔卑斯山轻型飞机坠毁事故中遇难",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cw62jvpele45o",
    },
    {
        "rank_no": 43,
        "title": "哥伦比亚和巴西成为杀害环保活动人士最致命国家",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c6kgxjl35822o",
    },
    {
        "rank_no": 44,
        "title": "Snapchat称愿意为青少年实施每日使用时间限制",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/cr3wjz3edd10o",
    },
    {
        "rank_no": 45,
        "title": "首尔一家米其林餐厅因使用蚂蚁作装饰被罚款",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.co.uk/news/articles/c639m42y43v4o",
    },
    {
        "rank_no": 46,
        "title": "非洲萨赫勒地区与基地组织和“伊斯兰国”相关暴力将创纪录",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/16/al-qaida-and-is-linked-violence-in-africas-sahel-belt-set-to-hit-record-levels-this-year",
    },
    {
        "rank_no": 47,
        "title": "美国将限制部分南非官员签证，指其存在反白人歧视",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/16/us-visa-restrictions-south-africans-trump-claims-anti-white-discrimination",
    },
    {
        "rank_no": 48,
        "title": "七名女性遗体被发现，加剧南非对女性暴力的愤怒",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/16/discovery-women-bodies-anger-femicide-south-africa",
    },
    {
        "rank_no": 49,
        "title": "巴西最高法院在总统选举前爆发激烈内斗",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/15/brazil-supreme-court-presidential-election",
    },
    {
        "rank_no": 50,
        "title": "环保活动人士在威胁加剧下组建自卫单位保护自然与土地",
        "source": "The Guardian",
        "region": "international",
        "url": "https://www.theguardian.com/world/2026/sep/16/nature-land-defenders-self-defence-murder-organised-crime",
    },
]


def page_is_junk(html: str) -> bool:
    sample = html[:3000]
    if JUNK_TEXT.search(sample):
        # BBC embeds video placeholders with "Enable JavaScript" in the head area.
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
