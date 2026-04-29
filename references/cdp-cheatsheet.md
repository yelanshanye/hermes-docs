# CDP 命令速查表

## 核心 CDP 方法

| 操作 | CDP Method | 关键参数 |
|------|-----------|---------|
| 创建窗口 | `Target.createTarget` | `{"newWindow": true, "url": "about:blank"}` |
| 列出标签页 | `Target.getTargets` | `{}` |
| 关闭标签页 | `Target.closeTarget` | `{"targetId": "xxx"}` |
| 导航 | `Page.navigate` | `{"url": "https://..."}` |
| 执行 JS | `Runtime.evaluate` | `{"expression": "...", "returnByValue": true}` |
| 截图 | `Page.captureScreenshot` | `{"format": "png"}` |
| 获取版本 | `Browser.getVersion` | `{}` |
| 处理弹窗 | `Page.handleJavaScriptDialog` | `{"accept": true/false, "promptText": ""}` |
| 获取所有 Cookie | `Network.getAllCookies` | `{}` |

## 常用 JS 表达式

```javascript
// 读标题和 URL
document.title + ' | ' + location.href

// 提取页面全部文本（前5000字符）
document.body.innerText.substring(0, 5000)

// 提取特定标签的链接
Array.from(document.querySelectorAll('a[href*="目标"]')).map(a => ({
  text: a.textContent, 
  href: a.href
}))

// 点击元素（CSS selector）
document.querySelector('button.submit').click()

// 填表
document.querySelector('input[name="email"]').value = 'test@test.com'

// 触发 input/change 事件（React 表单需要）
const el = document.querySelector('input[name="email"]');
el.value = 'test@test.com';
el.dispatchEvent(new Event('input', {bubbles: true}));

// 播放视频
document.querySelector('video').play()

// 暂停视频
document.querySelector('video').pause()

// 检查视频状态
document.querySelector('video').paused   // true=暂停, false=播放中

// 全屏
document.querySelector('video').requestFullscreen()

// 滚动页面
window.scrollTo(0, 1000)

// 滚动到底部
window.scrollTo(0, document.body.scrollHeight)

// 等待元素出现（Promise）
new Promise(resolve => {
  const check = () => {
    const el = document.querySelector('.target');
    el ? resolve(el) : setTimeout(check, 200);
  };
  check();
});
```

## 典型调用流程

```python
# === 搜索并播放视频 ===

# 1. 创建隔离窗口
result = browser_cdp(
    method="Target.createTarget",
    params={"newWindow": True, "url": "about:blank"}
)
tid = result["result"]["targetId"]

# 2. 搜索
browser_cdp(
    method="Page.navigate",
    params={"url": "https://cn.bing.com/search?q=蜡笔小新"},
    target_id=tid
)

# 3. 提取结果中的第一个视频链接
browser_cdp(
    method="Runtime.evaluate",
    params={"expression": "Array.from(document.querySelectorAll('a')).find(a=>a.href.includes('bilibili')).href", 
            "returnByValue": True},
    target_id=tid
)

# 4. 打开视频页
browser_cdp(
    method="Page.navigate",
    params={"url": "https://目标视频URL"},
    target_id=tid
)

# 5. 播放视频
browser_cdp(
    method="Runtime.evaluate",
    params={"expression": "document.querySelector('video').play()", 
            "returnByValue": True},
    target_id=tid
)

# 6. 清理
browser_cdp(
    method="Target.closeTarget",
    params={"targetId": tid}
)
```

## 禁止使用的高层工具（隔离模式下）

Hermes 内置的以下工具缺少 `target_id` 参数，会自动选择"当前活跃标签页"，隔离模式下禁止使用：

| 禁止 ❌ | CDP 替代方案 |
|---------|------------|
| `browser_navigate` | `Page.navigate` + target_id |
| `browser_click` | `Runtime.evaluate` + `.click()` |
| `browser_snapshot` | `Runtime.evaluate` + DOM 查询 |
| `browser_console` | `Runtime.evaluate` + target_id |
| `browser_type` | `Runtime.evaluate` + `.value =` + dispatchEvent |
| `browser_scroll` | `Runtime.evaluate` + `window.scrollTo()` |
| `browser_press` | `Runtime.evaluate` + 手动触发事件 |
| `browser_get_images` | `Runtime.evaluate` + img 提取 |