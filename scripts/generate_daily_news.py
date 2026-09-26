#!/usr/bin/env python3
"""Generate daily news JSON: fetch each article individually and verify."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")

CANDIDATES: list[dict[str, str]] = [
    # Domestic 30
    {"title": "习近平圆满结束对美国的国事访问", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10703971.shtml"},
    {"title": "习近平和彭丽媛同美国总统特朗普夫妇茶叙", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10703970.shtml"},
    {"title": "习近平和彭丽媛同美国总统特朗普夫妇共同参观美国国家档案馆", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-26/10703953.shtml"},
    {"title": "习近平和彭丽媛出席特朗普总统夫妇举行的欢迎国宴", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-25/10703632.shtml"},
    {"title": "习近平同美国总统特朗普举行小范围交流", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-25/10703534.shtml"},
    {"title": "中国海警局正告菲方立即停止在仁爱礁方向的侵权挑衅", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-25/10703738.shtml"},
    {"title": "中国选手陈妤颉夺得亚运会女子100米金牌", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-25/10703918.shtml"},
    {"title": "中国游泳队在本届亚运会以30枚金牌收官，创参赛史最佳成绩", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-26/10703960.shtml"},
    {"title": "张展硕在亚运会游泳项目夺得7金，追平单届个人夺金纪录", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-25/10703942.shtml"},
    {"title": "中秋节全国铁路预计发送旅客2234万人次", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-25/10703724.shtml"},
    {"title": "十五五期间全国碳市场覆盖范围将进一步扩大", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-25/10703757.shtml"},
    {"title": "十五五时期民政部将推动制定养老服务法", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/sh/2026/09-23/10702271.shtml"},
    {"title": "王陆进任河南省委副书记、省政府党组书记", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-23/10702154.shtml"},
    {"title": "俄公布国家杜马选举最终结果，统俄党获349席", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-25/10703900.shtml"},
    {"title": "也门胡塞武装称袭击沙特多地目标", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-25/10703614.shtml"},
    {"title": "哈萨克斯坦里海军演事故致14人遇难，搜救行动结束", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-25/10703804.shtml"},
    {"title": "马克龙表示法国正在尽一切努力避免燃油短缺", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-25/10703549.shtml"},
    {"title": "李在明称韩国将推动长期停滞的朝美对话尽快重启", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-23/10702286.shtml"},
    {"title": "伊朗总统佩泽希齐扬抵达纽约出席联合国大会", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-23/10702010.shtml"},
    {"title": "台风杜鹃致日本9人死亡4人失踪，超2万户家庭停电", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-23/10702213.shtml"},
    {"title": "中国选手张雨霏获得亚运会女子50米蝶泳冠军", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-25/10703740.shtml"},
    {"title": "中国选手覃海洋获得亚运会男子50米蛙泳冠军", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-25/10703743.shtml"},
    {"title": "中国选手李冰洁获得亚运会女子800米自由泳冠军", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-25/10703754.shtml"},
    {"title": "第五届全球数字贸易博览会在杭州启动", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-24/10703112.shtml"},
    {"title": "9月全国日均揽收快递5.85亿件，单日峰值超6.1亿件", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-25/10703703.shtml"},
    {"title": "中国新型电力系统建设进入加速转型期", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/cj/2026/09-23/10702245.shtml"},
    {"title": "厦金小三通迎来中秋客流高峰，半小时可跨海赴团圆", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gn/2026/09-25/10703749.shtml"},
    {"title": "中国C909医疗机赴吉尔吉斯斯坦开展医疗公益活动", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-25/10703785.shtml"},
    {"title": "2026年世界划联龙舟世界杯在湖南沅陵开赛", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/ty/2026/09-25/10703696.shtml"},
    {"title": "柬埔寨首相洪玛奈表示打击电信网络诈骗需要加强国际合作", "source": "中国新闻网", "region": "domestic",
     "url": "https://www.chinanews.com.cn/gj/2026/09-23/10702623.shtml"},
    # International 20
    {"title": "伊朗外长称伊朗提出七日内重开霍尔木兹海峡的计划", "source": "BBC", "region": "international",
     "url": "https://www.bbc.com/news/articles/cqgmrr9ekr7ko"},
    {"title": "泽连斯基称俄罗斯正攻击乌克兰数据中心以破坏民众正常生活", "source": "BBC", "region": "international",
     "url": "https://www.bbc.com/news/articles/c84gkwgk7d06o"},
    {"title": "美国最高法院允许特朗普政府使用争议性数据库核查选民公民身份", "source": "BBC", "region": "international",
     "url": "https://www.bbc.com/news/articles/ck05rrj3jeylo"},
    {"title": "曼城被认定违反英超多数财务公平规则，面临重大处罚", "source": "BBC", "region": "international",
     "url": "https://www.bbc.com/sport/football/articles/cw7v44ezry5go"},
    {"title": "OpenAI正在调查数十起智能体不当行为事件", "source": "BBC", "region": "international",
     "url": "https://www.bbc.com/news/articles/cw62jje658dlo"},
    {"title": "内塔尼亚胡在联合国大会发表强硬演讲，多国代表离场抗议", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news-analysis/2026/9/25/netanyahus-un-belligerence-wins-cheers-at-home-as-world-walks-out"},
    {"title": "波兰在乌克兰战争背景下加强防空部署", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/25/poland-boosts-air-defence-after-russian-provocations-amid-ukraine-war"},
    {"title": "伊朗表示正等待美方回应其结束战争的七天路线图", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/25/iran-says-it-awaits-us-response-on-seven-day-roadmap-to-end-war"},
    {"title": "教皇利奥十四世在法国警告人工智能可能削弱人类尊严", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/25/pope-leo-xiv-warns-ai-could-undermine-humanity-during-france-visit"},
    {"title": "刚果（金）埃博拉疫情扩散至两个新卫生区，世卫组织称形势严峻", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/25/dr-congos-ebola-outbreak-spreads-to-two-new-health-zones-who-says"},
    {"title": "特朗普与习近平结束峰会，双方未就人工智能等关键议题达成重大协议", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/us-news/2026/sep/25/donald-trump-xi-jinping-china-president-us-visit-red-carpet-treatment"},
    {"title": "教皇利奥十四世在法国访问期间警告人工智能威胁人类", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/world/2026/sep/25/pope-leo-ai-threat-to-humanity-three-day-france-visit"},
    {"title": "白宫电视转播池恢复运作，此前被禁媒体重新获得采访权限", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/media/2026/sep/25/trump-media-ban-white-house-pool"},
    {"title": "巴基斯坦总理在联合国大会抨击印度并赞扬特朗普", "source": "Deutsche Welle", "region": "international",
     "url": "https://www.dw.com/en/pakistans-sharif-rails-against-india-praises-trump-at-unga/live-79366211"},
    {"title": "美国最高法院第三次驳回密苏里州共和党绘制的国会选区地图", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/us-news/2026/sep/25/supreme-court-missouri-maps-trump"},
    {"title": "NASA救援老化太空望远镜的任务失败，航天器返回地球", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/science/2026/sep/25/nasa-telescope-rescue-mission-fails"},
    {"title": "姆巴佩进球后因膝伤离场，齐达内执教法国队首秀获胜", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/sports/2026/9/25/mbappe-goal-overshadowed-by-knee-injury-to-mar-zidane-debut-france-win"},
    {"title": "美国法院裁定各州可监管预测市场，Kalshi公司败诉", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/25/us-court-rules-against-kalshi-says-states-can-regulate-prediction-markets"},
    {"title": "巴基斯坦总理在联合国警告胡塞武装袭击麦加和麦地那将越过红线", "source": "Al Jazeera", "region": "international",
     "url": "https://www.aljazeera.com/news/2026/9/25/houthi-attack-on-mecca-medina-would-cross-red-line-pakistan-pm-tells-un"},
    {"title": "特朗普与习近平峰会关键要点：外交还是外交秀", "source": "The Guardian", "region": "international",
     "url": "https://www.theguardian.com/us-news/2026/sep/25/key-takeaways-trump-xi-summit-whitehouse-china-ai-trade"},
]

TITLE_STOPWORDS = {
    "正式", "通报", "处理", "结果", "关于", "今日", "今天", "最新",
    "消息", "报道", "新闻", "宣布", "确认", "相关", "情况", "问题",
}


def title_markers(title: str) -> list[str]:
    markers: list[str] = []
    for token in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}|\d{2,}", title):
        if token in TITLE_STOPWORDS:
            continue
        if len(token) <= 4:
            markers.append(token)
            continue
        for i in range(len(token) - 1):
            seg = token[i : i + 2]
            if seg not in TITLE_STOPWORDS:
                markers.append(seg)
    # dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for m in markers:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def content_matches_title(content: str, title: str) -> bool:
    markers = title_markers(title)
    if not markers:
        return True
    lowered = content.casefold()
    hits = sum(1 for m in markers if m.casefold() in lowered)
    return hits >= min(2, len(markers))


def fetch_raw(url: str) -> str | None:
    script = Path(__file__).resolve().parent / "fetch_article.py"
    proc = subprocess.run(
        [sys.executable, str(script), url],
        capture_output=True,
        text=True,
        timeout=45,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def translate_to_chinese(text: str) -> str:
    """Lightweight rule-based placeholder; real translation applied in post-process."""
    return text


def main() -> int:
    run_date = datetime.now(TZ).date().isoformat()
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / f"daily_news_raw_{run_date}.json"
    final_path = out_dir / f"daily_news_{run_date}.json"

    results: list[dict] = []
    for idx, row in enumerate(CANDIDATES, start=1):
        title = row["title"]
        url = row["url"]
        region = row["region"]
        print(f"[{idx}/50] {title[:36]}...", file=sys.stderr)
        raw = fetch_raw(url)
        content = ""
        if raw:
            if region == "domestic":
                content = raw if content_matches_title(raw, title) else ""
            else:
                # keep English for separate translation pass
                content = raw if len(raw) >= 80 else ""
        results.append(
            {
                "rank_no": idx,
                "title": title,
                "source": row["source"],
                "region": region,
                "url": url,
                "content": content,
                "needs_translation": region == "international" and bool(content),
            }
        )

    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    filled = sum(1 for x in results if x["content"])
    print(f"raw saved: {raw_path} ({filled}/50 fetched)", file=sys.stderr)

    # Final file without helper field; translation to be applied externally if needed
    final = []
    for row in results:
        item = {k: v for k, v in row.items() if k != "needs_translation"}
        final.append(item)
    final_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"final saved: {final_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
