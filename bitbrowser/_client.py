"""Core HTTP transport for the BitBrowser local API."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import ApiError, TransportError

_DEFAULT_BASE_URL = "http://127.0.0.1:54345"
_DEFAULT_TIMEOUT = 30.0


def _check_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Raise :class:`ApiError` when *success* is ``False``."""
    if not payload.get("success", False):
        raise ApiError(payload.get("msg", "unknown error"))
    return payload


class AsyncBitBrowserClient:
    """Async HTTP client for the BitBrowser local API.

    Manages a shared :class:`httpx.AsyncClient` and exposes service objects
    for each resource family.

    Args:
        base_url: Local API base URL (default ``http://127.0.0.1:54345``).
        timeout: Default request timeout in seconds (default ``30``).
        httpx_kwargs: Extra keyword arguments forwarded to
            :class:`httpx.AsyncClient`.

    Example::

        async with AsyncBitBrowserClient() as client:
            result = await client.browsers.open("abc123")
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        **httpx_kwargs: Any,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._httpx_kwargs = httpx_kwargs
        self._http: httpx.AsyncClient | None = None

        # Lazy-import to avoid circular imports
        from .browsers import AsyncBrowsersService
        from .groups import AsyncGroupsService
        from .tags import AsyncTagsService

        self.browsers: AsyncBrowsersService = AsyncBrowsersService(self)
        self.groups: AsyncGroupsService = AsyncGroupsService(self)
        self.tags: AsyncTagsService = AsyncTagsService(self)

    # ------------------------------------------------------------------
    # Context-manager protocol
    # ------------------------------------------------------------------

    async def __aenter__(self) -> AsyncBitBrowserClient:
        await self.open()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def open(self) -> None:
        """Open the underlying HTTP connection pool."""
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            **self._httpx_kwargs,
        )

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Internal request helper
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
        before_sleep=lambda rs: logger.warning(
            "Retry attempt {n} for request…",
            n=rs.attempt_number,
        ),
    )
    async def request(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST *body* to *path* and return the parsed JSON response.

        Raises:
            TransportError: On HTTP or network-level failures
                (retried up to 3 times with exponential back-off).
            ApiError: When the API returns ``success: false``
                (not retried — this is a business-logic failure).
        """
        if self._http is None:
            raise RuntimeError(
                "Client is not open. Use 'async with AsyncBitBrowserClient() as client:'"
                " or call 'await client.open()' first."
            )
        logger.debug("→ POST {} body={}", path, body)
        try:
            response = await self._http.post(path, json=body or {})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("HTTP error on {}: {}", path, exc)
            raise TransportError(str(exc)) from exc
        except httpx.RequestError as exc:
            logger.warning("Network error on {}: {}", path, exc)
            raise TransportError(str(exc)) from exc
        logger.debug("← {} {}", response.status_code, path)
        return _check_response(response.json())

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Return ``True`` if the local server is reachable.

        This is a no-parameter call useful for connectivity tests.
        """
        payload = await self.request("/health")
        return bool(payload.get("success", False))


class BitBrowserClient:
    """Synchronous HTTP client for the BitBrowser local API.

    Wraps :class:`AsyncBitBrowserClient` using a private
    :class:`httpx.Client` so callers do not need ``asyncio``.

    Args:
        base_url: Local API base URL (default ``http://127.0.0.1:54345``).
        timeout: Default request timeout in seconds (default ``30``).
        httpx_kwargs: Extra keyword arguments forwarded to
            :class:`httpx.Client`.

    Example::

        with BitBrowserClient() as client:
            result = client.browsers.open("abc123")
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        **httpx_kwargs: Any,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._httpx_kwargs = httpx_kwargs
        self._http: httpx.Client | None = None

        from .browsers import SyncBrowsersService
        from .groups import SyncGroupsService
        from .tags import SyncTagsService

        self.browsers: SyncBrowsersService = SyncBrowsersService(self)
        self.groups: SyncGroupsService = SyncGroupsService(self)
        self.tags: SyncTagsService = SyncTagsService(self)

    # ------------------------------------------------------------------
    # Context-manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> BitBrowserClient:
        self.open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def open(self) -> None:
        """Open the underlying HTTP connection pool."""
        self._http = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            **self._httpx_kwargs,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        if self._http is not None:
            self._http.close()
            self._http = None

    # ------------------------------------------------------------------
    # Internal request helper
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
        before_sleep=lambda rs: logger.warning(
            "Retry attempt {n} for request…",
            n=rs.attempt_number,
        ),
    )
    def request(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST *body* to *path* and return the parsed JSON response.

        Raises:
            TransportError: On HTTP or network-level failures
                (retried up to 3 times with exponential back-off).
            ApiError: When the API returns ``success: false``
                (not retried — this is a business-logic failure).
        """
        if self._http is None:
            raise RuntimeError(
                "Client is not open. Use 'with BitBrowserClient() as client:'"
                " or call 'client.open()' first."
            )
        logger.debug("→ POST {} body={}", path, body)
        try:
            response = self._http.post(path, json=body or {})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("HTTP error on {}: {}", path, exc)
            raise TransportError(str(exc)) from exc
        except httpx.RequestError as exc:
            logger.warning("Network error on {}: {}", path, exc)
            raise TransportError(str(exc)) from exc
        logger.debug("← {} {}", response.status_code, path)
        return _check_response(response.json())

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Return ``True`` if the local server is reachable."""
        payload = self.request("/health")
        return bool(payload.get("success", False))
