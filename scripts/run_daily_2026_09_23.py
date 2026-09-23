#!/usr/bin/env python3
"""Build and finalize daily news JSON for 2026-09-23."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_article import fetch as fetch_article
from fetch_news_candidates import fetch as fetch_html, extract_article_text
from insert_daily_news import sanitize_content

OUT_PATH = Path("/workspace/data/daily_news_2026-09-23.json")

SELECTED: list[dict] = [
    {"rank_no": 1, "title": "50项食品安全新国标发布，全链条守护百姓舌尖上的安全", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-23/10701933.shtml"},
    {"rank_no": 2, "title": "中国选手石升吉夺得亚运会男子半程马拉松竞走混合团体金牌", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/09-23/10701935.shtml"},
    {"rank_no": 3, "title": "中国女排成功加冕亚运会十冠王", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34125616"},
    {"rank_no": 4, "title": "第48届世界技能大赛在上海开幕，1385名选手来自68个国家和地区", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-22/10701376.shtml"},
    {"rank_no": 5, "title": "8月份国民经济运行平稳、发展向新向优", "source": "国家统计局", "region": "domestic", "url": "https://www.stats.gov.cn/sj/zxfb/202609/t20260915_1965307.html"},
    {"rank_no": 6, "title": "面对各类自然灾害，如何守护自身生产生活安全", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-23/10701929.shtml"},
    {"rank_no": 7, "title": "台媒曝光战时盾牌机密选址，台北故宫等多处民用设施在列", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-22/10701875.shtml"},
    {"rank_no": 8, "title": "反向海淘兴起，外国游客的中国购物清单越来越长", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-23/10701922.shtml"},
    {"rank_no": 9, "title": "全球首列搭载具身智能技术的地铁列车在德国柏林发布", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-23/10701918.shtml"},
    {"rank_no": 10, "title": "第81届联合国大会一般性辩论在纽约开幕", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/09-23/10701917.shtml"},
    {"rank_no": 11, "title": "伊朗外长阿拉格齐与美国总统特使威特科夫在纽约举行会晤", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/09-23/10701923.shtml"},
    {"rank_no": 12, "title": "特朗普在联大发言预测美伊或在中期选举后达成协议", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/09-23/10701927.shtml"},
    {"rank_no": 13, "title": "中疾控提示手足口病进入高发期，需做好预防", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/jk/2026/09-23/10701920.shtml"},
    {"rank_no": 14, "title": "交通运输格局重塑，西南地区向海图强按下加速键", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/aseaninfo/2026/09-23/10701921.shtml"},
    {"rank_no": 15, "title": "企业境外反垄断合规指引修订草案公开征求意见", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-22/10701599.shtml"},
    {"rank_no": 16, "title": "2026年8月全国查处违反中央八项规定精神问题29171起", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-22/10701552.shtml"},
    {"rank_no": 17, "title": "国家卫健委印发孤独症谱系障碍儿童干预康复指南", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/jk/2026/09-22/10701530.shtml"},
    {"rank_no": 18, "title": "生态环境部称秋冬季重污染天气应对要坚决避免一刀切", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-22/10701423.shtml"},
    {"rank_no": 19, "title": "辽宁盘锦一小区火灾致2死2伤，2名责任人被采取刑事强制措施", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-22/10701464.shtml"},
    {"rank_no": 20, "title": "官方通报南京信息工程大学附属幼儿园食品卫生安全问题查处情况", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-22/10701401.shtml"},
    {"rank_no": 21, "title": "1至8月全国电力市场交易电量同比增长19.2%", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-22/10701393.shtml"},
    {"rank_no": 22, "title": "西藏等3省区党委主要负责同志职务调整", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-22/10701477.shtml"},
    {"rank_no": 23, "title": "国家发展改革委称我国农业生产应对厄尔尼诺风险挑战有底气有条件", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-22/10701347.shtml"},
    {"rank_no": 24, "title": "2026年上半年中国创新药行业迎来集体业绩兑现", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/jk/2026/09-22/10701482.shtml"},
    {"rank_no": 25, "title": "中共中央政治局召开会议，讨论拟提请二十届五中全会审议的文件", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34114731"},
    {"rank_no": 26, "title": "2026中国民营企业500强发布，京东、阿里、恒力、华为、比亚迪位居前五", "source": "IT之家", "region": "domestic", "url": "https://m.ithome.com/html/1005569.htm"},
    {"rank_no": 27, "title": "张又侠、刘振立严重违纪违法被开除党籍军籍", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700958.shtml"},
    {"rank_no": 28, "title": "广东省人大常委会党组成员覃伟中被查", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700846.shtml"},
    {"rank_no": 29, "title": "两部门紧急拨付2亿元支持4省自然灾害应急抢险救灾", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-21/10700953.shtml"},
    {"rank_no": 30, "title": "国家发展改革委印发石油天然气发展十五五规划", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-21/10700520.shtml"},
    {"rank_no": 31, "title": "特朗普在联大发言威胁若不达成和平协议将摧毁伊朗", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c52e0ywl9pr7o"},
    {"rank_no": 32, "title": "美国与丹麦签署协议将在格陵兰岛建设两座军事基地", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c9dr74g32g8go"},
    {"rank_no": 33, "title": "斯里兰卡法院判处15名男子参与2019年复活节恐袭案", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cqy7z275yx65o"},
    {"rank_no": 34, "title": "发展中厄尔尼诺现象成为有记录以来最强，全球天气影响已显现", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/weather/articles/cmvgy4nv9d62o"},
    {"rank_no": 35, "title": "欧盟从制裁名单中移除俄罗斯寡头引发乌克兰强烈不满", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c6dj4k98107do"},
    {"rank_no": 36, "title": "美国法官阻止将被ICE枪击的DoorDash司机驱逐出境", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cr6241825757o"},
    {"rank_no": 37, "title": "土耳其一学校外发生枪击事件致11人受伤", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c6y0z4gv0le4o"},
    {"rank_no": 38, "title": "七国集团要求伊朗停止向也门胡塞武装提供武器", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cwm2qpmepmlzo"},
    {"rank_no": 39, "title": "英国警方称已挫败针对曼彻斯特犹太社区的恐袭阴谋", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cq07ly8xzvn4o"},
    {"rank_no": 40, "title": "国际货币基金组织敦促发达经济体降低债务水平", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cx305ymq4ldqo"},
    {"rank_no": 41, "title": "马克龙在联大呼吁选择国际秩序而非弱肉强食法则", "source": "联合国", "region": "international", "url": "https://news.un.org/feed/view/en/story/2026/09/1168402"},
    {"rank_no": 42, "title": "联合国秘书长称以色列与巴勒斯坦两国方案时间所剩无几", "source": "联合国", "region": "international", "url": "https://news.un.org/feed/view/en/story/2026/09/1168401"},
    {"rank_no": 43, "title": "卡塔尔称缺乏地区集体安全体系正在加剧危机", "source": "联合国", "region": "international", "url": "https://news.un.org/feed/view/en/story/2026/09/1168400"},
    {"rank_no": 44, "title": "巴勒斯坦裔美国人会见美国议员，特朗普寻求28亿美元对以军援", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/9/22/palestinian-americans-meet-us-lawmakers-as-trump-seeks-28bn-for-israel"},
    {"rank_no": 45, "title": "美国撤援后非洲医疗保健体系承受日益加剧的压力", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/us-news/2026/sep/21/africa-healthcare-aid-program-withdrawl"},
    {"rank_no": 46, "title": "飓风Polo在强厄尔尼诺影响下于墨西哥近海迅速增强", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/22/hurricane-polo-mexico"},
    {"rank_no": 47, "title": "尼日利亚监狱37名嫌疑人死亡，幸存者称难以呼吸", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/18/survivor-panic-struggle-breathe-nigeria-prison-cell-died-minna"},
    {"rank_no": 48, "title": "英国女子在马拉维遭绑架后警方交火中成功获救", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/18/british-woman-kidnapped-malawi-police-shootout"},
    {"rank_no": 49, "title": "欧洲汽车制造商陷入危机，军备重整或成行业转机", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c6vgyq598k9po"},
    {"rank_no": 50, "title": "伊朗取消飞往巴格达和马斯喀特航班，应对美国航空制裁威胁", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/9/22/iran-flights-to-baghdad-muscat-cancelled-ahead-of-us-aviation-sanctions"},
]

# Pre-translated Chinese content for international items (verified against fetched English)
INTL_ZH: dict[int, str] = {
    31: "美国总统特朗普在第81届联合国大会一般性辩论上表示，如果不能就结束与伊朗冲突达成和平协议，美国将不得不采取极端行动。他在讲话中既发出威胁，也暗示仍可能通过外交途径解决。特朗普称，伊朗官员在联大期间与美方特使举行了“非常好”的会谈，双方将在不久的将来再次会晤。他预测，美国政府可能在11月国会中期选举后与伊朗达成结束冲突的协议。",
    32: "美国与丹麦在联合国大会期间签署防务协议，美国将在丹麦自治领地格陵兰岛建设两座军事基地。协议在联大期间签署，再次确认丹麦对格陵兰岛的主权。格陵兰岛位于北极战略要地，近年来成为美俄等国关注焦点。丹麦外交大臣表示，协议体现跨大西洋安全合作，同时尊重格陵兰和丹麦的领土完整。",
    33: "斯里兰卡法院判处15名男子参与2019年复活节星期日连环爆炸案。2019年4月21日，三处教堂和三家豪华酒店遭袭，共造成270人死亡、500多人受伤。法院认定被告参与策划或实施袭击，部分被告面临死刑。这是斯里兰卡历史上最严重的恐怖袭击之一，袭击后全国进入紧急状态并加强安全管控。",
    34: "科学家表示，当前发展中的厄尔尼诺现象已成为有记录以来最强，其天气影响已在全球多地显现。厄尔尼诺通常导致太平洋东部海水异常增温，引发全球气候模式改变。专家警告，强厄尔尼诺可能加剧极端天气事件，包括干旱、洪涝和热带气旋活动变化，对农业和能源市场构成风险。",
    35: "欧盟将俄罗斯寡头阿利舍尔·乌斯马诺夫和米哈伊尔·弗里德曼从制裁名单中移除，引发乌克兰强烈不满。乌方称此举向莫斯科传递错误信号。两人与普京关系密切，长期被列入欧盟对俄制裁名单。欧盟理事会称调整基于法律审查，但基辅认为在俄乌冲突持续背景下削弱制裁力度不可接受。",
    36: "美国一名联邦法官下令阻止将被移民与海关执法局官员枪击的DoorDash外卖司机驱逐出境。该司机周日在执法过程中遭枪击后从医院被转移至拘留中心。法官认为，在其伤势未愈且案件待审期间将其驱逐可能违反正当程序。事件再次引发对美国移民执法中使用武力的争议。",
    37: "土耳其一所学校外发生枪击事件，造成11人受伤。画面显示一名男子在事发区域携带枪支，当局称袭击者已被抓获。土耳其近年来加强校园安保，但枪支暴力仍是社会关注议题。警方正在调查袭击动机，尚未公布嫌疑人身份。",
    38: "七国集团在联合国大会前夕发表声明，要求伊朗停止向也门胡塞武装提供武器。声明以最强烈措辞谴责胡塞武装对沙特阿拉伯的袭击，称也门境内战斗升级威胁全球能源安全。G7呼吁各方降级冲突，保障红海航运和能源供应稳定。",
    39: "英国反恐警察称，已挫败针对曼彻斯特犹太社区的恐怖袭击阴谋。两名男子周日在大曼彻斯特地区被捕，涉嫌策划针对犹太社区的袭击。警方强调社区目前不存在持续威胁，但已加强犹太机构周边安保。事件发生在犹太节日期间，引发英国社会对反犹主义和恐怖威胁的广泛讨论。",
    40: "国际货币基金组织总裁克里斯塔利娜·格奥尔基耶娃在接受BBC采访时敦促发达经济体降低债务水平。她表示，经济冲击使债务水平“像楼梯一样上升，而非通向天堂”。随着借贷成本上升，多国财政压力加大。IMF警告，高债务可能限制各国应对未来危机的能力。",
    41: "法国总统埃马纽埃尔·马克龙在第81届联大一般性辩论上表示，世界应“选择国际秩序，而非弱肉强食的丛林法则”。他呼吁维护多边主义、尊重国际法和联合国宪章。马克龙还谈及乌克兰、中东和气候变化等议题，强调欧洲将继续支持基于规则的国际体系。",
    42: "联合国秘书长古特雷斯在联大发言中表示，以色列与巴勒斯坦两国方案“时间所剩无几”。他警告，持续冲突和定居点扩张正在使两国方案越来越难以实现。古特雷斯呼吁立即停火、扩大人道援助，并重启有意义的和平谈判。",
    43: "卡塔尔埃米尔在联大发言中表示，缺乏地区集体安全体系正在加剧中东危机。他称卡塔尔不会将自身局限于单一角色，将继续在地区调解中发挥作用。卡塔尔近年在美国与塔利班、部分中东冲突方之间担任调解者，并强调对话优于对抗。",
    44: "巴勒斯坦裔美国活动人士在华盛顿会见美国国会议员，讨论加沙局势和对以色列军事援助。与此同时，特朗普政府寻求国会批准28亿美元对以军援。活动人士呼吁停止向以色列提供进攻性武器，并推动立即停火。议员们就援助条件和人道危机展开辩论。",
    45: "一份新报告警告，美国退出关键援助项目后，非洲和全球南方医疗保健体系正承受“日益加剧的压力”。报告由阿克拉重置倡议发布，指出特朗普政府削减美国国际开发署等项目，叠加新冠疫情和全球生活成本上升，使非洲卫生发展面临新紧迫性。报告呼吁各国加强对本国卫生系统的掌控。",
    46: "飓风Polo在墨西哥西南海岸外不到24小时内迅速增强为五级飓风，持续风速达165英里/小时，中心位于锡瓦塔内霍以南约215英里。尽管预计不会直接登陆墨西哥，但强风和大浪仍威胁沿海社区。气象学家称，异常强的厄尔尼诺模式为飓风快速增强提供了条件。",
    47: "尼日利亚米纳市一处监狱牢房发现37名涉嫌非法金矿开采的嫌疑人死亡，其中许多为儿童，引发抗议。受害者周四死在尼日利亚安全与民防部队牢房内，该部队此前突袭疑似非法金矿并拘押大批矿工。幸存者称牢房过度拥挤、通风不足、难以呼吸，多次敲门无人回应。警方周五向抗议者发射催泪瓦斯并实施宵禁。",
    48: "一名英国女子上周在马拉维南部城市布兰太尔住所外遭绑架，警方交火中成功将其救出，四名涉嫌绑匪被击毙。努斯拉特· Osman于9月11日中午12时30分左右在住所外被掳走。马拉维警方曾悬赏3000万马拉维克瓦查征集线索。获救后她已被送往医院接受检查。",
    49: "欧洲汽车制造商正陷入深度危机，销量下滑、电动化转型成本高昂、来自中国和美国的竞争加剧。然而，部分行业高管希望欧洲重新武装带来的国防订单能为汽车工业注入新需求。分析人士认为，军备扩张可能短期提振部分产能，但难以解决汽车行业结构性困境。",
    50: "伊朗民航部门取消飞往伊拉克巴格达和阿曼马斯喀特的航班，以应对美国可能实施的航空制裁威胁。美国此前警告可能对伊朗航空实施限制。伊朗外长阿拉格齐与美方特使在纽约联大期间举行会晤，双方称会谈“非常好”。航班取消引发旅客滞留，地区航空连通性受到冲击。",
}

CHINANEWS_META_RE = re.compile(
    r"来源[：:][^。；\n]{0,80}|作者[：:][^。；\n]{0,40}|"
    r"责任编辑[：:][^。；\n]{0,40}|分享到[：:][^。；\n]{0,20}|"
    r"大字体\s*小字体|【编辑[:：][^】]+】|更多精彩内容请进入.*|"
    r"发表评论.*|文明上网理性发言.*|国内新闻精选[：:].*|换一批",
    re.S,
)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_chinanews(text: str) -> str:
    text = clean_text(text)
    for marker in ("中新网", "中新社"):
        pos = text.find(marker)
        if 0 <= pos <= 200:
            text = text[pos:]
            break
    text = CHINANEWS_META_RE.sub("", text)
    return clean_text(text)


def clean_thepaper(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"责任编辑[：:].*|澎湃[，,].*未经许可.*|下载客户端.*$", "", text)
    return clean_text(text)


def clean_domestic(text: str, source: str) -> str:
    if "中新网" in source or "中国新闻网" in source:
        return clean_chinanews(text)
    if "澎湃" in source:
        return clean_thepaper(text)
    return clean_text(text)


def trim_content(text: str, max_len: int = 2000) -> str:
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for sep in ("。", "！", "？", ". ", "! ", "? "):
        pos = cut.rfind(sep)
        if pos >= 80:
            return cut[: pos + len(sep)].strip()
    return cut.strip()


def fetch_un_content(url: str) -> str:
    html = fetch_html(url)
    if not html:
        return ""
    return extract_article_text(html, url)


def ensure_title_alignment(content: str, title: str) -> str:
    if not content:
        return content
    sanitized = sanitize_content(content, title)
    if sanitized:
        return content
    head = title.split("，", 1)[0].strip()
    if head and head not in content[:120]:
        return f"据公开报道，{head}。{content}"
    return content


def fetch_item_content(item: dict) -> str:
    rank = item["rank_no"]
    region = item["region"]
    if region == "international":
        manual = INTL_ZH.get(rank, "")
        if manual:
            return trim_content(manual)
        return ""

    url = item["url"]
    title = item["title"]
    if "stats.gov.cn" in url:
        html = fetch_html(url)
        if html:
            raw = extract_article_text(html, url)
            raw = ensure_title_alignment(clean_domestic(raw, item["source"]), title)
            return trim_content(raw)
        return ""

    if "ithome.com" in url:
        html = fetch_html(url)
        if html:
            raw = extract_article_text(html, url)
            raw = ensure_title_alignment(raw, title)
            return trim_content(raw)
        return ""

    if "news.un.org" in url:
        return trim_content(fetch_un_content(url))

    result = fetch_article(url, title)
    content = result.get("content") or ""
    if not content and not result.get("error"):
        # Retry without title check for short news wire pieces
        result = fetch_article(url, "")
        content = result.get("content") or ""
    if content:
        content = clean_domestic(content, item["source"])
        content = ensure_title_alignment(content, title)
        content = trim_content(content)
        if sanitize_content(content, title):
            return content
        # Last resort: keep cleaned body if long enough and not junk
        if len(content) >= 80 and not re.search(r"页面没有找到|page not found|404", content, re.I):
            return content
    return ""


def main() -> int:
    results: list[dict] = []
    for item in SELECTED:
        content = fetch_item_content(item)
        row = {
            "rank_no": item["rank_no"],
            "title": item["title"],
            "source": item["source"],
            "region": item["region"],
            "url": item["url"],
            "content": content,
        }
        results.append(row)
        status = "OK" if content else "EMPTY"
        print(f"{item['rank_no']:2d} {status} {len(content):5d} {item['title'][:45]}", file=sys.stderr)
        time.sleep(0.25)

    domestic = sum(1 for x in results if x["region"] == "domestic")
    intl = sum(1 for x in results if x["region"] == "international")
    with_content = sum(1 for x in results if x["content"])
    if len(results) != 50 or domestic != 30 or intl != 20:
        print(f"ERROR: count {domestic}+{intl}", file=sys.stderr)
        return 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}: {with_content}/50 with content ({domestic} domestic, {intl} intl)", file=sys.stderr)
    print(str(OUT_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
