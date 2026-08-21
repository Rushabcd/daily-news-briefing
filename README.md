# 每日热点新闻简报

每天早上 8:00（北京时间）自动采集 28 条热点新闻，生成一张漂亮的竖版长图，通过 **Server酱** 推送到你的微信。

---

## 🚀 一键部署到 GitHub Actions（推荐，无需本机运行）

### 准备工作（5 分钟）

**① 注册 GitHub 账号**

如果你还没有 GitHub 账号，打开 [github.com](https://github.com) 点 **Sign up** 注册一个，用邮箱就能注册，很简单。

**② 获取 Server酱 SendKey**

1. 打开 [sct.ftqq.com](https://sct.ftqq.com)，用 GitHub 或微信扫码登录
2. 登录后点 **SendKey** → 复制那一串以 `SCT` 开头的密钥（比如 `SCT16370...`）

---

### 第 1 步：把代码上传到你的 GitHub

1. 打开 [github.com](https://github.com)，登录后点右上角 **+** → **New repository**
2. 仓库名填 `daily-news-briefing`（或你喜欢的名字），选 **Private**（私有仓库，别人看不到）
3. 不要勾选任何初始化选项，直接点 **Create repository**
4. 创建后会跳转到一个新页面，上面有你的仓库地址，类似：`https://github.com/你的用户名/daily-news-briefing.git`

打开你电脑上的终端（PowerShell / CMD / 终端），逐条执行以下命令（把 `你的用户名` 换成你的 GitHub 用户名）：

```bash
cd C:\Users\rfxue\Documents\Codex\2026-08-21\new-chat-2
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/你的用户名/daily-news-briefing.git
git push -u origin main
```

> 💡 如果提示要登录，会弹出浏览器窗口让你授权 GitHub，登录一次就行。

---

### 第 2 步：配置 SendKey（密钥）

1. 打开你的 GitHub 仓库页面（就是刚才创建的那个）
2. 点顶部的 **Settings** 标签
3. 点左侧菜单的 **Secrets and variables** → **Actions**
4. 点绿色的 **New repository secret** 按钮
5. **Name** 填：`SERVERCHAN_SENDKEY`
6. **Secret** 填：你从 Server酱 复制的那一串 SendKey
7. 点 **Add secret**

---

### 第 3 步：手动运行一次，测试是否成功

1. 点仓库顶部的 **Actions** 标签
2. 在左侧工作流列表里点 **每日热点新闻简报**
3. 点右侧的 **Run workflow** → 再点 **Run workflow**
4. 等一两分钟，黄色圆点变绿色勾勾就说明跑完了
5. 点进去看日志，如果最后显示「推送成功」，你的微信就会收到今天的新闻简报！

---

### 第 4 步：之后每天自动运行

什么都不用做！GitHub Actions 会自动在 **每天北京时间 08:00** 运行一次程序。

每次运行生成的长图可以在 Actions 页面下载（保留 7 天）。

---

## 📱 收到的推送长什么样子？

推送包含：
- **标题**：今日简报 · X月X日
- **文字内容**：28 条热点新闻 + 每日金句
- **可选图片**：竖版长图（如果开启了图片上传）

> 默认只推送文字。如果想同时收到长图，把 `config.json` 里的 `"image_upload"` 改成 `true`。

---

## 🛠 本地运行（用于测试）

如果你在 Windows 电脑上想先测试一下：

```bash
pip install pillow
python main.py
```

程序会自动采集新闻、生成长图并推送到你的微信。

---

## 📂 文件说明

| 文件 | 用途 |
|------|------|
| `main.py` | 主程序入口 |
| `news_collector.py` | 新闻采集（60s API + 百度/头条/微博/知乎） |
| `render.py` | 渲染竖版长图（Pillow） |
| `push.py` | Server酱 推送 |
| `config.json` | 本地测试用的配置 |
| `requirements.txt` | Python 依赖列表 |
| `.github/workflows/daily-news.yml` | GitHub Actions 自动部署配置 |

---

## 📊 数据来源

程序按以下顺序采集新闻，自动补足 28 条：

1. **60s API**（60s.viki.moe）— 每日 60 秒读懂世界，最稳定
2. **百度热搜** — top.baidu.com
3. **今日头条热榜** — www.toutiao.com
4. **微博热搜** — weibo.com
5. **知乎热榜** — zhihu.com
6. 内置兜底数据（所有在线源都失败时使用）

---

## 🎨 设计风格

长图样式参考设计说明，包含：
- 仿纸张纹理米白背景
- 渐变红色标题（"今"黑、"日"深红、"简""报"正红）
- 28 条热点新闻，关键数据红色高亮
- 每日金句 + 页脚

---

## ❓ 常见问题

**Q：推送失败怎么办？**
A：检查 SendKey 是否配置正确，或者 Server酱 服务是否正常。

**Q：新闻数量不够 28 条？**
A：如果所有数据源都失败，会使用内置的 30 条兜底新闻。正常情况都能采集到 28 条以上。

**Q：想修改推送时间？**
A：编辑 `.github/workflows/daily-news.yml`，修改 `cron: '0 0 * * *'` 这一行。UTC 时间比北京时间晚 8 小时，比如 `'0 16 * * *'` 是北京时间凌晨 0 点。

**Q：图片上传到微信不显示？**
A：Server酱 的图片推送依赖图床服务，有时可能不稳定。纯文字推送是稳定的。
