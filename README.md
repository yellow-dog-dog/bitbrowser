# bitbrowser

Async/sync Python SDK for the [BitBrowser](https://www.bitbrowser.net/) local
browser-profile API.

- **Async-first** with a synchronous wrapper (`BitBrowserClient`)
- **Pydantic v2** models — snake_case Python ↔ camelCase JSON via alias
- **Typed** end-to-end (PEP 561 `py.typed`-compliant)
- Resource services: `client.browsers`, `client.groups`, `client.tags`
- Built-in retries via `tenacity` for transient transport errors

## Installation

```bash
pip install git+https://github.com/yellow-dog-dog/bitbrowser.git
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add git+https://github.com/yellow-dog-dog/bitbrowser
```

Requires Python 3.12+ and a running BitBrowser client on the local machine
(default API at `http://127.0.0.1:54345`).

## Quick start (async)

```python
import asyncio
from bitbrowser import AsyncBitBrowserClient, Browser, BrowserFingerPrint


async def main() -> None:
    async with AsyncBitBrowserClient() as client:
        browser = await client.browsers.create(
            Browser(
                name="my-window",
                browser_finger_print=BrowserFingerPrint(
                    core_version="130",
                    ostype="PC",
                    os="Win32",
                ),
            )
        )
        result = await client.browsers.open(browser.id)
        print(result.ws)  # ws://127.0.0.1:XXXXX/devtools/browser/...


asyncio.run(main())
```

## Quick start (sync)

```python
from bitbrowser import BitBrowserClient, Browser, BrowserFingerPrint

with BitBrowserClient() as client:
    browser = client.browsers.create(
        Browser(browser_finger_print=BrowserFingerPrint())
    )
    result = client.browsers.open(browser.id, queue=True)
    print(result.ws)
```

## Driving Playwright over CDP

```python
import asyncio
from playwright.async_api import async_playwright
from bitbrowser import AsyncBitBrowserClient, Browser, BrowserFingerPrint


async def main() -> None:
    async with AsyncBitBrowserClient() as client:
        created = await client.browsers.create(
            Browser(browser_finger_print=BrowserFingerPrint())
        )
        opened = await client.browsers.open(created.id, queue=True)

        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(opened.ws)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://example.com")
            print(await page.title())
            await browser.close()

        await client.browsers.close(created.id)


asyncio.run(main())
```

See `demos/` for more examples.

## API surface

| Service | Methods |
|---------|---------|
| `client.browsers` | `create`, `update`, `open`, `close`, `delete`, `list`, `detail`, `pids` |
| `client.groups` | `add`, `edit`, `delete`, `list`, `detail` |
| `client.tags` | `add`, `edit`, `delete`, `list`, `detail` |

All async services have a sync counterpart with identical signatures.

## Configuration

```python
AsyncBitBrowserClient(
    base_url="http://127.0.0.1:54345",  # default
    timeout=30.0,
    # any extra kwargs are forwarded to httpx.AsyncClient
)
```

## Development

```bash
git clone https://github.com/yellow-dog-dog/bitbrowser
cd bitbrowser
uv sync --extra dev
uv run pytest
```

Integration tests in `tests/test_integration.py` require a running BitBrowser
instance and are skipped by default.

## License

MIT — see [LICENSE](LICENSE).
