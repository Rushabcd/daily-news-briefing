"""通过 Server酱（ServerChan）推送到微信。"""

import json
import os
import time
import urllib.parse
import urllib.request
import ssl

API_BASE = "https://sctapi.ftqq.com"


def push(sendkey, title, desp="", images=None):
    """发送推送，返回服务端 JSON 字符串。"""
    data = {"title": title, "desp": desp}
    if images:
        data["images"] = "\n".join(images)
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/{sendkey}.send",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def upload_image_catbox(path):
    """上传图片到 catbox.moe，返回公开 URL；失败返回 None。"""
    try:
        boundary = "----CodexBoundary" + str(int(time.time()))
        with open(path, "rb") as f:
            file_bytes = f.read()
        filename = os.path.basename(path)
        # 用简单 ASCII 文件名避免中文编码问题
        safe_filename = "briefing.png"
        parts = []
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="reqtype"\r\n\r\n'
            f"fileupload\r\n".encode()
        )
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="fileToUpload"; '
            f'filename="{safe_filename}"\r\n'
            f"Content-Type: image/png\r\n\r\n".encode()
        )
        parts.append(file_bytes)
        parts.append(f"\r\n--{boundary}--\r\n".encode())
        body = b"".join(parts)
        req = urllib.request.Request(
            "https://catbox.moe/user/api.php",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            url = resp.read().decode("utf-8", errors="replace").strip()
        return url if url.startswith("http") else None
    except Exception as exc:
        print(f"[上传] catbox.moe 失败：{exc}")
        return None
