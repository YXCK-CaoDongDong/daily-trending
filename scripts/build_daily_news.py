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
    {"rank_no": 1, "title": "习近平圆满结束对埃及的国事访问", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689164.shtml"},
    {"rank_no": 2, "title": "习近平和彭丽媛同埃及总统塞西夫妇共同参观大埃及博物馆", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689163.shtml"},
    {"rank_no": 3, "title": "习近平同埃及总统塞西举行会谈", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10689004.shtml"},
    {"rank_no": 4, "title": "谈及中东局势，习近平提出四点倡议", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10689116.shtml"},
    {"rank_no": 5, "title": "习近平致电祝贺挪威国王哈康八世即位", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10688674.shtml"},
    {"rank_no": 6, "title": "中国人民解放军南部战区位中国黄岩岛领海领空及周边区域组织战备警巡", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10688550.shtml"},
    {"rank_no": 7, "title": "西藏吉隆泥石流灾害已致21人遇难541人失联", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-02/10689110.shtml"},
    {"rank_no": 8, "title": "中国消防救援队伍水陆空并进扩大吉隆泥石流搜寻范围", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-02/10688980.shtml"},
    {"rank_no": 9, "title": "通往西藏吉隆口岸救援通道基本打通，救援力量可陆路进入", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-02/10688589.shtml"},
    {"rank_no": 10, "title": "西藏吉隆泥石流原因查明：尼泊尔境内高山冰崩引发链式灾害", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/08-27/10685521.shtml"},
    {"rank_no": 11, "title": "外交部：中方正全力搜救西藏吉隆泥石流灾害国内外失联人员", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-31/10687241.shtml"},
    {"rank_no": 12, "title": "应急管理部调派中国安能全力抢通吉隆口岸剩余900米救援通道", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10687794.shtml"},
    {"rank_no": 13, "title": "光伏装机首超煤电，中国能源转型进入下半场", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-02/10688962.shtml"},
    {"rank_no": 14, "title": "国家能源局：我国光伏发电装机规模历史性超过煤电", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-01/10687699.shtml"},
    {"rank_no": 15, "title": "国家层面首次明确158个基层病种", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10688488.shtml"},
    {"rank_no": 16, "title": "市场监管总局批准发布大型焰火燃放强制性国家标准", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-02/10688512.shtml"},
    {"rank_no": 17, "title": "七部门联合发文推动商品消费扩容升级", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/08-31/10687318.shtml"},
    {"rank_no": 18, "title": "2026年铁路暑运结束，全国铁路累计发送旅客9.54亿人次", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-01/10687693.shtml"},
    {"rank_no": 19, "title": "2026年电影暑期档总票房124.98亿元，《功夫女足》成票房冠军", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cul/2026/09-01/10687814.shtml"},
    {"rank_no": 20, "title": "2026年基本公共卫生服务经费人均财政补助标准提高至99元", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10687833.shtml"},
    {"rank_no": 21, "title": "华为、小米、荣耀等国产品牌手机集体上调售价", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-01/10688171.shtml"},
    {"rank_no": 22, "title": "我国首次实现地月双向高速激光通信", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/08-30/10686784.shtml"},
    {"rank_no": 23, "title": "中俄蒙将举行边防合作-2026联合演练", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-01/10688164.shtml"},
    {"rank_no": 24, "title": "我国在高端遥感动态成像关键技术领域取得重要突破", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10688565.shtml"},
    {"rank_no": 25, "title": "赖清德当局称防务预算将破万亿新台币，国台办回应", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10688503.shtml"},
    {"rank_no": 26, "title": "山西省人大常委会原副主任岳普煜被开除党籍", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10689029.shtml"},
    {"rank_no": 27, "title": "中国气象局气象探测中心原主任李良序一审获刑十三年", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10688988.shtml"},
    {"rank_no": 28, "title": "国务院安委会办公室联合交通运输部、农业农村部部署加强水上运输和渔业船舶安全防范", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-02/10688427.shtml"},
    {"rank_no": 29, "title": "台风沙德尔在南海再度加强为台风，中央气象台发布台风蓝色预警", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-01/10687762.shtml"},
    {"rank_no": 30, "title": "中央网信办深入开展清朗整治AI应用乱象专项行动第二阶段工作", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10688509.shtml"},
    # international 31-50
    {"rank_no": 31, "title": "特朗普警告伊朗若对美军袭击进行报复将遭更猛烈打击", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688366.shtml"},
    {"rank_no": 32, "title": "特朗普威胁随时准备对伊朗再次发动打击", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689171.shtml"},
    {"rank_no": 33, "title": "特朗普称对伊朗的新一轮打击不会持续太久", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689170.shtml"},
    {"rank_no": 34, "title": "伊朗称将继续打击美军基地，警告与美合作国家承担后果", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688613.shtml"},
    {"rank_no": 35, "title": "美军再袭伊朗，伊朗称击落一架美军MQ-9无人机", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688362.shtml"},
    {"rank_no": 36, "title": "伊朗官员称美军袭击胡齐斯坦省已致7人死亡", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688584.shtml"},
    {"rank_no": 37, "title": "伊朗称一婚礼现场遇袭致4人死亡", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688595.shtml"},
    {"rank_no": 38, "title": "一沙特船只在霍尔木兹海峡发生安全事故，致两名船员遇难", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10689011.shtml"},
    {"rank_no": 39, "title": "意大利向印尼提供一艘航母，换取40亿美元军火订单", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688832.shtml"},
    {"rank_no": 40, "title": "秘鲁外交部宣布与伊朗断绝外交关系", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688429.shtml"},
    {"rank_no": 41, "title": "德国指认俄罗斯涉莱比锡机场袭击并宣布反制措施", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688374.shtml"},
    {"rank_no": 42, "title": "英国首相伯纳姆在议会发表声明，阐述施政方向", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688373.shtml"},
    {"rank_no": 43, "title": "英国政府推出重塑英国新政框架", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689166.shtml"},
    {"rank_no": 44, "title": "扎哈罗娃称在日部署堤丰导弹系统不可接受", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688361.shtml"},
    {"rank_no": 45, "title": "刚果（金）埃博拉疫情感染病例超过6000例", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688630.shtml"},
    {"rank_no": 46, "title": "印尼首位女性央行行长宣誓就职", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10689058.shtml"},
    {"rank_no": 47, "title": "希奇莱马宣誓就任赞比亚总统，开启第二个五年任期", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688379.shtml"},
    {"rank_no": 48, "title": "中国第二批援尼紧急援助物资运抵加德满都", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688371.shtml"},
    {"rank_no": 49, "title": "巴基斯坦安全部队在俾路支省展开反恐行动，击毙21名恐怖分子", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688688.shtml"},
    {"rank_no": 50, "title": "加拿大总理呼吁美国认真对待两国贸易谈判", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688481.shtml"},
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
    }
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
