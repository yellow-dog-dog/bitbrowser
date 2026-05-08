"""Tests for bitbrowser._client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bitbrowser._client import (
    AsyncBitBrowserClient,
    BitBrowserClient,
    _check_response,
)
from bitbrowser.exceptions import ApiError, TransportError


# ===========================================================================
# _check_response helper
# ===========================================================================


class TestCheckResponse:
    def test_success_true_returns_payload(self):
        payload = {"success": True, "data": {"id": "br-1"}}
        result = _check_response(payload)
        assert result is payload

    def test_success_false_raises_api_error(self):
        with pytest.raises(ApiError, match="quota exceeded"):
            _check_response({"success": False, "msg": "quota exceeded"})

    def test_missing_success_raises_api_error(self):
        with pytest.raises(ApiError):
            _check_response({"msg": "something"})

    def test_api_error_uses_msg_field(self):
        with pytest.raises(ApiError) as exc_info:
            _check_response({"success": False, "msg": "not found"})
        assert exc_info.value.msg == "not found"

    def test_missing_msg_uses_unknown_error(self):
        with pytest.raises(ApiError) as exc_info:
            _check_response({"success": False})
        assert exc_info.value.msg == "unknown error"


# ===========================================================================
# AsyncBitBrowserClient
# ===========================================================================


class TestAsyncBitBrowserClientInit:
    def test_default_base_url(self):
        client = AsyncBitBrowserClient()
        assert client._base_url == "http://127.0.0.1:54345"

    def test_trailing_slash_stripped(self):
        client = AsyncBitBrowserClient(base_url="http://127.0.0.1:54345/")
        assert client._base_url == "http://127.0.0.1:54345"

    def test_custom_base_url(self):
        client = AsyncBitBrowserClient(base_url="http://localhost:9999")
        assert client._base_url == "http://localhost:9999"

    def test_default_timeout(self):
        client = AsyncBitBrowserClient()
        assert client._timeout == 30.0

    def test_custom_timeout(self):
        client = AsyncBitBrowserClient(timeout=60.0)
        assert client._timeout == 60.0

    def test_browsers_service_attached(self):
        from bitbrowser.browsers import AsyncBrowsersService

        client = AsyncBitBrowserClient()
        assert isinstance(client.browsers, AsyncBrowsersService)

    def test_http_is_none_before_open(self):
        client = AsyncBitBrowserClient()
        assert client._http is None


class TestAsyncBitBrowserClientContextManager:
    @pytest.mark.asyncio
    async def test_context_manager_opens_and_closes(self):
        async with AsyncBitBrowserClient() as client:
            assert client._http is not None
        assert client._http is None

    @pytest.mark.asyncio
    async def test_open_creates_httpx_async_client(self):
        client = AsyncBitBrowserClient()
        await client.open()
        assert isinstance(client._http, httpx.AsyncClient)
        await client.close()

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        client = AsyncBitBrowserClient()
        await client.close()  # Should not raise when already closed


class TestAsyncBitBrowserClientRequest:
    @pytest.mark.asyncio
    async def test_raises_runtime_error_if_not_open(self):
        client = AsyncBitBrowserClient()
        with pytest.raises(RuntimeError, match="not open"):
            await client.request("/some/path")

    @pytest.mark.asyncio
    async def test_raises_transport_error_on_http_status_error(self):
        client = AsyncBitBrowserClient.__new__(AsyncBitBrowserClient)
        mock_http = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_http.post = AsyncMock(return_value=mock_response)
        client._http = mock_http

        with pytest.raises(TransportError):
            await client.request("/path")

    @pytest.mark.asyncio
    async def test_raises_transport_error_on_request_error(self):
        client = AsyncBitBrowserClient.__new__(AsyncBitBrowserClient)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(
            side_effect=httpx.ConnectError("connection refused")
        )
        client._http = mock_http

        with pytest.raises(TransportError):
            await client.request("/path")

    @pytest.mark.asyncio
    async def test_successful_request_returns_json(self):
        client = AsyncBitBrowserClient.__new__(AsyncBitBrowserClient)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"success": True, "data": {}}
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        client._http = mock_http

        result = await client.request("/browser/list", {"page": 0})
        assert result == {"success": True, "data": {}}
        mock_http.post.assert_called_once_with("/browser/list", json={"page": 0})

    @pytest.mark.asyncio
    async def test_empty_body_sends_empty_dict(self):
        client = AsyncBitBrowserClient.__new__(AsyncBitBrowserClient)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        client._http = mock_http

        await client.request("/health")
        mock_http.post.assert_called_once_with("/health", json={})


class TestAsyncBitBrowserClientHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_true(self):
        client = AsyncBitBrowserClient.__new__(AsyncBitBrowserClient)
        client.request = AsyncMock(return_value={"success": True})
        result = await client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_false(self):
        client = AsyncBitBrowserClient.__new__(AsyncBitBrowserClient)
        client.request = AsyncMock(return_value={"success": False})
        result = await client.health_check()
        assert result is False


# ===========================================================================
# BitBrowserClient (sync)
# ===========================================================================


class TestBitBrowserClientInit:
    def test_default_base_url(self):
        client = BitBrowserClient()
        assert client._base_url == "http://127.0.0.1:54345"

    def test_trailing_slash_stripped(self):
        client = BitBrowserClient(base_url="http://127.0.0.1:54345/")
        assert client._base_url == "http://127.0.0.1:54345"

    def test_custom_timeout(self):
        client = BitBrowserClient(timeout=10.0)
        assert client._timeout == 10.0

    def test_browsers_service_attached(self):
        from bitbrowser.browsers import SyncBrowsersService

        client = BitBrowserClient()
        assert isinstance(client.browsers, SyncBrowsersService)

    def test_http_is_none_before_open(self):
        client = BitBrowserClient()
        assert client._http is None


class TestBitBrowserClientContextManager:
    def test_context_manager_opens_and_closes(self):
        with BitBrowserClient() as client:
            assert client._http is not None
        assert client._http is None

    def test_open_creates_httpx_client(self):
        client = BitBrowserClient()
        client.open()
        assert isinstance(client._http, httpx.Client)
        client.close()

    def test_close_idempotent(self):
        client = BitBrowserClient()
        client.close()  # Should not raise when already None


class TestBitBrowserClientRequest:
    def test_raises_runtime_error_if_not_open(self):
        client = BitBrowserClient()
        with pytest.raises(RuntimeError, match="not open"):
            client.request("/some/path")

    def test_raises_transport_error_on_http_status_error(self):
        client = BitBrowserClient.__new__(BitBrowserClient)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_http = MagicMock()
        mock_http.post.return_value = mock_response
        client._http = mock_http

        with pytest.raises(TransportError):
            client.request("/path")

    def test_raises_transport_error_on_request_error(self):
        client = BitBrowserClient.__new__(BitBrowserClient)
        mock_http = MagicMock()
        mock_http.post.side_effect = httpx.ConnectError("refused")
        client._http = mock_http

        with pytest.raises(TransportError):
            client.request("/path")

    def test_successful_request_returns_json(self):
        client = BitBrowserClient.__new__(BitBrowserClient)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"success": True, "data": {"id": "1"}}
        mock_http = MagicMock()
        mock_http.post.return_value = mock_response
        client._http = mock_http

        result = client.request("/browser/detail", {"id": "1"})
        assert result["data"]["id"] == "1"

    def test_empty_body_sends_empty_dict(self):
        client = BitBrowserClient.__new__(BitBrowserClient)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_http = MagicMock()
        mock_http.post.return_value = mock_response
        client._http = mock_http

        client.request("/health")
        mock_http.post.assert_called_once_with("/health", json={})


class TestBitBrowserClientHealthCheck:
    def test_health_check_true(self):
        client = BitBrowserClient.__new__(BitBrowserClient)
        client.request = MagicMock(return_value={"success": True})
        assert client.health_check() is True

    def test_health_check_false(self):
        client = BitBrowserClient.__new__(BitBrowserClient)
        client.request = MagicMock(return_value={"success": False})
        assert client.health_check() is False
