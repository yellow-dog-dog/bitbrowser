"""Integration tests — require an isolated BitBrowser API endpoint.

Run with:
    BITBROWSER_TEST_BASE_URL=<isolated-api-url> uv run pytest -m integration -v
"""

from __future__ import annotations

import os
import time

import pytest

from bitbrowser import BitBrowserClient, Browser, BrowserFingerPrint
from bitbrowser.exceptions import ApiError

pytestmark = pytest.mark.integration

# API 需要代理方式字段，noproxy 表示不使用代理
_NO_PROXY = {"proxy_method": 2, "proxy_type": "noproxy"}

# 基础指纹，避免 API 报「请选择代理方式」
_BASE_FP = BrowserFingerPrint(core_version="130", ostype="PC", os="Win32")


def _new_browser(**kwargs) -> Browser:
    return Browser(browser_finger_print=_BASE_FP, **_NO_PROXY, **kwargs)


@pytest.fixture(scope="module")
def client():
    base_url = os.environ.get("BITBROWSER_TEST_BASE_URL")
    if not base_url:
        pytest.skip(
            "Set BITBROWSER_TEST_BASE_URL to an isolated BitBrowser API "
            "before running integration tests."
        )
    with BitBrowserClient(base_url=base_url) as c:
        yield c


@pytest.fixture
def created_browser(client: BitBrowserClient):
    """Create a browser window for a test, then delete it afterwards."""
    browser = client.browsers.create(_new_browser(name="pytest-integration"))
    yield browser
    try:
        client.browsers.delete(browser.id)
    except ApiError:
        pass  # already deleted by the test


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------


def test_health_check(client: BitBrowserClient):
    assert client.health_check() is True


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_create_browser(client: BitBrowserClient):
    browser = client.browsers.create(_new_browser())
    assert browser.id is not None
    client.browsers.delete(browser.id)


def test_get_browser(client: BitBrowserClient, created_browser: Browser):
    result = client.browsers.get(created_browser.id)
    assert result.id == created_browser.id


def test_list_browsers(client: BitBrowserClient, created_browser: Browser):
    resp = client.browsers.list(page_size=50)
    ids = [b.id for b in resp.browsers]
    assert created_browser.id in ids


def test_update_browser(client: BitBrowserClient, created_browser: Browser):
    # BitBrowser requires proxy_method + browserFingerPrint even for partial updates
    client.browsers.update(
        _new_browser(id=created_browser.id, name="pytest-updated")
    )
    result = client.browsers.get(created_browser.id)
    assert result.name == "pytest-updated"


def test_delete_browser(client: BitBrowserClient):
    browser = client.browsers.create(_new_browser())
    client.browsers.delete(browser.id)
    with pytest.raises(ApiError):
        client.browsers.get(browser.id)


def test_batch_delete(client: BitBrowserClient):
    b1 = client.browsers.create(_new_browser())
    b2 = client.browsers.create(_new_browser())
    client.browsers.batch_delete([b1.id, b2.id])
    with pytest.raises(ApiError):
        client.browsers.get(b1.id)


# ---------------------------------------------------------------------------
# Open / close lifecycle — queue=True 串行化，间隔 2s 避免 429
# ---------------------------------------------------------------------------


def test_open_and_close_browser(client: BitBrowserClient, created_browser: Browser):
    time.sleep(2)
    result = client.browsers.open(created_browser.id, queue=True)
    assert result.ws.startswith("ws://")
    assert result.http != ""
    client.browsers.close(created_browser.id)


def test_open_result_has_pid(client: BitBrowserClient, created_browser: Browser):
    time.sleep(2)
    result = client.browsers.open(created_browser.id, queue=True)
    assert isinstance(result.pid, int)
    assert result.pid > 0
    client.browsers.close(created_browser.id)


# ---------------------------------------------------------------------------
# PID queries
# ---------------------------------------------------------------------------


def test_get_pids_for_open_browser(client: BitBrowserClient, created_browser: Browser):
    time.sleep(2)
    client.browsers.open(created_browser.id, queue=True)
    pids = client.browsers.get_pids([created_browser.id])
    assert created_browser.id in pids
    client.browsers.close(created_browser.id)


def test_get_all_pids_type(client: BitBrowserClient):
    result = client.browsers.get_all_pids()
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------


def test_random_fingerprint(client: BitBrowserClient, created_browser: Browser):
    fp = client.browsers.random_fingerprint(created_browser.id)
    assert isinstance(fp, BrowserFingerPrint)


# ---------------------------------------------------------------------------
# Proxy update
# ---------------------------------------------------------------------------


def test_update_proxy(client: BitBrowserClient, created_browser: Browser):
    client.browsers.update_proxy(
        [created_browser.id],
        proxy_method=2,
        proxy_type="socks5",
        host="1.2.3.4",
        port=1080,
        proxy_user_name="user",
        proxy_password="pass",
    )
    result = client.browsers.get(created_browser.id)
    assert result.proxy_type == "socks5"
    assert result.host == "1.2.3.4"
    assert result.port == 1080
