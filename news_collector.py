"""采集每日热点新闻，目标 25-30 条。

优先使用 60s API（每日 60 秒读懂世界），不足时依次从百度热搜、
今日头条热榜、微博热搜、知乎热榜补充，最后使用内置兜底数据。

返回格式：每条新闻为 dict，包含 title（标题）、url（点击跳转链接）、source（来源标识）。
"""

import json
import re
import ssl
import urllib.parse
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

TARGET_COUNT = 28

FALLBACK_NEWS = [
    "国家统计局发布最新经济数据，上半年国内生产总值同比增长 5.0%，经济运行总体平稳。",
    "教育部部署秋季开学工作，要求各地严格落实校园安全责任，加强心理健康教育。",
    "多地出台楼市新政，首付比例进一步下调至 15%，支持居民刚性和改善性住房需求。",
    "全国铁路暑运客流持续高位运行，单日发送旅客连续多日突破 1400 万人次。",
    "市场监管总局开展网络餐饮专项整治，重点打击无证经营和食品安全违法行为。",
    "我国新能源汽车保有量突破 2500 万辆，充电基础设施加快建设。",
    "多地遭遇强降雨天气，相关部门启动应急响应，全力做好防汛救灾工作。",
    "国家卫健委发布夏季重点传染病防控提示，提醒公众注意饮食卫生。",
    "国产大飞机 C919 新增多条商业航线，累计承运旅客突破 50 万人次。",
    "工信部推进中小企业数字化转型，计划三年内培育 10 万家专精特新企业。",
    "全国夏粮收购进展顺利，主产区累计收购小麦超过 6000 万吨。",
    "文旅部发布暑期旅游提示，倡导文明旅游，加强景区安全管理。",
    "我国科学家在量子计算领域取得新突破，相关成果发表于国际权威期刊。",
    "多地优化住房公积金政策，提高贷款额度至 120 万元，减轻职工购房压力。",
    "全国公安机关开展夏季治安打击整治行动，破获各类案件 12 万余起。",
    "医保局推动药品集中带量采购扩围，进一步降低群众用药负担，平均降价 53%。",
    "我国跨境电商进出口规模持续扩大，上半年同比增长 10.5%。",
    "多地高温天气持续，气象部门提醒公众做好防暑降温措施，局部可达 40°C。",
    "国际奥委会公布新周期赛事安排，多项国际赛事将在中国举办。",
    "全国多地举办全民健身活动，推动体育公共服务均等化，参与人数超 8000 万。",
    "央行宣布下调存款准备金率 0.5 个百分点，释放长期资金约 1 万亿元。",
    "我国 5G 基站总数突破 400 万个，覆盖全国所有地级市城区。",
    "农业农村部数据显示，全国生猪产能恢复至常年水平 95% 以上。",
    "中欧班列累计开行突破 10 万列，通达欧洲 25 个国家 200 多个城市。",
    "国家能源局发布数据，上半年可再生能源发电量占比达 35.2%。",
    "全国城镇新增就业 698 万人，完成全年目标 63%。",
    "我国数字经济规模突破 55 万亿元，占 GDP 比重超过 40%。",
    "教育部发布新版学科专业目录，新增 35 个急需紧缺专业。",
    "全国碳市场累计成交额突破 100 亿元，碳价稳中有升。",
    "我国跨境电商主体已超 10 万家，海外仓数量超过 2000 个。",
]

FALLBACK_QUOTE = "日日行，不怕千万里；常常做，不怕千万事。"


def _fetch(url, timeout=15, headers=None):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            **(headers or {}),
        },
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _clean_title(text):
    return re.sub(r"\s+", " ", text).strip()


def _strip_number(text):
    return re.sub(r"^\s*\d+[、.．]\s*", "", text).strip()


def _parse_hot(value):
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else 0


def _search_url(title, engine="baidu"):
    """为没有原始链接的标题构造搜索跳转链接。"""
    encoded = urllib.parse.quote(title)
    if engine == "baidu":
        return f"https://www.baidu.com/s?wd={encoded}"
    if engine == "weibo":
        return f"https://s.weibo.com/weibo?q={encoded}"
    if engine == "zhihu":
        return f"https://www.zhihu.com/search?type=content&q={encoded}"
    return f"https://www.baidu.com/s?wd={encoded}"


def collect_60s():
    """60s API：每日 60 秒读懂世界，返回约 20 条新闻和一句金句。

    该接口不提供单条 URL，返回的 link 为当日完整图文文章，所有新闻共用此链接。
    """
    data = json.loads(_fetch("https://60s.viki.moe/v2/60s"))
    payload = data.get("data") or {}
    news = [_strip_number(item) for item in payload.get("news", [])]
    news = [item for item in news if item]
    quote = payload.get("tip") or FALLBACK_QUOTE
    link = payload.get("link") or "https://60s.viki.moe"
    items = [{"title": t, "url": link, "source": "60秒"} for t in news]
    return items, quote


