"""按设计说明渲染「今日简报」竖版长图。"""

import os
import random
import re
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
MIN_HEIGHT = 1920
PAD_X = 64
CONTENT_WIDTH = WIDTH - PAD_X * 2

# 设计规范配色
BG = (250, 249, 247)          # 米白纸色 #FAF9F7
CARD_BG = (255, 255, 255)     # 卡片纯白 #FFFFFF
BLACK = (26, 26, 26)          # 纯黑 #1A1A1A
DARK_GRAY = (45, 45, 45)      # 正文深灰 #2D2D2D
MID_GRAY = (120, 120, 120)    # 次级文字 #787878
LIGHT_GRAY = (172, 170, 166)  # 装饰浅灰 #ACA8A6
LINE_GRAY = (232, 230, 226)   # 分隔线 #E8E6E2
DARK_RED = (185, 28, 28)      # 深红 #B91C1C
RED = (220, 38, 38)           # 正红 #DC2626
LIGHT_RED = (254, 242, 242)   # 浅红背景 #FEF2F2
GOLD = (180, 130, 30)         # 点缀金色 #B4821E
SOURCE_COLORS = {
    "60秒": (220, 38, 38),
    "百度": (59, 130, 246),
    "头条": (245, 87, 83),
    "微博": (239, 112, 152),
    "知乎": (0, 102, 255),
    "资讯": (107, 114, 128),
}

# 跨平台字体候选路径
FONT_CANDIDATES = {
    "title_bold": [
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ],
    "sans": [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ],
    "sans_bold": [
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ],
    "body": [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ],
    "quote": [
        "C:/Windows/Fonts/simkai.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ],
}

# 关键数据高亮：数字 + 单位，或 4 位以上大数字
KEY_DATA_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|％|万|亿|元|人|例|起|条|家|个|天|小时|分钟|岁|级|号|日|月|年|"
    r"次|辆|架|艘|米|公里|亩|吨|度|倍|位|名|户|件|项|笔|张|台|套|场|期|批|款|点|分|秒|时|周|"
    r"多|余|左右|以上|以下|人次|万辆|亿元|万元|个百分点|万亿|万件|万起|万例|万条|万次|万米|"
    r"万吨|万公里|平方公里|平方米|立方米|亿人次|亿件|亿起|亿例|亿条|亿次|亿吨|亿公里)"
    r"|\d{4,}(?:\.\d+)?"
)

_fonts = {}


def _load_font(kind, size):
    """按候选路径加载字体，全部失败时回退默认字体。"""
    for path in FONT_CANDIDATES.get(kind, []):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _init_fonts():
    _fonts["title"] = _load_font("title_bold", 56)
    _fonts["subtitle"] = _load_font("sans", 14)
    _fonts["date"] = _load_font("sans", 15)
    _fonts["news_num"] = _load_font("sans_bold", 18)
    _fonts["news"] = _load_font("body", 17)
    _fonts["source"] = _load_font("sans_bold", 12)
    _fonts["quote"] = _load_font("quote", 18)
    _fonts["quote_label"] = _load_font("sans_bold", 16)
    _fonts["footer"] = _load_font("sans", 13)
    _fonts["en"] = _load_font("sans", 16)


def wrap_lines(draw, text, font, max_width):
    """按字符换行，返回 [(行文本, 起始偏移)]。"""
    lines = []
    offset = 0
    for paragraph in text.split("\n"):
        line = ""
        start = offset
        for ch in paragraph:
            if draw.textlength(line + ch, font=font) <= max_width:
                line += ch
            else:
                lines.append((line, start))
                start = offset + 1
                line = ch
            offset += 1
        if line:
            lines.append((line, start))
        offset += 1
    return lines


def highlight_ranges(text):
    return [(match.start(), match.end()) for match in KEY_DATA_RE.finditer(text)]


def _in_ranges(pos, ranges):
    return any(start <= pos < end for start, end in ranges)


def _news_text(item):
    """兼容字符串和 dict 新闻格式。"""
    return item["title"] if isinstance(item, dict) else item


def _news_source(item):
    """获取新闻来源标识。"""
    return item.get("source", "") if isinstance(item, dict) else ""


def _draw_gradient_bar(img, y, height=8):
    """顶部红金渐变装饰条。"""
    pixels = img.load()
    for x in range(WIDTH):
        ratio = x / WIDTH
        r = int(DARK_RED[0] + (GOLD[0] - DARK_RED[0]) * ratio)
        g = int(DARK_RED[1] + (GOLD[1] - DARK_RED[1]) * ratio)
        b = int(DARK_RED[2] + (GOLD[2] - DARK_RED[2]) * ratio)
        for yy in range(y, y + height):
            pixels[x, yy] = (r, g, b)


def _source_badge_size(draw, source):
    """返回来源标签的 (宽度, 高度)。"""
    if not source:
        return 0, 0
    text_width = draw.textlength(source, font=_fonts["source"])
    return text_width + 20, 22


