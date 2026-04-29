---
name: browser-boss
description: 浏览器遥控器——用户只需说"搜一下""打开""截图""填表"，AI 自动操控本地 Edge/Chrome 浏览器。支持 Bing/头条搜索、网页交互、数据提取、隔离窗口模式（不影响用户正常使用）。每次用户提到浏览器操作、网页搜索、页面截图、CDP 相关任务时都应加载此 skill。
---

# Browser Boss — 浏览器总管

一句话：**把浏览器变成 AI 的遥控玩具**。用户用自然语言下指令，剩下的 AI 搞定。

## 快速判决策略

收到用户请求后，先判断属于哪类操作，然后选对应工具：

| 用户意图 | 用什么 | 是否需隔离窗口 |
|---------|--------|:---:|
| 搜索（"搜一下 xxx"） | `bb.py search` → 头条搜索 | 否 |
| 打开公开网页 | `bb.py open` | 否 |
| 需登录的网站（知乎/B站等） | `bb.py open --bridge`→可视化窗口 | 是 |
| 交互（点击/填表/截图） | CDP 命令 + target_id | **是** |
| 数据提取 | `browser_cdp(Runtime.evaluate)` + target_id | 是 |
| 批量任务 | `bb.py batch` | 是 |

**原则：只要涉及交互（点击/填表/滚动），一律走隔离窗口模式，避免干扰用户。**

## 工具选择（为什么是这个不是那个）

### bb.py — 一键直达
适合：搜索、打开网页。自动检测 Edge CDP 是否在线，不在线则通过 PowerShell 启动。

```bash
python3 /root/workspace/scripts/bb.py search "关键词"
python3 /root/workspace/scripts/bb.py open "https://example.com"
python3 /root/workspace/scripts/bb.py status
```

### browser_cdp + target_id — 精准控制
适合：所有交互式操作。原因是 Hermes 的高层工具（`browser_navigate`、`browser_click` 等）**没有 `target_id` 参数**——它们自动选择"当前活跃标签页"，无法精确指定目标窗口。如果用户在操作期间切回自己窗口，AI 的操作就会发生在用户窗口里。

**因此交互式操作必须全程走 CDP：**

```python
# 1. 创建隔离窗口
result = browser_cdp("Target.createTarget", 
    {"newWindow": True, "url": "about:blank"})
tid = result["result"]["targetId"]

# 2. 导航 & 操作（所有命令都带 target_id）
browser_cdp("Page.navigate", {"url": "https://..."}, target_id=tid)
browser_cdp("Runtime.evaluate", 
    {"expression": "document.querySelector('button').click()"}, 
    target_id=tid)

# 3. 用完关闭
browser_cdp("Target.closeTarget", {"targetId": tid})
```

## 环境要求

| 项目 | 说明 |
|------|------|
| 浏览器 | Microsoft Edge（Chromium），需开启 CDP |
| CDP 端口 | `127.0.0.1:9224` |
| 网络 | WSL2 镜像模式（`networkingMode=mirrored`），Windows 和 WSL 共享 localhost |
| bb.py | `/root/workspace/scripts/bb.py` |
| agent-browser | `/usr/bin/agent-browser` v0.26.0 |

## 搜索策略

- **首选：头条搜索** `https://so.toutiao.com/search?keyword=关键词` — 中文内容最丰富，不需 Cookie
- **备用：Bing** `https://cn.bing.com/search?q=关键词` — Edge CDP 进程无 Cookie 时可能空白
- **提取结果用 `document.body.innerText`**，比 snapshot 更完整（snapshot 常省略搜索结果内容）

## 隔离窗口模式 — 关键概念

Hermes 连接的是你本地 Edge 浏览器。为了避免 AI 操作干扰你正在看的页面，交互式操作需要创建**独立的浏览器窗口**：

```
你正在看的窗口：[知乎 | B站 | 工作文档]  ← AI 不碰
Hermes 工作窗口 ：[B站视频搜索]           ← AI 只在这里操作
```

具体流程和 CDP 命令参考见 `references/` 目录。

## 注意事项

- 搜索结果的 80%+ 信息直接从搜索页摘要获取，多数情况下不需要点开文章
- 用完后调用 `bb.py close` 或 `Target.closeTarget` 清理
- GitHub CodeMirror 6 编辑器注入受限（详见 `references/pitfalls.md`），优先用 `gh` CLI 操作文件
- 截图用 `browser_vision` 获取页面视觉信息，`Page.captureScreenshot` 获取原始截图

## 参考文档

- `references/cdp-cheatsheet.md` — CDP 命令速查表
- `references/pitfalls.md` — 踩坑实录（真实问题+解决方案）