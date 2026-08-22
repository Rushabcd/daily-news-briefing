# 每日热点新闻简报

每天早上 8:00（北京时间）自动采集 28 条热点新闻，渲染一张竖版长图，通过 **Server酱** 推送到你的微信。长图使用 **jsDelivr CDN** 加载（仓库需设为 Public）。

```
GitHub Actions（每天 08:00 定时）
    │  ① python main.py render   采集新闻 + 渲染长图 + 生成正文
    ▼
长图提交进仓库（自动清理 7 天前旧图）
    │  ② git push（jsDelivr 通过仓库地址加载图片，国内可访问）
    ▼
③ python main.py push   正文 + ![长图](jsDelivr URL) → Server酱 → 微信
```

---

## 🚀 部署到 GitHub Actions

### 准备（2 分钟）

1. **仓库设为 Public**
   - 仓库 → **Settings** → 拉到最底 **Danger Zone** → **Change visibility** → **Make public**
   - ⚠️ 必须公开：jsDelivr CDN 只能加载**公开仓库**里的文件（私有仓库的图片手机打不开）
2. **（重要）重新生成 Server酱 SendKey**
   - 早期版本把 SendKey 明文提交进了 git 历史，转公开后等于泄露，请到 [sct.ftqq.com](https://sct.ftqq.com) 重新生成一个新 Key
3. **更新 GitHub Secret**
   - 仓库 → **Settings** → **Secrets and variables** → **Actions** → 新建/更新 `SERVERCHAN_SENDKEY`，填新 Key
   - 注意：脚本**只从 Secret 读 Key**，`config.json` 里不放任何密钥

### 手动触发测试

仓库 → **Actions** → **每日热点新闻简报** → 右侧 **Run workflow** → 等两三分钟变绿。

推送成功标准：
- 微信"方糖服务号"收到标题为「今日简报 X月X日」的消息
- **点开消息**（微信通知卡片本身不显示图片，这是平台限制），详情页能看到正文 + 长图

### 之后每天自动运行

每天 **北京时间 08:00** 自动执行，无需任何操作。长图每天一个文件名，不会碰到 CDN 缓存问题。

---

## 📱 收到的推送长什么样？

- **通知卡片**：标题 + 文字摘要（微信平台限制，卡片内不能显示图片）
- **点开详情页**：28 条热点新闻（Markdown 列表）+ 每日金句 + **完整长图**

---

## 🛠 本地运行（测试）

```bash
pip install pillow
python main.py render     # 阶段1：采集 + 渲染长图（不需要 SendKey）
python main.py push       # 阶段2：推送（需要环境变量 SERVERCHAN_SENDKEY）
```

Windows 一键测试：

```bash
set SERVERCHAN_SENDKEY=你的Key
python main.py            # render + push 一起跑（图片需已提交进仓库才能显示）
```

---

## 📂 文件说明

| 文件 | 用途 |
|------|------|
| `main.py` | 主程序：`render` / `push` 两阶段 |
| `news_collector.py` | 新闻采集（60s API + 百度/头条/微博/知乎） |
| `render.py` | 渲染竖版长图（Pillow） |
| `push.py` | Server酱 推送（图片以 `![](url)` 嵌进正文） |
| `config.json` | 仓库名 / 分支等非敏感配置 |
| `.github/workflows/daily-news.yml` | Actions 定时任务 |

---

## ❓ 常见问题

**Q：图片还是不显示？**
A：① 确认仓库已 Public；② 确认推送详情页的图片链接格式是 `cdn.jsdelivr.net/gh/用户名/仓库@分支/outputs/briefing_日期.png`；③ jsDelivr 国内偶尔波动，可多刷新一次或换 `testingcf.jsdelivr.net` 前缀试试。

**Q：微信通知卡片里怎么显示图片？**
A：做不到。微信服务号通知卡片只显示文字，图片在**点开消息后的详情页**展示——这是微信平台限制，所有走服务号的推送方案都一样。

**Q：推送失败？**
A：检查 Secret 里的 `SERVERCHAN_SENDKEY` 是否正确（尤其重新生成后记得更新 Secret）；Server酱 免费版每天限 5 条。

**Q：修改推送时间？**
A：编辑 `daily-news.yml` 的 `cron: '0 0 * * *'`（UTC 时间，比北京晚 8 小时）。

**Q：SendKey 泄露了怎么办？**
A：立刻去 [sct.ftqq.com](https://sct.ftqq.com) 重新生成 Key，并更新 GitHub Secret。旧 Key 立即失效。
