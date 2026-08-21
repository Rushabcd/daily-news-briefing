"""每日热点新闻简报主程序：采集 → 渲染长图 → Server酱推送。"""

import json
import os
import sys
from datetime import datetime

from news_collector import collect_news
from push import push, upload_image_catbox
from render import render

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(PROJECT_DIR, "config.json")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    sendkey = cfg.get("sendkey") or os.environ.get("SERVERCHAN_SENDKEY", "")
    return cfg, sendkey


def build_markdown(news, quote, date):
    lines = [f"# 今日简报 · {date.month}月{date.day}日", ""]
    lines.extend(f"{i}. {text}" for i, text in enumerate(news, 1))
    lines.append("")
    lines.append(f"> 【每日金句】{quote}")
    return "\n".join(lines)


def main():
    cfg, sendkey = load_config()
    if not sendkey:
        print(
            "错误：未配置 Server酱 SendKey。\n"
            "请在 config.json 中填写 sendkey，或设置环境变量 SERVERCHAN_SENDKEY。"
        )
        sys.exit(1)

    print("[1/4] 采集热点新闻...")
    news, quote = collect_news()
    if not news:
        print("错误：新闻采集失败，未推送。")
        sys.exit(1)
    print(f"已获取 {len(news)} 条热点。")

    date = datetime.now()
    output_dir = cfg.get("output_dir") or os.path.join(PROJECT_DIR, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    image_path = os.path.join(output_dir, f"今日简报_{date:%Y%m%d}.png")

    print("[2/4] 渲染长图...")
    render(news, quote, date, image_path)
    print(f"长图已生成：{image_path}")

    title = f"今日简报 {date.month}月{date.day}日"
    desp = build_markdown(news, quote, date)

    images = None
    if cfg.get("image_upload"):
        print("[3/4] 上传长图...")
        url = upload_image_catbox(image_path)
        if url:
            images = [url]
            print(f"图片地址：{url}")
        else:
            print("图片上传失败，将仅推送文字内容。")

    print("[4/4] 推送微信...")
    result = push(sendkey, title, desp, images)
    print(result)
    try:
        code = json.loads(result).get("code")
        if code == 0:
            print("推送成功。")
        else:
            print(f"推送返回异常：{result}")
    except Exception:
        print(f"推送返回无法解析：{result}")


if __name__ == "__main__":
    main()
