# bitbrowser 中文入门

[English](README.md) · [连接排错](#连接排错)

这是比特浏览器本地 API 的 Python SDK，提供同步 `BitBrowserClient` 和异步
`AsyncBitBrowserClient`。SDK 不会安装或启动比特浏览器桌面客户端。

## 安装与准备

- Python **3.12 或 3.13**，以 [pyproject.toml](pyproject.toml) 的 `>=3.12,<3.14` 为准。
- 安装并启动比特浏览器，确认本地 API 服务可用。
- 默认 API 地址是 `http://127.0.0.1:54345`。如果客户端使用其他端口，传入实际的 `base_url`。
- 先在运行 Python 的同一台机器上检查连接。Docker、WSL、远程服务器中的
  `127.0.0.1` 指向各自的运行环境，不一定是安装比特浏览器的主机。

```bash
python -m pip install "git+https://github.com/yellow-dog-dog/bitbrowser.git"
```

在已有的 uv 项目中也可以使用：

```bash
uv add git+https://github.com/yellow-dog-dog/bitbrowser
```

## 第一步：只检查连接

下面的检查不会创建、打开或删除窗口。`health_check()` 向 `/health` 发送 POST；
服务返回 `success: false` 时会抛出 `ApiError`，并非简单返回 `False`。

```python
from bitbrowser import ApiError, BitBrowserClient, TransportError

try:
    with BitBrowserClient(timeout=5.0) as client:
        print("本地 API 可用：", client.health_check())
except TransportError as exc:
    print("HTTP 或网络连接失败：", exc)
except ApiError as exc:
    print("比特浏览器 API 返回失败：", exc.msg)
```

也可以在终端单独验证本地 API，排除 Python 环境问题：

```bash
curl --noproxy "*" --max-time 5 -X POST "http://127.0.0.1:54345/health" -H "Content-Type: application/json" -d "{}"
```

## 第二步：读取已有窗口

分页从 `page=0` 开始，返回对象的窗口列表是 `.browsers`，总数是 `.total`。
读取详情使用 `get(id)`。

```python
from bitbrowser import BitBrowserClient

with BitBrowserClient() as client:
    result = client.browsers.list(page=0, page_size=10)
    print("窗口总数：", result.total)
    for browser in result.browsers:
        print(browser.id, browser.name)
```

## 第三步：创建并打开窗口（异步）

此示例会创建一个新配置并打开窗口，结束时关闭窗口，**保留配置**。
每次运行都会新建配置。`client.close()` 只关闭 SDK 的 HTTP 连接池；
关闭浏览器窗口需要 `client.browsers.close(id)`。不要用 `delete(id)` 代替关闭：
删除配置是永久操作，没有回收站。

```python
import asyncio

from bitbrowser import AsyncBitBrowserClient, Browser, BrowserFingerPrint


async def main() -> None:
    async with AsyncBitBrowserClient() as client:
        created = await client.browsers.create(
            Browser(
                name="sdk-example",
                proxy_method=2,
                proxy_type="noproxy",
                browser_finger_print=BrowserFingerPrint(),
            )
        )
        if not created.id:
            raise RuntimeError("创建响应中没有窗口 ID，请检查 API 返回结果")
        try:
            opened = await client.browsers.open(created.id, queue=True)
            print("CDP WebSocket：", opened.ws)
        finally:
            await client.browsers.close(created.id)


asyncio.run(main())
```

`browser_finger_print` 必须提供；不指定具体指纹值时可传 `BrowserFingerPrint()`。
示例中的无代理配置与仓库的集成测试一致。需要指定内核时，使用本机实际可用的
`core_version`，不要直接复制其他机器的版本号。同步接口使用相同的方法，去掉
`await`，并把 `async with AsyncBitBrowserClient()` 换成 `with BitBrowserClient()`。
在已有事件循环的环境（如 Notebook）中，使用 `await main()`，不要再次调用 `asyncio.run()`。

## 用 Playwright 连接已有窗口

Playwright 是可选依赖，需要单独安装：

```bash
python -m pip install playwright
```

下面连接的是比特浏览器启动的 Chromium 窗口，不调用 `launch()`。
将 `BROWSER_ID` 替换为上一步或窗口列表中的实际 ID。示例会打开该窗口、访问
`https://example.com`，最后关闭该窗口；请使用专门用于测试的配置。

```python
import asyncio

from playwright.async_api import async_playwright

from bitbrowser import AsyncBitBrowserClient

BROWSER_ID = "替换为实际窗口ID"


async def main() -> None:
    async with AsyncBitBrowserClient() as client:
        try:
            opened = await client.browsers.open(BROWSER_ID, queue=True)
            async with async_playwright() as pw:
                browser = await pw.chromium.connect_over_cdp(opened.ws)
                try:
                    if not browser.contexts:
                        raise RuntimeError("CDP 已连接，但没有可用的浏览器上下文")
                    context = browser.contexts[0]
                    page = await context.new_page()
                    await page.goto("https://example.com")
                    print(await page.title())
                finally:
                    await browser.close()
        finally:
            await client.browsers.close(BROWSER_ID)


asyncio.run(main())
```

`base_url` 是 SDK 的本地管理 API 地址；`opened.ws` 是本次打开窗口返回的 CDP
WebSocket 地址。不要把 `http://127.0.0.1:54345` 当成 CDP 地址，也不要复用已关闭
窗口的旧 WebSocket 地址。`opened.http` 是调试地址（`host:port`），不是管理 API。

## 连接排错

按「本地 API → 打开窗口 → CDP」的顺序定位，先让健康检查成功，再运行自动化。

| 现象 | 检查与处理 |
| --- | --- |
| `TransportError` / connection refused | 确认桌面客户端正在运行、本地 API 已可用，核对主机和端口；在运行 Python 的环境里执行上面的 curl。 |
| HTTP 4xx/5xx | SDK 也会将 HTTP 状态错误包装为 `TransportError`。检查错误中的 URL、状态码和服务端日志，确认连接到正确服务。 |
| 连接超时 | 先检查连通性；窗口启动确实较慢时可增大 `timeout`。例如 `BitBrowserClient(timeout=60.0)`，这不会修复错误的地址或端口。 |
| curl 成功，Python 失败 | 核对 Python/虚拟环境与 `base_url`；若本机代理环境变量影响请求，可对本地 API 使用 `trust_env=False`（见下方）。 |
| `ApiError` | 请求已得到 API 响应，但 `success` 为假或缺失。读取 `exc.msg`，核对窗口 ID、代理方式、指纹及本机可用内核。SDK 不自动重试这种业务错误。 |
| `Client is not open` | 使用 `with` / `async with`；若手动管理生命周期，先调用 `client.open()` / `await client.open()`，结束时关闭。 |
| 提示必须提供 `browser_finger_print` | 创建时传入 `Browser(browser_finger_print=BrowserFingerPrint(), ...)`；SDK 会在发请求前校验此字段。 |
| Playwright 连接失败 | 先确认 `browsers.open()` 成功，使用最新的 `opened.ws`，检查该地址在运行 Playwright 的环境中是否可达，并确认使用 Chromium 内核。 |
| JSON 解码错误 / Pydantic `ValidationError` | 检查是否连错服务、响应是否为预期 JSON，以及 API 版本/返回字段。此类解析错误不会包装成 `TransportError` 或自动重试。 |

本地 API 需要绕过环境代理时，可在同步或异步客户端传入 HTTPX 参数：

```python
from bitbrowser import BitBrowserClient

with BitBrowserClient(
    base_url="http://127.0.0.1:54345",
    timeout=30.0,
    trust_env=False,
) as client:
    print(client.health_check())
```

注意：

- 当前实现对 `TransportError` **最多尝试 3 次（包含首次）**，重试间隔为 1 秒、2 秒。
  因此 `timeout=5.0` 不代表整个操作必定在 5 秒内结束。
- 所有请求都经过同一重试逻辑，包括创建等写操作。超时不保证服务端未执行；
  手动重试创建前先检查窗口列表，避免重复创建。
- 关闭窗口后，按源码说明至少等待 5 秒再重新打开或删除，给进程退出留出时间。
- 跨机器连接时，管理 API 和 CDP 两条连接都必须可达。不要直接把本地管理端口或
  CDP 调试端口暴露到公网；优先让 Python 与比特浏览器在同一主机运行。
- SDK 的 DEBUG 日志可能包含请求体。分享排错日志前移除代理密码、Cookie 和其他私人数据。

## 本地开发与验证

```bash
git clone https://github.com/yellow-dog-dog/bitbrowser
cd bitbrowser
uv sync --extra dev
uv run pytest -m "not integration"
```

当前仓库的集成测试只是标记为 `integration`，**并没有默认跳过机制**。
普通 `pytest` 也会收集并运行它们。仅在已准备好本地比特浏览器、测试账号和对应
内核时运行 `uv run pytest -m integration -v`；这些测试会创建、打开、修改并永久
删除测试配置。请先阅读 [tests/test_integration.py](tests/test_integration.py)。

更多示例见 [demos](demos/)，实现见 [_client.py](bitbrowser/_client.py)、
[browsers.py](bitbrowser/browsers.py) 和 [models.py](bitbrowser/models.py)。
