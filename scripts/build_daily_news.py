#!/usr/bin/env python3
"""Build daily news JSON: fetch and validate 50 curated items."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FETCH = ROOT / "scripts" / "fetch_article.py"
TZ = ZoneInfo("Asia/Shanghai")

ITEMS = [
    {"rank_no": 1, "title": "习近平出席上海合作组织成员国元首理事会第二十六次会议并发表重要讲话", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/leaders/20260901/f68ac1bf9b0044028c2b0509454f1eef/c.html"},
    {"rank_no": 2, "title": "习近平出席“上海合作组织+”会议并发表重要讲话", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/leaders/20260901/a19fa9a116d24434a6ce30356fb00b82/c.html"},
    {"rank_no": 3, "title": "习近平抵达开罗对埃及进行国事访问", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/leaders/20260902/0e7dbd427dbd484e911173f44dc616aa/c.html"},
    {"rank_no": 4, "title": "华为、小米、荣耀等品牌手机集体上调售价，部分旗舰机型涨幅达千元", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-01/10688171.shtml"},
    {"rank_no": 5, "title": "应急管理部调派中国安能全力抢通吉隆口岸剩余900米救援通道", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10687794.shtml"},
    {"rank_no": 6, "title": "拒服兵役代价有多大，多地公布联合惩戒案例", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-17/10678987.shtml"},
    {"rank_no": 7, "title": "俄方称俄中正讨论建立公民永久免签制度，中方表示愿同俄方保持沟通", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/07-29/10668592.shtml"},
    {"rank_no": 8, "title": "中共中央宣传部等12部门联合印发通知，组织开展2026年全民国防教育月活动", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/20260901/46965e5525d04d468f8eb7b9df7c9ddc/c.html"},
    {"rank_no": 9, "title": "市场监管总局修订发布《机动车运行安全技术条件》强制性国家标准", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-31/10687209.shtml"},
    {"rank_no": 10, "title": "七部门联合发文推动商品消费扩容升级，提出到2030年培育十万亿级消费市场", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-31/10687318.shtml"},
    {"rank_no": 11, "title": "2026年电影暑期档总票房124.98亿元，《功夫女足》成票房冠军", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cul/2026/09-01/10687814.shtml"},
    {"rank_no": 12, "title": "国家能源局：我国光伏发电装机规模历史性超过煤电", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-01/10687699.shtml"},
    {"rank_no": 13, "title": "中国民营运载火箭智神星一号首飞成功", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10687795.shtml"},
    {"rank_no": 14, "title": "我国首次实现地月双向高速激光通信", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-30/10686784.shtml"},
    {"rank_no": 15, "title": "中俄蒙将举行“边防合作-2026”联合演练", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10688164.shtml"},
    {"rank_no": 16, "title": "李强会见美中贸易全国委员会董事会代表团", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/leaders/20260901/dd7e9b1e11624cb9a265fe92ca25a232/c.html"},
    {"rank_no": 17, "title": "外交部介绍全球治理倡议提出一周年取得的进展和成果", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10687909.shtml"},
    {"rank_no": 18, "title": "台风“沙德尔”复活后持续影响南方多地，中央气象台发布暴雨黄色预警", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-01/10687762.shtml"},
    {"rank_no": 19, "title": "约翰·特努斯正式接替蒂姆·库克出任苹果公司首席执行官", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/04-21/10607466.shtml"},
    {"rank_no": 20, "title": "渝万高铁铺轨工程成功接入重庆东站", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-24/10683422.shtml"},
    {"rank_no": 21, "title": "我国铜金矿勘查再获重大突破，有望在华东地区新形成大型资源基地", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-01/10687689.shtml"},
    {"rank_no": 22, "title": "2026年基本公共卫生服务经费人均财政补助标准提高至99元", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10687833.shtml"},
    {"rank_no": 23, "title": "暑运期间全国民航累计运送旅客1.51亿人次", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/20260901/0fe2eeb0acb044059c06c2fe69dd25ae/c.html"},
    {"rank_no": 24, "title": "彭丽媛出席上海合作组织峰会配偶集体活动", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10688022.shtml"},
    {"rank_no": 25, "title": "外交部：中方正全力搜救西藏吉隆泥石流灾害国内外失联人员", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-31/10687241.shtml"},
    {"rank_no": 26, "title": "西藏吉隆泥石流灾害原因查明：尼泊尔境内高位冰川崩塌引发链式灾害", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/08-27/10685521.shtml"},
    {"rank_no": 27, "title": "中国提出到2030年社会消费品零售总额达60万亿元左右", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-31/10687376.shtml"},
    {"rank_no": 28, "title": "2026年铁路暑运结束，全国铁路累计发送旅客9.54亿人次", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-01/10687693.shtml"},
    {"rank_no": 29, "title": "三项婴童用品国家标准9月1日起实施，助力儿童健康成长", "source": "新华网", "region": "domestic", "url": "https://www.news.cn/politics/20260901/22b0b48984be4bbab12161ee84dba5a8/c.html"},
    {"rank_no": 30, "title": "时政快讯：习近平出席上海合作组织成员国元首理事会第二十六次会议", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10687789.shtml"},
    {"rank_no": 31, "title": "伊朗称打击多个美军目标以回应拉腊克岛遭袭，并击落一架MQ-9无人机", "source": "新华网", "region": "international", "url": "https://www.news.cn/milpro/20260901/c7d53d718f2d4e53922402e4c92e3339/c.html"},
    {"rank_no": 32, "title": "特朗普称将对伊朗袭击美国驻约旦基地进行狠狠回击", "source": "新华网", "region": "international", "url": "https://www.news.cn/world/20260831/70215d69f48e48b6a6f243f5f4a3c294/c.html"},
    {"rank_no": 33, "title": "美伊再度交火：美军袭击伊朗导弹阵地，伊朗回击", "source": "中国新闻网", "region": "international", "url": "http://www.chinanews.com.cn/gj/2026/08-31/10686968.shtml"},
    {"rank_no": 34, "title": "约旦军方称已拦截8枚入侵该国领空的导弹", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-31/10687014.shtml"},
    {"rank_no": 35, "title": "外媒：尼泊尔泥石流灾害造成的遇难人数升至987人", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-01/10687829.shtml"},
    {"rank_no": 36, "title": "德国调查人员发现莱比锡机场事件第三架涉事无人机及军用级炸药", "source": "新华网", "region": "international", "url": "http://www.news.cn/20260826/abff405ba2ae431f92583fcf312cac41/c.html"},
    {"rank_no": 37, "title": "法国前总理爱德华·巴拉迪尔在巴黎去世，享年97岁", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-01/10687705.shtml"},
    {"rank_no": 38, "title": "挪威国王哈拉尔五世去世，其子哈康八世继位", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-28/10685840.shtml"},
    {"rank_no": 39, "title": "日本外务省2027财年预算概算要求首次突破1万亿日元", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-01/10687736.shtml"},
    {"rank_no": 40, "title": "委内瑞拉首都附近迈克蒂亚国际机场恢复商业货运航班", "source": "新华网", "region": "international", "url": "https://www.news.cn/world/20260806/79a2f308788d4f4093e47138bac946ef/c.html"},
    {"rank_no": 41, "title": "加美贸易谈判破裂，加拿大总理卡尼宣布对美征收报复性关税", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-23/10682513.shtml"},
    {"rank_no": 42, "title": "乌克兰基辅地区遭俄罗斯大规模袭击，造成17人死亡", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-05/10672390.shtml"},
    {"rank_no": 43, "title": "基辅空袭死亡人数上升，俄方称乌克兰问题和平解决前景不乐观", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-21/10681495.shtml"},
    {"rank_no": 44, "title": "英国国王接受斯塔默辞呈，安迪·伯纳姆接任英国首相", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/07-20/10663099.shtml"},
    {"rank_no": 45, "title": "美国心情不美了：美伊冲突陷入打不赢、谈不拢、退不出困局", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-31/10687304.shtml"},
    {"rank_no": 46, "title": "中国隧道救援专家抵达尼泊尔协助开展搜救工作", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-30/10686728.shtml"},
    {"rank_no": 47, "title": "德媒：莱比锡机场事件中发现第三架涉事无人机", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-26/10684282.shtml"},
    {"rank_no": 48, "title": "以色列空袭约旦河西岸杰宁市致3人死亡，以方称死者为哈马斯成员", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-29/10686338.shtml"},
    {"rank_no": 49, "title": "库什纳与内塔尼亚胡会晤，寻求推进加沙和平计划", "source": "新华网", "region": "international", "url": "https://www.news.cn/world/20260818/359b89cd48e141b798414423c714e659/c.html"},
    {"rank_no": 50, "title": "委内瑞拉证实同美国达成石油合作协议", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/08-29/10686373.shtml"},
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
    import re

    stop = {"正式", "通报", "关于", "今日", "最新", "消息", "报道", "新闻", "宣布", "确认", "相关", "情况", "问题", "多大", "代价"}
    markers: list[str] = []
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,4}|[A-Za-z]{3,}|\d{2,}", title):
        if chunk in stop:
            continue
        markers.append(chunk)
    return markers


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
