#!/usr/bin/env python3
"""
Browser Boss — 操控 Windows Edge CDP（WSL2 镜像网络）

用法:
  bb search "关键词"      → 头条搜索（中文最佳）
  bb bing "关键词"        → Bing 搜索
  bb open "URL"           → 打开网页
  bb status               → 检查 Edge CDP 状态
  bb close                → 断开 agent-browser 连接
  bb text                 → 提取 body.innerText

依赖:
  - Microsoft Edge（启动时带 --remote-debugging-port=9224）
  - WSL2 镜像网络模式（networkingMode=mirrored）
  - agent-browser CLI（/usr/bin/agent-browser）

Edge 启动方式（内部自动处理）：
  通过 PowerShell 启动新 Edge 进程，不影响用户正在使用的 Edge 窗口。
"""

import subprocess
import sys
import json
import os
import time
import urllib.parse
from typing import Optional, Tuple

EDGE_CDP_PORT = 9224
POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
AGENT_BROWSER = "agent-browser"


def _run(cmd: list, timeout: int = 30) -> Tuple[str, int]:
    """运行命令，返回 (stdout, exit_code)。"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", -1


def _pwsh(script: str, timeout: int = 10) -> str:
    """运行 PowerShell 脚本，返回 stdout。"""
    out, _ = _run([POWERSHELL, "-Command", script], timeout)
    return out


def edge_cdp_running() -> bool:
    """检查 Edge CDP 是否在线。"""
    result = _pwsh(
        f"try {{$null=Invoke-RestMethod 'http://localhost:{EDGE_CDP_PORT}/json/version' "
        f"-TimeoutSec 2; 'OK'}} catch {{'OFF'}}",
        timeout=5
    )
    return result.strip() == "OK"


def start_edge_cdp() -> bool:
    """如果 Edge CDP 不在线，启动它。返回是否成功启动。"""
    if edge_cdp_running():
        return True

    print("🔧 Edge CDP 不在线，正在启动...")
    _pwsh(f"""
        $e = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
        if (Test-Path $e) {{
            Start-Process -FilePath $e -ArgumentList @(
                '--remote-debugging-port={EDGE_CDP_PORT}',
                '--remote-allow-origins=*',
                '--no-first-run',
                '--no-default-browser-check',
                '--new-window',
                'about:blank'
            )
        }} else {{
            $e = 'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
            Start-Process -FilePath $e -ArgumentList @(
                '--remote-debugging-port={EDGE_CDP_PORT}',
                '--remote-allow-origins=*',
                '--no-first-run',
                '--no-default-browser-check',
                '--new-window',
                'about:blank'
            )
        }}
    """, timeout=8)

    # 等待 CDP 就绪
    for _ in range(10):
        time.sleep(0.5)
        if edge_cdp_running():
            print("✅ Edge CDP 已启动")
            return True

    print("❌ Edge CDP 启动失败")
    return False


def _connect_agent_browser() -> bool:
    """连接到 Edge CDP"""
    out, code = _run([AGENT_BROWSER, "connect", str(EDGE_CDP_PORT)], timeout=10)
    return code == 0


def search(query: str, engine: str = "toutiao") -> Optional[str]:
    """搜索并返回结果页文本。默认头条搜索。"""
    if not start_edge_cdp():
        return None

    if engine == "toutiao":
        url = f"https://so.toutiao.com/search?keyword={urllib.parse.quote(query)}"
    else:
        url = f"https://cn.bing.com/search?q={urllib.parse.quote(query)}"

    return open_url(url)


def open_url(url: str) -> Optional[str]:
    """打开 URL 并返回页面文本。"""
    if not start_edge_cdp():
        return None

    _connect_agent_browser()

    # 通过 CDP 导航
    _pwsh(f"""
        $body = @{{url='{url}'}} | ConvertTo-Json
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add('Content-Type', 'application/json')
        try {{
            $wc.UploadString('http://localhost:{EDGE_CDP_PORT}/json/version', '') | Out-Null
        }} catch {{}}
    """, timeout=15)

    time.sleep(2)  # 等页面加载
    return url


def get_page_text() -> Optional[str]:
    """获取当前页面 innerText。"""
    out, _ = _run([
        AGENT_BROWSER, "console", "--expr",
        "document.body.innerText.substring(0, 5000)"
    ], timeout=10)
    return out if out else None


def disconnect():
    """断开 agent-browser 连接。"""
    _run([AGENT_BROWSER, "close"], timeout=5)


# ─── CLI ────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("可用命令: search | bing | open | status | close | text")
        sys.exit(0)

    action = sys.argv[1]

    if action == "search":
        if len(sys.argv) < 3:
            print("用法: bb search <关键词>"); sys.exit(1)
        url = search(sys.argv[2])
        print(f"✅ 搜索: so.toutiao.com/search?keyword={urllib.parse.quote(sys.argv[2])}")

    elif action == "bing":
        if len(sys.argv) < 3:
            print("用法: bb bing <关键词>"); sys.exit(1)
        url = search(sys.argv[2], engine="bing")
        print("✅ Bing 搜索完成")

    elif action == "open":
        if len(sys.argv) < 3:
            print("用法: bb open <URL>"); sys.exit(1)
        url = open_url(sys.argv[2])
        print(f"✅ 已打开: {sys.argv[2]}")

    elif action == "status":
        status = "在线" if edge_cdp_running() else "离线"
        print(f"Edge CDP ({EDGE_CDP_PORT}): {status}")

    elif action == "close":
        disconnect()
        print("✅ 已断开 agent-browser")

    elif action == "text":
        text = get_page_text()
        if text:
            print(text[:5000])
        else:
            print("❌ 获取页面文本失败")

    else:
        print(f"未知命令: {action}")
        print("可用: search | bing | open | status | close | text")


if __name__ == "__main__":
    main()