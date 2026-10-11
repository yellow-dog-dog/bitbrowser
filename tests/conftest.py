"""Shared fixtures for bitbrowser tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from bitbrowser import AsyncBitBrowserClient, BitBrowserClient

# ---------------------------------------------------------------------------
# Async client fixture — no real HTTP; request() is an AsyncMock
# ---------------------------------------------------------------------------


@pytest.fixture
def async_client() -> AsyncBitBrowserClient:
    """Return an AsyncBitBrowserClient whose ``request`` method is an AsyncMock."""
    client = AsyncBitBrowserClient.__new__(AsyncBitBrowserClient)
    client._base_url = "http://127.0.0.1:54345"
    client._timeout = 30.0
    client._httpx_kwargs = {}
    client._http = MagicMock()  # not None so request() won't raise RuntimeError

    from bitbrowser.browsers import AsyncBrowsersService

    client.browsers = AsyncBrowsersService(client)
    client.request = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Sync client fixture — no real HTTP; request() is a MagicMock
# ---------------------------------------------------------------------------


@pytest.fixture
def sync_client() -> BitBrowserClient:
    """Return a BitBrowserClient whose ``request`` method is a MagicMock."""
    client = BitBrowserClient.__new__(BitBrowserClient)
    client._base_url = "http://127.0.0.1:54345"
    client._timeout = 30.0
    client._httpx_kwargs = {}
    client._http = MagicMock()  # not None

    from bitbrowser.browsers import SyncBrowsersService

    client.browsers = SyncBrowsersService(client)
    client.request = MagicMock()
    return client


# ---------------------------------------------------------------------------
# Canonical API payloads reused across tests
# ---------------------------------------------------------------------------


OPEN_RESULT_DATA = {
    "ws": "ws://127.0.0.1:9222/devtools/browser/abc",
    "http": "127.0.0.1:9222",
    "coreVersion": "130",
    "driver": "/path/to/chromedriver",
    "seq": 1,
    "name": "my-window",
    "remark": "note",
    "groupId": "grp-1",
    "pid": 12345,
}

BROWSER_DATA = {
    "id": "br-123",
    "name": "test-browser",
    "groupId": "grp-1",
    "seq": 2,
    "proxyType": "socks5",
    "host": "1.2.3.4",
    "port": 1080,
    "browserFingerPrint": {
        "coreVersion": "130",
        "ostype": "PC",
        "os": "Win32",
    },
}
