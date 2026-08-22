"""每日热点新闻简报主程序：采集 → 渲染长图 → 提交图床 → Server酱推送。

两阶段运行（GitHub Actions 使用，保证长图先提交进仓库、CDN 可加载后再发消息）：
    python main.py render   # 阶段1：采集新闻 + 渲染长图 + 生成推送正文 outputs/push_content.md
    python main.py push     # 阶段2：拼接 jsDelivr 长图链接 → 推送到微信

本地一键测试（不带头图，图片链接需要先由 Actions 或手动把 png 提交进仓库）：
    SERVERCHAN_SENDKEY=SCTxxx python main.py

SendKey 从环境变量 SERVERCHAN_SENDKEY 读取（本地测试也可临时放回 config.json），
不要把 SendKey 提交进仓库。
"""

import json
import os
import sys
from datetime import datetime

from news_collector import collect_news
from push import push
from render import render

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(PROJECT_DIR, "config.json")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    sendkey = os.environ.get("SERVERCHAN_SENDKEY", "") or cfg.get("sendkey", "")
    return cfg, sendkey


def build_markdown(news, quote, date):
    lines = [f"# 今日简报 · {date.month}月{date.day}日", ""]
    lines.append(f"> {date.year}年{date.month}月{date.day}日 · 每天60秒知天下")
    lines.append("")
    lines.extend(f"{i}. {text}" for i, text in enumerate(news, 1))
    lines.append("")
    lines.append(f"> 【每日金句】{quote}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("🖼 **下方是今日简报完整长图**")
    return "\n".join(lines)


def image_url(cfg, image_filename):
    """生成长图的 jsDelivr CDN 地址（要求仓库为 public）。"""
    repo = cfg.get("github_repo", "")
    branch = cfg.get("github_branch", "main")
    if repo:
        return f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/outputs/{image_filename}"
    return None


def output_dir(cfg):
    return cfg.get("output_dir") or os.path.join(PROJECT_DIR, "outputs")


def phase_render(cfg):
    """阶段1：采集 → 渲染长图 → 生成推送正文文件。"""
    print("[1/2] 采集热点新闻...")
    news, quote = collect_news()
    if not news:
        print("错误：新闻采集失败，未生成简报。")
        sys.exit(1)
    print(f"已获取 {len(news)} 条热点。")

    date = datetime.now()
    out_dir = output_dir(cfg)
    os.makedirs(out_dir, exist_ok=True)
    image_path = os.path.join(out_dir, f"briefing_{date:%Y%m%d}.png")

    print("[2/2] 渲染长图...")
    render(news, quote, date, image_path)
    print(f"长图已生成：{image_path}")

    md = build_markdown(news, quote, date)
    md_path = os.path.join(out_dir, "push_content.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"推送正文已生成：{md_path}")
    return image_path


def phase_push(cfg, sendkey):
    """阶段2：读取正文 + 拼接长图 CDN 链接 → 推送微信。"""
    if not sendkey:
        print(
            "错误：未配置 Server酱 SendKey。\n"
            "请设置环境变量 SERVERCHAN_SENDKEY（GitHub Actions 中配置 Secret）。"
        )
        sys.exit(1)

    date = datetime.now()
    out_dir = output_dir(cfg)
    md_path = os.path.join(out_dir, "push_content.md")
    if not os.path.exists(md_path):
        print(f"错误：未找到 {md_path}，请先运行 python main.py render")
        sys.exit(1)

    with open(md_path, encoding="utf-8") as f:
        desp = f.read()

    image_name = f"briefing_{date:%Y%m%d}.png"
    url = image_url(cfg, image_name)
    if url:
        desp += f"\n\n![今日简报]({url})"
        print(f"长图链接：{url}")
    else:
        print("config.json 未配置 github_repo，本次仅推送文字。")

    print("推送微信...")
    result = push(sendkey, f"今日简报 {date.month}月{date.day}日", desp)
    print(result)
    try:
        code = json.loads(result).get("code")
        if code == 0:
            print("推送成功。")
        else:
            print(f"推送返回异常：{result}")
    except Exception:
        print(f"推送返回无法解析：{result}")


def main():
    cfg, sendkey = load_config()
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"

    if phase == "render":
        phase_render(cfg)
    elif phase == "push":
        phase_push(cfg, sendkey)
    elif phase == "all":
        # 本地一键测试：渲染 + 直接推送（图片链接能否加载取决于图片是否已提交仓库）
        phase_render(cfg)
        phase_push(cfg, sendkey)
    else:
        print(f"未知参数：{phase}（可用：render / push）")
        sys.exit(1)


if __name__ == "__main__":
    main()
