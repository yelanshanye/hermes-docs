# 踩坑实录

这些是开发和实际使用中遇到的真问题。每个坑都记录了现象、原因、解决方案。

---

## 坑 1：高层工具无 target_id（2026-04-28）

**现象：** 创建独立窗口后，用 `browser_navigate` 导航，结果跳到了用户正在看的标签页。

**原因：** `browser_navigate`、`browser_click` 等 Hermes 内置浏览器工具没有 `target_id` 参数，它们自动选择"当前活跃标签页"。如果用户在 AI 操作期间手动切回自己窗口，操作就会发生在用户窗口。

**解决：** 隔离模式下禁用所有高层工具，全部改用 `browser_cdp(method=..., params=..., target_id=...)`。

---

## 坑 2：Bing 返回空白页

**现象：** 在 WSL 内 curl 或直接访问 Bing，经常返回空白或只有搜索框。

**原因：** BING 有较强的反爬机制，无浏览器环境的请求会被拦截。

**解决：**
- 通过 CDP 连接的 Edge 浏览器访问（Edge 有完整的浏览器环境和 Cookie）
- 优先使用**头条搜索**（so.toutiao.com），不对 Cookie 敏感，中文结果更丰富

---

## 坑 3：CodeMirror 6 编辑器注入（2026-04-28）

**现象：** 在 GitHub 等使用 CM6 的网站通过 CDP 向编辑器注入内容时，内容不显示或只显示第一行。

**原因：** CM6 不使用传统 textarea，而是通过 Canvas 渲染。直接修改 DOM 不会同步到 React 状态。

**解决：**
- **优先用 `gh` CLI 或 `curl` + GitHub API 操作文件**，不要通过浏览器注入
- 必须通过浏览器时：通过 `cmView.view.dispatch({changes: {from, to, insert}})` 操作，但 CM6 实例不总暴露在全局
- 单次 `Runtime.evaluate` expression 有效载荷约 4700 字符上限，超长内容需分块

---

## 坑 4：验证码识别（2026-04-28）

**现象：** 注册页面有验证码图片，`vision_analyze` 无法直接从 URL 读取（需要 Cookie），放大后的 base64 文件名超限。

**解决：**
1. 用 `Runtime.evaluate` 在页面上把验证码 img 通过 Canvas 转 base64
2. 保存为临时文件
3. 用 `tesseract OCR` 识别（需要 `apt install tesseract-ocr`）

---

## 坑 5：WSL2 镜像网络的 localhost 共享

**现象：** `networkingMode=mirrored` 下，Windows 和 WSL 共享 localhost，但某些边缘场景下端口映射行为不一致。

**解决：** 使用 `127.0.0.1` 明确指定地址，不依赖 DNS 解析或 `localhost` 别名。

---

## 坑 6：Edge CDP 窗口被关闭后 agent-browser 残留

**现象：** `agent-browser close` 后，Edge 窗口仍在。

**行为说明（非 Bug）：**
- `agent-browser close` 只是断开 agent-browser 与 CDP 的连接
- Edge 窗口**不会被关闭**——这是设计如此，避免误杀用户窗口
- 如果你在隔离模式下创建了新窗口，用 `Target.closeTarget` 关闭

---

## 经验总结

1. **能用 CLI/API 就不用浏览器注入** — 更可靠、更快、不依赖 DOM 状态
2. **搜索先用头条** — 中文内容好、反爬弱、不需登录态
3. **交互必须隔离** — 只要涉及点击/填表/滚动，就走 CDP + target_id
4. **提取数据用 innerText** — 比 accessibility snapshot 更完整