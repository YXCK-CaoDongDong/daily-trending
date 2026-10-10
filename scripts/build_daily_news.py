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
    {"rank_no": 1, "title": "习近平结束出席2026年上海合作组织峰会和对吉尔吉斯斯坦、埃及的国事访问回到北京", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689279.shtml"},
    {"rank_no": 2, "title": "习言道｜在大埃及博物馆，习近平谈到“文明力量”", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689807.shtml"},
    {"rank_no": 3, "title": "文明的双向奔赴，习近平参观大埃及博物馆", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689887.shtml"},
    {"rank_no": 4, "title": "“千里同好”，习近平历史性访问推动中埃关系再深化", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689692.shtml"},
    {"rank_no": 5, "title": "习近平同埃及总统塞西举行会谈", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10689004.shtml"},
    {"rank_no": 6, "title": "谈及中东局势，习近平提出四点倡议", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-02/10689116.shtml"},
    {"rank_no": 7, "title": "西藏吉隆泥石流灾害已致21人遇难541人失联", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-02/10689110.shtml"},
    {"rank_no": 8, "title": "西藏吉隆镇各族民众守望相助共渡泥石流灾害难关", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-04/10689987.shtml"},
    {"rank_no": 9, "title": "西藏吉隆口岸核心区域临时供电线路已抢通", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689819.shtml"},
    {"rank_no": 10, "title": "世界最长在建跨海高速铁路桥七座主塔全部封顶", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-03/10689637.shtml"},
    {"rank_no": 11, "title": "《促进中小企业发展“十五五”规划》发布，官方解读要点", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-03/10689663.shtml"},
    {"rank_no": 12, "title": "商务部回应美利用G20炒作所谓“经济失衡”论调", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-03/10689567.shtml"},
    {"rank_no": 13, "title": "商务部：敦促法方立即停止反超快时尚法实施", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-03/10689562.shtml"},
    {"rank_no": 14, "title": "外交部：希望韩国政府切实践行一个中国原则", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689933.shtml"},
    {"rank_no": 15, "title": "中方：坚决遏制日本“新型军国主义”披着“国家正常化”外衣为害世界", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689607.shtml"},
    {"rank_no": 16, "title": "越南声称对西沙群岛拥有主权，中国外交部驳斥", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689553.shtml"},
    {"rank_no": 17, "title": "三部门调拨5000件中央救灾物资，支持福建做好救灾救助工作", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689726.shtml"},
    {"rank_no": 18, "title": "水利部针对江西启动洪水防御Ⅳ级应急响应", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-03/10689519.shtml"},
    {"rank_no": 19, "title": "台风“沙德尔”进入广东，全省最大降雨量达315.1毫米", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-03/10689524.shtml"},
    {"rank_no": 20, "title": "四川绵阳市北川县发生4.8级地震，震源深度10千米", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-03/10689806.shtml"},
    {"rank_no": 21, "title": "海口一正在装修的餐厅发生火灾，致6死3伤", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-03/10689706.shtml"},
    {"rank_no": 22, "title": "直击福州闽侯内涝抢险：橡皮艇穿梭泽国，昼夜转移被困民众", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/sh/2026/09-03/10689869.shtml"},
    {"rank_no": 23, "title": "“香港大药房”横行，下架35家店铺只是开始", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-03/10689936.shtml"},
    {"rank_no": 24, "title": "央行：2026年2季度末金融业机构总资产562.2万亿元", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-03/10689612.shtml"},
    {"rank_no": 25, "title": "中国地震局解读地震预警：如何实现“稳准快”", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689790.shtml"},
    {"rank_no": 26, "title": "光伏装机首超煤电，中国能源转型进入下半场", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cj/2026/09-02/10688962.shtml"},
    {"rank_no": 27, "title": "平陆运河举行船舶通航全要素综合演练", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689446.shtml"},
    {"rank_no": 28, "title": "全国学生总体近视率近五年连续下降", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689513.shtml"},
    {"rank_no": 29, "title": "按病种付费3.0版分组方案发布，这些变化与你有关", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/jk/2026/09-03/10689518.shtml"},
    {"rank_no": 30, "title": "AI短剧“撞脸”幕后：盗脸、买卖脸成完整产业链", "source": "中国新闻网", "region": "domestic", "url": "https://www.chinanews.com.cn/cul/2026/09-03/10689561.shtml"},
    # international 31-50
    {"rank_no": 31, "title": "特朗普威胁随时准备对伊朗再次发动打击", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689171.shtml"},
    {"rank_no": 32, "title": "特朗普称对伊朗的新一轮打击不会持续太久", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689170.shtml"},
    {"rank_no": 33, "title": "特朗普警告伊朗若对美军袭击进行报复将遭更猛烈打击", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688366.shtml"},
    {"rank_no": 34, "title": "美军再袭伊朗，伊朗称击落一架美军MQ-9无人机", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688362.shtml"},
    {"rank_no": 35, "title": "一沙特船只在霍尔木兹海峡发生安全事故，致两名船员遇难", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10689011.shtml"},
    {"rank_no": 36, "title": "秘鲁外交部宣布与伊朗断绝外交关系", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688429.shtml"},
    {"rank_no": 37, "title": "德国指认俄罗斯涉莱比锡机场袭击并宣布反制措施", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688374.shtml"},
    {"rank_no": 38, "title": "英国政府推出重塑英国新政框架", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689166.shtml"},
    {"rank_no": 39, "title": "英国首相伯纳姆在议会发表声明，阐述施政方向", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688373.shtml"},
    {"rank_no": 40, "title": "刚果（金）埃博拉疫情死亡病例超3000例", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689188.shtml"},
    {"rank_no": 41, "title": "世界气象组织：未来数月将形成超强厄尔尼诺事件", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689754.shtml"},
    {"rank_no": 42, "title": "普京：乌克兰问题仍存在解决机会", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689773.shtml"},
    {"rank_no": 43, "title": "马杜罗律师团队要求美国撤销诉讼", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689633.shtml"},
    {"rank_no": 44, "title": "阿根廷外交部长：必须掌握一切可用手段实现对马岛主权", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689514.shtml"},
    {"rank_no": 45, "title": "意大利向印尼提供一艘航母，换取40亿美元军火订单", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688832.shtml"},
    {"rank_no": 46, "title": "中国政府第三批紧急援助物资运抵尼泊尔", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gn/2026/09-03/10689688.shtml"},
    {"rank_no": 47, "title": "美国“林肯”号航母抵达泰国休整，海上航行286天后舰体布满锈迹", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689206.shtml"},
    {"rank_no": 48, "title": "美国发生大规模枪击致多人死伤，枪支犯罪引发担忧", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-03/10689258.shtml"},
    {"rank_no": 49, "title": "印尼首位女性央行行长宣誓就职", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10689058.shtml"},
    {"rank_no": 50, "title": "巴基斯坦安全部队在俾路支省展开反恐行动，击毙21名恐怖分子", "source": "中国新闻网", "region": "international", "url": "https://www.chinanews.com.cn/gj/2026/09-02/10688688.shtml"},
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
    # dedupe preserving order
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
