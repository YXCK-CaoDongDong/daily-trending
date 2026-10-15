#!/usr/bin/env python3
"""Build daily trending news JSON (50 items) and optionally insert."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Allow importing fetch_article from same directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_article import fetch  # noqa: E402

TZ = ZoneInfo("Asia/Shanghai")

# rank_no, title, source, region, url, optional manual_content
ITEMS: list[dict] = [
    # --- domestic 30 ---
    {
        "rank_no": 1,
        "title": "8家中央金融企业计划共增资3600亿元用于补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/6445db11e5a048eb932ae3e120061502/c.html",
    },
    {
        "rank_no": 2,
        "title": "财政部将发行3000亿元特别国债支持8家中央金融企业补充核心一级资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/d8c683a121174577abbecd8106bfa2b7/c.html",
    },
    {
        "rank_no": 3,
        "title": "中国工商银行拟向特定对象发行A股募资不超过1000亿元用于补充资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260906/7a17cb99f69d4ab6b095ec18bdbea07d/c.html",
    },
    {
        "rank_no": 4,
        "title": "中国农业银行拟向特定对象发行A股募资不超过1600亿元用于补充资本",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260906/e4c83df5a832487faa94d0313189ecf7/c.html",
    },
    {
        "rank_no": 5,
        "title": "财政部将向中国进出口银行注资300亿元",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/fortune/20260906/b9b5ae6a01bb4933a8279d74e66c2c6f/c.html",
    },
    {
        "rank_no": 6,
        "title": "西藏吉隆“8·26”泥石流灾害已致43人遇难519人失联",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/12341483ea9e456b9b7d8935873ac295/c.html",
    },
    {
        "rank_no": 7,
        "title": "救援人员在西藏吉隆核心区域开展地毯式搜寻发现遗物993件",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-06/10691499.shtml",
    },
    {
        "rank_no": 8,
        "title": "中国女篮世界杯加时74比70逆转捷克队取得首胜",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/sports/20260906/9a83cef143694ab2bc4d517eed4baa83/c.html",
    },
    {
        "rank_no": 9,
        "title": "中国选手郑钦文晋级美网女单16强",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/ty/2026/09-06/10691266.shtml",
    },
    {
        "rank_no": 10,
        "title": "贵州中医药大学第二附属医院伤医案犯罪嫌疑人胡某某被刑拘",
        "source": "央广网",
        "region": "domestic",
        "url": "https://news.cnr.cn/native/gd/kx/20260906/t20260906_527805734.shtml",
    },
    {
        "rank_no": 11,
        "title": "多地市场监管部门严查赵一鸣、好想来等量贩零食门店计量问题",
        "source": "北京日报",
        "region": "domestic",
        "url": "https://finance.sina.com.cn/stock/marketresearch/2026-09-06/doc-iniqxiqn9841812.shtml",
    },
    {
        "rank_no": 12,
        "title": "江西低保家庭女生赴港看演唱会被取消低保资格，赣州民政局称正在核查",
        "source": "中华网",
        "region": "domestic",
        "url": "https://news.china.com/socialgd/10000169/20260906/49722571.html",
    },
    {
        "rank_no": 13,
        "title": "CHINA GT上海站赛车碰撞起火，组委会致歉并将进一步调查",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34019796",
    },
    {
        "rank_no": 14,
        "title": "山东临清先锋大桥步道桥板脱落致22岁行人坠河身亡",
        "source": "澎湃新闻",
        "region": "domestic",
        "url": "https://www.thepaper.cn/newsDetail_forward_34016288",
    },
    {
        "rank_no": 15,
        "title": "江西省公安厅原党委委员万秀奇接受纪律审查和监察调查",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/gn/2026/09-06/10691532.shtml",
    },
    {
        "rank_no": 16,
        "title": "广东湛江5岁女童电子病历被医生标注“刁蛮”，涉事医生被立案调查",
        "source": "光明网",
        "region": "domestic",
        "url": "https://news.china.com/socialgd/10000169/20260906/49722169.html",
    },
    {
        "rank_no": 17,
        "title": "山西阳高县7个村庄地下水监测井采样造假，饮用水冒充地下水",
        "source": "央视财经",
        "region": "domestic",
        "url": "https://news.china.com/socialgd/10000169/20260906/49722768.html",
    },
    {
        "rank_no": 18,
        "title": "福州永泰县同安镇房屋坍塌4名失联人员经27小时营救全部脱险",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/b8c6bd335e944960939df01a68b669e7/c.html",
        "manual_content": (
            "新华社北京9月6日电 9月4日，福建省福州市永泰县同安镇一处房屋发生坍塌，"
            "造成4人失联。当地消防救援力量随即赶赴现场开展搜救。经过连续27个多小时的"
            "昼夜奋战，4名被困人员全部被成功救出，生命体征平稳。目前，有关部门正就"
            "坍塌原因开展调查，并对周边区域开展安全排查。"
        ),
    },
    {
        "rank_no": 19,
        "title": "内蒙古贺兰山综合科考发现6个新物种",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/travel/20260904/da6481c3ea7c465880975d682f7ed44c/c.html",
    },
    {
        "rank_no": 20,
        "title": "教育部回应中小学是否一定要买校服：坚持自愿购买原则",
        "source": "新京报",
        "region": "domestic",
        "url": "https://www.bjnews.com.cn/detail/1788657399129092.html",
    },
    {
        "rank_no": 21,
        "title": "胖东来要求供应商填报员工社保和工时信息作为招商初筛必填项",
        "source": "界面新闻",
        "region": "domestic",
        "url": "https://www.jiemian.com/article/15047448.html",
    },
    {
        "rank_no": 22,
        "title": "多家银行集中清淤不良，工商银行上半年核销819亿元",
        "source": "央视网",
        "region": "domestic",
        "url": "https://finance.cctv.com/2026/09/04/ARTIuz2PcpgZOtcBlvLXzKHC260904.shtml",
    },
    {
        "rank_no": 23,
        "title": "中国博主在伦敦皮卡迪利广场直播时遭外籍青年殴打致脊椎骨折",
        "source": "微博热搜",
        "region": "domestic",
        "url": None,
        "manual_content": (
            "9月4日，网名为“南归归一”的中国博主在英国伦敦皮卡迪利广场进行直播时，"
            "据其自述遭一群外籍青年辱骂、抢夺手表未遂并殴打。博主称被打后手部受伤、"
            "背部疑似骨折，已前往医院救治。博主表示已向伦敦警方报案，警方将事件登记为"
            "普通袭击案，未派警员到场，并建议其自行联系保险公司和医院。相关视频在"
            "社交媒体传播，引发网友对海外华人安全及警方处置方式的讨论。截至报道时，"
            "警方尚未公布逮捕信息，博主表示仍在跟进案件。"
        ),
    },
    {
        "rank_no": 24,
        "title": "巴布亚新几内亚动物园员工被鳄鱼咬伤1小时后不治身亡",
        "source": "新京报",
        "region": "domestic",
        "url": "https://www.bjnews.com.cn/detail/1788694985129357.html",
    },
    {
        "rank_no": 25,
        "title": "瑞金至延安高铁正式开通，长征出发地与落脚点实现高铁直达",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/politics/20260906/e96808a8004343fe8eb29fdcbd2f62e7/c.html",
    },
    {
        "rank_no": 26,
        "title": "2026年全民国防教育月活动在全国启动",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/7b5b68bda20c4ef6b0aed410d82be529/c.html",
    },
    {
        "rank_no": 27,
        "title": "江西遂川受台风“沙德尔”影响出现地质灾害，当地开展搜救",
        "source": "中国新闻网",
        "region": "domestic",
        "url": "https://www.chinanews.com.cn/sh/2026/09-06/10691290.shtml",
    },
    {
        "rank_no": 28,
        "title": "甘肃榆中6家企业在莴笋收购环节违法使用果绿添加剂被立案查处",
        "source": "经济观察网",
        "region": "domestic",
        "url": "http://www.eeo.com.cn/2026/0905/1025498.shtml",
    },
    {
        "rank_no": 29,
        "title": "北京月捐人停捐不到一个月被慈善机构电话催捐引发争议",
        "source": "网易新闻",
        "region": "domestic",
        "url": "https://www.163.com/dy/article/L63BTCI705560STT.html",
    },
    {
        "rank_no": 30,
        "title": "甘肃大部迎持续阴雨天气，最大累积降水量70至90毫米",
        "source": "新华网",
        "region": "domestic",
        "url": "https://www.news.cn/20260906/20825c3f5b7c46d9b367151f86c11fd3/c.html",
    },
    # --- international 20 (ranks 31-50) ---
    {
        "rank_no": 31,
        "title": "极右翼德国选择党在萨克森-安哈尔特州选举中以约44%得票率成为第一大党",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260907/01f22c1c10d9480d9b2e6425381070ef/c.html",
    },
    {
        "rank_no": 32,
        "title": "一架亚马逊货机在迈阿密机场冲出跑道起火，至少5人死亡",
        "source": "人民网",
        "region": "international",
        "url": "http://world.people.com.cn/n1/2026/0907/c1002-40793490.html",
    },
    {
        "rank_no": 33,
        "title": "印尼喀拉喀托之子火山喷发，雅加达主要机场暂停起降",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260906/6def9de3d71d4cd1bcca8c231ba1e41c/c.html",
    },
    {
        "rank_no": 34,
        "title": "泽连斯基称与美特使会晤“非常具有实质性”，预期战争将持续至冬季",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260907/7047a825cd114bf6b04437887868d853/c.html",
    },
    {
        "rank_no": 35,
        "title": "普京与美方特使会见超过3小时，此前俄乌达成“三日停火”",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260906/6899c01671dc4c589c9dbce3f4dbc2a0/c.html",
    },
    {
        "rank_no": 36,
        "title": "伊朗称将在霍尔木兹海峡之外设立禁区",
        "source": "人民网",
        "region": "international",
        "url": "http://world.people.com.cn/n1/2026/0907/c1002-40793498.html",
    },
    {
        "rank_no": 37,
        "title": "印度新德里萨特亚尼凯坦五层学生宿舍楼倒塌，已致至少6人死亡",
        "source": "中国报",
        "region": "international",
        "url": "https://www.chinapress.com.my/20260906/6%e5%b1%82%e5%bb%ba%e7%ad%91-%e7%aa%81%e5%80%92%e5%a1%8c-%e5%8d%b050%e5%ad%a6%e7%94%9f-%e5%9f%8b%e7%93%a6%e7%a0%be%e5%a0%86/",
        "manual_content": (
            "9月6日下午1时30分左右，印度新德里西南部萨特亚尼凯坦地区一栋五层学生"
            "宿舍楼发生倒塌。当地媒体报道，事发建筑名为“Hostel Daze”，事发时约有"
            "30至50名学生在楼内，部分学生通过手机向外求救。印度全印度医学科学"
            "研究院等机构收治多名伤者，截至后续通报，事故已造成至少6人死亡，"
            "另有十余人获救并接受治疗。德里警方已对建筑业主及相关人员立案调查，"
            "搜救与原因调查仍在进行。当地议员称，事发前地下室正在进行施工维修，"
            "或与结构失稳有关。"
        ),
    },
    {
        "rank_no": 38,
        "title": "牙买加政府将向查尔斯三世国王递交奴隶制赔偿请愿书",
        "source": "UA.NEWS",
        "region": "international",
        "url": "https://ua.news/cn/world/iamaiska-delegatsiia-peredast-koroliu-charlzu-iii-petitsiiu-pro-reparatsii-za-rabstvo",
        "manual_content": (
            "牙买加政府代表团已抵达英国伦敦，计划向查尔斯三世国王递交一份关于"
            "奴隶制赔偿的请愿书。请愿书请求国王将三个法律问题提交枢密院司法"
            "委员会审议：将非洲人强制运往牙买加是否合法、是否构成反人类罪，"
            "以及英国是否负有就奴隶制及其后果向牙买加提供赔偿的法律义务。"
            "牙买加文化部长奥利维亚·格兰奇表示，奴隶制遗留问题仍在影响该国"
            "经济、教育、医疗及应对气候危机的能力。1833年英国废除奴隶制时"
            "向奴隶主支付补偿，相关贷款直至2015年才还清。英国政府此前多次"
            "表示不会就奴隶制支付赔偿。请愿书本身并非直接索赔，而是寻求通过"
            "法律途径明确英国责任，判决仍可上诉。"
        ),
    },
    {
        "rank_no": 39,
        "title": "“欧佩克+”主要产油国决定保持10月原油产量不变",
        "source": "新华网",
        "region": "international",
        "url": "http://intl.ce.cn/sjjj/qy/202609/t20260906_3196812.shtml",
    },
    {
        "rank_no": 40,
        "title": "墨西哥中部烟花爆炸致9死24伤",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260906/7c5f0f9f267549f8aadd6bd4eb197f6d/c.html",
    },
    {
        "rank_no": 41,
        "title": "以色列空袭加沙致至少7人受伤",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260906/cdfaaf28dc034aea9e2c3f7b938f4555/c.html",
    },
    {
        "rank_no": 42,
        "title": "韩国出口额创历史新高",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/fortune/20260906/85382aea963c4fac9c7d8f73ecaf8ac8/c.html",
    },
    {
        "rank_no": 43,
        "title": "日本岐阜县一甜品店发生火灾致2死3伤",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260906/7a61d973ea88413cbca8baab33674e4e/c.html",
    },
    {
        "rank_no": 44,
        "title": "驻日美军士兵被指当街殴打多名冲绳县居民",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/world/20260906/38dd3f5e98dc4928b0eca1c7a5aa057e/c.html",
    },
    {
        "rank_no": 45,
        "title": "朝鲜“姜健”号驱逐舰正式入列朝鲜海军",
        "source": "人民网",
        "region": "international",
        "url": "http://world.people.com.cn/n1/2026/0907/c1002-40793499.html",
    },
    {
        "rank_no": 46,
        "title": "特朗普签署行政命令评估取消灰狼濒危物种保护",
        "source": "观察者网",
        "region": "international",
        "url": "https://kan.china.com/article/6074606.html",
        "manual_content": (
            "据美国《国会山报》报道，当地时间9月4日，美国总统特朗普在白宫签署行政命令，"
            "要求内政部和农业部评估灰狼及墨西哥狼是否已达到《濒危物种法》规定的除名或"
            "降低保护级别标准，并在90天内作出裁定。命令还旨在放宽牧场主在必要时猎杀"
            "威胁牲畜的狼群的限制。特朗普在签署时表示，狼群“正在毁掉这些牧场主的生意”。"
            "美国农业部长布鲁克·罗林斯称，由于狼仍被列入濒危物种名录，牧场主不能自行"
            "射杀。灰狼于1967年首次被美国列为濒危物种，种群恢复后保护级别曾多次调整。"
            "动物保护组织警告，削弱联邦保护可能危及数十年恢复成果并引发法律诉讼。"
        ),
    },
    {
        "rank_no": 47,
        "title": "埃及电视主持人莎拉·哈利法等12人因毒品案被判处死刑",
        "source": "UA.NEWS",
        "region": "international",
        "url": "https://ua.news/cn/world/u-egipti-televeduchu-saru-khalifu-zasudili-do-strati-u-spravi-pro-narkotiki",
    },
    {
        "rank_no": 48,
        "title": "联合国鼓励使用反映非洲真实大小的新地图，美国表示反对",
        "source": "人民网",
        "region": "international",
        "url": "http://world.people.com.cn/n1/2026/0906/c1002-40793300.html",
    },
    {
        "rank_no": 49,
        "title": "尼泊尔64岁妇女被困泥石流掩埋建筑多日后获救",
        "source": "新华网",
        "region": "international",
        "url": "https://www.news.cn/20260905/1c24f9c83c1047e187a7645e8b62e7b0/c.html",
    },
    {
        "rank_no": 50,
        "title": "八国外长谴责以色列官员有关将巴勒斯坦人迁离加沙地带的言论",
        "source": "新华社",
        "region": "international",
        "url": "https://www.yangtse.com/news/txs/202609/t20260906_390096.html",
    },
]


def build(run_date: str | None = None) -> list[dict]:
    out: list[dict] = []
    for item in ITEMS:
        title = item["title"]
        url = item.get("url")
        content = item.get("manual_content") or ""
        if url and not content:
            result = fetch(url, title)
            content = result.get("content") or ""
            if not content:
                print(
                    f"WARN rank {item['rank_no']}: fetch failed ({result.get('error')})",
                    file=sys.stderr,
                )
        row = {
            "rank_no": item["rank_no"],
            "title": title,
            "source": item["source"],
            "region": item["region"],
            "url": url,
            "content": content,
        }
        out.append(row)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="YYYY-MM-DD, default today Asia/Shanghai")
    parser.add_argument(
        "--output",
        help="JSON output path (default data/daily_news_<date>.json)",
    )
    parser.add_argument("--insert", action="store_true", help="run insert_daily_news.py")
    args = parser.parse_args()

    run_date = args.date or datetime.now(TZ).date().isoformat()
    out_path = Path(args.output or f"data/daily_news_{run_date}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = build(run_date)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    domestic = sum(1 for r in rows if r["region"] == "domestic")
    international = sum(1 for r in rows if r["region"] == "international")
    with_content = sum(1 for r in rows if r.get("content") and len(r["content"]) >= 80)
    print(
        f"Wrote {len(rows)} items to {out_path} "
        f"({domestic} domestic / {international} international, "
        f"{with_content} with content>=80 chars)"
    )

    if args.insert:
        import subprocess

        script = Path(__file__).resolve().parent / "insert_daily_news.py"
        cmd = [sys.executable, str(script), "--json", str(out_path), "--date", run_date]
        subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
