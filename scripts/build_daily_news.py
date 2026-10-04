#!/usr/bin/env python3
"""Build daily news JSON: fetch each URL, translate international items to Chinese."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import trafilatura

sys.path.insert(0, str(Path(__file__).resolve().parent))
from translate_util import translate_en_to_zh

MIN_CONTENT = 400
MAX_CONTENT = 2000
MAX_STORE = 20000

JUNK = re.compile(
    r"页面没有找到|page not found|404|access denied|请先登录|本网站所刊载信息",
    re.I,
)


def translate_zh(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text[:200]):
        return text.strip()
    return translate_en_to_zh(text)


def fetch_content(url: str) -> str | None:
    html = trafilatura.fetch_url(url)
    if not html:
        return None
    text = trafilatura.extract(html, favor_precision=True)
    if not text:
        return None
    text = re.sub(r"\s+\n", "\n", text.strip())
    text = re.sub(r"\n{3,}", "\n\n", text)
    if JUNK.search(text[:500]):
        return None
    return text


def normalize_content(text: str | None) -> str:
    if not text:
        return ""
    if len(text) < MIN_CONTENT:
        return ""
    if len(text) > MAX_CONTENT:
        text = text[:MAX_CONTENT]
    return text.strip()


CURATED: list[dict] = [
    # domestic 1-30
    {"title": "10月2日全社会跨区域人员流动量达30550.4万人次", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-03/10707485.shtml"},
    {"title": "国庆假期第二天全国道路交通总体平稳有序，公安部交管局发布出行安全提示", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-02/10707292.shtml"},
    {"title": "我国首个百兆瓦级全钒液流电池储能电站成功并网", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-02/10707319.shtml"},
    {"title": "外交部：中方欢迎普京总统出席APEC领导人非正式会议", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707596.shtml"},
    {"title": "美方称星巴克在新疆开设门店“道德沦丧”，外交部回应", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707597.shtml"},
    {"title": "商务部就对原产于欧盟的进口对硝基甲苯发起反倾销调查答记者问", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-03/10707388.shtml"},
    {"title": "2026年中国电影年度票房突破300亿元", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-03/10707479.shtml"},
    {"title": "今年2500亿元超长期特别国债支持消费品以旧换新资金已全部下达", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-03/10707526.shtml"},
    {"title": "中国队以169金89银83铜收官，创境外参加亚运会最佳战绩", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/10-03/10707602.shtml"},
    {"title": "洪可新夺得亚运会女子摔跤57公斤级金牌，中国队以169金收官", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/10-04/10707671.shtml"},
    {"title": "毕焜担任爱知·名古屋亚运会闭幕式中国体育代表团旗手", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/10-04/10707677.shtml"},
    {"title": "中国男足亚运队点球大战获胜摘铜，时隔28年再登亚运会领奖台", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/10-03/10707566.shtml"},
    {"title": "东航再通报“空姐下跪道歉”事件：已向公安机关报案", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-03/10707556.shtml"},
    {"title": "公安机关发布国庆假期防范电信网络诈骗安全提示", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707572.shtml"},
    {"title": "假期返程需备厚外套，中东部地区将有大风降温天气", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-03/10707649.shtml"},
    {"title": "我国首个深水油田流花油田取得新突破，“国之重器”协同运转", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707663.shtml"},
    {"title": "第169次中老缅泰湄公河联合巡逻执法行动结束", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-02/10707299.shtml"},
    {"title": "免签红利叠加便利服务，扬州向全球游客发出China Travel邀请", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-03/10707397.shtml"},
    {"title": "高铁试点增设自行车专座，新增13座试点车站", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-03/10707406.shtml"},
    {"title": "云冈石窟2026年客流量提前突破500万人次", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707422.shtml"},
    {"title": "中国新发现一种有羽毛恐龙化石，为飞行特征演化提供新证据", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707421.shtml"},
    {"title": "居民水电气计量整治“回头看”，10.62万个问题整改到位", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/10-03/10707519.shtml"},
    {"title": "应急管理部视频调度国庆假期安全防范工作", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707521.shtml"},
    {"title": "广东超70个镇街遭遇暴雨，全省最大降雨量达125毫米", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-02/10707298.shtml"},
    {"title": "九寨沟景区迎来2026年度第500万名游客", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/10-03/10707628.shtml"},
    {"title": "中国外交部：一贯反对将民用无人机用于军事目的", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707633.shtml"},
    {"title": "中国外交部：所谓新疆存在“种族灭绝”是赤裸裸的谎言", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/10-03/10707636.shtml"},
    {"title": "阿联酋检方认定迪拜航空涉事副驾驶企图实施恐怖活动", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/10-03/10707529.shtml"},
    {"title": "马克龙称七国集团成员国将释放至多1亿桶战略石油储备", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/10-03/10707343.shtml"},
    {"title": "澳大利亚发生汽车冲撞人群事件致9人受伤", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/10-03/10707443.shtml"},
    # international 31-50
    {"title": "阿联酋官员称迪拜航空副驾驶用斧头袭击机长", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c61wv7lgex13o"},
    {"title": "俄罗斯再次袭击乌克兰首都基辅第二座主要桥梁", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c83vqxzdg1yko"},
    {"title": "西班牙住房危机引发大规模抗议，全国逾50场集会举行", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cm2kej47095no"},
    {"title": "七国集团协调释放数百万桶石油和柴油以应对价格飙升", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/ck87zg8jnwngo"},
    {"title": "田纳西州监狱负责人将在克里斯塔·派克死刑执行失败后辞职", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c8zxl62yzxzxo"},
    {"title": "马萨诸塞州外海一架载有6人的医疗飞机失联", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cme3x85013llo"},
    {"title": "康奈尔大学校长称兄弟会强奸指控“令人深感不安”", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/ckly0leelnz4o"},
    {"title": "索马里总统称索马里在任何情况下都不会接受以色列存在", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/3/somalia-wont-accept-israeli-presence-under-any-circumstances-president"},
    {"title": "阿尔及利亚总统称已向尼日尔派遣战机挫败政变企图", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/3/algeria-sent-fighter-jets-to-niger-to-thwart-coup-attempt-president-says"},
    {"title": "田纳西州监狱官员在克里斯塔·派克死刑执行失败后辞职", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/3/tennessee-prisons-official-resigns-after-christa-pikes-failed-us-execution"},
    {"title": "西班牙住房改革失败后数万人走上街头抗议", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/3/tens-of-thousands-protest-in-spain-after-failed-housing-reforms"},
    {"title": "2026年巴西总统选举：选民需要了解什么", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/3/what-to-know-about-brazils-2026-presidential-election"},
    {"title": "百慕大飞往波士顿的空中救护车航班失联", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/10/3/air-ambulance-missing-on-flight-from-bermuda-to-boston"},
    {"title": "英格兰在欧国联7比0大胜克罗地亚，凯恩延续进球势头", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/sports/2026/10/3/england-trounce-croatia-7-0-in-nations-league-as-kane-goal-run-continues"},
    {"title": "联合国人权高专：乌克兰战争是必须结束的人权灾难", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168513"},
    {"title": "世卫组织：全球预期寿命回升至接近疫情前水平", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168515"},
    {"title": "刚果（金）埃博拉应对受挫：营地转运中心被烧毁", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168499"},
    {"title": "世卫组织呼吁在冬季来临前向加沙大规模输送援助", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/10/1168508"},
    {"title": "朝鲜在首尔要求就受伤士兵事件道歉后发射弹道导弹", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/oct/03/north-korea-launches-ballistic-missile-after-seoul-demands-apology-over-wounded-soldiers"},
    {"title": "美国海岸警卫队搜寻马萨诸塞州外海失联空中救护车", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/us-news/2026/oct/03/us-coast-guard-missing-air-ambulance-massachusetts"},
]


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/news_2026-10-04.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []
    for i, row in enumerate(CURATED, start=1):
        raw = fetch_content(row["url"])
        title = row["title"]
        content = raw or ""
        if row["region"] == "international" and raw:
            try:
                content = translate_zh(raw)
            except Exception:
                content = ""
        elif row["region"] == "domestic" and raw:
            content = raw
        content = normalize_content(content)
        items.append(
            {
                "rank_no": i,
                "title": title,
                "source": row["source"],
                "region": row["region"],
                "url": row["url"],
                "content": content,
            }
        )
        print(f"[{i}/50] {row['region']} len={len(content)}", file=sys.stderr)
        time.sleep(0.3)
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
