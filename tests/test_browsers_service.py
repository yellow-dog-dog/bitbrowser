"""Tests for bitbrowser.browsers — both Async and Sync services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from bitbrowser.browsers import AsyncBrowsersService, SyncBrowsersService
from bitbrowser.models import Browser, BrowserFingerPrint, ListBrowsersResponse, OpenResult
from .conftest import BROWSER_DATA, OPEN_RESULT_DATA


# ===========================================================================
# Helpers
# ===========================================================================


def _make_async_service() -> tuple[AsyncBrowsersService, AsyncMock]:
    mock_client = MagicMock()
    mock_client.request = AsyncMock()
    svc = AsyncBrowsersService(mock_client)
    return svc, mock_client.request


def _make_sync_service() -> tuple[SyncBrowsersService, MagicMock]:
    mock_client = MagicMock()
    svc = SyncBrowsersService(mock_client)
    return svc, mock_client.request


def _ok(data=None) -> dict:
    return {"success": True, "data": data or {}}


# ===========================================================================
# AsyncBrowsersService
# ===========================================================================


class TestAsyncCreate:
    @pytest.mark.asyncio
    async def test_create_returns_browser_with_id(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"id": "br-new", "groupId": "grp-1"})
        b = Browser(browser_finger_print=BrowserFingerPrint(core_version="130"))
        result = await svc.create(b)
        assert result.id == "br-new"
        assert result.group_id == "grp-1"

    @pytest.mark.asyncio
    async def test_create_raises_if_no_finger_print(self):
        svc, _ = _make_async_service()
        with pytest.raises(ValueError, match="browser_finger_print"):
            await svc.create(Browser())

    @pytest.mark.asyncio
    async def test_create_strips_id_from_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"id": "br-new"})
        b = Browser(id="old-id", browser_finger_print=BrowserFingerPrint())
        await svc.create(b)
        body = req.call_args[0][1]
        assert "id" not in body

    @pytest.mark.asyncio
    async def test_create_posts_to_correct_path(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"id": "x"})
        await svc.create(Browser(browser_finger_print=BrowserFingerPrint()))
        assert req.call_args[0][0] == "/browser/update"

    @pytest.mark.asyncio
    async def test_create_falls_back_to_browser_group_id(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"id": "br-1"})
        b = Browser(group_id="my-grp", browser_finger_print=BrowserFingerPrint())
        result = await svc.create(b)
        assert result.group_id == "my-grp"


class TestAsyncGet:
    @pytest.mark.asyncio
    async def test_get_returns_browser(self):
        svc, req = _make_async_service()
        req.return_value = _ok(BROWSER_DATA)
        result = await svc.get("br-123")
        assert result.id == "br-123"
        assert result.name == "test-browser"

    @pytest.mark.asyncio
    async def test_get_posts_correct_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok(BROWSER_DATA)
        await svc.get("br-123")
        req.assert_called_once_with("/browser/detail", {"id": "br-123"})

    @pytest.mark.asyncio
    async def test_get_parses_nested_finger_print(self):
        svc, req = _make_async_service()
        req.return_value = _ok(BROWSER_DATA)
        result = await svc.get("br-123")
        assert isinstance(result.browser_finger_print, BrowserFingerPrint)
        assert result.browser_finger_print.core_version == "130"


class TestAsyncList:
    @pytest.mark.asyncio
    async def test_list_returns_response(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"list": [BROWSER_DATA], "total": 1})
        resp = await svc.list()
        assert isinstance(resp, ListBrowsersResponse)
        assert resp.total == 1
        assert len(resp.browsers) == 1

    @pytest.mark.asyncio
    async def test_list_default_pagination(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"list": [], "total": 0})
        await svc.list()
        body = req.call_args[0][1]
        assert body["page"] == 0
        assert body["pageSize"] == 10

    @pytest.mark.asyncio
    async def test_list_with_filters(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"list": [], "total": 0})
        await svc.list(page=2, page_size=5, group_id="grp-1", name="test", sort="asc")
        body = req.call_args[0][1]
        assert body["page"] == 2
        assert body["pageSize"] == 5
        assert body["groupId"] == "grp-1"
        assert body["name"] == "test"
        assert body["sort"] == "asc"

    @pytest.mark.asyncio
    async def test_list_optional_filters_not_sent_when_none(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"list": [], "total": 0})
        await svc.list()
        body = req.call_args[0][1]
        assert "groupId" not in body
        assert "name" not in body

    @pytest.mark.asyncio
    async def test_list_seq_range_filters(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"list": [], "total": 0})
        await svc.list(min_seq=1, max_seq=50)
        body = req.call_args[0][1]
        assert body["minSeq"] == 1
        assert body["maxSeq"] == 50

    @pytest.mark.asyncio
    async def test_list_total_falls_back_to_len(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"list": [BROWSER_DATA]})
        resp = await svc.list()
        assert resp.total == 1


class TestAsyncUpdate:
    @pytest.mark.asyncio
    async def test_update_raises_if_no_id(self):
        svc, _ = _make_async_service()
        with pytest.raises(ValueError, match="browser.id"):
            await svc.update(Browser(name="x"))

    @pytest.mark.asyncio
    async def test_update_posts_correct_path(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.update(Browser(id="br-1", name="new-name"))
        assert req.call_args[0][0] == "/browser/update"

    @pytest.mark.asyncio
    async def test_update_includes_id_in_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.update(Browser(id="br-1", name="x"))
        body = req.call_args[0][1]
        assert body["id"] == "br-1"


class TestAsyncBatchUpdate:
    @pytest.mark.asyncio
    async def test_batch_update_raises_if_empty_ids(self):
        svc, _ = _make_async_service()
        with pytest.raises(ValueError, match="ids must not be empty"):
            await svc.batch_update([])

    @pytest.mark.asyncio
    async def test_batch_update_posts_ids(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.batch_update(["br-1", "br-2"])
        body = req.call_args[0][1]
        assert body["ids"] == ["br-1", "br-2"]

    @pytest.mark.asyncio
    async def test_batch_update_with_browser_object(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        b = Browser(id="should-be-stripped", name="bulk")
        await svc.batch_update(["br-1"], browser=b)
        body = req.call_args[0][1]
        assert body["name"] == "bulk"
        assert "id" not in body

    @pytest.mark.asyncio
    async def test_batch_update_with_extra_fields(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.batch_update(["br-1"], abortImage=True)
        body = req.call_args[0][1]
        assert body["abortImage"] is True


class TestAsyncDelete:
    @pytest.mark.asyncio
    async def test_delete_posts_correct_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.delete("br-1")
        req.assert_called_once_with("/browser/delete", {"id": "br-1"})

    @pytest.mark.asyncio
    async def test_batch_delete_raises_if_empty(self):
        svc, _ = _make_async_service()
        with pytest.raises(ValueError, match="ids must not be empty"):
            await svc.batch_delete([])

    @pytest.mark.asyncio
    async def test_batch_delete_posts_ids(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.batch_delete(["br-1", "br-2"])
        body = req.call_args[0][1]
        assert body["ids"] == ["br-1", "br-2"]


class TestAsyncOpen:
    @pytest.mark.asyncio
    async def test_open_returns_open_result(self):
        svc, req = _make_async_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        result = await svc.open("br-1")
        assert isinstance(result, OpenResult)
        assert result.ws == OPEN_RESULT_DATA["ws"]

    @pytest.mark.asyncio
    async def test_open_default_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        await svc.open("br-1")
        body = req.call_args[0][1]
        assert body["id"] == "br-1"
        assert body["args"] == []
        assert body["queue"] is False

    @pytest.mark.asyncio
    async def test_open_with_queue(self):
        svc, req = _make_async_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        await svc.open("br-1", queue=True)
        assert req.call_args[0][1]["queue"] is True

    @pytest.mark.asyncio
    async def test_open_with_ignore_default_urls(self):
        svc, req = _make_async_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        await svc.open("br-1", ignore_default_urls=True)
        assert req.call_args[0][1]["ignoreDefaultUrls"] is True

    @pytest.mark.asyncio
    async def test_open_with_new_page_url(self):
        svc, req = _make_async_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        await svc.open("br-1", new_page_url="https://example.com")
        assert req.call_args[0][1]["newPageUrl"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_open_new_page_url_absent_by_default(self):
        svc, req = _make_async_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        await svc.open("br-1")
        assert "newPageUrl" not in req.call_args[0][1]

    @pytest.mark.asyncio
    async def test_open_with_args(self):
        svc, req = _make_async_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        await svc.open("br-1", args=["--headless"])
        assert req.call_args[0][1]["args"] == ["--headless"]


class TestAsyncClose:
    @pytest.mark.asyncio
    async def test_close_posts_correct_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.close("br-1")
        req.assert_called_once_with("/browser/close", {"id": "br-1"})

    @pytest.mark.asyncio
    async def test_close_all_posts_to_correct_path(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.close_all()
        req.assert_called_once_with("/browser/close/all")

    @pytest.mark.asyncio
    async def test_reset_close_state(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.reset_close_state("br-1")
        req.assert_called_once_with("/browser/closing/reset", {"id": "br-1"})


class TestAsyncUpdateProxy:
    @pytest.mark.asyncio
    async def test_raises_if_empty_ids(self):
        svc, _ = _make_async_service()
        with pytest.raises(ValueError, match="ids must not be empty"):
            await svc.update_proxy(
                [], proxy_method=2, proxy_type="http", host="x", port=80
            )

    @pytest.mark.asyncio
    async def test_required_fields_in_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.update_proxy(
            ["br-1"],
            proxy_method=2,
            proxy_type="socks5",
            host="1.2.3.4",
            port=1080,
        )
        body = req.call_args[0][1]
        assert body["ids"] == ["br-1"]
        assert body["proxyMethod"] == 2
        assert body["proxyType"] == "socks5"
        assert body["host"] == "1.2.3.4"
        assert body["port"] == 1080

    @pytest.mark.asyncio
    async def test_optional_refresh_proxy_url(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.update_proxy(
            ["br-1"],
            proxy_method=2,
            proxy_type="http",
            host="x",
            port=80,
            refresh_proxy_url="http://refresh.example.com",
        )
        assert req.call_args[0][1]["refreshProxyUrl"] == "http://refresh.example.com"

    @pytest.mark.asyncio
    async def test_optional_dynamic_ip_fields(self):
        svc, req = _make_async_service()
        req.return_value = _ok()
        await svc.update_proxy(
            ["br-1"],
            proxy_method=3,
            proxy_type="http",
            host="x",
            port=80,
            dynamic_ip_url="http://extract.example.com",
            dynamic_ip_channel="vendor",
            is_dynamic_ip_change_ip=True,
        )
        body = req.call_args[0][1]
        assert body["dynamicIpUrl"] == "http://extract.example.com"
        assert body["dynamicIpChannel"] == "vendor"
        assert body["isDynamicIpChangeIp"] is True


class TestAsyncPids:
    @pytest.mark.asyncio
    async def test_get_pids_raises_if_empty(self):
        svc, _ = _make_async_service()
        with pytest.raises(ValueError):
            await svc.get_pids([])

    @pytest.mark.asyncio
    async def test_get_pids_returns_mapping(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"br-1": 1234})
        result = await svc.get_pids(["br-1"])
        assert result == {"br-1": 1234}

    @pytest.mark.asyncio
    async def test_get_all_pids(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"br-1": 1111, "br-2": 2222})
        result = await svc.get_all_pids()
        assert result["br-2"] == 2222

    @pytest.mark.asyncio
    async def test_get_alive_pids_raises_if_empty(self):
        svc, _ = _make_async_service()
        with pytest.raises(ValueError):
            await svc.get_alive_pids([])

    @pytest.mark.asyncio
    async def test_get_alive_pids_returns_mapping(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"br-1": 9999})
        result = await svc.get_alive_pids(["br-1"])
        assert result == {"br-1": 9999}

    @pytest.mark.asyncio
    async def test_get_pids_returns_empty_dict_on_none_data(self):
        svc, req = _make_async_service()
        req.return_value = {"success": True, "data": None}
        result = await svc.get_pids(["br-1"])
        assert result == {}


class TestAsyncRandomFingerprint:
    @pytest.mark.asyncio
    async def test_returns_browser_finger_print(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"coreVersion": "130", "os": "Win32"})
        result = await svc.random_fingerprint("br-1")
        assert isinstance(result, BrowserFingerPrint)
        assert result.core_version == "130"

    @pytest.mark.asyncio
    async def test_posts_correct_body(self):
        svc, req = _make_async_service()
        req.return_value = _ok({"coreVersion": "130"})
        await svc.random_fingerprint("br-42")
        req.assert_called_once_with(
            "/browser/fingerprint/random", {"browserId": "br-42"}
        )


# ===========================================================================
# SyncBrowsersService — mirrors async tests without async/await
# ===========================================================================


class TestSyncCreate:
    def test_create_returns_browser_with_id(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"id": "br-new", "groupId": "grp-1"})
        result = svc.create(Browser(browser_finger_print=BrowserFingerPrint()))
        assert result.id == "br-new"

    def test_create_raises_if_no_finger_print(self):
        svc, _ = _make_sync_service()
        with pytest.raises(ValueError, match="browser_finger_print"):
            svc.create(Browser())

    def test_create_strips_id_from_body(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"id": "br-new"})
        svc.create(Browser(id="old", browser_finger_print=BrowserFingerPrint()))
        assert "id" not in req.call_args[0][1]


class TestSyncGet:
    def test_get_returns_browser(self):
        svc, req = _make_sync_service()
        req.return_value = _ok(BROWSER_DATA)
        result = svc.get("br-123")
        assert result.id == "br-123"

    def test_get_posts_correct_body(self):
        svc, req = _make_sync_service()
        req.return_value = _ok(BROWSER_DATA)
        svc.get("br-123")
        req.assert_called_once_with("/browser/detail", {"id": "br-123"})


class TestSyncList:
    def test_list_returns_response(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"list": [BROWSER_DATA], "total": 1})
        resp = svc.list()
        assert resp.total == 1
        assert len(resp.browsers) == 1

    def test_list_default_pagination(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"list": [], "total": 0})
        svc.list()
        body = req.call_args[0][1]
        assert body["page"] == 0
        assert body["pageSize"] == 10

    def test_list_with_filters(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"list": [], "total": 0})
        svc.list(page=1, page_size=20, opened=True, owned_by_me=False)
        body = req.call_args[0][1]
        assert body["page"] == 1
        assert body["pageSize"] == 20
        assert body["opened"] is True
        assert body["ownedByMe"] is False


class TestSyncUpdate:
    def test_update_raises_if_no_id(self):
        svc, _ = _make_sync_service()
        with pytest.raises(ValueError, match="browser.id"):
            svc.update(Browser(name="x"))

    def test_update_posts_to_correct_path(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.update(Browser(id="br-1", name="new"))
        assert req.call_args[0][0] == "/browser/update"


class TestSyncBatchUpdate:
    def test_raises_if_empty_ids(self):
        svc, _ = _make_sync_service()
        with pytest.raises(ValueError):
            svc.batch_update([])

    def test_posts_ids(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.batch_update(["br-1"])
        assert req.call_args[0][1]["ids"] == ["br-1"]


class TestSyncDelete:
    def test_delete_posts_correct_body(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.delete("br-1")
        req.assert_called_once_with("/browser/delete", {"id": "br-1"})

    def test_batch_delete_raises_if_empty(self):
        svc, _ = _make_sync_service()
        with pytest.raises(ValueError):
            svc.batch_delete([])

    def test_batch_delete_posts_ids(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.batch_delete(["br-1", "br-2"])
        assert req.call_args[0][1]["ids"] == ["br-1", "br-2"]


class TestSyncOpen:
    def test_open_returns_open_result(self):
        svc, req = _make_sync_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        result = svc.open("br-1")
        assert isinstance(result, OpenResult)
        assert result.ws == OPEN_RESULT_DATA["ws"]

    def test_open_default_body(self):
        svc, req = _make_sync_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        svc.open("br-1")
        body = req.call_args[0][1]
        assert body["id"] == "br-1"
        assert body["args"] == []
        assert body["queue"] is False

    def test_open_with_ignore_default_urls(self):
        svc, req = _make_sync_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        svc.open("br-1", ignore_default_urls=True)
        assert req.call_args[0][1]["ignoreDefaultUrls"] is True

    def test_open_new_page_url_absent_by_default(self):
        svc, req = _make_sync_service()
        req.return_value = _ok(OPEN_RESULT_DATA)
        svc.open("br-1")
        assert "newPageUrl" not in req.call_args[0][1]


class TestSyncClose:
    def test_close_posts_correct_body(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.close("br-1")
        req.assert_called_once_with("/browser/close", {"id": "br-1"})

    def test_close_all(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.close_all()
        req.assert_called_once_with("/browser/close/all")

    def test_reset_close_state(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.reset_close_state("br-1")
        req.assert_called_once_with("/browser/closing/reset", {"id": "br-1"})


class TestSyncUpdateProxy:
    def test_raises_if_empty_ids(self):
        svc, _ = _make_sync_service()
        with pytest.raises(ValueError):
            svc.update_proxy([], proxy_method=2, proxy_type="http", host="x", port=80)

    def test_required_fields_in_body(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.update_proxy(
            ["br-1"],
            proxy_method=2,
            proxy_type="socks5",
            host="1.2.3.4",
            port=1080,
        )
        body = req.call_args[0][1]
        assert body["proxyType"] == "socks5"
        assert body["port"] == 1080

    def test_optional_fields_absent_by_default(self):
        svc, req = _make_sync_service()
        req.return_value = _ok()
        svc.update_proxy(["br-1"], proxy_method=2, proxy_type="http", host="x", port=80)
        body = req.call_args[0][1]
        assert "refreshProxyUrl" not in body
        assert "dynamicIpUrl" not in body


class TestSyncPids:
    def test_get_pids_raises_if_empty(self):
        svc, _ = _make_sync_service()
        with pytest.raises(ValueError):
            svc.get_pids([])

    def test_get_pids_returns_mapping(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"br-1": 1234})
        assert svc.get_pids(["br-1"]) == {"br-1": 1234}

    def test_get_all_pids(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"br-1": 1111})
        assert svc.get_all_pids() == {"br-1": 1111}

    def test_get_alive_pids_raises_if_empty(self):
        svc, _ = _make_sync_service()
        with pytest.raises(ValueError):
            svc.get_alive_pids([])

    def test_get_alive_pids_returns_mapping(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"br-1": 9999})
        assert svc.get_alive_pids(["br-1"]) == {"br-1": 9999}

    def test_get_pids_returns_empty_dict_on_none_data(self):
        svc, req = _make_sync_service()
        req.return_value = {"success": True, "data": None}
        assert svc.get_pids(["br-1"]) == {}


class TestSyncRandomFingerprint:
    def test_returns_browser_finger_print(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"coreVersion": "130"})
        result = svc.random_fingerprint("br-1")
        assert isinstance(result, BrowserFingerPrint)
        assert result.core_version == "130"

    def test_posts_correct_body(self):
        svc, req = _make_sync_service()
        req.return_value = _ok({"coreVersion": "130"})
        svc.random_fingerprint("br-42")
        req.assert_called_once_with(
            "/browser/fingerprint/random", {"browserId": "br-42"}
        )
