# Browser Boss — Hermes 浏览器操控 Skill

> 一句话：把浏览器变成 AI 的遥控玩具。用户用自然语言下指令，AI 自动操控本地 Edge/Chrome。

[![Skill](https://img.shields.io/badge/skill-browser--boss-blue)](https://skills.sh/yelanshanye/hermes-docs)
[![Version](https://img.shields.io/badge/version-2.1.0-green)]()

## 快速开始

### 安装

```bash
npx skills add yelanshanye/hermes-docs@browser-boss
```

或者直接下载 [browser-boss-skill.skill](./browser-boss-skill.skill) 手动安装。

### 使用示例

对 Hermes 说：

- 🔍 **搜索**："帮我搜一下蜡笔小新"
- 🌐 **打开网页**："打开 B站，搜海绵宝宝第一季"
- 🎬 **播放视频**："搜蜡笔小新，找到后播放"
- 📸 **截图**："给我截个图"
- 📋 **提取数据**："把页面文章标题都提取出来"

### 环境要求

| 项目 | 说明 |
|------|------|
| 浏览器 | Microsoft Edge（Chromium），需开启 CDP 调试端口 |
| CDP 端口 | `127.0.0.1:9224` |
| 网络 | WSL2 镜像模式（`networkingMode=mirrored`） |
| agent-browser | v0.26.0+ |
| bb.py | Python 3 统一入口脚本 |

## 功能特性

- ✅ 自然语言驱动，零代码
- ✅ 自动选择最优搜索引擎（头条/Bing）
- ✅ 隔离窗口模式 — AI 操作不影响你正在看的页面
- ✅ 可视化 + Headless 双模式
- ✅ 填表/点击/截图/数据提取 一站式

## 文件结构

```
hermes-docs/
├── SKILL.md                          ← skill 主文件
├── README.md                         ← 本文件
├── browser-boss-skill.skill          ← 分发包（zip 格式）
├── scripts/
│   └── bb.py                         ← 统一入口脚本
└── references/
    ├── cdp-cheatsheet.md             ← CDP 命令速查
    └── pitfalls.md                   ← 踩坑实录
```

## 架构

```
用户发话 → Hermes Agent 加载 browser-boss skill
         → 判断任务类型（搜索/交互/提取）
         → 选择工具链（bb.py / CDP + target_id）
         → 操作 Windows Edge 浏览器
```

### 核心设计决策

**为什么交互必须走 CDP？** Hermes 内置的高层浏览器工具（`browser_navigate` 等）没有 `target_id` 参数，无法精确指定目标窗口。如果用户切回自己窗口，AI 的操作就会误入。因此所有交互式操作全程通过 `browser_cdp(method=..., params=..., target_id=...)` 执行。

## 踩坑实录

见 [references/pitfalls.md](./references/pitfalls.md)，记录了真实使用中遇到的 6 个问题和解决方案，包括：
- 高层工具无 target_id 导致窗口冲突
- Bing 返回空白页
- CodeMirror 6 编辑器注入失败
- 验证码 OCR 识别

## License

MIT
