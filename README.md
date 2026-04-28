# Hermes Browser Boss — 使用文档

> **版本：** v2.0.0  
> **定位：** Hermes AI 助手的浏览器自动化 Skill  
> **核心卖点：** 傻瓜式操控，用户只需发话，AI 自动执行浏览器任务

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [功能清单](#功能清单)
4. [架构设计](#架构设计)
5. [使用场景](#使用场景)
6. [隔离窗口模式（重要）](#隔离窗口模式重要)
7. [CDP 命令参考](#cdp-命令参考)
8. [常见问题](#常见问题)
9. [踩坑实录](#踩坑实录)

---

## 概述

Browser Boss 是 Hermes Agent 的内置浏览器操控技能。它让 AI 能够像人一样操作你的本地浏览器——搜索、打开网页、填表、点击、截图，全自动完成。

**核心理念：全自动，零手动。** 你只需要说"帮我搜一下xxx"，剩下的事情 Hermes 全部搞定。

### 它不是什么

- ❌ 不是爬虫框架
- ❌ 不是浏览器自动化测试工具（虽然底层用了 CDP）
- ❌ 不需要你写代码

### 它是什么

- ✅ 一个**自然语言驱动的浏览器遥控器**
- ✅ AI 自动判断用哪个工具、怎么操作
- ✅ 支持可视化（在用户眼前操作）和 Headless（后台静默）双模式

---

## 快速开始

### Step 1：确保 Edge 开启了 CDP 调试端口

在你的 Windows 上，用以下方式启动 Edge：

```powershell
# 关闭所有 Edge 窗口，然后：
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9224
```

或者让 Hermes 自动启动（推荐）：

```bash
# WSL 内
cd /root/workspace/scripts
python3 bb.py status    # 检查 CDP 是否在线
python3 bb.py open "https://www.baidu.com"  # 如果不在线，自动启动
```

### Step 2：对 Hermes 发话

```
"帮我搜一下蜡笔小新动漫在线观看"
"打开 bilibili.com，搜海绵宝宝第一季第一集，播放"
"把这个页面的内容提取出来"
```

就这么简单。

---

## 功能清单

| 功能 | 你这么说 | Hermes 做的事 |
|------|---------|--------------|
| 🔍 搜索 | "搜一下xxx" | 自动选择 Bing/头条/Google，提取搜索结果 |
| 🌐 打开网页 | "打开xxx.com" | 导航到目标 URL |
| 👆 点击 | "点那个xxx按钮" | 定位元素并点击 |
| ⌨️ 填表 | "帮我在邮箱框填xxx" | 定位输入框并填入内容 |
| 📸 截图 | "给我截个图" | 截取当前页面 |
| 📋 提取 | "把页面内容提取出来" | 获取页面文本 |
| 📦 批量 | "批量搜这几个关键词" | 依次执行多个搜索 |
| 🎬 播放控制 | "播放/暂停/全屏" | 操作 video 元素 |
| 🔒 隔离模式 | （自动） | 新窗口操作，不影响用户 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│                     用户发话                          │
│          "帮我搜一下蜡笔小新"                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 Hermes Agent (AI)                    │
│                                                      │
│  1. 加载 browser-boss skill                         │
│  2. 判断任务类型（搜索？填表？截图？）                 │
│  3. 选择工具链（CDP？Headless？bb.py？）             │
│  4. 执行操作                                         │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │  bb.py   │ │ CDP 直连 │ │ Headless │
   │ (统一入口)│ │(Edge 9224)│ │(agent-   │
   │          │ │          │ │ browser) │
   └────┬─────┘ └────┬─────┘ └────┬─────┘
        │            │            │
        ▼            ▼            ▼
   ┌─────────────────────────────────────┐
   │        Windows Edge 浏览器           │
   │        127.0.0.1:9224 (CDP)          │
   │  ┌─────────┐  ┌──────────────────┐  │
   │  │ 用户窗口 │  │  Hermes 工作窗口  │  │
   │  │ (不碰)   │  │  (独立隔离)      │  │
   │  └─────────┘  └──────────────────┘  │
   └─────────────────────────────────────┘
```

### 三层工具架构

| 层级 | 工具 | 用途 | target_id |
|------|------|------|-----------|
| **高层** | `browser_navigate`, `browser_click`, `browser_console` 等 | 简单任务、单标签页 | ❌ 不支持 |
| **中层** | `bb.py` (Python 统一入口) | 搜索、打开、填表、批处理 | ❌ 不支持 |
| **底层** | `browser_cdp` (CDP 原生协议) | **隔离窗口模式专用** | ✅ 支持 |

---

## 使用场景

### 场景 1：日常搜索

```
用户：帮我搜一下最近有什么好看的动漫
```

Hermes 自动：
1. 打开 Bing 搜索
2. 提取搜索结果摘要
3. 整理成列表返回给用户

### 场景 2：打开指定网站并交互

```
用户：打开 B站，搜海绵宝宝第一季第一集，播放
```

Hermes 自动：
1. 创建独立窗口
2. 导航到 B站搜索
3. 提取第一个结果的链接
4. 导航到视频页
5. 点击播放 + 全屏

### 场景 3：数据提取

```
用户：把这个页面的所有文章标题和链接提取出来
```

Hermes 自动：
1. 在目标页面执行 `document.body.innerText`
2. 或用选择器提取特定元素
3. 整理成结构化数据返回

### 场景 4：批量任务

```
用户：帮我搜这5个关键词，把结果汇总
```

Hermes 自动：
1. 依次搜索每个关键词
2. 收集结果
3. 汇总输出

---

## 隔离窗口模式（重要）

### 问题背景

在 WSL2 镜像网络模式下，Hermes 连接的是你**正在使用的 Edge 浏览器**。如果你和 Hermes 同时操作，会产生冲突：

- `browser_navigate` 会覆盖你正在看的页面
- `browser_click` 会在你正在用的标签页里点击
- 你切回自己窗口时，Hermes 会在你的窗口里操作

### 解决方案

Hermes **创建独立新窗口**，在自己窗口里操作，完全隔离。

### 操作流程

```
1. Target.createTarget({newWindow: true})  → 弹出新窗口，拿到 target_id
2. Page.navigate("URL", target_id)          → 在新窗口导航
3. Runtime.evaluate("JS代码", target_id)    → 在新窗口执行操作
4. Target.closeTarget(target_id)            → 清理
```

### ⚠️ 关键规则

**隔离模式下，禁止使用以下高层工具：**

| 禁止 ❌ | 原因 | 替代 ✅ |
|---------|------|--------|
| `browser_navigate` | 跳到用户标签页 | `browser_cdp(Page.navigate, target_id=xxx)` |
| `browser_click` | 在错误标签页点击 | `browser_cdp(Runtime.evaluate, ".click()")` |
| `browser_snapshot` | 返回错误标签页 DOM | `browser_cdp(Runtime.evaluate)` |
| `browser_console` | 在错误标签页执行 JS | `browser_cdp(Runtime.evaluate, target_id=xxx)` |
| `browser_type` | 在错误标签页输入 | `browser_cdp(Runtime.evaluate, ".value =")` |
| `browser_scroll` | 滚动错误标签页 | `browser_cdp(Runtime.evaluate, "scrollTo()")` |
| `browser_press` | 按键发到错误标签页 | `browser_cdp(Runtime.evaluate)` |
| `browser_get_images` | 返回错误标签页图片 | `browser_cdp(Runtime.evaluate)` |

---

## CDP 命令参考

### 核心 CDP 方法

| 操作 | CDP Method | 关键参数 |
|------|-----------|---------|
| 创建窗口 | `Target.createTarget` | `{"newWindow": true, "url": "about:blank"}` |
| 列出标签页 | `Target.getTargets` | `{}` |
| 关闭标签页 | `Target.closeTarget` | `{"targetId": "xxx"}` |
| 导航 | `Page.navigate` | `{"url": "https://..."}` |
| 执行 JS | `Runtime.evaluate` | `{"expression": "...", "returnByValue": true}` |
| 截图 | `Page.captureScreenshot` | `{"format": "png"}` |
| 获取版本 | `Browser.getVersion` | `{}` |
| 处理弹窗 | `Page.handleJavaScriptDialog` | `{"accept": true/false}` |

### 常用 JS 表达式

```javascript
// 读标题和 URL
document.title + ' | ' + location.href

// 提取页面全部文本（前5000字符）
document.body.innerText.substring(0, 5000)

// 提取特定标签的链接
Array.from(document.querySelectorAll('a[href*="目标"]')).map(a => ({text: a.textContent, href: a.href}))

// 点击元素
document.querySelector('button.xxx').click()

// 填表
document.querySelector('input[name="email"]').value = 'test@test.com'

// 播放视频
document.querySelector('video').play()

// 暂停
document.querySelector('video').pause()

// 检查视频状态
document.querySelector('video').paused   // true=暂停, false=播放中

// 全屏
document.querySelector('video').requestFullscreen()

// 滚动
window.scrollTo(0, 1000)
```

### 典型调用格式

```python
# 1. 创建窗口
result = browser_cdp(
    method="Target.createTarget",
    params={"newWindow": True, "url": "about:blank"}
)
tid = result["result"]["targetId"]

# 2. 导航
browser_cdp(
    method="Page.navigate",
    params={"url": "https://目标URL"},
    target_id=tid
)

# 3. 执行操作
browser_cdp(
    method="Runtime.evaluate",
    params={
        "expression": "document.querySelector('video').play()",
        "returnByValue": True
    },
    target_id=tid
)

# 4. 关闭
browser_cdp(
    method="Target.closeTarget",
    params={"targetId": tid}
)
```

---

## 常见问题

### Q：Hermes 操作时会覆盖我正在看的页面吗？

**不会。** Hermes 使用隔离窗口模式，创建独立的 Edge 窗口，在你原来的窗口之外操作。你现在在看什么，完全不受影响。

### Q：为什么有时候 Hermes 会跳到我的页面里？

这通常是因为在隔离模式完善之前，高层工具（`browser_navigate` 等）没有 target_id 参数，无法精确指定目标窗口。**v2.0.0 已修复此问题**，隔离模式下全程使用 CDP 命令 + target_id。

### Q：我需要安装什么吗？

不需要安装额外的浏览器插件或驱动。只需要：
- Windows 上有 Edge 浏览器
- Edge 开启了 CDP 调试端口（9224）
- Hermes 配置中指定了 `browser.cdp_url: http://127.0.0.1:9224`

### Q：支持 Chrome 吗？

支持。将端口改为 Chrome 的调试端口即可。Edge 和 Chrome 共享 Chromium 内核，CDP 协议完全兼容。

### Q：Hermes 能看到我的密码吗？

Hermes 操作浏览器时，能获取到页面上你输入的内容。**如果你在 Hermes 操作的标签页中输入敏感信息，AI 可以看到。** 建议：
- 让 Hermes 使用独立窗口
- 不在 Hermes 工作窗口里输入密码
- 敏感操作在自己窗口完成

### Q：操作完成后浏览器窗口会关吗？

Hermes 会关闭自己创建的工作标签页，但**不会关闭你的浏览器**。

---

## 踩坑实录

这些是开发和使用过程中遇到的真实问题，记录在此供参考。

### 坑 1：高层工具无 target_id（2026-04-28）

**现象：** 创建独立窗口后，用 `browser_navigate` 导航，结果跳到了用户的活跃标签页。

**原因：** `browser_navigate`、`browser_click`、`browser_console` 等工具没有 `target_id` 参数，自动选择"当前活跃标签页"。如果用户此时切回自己窗口，就会操作到用户窗口。

**解决：** 隔离模式下禁用所有高层工具，全部改用 `browser_cdp(method=..., params=..., target_id=...)`。

### 坑 2：验证码识别（2026-04-28）

**现象：** 注册页面有验证码，`vision_analyze` 无法直接从 URL 读取（需要 Cookie），放大后的 base64 又太长导致文件名超限。

**解决：** 
1. 用 `Runtime.evaluate` 在页面上把验证码 img 通过 Canvas 转 base64
2. 保存为临时文件
3. 用 `tesseract OCR` 识别（需要安装 `tesseract-ocr`）

### 坑 3：Bing 返回空白页

**现象：** 在 WSL 内 curl 或直接访问 Bing，经常返回空白或只有搜索框。

**解决：** 通过 CDP 连接的 Edge 浏览器访问（Edge 有完整的浏览器环境和 Cookie），不走 curl。

### 坑 4：WSL2 镜像网络的端口变化

**现象：** `networkingMode=mirrored` 下，localhost 共享，但某些端口映射行为不同。

**解决：** 使用 `127.0.0.1` 明确指定，不依赖 DNS 解析。

---

## 环境信息

| 项目 | 值 |
|------|-----|
| 操作系统 | Windows 11 + WSL2 |
| 网络模式 | `networkingMode=mirrored` |
| 浏览器 | Microsoft Edge (Chromium) |
| CDP 端口 | `127.0.0.1:9224` |
| bb.py | `/root/workspace/scripts/bb.py` |
| agent-browser | `/usr/bin/agent-browser` (v0.26.0) |
| Python | Python 3 (WSL 内) |

---

## 更新日志

### v2.0.0 (2026-04-28)

- ✅ 新增隔离窗口模式（CDP + target_id）
- ✅ 完整禁止使用清单（8个高层工具）
- ✅ 踩坑实录文档化
- ✅ 全屏播放支持
- ✅ 验证码 OCR 识别流程

### v1.0.0

- 初始版本
- 基础搜索/导航/点击功能
- bb.py 统一入口
- 桥接模式支持

---

> **License:** MIT  
> **维护者:** Hermes Agent + 用户  
> **反馈:** 直接在 Hermes 对话中提 issue-style 的问题即可
