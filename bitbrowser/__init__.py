"""BitBrowser SDK — Python client for the BitBrowser local API.

Exposes both an async client (:class:`AsyncBitBrowserClient`) and a
synchronous client (:class:`BitBrowserClient`).

Quick-start (sync)::

    from bitbrowser import BitBrowserClient, Browser, BrowserFingerPrint

    with BitBrowserClient() as client:
        # Create a Windows Chrome window with a randomised fingerprint
        browser = client.browsers.create(
            Browser(
                name="my-window",
                proxy_type="socks5",
                host="1.2.3.4",
                port=1080,
                proxy_user_name="user",
                proxy_password="pass",
                browser_finger_print=BrowserFingerPrint(
                    core_version="130",
                    ostype="PC",
                    os="Win32",
                ),
            )
        )
        result = client.browsers.open(browser.id, queue=True)
        print(result.ws)   # ws://127.0.0.1:XXXXX/devtools/browser/...

Quick-start (async)::

    import asyncio
    from bitbrowser import AsyncBitBrowserClient, Browser, BrowserFingerPrint

    async def main():
        async with AsyncBitBrowserClient() as client:
            browser = await client.browsers.create(
                Browser(browser_finger_print=BrowserFingerPrint())
            )
            result = await client.browsers.open(browser.id)
            print(result.ws)

    asyncio.run(main())
"""

from ._client import AsyncBitBrowserClient, BitBrowserClient
from .browsers import AsyncBrowsersService, SyncBrowsersService
from .exceptions import ApiError, BitBrowserError, TransportError
from .groups import AsyncGroupsService, SyncGroupsService
from .models import (
    Browser,
    BrowserFingerPrint,
    Group,
    ListBrowsersResponse,
    ListGroupsResponse,
    OpenResult,
    Tag,
)
from .tags import AsyncTagsService, SyncTagsService

__all__ = [
    "ApiError",
    "AsyncBitBrowserClient",
    "AsyncBrowsersService",
    "AsyncGroupsService",
    "AsyncTagsService",
    "BitBrowserClient",
    "BitBrowserError",
    "Browser",
    "BrowserFingerPrint",
    "Group",
    "ListBrowsersResponse",
    "ListGroupsResponse",
    "OpenResult",
    "SyncBrowsersService",
    "SyncGroupsService",
    "SyncTagsService",
    "Tag",
    "TransportError",
]
