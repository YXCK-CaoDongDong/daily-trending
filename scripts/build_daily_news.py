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
    {"rank_no": 1, "title": "山东省青岛市政府党组成员、副市长高健涉嫌严重违纪违法，接受山东省纪委监委纪律审查和监察调查", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-14/10695996.shtml"},
    {"rank_no": 2, "title": "山东省文化和旅游厅通报菏泽元代古沉船考古疑似文物遗失问题，已组建联合调查组开展核查", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-13/10695721.shtml"},
    {"rank_no": 3, "title": "媒体实地采访显示，菏泽被频繁检查的烧烤店116件投诉均来自同一举报人", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34061555"},
    {"rank_no": 4, "title": "2026年中国国际服务贸易交易会在北京闭幕，达成7类共1200余项成果", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-14/10696021.shtml"},
    {"rank_no": 5, "title": "市场监管总局批准发布4项矿山安全强制性国家标准，将于2027年3月1日起实施", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-14/10695960.shtml"},
    {"rank_no": 6, "title": "北京市将于2026年9月19日全民国防教育日在部分区域试鸣防空警报", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-14/10695985.shtml"},
    {"rank_no": 7, "title": "中央气象台发布预报，海南岛、广西等地未来三天将有较强降雨，需防范暴雨次生灾害", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-14/10695897.shtml"},
    {"rank_no": 8, "title": "受防汛防风应急响应影响，三亚全市涉山、涉海、涉空旅游项目暂停经营", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-14/10695919.shtml"},
    {"rank_no": 9, "title": "2026年WDSF世界青年霹雳舞锦标赛在成都收官，中国选手崔圣雨成功卫冕男子组冠军", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/09-14/10695950.shtml"},
    {"rank_no": 10, "title": "德国选手兹维列夫以3比1战胜谢尔顿，职业生涯首次夺得美网男单冠军", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/09-14/10695935.shtml"},
    {"rank_no": 11, "title": "2026数字人民币技术与应用论坛在北京首钢园举行，集中发布多项代表性研究成果", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-14/10695956.shtml"},
    {"rank_no": 12, "title": "北京市人大常委会通过决定，进一步促进民族团结进步，以首善标准建设示范城市", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-13/10695800.shtml"},
    {"rank_no": 13, "title": "中央组织部会同有关部委修订印发5个办法，进一步加强行业事业单位领导人员管理", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34060526"},
    {"rank_no": 14, "title": "多地官方辟谣称所谓“安全健康教育网”培训活动并非由官方组织", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34062597"},
    {"rank_no": 15, "title": "卫国戍边烈士肖思远的弟弟肖荣基获选拔提干", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34062603"},
    {"rank_no": 16, "title": "广东探索以词元消耗等数字化指标为人工智能企业授信", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-14/10695874.shtml"},
    {"rank_no": 17, "title": "央视曝光部分农村近200万元建成的污水处理站未投入使用仍向村民收费", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34062116"},
    {"rank_no": 18, "title": "Anthropic首席执行官呼吁放缓人工智能开发，称若方向错误人类毁灭概率不止10%", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34060452"},
    {"rank_no": 19, "title": "媒体调查称部分用人单位以“第一学历”设置隐性门槛，教育部此前明确我国没有“第一学历”概念", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34064723"},
    {"rank_no": 20, "title": "王毅就习近平主席赴印度出席金砖国家领导人第十八次会晤接受媒体采访", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34062704"},
    {"rank_no": 21, "title": "2026年9月11日外交部发言人毛宁主持例行记者会", "source": "外交部", "region": "domestic", "url": "https://www.fmprc.gov.cn/jzhsl_673025/202609/t20260911_12020879.shtml"},
    {"rank_no": 22, "title": "注册高仿账号批量搬运就医素材骗捐，“影子账号”窃取公众善意", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/fz/2026/09-14/10695972.shtml"},
    {"rank_no": 23, "title": "共享中国市场机遇，2026服贸会吸引1830余家企业线下参展、5300余家企业线上参展", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-14/10696023.shtml"},
    {"rank_no": 24, "title": "长江三峡·巫溪红池坝第十三届自行车赛在重庆巫溪开赛，选手挑战高海拔赛道", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/09-14/10695938.shtml"},
    {"rank_no": 25, "title": "朝中社报道，朝鲜人民军各级联合部队12日进行协同火力打击训练", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/09-14/10695980.shtml"},
    {"rank_no": 26, "title": "烧烤店主实名举报元青花杯遗失后遭同一人116次恶意投诉，店铺被迫停业摆摊卖红薯", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34060867"},
    {"rank_no": 27, "title": "大众网实地采访确认，菏泽被频繁检查的烧烤店116件投诉均来自同一举报人", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34061219"},
    {"rank_no": 28, "title": "游客在距市区约30公里的泸州东站下车后建议更改站名，官方作出答复", "source": "澎湃新闻", "region": "domestic", "url": "https://www.thepaper.cn/newsDetail_forward_34064772"},
    {"rank_no": 29, "title": "书香中国公益活动在河北怀来举行，向沙城中学附属小学捐赠数字图书馆", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-14/10695964.shtml"},
    {"rank_no": 30, "title": "部分企业滥用背景调查制造求职隐形门槛，物业纠纷和劳动仲裁记录成拒录原因", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-14/10695889.shtml"},
    # international 31-50
    {"rank_no": 31, "title": "俄罗斯无人机在波乌边境袭击乌克兰列车，约翰逊等欧洲官员刚离开车站", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cy5zg41dkqwo"},
    {"rank_no": 32, "title": "瑞典左翼政党联盟在议会选举中略微领先，最终结果仍难预料", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c0qx5d79kdeo"},
    {"rank_no": 33, "title": "印度尼西亚爪哇海客轮倾覆致6人死亡，130人仍下落不明", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cvgykzgljlyo"},
    {"rank_no": 34, "title": "特朗普结束爱尔兰访问，宣布将取消所有爱尔兰威士忌关税", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cx2z79n0eeno"},
    {"rank_no": 35, "title": "土耳其警方突袭多家同性恋酒吧及活动人士住所，拘留数十人", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cpve191wy47o"},
    {"rank_no": 36, "title": "美国众议员蒂芙尼所乘小型飞机因机械故障迫降威斯康星湖，游泳脱险", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c5y5d87x72zo"},
    {"rank_no": 37, "title": "特朗普淡化人工智能风险警告，称需与中国竞争", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c7v48vp31mdo"},
    {"rank_no": 38, "title": "加拿大向乌克兰提供防空支持，泽连斯基访问卡尔加里", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/10/zelenskyy-canada-visit"},
    {"rank_no": 39, "title": "六名尼日利亚籍嫌疑人因在线 romance 诈骗被引渡至美国", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/us-news/2026/sep/12/nigerians-extradited-online-romance-scams"},
    {"rank_no": 40, "title": "乌干达国王奥约正式安葬，继任者争议仍在继续", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/12/burial-king-oyo-uganda"},
    {"rank_no": 41, "title": "美国国务卿鲁比奥表示将加强与盟友合作打击毒品贸易", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/us-news/2026/sep/09/rubio-us-allies-drug-trafficking"},
    {"rank_no": 42, "title": "伊朗战争重塑金砖国家关系，也暴露内部分歧", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/ce8767g4jdpo"},
    {"rank_no": 43, "title": "俄罗斯民众追问2024年乌军库尔斯克攻势后数百名失踪者下落", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c62ene9kr71o"},
    {"rank_no": 44, "title": "阿富汗女性以“外星恐怖分子”法庭程序被从美国驱逐", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c3eqpd9zgl9o"},
    {"rank_no": 45, "title": "英格兰学校餐饮新规禁止油炸食品", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cy4zrepw78eo"},
    {"rank_no": 46, "title": "兹维列夫在美网男单决赛击败谢尔顿，夺得第二个大满贯冠军", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/sport/tennis/articles/c1wx9qpxjg3o"},
    {"rank_no": 47, "title": "启动1550万美元基金，推动全球消除女性割礼", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/global-development/2026/sep/11/15m-fund-launched-to-create-unstoppable-momentum-to-end-fgm-worldwide"},
    {"rank_no": 48, "title": "乌干达宣布退出哈里王子主办的Invictus Games", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/09/uganda-withdraws-invictus-games-out-of-respect-king-charles"},
    {"rank_no": 49, "title": "英国跨党派委员会呼吁立法应对人工智能对人权的威胁", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cwyzvgj70y4o"},
    {"rank_no": 50, "title": "加拿大拳击传奇选手丘瓦洛去世，享年89岁", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cy8zv8v1z7zo"},
]


def main() -> int:
    out = []
    for item in SELECTED:
        url = item["url"]
        html = fetch(url)
        content = ""
        if html and not JUNK_TEXT.search(html[:3000]):
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
