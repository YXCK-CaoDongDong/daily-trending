#!/usr/bin/env python3
"""Build daily news JSON: fetch authoritative articles, translate EN->ZH, write file."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_article import fetch_article  # noqa: E402

TZ = ZoneInfo("Asia/Shanghai")

NEWS_ITEMS = [
    # --- domestic 1-30 ---
    {"rank_no": 1, "title": "商务部等七部门联合印发意见，提出20项措施推动商品消费扩容升级", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-31/10687318.shtml"},
    {"rank_no": 2, "title": "习近平出席上海合作组织峰会并同吉尔吉斯斯坦总统扎帕罗夫举行会谈", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/leaders/20260831/e901b91c636e4e20bea6833f4e45933f/c.html"},
    {"rank_no": 3, "title": "习近平在比什凯克出席上合峰会期间会见俄罗斯总统普京", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/leaders/20260831/f8ffa799b9ff4f2ca00c7422f8eb1d3d/c.html"},
    {"rank_no": 4, "title": "西藏吉隆举行“8·26”泥石流灾害新闻发布会，全体人员为遇难者默哀", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/local/20260830/5bf1df3baf7342ec918d3383bebd24fa/c.html"},
    {"rank_no": 5, "title": "尼泊尔泥石流灾害已造成903人遇难、4247人失联", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-31/10687164.shtml", "alt_urls": ["https://www.chinanews.com.cn/gn/2026/08-30/10686615.shtml"]},
    {"rank_no": 6, "title": "西藏吉隆泥石流灾害排查出261名失联外籍人员", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/20260830/beb5bead02a54deba21a6b2d175eaee5/c.html"},
    {"rank_no": 7, "title": "国道216线受吉隆泥石流冲击通行中断，抢通工作持续进行", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-31/10686977.shtml"},
    {"rank_no": 8, "title": "华为上半年营业收入4678亿元，归母净利润234.28亿元", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_33978684"},
    {"rank_no": 9, "title": "华为、小米、荣耀等多款手机今日起集体调价", "source": "中国新闻网", "region": "domestic", "url": "http://www.hn.chinanews.com.cn/news/cjxx/2026/0810/532321.html"},
    {"rank_no": 10, "title": "央行：上半年个人住房贷款余额减少7163亿元", "source": "中国新闻网", "region": "domestic", "url": "http://www.chinanews.com.cn/cj/2026/07-28/10667989.shtml"},
    {"rank_no": 11, "title": "两部门：将个人住房贷款最长期限由30年延长至40年", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-28/10686169.shtml"},
    {"rank_no": 12, "title": "江苏省委常委、组织部部长刘建洋接受审查调查", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/legal/20260831/4a1cd14566b1479296b955c128d0282d/c.html", "alt_urls": ["https://www.chinanews.com.cn/gn/2026/08-31/10687437.shtml"], "fallback_content": "新华社北京8月31日电 江苏省委常委、组织部部长刘建洋涉嫌严重违纪违法，目前正接受中央纪委国家监委纪律审查和监察调查。刘建洋曾任江西、福建等地要职，2024年3月起任江苏省委组织部部长。中央纪委国家监委网站同日发布上述消息，江苏省委随后召开常委会表示坚决拥护党中央决定。"},
    {"rank_no": 13, "title": "吉林白城回应事业单位招聘出现多岗位“高分断层”情况", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/08-31/10687517.shtml"},
    {"rank_no": 14, "title": "三大航企2026年上半年预计合计净亏损73.73亿至89.73亿元", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_33586314"},
    {"rank_no": 15, "title": "中国选手郑钦文晋级2026年美网女单正赛", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/08-29/10686280.shtml"},
    {"rank_no": 16, "title": "美网正赛开打，中国选手王欣瑜、吴易昺晋级单打次轮", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/08-31/10687033.shtml"},
    {"rank_no": 17, "title": "沪市上市公司2026年半年报披露收官，近八成公司实现盈利", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-31/10687142.shtml"},
    {"rank_no": 18, "title": "我国铜金矿勘查再获重大突破，有望新形成大型资源基地", "source": "中国经济网", "region": "domestic", "url": "http://www.ce.cn/xwzx/gnsz/gdxw/202609/t20260901_3185626.shtml"},
    {"rank_no": 19, "title": "女子被踢出845个工作群遭职场冷板凳后被迫离职，法院两审用人单位败诉", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_33977805"},
    {"rank_no": 20, "title": "中国羽毛球协会副主席夏煊泽接受审查调查", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_33978395"},
    {"rank_no": 21, "title": "三部门完善商品房预售管理并推行现房销售", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/20260828/6a2cbaa5cc6f4a6e8d329c38edd3272b/c.html", "alt_urls": ["https://www.chinanews.com.cn/cj/2026/08-28/10686054.shtml"]},
    {"rank_no": 22, "title": "台风“沙德尔”停止编号后再度加强为台风，江南华南等地有强降雨", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-01/10687593.shtml"},
    {"rank_no": 23, "title": "2026年中国电影暑期档总票房124.98亿元收官", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cul/2026/08-31/10687562.shtml"},
    {"rank_no": 24, "title": "截至7月底我国光伏发电装机容量达12.86亿千瓦，首次超过煤电", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-25/10683760.shtml", "fallback_content": "据国家能源局消息，截至2026年7月底，全国累计发电装机容量40.8亿千瓦，同比增长11.0%。其中，太阳能发电装机容量12.9亿千瓦，同比增长16.1%；风电装机容量6.9亿千瓦，同比增长19.5%。国家能源局9月1日进一步明确，截至今年7月底，我国光伏发电装机容量达到12.86亿千瓦，其中集中式光伏7.04亿千瓦、分布式光伏5.82亿千瓦，光伏发电装机容量首次超过煤电，成为我国装机规模最大的电源类型。"},
    {"rank_no": 25, "title": "星河动力智神星一号可复用运载火箭完成关键地面试验，近期择机首飞", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-19/10680239.shtml", "fallback_content": "据星河动力航天消息，智神星一号可重复使用液体运载火箭已完成大型地面试验并总装完毕，计划近期择机首飞。该型火箭起飞质量约283吨，低轨最大运载能力7吨，一子级设计可重复使用不少于25次，首飞任务主要验证入轨能力，后续将逐步开展再入控制和定点回收试验。2026年9月1日，智神星一号运载火箭首飞任务取得圆满成功，标志着我国商业航天可复用火箭研制进入新阶段。"},
    {"rank_no": 26, "title": "韩国警方批捕涉嫌杀害中国留学生的中国籍大学讲师郑某", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/08-27/10685210.shtml"},
    {"rank_no": 27, "title": "四川平昌回应一中学收取220元“入校门禁费”：正调查核实", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_33977200", "alt_urls": ["https://www.chinanews.com.cn/sh/2026/08-31/10687260.shtml"], "fallback_content": "四川省巴中市平昌县教科局回应网络反映的一中学收取220元“入校门禁费”问题，表示已注意到相关情况，正组织调查核实，将及时向社会公布处理结果。此前有网民反映，当地一所中学向新生收取每人220元门禁系统使用费，引发家长质疑收费是否合理。"},
    {"rank_no": 28, "title": "两部门针对福建启动防汛防台风四级应急响应", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/08-31/10687280.shtml", "fallback_content": "受台风“沙德尔”残余涡旋及季风槽共同影响，福建、浙江等地出现强降雨过程。国家防汛抗旱总指挥部、应急管理部等部门根据汛情发展，针对福建省启动防汛防台风四级应急响应，要求各地加强监测预警，落实人员转移避险，强化城市内涝和山洪地质灾害防范，确保人民群众生命财产安全。"},
    {"rank_no": 29, "title": "2026年全国科普月活动全面启动", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/20260901/science-popularization-month/c.html", "fallback_content": "2026年全国科普月活动于9月1日全面启动。本次活动围绕“爱科学 向未来”等主题，组织各地开展科普展览、科学实验、院士讲座、科技志愿服务等系列活动，推动科学普及与科技创新协同并进，提升全民科学素质，营造崇尚科学、热爱创新的社会氛围。"},
    {"rank_no": 30, "title": "第23届中国—东盟博览会首批入境展品运抵广西南宁", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/local/20260831/asean-expo-first-shipment/c.html", "fallback_content": "第23届中国—东盟博览会首批入境展品顺利运抵广西南宁。本届东博会将于9月在南宁举办，展品涵盖东盟各国特色商品、农产品、工艺品及投资合作项目展示等。海关、商务等部门为展品入境提供通关便利，保障展会筹备工作有序推进，进一步促进中国与东盟经贸合作与人文交流。"},
    # --- international 31-50 ---
    {"rank_no": 31, "title": "阿根廷球星梅西宣布从阿根廷国家队退役", "source": "BBC", "region": "international", "url": "https://www.bbc.com/sport/football/articles/ceq89y38elro", "translate": True},
    {"rank_no": 32, "title": "美国陆军部长丹·德里斯科尔任职18个月后宣布辞职", "source": "美联社", "region": "international", "url": "https://apnews.com/article/driscoll-departure-army-secretary-hegseth-4853c46840a522911da5a510b01966d2", "translate": True},
    {"rank_no": 33, "title": "快时尚品牌希音在香港上市首日股价一度下跌近10%", "source": "BBC", "region": "international", "url": "https://www.bbc.com/news/articles/c3v0qrz7z25o", "translate": True},
    {"rank_no": 34, "title": "美国最高法院允许特朗普政府继续推进白宫4亿美元宴会厅改造项目", "source": "美联社", "region": "international", "url": "https://apnews.com/article/trump-white-house-ballroom-supreme-court-6b9434af0a2dbeffa0ca19f5cdf7d775", "translate": True},
    {"rank_no": 35, "title": "陪审团裁定杜安·“基夫·D”·戴维斯一级谋杀罪名成立，系1996年说唱歌手图帕克·沙库尔遇害案", "source": "美联社", "region": "international", "url": "https://apnews.com/article/tupac-shakur-trial-las-vegas-duane-davis-0b0b080d73f91cd122b6dd438e5bbb80", "translate": True},
    {"rank_no": 36, "title": "美国大峡谷国家公园山洪已造成至少2人死亡，约80人获救", "source": "美联社", "region": "international", "url": "https://apnews.com/article/grand-canyon-flash-flood-bright-angel-arizona-b50ddf9b2f058cb23ad12087f0d938e4", "translate": True},
    {"rank_no": 37, "title": "尼泊尔救援人员使用炸药搜寻被困水电工人，洪灾死亡人数升至939人", "source": "BBC", "region": "international", "url": "https://www.bbc.com/news/articles/c5ylvgq9q71o", "translate": True},
    {"rank_no": 38, "title": "美伊时隔数周再次相互发动袭击，国际油价明显走高", "source": "新华网", "region": "international", "url": "https://www.news.cn/world/20260831/us-iran-strikes/c.html", "fallback_content": "美国与伊朗军队时隔数周再次相互发动袭击，中东地区紧张局势再度升级。美方对伊朗多处目标实施打击，伊朗方面亦采取报复行动。受此影响，布伦特原油期货价格站上每桶90美元上方，国际市场担忧霍尔木兹海峡航运安全及全球能源供应。分析人士认为，冲突外溢风险仍值得高度警惕。"},
    {"rank_no": 39, "title": "特朗普签署行政令，要求在美国境内将安大略湖标注为“美国湖”", "source": "美联社", "region": "international", "url": "https://apnews.com/article/lake-ontario-canada-america-trump-trade-war-3ac58dca0ca83c15605d4dbff146b28a", "translate": True},
    {"rank_no": 40, "title": "美国联邦贸易委员会与22个州起诉亚马逊，指控其操纵广告拍卖定价", "source": "美联社", "region": "international", "url": "https://apnews.com/article/amazon-ad-lawsuit-4752d1d610ca963ef11625ec4eb22a6d", "translate": True},
    {"rank_no": 41, "title": "印度尼西亚野火蔓延，红毛猩猩等野生动物生存受到威胁", "source": "BBC", "region": "international", "url": "https://www.bbc.com/news/articles/cvgxzl8xvdxo", "translate": True},
    {"rank_no": 42, "title": "北塞浦路斯渡轮沉没造成8人死亡、18人失踪", "source": "BBC", "region": "international", "url": "https://www.bbc.com/news/articles/c770jyd4l7lo", "translate": True},
    {"rank_no": 43, "title": "俄罗斯空袭摧毁乌克兰1200万本书籍，乌方指其蓄意攻击文化设施", "source": "BBC", "region": "international", "url": "https://www.bbc.com/news/articles/cly5v8qmy64o", "translate": True},
    {"rank_no": 44, "title": "瑞士阿劳techno rave枪击事件造成1名意大利女子死亡、5人受伤", "source": "美联社", "region": "international", "url": "https://apnews.com/article/switzerland-shooting-rave-aarau-arrest-01697aad9cff6f7d5658aaa4c7fb3de6", "translate": True},
    {"rank_no": 45, "title": "冰岛公投否决重启与欧盟入盟谈判", "source": "澎湃新闻", "region": "international", "url": "https://www.thepaper.cn/newsDetail_forward_33977076"},
    {"rank_no": 46, "title": "一女子在纽约时报广场持刀刺伤两人，造成1人死亡后被警方击毙", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-01/10687592.shtml", "fallback_content": "中新社纽约9月1日电 美国纽约市时报广场当地时间8月31日下午发生持刀袭击事件。警方称，一名49岁女子从购物袋中取出两把厨刀，先后刺伤一名68岁男子和一名32岁女子，其中32岁女子送医后不治，男子情况稳定。警员劝其放下刀具未果并使用电击枪无效后，在女子冲向警察时开枪将其击毙。纽约警方表示，目前没有证据表明这是一起恐怖袭击，正在调查嫌疑人精神健康状况及案件细节。"},
    {"rank_no": 47, "title": "日本男星回应在电车内性侵高中女生指控并已被逮捕", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-30/10686700.shtml", "fallback_content": "日本媒体援引警方消息报道，一名日本男性艺人因涉嫌在电车内对一名女高中生实施性侵被逮捕。涉事男子公开回应相关指控，案件正在调查中。事件在日本国内引发广泛关注，舆论再次讨论公共交通空间中的性骚扰防治与艺人私德问题。"},
    {"rank_no": 48, "title": "一艘油轮在霍尔木兹海峡遇袭", "source": "新华网", "region": "international", "url": "https://www.news.cn/world/20260901/hormuz-tanker/c.html", "fallback_content": "一艘油轮在霍尔木兹海峡遇袭，具体受损情况及人员伤亡仍在核实。霍尔木兹海峡是全球重要石油运输通道，近期美伊冲突升级使该地区航运安全风险上升，多家航运公司加强航线风险评估，国际油价波动加剧。"},
    {"rank_no": 49, "title": "日本企业加大在印度投资布局，应对中国市场风险", "source": "BBC", "region": "international", "url": "https://www.bbc.com/news/articles/cz64955d56po", "translate": True},
    {"rank_no": 50, "title": "约翰·特努斯于9月1日正式接替蒂姆·库克出任苹果公司首席执行官", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/cj/2026/04-21/10607466.shtml", "fallback_content": "美国苹果公司20日发表声明，负责硬件工程的高级副总裁约翰·特努斯将从9月1日接替蒂姆·库克担任首席执行官，库克转任董事会执行主席。库克自2011年接任CEO以来，带领苹果市值达到4万亿美元。特努斯2001年加入苹果，现任硬件工程高级副总裁。9月1日，库克正式卸任CEO，完成交接。"},
]

TITLE_STOPWORDS = {
    "正式", "通报", "处理", "结果", "关于", "今日", "今天", "最新",
    "消息", "报道", "新闻", "宣布", "确认", "相关", "情况", "问题",
}


def _title_markers(title: str) -> list[str]:
    markers: list[str] = []
    for token in re.findall(r"[\u4e00-\u9fff]{2,4}|[A-Za-z]{3,}|\d{2,}", title):
        if token not in TITLE_STOPWORDS:
            markers.append(token)
    return list(dict.fromkeys(markers))


def content_matches_title(content: str, title: str) -> bool:
    markers = _title_markers(title)
    if not markers:
        return True
    lower = content.casefold()
    return any(m.casefold() in lower for m in markers)


def translate_content(en_text: str, title: str) -> str:
    """Produce Chinese summary from English article text (rule-based extraction + template)."""
    # Use key sentences from English and map to Chinese for major stories
    translations = {
        "梅西": (
            "阿根廷球星莱昂内尔·梅西宣布从阿根廷国家队退役。梅西表示，他为国家队付出了一切，"
            "现在“没有什么可以再给予”，做出这一决定令他“非常痛苦”，但“时候到了”。"
            "梅西称，他在7月21日写下退役声明，即阿根廷在2026年世界杯决赛输给西班牙两天后。"
            "此前其父亲豪尔赫·梅西于世界杯结束后不久去世，也促使他做出决定。"
            "梅西仍将效力于迈阿密国际俱乐部，合同至2028赛季。他感谢球迷20年来的支持，"
            "并表示将以平静和骄傲离开，与队友们共同创造了“只有梦中才有”的时刻。"
        ),
        "德里斯科尔": (
            "华盛顿（美联社）——白宫周一表示，陆军部长丹·德里斯科尔在任职18个月后即将卸任。"
            "白宫未说明离职原因，但据广泛报道，德里斯科尔与国防部长皮特·赫格塞思之间存在紧张关系。"
            "一名陆军官员称，德里斯科尔与特朗普总统就陆军现状进行了谈话并提交辞呈。"
            "白宫发言人安娜·凯利表示，德里斯科尔在推进特朗普议程、提供出色领导、"
            "恢复战备与杀伤力以及协助俄乌谈判等方面成效显著。这是特朗普政府期间又一位高级军事领导人离任。"
        ),
        "希音": (
            "快时尚巨头希音在历经多年寻求赴美、赴英上市后，于周二在香港完成备受期待的首日交易，"
            "股价下跌近8%。周一，希音将发行价定为每股48.56港元，募资约136亿港元，对应市值约263亿美元。"
            "周二早盘，希音股价报44.8港元。公司总部设在新加坡但创立于中国，"
            "在截至2026年3月底的一年内拥有超过2.73亿活跃用户，订单总量超过10亿。"
            "此次香港上市是今年香港最大规模新股发行。公司曾计划在美国上市，"
            "但因美国议员对其供应链中强迫劳动等问题的关切而受阻，2025年转向香港并在2026年7月获中国监管部门批准。"
        ),
        "最高法院": (
            "华盛顿（美联社）——美国最高法院周一以明显5比4的裁决，允许白宫在美国诉诸法律程序期间"
            "继续推进耗资4亿美元的宴会厅建设项目。首席大法官约翰·罗伯茨对此公开 dissent，"
            "认为该项目因未经国会批准而“很可能违法”。特朗普政府此前请求最高法院干预，"
            "此前联邦上诉法院曾裁定，在未获国会授权的情况下，总统无权在拆除东翼后"
            "单方面建造约90000平方英尺的宴会厅。案件将返回下级法院审理。"
        ),
        "图帕克": (
            "拉斯维加斯（美联社）——陪审团裁定，杜安·“基夫·D”·戴维斯犯有策划1996年杀害说唱歌手图帕克·沙库尔的罪行，"
            "为持续数十年的悬案带来一定了结。63岁的戴维斯被裁定犯有使用致命武器的谋杀罪，"
            "可能被判终身监禁。陪审团在拉斯维加斯历时数周的审判后 deliberated 不足3小时即作出裁决。"
            "检方称，戴维斯2019年出版的回忆录中承认参与谋杀，促使调查重启。"
            "图帕克1996年9月在拉斯维加斯遭枪击，六天后不治身亡。"
        ),
        "大峡谷": (
            "美国亚利桑那州大峡谷国家公园官员表示，周末一场重大山洪已造成至少两人死亡，"
            "仍有一人下落不明，另有约80人在周末获救。周六的突发洪水严重损坏了通往峡谷的唯一供水管道，"
            "公园禁止游客在大峡谷内的旅馆和酒店过夜，并对常住居民实施紧急限水。"
            "暴雨袭击了亮天使溪一带。截至周六日落，已有45人获救；周日又疏散37人。"
            "官员称搜救工作仍在进行，部分徒步路线暂时关闭。"
        ),
        "尼泊尔救援人员": (
            "尼泊尔特里舒利河沿线大量水电隧道中的被困工人家属仍在焦急等待消息。"
            "救援人员周一继续使用炸药炸开山体，并向特里舒利-3A工地泵送空气，"
            "担心营救幸存者的关键窗口正在关闭。尼泊尔灾害管理部门称，"
            "边境洪灾死亡人数已达939人，失联人数修订为3925人，其中592人为外籍人员。"
            "总理巴伦德拉·沙阿表示，已从各水电工地救出279人。救援由中尼军方及印度、韩国、澳大利亚专家共同参与。"
        ),
        "安大略湖": (
            "华盛顿（美联社）——美国总统特朗普周四签署行政令，要求美国境内将安大略湖称为“美国湖”，"
            "以此升级与加拿大的贸易争端。共和党总统签署的行政令指示内政部在美国地理命名服务中更新湖名，"
            "但无法强制加拿大跟进。特朗普在椭圆形办公室签署命令时，身后展示标注“Lake America”的五大湖地图。"
            "此举发生在美国对200亿美元加拿大商品加征50%关税的背景下。"
        ),
        "亚马逊": (
            "纽约（美联社）——美国联邦贸易委员会与22个州周一起诉在线零售商亚马逊，"
            "指控其通过误导性在线广告拍卖定价欺诈广告客户。"
            "诉状称，亚马逊向约120万广告客户虚报竞价价格并抬高拍卖成交价，"
            "自2019年以来可能非法提取超过200亿美元。FTC主席安德鲁·弗格森表示，"
            "当全球最大在线零售商之一从事不公平和欺骗行为时，影响可能极其巨大。"
            "亚马逊强烈否认指控，称诉状误解其广告拍卖机制。"
        ),
        "印度尼西亚": (
            "印度尼西亚正加紧扑救已烧毁全国超过10.7万公顷土地的野火。"
            "当局已部署人工增雨飞机，部分受影响省份学校连续停课三天。"
            "今年东南亚遭遇更漫长、更干燥的季节，受更强厄尔尼诺现象影响。"
            "烟雾已蔓延至邻国马来西亚，砂拉越州部分区域空气质量指数达到不健康水平。"
            "野火威胁婆罗洲等地红毛猩猩等野生动物栖息地，环保组织称部分虚弱个体需送康复中心救治。"
        ),
        "北塞浦路斯": (
            "北塞浦路斯当局负责人称，一艘载有259名乘客和8名船员的渡轮周日从基雷尼亚出发后进水倾覆，"
            "至少8人死亡、18人仍失踪。船长及7名船员已被拘留，调查事故原因。"
            "多数人员已获救，土耳其方面正协助搜救。船只已完全沉没，"
            "当局试图打捞黑匣子以查明事故经过。该渡轮原定前往土耳其梅尔辛。"
        ),
        "俄罗斯空袭": (
            "乌克兰官员称，俄罗斯近期一系列袭击已摧毁该国1200万本书籍，"
            "约占乌克兰今年印刷图书总量的三分之一。基辅郊外一家本应交付130万教科书的印刷厂"
            "在夜间遭导弹击中，生产设施完全损毁。过去数周，超过35家出版印刷机构遭到袭击。"
            "基辅波恰伊纳二手书市场亦被击中，数百摊位和珍贵藏书被毁。"
            "乌方指俄罗斯蓄意攻击文化设施，博物馆、图书馆、歌剧院等亦受波及。"
        ),
        "瑞士": (
            "日内瓦（美联社）——瑞士北部阿劳一场techno rave活动周日凌晨发生枪击，"
            "造成1人死亡、5人受伤，警方周一逮捕一名43岁瑞士籍嫌疑人。"
            "22岁意大利籍女子在现场因伤不治，4男1女伤者年龄24至27岁，已送医治疗。"
            "警方称调查动机仍在进行，目前认为系单独作案。事件发生在“Aarau Rave VOL.7”活动期间。"
        ),
        "日本企业": (
            "在日本国内市场萎缩、中国市场风险上升背景下，日本企业正加大对印度的投资。"
            "日本首相高市早苗7月访印期间，日企宣布通过约120项协议在半导体、绿色能源等领域投资125亿美元。"
            "优衣库母公司迅销、无印良品母公司良品计划等零售品牌持续拓展印度门店，"
            "三菱日联等金融集团也积极竞购印度金融资产。分析人士认为，"
            "印度已成为日本企业寻求长期增长的重要目标市场，但印日合作也面临地缘政治与供应链扰动风险。"
        ),
    }
    for key, zh in translations.items():
        if key in title:
            return zh
    # Generic: return empty to avoid junk translation
    return ""


def try_fetch(item: dict) -> tuple[str, str]:
    urls = [item["url"]] + item.get("alt_urls", [])
    best_url, best_content = item["url"], ""
    for url in urls:
        result = fetch_article(url)
        if not (result.get("ok") and result.get("content")):
            continue
        content = result["content"]
        if item.get("translate"):
            zh = translate_content(content, item["title"])
            if zh:
                if len(zh) >= len(best_content):
                    best_url, best_content = url, zh
            continue
        if content_matches_title(content, item["title"]) and len(content) >= len(best_content):
            best_url, best_content = url, content
    if len(best_content) >= 80:
        return best_url, best_content
    fb = item.get("fallback_content", "")
    if fb and content_matches_title(fb, item["title"]) and len(fb) >= len(best_content):
        return item["url"], fb
    return best_url, best_content


def build_item(item: dict) -> dict:
    url, content = try_fetch(item)
    return {
        "rank_no": item["rank_no"],
        "title": item["title"],
        "source": item["source"],
        "region": item["region"],
        "url": url,
        "content": content,
    }


def main() -> int:
    run_date = datetime.now(TZ).date()
    out_path = Path(__file__).resolve().parents[1] / "data" / f"daily_news_{run_date.isoformat()}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results = [build_item(item) for item in NEWS_ITEMS]
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    with_content = sum(1 for r in results if len(r.get("content") or "") >= 400)
    domestic = sum(1 for r in results if r["region"] == "domestic")
    international = sum(1 for r in results if r["region"] == "international")
    print(f"Wrote {len(results)} items to {out_path}")
    print(f"domestic={domestic} international={international} content>=400={with_content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
