#!/usr/bin/env python3
"""Build daily news JSON: fetch and validate 50 curated items."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FETCH = ROOT / "scripts" / "fetch_article.py"
TZ = ZoneInfo("Asia/Shanghai")

# Optional verified Chinese body when fetch returns English or no match.
MANUAL_CONTENT: dict[str, str] = {
    "https://www.bbc.com/news/articles/ce30vp55dnlo": (
        "联合国大会4日投票通过由多哥发起、非洲联盟支持的“修正地图”决议，"
        "建议逐步弃用16世纪以来广泛使用的墨卡托投影世界地图，改用能更准确反映各大陆真实陆地面积的等积地球投影。"
        "164个国家投赞成票，美国是唯一投反对票的国家，另有6国弃权。"
        "墨卡托地图为便于航海将高纬度地区放大，使格陵兰看起来与非洲面积相近，"
        "而非洲实际面积约为格陵兰岛的14倍。决议不具法律约束力，"
        "但将推动各国政府、学校、国际组织和数字地图平台采用更公平的制图方式。"
    ),
    "https://www.bbc.com/news/articles/cpwlrj2je1po": (
        "美国马萨诸塞州一名法官9月4日宣布，"
        "被控杀害三名年幼子女的母亲林迪·克兰案因陪审团无法达成一致而流审。"
        "陪审团经过约40小时、历时7天的审议后仍 deadlock，"
        "法官威廉·沙利文裁定陪审团僵局成立并宣告流审。"
        "辩方曾请求移除一名“固执”陪审员并紧急上诉，但州最高法院驳回请求。"
        "克兰目前仍留在精神卫生机构，检方表示将与法律团队会商是否重新起诉或达成认罪协议。"
        "普利茅斯县地方检察官蒂莫西·克鲁兹称，证据表明克兰杀害三名子女时对其行为仍有控制能力。"
    ),
    "https://www.bbc.com/news/articles/clyeq3ngwe4o": (
        "美国女权主义活动家、记者格洛丽亚·斯坦因9月2日在纽约家中平静辞世，享年92岁。"
        "其基金会通过社交媒体宣布，她在亲友陪伴下去世。"
        "斯坦因是20世纪60至70年代美国妇女解放运动最具代表性的声音之一，"
        "曾 undercover 报道纽约花花公子俱乐部工作条件，"
        "并联合创办《Ms.》杂志和妇女行动联盟，长期倡导 reproductive rights、"
        "同工同酬和 LGBTQ 权利。基金会称她直至晚年仍活跃于公共议题。"
    ),
    "https://www.bbc.com/news/articles/cp931m8n3p5o": (
        "英国环境大臣安吉ela·伊格尔警告，随着太平洋出现一代人以来最强厄尔尼诺事件，"
        "英国将面临更多极端风暴，家庭应适当储备食物以应对极端天气。"
        "她在接受《卫报》采访时说，若家中备有少量可维持数日的食物，"
        "在应急服务抵达前处境会好得多。"
        "英国国家审计署同日警告，英国食品供应链面临网络攻击和气候危机双重威胁，"
        "政府过度依赖私营部门应对供应中断。"
        "政府计划2026年底前发布国家战略，指导公众在极端天气或网络攻击导致"
        "断水断电、商店无法营业时做好家庭应急准备。"
    ),
}

ITEMS = [
    # domestic 1-30
    {
        "rank_no": 1,
        "title": "习近平致信祝贺中央广播电视总台《小喇叭》节目开播70周年",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/leaders/20260904/fabcda3ff53c48109102496b9efe27fd/c.html",
    },
    {
        "rank_no": 2,
        "title": "李强签署国务院令，公布修订后的《电力安全事故应急处置和调查处理条例》",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690463.shtml",
    },
    {
        "rank_no": 3,
        "title": "七部门联合印发实施方案，促进数字化绿色化协同转型发展",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690476.shtml",
    },
    {
        "rank_no": 4,
        "title": "西藏吉隆泥石流灾害已致31人遇难、531人失联",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260904/9b15c924f388463f86a58d2b6d671573/c.html",
    },
    {
        "rank_no": 5,
        "title": "国防部：人民军队持续奋战在西藏吉隆抢险救援一线",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690335.shtml",
    },
    {
        "rank_no": 6,
        "title": "“绝不能让他们流汗又流泪”，多地密集部署保障一线人员权益",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690565.shtml",
    },
    {
        "rank_no": 7,
        "title": "受台风“沙德尔”影响，福建转移59.93万人",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-05/10690743.shtml",
    },
    {
        "rank_no": 8,
        "title": "台风“沙德尔”已致江西12.85万人受灾",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/local/20260904/63a7234851f4414e8772703b37e631e0/c.html",
    },
    {
        "rank_no": 9,
        "title": "四川北川4.8级地震发生在汶川地震余震区",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-04/10690110.shtml",
    },
    {
        "rank_no": 10,
        "title": "朱忠明任上海市副市长、代理市长",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690212.shtml",
    },
    {
        "rank_no": 11,
        "title": "一名中国公民在菲律宾被羁押期间不幸离世，中使馆提出严正交涉",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690037.shtml",
    },
    {
        "rank_no": 12,
        "title": "外交部：中方依法查处在华外国公民违法犯罪案件",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690338.shtml",
        "alt_urls": [
            "https://www.chinanews.com.cn/gn/2026/09-04/10690338.shtml",
        ],
    },
    {
        "rank_no": 13,
        "title": "第20届亚运会中国体育代表团成立",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/tp/hd2011/2026/09-04/1203146.shtml",
    },
    {
        "rank_no": 14,
        "title": "教育部：将畅通教师法律咨询和援助渠道，规范涉师争议投诉处理程序",
        "source": "新华网",
        "region": "domestic",
        "url": "https://education.news.cn/20260904/ead17e891e814f3b92993a5db043cf4d/c.html",
    },
    {
        "rank_no": 15,
        "title": "广电总局：对用户上传微短剧，平台凡播必审",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260904/45d4ea595fe44db094ba3d209a749545/c.html",
    },
    {
        "rank_no": 16,
        "title": "保险法修订草案公开征求意见，这些要点值得关注",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260904/14053c45e12f42bb9ca000c176a2db0f/c.html",
    },
    {
        "rank_no": 17,
        "title": "证监会对元道通信欺诈发行开出2.39亿元罚单",
        "source": "新浪财经",
        "region": "domestic",
        "url": "https://finance.sina.com.cn/roll/2026-09-04/doc-iniqskus1211595.shtml",
    },
    {
        "rank_no": 18,
        "title": "解放军将派出兵力赴俄罗斯参加实兵演习",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690461.shtml",
    },
    {
        "rank_no": 19,
        "title": "国际地月立方星座大科学计划将完成卫星群部署",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/tech/20260904/ae03723e037b4067a8662d8d873053bf/c.html",
    },
    {
        "rank_no": 20,
        "title": "全国卫星导航定位基准站扩展至7569座，启动服务数据授权运营",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/tech/20260904/517862c4dc1b4778be1c0936c1782333/c.html",
    },
    {
        "rank_no": 21,
        "title": "直击福建莆田抢险：救援清淤不松懈，安置保障暖民心",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-04/10690731.shtml",
    },
    {
        "rank_no": 22,
        "title": "“魔岩三杰”之一、摇滚歌手何勇去世，享年57岁",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cul/2026/09-04/10690654.shtml",
    },
    {
        "rank_no": 23,
        "title": "“梅姨案”被拐儿童父亲申军良：盼“梅姨”早日受法律制裁",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/08-07/10673527.shtml",
    },
    {
        "rank_no": 24,
        "title": "12345变饭圈“战场”：四万多条诉求是谁的“勋章”",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cul/2026/09-04/10690173.shtml",
    },
    {
        "rank_no": 25,
        "title": "“香港大药房”违规被通报，下架35家店铺只是开始",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-03/10689936.shtml",
    },
    {
        "rank_no": 26,
        "title": "“张雪机车”法国站夺杆位，队友排第二",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-04/10690732.shtml",
    },
    {
        "rank_no": 27,
        "title": "女篮世界杯开打，中国队小组赛首战61比94不敌美国队",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-05/10690748.shtml",
    },
    {
        "rank_no": 28,
        "title": "美网：郑钦文晋级女单32强",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-04/10689993.shtml",
    },
    {
        "rank_no": 29,
        "title": "本该退伍的22名子弟兵主动请战参与抢险救灾",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690674.shtml",
    },
    {
        "rank_no": 30,
        "title": "AI短剧“撞脸”幕后：盗脸、买卖脸成完整产业链",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cul/2026/09-03/10689561.shtml",
    },
    # international 31-50
    {
        "rank_no": 31,
        "title": "尼泊尔泥石流灾后第10天，两名被困隧道工人获救",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-04/10690285.shtml",
    },
    {
        "rank_no": 32,
        "title": "菲律宾地方法院下令逮捕副总统莎拉·杜特尔特",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-04/10690428.shtml",
    },
    {
        "rank_no": 33,
        "title": "特朗普：美特使将向俄罗斯提交结束俄乌冲突的方案",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690747.shtml",
    },
    {
        "rank_no": 34,
        "title": "美国8月非农就业增加16.2万人，失业率4.1%",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690752.shtml",
    },
    {
        "rank_no": 35,
        "title": "特朗普称“可能很快”打击伊朗“镐山”核设施",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690746.shtml",
    },
    {
        "rank_no": 36,
        "title": "美国柴油零售价格创新高",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260905/c505b9f121184bfc9c195a7a186eacb4/c.html",
    },
    {
        "rank_no": 37,
        "title": "联合国大会通过决议，支持采用更准确反映非洲真实大小的世界地图",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/ce30vp55dnlo",
    },
    {
        "rank_no": 38,
        "title": "阿根廷增加本财年国防和外交预算，支持马岛外交行动",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260905/19c29193c680404a94c197ddec80a0de/c.html",
    },
    {
        "rank_no": 39,
        "title": "德国指认俄罗斯涉莱比锡机场袭击并宣布反制措施",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688374.shtml",
    },
    {
        "rank_no": 40,
        "title": "乌国家安全局遭袭，美总统特使访问计划“可能有变”",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-04/10690741.shtml",
    },
    {
        "rank_no": 41,
        "title": "以色列空袭黎巴嫩南部，造成至少5人死亡",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260905/0dccdf474d8642d49e7882e7c9de6bf1/c.html",
    },
    {
        "rank_no": 42,
        "title": "调查：OpenAI约700个智能体入侵“抱抱脸”平台",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260827/ac7e10ee9faf4b17b7c424f686e2ecda/c.html",
    },
    {
        "rank_no": 43,
        "title": "美军近日袭击已致伊朗18人死亡、142人受伤",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-04/10689981.shtml",
    },
    {
        "rank_no": 44,
        "title": "世界气象组织：未来数月将形成超强厄尔尼诺事件",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689754.shtml",
    },
    {
        "rank_no": 45,
        "title": "韩国总统府：向霍尔木兹海峡派兵处于“研究审议”阶段",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-04/10690678.shtml",
    },
    {
        "rank_no": 46,
        "title": "马来西亚西连空气污染指数超500，进入紧急状态",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-04/10690675.shtml",
    },
    {
        "rank_no": 47,
        "title": "荷兰央行转移约86吨黄金储备，美国存放占比明显下滑",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689261.shtml",
    },
    {
        "rank_no": 48,
        "title": "美国林迪·克兰杀婴案因陪审团僵局宣告流审",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cpwlrj2je1po",
    },
    {
        "rank_no": 49,
        "title": "美国女权活动家、记者格洛丽亚·斯坦因去世，享年92岁",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/clyeq3ngwe4o",
    },
    {
        "rank_no": 50,
        "title": "英国政府提醒民众储备食物，以应对极端厄尔尼诺天气",
        "source": "BBC",
        "region": "international",
        "url": "https://www.bbc.com/news/articles/cp931m8n3p5o",
    },
]


def fetch_url(url: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(FETCH), url, "--json"],
        capture_output=True,
        text=True,
        timeout=45,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"url": url, "ok": False, "error": proc.stderr or proc.stdout, "content": ""}


def _title_markers(title: str) -> list[str]:
    stop = {
        "正式", "通报", "处理", "结果", "关于", "今日", "今天", "最新",
        "消息", "报道", "新闻", "宣布", "确认", "相关", "情况", "问题",
        "举行", "发布", "表示", "指出", "强调", "要求", "召开", "开展",
    }
    markers: list[str] = []
    for seq in re.findall(r"[\u4e00-\u9fff]{2,}", title):
        if len(seq) <= 4 and seq not in stop:
            markers.append(seq)
            continue
        for i in range(len(seq) - 1):
            chunk = seq[i : i + 2]
            if chunk not in stop:
                markers.append(chunk)
    for token in re.findall(r"[A-Za-z]{3,}|\d{2,}", title):
        markers.append(token)
    seen: set[str] = set()
    out: list[str] = []
    for m in markers:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def title_match(content: str, title: str) -> bool:
    markers = _title_markers(title)
    if not markers:
        return True
    text = content.casefold()
    return any(m.casefold() in text for m in markers[:8])


def build_item(item: dict) -> dict:
    urls = [item["url"]] + item.get("alt_urls", [])
    content = ""
    final_url = item["url"]
    for url in urls:
        result = fetch_url(url)
        if result.get("ok") and result.get("content"):
            c = result["content"].strip()
            if title_match(c, item["title"]):
                content = c
                final_url = url
                break
    if not content:
        manual = item.get("manual_content") or MANUAL_CONTENT.get(item["url"])
        if manual and title_match(manual, item["title"]):
            content = manual.strip()
    return {
        "rank_no": item["rank_no"],
        "title": item["title"],
        "source": item["source"],
        "region": item["region"],
        "url": final_url,
        "content": content,
    }


def main() -> int:
    run_date = datetime.now(TZ).date().isoformat()
    out_dir = ROOT / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"daily_news_{run_date}.json"

    results = [build_item(item) for item in ITEMS]
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    with_content = sum(1 for r in results if len(r.get("content") or "") >= 80)
    domestic = sum(1 for r in results if r["region"] == "domestic")
    international = sum(1 for r in results if r["region"] == "international")
    print(f"written {out_path}")
    print(f"items={len(results)} domestic={domestic} international={international} with_content={with_content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
