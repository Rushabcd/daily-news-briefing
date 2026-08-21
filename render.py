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
BLACK = (26, 26, 26)          # 纯黑 #1A1A1A
DARK_GRAY = (45, 45, 45)      # 正文深灰 #2D2D2D
MID_GRAY = (120, 120, 120)    # 次级文字 #787878
LIGHT_GRAY = (172, 170, 166)  # 装饰浅灰 #ACA8A6
LINE_GRAY = (222, 220, 216)   # 分隔线 #DEDCD8
DARK_RED = (200, 30, 30)      # 深红 #C81E1E
RED = (231, 60, 47)           # 正红 #E73C2F
GOLD = (196, 152, 60)         # 点缀金色 #C4983C

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
    _fonts["title"] = _load_font("title_bold", 44)
    _fonts["subtitle"] = _load_font("sans", 13)
    _fonts["date"] = _load_font("sans", 14)
    _fonts["news_num"] = _load_font("sans_bold", 16)
    _fonts["news"] = _load_font("body", 16)
    _fonts["quote"] = _load_font("quote", 17)
    _fonts["quote_label"] = _load_font("sans_bold", 15)
    _fonts["footer"] = _load_font("sans", 13)
    _fonts["en"] = _load_font("sans", 15)


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


def _news_text_width(draw, index):
    number = f"{index}、"
    num_width = draw.textlength(number, font=_fonts["news_num"])
    return CONTENT_WIDTH - num_width - 12


def _news_item_height(draw, index, text):
    lines = wrap_lines(draw, text, _fonts["news"], _news_text_width(draw, index))
    return len(lines) * 28


def draw_header(draw, date):
    """顶部装饰条 + 副标题 + 主标题 + 日期行。"""
    y = 52

    # NEWS TODAY 英文标识
    en = "N E W S   T O D A Y"
    en_width = draw.textlength(en, font=_fonts["en"])
    draw.text(((WIDTH - en_width) / 2, y), en, font=_fonts["en"], fill=GOLD)
    y += 36

    # 装饰线：左短实线 + 中间长虚线 + 右短实线
    draw.line([(PAD_X, y), (200, y)], fill=LIGHT_GRAY, width=1)
    dash_x = 220
    while dash_x < 860:
        draw.line([(dash_x, y), (min(dash_x + 12, 860), y)], fill=LIGHT_GRAY, width=1)
        dash_x += 22
    draw.line([(880, y), (WIDTH - PAD_X, y)], fill=LIGHT_GRAY, width=1)
    y += 50

    # 副标题行
    draw.text((PAD_X, y), "热点资讯", font=_fonts["subtitle"], fill=MID_GRAY)
    right = "新鲜有料"
    right_width = draw.textlength(right, font=_fonts["subtitle"])
    draw.text((WIDTH - PAD_X - right_width, y), right, font=_fonts["subtitle"], fill=MID_GRAY)
    y += 42

    # 主标题（设计规范配色）
    title = "今日简报"
    colors = [BLACK, DARK_RED, RED, RED]
    x = PAD_X
    for ch, color in zip(title, colors):
        draw.text((x, y), ch, font=_fonts["title"], fill=color)
        x += draw.textlength(ch, font=_fonts["title"])
    y += 74

    # 日期行
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    date_text = (
        f"{date.year}年{date.month}月{date.day}日 {weekdays[date.weekday()]}  ·  每天60秒知天下"
    )
    draw.text((PAD_X, y), date_text, font=_fonts["date"], fill=MID_GRAY)
    y += 48

    # 分隔线
    draw.line([(PAD_X, y), (WIDTH - PAD_X, y)], fill=LINE_GRAY, width=1)
    return y + 30


def draw_news_item(draw, index, text, x, y, line_height=28):
    """绘制单条新闻，关键数据用红色高亮。"""
    number = f"{index}、"
    draw.text((x, y), number, font=_fonts["news_num"], fill=BLACK)
    num_width = draw.textlength(number, font=_fonts["news_num"])
    text_x = x + num_width + 12
    text_width = CONTENT_WIDTH - num_width - 12
    ranges = highlight_ranges(text)

    for line, start in wrap_lines(draw, text, _fonts["news"], text_width):
        cx = text_x
        i = 0
        while i < len(line):
            pos = start + i
            if _in_ranges(pos, ranges):
                j = i
                while j < len(line) and _in_ranges(start + j, ranges):
                    j += 1
                seg = line[i:j]
                draw.text((cx, y), seg, font=_fonts["news"], fill=DARK_RED)
                cx += draw.textlength(seg, font=_fonts["news"])
                i = j
            else:
                j = i
                while j < len(line) and not _in_ranges(start + j, ranges):
                    j += 1
                seg = line[i:j]
                draw.text((cx, y), seg, font=_fonts["news"], fill=DARK_GRAY)
                cx += draw.textlength(seg, font=_fonts["news"])
                i = j
        y += line_height
    return y


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
    """每日金句 + 页脚。"""
    draw.line([(PAD_X, y), (WIDTH - PAD_X, y)], fill=LINE_GRAY, width=1)
    y += 30

    draw.text((PAD_X, y), "【每日金句】", font=_fonts["quote_label"], fill=DARK_RED)
    y += 40
    for line, _ in wrap_lines(draw, quote, _fonts["quote"], CONTENT_WIDTH):
        draw.text((PAD_X, y), line, font=_fonts["quote"], fill=MID_GRAY)
        y += 34
    y += 20

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
        y = rng.randint(0, img.height - 1)
        x = rng.randint(0, img.width)
        length = rng.randint(30, 160)
        draw.line(
            [(x, y), (min(x + length, img.width), y)],
            fill=(238, 236, 232),
            width=1,
        )
    return textured


def render(news, quote, date=None, output_path=None):
    date = date or datetime.now()
    _init_fonts()
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    header_bottom = 360
    news_height = 0
    for i, text in enumerate(news):
        item_h = _news_item_height(probe, i + 1, text)
        news_height += item_h
        if i < len(news) - 1:
            news_height += 14

    quote_lines = len(wrap_lines(probe, quote, _fonts["quote"], CONTENT_WIDTH))
    footer_height = 140 + quote_lines * 34
    height = max(MIN_HEIGHT, header_bottom + news_height + footer_height)

    img = Image.new("RGB", (WIDTH, height), BG)
    img = _add_paper_texture(img)
    draw = ImageDraw.Draw(img)

    y = draw_header(draw, date)
    for i, text in enumerate(news):
        y = draw_news_item(draw, i + 1, text, PAD_X, y)
        if i < len(news) - 1:
            y += 14
    draw_footer(draw, quote, y)

    if output_path:
        img.save(output_path, "PNG")
    return output_path or img