def _draw_source_badge(draw, x, y, source):
    """绘制圆角来源标签。"""
    if not source:
        return
    color = SOURCE_COLORS.get(source, MID_GRAY)
    w, h = _source_badge_size(draw, source)
    # 使用来源对应颜色作为标签背景
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=color)
    draw.text((x + 10, y + 4), source, font=_fonts["source"], fill=(255, 255, 255))


def draw_header(draw, date):
    """顶部渐变条 + 英文标识 + 主标题 + 日期行。"""
    y = 64

    # NEWS TODAY 英文标识
    en = "N E W S   T O D A Y"
    en_width = draw.textlength(en, font=_fonts["en"])
    draw.text(((WIDTH - en_width) / 2, y), en, font=_fonts["en"], fill=GOLD)
    y += 40

    # 装饰短线
    line_w = 80
    draw.line([(WIDTH / 2 - line_w, y), (WIDTH / 2 + line_w, y)], fill=LIGHT_GRAY, width=1)
    y += 36

    # 副标题行
    left_label = "热点资讯"
    right_label = "新鲜有料"
    lw = draw.textlength(left_label, font=_fonts["subtitle"])
    rw = draw.textlength(right_label, font=_fonts["subtitle"])
    gap = CONTENT_WIDTH - lw - rw
    draw.text((PAD_X, y), left_label, font=_fonts["subtitle"], fill=MID_GRAY)
    draw.text((PAD_X + lw + gap, y), right_label, font=_fonts["subtitle"], fill=MID_GRAY)
    y += 46

    # 主标题
    title = "今日简报"
    title_width = draw.textlength(title, font=_fonts["title"])
    draw.text((PAD_X, y), title, font=_fonts["title"], fill=BLACK)
    # 标题下方红色短下划线
    underline_y = y + 74
    draw.line([(PAD_X, underline_y), (PAD_X + title_width * 0.55, underline_y)], fill=RED, width=4)
    y += 100

    # 日期行
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    date_text = (
        f"{date.year}年{date.month}月{date.day}日 {weekdays[date.weekday()]}  ·  每天60秒知天下"
    )
    draw.text((PAD_X, y), date_text, font=_fonts["date"], fill=MID_GRAY)
    y += 56

    # 分隔线
    draw.line([(PAD_X, y), (WIDTH - PAD_X, y)], fill=LINE_GRAY, width=1)
    return y + 34


def _news_item_lines(draw, text, index, max_text_w):
    """计算新闻标题换行，并返回行列表。"""
    return wrap_lines(draw, text, _fonts["news"], max_text_w)


def _news_item_height(draw, index, text, source):
    """计算单条新闻卡片高度。"""
    number = f"{index}."
    num_width = draw.textlength(number, font=_fonts["news_num"])
    # 卡片内边距：左 24（给竖条和序号留空），右 24，上下 22
    text_available_w = CONTENT_WIDTH - 24 - num_width - 16 - 24
    lines = _news_item_lines(draw, text, index, text_available_w)
    h = max(44, len(lines) * 30 + 44)
    # 如果来源标签放不下了，额外加一行
    badge_w, badge_h = _source_badge_size(draw, source)
    last_line_w = 0
    if lines:
        last_line_w = draw.textlength(lines[-1][0], font=_fonts["news"])
    if badge_w and last_line_w + badge_w + 18 > text_available_w:
        h += 28
    return h


def draw_news_item(draw, index, item, x, y):
    """绘制单条新闻卡片：左侧红条、序号、标题（关键数据红色高亮）、来源标签。"""
    text = _news_text(item)
    source = _news_source(item)

    # 卡片背景
    card_h = _news_item_height(draw, index, text, source)
    draw.rounded_rectangle([x, y, x + CONTENT_WIDTH, y + card_h], radius=14, fill=CARD_BG)

    # 左侧红色竖条
    bar_w = 6
    draw.rounded_rectangle([x + 18, y + 18, x + 18 + bar_w, y + card_h - 18], radius=3, fill=RED)

    # 序号
    number = f"{index}."
    num_x = x + 36
    num_y = y + 24
    draw.text((num_x, num_y), number, font=_fonts["news_num"], fill=RED)
    num_width = draw.textlength(number, font=_fonts["news_num"])

    # 正文区域
    text_x = num_x + num_width + 16
    text_y = y + 24
    text_w = CONTENT_WIDTH - 24 - (text_x - x) - 24
    ranges = highlight_ranges(text)
    lines = _news_item_lines(draw, text, index, text_w)

    for line, start in lines:
        cx = text_x
        i = 0
        while i < len(line):
            pos = start + i
            if _in_ranges(pos, ranges):
                j = i
                while j < len(line) and _in_ranges(start + j, ranges):
                    j += 1
                seg = line[i:j]
                draw.text((cx, text_y), seg, font=_fonts["news"], fill=DARK_RED)
                cx += draw.textlength(seg, font=_fonts["news"])
                i = j
            else:
                j = i
                while j < len(line) and not _in_ranges(start + j, ranges):
                    j += 1
                seg = line[i:j]
                draw.text((cx, text_y), seg, font=_fonts["news"], fill=DARK_GRAY)
                cx += draw.textlength(seg, font=_fonts["news"])
                i = j
        text_y += 30

    # 来源标签：尽量放在最后一行末尾，放不下则另起一行
    if source:
        badge_w, badge_h = _source_badge_size(draw, source)
        last_line_w = draw.textlength(lines[-1][0], font=_fonts["news"]) if lines else 0
        line_start_y = y + 24 + (len(lines) - 1) * 30
        if last_line_w + badge_w + 18 <= text_w:
            badge_x = text_x + last_line_w + 12
            badge_y = line_start_y - 1
        else:
            badge_x = text_x
            badge_y = text_y + 4
        _draw_source_badge(draw, badge_x, badge_y, source)

    return y + card_h


