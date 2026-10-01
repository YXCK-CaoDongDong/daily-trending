#!/usr/bin/env python3
"""Build daily news JSON: fetch each URL, translate international items to Chinese."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import trafilatura
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


def normalize_content(text: str | None, title: str) -> str:
    if not text:
        return ""
    if len(text) < MIN_CONTENT:
        return ""
    if len(text) > MAX_CONTENT:
        text = text[:MAX_CONTENT]
    return text.strip()


CURATED: list[dict] = [
    # domestic 1-30
    {"title": "庆祝中华人民共和国成立77周年招待会在京举行，习近平发表重要讲话", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706444.shtml"},
    {"title": "习近平在庆祝中华人民共和国成立77周年招待会上发表讲话", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706448.shtml"},
    {"title": "烈士纪念日向人民英雄敬献花篮仪式在京隆重举行", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706088.shtml"},
    {"title": "《求是》杂志发表习近平总书记重要文章《加强普惠性、基础性、兜底性民生建设》", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706225.shtml"},
    {"title": "第四次全国文物普查省域整体验收全面完成", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706547.shtml"},
    {"title": "水利部：今年1至9月我国完成水利建设投资7950亿元", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706346.shtml"},
    {"title": "中央网信办部署开展“清朗·整治短视频虚假人设乱象”专项行动", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706334.shtml"},
    {"title": "检察机关依法对吴刚、王策鸿、刘建华、杨仁忠提起公诉", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706300.shtml"},
    {"title": "自然资源部：全国烈士陵园不动产全部完成确权登记发证", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10705982.shtml"},
    {"title": "中欧“微笑”卫星转入科学运行阶段并发布首批在轨观测数据", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706262.shtml"},
    {"title": "9月中国制造业采购经理指数为50.1%，升至扩张区间", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-30/10706023.shtml"},
    {"title": "9月中国非制造业商务活动指数为50.2%，重回扩张区间", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-30/10706121.shtml"},
    {"title": "中央财政首次对居民购房贷款实施贴息，政策10月1日起实施", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-30/10706390.shtml"},
    {"title": "云南昆明发生4.3级地震，市民有序避险", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-30/10706447.shtml"},
    {"title": "云南昆明4.3级地震暂无人员伤亡报告，启动地震四级应急响应", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-30/10706534.shtml"},
    {"title": "易会满涉嫌受贿案被提起公诉", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706106.shtml"},
    {"title": "朱忠明当选上海市市长", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706391.shtml"},
    {"title": "南部战区位中国黄岩岛领海领空及周边区域组织战备警巡", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706041.shtml"},
    {"title": "中国海警位中国黄岩岛领海及周边区域开展执法巡查", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706040.shtml"},
    {"title": "今年我国快递业务量已超1500亿件，较去年提前12天", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-30/10705989.shtml"},
    {"title": "哈伊高铁等四条高铁线路9月28日集中开通运营", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-28/10704644.shtml"},
    {"title": "泰国持续强降雨引发洪灾已致24人死亡，数百万人受灾", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gj/2026/10-01/10706584.shtml"},
    {"title": "国务院办公厅印发《关于发展体育赛事激发消费活力的意见》", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/20260930/d26d8411972a4267b3af13f9251320d5/c.html"},
    {"title": "国办意见提出到2030年培育一批具有世界影响力的体育赛事", "source": "中国政府网", "region": "domestic", "url": "https://www.gov.cn/zhengce/content/202609/content_7082492.htm"},
    {"title": "第33届中国电视金鹰奖揭晓，于和伟、宋佳获最佳男女主角", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cul/2026/09-29/10705945.shtml"},
    {"title": "陈艺文获爱知·名古屋亚运会跳水女子3米板金牌", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/09-30/10706373.shtml"},
    {"title": "中国男足亚运队1比2不敌韩国队，无缘亚运会决赛", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/09-30/10706427.shtml"},
    {"title": "中国跳水队在本届亚运会达成第100枚金牌", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/ty/2026/10-01/10706578.shtml"},
    {"title": "国台办回应鲁比奥涉售台武器言论", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706266.shtml"},
    {"title": "山东省日照市委原常委耿学伟被开除党籍", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-30/10706228.shtml"},
    # international 31-50
    {"title": "迪拜飞往特拉维夫航班上副驾刺伤机长，乘客与机组控制飞机后紧急降落", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cqjdv7pmj9dno"},
    {"title": "俄罗斯对乌克兰能源基础设施发动春季以来最大规模空袭", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/ckjw5jx2l393o"},
    {"title": "瑞士冰川2026年因高温与少雪损失超过5%冰量", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c6n9w0ypjwl9o"},
    {"title": "六名人贩子因英吉利海峡最严重偷渡事故被判过失杀人罪入狱", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/c6n8m33pn9djo"},
    {"title": "美国最高法院允许田纳西州执行克里斯塔·派克死刑", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cq8r6rjdvlx6o"},
    {"title": "普京未显露停战迹象，俄罗斯加大对乌克兰战争压力", "source": "BBC", "region": "international", "url": "https://www.bbc.co.uk/news/articles/cqx2ze420kpyo"},
    {"title": "加拿大真相与和解日活动附近车辆冲撞行人致两人死亡", "source": "BBC", "region": "international", "url": "https://www.bbc.com/news/articles/c3kg8gwzqnvko"},
    {"title": "Flydubai航班在5000米俯冲后安全降落，乘客回忆惊魂时刻", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/30/whoever-is-hearing-me-we-need-help-how-flight-1073-survived-its-5000-metre-plunge"},
    {"title": "联合国辩论聚焦谁应主导人工智能治理", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/09/1168498"},
    {"title": "索马里家庭在饥饿危机加剧背景下再遭暴力冲击", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/09/1168495"},
    {"title": "联合国儿童基金会：黎巴嫩五分之一儿童睡前挨饿", "source": "UN News", "region": "international", "url": "https://news.un.org/en/story/2026/09/1168490"},
    {"title": "宾夕法尼亚州确认第五例与麻疹相关的死亡病例", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/9/30/pennsylvania-confirms-fifth-measles-associated-death-as-us-outbreak-grows"},
    {"title": "美国参议院否决限制人工智能数据中心用电成本的法案", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/9/30/us-senate-rejects-bill-targeting-ai-data-centre-electricity-costs"},
    {"title": "香港一名记者因煽动罪被捕", "source": "Al Jazeera", "region": "international", "url": "https://www.aljazeera.com/news/2026/9/30/hong-kong-journalist-arrested-on-sedition-charge"},
    {"title": "法国高中生抗议蔓延，数百人被捕", "source": "Deutsche Welle", "region": "international", "url": "https://www.dw.com/en/france-hundreds-arrested-as-student-protests-escalate/a-79495633"},
    {"title": "欧盟五国计划2027年在非洲设立首个遣返中心", "source": "Deutsche Welle", "region": "international", "url": "https://www.dw.com/en/five-eu-states-plan-first-deportation-center-in-africa-for-2027/a-79490162"},
    {"title": "特朗普公布韩国对美投资计划，涉及阿拉斯加液化天然气项目", "source": "Yonhap", "region": "international", "url": "https://en.yna.co.kr/view/AEN20261001000852315"},
    {"title": "首尔与华盛顿选定得州电厂为战略投资首个项目", "source": "Yonhap", "region": "international", "url": "https://en.yna.co.kr/view/AEN20261001000400320"},
    {"title": "南非领导人呼吁男性在性别暴力问题上发声", "source": "The Guardian", "region": "international", "url": "https://www.theguardian.com/world/2026/sep/30/south-africa-gender-based-violence-women-killings"},
    {"title": "加沙难民营条件恶劣，非政府组织指以色列移动“黄线”", "source": "Deutsche Welle", "region": "international", "url": "https://www.dw.com/en/gaza-ngo-reports-dire-camp-conditions-says-israel-is-moving-yellow-line/a-79488777"},
]


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/daily_news_2026-10-01.json")
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
        content = normalize_content(content, title)
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
        print(f"[{i}/50] {row['region']} content_len={len(content)}", file=sys.stderr)
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
