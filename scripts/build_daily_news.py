#!/usr/bin/env python3
"""Build daily news JSON for 2026-09-28 cron run."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "news_2026-09-28.json"


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


ITEMS: list[dict] = [
    {"rank_no": 1, "title": "中美达成八点成果共识", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704151.shtml"},
    {"rank_no": 2, "title": "王毅谈习近平主席对美国进行国事访问：开辟大国相处正确之道", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704199.shtml"},
    {"rank_no": 3, "title": "习近平结束对美国的国事访问回到北京", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704150.shtml"},
    {"rank_no": 4, "title": "习近平向全球发展倡议5周年高级别对话会致贺信", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10703977.shtml"},
    {"rank_no": 5, "title": "大熊猫“平平”“福双”已启程赴美", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-27/10704316.shtml"},
    {"rank_no": 6, "title": "中国代表团在亚运会突破百金，男足时隔28年再进亚运四强", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-27/10704305.shtml"},
    {"rank_no": 7, "title": "林诗栋/蒯曼击败王楚钦/孙颖莎夺得亚运会乒乓球混双冠军", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-27/10704304.shtml"},
    {"rank_no": 8, "title": "中国队3比0击败泰国队，时隔28年重返亚运男足四强", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704207.shtml"},
    {"rank_no": 9, "title": "名古屋亚运会状况频发，组委会致歉", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704278.shtml"},
    {"rank_no": 10, "title": "王曼昱战胜孙颖莎夺得爱知·名古屋亚运会女单冠军", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-27/10704594.shtml"},
    {"rank_no": 11, "title": "黄友政/林诗栋夺得爱知·名古屋亚运会乒乓球男双冠军", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-27/10704533.shtml"},
    {"rank_no": 12, "title": "全国铁路迎来中秋假期返程客流高峰，9月27日预计发送旅客1686万人次", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-27/10704445.shtml"},
    {"rank_no": 13, "title": "中国蝉联世界技能大赛金牌榜榜首，创历史最好成绩", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-27/10704621.shtml"},
    {"rank_no": 14, "title": "4条高铁将同日开通，多地迈入高铁时代", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-27/10704309.shtml"},
    {"rank_no": 15, "title": "福州市罗源县发生一起滑坡-泥石流险情，致3人失联", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-27/10704353.shtml"},
    {"rank_no": 16, "title": "南部战区位黄岩岛周边海空域组织海空联合演训", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-27/10704317.shtml"},
    {"rank_no": 17, "title": "华西至黄淮江淮多降水，中东部地区将有大风降温过程", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-27/10704320.shtml"},
    {"rank_no": 18, "title": "国务院安委办、应急管理部调度抽查5省市中秋假期安全防范暗访检查工作", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-27/10704374.shtml"},
    {"rank_no": 19, "title": "从共享到共筑：数贸会上的开放之约", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-27/10704473.shtml"},
    {"rank_no": 20, "title": "香江观澜：政策落地提速，香港离岸人民币生态持续完善", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-27/10704468.shtml"},
    {"rank_no": 21, "title": "外交部：关于人工智能表述问题，中方重视美方立场也尊重美方提法", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10704210.shtml"},
    {"rank_no": 22, "title": "第48届世界技能大赛收官，热门赛项亮点频出", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-26/10704259.shtml"},
    {"rank_no": 23, "title": "AI时代，为啥还要拼技能？世赛现场即答案", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-27/10704312.shtml"},
    {"rank_no": 24, "title": "产业链协同赋能“新广货”出海", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-26/10704176.shtml"},
    {"rank_no": 25, "title": "一本“技能护照”如何实现“跨国旅行”", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/edu/2026/09-27/10704318.shtml"},
    {"rank_no": 26, "title": "孙颖莎：混双项目国际竞争激烈，各队水平接近", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704271.shtml"},
    {"rank_no": 27, "title": "王楚钦：后续需要重新研究如何提升混双实力", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10704262.shtml"},
    {"rank_no": 28, "title": "驻泰国使馆提醒在泰中国公民防范强降雨及洪涝灾害", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-27/10704303.shtml"},
    {"rank_no": 29, "title": "中国驻菲使馆发言人就菲防长涉华消极言论表明立场", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-27/10704577.shtml"},
    {"rank_no": 30, "title": "全球发展倡议5周年，切实助力世界可持续发展", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-26/10704296.shtml"},
    {"rank_no": 31, "title": "英国反恐警方在美军基地附近逮捕5人，疏散数十户居民", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/cqrm99mm9l84o"},
    {"rank_no": 32, "title": "美国东北部“东北风暴”造成洪涝停电，纽约和新泽西宣布紧急状态", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/ck1wxxzn5jndo"},
    {"rank_no": 33, "title": "南非两起大规模枪击事件致27人死亡", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/ck5ywnp075d1o"},
    {"rank_no": 34, "title": "曼谷道路被淹，泰国宣布洪水灾难紧急状态", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/ck1wxx8n2x3zo"},
    {"rank_no": 35, "title": "瑞士选民否决写入宪法的更严格中立条款", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/cm750plvwy9vo"},
    {"rank_no": 36, "title": "也门塔伊兹前线战事升级，胡塞武装与政府军在山区交火", "source": "BBC", "region": "international",
     "url": "https://www.bbc.co.uk/news/articles/cw98005ndz7no"},
    {"rank_no": 37, "title": "塞尔维亚总统武契奇辞职，将竞选总理参加提前大选", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/serbian-president-aleksandar-vucic-resigns-amid-prolonged-protests"},
    {"rank_no": 38, "title": "强风暴袭击美国东北部，造成洪涝和大范围停电", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/powerful-storm-floods-us-northeast-causes-power-outages"},
    {"rank_no": 39, "title": "教皇利奥十四世在法国会见性侵幸存者，承诺采取进一步行动", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/pope-pledges-action-on-clergy-child-abuse-in-meeting-with-french-survivors"},
    {"rank_no": 40, "title": "韩国就乌克兰披露朝鲜战俘转移事宜向基辅表达强烈遗憾", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/south-korea-ukraine-relations-sour-over-north-korean-pow-transfer"},
    {"rank_no": 41, "title": "刚果（金）基伍湖沉船事故致至少12人死亡，数十人失踪", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/at-least-12-dead-and-dozens-missing-after-a-vessel-capsizes-in-drc"},
    {"rank_no": 42, "title": "以色列撤销荷兰驻拉姆安拉外交官身份，回应定居点制裁", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/israel-revokes-dutch-diplomats-status-over-sanctions-on-settlements"},
    {"rank_no": 43, "title": "美国底特律脱衣舞俱乐部枪击致3死4伤", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/three-killed-four-injured-in-shooting-at-detroit-michigan-strip-club"},
    {"rank_no": 44, "title": "古巴副外长称美国对古巴动武将构成“骇人听闻的国际罪行”", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/27/atrocious-crime-cuban-official-decries-possibility-of-us-military-action"},
    {"rank_no": 45, "title": "飓风“诺洛”仍威胁夏威夷，墨西哥下加利福尼亚半岛备战“波罗”", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/us-news/2026/sep/27/hurricane-nolo-hawaii-hurricane-polo-mexico"},
    {"rank_no": 46, "title": "村民报警与999呼叫引发英国空军基地附近恐袭逮捕", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/uk-news/2026/sep/27/villagers-raf-fairford-evacuation"},
    {"rank_no": 47, "title": "印度外长：远离冲突的国家也在为并非自身发动的战争付出代价", "source": "联合国新闻", "region": "international",
     "url": "https://news.un.org/en/story/2026/09/1168460"},
    {"rank_no": 48, "title": "联大辩论第五天：人工智能与移民成焦点议题", "source": "联合国新闻", "region": "international",
     "url": "https://news.un.org/en/story/2026/09/1168462"},
    {"rank_no": 49, "title": "加拿大外长：全球秩序面临“断裂”，呼吁加强多边合作", "source": "联合国新闻", "region": "international",
     "url": "https://news.un.org/en/story/2026/09/1168461"},
    {"rank_no": 50, "title": "南非约翰内斯堡和开普敦附近两起大规模枪击致至少27人死亡", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/world/2026/sep/27/mass-shootings-south-africa-johannesburg-cape-town"},
]

INTL_CONTENT: dict[str, str] = {
    "https://www.bbc.co.uk/news/articles/cqrm99mm9l84o": (
        "英国警方称，5名男子因涉嫌准备实施恐怖活动和爆炸物相关犯罪被捕。此前有人报告三辆“可疑车辆”正驶向"
        "格洛斯特郡费尔福德皇家空军基地。周日凌晨约00:45，警方宣布重大事件，基地附近数十户居民被疏散。"
        "该基地长期供美国空军使用，近期也被用作对伊朗实施防御打击的前进基地。英国陆军爆炸物处理小组正在检查"
        "基地附近车辆，反恐警察主导调查。附近韦尔福德村被疏散居民被告知当晚无法返家，但官员称事态已受控。"
        "现场设置了400米警戒线，并部署危险区域响应小组。美国总统特朗普称，被捕者“想制造重大破坏”，"
        "并表示美方“长期掌握其动向并已将其抓获”。英国国防大臣韦斯·斯特里廷表示已与美国防长皮特·赫格塞思沟通。"
        "美国国防部同时将萨福克郡莱肯希思基地威胁等级提升至第二高类别。警方称5人仍被拘留，调查处于早期阶段。"
    ),
    "https://www.bbc.co.uk/news/articles/ck1wxxzn5jndo": (
        "一场被称为“东北风暴”的强风暴给美国东北部带来沿海洪涝、停电和交通混乱，纽约和新泽西已宣布紧急状态。"
        "美国国家气象局称，包括纽约市和波士顿在内的地区面临危险沿海洪涝、强风和强降雨。弗吉尼亚至缅因数千万人"
        "处于风暴路径上。布鲁克林一名56岁纽约市住房局员工被倒树砸中身亡。据停电追踪网站PowerOutage，"
        "超过16万户家庭断电，几乎全部位于东北部。联邦航空管理局建议乘客向航空公司确认航班状态，"
        "FlightAware显示逾2400架次航班延误、1199架次取消。周六满月将加剧沿海洪涝，新泽西Surf City和"
        "Manasquan等社区街道和房屋被淹。纽约市长佐赫兰·曼达尼提醒居民不要驾车或步行穿越积水。"
        "波士顿红袜队将一场主场比赛改至周日举行，中央公园全球公民节等多场大型活动取消。"
    ),
    "https://www.bbc.co.uk/news/articles/ck5ywnp075d1o": (
        "南非两起大规模枪击事件共造成27人死亡。周六晚，8名枪手在约翰内斯堡附近一家酒吧内外开枪，"
        "造成17人死亡、15人受伤，随后焚毁两辆车辆逃离。警方称死者包括13男4女，受害者多数为南非公民，"
        "也有来自埃塞俄比亚和莱索托的人员。豪登省警察局长汤米·姆托姆贝尼表示，作案动机可能是抢劫，"
        "但也不排除非法采矿团伙之间的地盘争夺。周日凌晨，开普敦附近一家娱乐烧烤场所再发生枪击，"
        "10人死亡、11人受伤，5人在现场死亡，5人在送医后死亡。周日早上两起案件均未宣布逮捕。"
        "南非是全球谋杀率最高的国家之一，近期连环大规模枪击引发社会震动。总统西里尔·拉马福萨称，"
        "必须“动用一切手段”打击犯罪。"
    ),
    "https://www.bbc.co.uk/news/articles/ck1wxx8n2x3zo": (
        "泰国首都曼谷自周四以来降雨量超过300毫米，道路被淹，全市宣布洪水灾难紧急状态。"
        "周日，曼谷大都会管理局表示降雨已减弱，但运河水位仍然很高，市长警告洪灾尚未结束。"
        "当局敦促民众留在家中，靠近运河的居民被建议将物品移至高处。近期极端天气使曼谷排水系统不堪重负，"
        "交通严重混乱。67岁的索姆基德·普克-ngam告诉法新社，水位已至腰部，店铺已关闭两天，"
        "情况似乎比2011年曼谷遭遇的全国性洪灾更严重。曼谷全部50个区均被宣布为紧急区域。"
        "市长查德chart·西蒂蓬表示东部受灾最重，正全力抽水，但运河已满，靠近运河的区域风险最高。"
        "泰国气象部门预计本周仍有强降雨。"
    ),
    "https://www.bbc.co.uk/news/articles/cm750plvwy9vo": (
        "瑞士选民以超过70%的反对票，否决将更严格中立定义写入宪法的提案。该倡议由右翼瑞士人民党推动，"
        "若通过将要求瑞士未经联合国批准不得实施制裁，并限制与北约深化合作。俄罗斯全面入侵乌克兰后，"
        "瑞士中立传统再度引发辩论，莫斯科公开支持该倡议，而联邦政府及主要政党均反对。"
        "研究员卢卡斯·戈尔德表示，选民并非拒绝中立本身，而是支持对俄罗斯实施制裁。"
        "瑞士外长伊gnazio·卡西斯称，中立“始终以一定灵活性适用”，并不意味着对违反国际规则的行为袖手旁观。"
        "瑞士1815年在维也纳会议获“永久中立”地位，1907年海牙公约进一步界定其中立义务。"
    ),
    "https://www.bbc.co.uk/news/articles/cw98005ndz7no": (
        "也门塔伊兹市前线战事升级，胡塞武装与沙特支持的政府军在山地激烈交火。"
        "半岛电视台记者在政府军陪同下前往距胡塞控制区仅数百米的前线，途中遭遇无人机逼近并躲避炮击。"
        "9月10日胡塞武装夺取红海港口穆哈后，四年来的停火局面破裂，并控制俯瞰曼德海峡的战略地带。"
        "塔伊兹是也门第三大城市，人口近百万，处于政府军与胡塞武装控制区交汇地带。"
        "联合国难民署称，仅本月就有超过13万人因也门战事流离失所，另有520万人此前已因内战流离失所。"
        "塔伊兹革命医院重症监护病房床位几乎全满，12岁女孩在放牧时被迫击炮弹片击中头部，医生称其脑部受损严重。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/serbian-president-aleksandar-vucic-resigns-amid-prolonged-protests": (
        "塞尔维亚总统亚历山大·武契奇宣布辞职，将竞选总理参加10月25日提前举行的议会选举。"
        "武契奇2014年以来长期主导塞尔维亚政坛，因宪法限制无法寻求第三任期总统，"
        "现试图通过议会选举延续权力。辞职前他赦免49人，其中23人与抗议活动有关。"
        "2024年11月诺维萨德火车站雨棚坍塌致16人死亡，引发近两年的学生主导大规模抗议，"
        "示威者指控政府腐败、缺乏透明度并干预国家机构。武契奇及盟友否认相关指控。"
        "“学生获胜”运动将与多个反对党联合参选。分析人士警告，若10月25日选举后局势恶化，"
        "塞尔维亚政治危机可能进一步外溢至西巴尔干地区。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/powerful-storm-floods-us-northeast-causes-power-outages": (
        "一场强风暴连续第二天袭击美国东北部海岸线，低洼地区再次遭遇洪涝，"
        "新英格兰地区数以万计家庭断电。新泽西潮汐上涨淹没低洼社区，"
        "长岛强风刮倒树木并损坏房屋和电线杆。纽约皇后区霍华德海滩街道被淹。"
        "自周五以来，新泽西部分区域降雨量超过10厘米，叠加海水上涨，"
        "部分地区出现近十年来未见的高水位洪涝。这场“东北风暴”让人联想到2012年"
        "造成600多亿美元损失的“桑迪”飓风，但本次影响远不及当时。"
        "周日东北部和中大西洋地区仍有超过10万户断电，波士顿洛根机场取消逾250架次航班。"
        "预报员称风暴虽在减弱，但周日夜间高潮仍可能继续引发潮汐洪涝。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/pope-pledges-action-on-clergy-child-abuse-in-meeting-with-french-survivors": (
        "罗马天主教教皇利奥十四世在法国卢尔德会见七名神职人员性侵幸存者，"
        "梵蒂冈称其“感谢他们痛苦的证词”并“重申结束天主教神父造成伤害的承诺”。"
        "幸存者让-马里·德尔博称，教皇看到他情绪崩溃后将他拥入怀中，"
        "“是极不寻常的时刻”。幸存者表示感到被倾听，对教皇的关怀和对其个案的了解印象深刻，"
        "但希望言论能伴随实际行动。2021年独立调查估计，70年来约33万名法国儿童"
        "曾遭天主教神职人员和相关人员性侵。教皇在卢尔德面向约15万人举行弥撒时称，"
        "教会必须有勇气面对过去，但未直接为性侵道歉。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/south-korea-ukraine-relations-sour-over-north-korean-pow-transfer": (
        "韩国总统办公室要求乌克兰就披露朝鲜战俘转移事宜作出正式解释并道歉，"
        "指责基辅违反此前保密协议并损害互信。"
        "乌克兰总统泽连斯基在联大发言中称，乌方已将两名朝鲜战俘移交韩国。"
        "韩方称，保密协议旨在依照国际法和人道原则保护士兵安全。"
        "乌总统办公室则否认存在保密协议。两名朝鲜士兵2025年1月在俄罗斯库尔斯克州被乌军俘获，"
        "韩媒称他们表达过投奔韩国的意愿。韩国情报部门估计，"
        "朝鲜自2024年以来向俄罗斯派遣约1.4万至1.5万名士兵支援对乌作战，"
        "其中逾6000人在战斗中丧生。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/at-least-12-dead-and-dozens-missing-after-a-vessel-capsizes-in-drc": (
        "刚果（金）南基伍省基伍湖一艘载有鱼贩的船只周六夜间倾覆，"
        "当局称至少12人死亡、数十人仍失踪。"
        "当地官员称，船上载有50多人，约15人获救，事故原因尚不清楚。"
        "刚果（金）河流和湖泊是逾1亿人口的重要交通方式，船只常超载且乘客很少穿救生衣。"
        "本周早些时候，坦噶尼喀湖另一起沉船事故造成至少41人死亡、49人获救。"
        "民间社会人士多塞勒·巴加扎内表示，当局已开始要求乘客穿救生衣，"
        "但许多人仍未遵守。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/israel-revokes-dutch-diplomats-status-over-sanctions-on-settlements": (
        "以色列外交部宣布，撤销荷兰驻约旦河西岸拉姆allah代表处外交官的以色列外交身份，"
        "以回应荷兰9月22日生效的禁止进口、购买和销售约旦河西岸非法定居点商品的措施。"
        "以外长吉迪恩·萨尔称，若荷兰希望继续代表巴勒斯坦利益，"
        "应改在巴勒斯坦权力机构辖区开展活动，而非在以色列领土上。"
        "以色列要求相关外交官在七天内交还以色列签发的外交证件。"
        "萨尔称，任何对以色列采取敌对单边行动的国家都将失去在该地区的影响力。"
        "荷兰是全球通往欧洲的重要贸易门户，有机构称荷兰占以色列定居点农产品出口欧盟份额的近一半。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/three-killed-four-injured-in-shooting-at-detroit-michigan-strip-club": (
        "美国密歇根州底特律一家通宵脱衣舞俱乐部周日上午发生枪击，造成3人死亡、4人受伤。"
        "警方称，在上午7时20分接警后四分钟内赶到现场，发现3人遭致命枪击。"
        "另有4名20至30岁男女受伤，伤势非致命。3名死者年龄均超30岁，身份尚未公布。"
        "底特律警察局长托德·贝蒂森表示，枪击前俱乐部内发生口角，"
        "“有人决定用枪支暴力解决问题”。警方尚未宣布逮捕，但称已掌握线索，"
        "公众暂无持续危险。该地址今年以来已接到7次警方呼叫。市长玛丽·谢菲尔德表示，"
        "将打击非法通宵经营场所。"
    ),
    "https://www.aljazeera.com/news/2026/9/27/atrocious-crime-cuban-official-decries-possibility-of-us-military-action": (
        "古巴副外长卡洛斯·费尔南德斯·德·科西奥警告，美国对古巴采取军事行动将构成"
        "“骇人听闻的国际罪行”，并驳斥特朗普称古巴是“失败国家”的说法。"
        "特朗普周二在联大称“自由将降临”古巴，周六又表示“不认为需要动用军队”，"
        "但称古巴“失败得非常严重”。德·科西奥称，通过中断商业运输、"
        "以饥饿胁迫民众、剥夺稳定医疗和燃料等方式施压，"
        "“相当于种族灭绝”。美国对古巴经济制裁已持续60余年，"
        "特朗普政府今年还实施石油封锁，导致古巴燃料短缺和持续停电。"
        "他表示古巴必须做好应对军事侵略的准备，并仍愿在相互尊重、"
        "兼顾双方利益并尊重主权的前提下与华盛顿对话。"
    ),
    "https://www.theguardian.com/us-news/2026/sep/27/hurricane-nolo-hawaii-hurricane-polo-mexico": (
        "飓风“诺洛”周日正远离夏威夷群岛，但强降雨、山洪和强风的威胁仍在，"
        "尤其是仍在从先前风暴中恢复的大岛。诺洛中心位于檀香山以南约585公里，"
        "最大持续风速185公里/小时，预计将进一步增强并向西北转向。"
        "外围雨带可能在大岛部分地区带来高达50厘米降雨，引发危及生命的洪涝和泥石流。"
        "与此同时，飓风“波罗”以205公里/小时风速逼近墨西哥下加利福尼亚半岛，预计周一登陆。"
        "墨西哥政府已发布沿岸飓风警告，海军在瓜伊马斯和马萨特兰港口部署船只准备运送人道援助。"
        "美国国家气象局称，受厄尔尼诺影响，本季太平洋风暴活动高于平均水平。"
    ),
    "https://www.theguardian.com/uk-news/2026/sep/27/villagers-raf-fairford-evacuation": (
        "英国格洛斯特郡韦尔福德村一名居民凌晨1点驾车回家时发现三辆白色厢式车和"
        "一群戴头套、面罩的男子，随即拨打999报警，警方约15分钟后到场。"
        "她认为自己的报警可能打乱了对方的计划。若未接到这通电话，"
        "当局可能无法及时察觉这些车辆和潜在威胁。"
        "近期费尔福德基地因允许美军用于对伊朗打击而安保明显加强。"
        "周日清晨，85户居民被警察敲门要求立即撤离至附近休闲中心。"
        "村民朱利安·塔兹伯里称警察“敲门说必须撤离，有重大事件，但无法透露细节”。"
        "爆炸物专家正在检查三辆厢式车，现场部署陆军、拆弹小组和反恐警察。"
        "该基地跑道近2英里，可起降B-1、B-52等重型轰炸机。"
    ),
    "https://news.un.org/en/story/2026/09/1168460": (
        "印度外长苏杰生周六在联大一般性辩论中表示，暴力冲突持续破坏国际和平与安全，"
        "而远离战场、对冲突不负直接责任的国家也在付出沉重代价。"
        "他对海湾地区持续冲突以及国际水道上商船和船员遭袭表示严重关切，"
        "并称西亚和中东要实现持久和平，必须落实两国方案。"
        "他还说，乌克兰战争进入第五年同样令人担忧，印度支持旨在实现和平的倡议。"
        "他警告，一个不断遭受威胁和压力的世界正“生活在深渊边缘”，"
        "并指出从金融、市场准入到供应链和技术，“一切都被武器化”，"
        "全球南方在粮食、燃料、化肥和融资危机中尤为艰难。"
        "他将恐怖主义描述为持续威胁，称国家支持的跨境恐怖主义是对全球秩序的直接冒犯。"
    ),
    "https://news.un.org/en/story/2026/09/1168462": (
        "联合国新闻《要点》栏目总结联大一般性辩论第五天：人工智能与移民等21世纪重塑性力量成为焦点。"
        "中国副总统韩正表示，人工智能应“向善”发展，并呼吁缩小数字鸿沟。"
        "新加坡外长维文称，人工智能是“最紧迫的前沿”，政府需要投资基础设施、技能和安全保障，"
        "“人类必须保持控制并承担责任”。"
        "牙买加外长警告，不能让人工智能“加深旧有不平等并制造全新的全球鸿沟”。"
        "马来西亚外长指出，全球南方不能仅仅成为数据中心所在地，而决策却在别处做出。"
        "摩尔多瓦总理称，技术发展快于监管；"
        "德国外长瓦德富尔既想象人工智能帮助人类预防饥荒、治愈癌症，"
        "也警告其在错误手中可能扰乱经济并影响全球和平。"
        "辩论还将于周一进行最后一天。"
    ),
    "https://news.un.org/en/story/2026/09/1168461": (
        "加拿大外长阿妮塔·阿南德周六在联大警告，国际秩序已进入深度动荡时代，"
        "呼吁在主要大国转向远离全球经济一体化之际加强多边合作。"
        "她表示，加拿大将追求更大战略自主，同时围绕共同挑战建立议题联盟，"
        "包括对乌克兰的支持和北极安全。加拿大与伙伴发起“多边主义伙伴”倡议，"
        "支持联合国改革。关于伊朗，她表示加拿大视其为地区和平与安全的主要威胁。"
        "关于以巴冲突，她重申支持通过谈判实现两国方案，"
        "并称约旦河西岸以色列定居点违反国际法。"
        "她最后表示，加拿大将自信而坚定地前行，继续恪守国际法。"
    ),
    "https://www.theguardian.com/world/2026/sep/27/mass-shootings-south-africa-johannesburg-cape-town": (
        "南非约翰内斯堡附近和开普敦附近两起大规模枪击共造成至少27人死亡，"
        "该国正面临全球最高的谋杀率之一。"
        "周六晚，8名持AK-47和手枪的枪手在约翰内斯堡西南韦德拉镇一家酒吧内外开枪，"
        "造成17人死亡、至少15人受伤，并焚毁两辆车辆后逃离。"
        "豪登省警察局长汤米·姆托姆贝尼表示，一条调查线索是非法采矿“地盘战争”。"
        "周日凌晨，开普敦附近勒旺德尔一家烧烤娱乐场再发生枪击，10人死亡、11人受伤，"
        "5人在现场死亡，5人在送医后死亡。两起案件周日均未宣布逮捕。"
        "总统西里尔·拉马福萨表示，安全部队将继续全力以赴。"
        "2024年南非谋杀率约为每10万人40起，是全球第九高；"
        "截至6月30日的12个月里，南非共记录逾2.27万起谋杀案。"
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
        print(
            f"  [{row['rank_no']}] {row['region']:12s} content={len(content):5d}  {row['title'][:40]}",
            file=sys.stderr,
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    domestic = sum(1 for r in result if r["region"] == "domestic")
    international = sum(1 for r in result if r["region"] == "international")
    print(f"Wrote {len(result)} items ({domestic} domestic / {international} international) to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
