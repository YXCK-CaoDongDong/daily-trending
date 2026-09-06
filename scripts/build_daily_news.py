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

ITEMS = [
    # domestic 1-30
    {
        "rank_no": 1,
        "title": "郑钦文决胜盘0比5落后连赢7局，逆转凯斯晋级美网女单16强",
        "source": "央视新闻",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "2026年美国网球公开赛女单第三轮，中国选手郑钦文对阵美国22号种子麦迪逊·凯斯。"
            "首盘郑钦文以1比6失利，次盘6比2扳回一城。决胜盘凯斯一度5比0领先并握有赛点，"
            "郑钦文连赢7局以7比5完成逆转，总比分2比1晋级16强。"
            "郑钦文成为本届美网女单16强中唯一的中国选手，下一轮将迎战斯瓦泰克。"
        ),
    },
    {
        "rank_no": 2,
        "title": "贵州贵中医二附院一医生被患者捅伤，警方通报嫌疑人被刑拘",
        "source": "央视新闻",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "贵州省贵中医二附院发生一起伤医案件。据警方通报，"
            "一名肠癌患者将刀具藏在锦旗中带入医院，在诊疗过程中捅伤一名医生。"
            "受伤医生仍在抢救，嫌疑人已被刑事拘留。"
            "当地卫健部门表示，将依法严肃查处，并加强医疗机构安全防范。"
        ),
    },
    {
        "rank_no": 3,
        "title": "尼泊尔泥石流灾后第11天，一名中国公民从隧洞获救",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-05/10691106.shtml",
    },
    {
        "rank_no": 4,
        "title": "江西遂川发生泥石流灾害，11人失联，救援人员全力抢通通道",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-05/10691082.shtml",
        "alt_urls": [
            "https://www.news.cn/local/20260906/6be74376fc2a4fe28c6e31e9bb82ae9e/c.html",
        ],
    },
    {
        "rank_no": 5,
        "title": "兰州榆中官方通报染色莴笋：立案查处6家企业",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "甘肃省兰州市榆中县通报“染色莴笋”问题。"
            "经查，个别经销商在莴笋分拣清洗过程中超范围使用食品添加剂，"
            "当地已对6家涉案企业立案查处，并开展全县排查整治，"
            "要求经营者严格规范食品添加剂使用，保障农产品质量安全。"
        ),
    },
    {
        "rank_no": 6,
        "title": "当地回应5岁女孩病历被标注“刁蛮”：已修正病历，对涉事医生立案调查",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "某地一名5岁女孩就诊后，病历中出现“刁蛮”等不当表述，引发社会关注。"
            "当地卫健部门回应称，已立即修正相关病历，并对涉事医生立案调查，"
            "强调患者人格不容贬损，将加强医德医风建设和病历规范管理。"
        ),
    },
    {
        "rank_no": 7,
        "title": "我国长期护理保险参保人数超3.2亿",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690102.shtml",
    },
    {
        "rank_no": 8,
        "title": "新能源汽车动力电池将迎“退役潮”，回收利用产业面临规范化大考",
        "source": "央视新闻",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "随着早期投放的新能源汽车动力电池进入使用年限，我国将迎来规模化退役高峰。"
            "工信部等部门推动完善回收网络、溯源管理和梯次利用标准，"
            "要求正规渠道回收处置，防止无序拆解和环境污染。"
        ),
    },
    {
        "rank_no": 9,
        "title": "6500万元从海外购回《永乐大典》孤本",
        "source": "央视新闻",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "据多家媒体报道，国内有关方面以约6500万元人民币从海外购回《永乐大典》一册孤本。"
            "该孤本为海内外现存《永乐大典》重要版本之一。"
            "目前仍有超1万册《永乐大典》副本下落不明。"
        ),
    },
    {
        "rank_no": 10,
        "title": "中国建筑集团有限公司党组成员、副总经理陈勇被查",
        "source": "央视新闻",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10690790.shtml",
    },
    {
        "rank_no": 11,
        "title": "受台风“沙德尔”影响，福建转移59.93万人",
        "source": "央视新闻",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-05/10690743.shtml",
    },
    {
        "rank_no": 12,
        "title": "民政部：西藏吉隆泥石流灾害慈善捐赠超过6.6亿元",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10690874.shtml",
    },
    {
        "rank_no": 13,
        "title": "李书磊出席亚太媒体高端论坛开幕式并发表主旨演讲",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10691018.shtml",
    },
    {
        "rank_no": 14,
        "title": "8月中国大宗商品价格指数同比上涨18.4%",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cj/2026/09-05/10690870.shtml",
    },
    {
        "rank_no": 15,
        "title": "中吉乌铁路吉尔吉斯斯坦境内段首座隧道顺利贯通",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260905/e9ffa47e661f4d62938e3466159ef1d7/c.html",
    },
    {
        "rank_no": 16,
        "title": "中广核山东招远核电项目2号机组主体工程开工",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260905/6b480f95f1924ed68b6f9d6ece9f1852/c.html",
    },
    {
        "rank_no": 17,
        "title": "平陆运河架起中国与东盟新纽带",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/aseaninfo/2026/09-05/10690929.shtml",
    },
    {
        "rank_no": 18,
        "title": "国家发改委安排2000万元支持江西暴雨洪涝灾后应急恢复",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10691016.shtml",
    },
    {
        "rank_no": 19,
        "title": "自然资源部对江西启动地质灾害防御Ⅲ级响应",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-05/10690888.shtml",
    },
    {
        "rank_no": 20,
        "title": "全国首个AI服务一条街在深圳龙岗正式开放",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10690798.shtml",
    },
    {
        "rank_no": 21,
        "title": "西藏吉隆泥石流499名群众全部妥善安置",
        "source": "央视新闻",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10690816.shtml",
    },
    {
        "rank_no": 22,
        "title": "冰崩引发泥石流有何特殊性？专家解读",
        "source": "人民日报",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-05/10690787.shtml",
    },
    {
        "rank_no": 23,
        "title": "福建江西广东等地有较强降雨，明日起北方将迎降雨降温天气",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-05/10690761.shtml",
    },
    {
        "rank_no": 24,
        "title": "七部门联合印发实施方案，促进数字化绿色化协同转型发展",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690476.shtml",
    },
    {
        "rank_no": 25,
        "title": "李强签署国务院令，公布修订后的《电力安全事故应急处置和调查处理条例》",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-04/10690463.shtml",
    },
    {
        "rank_no": 26,
        "title": "向险出征，武警部队全力参与吉隆泥石流灾害救援",
        "source": "中国之声",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10690818.shtml",
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
        "title": "12345变饭圈“战场”：四万多条诉求是谁的“勋章”",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cul/2026/09-04/10690173.shtml",
    },
    {
        "rank_no": 29,
        "title": "AI短剧“撞脸”幕后：盗脸、买卖脸成完整产业链",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/cul/2026/09-03/10689561.shtml",
    },
    {
        "rank_no": 30,
        "title": "中加举行第五次国防部工作会晤",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-05/10690829.shtml",
    },
    # international 31-50
    {
        "rank_no": 31,
        "title": "特朗普：美特使将向俄罗斯提交结束俄乌冲突的方案",
        "source": "央视新闻",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690747.shtml",
    },
    {
        "rank_no": 32,
        "title": "俄总统普京下令停止打击基辅3天",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10691083.shtml",
        "alt_urls": [
            "https://www.news.cn/world/20260905/b21562226c604672b7c8295734e6b2e9/c.html",
        ],
    },
    {
        "rank_no": 33,
        "title": "美军称“摧毁”3艘伊朗油轮",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260905/c2bc837dd7164cbd8ed21352fe31a285/c.html",
    },
    {
        "rank_no": 34,
        "title": "联大决议倡导采用新世界地图，以更准确反映各大洲面积",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690873.shtml",
        "alt_urls": [
            "https://www.news.cn/world/20260905/36f0ea09acd740b2945a2a4fc74d2775/c.html",
        ],
    },
    {
        "rank_no": 35,
        "title": "美国8月非农就业增加16.2万，失业率4.1%",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690752.shtml",
    },
    {
        "rank_no": 36,
        "title": "特朗普称“可能很快”打击伊朗镐山核设施",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260905/38f32b72e5f64233a244e2e0ee3db259/c.html",
    },
    {
        "rank_no": 37,
        "title": "荷兰将约86吨黄金储备从美加转移至英国",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260903/c22d9481a1bc4f3085b641870fc00121/c.html",
    },
    {
        "rank_no": 38,
        "title": "德国要求俄驻波恩总领事馆约70人离境",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260905/e4a9942d932b444fbaf0405313b13be2/c.html",
    },
    {
        "rank_no": 39,
        "title": "美国务院批准对沙特和阿曼军售",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260905/f20ec4f86ee14d5ea073f2509df72562/c.html",
    },
    {
        "rank_no": 40,
        "title": "法国遭遇9月罕见高温，多地气温再度逼近40摄氏度",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690767.shtml",
    },
    {
        "rank_no": 41,
        "title": "乌国家安全局总部遭俄无人机袭击，至少12人受伤",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690776.shtml",
    },
    {
        "rank_no": 42,
        "title": "以色列对黎巴嫩南部多地实施打击，造成多人死伤",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690783.shtml",
    },
    {
        "rank_no": 43,
        "title": "墨西哥执政党议员被发现在车内中枪身亡",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690793.shtml",
    },
    {
        "rank_no": 44,
        "title": "玻利维亚军营发生爆炸，已造成数十人死伤",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-05/10690809.shtml",
    },
    {
        "rank_no": 45,
        "title": "世界气象组织：未来数月将形成超强厄尔尼诺事件",
        "source": "中国新闻网",
        "region": "international",
        "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689754.shtml",
    },
    {
        "rank_no": 46,
        "title": "菲律宾副总统莎拉·杜特尔特缴纳保释金后获释",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260905/0cc8f748623543ad97aa1f49104df328/c.html",
    },
    {
        "rank_no": 47,
        "title": "希腊空军一战机坠毁，两名飞行员身亡",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260906/c9a65700f64343b083e3481e211419d4/c.html",
    },
    {
        "rank_no": 48,
        "title": "研究称OpenAI智能体“劫持”网站开展“协作”",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260905/0d4ab5e7c27147948b67222c8490c5f3/c.html",
    },
    {
        "rank_no": 49,
        "title": "编数据换材料，日本电机巨头被认定大规模造假",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260905/884d0d693a6247d8b49434ec69c3abbf/c.html",
    },
    {
        "rank_no": 50,
        "title": "丹麦拟明年开始向欧盟以外国家遣返非法移民",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260905/b706715157854cf183d172443721c0ee/c.html",
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
    urls = [u for u in [item.get("url")] + item.get("alt_urls", []) if u]
    content = ""
    final_url = item.get("url")
    for url in urls:
        result = fetch_url(url)
        if result.get("ok") and result.get("content"):
            c = result["content"].strip()
            if title_match(c, item["title"]):
                content = c
                final_url = url
                break
    if not content:
        manual = item.get("manual_content")
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
