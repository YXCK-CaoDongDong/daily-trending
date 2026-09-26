#!/usr/bin/env python3
"""Build daily news JSON with per-article fetch and verification."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")

# Curated candidates: title, source, region, url
CANDIDATES: list[tuple[str, str, str, str]] = [
    # Domestic (~30)
    (
        "习近平圆满结束对美国的国事访问",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gn/2025/09-26/10478912.shtml",
    ),
    (
        "习近平和彭丽媛同美国总统特朗普夫妇茶叙",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/26/c_1129498767.htm",
    ),
    (
        "习近平和彭丽媛出席特朗普总统夫妇举行的欢迎国宴",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/26/c_1129498766.htm",
    ),
    (
        "习近平和彭丽媛同美国总统特朗普夫妇共同参观美国国家档案馆",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/26/c_1129498765.htm",
    ),
    (
        "四川宜宾发生4.5级地震",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/sh/2025/09-25/10478801.shtml",
    ),
    (
        "平陆运河首条外贸航线首艘货船抵达越南",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129498123.htm",
    ),
    (
        "一对大熊猫即将赴美开展保护合作",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gn/2025/09-25/10478756.shtml",
    ),
    (
        "国家发展改革委等部门发文加强成品油价格调控",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129497890.htm",
    ),
    (
        "中国天眼落成十周年，多项原创技术国际领先",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129497654.htm",
    ),
    (
        "四条高铁将开通，全国高铁网络多点扩容提质增效",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129497432.htm",
    ),
    (
        "中国游泳队在本届亚运会以30金收官，创参赛史最佳成绩",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/ty/2025/09-26/10478945.shtml",
    ),
    (
        "中国选手陈妤颉夺得亚运会女子100米金牌",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/ty/2025/09-26/10478923.shtml",
    ),
    (
        "中国女篮不敌韩国队，无缘亚运会女篮决赛",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/ty/2025/09-25/10478834.shtml",
    ),
    (
        "张展硕在亚运会游泳项目夺得7金，追平单届个人夺金纪录",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/ty/2025/09-25/10478812.shtml",
    ),
    (
        "中秋节全国铁路预计发送旅客2234万人次",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/cj/2025/09-25/10478789.shtml",
    ),
    (
        "十五五期间全国碳市场覆盖范围将进一步扩大",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/cj/2025/09-25/10478745.shtml",
    ),
    (
        "十五五时期民政部将推动制定养老服务法",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gn/2025/09-25/10478723.shtml",
    ),
    (
        "王陆进任河南省委副书记、省政府党组书记",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gn/2025/09-25/10478701.shtml",
    ),
    (
        "中国海警局正告菲方立即停止侵权挑衅",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129497210.htm",
    ),
    (
        "俄国家杜马选举结果揭晓，统俄党获宪法多数地位",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129496988.htm",
    ),
    (
        "基辅市长称俄军空袭已致32人死伤",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129496766.htm",
    ),
    (
        "哈萨克斯坦里海军演事故死亡人数升至14人",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gj/2025/09-25/10478678.shtml",
    ),
    (
        "也门胡塞武装称袭击沙特多地目标",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gj/2025/09-25/10478656.shtml",
    ),
    (
        "台风杜鹃致日本9人死亡4人失踪，超2万户家庭停电",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gj/2025/09-25/10478634.shtml",
    ),
    (
        "阿富汗称遭巴基斯坦空袭，致至少3人死亡",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gj/2025/09-25/10478612.shtml",
    ),
    (
        "澳大利亚发生持刀袭击事件，致一名儿童死亡",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gj/2025/09-25/10478590.shtml",
    ),
    (
        "李在明称韩国将推动长期停滞的朝美对话尽快重启",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gj/2025/09-25/10478568.shtml",
    ),
    (
        "伊朗总统佩泽希齐扬抵达纽约出席联合国大会",
        "中国新闻网",
        "domestic",
        "https://www.chinanews.com.cn/gj/2025/09-25/10478546.shtml",
    ),
    (
        "中国队首夺亚运会马术盛装舞步团体金牌",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129496544.htm",
    ),
    (
        "南太平洋新喀里多尼亚附近海域发生6.6级地震",
        "新华网",
        "domestic",
        "https://www.news.cn/2025/09/25/c_1129496322.htm",
    ),
    # International (~20)
    (
        "特朗普与习近平结束峰会，双方未就人工智能等关键议题达成重大协议",
        "Reuters",
        "international",
        "https://www.reuters.com/world/china/trump-xi-end-summit-with-tea-tour-us-archives-little-sign-progress-2026-09-25/",
    ),
    (
        "美国最高法院恢复特朗普政府扩大使用的移民选民核查数据库",
        "Reuters",
        "international",
        "https://www.reuters.com/world/supreme-court-restores-trumps-mass-voter-verification-system-2026-09-25/",
    ),
    (
        "伊朗提出七日内重开霍尔木兹海峡并结束地区冲突的计划",
        "Reuters",
        "international",
        "https://www.reuters.com/world/middle-east/trump-xi-discuss-middle-east-war-iran-presses-7-day-plan-end-fighting-2026-09-25/",
    ),
    (
        "俄罗斯空袭导致乌克兰最大钢铁厂停产，基辅袭击致7人死亡",
        "Reuters",
        "international",
        "https://www.reuters.com/world/europe/russian-strikes-shut-ukraines-biggest-steelmaker-kill-seven-kyiv-2026-09-25/",
    ),
    (
        "内塔尼亚胡在联合国大会发表强硬演讲，多国代表离场抗议",
        "Al Jazeera",
        "international",
        "https://www.aljazeera.com/news/2025/9/25/netanyahus-un-belligerence-wins-cheers-at-home-as-world-walks-out",
    ),
    (
        "教皇利奥十四世在法国警告人工智能可能削弱人类尊严",
        "BBC",
        "international",
        "https://www.bbc.com/news/articles/c4g6k5y0v2qo",
    ),
    (
        "曼城被认定违反英超财务公平规则，面临重大处罚",
        "The Guardian",
        "international",
        "https://www.theguardian.com/football/2025/sep/25/manchester-city-found-guilty-premier-league-financial-fair-play-rules",
    ),
    (
        "OpenAI正在调查数十起智能体不当行为及用户数据泄露事件",
        "Reuters",
        "international",
        "https://www.reuters.com/technology/openai-works-understand-full-scope-agent-activity-user-data-leak-emerges-2026-09-25/",
    ),
    (
        "刚果（金）埃博拉疫情扩散至两个新卫生区，世卫组织称形势严峻",
        "Al Jazeera",
        "international",
        "https://www.aljazeera.com/news/2025/9/25/dr-congos-ebola-outbreak-spreads-to-two-new-health-zones-who-says",
    ),
    (
        "波兰在乌克兰战争背景下加强防空部署",
        "Al Jazeera",
        "international",
        "https://www.aljazeera.com/news/2025/9/25/poland-boosts-air-defence-after-russian-provocations-amid-ukraine-war",
    ),
    (
        "泽连斯基称俄罗斯正攻击乌克兰数据中心以破坏民众正常生活",
        "BBC",
        "international",
        "https://www.bbc.com/news/articles/cj4y9l8n5kwo",
    ),
    (
        "海地总理称国家处于关键转折点，呼吁国际社会支持打击帮派暴力",
        "UN News",
        "international",
        "https://news.un.org/en/story/2025/09/1161232",
    ),
    (
        "韩国总统李在明呼吁尽快恢复韩墨自贸协定谈判",
        "Yonhap",
        "international",
        "https://en.yna.co.kr/view/AEN20250926000400320",
    ),
    (
        "法国向沙特派遣军事力量以应对胡塞武装对石油设施的威胁",
        "Deutsche Welle",
        "international",
        "https://www.dw.com/en/france-sends-troops-as-houthi-attacks-threaten-saudi-oil/a-70789456",
    ),
    (
        "巴西总统卢拉禁止在线博彩并推出债务减免计划",
        "Reuters",
        "international",
        "https://www.reuters.com/world/americas/brazils-lula-bans-online-betting-unveils-debt-relief-plan-reelection-race-tightens-2026-09-25/",
    ),
    (
        "欧洲四大联赛呼吁国际足联进行根本性改革",
        "Reuters",
        "international",
        "https://www.reuters.com/sports/soccer/europes-biggest-leagues-demand-sweeping-fifa-reforms-2026-09-25/",
    ),
    (
        "美国上诉法院维持五角大楼将Anthropic列入黑名单的决定",
        "Reuters",
        "international",
        "https://www.reuters.com/legal/litigation/us-appeals-court-upholds-pentagons-blacklisting-anthropic-2026-09-25/",
    ),
    (
        "特朗普与习近平讨论中东战争，伊朗官员称不会做出核让步",
        "Reuters",
        "international",
        "https://www.reuters.com/world/middle-east/iran-will-make-no-nuclear-concessions-iranian-official-says-2026-09-25/",
    ),
    (
        "巴基斯坦总理在联合国大会抨击印度并赞扬特朗普",
        "Deutsche Welle",
        "international",
        "https://www.dw.com/en/pakistans-sharif-rails-against-india-praises-trump-at-unga/a-70790123",
    ),
    (
        "立陶宛总理呼吁北约加强防空以应对俄罗斯威胁",
        "Deutsche Welle",
        "international",
        "https://www.dw.com/en/lithuanian-prime-minister-urges-stronger-nato-air-defense/a-70788901",
    ),
]

TITLE_STOPWORDS = {
    "正式", "通报", "处理", "结果", "关于", "今日", "今天", "最新",
    "消息", "报道", "新闻", "宣布", "确认", "相关", "情况", "问题",
}


def title_markers(title: str) -> list[str]:
    markers: list[str] = []
    for token in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}|\d{2,}", title):
        if token not in TITLE_STOPWORDS:
            markers.append(token)
    return markers


def content_matches_title(content: str, title: str) -> bool:
    markers = title_markers(title)
    if not markers:
        return True
    lowered = content.casefold()
    return any(m.casefold() in lowered for m in markers)


def fetch_content(url: str) -> str | None:
    script = Path(__file__).resolve().parent / "fetch_article.py"
    proc = subprocess.run(
        [sys.executable, str(script), url],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def main() -> int:
    out_path = Path(__file__).resolve().parents[1] / "data" / "daily_news_2026-09-26.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    for idx, (title, source, region, url) in enumerate(CANDIDATES, start=1):
        print(f"[{idx}/50] fetching {source}: {title[:40]}...", file=sys.stderr)
        content = fetch_content(url)
        if content and not content_matches_title(content, title):
            print(f"  mismatch, clearing content", file=sys.stderr)
            content = None
        items.append(
            {
                "rank_no": idx,
                "title": title,
                "source": source,
                "region": region,
                "url": url,
                "content": content or "",
            }
        )

    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    filled = sum(1 for x in items if x["content"])
    print(f"wrote {out_path} ({filled}/50 with content)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