def collect_baidu():
    """百度热搜实时榜。"""
    html = _fetch("https://top.baidu.com/board?tab=realtime")
    titles = re.findall(r'class="c-single-text-ellipsis"[^>]*>([^<]+)<', html)
    values = re.findall(r'class="hot-index_1Bl1a"[^>]*>([^<]+)<', html)
    items = []
    for i, title in enumerate(titles):
        title = _clean_title(title)
        if not title:
            continue
        hot = _parse_hot(values[i]) if i < len(values) else 0
        items.append({
            "title": title,
            "url": _search_url(title, "baidu"),
            "source": "百度",
            "hot": hot,
        })
    return items


def collect_toutiao():
    """今日头条热榜。"""
    data = json.loads(
        _fetch("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    )
    items_raw = data.get("data") or []
    items = []
    for entry in items_raw:
        title = _clean_title(entry.get("Title") or "")
        if not title:
            continue
        url = entry.get("Url") or _search_url(title, "baidu")
        items.append({
            "title": title,
            "url": url,
            "source": "头条",
            "hot": _parse_hot(entry.get("HotValue")),
        })
    return items


def collect_weibo():
    """微博热搜榜。"""
    data = json.loads(_fetch("https://weibo.com/ajax/side/hotSearch"))
    realtime = (data.get("data") or {}).get("realtime") or []
    items = []
    for entry in realtime:
        title = _clean_title(entry.get("word") or "")
        if not title:
            continue
        items.append({
            "title": title,
            "url": _search_url(title, "weibo"),
            "source": "微博",
            "hot": _parse_hot(entry.get("num")),
        })
    return items


def collect_zhihu():
    """知乎热榜。"""
    data = json.loads(
        _fetch(
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50",
            headers={"Referer": "https://www.zhihu.com/"},
        )
    )
    items = []
    for entry in data.get("data") or []:
        target = entry.get("target") or {}
        title = _clean_title(target.get("title") or "")
        if not title:
            continue
        url = target.get("url") or _search_url(title, "zhihu")
        # 知乎返回的 url 有时是 /question/xxx，需要补全协议和域名
        if url.startswith("/"):
            url = f"https://www.zhihu.com{url}"
        items.append({
            "title": title,
            "url": url,
            "source": "知乎",
            "hot": _parse_hot(entry.get("detail_text")),
        })
    return items


def _title_key(text):
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = _title_key(item["title"])
        if not key or key in seen:
            continue
        duplicate = False
        for old in seen:
            if len(key) >= 8 and (key in old or old in key):
                duplicate = True
                break
        if duplicate:
            continue
        seen.add(key)
        result.append(item)
    return result


def collect_news():
    """返回 (新闻列表, 金句)。优先 60s API，不足时从其他平台补充。

    每条新闻为 dict：{"title": str, "url": str, "source": str}
    """
    items = []
    quote = FALLBACK_QUOTE

    try:
        items, quote = collect_60s()
        print(f"[采集] 60s API：{len(items)} 条")
    except Exception as exc:
        print(f"[采集] 60s API 失败：{exc}")

    if len(items) < TARGET_COUNT:
        supplement = []
        for name, fn in [
            ("百度热搜", collect_baidu),
            ("今日头条", collect_toutiao),
            ("微博热搜", collect_weibo),
            ("知乎热榜", collect_zhihu),
        ]:
            try:
                batch = fn()
                if batch:
                    print(f"[采集] {name}：{len(batch)} 条")
                    supplement.extend(batch)
            except Exception as exc:
                print(f"[采集] {name} 失败：{exc}")

        supplement = _dedupe(supplement)
        supplement.sort(key=lambda item: item.get("hot", 0), reverse=True)
        existing_keys = {_title_key(i["title"]) for i in items}
        for item in supplement:
            if len(items) >= TARGET_COUNT:
                break
            key = _title_key(item["title"])
            if not key or key in existing_keys:
                continue
            dup = False
            for old in existing_keys:
                if len(key) >= 8 and (key in old or old in key):
                    dup = True
                    break
            if dup:
                continue
            existing_keys.add(key)
            items.append(item)

    if not items:
        print("[采集] 所有数据源均失败，使用内置兜底数据。")
        items = [
            {"title": t, "url": _search_url(t, "baidu"), "source": "资讯"}
            for t in FALLBACK_NEWS[:TARGET_COUNT]
        ]

    print(f"[采集] 最终 {len(items)} 条热点")
    return items[:TARGET_COUNT], quote
