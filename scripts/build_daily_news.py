#!/usr/bin/env python3
"""Build daily news JSON: fetch domestic articles, attach international translations."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
OUT = Path(__file__).resolve().parents[1] / "data" / "news_2026-09-27.json"


def fetch(url: str) -> str:
    r = subprocess.run(
        ["curl", "-sL", url, "-H", "User-Agent: Mozilla/5.0", "--max-time", "25"],
        capture_output=True,
    )
    return r.stdout.decode("utf-8", errors="replace")


def strip_html(html: str) -> str:
    html = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    text = unescape(html)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_chinanews(html: str) -> str:
    m = re.search(r'<div class="left_zw">([\s\S]*?)</div>', html)
    return strip_html(m.group(1)) if m else ""


def fetch_domestic(url: str) -> str:
    return extract_chinanews(fetch(url))


# rank_no, title, source, region, url — content fetched or provided below
ITEMS: list[dict] = [
    # --- domestic 1-30 ---
    {"rank_no": 1, "title": "习近平结束对美国的国事访问回到北京", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704150.shtml"},
    {"rank_no": 2, "title": "中美达成八点成果共识", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704151.shtml"},
    {"rank_no": 3, "title": "王毅谈习近平主席对美国进行国事访问：开辟大国相处正确之道", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704199.shtml"},
    {"rank_no": 4, "title": "大熊猫“平平”“福双”已启程赴美", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-27/10704316.shtml"},
    {"rank_no": 5, "title": "中国代表团在亚运会突破百金，男足时隔28年再进亚运四强", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-27/10704305.shtml"},
    {"rank_no": 6, "title": "林诗栋/蒯曼击败王楚钦/孙颖莎夺得亚运会乒乓球混双冠军", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-27/10704304.shtml"},
    {"rank_no": 7, "title": "中国队3比0击败泰国队，时隔28年重返亚运男足四强", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704207.shtml"},
    {"rank_no": 8, "title": "名古屋亚运会状况频发，组委会致歉", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704278.shtml"},
    {"rank_no": 9, "title": "外交部：关于人工智能表述问题，中方重视美方立场也尊重美方提法", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704210.shtml"},
    {"rank_no": 10, "title": "在美侨胞：中美关系稳定发展为世界增添确定性", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/hr/2026/09-26/10704020.shtml"},
    {"rank_no": 11, "title": "习近平向全球发展倡议5周年高级别对话会致贺信", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10703977.shtml"},
    {"rank_no": 12, "title": "“祝福祖国”巨型花篮亮相北京天安门广场", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704044.shtml"},
    {"rank_no": 13, "title": "民企推动中国消费市场新活力", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-26/10704148.shtml"},
    {"rank_no": 14, "title": "驻泰国使馆提醒在泰中国公民防范强降雨及洪涝灾害", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-27/10704303.shtml"},
    {"rank_no": 15, "title": "福建罗源县碧里乡发生滑坡泥石流险情，3人暂未联系上", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-27/10704301.shtml"},
    {"rank_no": 16, "title": "4条高铁将同日开通，多地迈入高铁时代", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-27/10704309.shtml"},
    {"rank_no": 17, "title": "第48届世界技能大赛收官，热门赛项亮点频出", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-26/10704259.shtml"},
    {"rank_no": 18, "title": "AI时代，为啥还要拼技能？世赛现场即答案", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-27/10704312.shtml"},
    {"rank_no": 19, "title": "哈萨克斯坦总统：哈中多领域合作不断深化", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-26/10703962.shtml"},
    {"rank_no": 20, "title": "中国人民解放军南部战区位黄岩岛周边海空域组织海空联合演训", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-27/10704317.shtml"},
    {"rank_no": 21, "title": "全球发展倡议5周年，切实助力世界可持续发展", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-26/10704296.shtml"},
    {"rank_no": 22, "title": "各地商圈新场景新业态加快“上新”，特色服务让消费加速升级", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-26/10704275.shtml"},
    {"rank_no": 23, "title": "西藏接连发布暴雪预警，冈仁波齐景区暂停进入", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-26/10704240.shtml"},
    {"rank_no": 24, "title": "“十一”假期前四川、陕西等地部分地区有大到暴雨，注意防范", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-26/10704297.shtml"},
    {"rank_no": 25, "title": "中国女篮亚运会摘铜，宫鲁鸣：未完成夺冠目标有遗憾", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704203.shtml"},
    {"rank_no": 26, "title": "孙颖莎：混双项目国际竞争激烈，各队水平接近", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704271.shtml"},
    {"rank_no": 27, "title": "王楚钦：后续需要重新研究如何提升混双实力", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704262.shtml"},
    {"rank_no": 28, "title": "产业链协同赋能“新广货”出海", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-26/10704176.shtml"},
    {"rank_no": 29, "title": "一本“技能护照”如何实现“跨国旅行”", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/edu/2026/09-27/10704318.shtml"},
    {"rank_no": 30, "title": "“栋曼组合”夺金，国乒包揽亚运混双金银牌", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704213.shtml"},
    # --- international 31-50 ---
    {"rank_no": 31, "title": "特朗普拒绝伊朗七天内重开霍尔木兹海峡的提议", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/cqgmrr9ekr7ko"},
    {"rank_no": 32, "title": "伊朗总统佩泽希齐扬称不再信任与华盛顿的对话", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/26/pezeshkian-says-iran-no-longer-trusts-talks-with-washington"},
    {"rank_no": 33, "title": "教皇利奥十四世在巴黎露天弥撒上称赞年轻人的热情与投入", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/cm4gjjwvvlzro"},
    {"rank_no": 34, "title": "雅典卫城附近公寓楼爆炸致6人死亡，含一名英国公民", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/c6p3kk78l4l1o"},
    {"rank_no": 35, "title": "美国东北部风暴致洪涝停电，纽约和新泽西宣布紧急状态", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/ck1wxxzn5jndo"},
    {"rank_no": 36, "title": "巴基斯坦德拉伊斯梅尔汗自杀式爆炸致至少12人死亡", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/26/blast-in-pakistans-dera-ismail-khan-kills-several-people"},
    {"rank_no": 37, "title": "俄乌互攻致至少10人死亡，双方继续远程打击", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/26/at-least-10-people-killed-in-russian-and-ukrainian-attacks"},
    {"rank_no": 38, "title": "哈马斯批评和平委员会拒绝与近东救济工程处在加沙合作", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/26/hamas-slams-board-of-peace-for-refusal-to-work-with-unrwa-in-gaza"},
    {"rank_no": 39, "title": "古巴外长谴责美国对古巴的“集体惩罚”", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/26/cuba-condemns-us-collective-punishment-as-trump-predicts-deal"},
    {"rank_no": 40, "title": "巴西总统卢拉在大选前宣布禁止网络赌博", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/c914ddj21rzlo"},
    {"rank_no": 41, "title": "曼谷道路被淹，泰国宣布洪水灾难紧急状态", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/ck1wxx8n2x3zo"},
    {"rank_no": 42, "title": "独立报告指犹他大学校园查理·柯克遇害事件存在安全疏漏", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/cq4g55r76d9lo"},
    {"rank_no": 43, "title": "爱尔兰队将为对以色列比赛佩戴黑袖标", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/sport/football/articles/ckddvv5dn4eyo"},
    {"rank_no": 44, "title": "白宫禁止CNN记者搭乘空军一号随特朗普出行", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/cxq633770y16o"},
    {"rank_no": 45, "title": "南非约翰内斯堡东部再发现一具女性遗体，警方调查连环杀人案", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/c3vgyyj8q807o"},
    {"rank_no": 46, "title": "埃塞俄比亚提格雷地区战事升级，和平协议面临破裂风险", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/26/is-ethiopia-on-the-verge-of-another-civil-war-as-fighting-erupts-in-tigray"},
    {"rank_no": 47, "title": "中美同意设立人工智能安全事件沟通渠道", "source": "Deutsche Welle", "region": "international",
     "url": "https://www.dw.com/en/china-us-agree-to-set-up-channel-for-ai-safety-incidents/a-79443351"},
    {"rank_no": 48, "title": "希腊当局调查雅典普拉卡区公寓楼爆炸原因", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/world/2026/sep/26/greek-authorities-seek-answers-after-six-killed-in-athens-apartment-block-explosion"},
    {"rank_no": 49, "title": "特朗普拒绝伊朗重开霍尔木兹海峡方案", "source": "Deutsche Welle", "region": "international",
     "url": "https://www.dw.com/en/trump-rejects-iran-proposal-to-reopen-strait-of-hormuz/a-79444893"},
    {"rank_no": 50, "title": "巴基斯坦警方检查站遭自杀式袭击致至少11人死亡", "source": "Deutsche Welle", "region": "international",
     "url": "https://www.dw.com/en/pakistan-suicide-attack-at-police-stop-kills-at-least-11/a-79443050"},
]

# Pre-translated Chinese content for international items (verified against source articles)
INTL_CONTENT: dict[str, str] = {
    "https://www.bbc.co.uk/news/articles/cqgmrr9ekr7ko": (
        "美国总统唐纳德·特朗普拒绝了伊朗在一周内重开霍尔木兹海峡、恢复商业航运的提议。"
        "他在白宫对记者表示，德黑兰希望立即开放海峡，因为他们在冲突中损失惨重。"
        "伊朗外长阿巴斯·阿拉格希在电报上回应称，已注意到特朗普的言论，但将等待调解方的正式答复。"
        "周五，阿拉格希在纽约联合国总部表示，若满足必要条件，可在七天内重开这条承载全球约五分之一油气贸易的水道。"
        "该水道自2月战争爆发以来基本处于关闭状态。特朗普周六说：“我拒绝他们的协议”，"
        "并声称美国已“完全控制”海峡，大量石油正通过该水道运输。"
        "他表示愿意达成协议，但伊朗提出的方案“不可接受”。"
        "双方今年6月曾签署一份谅解备忘录，内容包括停火、部分重开海峡、解除美方海上封锁等，但此后双方恢复打击，协议破裂。"
        "伊朗已对未经授权试图穿越海峡的船只发动攻击，美国则打击伊朗在海峡内的目标并维持对伊朗港口的封锁。"
    ),
    "https://www.aljazeera.com/news/2026/9/26/pezeshkian-says-iran-no-longer-trusts-talks-with-washington": (
        "伊朗总统马苏德·佩泽希齐扬在接受半岛电视台采访时表示，在前几轮谈判后遭遇袭击和制裁，"
        "伊朗已不再信任与美国的谈判。他说：“我们对美方没有信任，不知道可以在什么基础上与之达成谅解。”"
        "佩泽希齐扬本周与外长阿拉格希赴纽约出席联合国大会，提出可在七天内结束美以对伊战争并重新开放霍尔木兹海峡的方案。"
        "阿拉格希周五表示，初步步骤需四至五天，第六天重开海峡，第七天启动最终谈判。"
        "方案要求美方解除对伊朗港口的封锁、豁免石油制裁、释放约120亿美元冻结资产并遵守地区停火；"
        "伊朗则重开霍尔木兹海峡。佩泽希齐扬称卡塔尔和巴基斯坦正向华盛顿转达伊朗信息。"
        "他还否认伊朗主动封锁海峡，称美方先切断航线，关闭海峡是“路线被切断后的自然反应”。"
        "他表示地区安全应通过本地区国家合作实现，“我们不需要地区警察”。"
    ),
    "https://www.bbc.co.uk/news/articles/cm4gjjwvvlzro": (
        "教皇利奥十四世在巴黎露天弥撒上称赞年轻人为天主教会带来的“热情、活力与投入”。"
        "梵蒂冈估计约70万人聚集在协和广场参加弥撒，这是教皇访法第二天的活动。"
        "教皇乘坐敞篷教宗座驾沿香榭丽舍大街向人群致意。弥撒期间，他呼吁信徒不要将信仰藏于心中，"
        "而应“让它溢出，使所遇之人得到滋润”。他将年轻人称为“今日教会”，称赞他们给基督教社区带来喜悦。"
        "周五，教皇在爱丽舍宫受到法国总统马克龙欢迎，并在法兰西体育场与约8万名年轻人会面。"
        "周六晚，教皇飞往西南部小镇卢尔德，将在那里举行另一场预计15万人参加的弥撒。"
        "访法首日，教皇在爱丽舍宫警告人工智能风险，称不应在“机器天堂”中失去人性。"
    ),
    "https://www.bbc.co.uk/news/articles/c6p3kk78l4l1o": (
        "希腊首都雅典历史中心普拉卡区一栋含短租公寓的建筑发生爆炸并坍塌，造成6人死亡，其中包括一名英国公民。"
        "爆炸发生于周五清晨，疑似由燃气泄漏引发。死者还包括四名美国游客和一对据报居住在上层的希腊老年夫妇。"
        "周六下午前，六具遗体均已找到。雅典市长哈里斯·杜卡斯称这是“难以置信的灾难”。"
        "警方称，四名美国游客原定周五从雅典机场飞往美国，但未能按时出现，由此确认他们失踪。"
        "三层建筑因爆炸力完全倒塌，周边建筑受损，碎片散落道路。"
        "救援人员使用挖掘机和热成像设备搜寻幸存者。英国外交部表示正与当地政府保持联系。"
    ),
    "https://www.bbc.co.uk/news/articles/ck1wxxzn5jndo": (
        "一场被称为“东北风暴”的强风暴给美国东北部带来沿海洪涝、停电和交通混乱，纽约和新泽西已宣布紧急状态。"
        "美国国家气象局称，包括纽约市和波士顿在内的地区面临危险沿海洪涝、强风和强降雨。"
        "弗吉尼亚至缅因数千万人处于风暴路径上。埃德·希兰原定在波士顿举行的演唱会因天气取消。"
        "据停电追踪网站PowerOutage，超过10万户家庭断电，几乎全部位于东北部。"
        "联邦航空管理局建议乘客向航空公司确认航班状态，FlightAware显示逾2400架次航班延误、1199架次取消。"
        "周六满月将加剧沿海洪涝，新泽西Surf City和Manasquan等社区街道和房屋被淹。"
        "纽约市长佐赫兰·曼达尼提醒居民不要驾车或步行穿越积水。波士顿红袜队将一场主场比赛改至周日举行。"
    ),
    "https://www.aljazeera.com/news/2026/9/26/blast-in-pakistans-dera-ismail-khan-kills-several-people": (
        "巴基斯坦西北部德拉伊斯梅尔汗地区一处路边警察检查站发生自杀式爆炸，警方称至少12人死亡、30人受伤。"
        "袭击发生于开伯尔-普什图省，目击者称爆炸后还听到枪声。警方称多数死伤者为安全人员和路人，"
        "遇难者包括警察、海关人员和林业部门人员。救援1122表示，爆炸发生在德拉兹因达地区阿曼梅拉附近。"
        "半岛电视台记者称，袭击者驾驶载有炸药的车辆冲撞检查站。尚无组织立即宣称负责，但怀疑指向巴基斯坦塔利班（TTP）。"
        "TTP与2021年重返权力的阿富汗塔利班关系密切但组织独立。该地区近期袭击频发，"
        "巴基斯坦指责喀布尔允许TTP从阿富汗境内活动。两天前，巴阿边境交火致至少13名阿富汗塔利班武装人员死亡。"
    ),
    "https://www.aljazeera.com/news/2026/9/26/at-least-10-people-killed-in-russian-and-ukrainian-attacks": (
        "俄罗斯与乌克兰互攻造成至少10人死亡。俄方袭击在乌克兰扎波罗热造成两名妇女死于自家房屋废墟下，"
        "苏梅市另有两人遇难。乌总统泽连斯基在社交媒体上称，俄方每天都在升级打击。"
        "乌克兰继续以远程无人机袭击俄罗斯炼油厂和工业设施。俄罗斯克拉斯诺达尔州州长称，"
        "乌方无人机袭击造成3人死亡、2人受伤，并引发两处工业设施火灾，其中一处为炼油厂。"
        "俄方称在乌克兰黑海港口敖德萨附近打击一艘运载军事物资的货船，并袭击一处物流枢纽。"
        "周五，俄方对基辅的袭击造成7人死亡、58人受伤，迫使乌克兰最大钢铁企业停产。"
        "泽连斯基周五表示，华盛顿提议在阿联酋举行俄乌美三方官员会晤，正等待美方确定日期。"
        "俄外长拉夫罗夫周六在联大指责欧洲阻挠美方感兴趣的和平谈判，并称俄方将实现其在乌克兰的军事目标。"
    ),
    "https://www.aljazeera.com/news/2026/9/26/hamas-slams-board-of-peace-for-refusal-to-work-with-unrwa-in-gaza": (
        "巴勒斯坦伊斯兰抵抗运动（哈马斯）谴责“和平委员会”拒绝与联合国近东巴勒斯坦难民救济和工程处（近东救济工程处）合作，"
        "并称该机构在加沙将不起作用。哈马斯发言人哈齐姆·卡西姆称，这是“与以色列立场完全一致”，"
        "旨在终结近东救济工程处运作、阻止其向巴勒斯坦人提供援助并消除回归权。"
        "和平委员会周五在社交媒体上表示，加沙的近东救济工程处参与情况不变，但只会与“值得信赖的伙伴”合作，"
        "并称近东救济工程处不符合相关标准。近东救济工程处1949年成立，长期为巴勒斯坦难民提供援助和教育服务。"
        "周六，以色列在加沙和约旦河西岸的袭击仍在继续。加沙卫生部称过去48小时以方袭击造成7名巴勒斯坦人死亡。"
    ),
    "https://www.aljazeera.com/news/2026/9/26/cuba-condemns-us-collective-punishment-as-trump-predicts-deal": (
        "古巴外长布鲁诺·罗德里格斯在联合国大会发言，谴责美国对古巴的石油封锁是旨在引发人道危机的“集体惩罚”。"
        "特朗普周六在白宫对记者表示，相信美古将达成协议，且他认为不需要动用军事力量。"
        "罗德里格斯表示，古巴始终愿意在主权平等、不设前提条件下与美方对话。"
        "本周特朗普在联大称古巴是“绝对失败国家”，称“自由将降临”该岛，古巴代表团在其发言时离场。"
        "美国对古巴的经济禁运已持续60余年，特朗普政府今年还实施石油封锁，导致古巴燃料短缺和持续停电。"
        "巴西、墨西哥和巴基斯坦等国呼吁结束禁运和新的石油封锁，反对对古巴的单边经济限制。"
    ),
    "https://www.bbc.co.uk/news/articles/c914ddj21rzlo": (
        "巴西总统路易斯·伊纳西奥·卢拉·达席尔瓦在大选前数天宣布禁止网络赌博。"
        "这位左翼领导人周五签署临时法令，禁止所有体育博彩和在线赌场。巴西网络赌博业2018年合法化后迅速扩张，"
        "被指导致大量家庭因成瘾而收入受损。卢拉称该行业是“癌症”，必须“切除肿瘤，否则它会杀死我们”。"
        "其竞争对手弗拉维奥·博索纳罗指责此举出于政治动机。新措施要求博彩账户在10月5日前提现，禁止新存款，"
        "须在120天内获国会批准方可继续生效。卢拉还在联大指责该行业“将成瘾变为利润”。"
        "一项Atlas和彭博调查显示，约59.9%的巴西成年人支持禁止网络博彩。"
    ),
    "https://www.bbc.co.uk/news/articles/ck1wxx8n2x3zo": (
        "泰国首都曼谷在连续48小时强降雨后道路被淹，全市宣布洪水灾难紧急状态。"
        "当局敦促民众留在家中，靠近运河的居民被建议将物品移至高处。"
        "近期极端天气使曼谷排水系统不堪重负，交通严重混乱。降雨预计将持续至周日，"
        "人们担心更多运河可能决堤。67岁的索姆基德·普克-ngam告诉法新社，水位已至腰部，店铺已关闭两天。"
        "她说情况似乎比2011年曼谷遭遇的全国性洪灾更严重，当时泰国数百人遇难。"
        "曼谷全部50个区均被宣布为紧急区域，市长查德chart·西蒂蓬表示东部受灾最重，"
        "正全力抽水，但运河已满，靠近运河的区域风险最高。"
    ),
    "https://www.bbc.co.uk/news/articles/cq4g55r76d9lo": (
        "独立审查报告指出，去年保守派活动人士查理·柯克在犹他谷大学遇害的活动存在多项安全疏漏。"
        "报告称，校方未进行书面安全评估，也未制定活动行动计划，将关键决策交给柯克所属组织“美国转折点”。"
        "柯克助手坚持在户外场地演讲，覆盖了校方对周边高楼安全隐患的担忧。"
        "2025年9月10日，柯克在奥勒姆校区庭院向数千人演讲时，遭附近屋顶枪手击中颈部身亡。"
        "报告指校方警察与柯克私人安保团队协调不足，活动前双方负责人原定会面但未举行。"
        "审查结论认为无校方人员恶意漠视安全，但提出多项改进建议。柯克家人此前已发出不当死亡诉讼通知。"
    ),
    "https://www.bbc.co.uk/sport/football/articles/ckddvv5dn4eyo": (
        "爱尔兰足协确认，爱尔兰队将于周日在匈牙利对阵以色列的欧国联比赛中佩戴黑袖标，"
        "“以纪念加沙冲突中失去的所有生命”，并决定照常参赛。足协首席执行官大卫·库雷尔表示，"
        "一名球员（门将加文·巴祖努）已退出比赛以示抗议，但队内投票以“显著多数”支持参赛。"
        "球员还将放弃部分媒体义务，并将两场对以色列比赛及周四对奥地利比赛的出场费捐作慈善。"
        "比赛自抽签以来争议不断，“停止比赛”运动呼吁爱尔兰队抵制。"
        "巴祖努在社交媒体表示，基于个人信念，他认为参与对以色列的比赛是错误的，"
        "强调其立场并非针对以色列人民或犹太社区，而是反对该地区对无辜者的杀戮。"
        "以色列足协称足球与政治应分开，赞赏爱尔兰队最终决定参赛。"
    ),
    "https://www.bbc.co.uk/news/articles/cxq633770y16o": (
        "美国有线电视新闻网（CNN）被禁止搭乘空军一号随特朗普总统前往田纳西州。"
        "这是白宫与媒体争端中的最新举措。CNN原定于周六随特朗普赴田纳西观看大学橄榄球赛，"
        "但周五晚白宫发布的媒体行程未列入该台。上周，特朗普以三家媒体撰写“虚构或谎言”为由，"
        "禁止CNN、Politico和MS NOW记者进入白宫，相关媒体表示将采取法律行动。"
        "联邦法官此后裁定，禁止新闻机构进入白宫可能违宪，要求政府至少暂时恢复其进入权。"
        "然而周四为中国领导人习近平举行的国宴上，部分CNN和MS NOW记者仍被拒绝入场报道。"
        "特朗普周六在社交媒体上再次批评CNN等“假新闻”媒体。"
    ),
    "https://www.bbc.co.uk/news/articles/c3vgyyj8q807o": (
        "南非警方在约翰内斯堡以东的埃库鲁莱尼地区又发现一具女性遗体，使近月在该地区遇害女性总数升至10人。"
        "周六上午发现的遗体由其前一晚在酒吧同行的朋友辨认。当地警察局长表示，不能排除连环杀手的可能性，"
        "指出10起死亡及索韦托另一起案件存在相似作案手法。最新遗体在滕比萨一处墓地被发现。"
        "自今年7月以来，已有10具女性遗体在类似情况下被发现，多数在肯普顿帕克，几乎均遭受极端暴力。"
        "南非是全球性别暴力发生率最高的国家之一。今年4月至6月，南非共发生5427起谋杀案。"
        "人权委员会上周称，同期569名女性被杀，1052名女性遭遇谋杀未遂。本周已有3名男子因其中一起案件出庭。"
    ),
    "https://www.aljazeera.com/news/2026/9/26/is-ethiopia-on-the-verge-of-another-civil-war-as-fighting-erupts-in-tigray": (
        "埃塞俄比亚联邦军队与北部提格雷地区武装之间的战斗加剧，引发人们对2022年结束两年战争的和平协议可能破裂的担忧。"
        "本月，来自埃塞俄比亚各地的七个武装团体组成新联盟，寻求推翻阿比·艾哈迈德总理的政府。"
        "提格雷人民解放阵线（TPLF）与阿比政府关系恶化，2020年11月爆发战争，造成数十万人死亡、数百万人流离失所。"
        "2022年11月在南非比勒陀利亚签署的和平协议结束了全面战争，但西部提格雷领土归属等争议未解决。"
        "本周战斗在提格雷南部加剧，并蔓延至邻近的阿法尔和阿姆哈拉地区。双方互相指责对方挑起冲突。"
        "提格雷武装已控制默克莱、阿克苏姆和希雷机场，民用航班中断。非盟呼吁立即停火并恢复谈判。"
        "分析人士警告存在地区冲突升级风险，厄立特里亚与埃塞俄比亚关系也因红海港口问题恶化。"
    ),
    "https://www.dw.com/en/china-us-agree-to-set-up-channel-for-ai-safety-incidents/a-79443351": (
        "中美首脑会晤后，双方承诺设立人工智能安全事件“沟通渠道”，并加强两军协调。"
        "中方周六表示，双方同意对约300亿美元“非敏感”商品互降关税，适用于农产品和节日装饰品等出口。"
        "中国外交部称，人工智能技术持续发展，各方可加强交流、深入讨论并寻求共识，新一轮以AI为重点的对话定于11月举行。"
        "双方还将加快军事危机沟通机制建设。美国此前宣布延长去年10月釜山达成的贸易休战协议至明年1月。"
        "白宫称，双方讨论了美方对稀土供应的担忧，中国同意在2027和2028年至少进口1000万吨美国煤炭。"
        "中国外交部还表示，双方同意伊朗不应拥有核武器，任何国家都不应对国际水道征收过境费，"
        "此表述涉及霍尔木兹海峡。特朗普和习近平预计年底前还将再会晤两次。"
    ),
    "https://www.theguardian.com/world/2026/sep/26/greek-authorities-seek-answers-after-six-killed-in-athens-apartment-block-explosion": (
        "希腊当局正调查雅典古城中心一栋两层公寓楼为何在“数秒之内”坍塌并造成6人死亡。"
        "紧急救援人员在爆炸发生逾24小时后的周六找到遇难者，其中包括四名美国游客。"
        "消防部门称发现三女三男的遗体。卫报获悉，居住在上层的一套公寓内一对77岁和78岁的英国男子及其希腊妻子也在遇难者之列。"
        "遗体已送往停尸房进行尸检。救援曾使用热成像和地震检波器搜寻幸存者。"
        "四名美国游客住在一楼短租公寓，原定周五飞回美国。当局怀疑燃气泄漏引发爆炸，但官方表示有多种可能原因。"
        "普拉卡区毗邻公元前5世纪建成的卫城，每日吸引大量游客。爆炸还造成至少3人受伤，碎片击碎附近建筑窗户。"
        "希腊政府正收紧对普拉卡短租的监管，爆炸也引发对民宿安全监管的争论。"
    ),
    "https://www.dw.com/en/trump-rejects-iran-proposal-to-reopen-strait-of-hormuz/a-79444893": (
        "美国总统特朗普周六表示，已拒绝伊朗重开霍尔木兹海峡并结束敌对状态的提议。"
        "他在白宫对记者说：“我拒绝他们的提议……我拒绝了他们的协议。”"
        "伊朗在联合国大会期间提出可在七天内重开这条战略水道的方案，并称已通过卡塔尔调解人转交华盛顿。"
        "特朗普称：“他们想立即开放霍尔木兹海峡，因为他们输得很惨。”他声称美方“大获全胜”，"
        "并已“完全控制”海峡。华尔街日报报道，特朗普对德黑兰能否满足其要求持怀疑态度，"
        "并告诉幕僚可能在11月美国中期选举后恢复轰炸。数小时前，特朗普还在社交媒体上发布图片，"
        "将霍尔木兹海峡称为“特朗普海峡”。伊朗总统佩泽希齐扬称该方案是与最高领袖协调制定的。"
    ),
    "https://www.dw.com/en/pakistan-suicide-attack-at-police-stop-kills-at-least-11/a-79443050": (
        "巴基斯坦西北部周六发生自杀式爆炸，当局称至少11人死亡。爆炸发生在德拉伊斯梅尔汗市一处路边警察检查站，"
        "该市为巴基斯坦第十大城市，位于与阿富汗接壤的开伯尔-普什图省，长期遭受伊斯兰武装暴力袭击。"
        "警方称约30人受伤，多数为安全人员和路人，部分伤者情况危急。救援1122已将伤者送医。"
        "巴基斯坦塔利班（TTP）宣称对袭击负责。巴基斯坦近年袭击激增，多由TTP和俾路支解放军发动。"
        "TTP与阿富汗塔利班结盟。巴基斯坦多次指责喀布尔允许TTP从阿富汗境内活动，并实施跨境空袭。"
        "此次袭击发生前两天，巴阿边境交火造成至少13名阿富汗塔利班武装人员死亡。中国、土耳其、卡塔尔和沙特正调解两国关系。"
    ),
}


def main() -> int:
    result = []
    for item in ITEMS:
        row = {k: item[k] for k in ("rank_no", "title", "source", "region", "url")}
        if item["region"] == "domestic":
            content = fetch_domestic(item["url"])
        else:
            content = INTL_CONTENT.get(item["url"], "")
        if len(content) > 20000:
            content = content[:20000]
        row["content"] = content
        result.append(row)
        print(f"  [{row['rank_no']}] {row['region']:12s} content={len(content):5d}  {row['title'][:40]}", file=sys.stderr)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    domestic = sum(1 for r in result if r["region"] == "domestic")
    international = sum(1 for r in result if r["region"] == "international")
    print(f"Wrote {len(result)} items ({domestic} domestic / {international} international) to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
