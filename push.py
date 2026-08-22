"""通过 Server酱（ServerChan）推送到微信。

Server酱 API 只支持两个 POST 参数（官方文档 https://sct.ftqq.com/sendkey）：
    title: 标题（必填，最长 32 字符，不能含换行）
    desp:  正文，支持 Markdown；图片必须用 ![](图片URL) 语法嵌在正文里才会显示

注意：不存在名为 images 的参数，单独传 images 字段会被服务端静默丢弃。
图片 URL 必须是国内可访问的公网地址（本项目使用 jsDelivr CDN 加载仓库内长图）。
"""

import ssl
import urllib.parse
import urllib.request

API_BASE = "https://sctapi.ftqq.com"


def push(sendkey, title, desp=""):
    """发送推送，返回服务端 JSON 字符串。

    图片请以 Markdown 语法拼进 desp，例如：
        desp = "正文内容\\n\\n![今日简报](https://cdn.jsdelivr.net/gh/xxx/xxx.png)"
    """
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/{sendkey}.send",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")