def _draw_wechat_icon(draw, x, y, size):
    """绘制简化微信气泡图标。"""
    body_h = int(size * 0.72)
    radius = int(size * 0.28)
    draw.rounded_rectangle([x, y, x + size, y + body_h], radius=radius, fill=MID_GRAY)
    draw.polygon(
        [
            (x + int(size * 0.16), y + body_h - 1),
            (x + int(size * 0.34), y + body_h - 1),
            (x + int(size * 0.22), y + int(size * 0.95)),
        ],
        fill=MID_GRAY,
    )
    draw.ellipse(
        [x + int(size * 0.24), y + int(size * 0.26),
         x + int(size * 0.42), y + int(size * 0.44)],
        fill=BG,
    )
    draw.ellipse(
        [x + int(size * 0.54), y + int(size * 0.26),
         x + int(size * 0.72), y + int(size * 0.44)],
        fill=BG,
    )


def draw_footer(draw, quote, y):
    """每日金句卡片 + 页脚。"""
    # 金句卡片
    quote_lines = wrap_lines(draw, quote, _fonts["quote"], CONTENT_WIDTH - 56)
    card_h = 56 + len(quote_lines) * 36
    draw.rounded_rectangle([PAD_X, y, WIDTH - PAD_X, y + card_h], radius=14, fill=LIGHT_RED)
    # 左侧深红竖条
    draw.rounded_rectangle([PAD_X + 18, y + 18, PAD_X + 24, y + card_h - 18], radius=3, fill=DARK_RED)

    label = "每日金句"
    draw.text((PAD_X + 38, y + 20), label, font=_fonts["quote_label"], fill=DARK_RED)
    ly = y + 52
    for line, _ in quote_lines:
        draw.text((PAD_X + 38, ly), line, font=_fonts["quote"], fill=DARK_RED)
        ly += 36
    y += card_h + 34

    # 页脚分隔线
    draw.line([(PAD_X, y), (WIDTH - PAD_X, y)], fill=LINE_GRAY, width=1)
    y += 24

    draw.text((PAD_X, y), "正能量", font=_fonts["footer"], fill=LIGHT_GRAY)
    right = "每天60秒知天下"
    right_width = draw.textlength(right, font=_fonts["footer"])
    icon_size = 18
    icon_x = WIDTH - PAD_X - right_width - icon_size - 12
    _draw_wechat_icon(draw, icon_x, y + 1, icon_size)
    draw.text((WIDTH - PAD_X - right_width, y), right, font=_fonts["footer"], fill=LIGHT_GRAY)
    return y + 44


def _add_paper_texture(img):
    """叠加细微纸张纤维纹理。"""
    noise = Image.effect_noise(img.size, 6).convert("RGB")
    textured = Image.blend(img, noise, 0.018)
    draw = ImageDraw.Draw(textured)
    rng = random.Random(20260821)
    for _ in range(80):
        yy = rng.randint(0, img.height - 1)
        xx = rng.randint(0, img.width)
        length = rng.randint(30, 160)
        draw.line(
            [(xx, yy), (min(xx + length, img.width), yy)],
            fill=(238, 236, 232),
            width=1,
        )
    return textured


def render(news, quote, date=None, output_path=None):
    date = date or datetime.now()
    _init_fonts()
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    header_bottom = 390
    news_height = 0
    for i, item in enumerate(news):
        text = _news_text(item)
        source = _news_source(item)
        item_h = _news_item_height(probe, i + 1, text, source)
        news_height += item_h
        if i < len(news) - 1:
            news_height += 18

    quote_lines = len(wrap_lines(probe, quote, _fonts["quote"], CONTENT_WIDTH - 56))
    footer_height = 130 + quote_lines * 36
    height = max(MIN_HEIGHT, header_bottom + news_height + footer_height)

    img = Image.new("RGB", (WIDTH, height), BG)
    _draw_gradient_bar(img, 0)
    img = _add_paper_texture(img)
    draw = ImageDraw.Draw(img)

    y = draw_header(draw, date)
    for i, item in enumerate(news):
        y = draw_news_item(draw, i + 1, item, PAD_X, y)
        if i < len(news) - 1:
            y += 18
    draw_footer(draw, quote, y)

    if output_path:
        img.save(output_path, "PNG")
    return output_path or img
