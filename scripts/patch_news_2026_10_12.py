#!/usr/bin/env python3
"""One-off patch: Chinese intl translations and domestic fixes for 2026-10-12."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_daily_news import fetch_article, clamp_content  # noqa: E402

JSON_PATH = ROOT / "data" / "news_2026-10-12.json"

INTL_ZH: dict[str, dict[str, str]] = {
    "https://www.aljazeera.com/news/2026/10/11/us-homeland-security-secretary-sees-no-risk-from-livestreamed-execution?traffic_source=rss": {
        "title": "美国国土安全部长称直播处决不会增加安全风险",
        "content": (
            "美国国土安全部长马克韦恩·穆林为计划直播处决尼达尔·哈桑一事辩护，淡化有关画面可能被极端组织用作宣传的担忧。"
            "哈桑为前陆军少校，2009年在得州胡德堡基地枪击案中杀害13人，2013年被判处死刑，直播处决定于12月3日。"
            "穆林称观看者可自行选择是否收看。共和党参议员汤姆·蒂利斯等人警告，公开处决可能被恐怖组织用于招募并激化激进情绪。"
            "国防部长赫格塞思上周宣布直播计划引发争议，特朗普周六表示可能重新考虑。"
        ),
    },
    "https://www.aljazeera.com/news/2026/10/11/two-killed-near-israeli-occupied-area-in-south-lebanon?traffic_source=rss": {
        "title": "黎巴嫩南部两名男子在橄榄收获期间遇难",
        "content": (
            "黎巴嫩官方媒体称，南部宾特朱拜勒区两名男子在参与年度橄榄收获时遇难：一人因近期战事遗留爆炸物在弗龙村身亡，"
            "另一人在亚特尔镇遭以方炮击时在田间遇难。黎军指认以坦克火力并称袭击公然违反既有协议。"
            "今年6月黎以达成停火后南部暴力有所减少但未停止。国际移民组织8月记录近35万境内流离失所者。"
        ),
    },
    "https://www.aljazeera.com/news/2026/10/11/mexican-president-urges-residents-to-shelter-as-hurricane-simon-approaches?traffic_source=rss": {
        "title": "墨西哥总统敦促沿海居民就地避险应对四级飓风“西蒙”",
        "content": (
            "墨西哥总统克劳迪娅·辛鲍姆呼吁哈利斯科、科利马、纳亚里特和米却肯沿海居民在官方宣布危险解除前留在室内。"
            "四级飓风“西蒙”周日沿哈利斯科近海移动，风速至少约240公里/小时，部分地区累计降雨量或达76厘米，山区面临泥石流风险。"
            "哈利斯科28个市镇处于最高气旋警报，热门旅游城市巴亚尔塔港商家封堵门窗并堆放沙袋，部分地区已停课并组织疏散。"
        ),
    },
    "https://www.aljazeera.com/news/2026/10/11/republican-senator-says-trump-diesel-agreement-with-russia-may-be-illegal?traffic_source=rss": {
        "title": "共和党参议员称特朗普放宽对俄柴油制裁可能违法",
        "content": (
            "美国共和党参议员汤姆·蒂利斯质疑总统特朗普暂时放松对俄罗斯柴油制裁以压低油价的决定可能违反国会立法。"
            "蒂利斯称若白宫不调整路线，他将难以支持年底拨款等立法议程。七名跨党派参议员联名敦促政府立即撤销对俄能源制裁松绑。"
            "特朗普周五称与普京通话后同意向全球市场供应柴油，乌克兰总统泽连斯基批评此举为莫斯科战争机器输血。"
            "蒂利斯指出，要缓解能源压力应首先解决伊朗局势，并强调是普京发动战争而非泽连斯基。"
        ),
    },
    "https://www.aljazeera.com/news/2026/10/11/war-and-high-debt-to-dominate-imf-world-bank-meetings-in-bangkok?traffic_source=rss": {
        "title": "战争与高债务将主导曼谷IMF与世行年会议程",
        "content": (
            "本周全球财长与央行行长将在曼谷出席国际货币基金组织和世界银行年会，中东战事扩大、史上最大规模能源供应冲击"
            "及利率上升叠加，给本已疲弱的全球增长带来严峻风险。美以对伊朗战争进入第八个月，通胀影响预计主导会议议程。"
            "IMF总裁格奥尔基耶娃称约1.8万人注册参会。七国集团同意在特朗普压力下释放1亿桶柴油和原油应急储备。"
            "IMF研究显示食品与能源价格骤升日益成为推高通胀预期、加剧贫困并威胁稳定的危机来源；全球公共债务将达二战以来最高水平。"
        ),
    },
    "https://www.aljazeera.com/news/2026/10/11/turkiye-highway-crash-kills-11-injures-27-after-tour-bus-hits-truck?traffic_source=rss": {
        "title": "土耳其旅游大巴与拖车相撞致11死27伤",
        "content": (
            "土耳其马尼萨省盖布泽-奥尔汉加齐-伊兹密尔高速阿克希萨尔收费站附近，一辆旅游大巴与载有木板的拖车相撞，"
            "至少11人死亡、27人受伤。伤者已送医，大巴司机出院后被警方拘留。马尼萨省长称事故调查在检方协调下进行，"
            "内政部长呼吁严格遵守交通规则。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/c6pvg4jyz1m0o?at_medium=RSS&at_campaign=rss": {
        "title": "特朗普称俄乌同意“能源停火”，泽连斯基欢迎但俄方未回应",
        "content": (
            "美国总统特朗普称俄乌已同意立即生效的“能源停火”，但未公布细节。乌克兰总统泽连斯基起初表示惊讶，"
            "随后称若莫斯科同步遵守，基辅愿停止打击俄能源设施。泽连斯基指特朗普宣布后俄方仍袭击乌多地电力与能源设施。"
            "特朗普推动乌克兰停止打击俄炼油厂，以便落实美俄柴油交易，该交易在欧美及美国两党中引发批评。"
            "七名美国参议员称该交易违背禁止进口俄能源的法律，共和党参议员蒂利斯称可能危及美国人安全。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/cr93znyk44e1o?at_medium=RSS&at_campaign=rss": {
        "title": "利雅得机场两天内再遭胡塞袭击致1死11伤",
        "content": (
            "沙特官员称，首都利雅得哈立德国王国际机场周日再遭袭击，1名巴基斯坦居民死亡、11人受伤，"
            "此前一天同类袭击已致13死308伤。胡塞武装宣称对袭击负责并警告航空公司避开沙特机场与领空。"
            "美方称一名美国公民在前一日袭击中遇难，国务卿鲁比奥予以谴责。特朗普表示将迅速决定是否打击胡塞武装。"
            "地区紧张因也门内战及红海航运安全局势升级而加剧。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/c6jdm3zggl0ko?at_medium=RSS&at_campaign=rss": {
        "title": "英国首相称有明确证据表明俄罗斯干预了脱欧公投",
        "content": (
            "英国首相安迪·伯纳姆表示，有明确答案显示俄罗斯干预了2016年英国脱欧公投，并警告类似活动在法德等国持续。"
            "他在播客中称上任后曾询问相关情况。2020年英国议会情报与安全委员会报告未就俄是否影响公投结果下定论，"
            "但批评政府未充分评估威胁。伯纳姆宣布英国将设立新中心打击虚假信息，并加强《国家安全法》等工具。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/c6n9rvynl5p5o?at_medium=RSS&at_campaign=rss": {
        "title": "波兰拘留涉嫌策划刺杀总理图斯克男子",
        "content": (
            "波兰总理唐纳德·图斯克称，警方已拘留一名涉嫌策划对其及国防部长科西尼亚克-卡米什实施袭击的波兰籍嫌疑人。"
            "内政部称警方通过保护部门转交的邮件获悉威胁，特勤部门视威胁“极其严重”。图斯克感谢警方迅速果断行动。"
            "波兰近一周发生多起校园持刀案件，安全部门周日召开特别会议应对多重安全挑战。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/cm78pwdp3n5qo?at_medium=RSS&at_campaign=rss": {
        "title": "智库警告伊朗战争冲击英国财政大臣首份预算安排",
        "content": (
            "英国财政研究所警告，美以对伊朗战争引发的价格上涨给财政大臣约翰·希利编制首份预算带来重大挑战。"
            "高于预期的通胀可能侵蚀各部门可支配资金，迫使政府在减税、增支与削减之间抉择。"
            "俄乌战争与中东冲突推高全球能源价格并增加英国债务利息负担。IFS预计政府仍可能勉强满足财政规则，但缓冲空间缩小，"
            "为维持部门预算到2029-30年或需额外筹集约250亿英镑。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/cwy7lxx60dg5o?at_medium=RSS&at_campaign=rss": {
        "title": "联合国称吉布提近海沉船事故已致139人死亡含15名儿童",
        "content": (
            "国际移民组织称，一艘载有305人的移民船周四晚在吉布提奥博克附近倾覆，至少139人死亡、84人失踪，"
            "约82人获救，遇难者包括15名儿童。幸存者均为埃塞俄比亚公民。该航线每年吸引数万非洲之角移民前往海湾务工，"
            "2025年同一路线逾900人死失踪。也门内战与地区不稳定使穿越曼德海峡的偷渡仍屡禁不止。"
        ),
    },
    "https://www.theguardian.com/world/2026/oct/09/navanethem-navi-pillay-wins-nobel-peace-prize": {
        "title": "国际法院法官纳维·皮莱获诺贝尔和平奖",
        "content": (
            "挪威诺贝尔委员会将2026年和平奖授予南非籍国际法院法官、前联合国人权高专纳维·皮莱，"
            "表彰其推动国际法与和平解决争端。委员会提到她主持联合国调查委员会认定以色列在加沙实施灭绝种族行为等经历。"
            "皮莱正主持缅甸相关种族灭绝案件。以色列外交部强烈批评该决定。数小时后特朗普政府宣布对国际刑事法院实施新制裁。"
        ),
    },
    "https://www.theguardian.com/environment/2026/oct/09/isaias-strengthens-first-atlantic-hurricane-2026": {
        "title": "“伊萨亚斯”加强为2026年大西洋飓风季首个飓风",
        "content": (
            "“伊萨亚斯”已成为2026年大西洋飓风季首个飓风，风速约80英里/小时，最低气压975毫巴。"
            "美国国家海洋和大气管理局预计其周五接近美国墨西哥湾北部沿岸时将加强为二级飓风并登陆，"
            "沿岸降雨量约75至150毫米，局部可达250毫米，存在山洪与河流洪水风险，并可能出现危及生命的风暴潮。"
            "佛罗里达狭长地带、阿拉巴马和密西西比部分地区已发布飓风警告，当局呼吁民众准备长时间停电并遵守疏散令。"
            "受强厄尔尼诺影响，本季大西洋飓风活动异常偏弱，有记录以来首个飓风形成时间晚于1905年10月8日。"
        ),
    },
    "https://www.theguardian.com/world/2026/oct/08/south-korea-fuel-shipments-to-russia-domestic-law": {
        "title": "韩国称若查实向俄运油违法将依法处理",
        "content": (
            "韩国政府回应《卫报》关于韩港口向俄运送燃油的报道，称正核查相关装船情况，"
            "若确认违反国内法律法规将依法处理。卫报分析显示7月至8月约17.6万吨燃油（多为柴油）"
            "在韩多个港口装船后驶往俄远东，其中三艘油轮受英国和欧盟制裁。"
            "首尔称精炼石油产品不在其对俄出口管制主要清单内，海关未记录柴油等直接出口至俄，"
            "但将核查船舶实际航线与申报目的地是否一致。乌克兰方面批评此举与韩方制裁立场相悖，"
            "两国因战俘移交等议题关系紧张，韩外交部称将召回驻乌克兰大使。"
        ),
    },
    "https://www.theguardian.com/world/2026/oct/11/zelenskyy-trump-ukraine-russia-energy-ceasefire": {
        "title": "特朗普宣布乌俄能源停火，泽连斯基称事先不知情",
        "content": (
            "特朗普在社交媒体宣布乌俄立即生效能源停火且双方已同意，未提供细节。泽连斯基称若普京同步执行则乌方愿遵守，"
            "但强调须先看到俄方停止袭击乌能源设施。他反对特朗普放宽对俄柴油制裁，称将为普京战争提供额外资金。"
            "特朗普周六还要求乌克兰更换领导人。泽连斯基与英法加及欧盟领导人通话寻求支持，"
            "并指俄方周日仍袭击哈尔科夫等地电力设施，显示莫斯科无意停火。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/ckp8gyd65z2go?at_medium=RSS&at_campaign=rss": {
        "title": "图斯克称波兰校园持刀案受网络暴力崇拜煽动",
        "content": (
            "波兰总理图斯克表示，本周三起校园暴力袭击与网上对暴力的美化有关，已致1名女校工死亡、多人受伤。"
            "警方在全国搜查学校后拘留117名涉嫌持刀或威胁袭击者。图斯克称部分涉案者与极右翼网络环境有关，"
            "并指搜索纳粹内容及网络“杀人偶像”现象上升。安全部门同日还处理针对图斯克与国防部长的刺杀威胁情报。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/cr4g1pwxxlq1o?at_medium=RSS&at_campaign=rss": {
        "title": "分析人士：利雅得机场遇袭是本已紧张局势的危险升级",
        "content": (
            "沙特首都机场连续遭袭标志着本已高度紧张的中东局势进一步恶化。胡塞武装近期加大对沙特境内关键基础设施打击，"
            "并试图控制红海沿岸与曼德海峡要地。也门内战已逾十年，造成严重人道危机。"
            "袭击亦与伊朗、美国、以色列之间更广泛对抗相关。特朗普称将迅速决定是否军事介入，"
            "但在美国中期选举前直接卷入也门冲突面临国内政治压力。"
        ),
    },
    "https://www.bbc.co.uk/news/articles/cw0k0g57mk3zo?at_medium=RSS&at_campaign=rss": {
        "title": "乌克兰第三次袭击俄科技巨头Yandex数据中心",
        "content": (
            "乌克兰无人机袭击莫斯科附近弗拉基米尔州Yandex数据中心，系本周第三次打击这家被称为“俄罗斯谷歌”的企业。"
            "公司称设施受损并暂停运营，部分服务中断。基辅称目标是削弱为战争提供收入的俄方基础设施。"
            "袭击发生在美国总统特朗普要求乌克兰停止打击俄炼油厂数小时后。俄方周末继续袭击扎波罗热等地，"
            "周六至少20人包括4名儿童在袭击中丧生。"
        ),
    },
    "https://www.theguardian.com/world/2026/oct/11/poland-possible-plot-attack-prime-minister-donald-tusk": {
        "title": "波兰总理称涉嫌策划刺杀其与国防部长男子已被拘留",
        "content": (
            "波兰总理唐纳德·图斯克在社交媒体确认，威胁对其及国防部长科西尼亚克-卡米什发动袭击的男子已被拘留，"
            "并赞扬警方行动迅速果断。内政部长称警方收到可信刺杀情报后启动应对，特勤协调机构称威胁“极其严重”，"
            "存在较高实施可能。波兰作为北约与欧盟成员，在近期校园持刀事件后整体安全警戒升高。"
        ),
    },
}

DOMESTIC_FIXES = {
    27: {
        "title": "郑钦文创造历史 首夺中网女单冠军",
        "url": "https://www.chinanews.com.cn/ty/2026/10-12/10711158.shtml",
        "source": "中国新闻网",
    },
    30: {
        "title": "王曼昱女单卫冕 国乒两冠收官WTT中国大满贯",
        "url": "https://www.chinanews.com.cn/ty/2026/10-11/10711146.shtml",
        "source": "中国新闻网",
    },
    40: {
        "title": "波兰拘留涉嫌策划刺杀总理图斯克男子",
        "url": "https://www.bbc.co.uk/news/articles/c6n9rvynl5p5o?at_medium=RSS&at_campaign=rss",
        "source": "BBC",
        "region": "international",
    },
    47: {
        "title": "图斯克称波兰校园持刀案受网络暴力崇拜煽动",
        "url": "https://www.bbc.co.uk/news/articles/ckp8gyd65z2go?at_medium=RSS&at_campaign=rss",
        "source": "BBC",
        "region": "international",
    },
}


def main() -> None:
    items = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by_rank = {i["rank_no"]: i for i in items}

    # domestic rank 1 refetch
    d1 = by_rank[1]
    d1["content"] = fetch_article(d1["url"])

    for rank, patch in DOMESTIC_FIXES.items():
        row = by_rank[rank]
        row.update({k: v for k, v in patch.items() if k != "region"})
        if patch.get("region"):
            row["region"] = patch["region"]
        if row["region"] == "domestic":
            row["content"] = fetch_article(row["url"])

    for row in items:
        if row["region"] != "international":
            continue
        zh = INTL_ZH.get(row["url"])
        if not zh:
            print(f"missing zh for {row['url']}", file=sys.stderr)
            continue
        row["title"] = zh["title"]
        row["content"] = clamp_content(zh["content"])

    JSON_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"patched {JSON_PATH}")


if __name__ == "__main__":
    main()
