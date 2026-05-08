"""BrowsersService — CRUD and lifecycle operations for BitBrowser windows.

Follows Google AIP conventions:
  - Standard methods: ``create``, ``get``, ``list``, ``update``, ``delete``
  - Custom methods prefixed with a verb: ``open``, ``close``, ``reset_close_state``, …
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import Browser, BrowserFingerPrint, ListBrowsersResponse, OpenResult

if TYPE_CHECKING:
    from ._client import AsyncBitBrowserClient, BitBrowserClient


# ---------------------------------------------------------------------------
# Async service
# ---------------------------------------------------------------------------


class AsyncBrowsersService:
    """Async service for managing BitBrowser windows.

    Do not instantiate directly — access via
    :attr:`AsyncBitBrowserClient.browsers`.
    """

    def __init__(self, client: AsyncBitBrowserClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # AIP-133  Create
    # ------------------------------------------------------------------

    async def create(self, browser: Browser) -> Browser:
        """Create a new browser window.

        The ``browser_finger_print`` field of *browser* is required.
        Pass ``BrowserFingerPrint()`` to randomise all fingerprint values.

        The ``group_id`` field is optional — if omitted, BitBrowser will
        create or reuse a default "API" group automatically.

        Args:
            browser: Configuration for the new window.  Must have
                ``browser_finger_print`` set.

        Returns:
            The created :class:`Browser` with its ``id`` populated.

        Raises:
            ValueError: If ``browser_finger_print`` is not provided.
            ApiError: If the API reports a failure.
        """
        if browser.browser_finger_print is None:
            raise ValueError(
                "browser.browser_finger_print is required. "
                "Pass BrowserFingerPrint() to randomise all values."
            )
        body = browser.model_dump(by_alias=True, exclude_none=True)
        # Ensure the id field is not sent for a create call
        body.pop("id", None)
        payload = await self._client.request("/browser/update", body)
        data = payload.get("data", {})
        return Browser(
            id=data.get("id"),
            group_id=data.get("groupId") or browser.group_id,
        )

    # ------------------------------------------------------------------
    # AIP-131  Get
    # ------------------------------------------------------------------

    async def get(self, browser_id: str) -> Browser:
        """Get the full details of a browser window.

        Args:
            browser_id: The unique window ID.

        Returns:
            A fully-populated :class:`Browser` instance.

        Raises:
            ApiError: If the API reports a failure (e.g. not found).
        """
        payload = await self._client.request(
            "/browser/detail", {"id": browser_id}
        )
        return Browser.model_validate(payload["data"])

    # ------------------------------------------------------------------
    # AIP-132  List
    # ------------------------------------------------------------------

    async def list(
        self,
        *,
        page: int = 0,
        page_size: int = 10,
        group_id: str | None = None,
        name: str | None = None,
        remark: str | None = None,
        seq: int | None = None,
        min_seq: int | None = None,
        max_seq: int | None = None,
        sort: str | None = None,
        owned_by_me: bool | None = None,
        opened: bool | None = None,
    ) -> ListBrowsersResponse:
        """List browser windows with pagination and optional filters.

        Args:
            page: Zero-based page index (default ``0``).
            page_size: Results per page, max ``100`` (default ``10``).
            group_id: Filter by group ID.
            name: Fuzzy-match by window name.
            remark: Exact-match by remark/label.
            seq: Exact-match by sequence number.
            min_seq: Lower bound for sequence-number range query.
                Cannot be combined with *seq*.
            max_seq: Upper bound for sequence-number range query.
                Cannot be combined with *seq*.
            sort: Sort order — ``"asc"`` or ``"desc"``.
            owned_by_me: Return only windows created by the current user.
            opened: Return only currently-open windows.

        Returns:
            A :class:`ListBrowsersResponse` containing the matching windows
            and pagination metadata.

        Raises:
            ApiError: If the API reports a failure.
        """
        body: dict[str, Any] = {"page": page, "pageSize": page_size}
        if group_id is not None:
            body["groupId"] = group_id
        if name is not None:
            body["name"] = name
        if remark is not None:
            body["remark"] = remark
        if seq is not None:
            body["seq"] = seq
        if min_seq is not None:
            body["minSeq"] = min_seq
        if max_seq is not None:
            body["maxSeq"] = max_seq
        if sort is not None:
            body["sort"] = sort
        if owned_by_me is not None:
            body["ownedByMe"] = owned_by_me
        if opened is not None:
            body["opened"] = opened

        payload = await self._client.request("/browser/list", body)
        data = payload.get("data", {})
        rows: list[dict[str, Any]] = data.get("list", [])
        return ListBrowsersResponse(
            browsers=[Browser.model_validate(row) for row in rows],
            total=data.get("total", len(rows)),
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # AIP-134  Update
    # ------------------------------------------------------------------

    async def update(self, browser: Browser) -> None:
        """Update fields on an existing browser window.

        Only the non-``None`` fields in *browser* are sent.  The ``id``
        field is required to identify which window to update.

        To update *only* proxy settings, use :meth:`update_proxy` instead.

        Args:
            browser: Partial :class:`Browser` with ``id`` set and whichever
                fields you want to change populated.

        Raises:
            ValueError: If ``browser.id`` is not set.
            ApiError: If the API reports a failure.
        """
        if not browser.id:
            raise ValueError("browser.id is required for update.")
        body = browser.model_dump(by_alias=True, exclude_none=True)
        await self._client.request("/browser/update", body)

    async def batch_update(
        self,
        ids: list[str],
        *,
        browser: Browser | None = None,
        **fields: Any,
    ) -> None:
        """Update specific fields across multiple browser windows at once.

        Pass either a *browser* object (its non-``None`` fields are used) or
        individual keyword arguments for the API camelCase or Python
        snake_case keys.

        Args:
            ids: List of window IDs to update.
            browser: Optional :class:`Browser` whose non-``None`` fields
                are sent.  The ``id`` field is ignored.
            **fields: Additional raw fields to include in the request body
                (camelCase or snake_case — snake_case is converted
                automatically).

        Raises:
            ValueError: If *ids* is empty.
            ApiError: If the API reports a failure.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        body: dict[str, Any] = {"ids": ids}
        if browser is not None:
            partial = browser.model_dump(by_alias=True, exclude_none=True)
            partial.pop("id", None)
            body.update(partial)
        body.update(fields)
        await self._client.request("/browser/update/partial", body)

    # ------------------------------------------------------------------
    # AIP-135  Delete
    # ------------------------------------------------------------------

    async def delete(self, browser_id: str) -> None:
        """Permanently delete a browser window (no recycle bin).

        Args:
            browser_id: The window ID to delete.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request("/browser/delete", {"id": browser_id})

    async def batch_delete(self, ids: list[str]) -> None:
        """Permanently delete up to 100 browser windows at once.

        Args:
            ids: Window IDs to delete (max 100 per call).

        Raises:
            ValueError: If *ids* is empty.
            ApiError: If the API reports a failure.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        await self._client.request("/browser/delete/ids", {"ids": ids})

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — lifecycle
    # ------------------------------------------------------------------

    async def open(
        self,
        browser_id: str,
        *,
        args: list[str] | None = None,
        queue: bool = False,
        ignore_default_urls: bool = False,
        new_page_url: str | None = None,
    ) -> OpenResult:
        """Open a browser window and return its automation endpoints.

        Args:
            browser_id: The window ID to open.
            args: Additional Chromium CLI flags, e.g.
                ``["--headless", "--incognito"]``.
            queue: Serialise concurrent open requests to prevent
                race conditions (recommended for multi-threaded use).
            ignore_default_urls: Open a blank page instead of the
                window's saved URLs.
            new_page_url: URL to open on launch.  Requires
                *ignore_default_urls* to be ``True``.

        Returns:
            An :class:`OpenResult` with ``ws`` and ``http`` endpoints for
            Playwright / Selenium automation.

        Raises:
            ApiError: If the API reports a failure.
        """
        body: dict[str, Any] = {"id": browser_id, "args": args or [], "queue": queue}
        if ignore_default_urls:
            body["ignoreDefaultUrls"] = True
        if new_page_url is not None:
            body["newPageUrl"] = new_page_url
        payload = await self._client.request("/browser/open", body)
        return OpenResult.model_validate(payload["data"])

    async def close(self, browser_id: str) -> None:
        """Close an open browser window.

        After calling this method, wait at least 5 seconds before
        reopening or deleting the window to allow the process to exit.

        Args:
            browser_id: The window ID to close.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request("/browser/close", {"id": browser_id})

    async def close_all(self) -> None:
        """Close all currently open browser windows.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request("/browser/close/all")

    async def reset_close_state(self, browser_id: str) -> None:
        """Reset a window that is stuck in "opening" or "closing" state.

        Use this only when the browser has genuinely closed but the API
        still reports it as active due to an abnormal exit.

        Args:
            browser_id: The window ID to reset.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request(
            "/browser/closing/reset", {"id": browser_id}
        )

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — proxy
    # ------------------------------------------------------------------

    async def update_proxy(
        self,
        ids: list[str],
        *,
        proxy_method: int,
        proxy_type: str,
        host: str,
        port: int,
        proxy_user_name: str = "",
        proxy_password: str = "",
        ip_check_service: str = "ip123in",
        refresh_proxy_url: str | None = None,
        dynamic_ip_url: str | None = None,
        dynamic_ip_channel: str | None = None,
        is_dynamic_ip_change_ip: bool | None = None,
        is_ipv6: bool = False,
    ) -> None:
        """Batch-update the proxy settings for one or more windows.

        Args:
            ids: Window IDs to update.
            proxy_method: ``2`` custom proxy · ``3`` dynamic-IP extraction.
            proxy_type: One of ``"noproxy"``, ``"http"``, ``"https"``,
                ``"socks5"``, ``"ssh"``.
            host: Proxy host.
            port: Proxy port.
            proxy_user_name: Proxy username.
            proxy_password: Proxy password.
            ip_check_service: IP lookup provider.
            refresh_proxy_url: Proxy refresh URL.
            dynamic_ip_url: Extraction URL (when *proxy_method* is ``3``).
            dynamic_ip_channel: Extraction vendor.
            is_dynamic_ip_change_ip: Re-extract on every open.
            is_ipv6: Whether the proxy uses IPv6.

        Raises:
            ValueError: If *ids* is empty.
            ApiError: If the API reports a failure.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        body: dict[str, Any] = {
            "ids": ids,
            "proxyMethod": proxy_method,
            "proxyType": proxy_type,
            "host": host,
            "port": port,
            "proxyUserName": proxy_user_name,
            "proxyPassword": proxy_password,
            "ipCheckService": ip_check_service,
            "isIpv6": is_ipv6,
        }
        if refresh_proxy_url is not None:
            body["refreshProxyUrl"] = refresh_proxy_url
        if dynamic_ip_url is not None:
            body["dynamicIpUrl"] = dynamic_ip_url
        if dynamic_ip_channel is not None:
            body["dynamicIpChannel"] = dynamic_ip_channel
        if is_dynamic_ip_change_ip is not None:
            body["isDynamicIpChangeIp"] = is_dynamic_ip_change_ip
        await self._client.request("/browser/proxy/update", body)

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — process / PID queries
    # ------------------------------------------------------------------

    async def get_pids(self, ids: list[str]) -> dict[str, int]:
        """Return the OS process IDs for the given window IDs.

        Windows that are not open will not appear in the result.

        Args:
            ids: Window IDs to query.

        Returns:
            A mapping of ``{window_id: pid}``.

        Raises:
            ValueError: If *ids* is empty.
            ApiError: If the API reports a failure.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        payload = await self._client.request("/browser/pids", {"ids": ids})
        return payload.get("data") or {}

    async def get_all_pids(self) -> dict[str, int]:
        """Return the OS process IDs for all open windows.

        Returns:
            A mapping of ``{window_id: pid}``.

        Raises:
            ApiError: If the API reports a failure.
        """
        payload = await self._client.request("/browser/pids/all")
        return payload.get("data") or {}

    async def get_alive_pids(self, ids: list[str]) -> dict[str, int]:
        """Return PIDs for the given windows, verifying each process is alive.

        Dead processes are filtered out automatically.

        Args:
            ids: Window IDs to query.

        Returns:
            A mapping of ``{window_id: pid}`` for alive processes only.

        Raises:
            ValueError: If *ids* is empty.
            ApiError: If the API reports a failure.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        payload = await self._client.request(
            "/browser/pids/alive", {"ids": ids}
        )
        return payload.get("data") or {}

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — fingerprint
    # ------------------------------------------------------------------

    async def random_fingerprint(
        self, browser_id: str
    ) -> BrowserFingerPrint:
        """Randomise the fingerprint of a window and return the new values.

        This does **not** persist the fingerprint — it returns a
        :class:`BrowserFingerPrint` object that you can inspect or pass to
        :meth:`update`.

        Args:
            browser_id: The window ID.

        Returns:
            The newly randomised :class:`BrowserFingerPrint`.

        Raises:
            ApiError: If the API reports a failure.
        """
        payload = await self._client.request(
            "/browser/fingerprint/random", {"browserId": browser_id}
        )
        return BrowserFingerPrint.model_validate(payload["data"])

    # ------------------------------------------------------------------
    # Custom methods — batch group / remark / close-by-seqs
    # ------------------------------------------------------------------

    async def batch_update_group(
        self, browser_ids: list[str], group_id: str
    ) -> None:
        """Move multiple windows to the same group.

        Args:
            browser_ids: List of window IDs to move.
            group_id: Target group ID.

        Raises:
            ValueError: If ``browser_ids`` is empty.
            ApiError: If the API reports a failure.
        """
        if not browser_ids:
            raise ValueError("browser_ids must not be empty.")
        await self._client.request(
            "/browser/group/update",
            {"groupId": group_id, "browserIds": browser_ids},
        )

    async def batch_update_remark(
        self, browser_ids: list[str], remark: str
    ) -> None:
        """Set the same remark string on multiple windows.

        Args:
            browser_ids: List of window IDs to update.
            remark: The new remark string.

        Raises:
            ValueError: If ``browser_ids`` is empty.
            ApiError: If the API reports a failure.
        """
        if not browser_ids:
            raise ValueError("browser_ids must not be empty.")
        await self._client.request(
            "/browser/remark/update",
            {"browserIds": browser_ids, "remark": remark},
        )

    async def close_by_seqs(self, seqs: list[int]) -> None:
        """Close browser windows by their sequence numbers.

        Args:
            seqs: List of window sequence numbers to close.

        Raises:
            ValueError: If ``seqs`` is empty.
            ApiError: If the API reports a failure.
        """
        if not seqs:
            raise ValueError("seqs must not be empty.")
        await self._client.request("/browser/close/byseqs", {"seqs": seqs})

    # ------------------------------------------------------------------
    # Custom methods — ports / cache
    # ------------------------------------------------------------------

    async def get_ports(self) -> dict[str, str]:
        """Return the remote-debugging ports for all open windows.

        Returns:
            A mapping of ``{window_id: port_string}`` for every open window
            that has a debug port.

        Raises:
            ApiError: If the API reports a failure.
        """
        payload = await self._client.request("/browser/ports")
        return payload.get("data") or {}

    async def clear_cache(self, ids: list[str]) -> None:
        """Clear all local and remote cache data for the given windows.

        Args:
            ids: Window IDs whose caches should be cleared.

        Raises:
            ValueError: If ``ids`` is empty.
            ApiError: If the API reports a failure.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        await self._client.request("/cache/clear", {"ids": ids})

    async def clear_cache_except_extensions(self, ids: list[str]) -> None:
        """Clear window cache while preserving extension data.

        Args:
            ids: Window IDs whose caches should be cleared.

        Raises:
            ValueError: If ``ids`` is empty.
            ApiError: If the API reports a failure.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        await self._client.request("/cache/clear/exceptExtensions", {"ids": ids})

    # ------------------------------------------------------------------
    # Custom methods — proxy check
    # ------------------------------------------------------------------

    async def check_proxy(
        self,
        host: str,
        port: int,
        proxy_type: str,
        proxy_user_name: str,
        proxy_password: str,
        *,
        ip_check_service: str = "ip123in",
        check_exists: int = 0,
    ) -> dict[str, Any]:
        """Check whether a proxy is reachable and return its IP information.

        Args:
            host: Proxy host.
            port: Proxy port.
            proxy_type: One of ``"http"``, ``"socks5"``, ``"ssh"``.
            proxy_user_name: Proxy username.
            proxy_password: Proxy password.
            ip_check_service: IP lookup provider.  ``"ip123in"`` (default)
                or ``"ip-api"``.
            check_exists: Whether to verify the IP has not already been
                used.  ``1`` to check, ``0`` to skip (default).

        Returns:
            The raw ``data`` dict from the API response, containing IP
            information such as country, city, and timezone.

        Raises:
            ApiError: If the proxy is unreachable or the API returns an
                error.
        """
        body: dict[str, Any] = {
            "host": host,
            "port": port,
            "proxyType": proxy_type,
            "proxyUserName": proxy_user_name,
            "proxyPassword": proxy_password,
            "ipCheckService": ip_check_service,
            "checkExists": check_exists,
        }
        payload = await self._client.request("/checkagent", body)
        return payload.get("data") or {}

    # ------------------------------------------------------------------
    # Custom methods — cookies
    # ------------------------------------------------------------------

    async def set_cookies(
        self, browser_id: str, cookies: list[dict[str, Any]]
    ) -> None:
        """Inject cookies into an already-open browser window.

        The window must be open before calling this method.

        Args:
            browser_id: The window ID.
            cookies: A list of cookie dicts.  Each dict must conform to
                the standard CDP cookie format (``name``, ``value``,
                ``domain``, etc.).

        Raises:
            ValueError: If ``cookies`` is empty.
            ApiError: If the API reports a failure.
        """
        if not cookies:
            raise ValueError("cookies must not be empty.")
        await self._client.request(
            "/browser/cookies/set",
            {"browserId": browser_id, "cookies": cookies},
        )

    async def clear_cookies(
        self, browser_id: str, *, save_synced: bool = True
    ) -> None:
        """Clear all cookies for a browser window.

        Works regardless of whether the window is currently open.
        Requires BitBrowser client version 7.0.2 or later.

        Args:
            browser_id: The window ID.
            save_synced: When ``True`` (default), also clears cookies that
                have already been synced to the cloud.  Pass ``False`` to
                keep the synced copy.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request(
            "/browser/cookies/clear",
            {"browserId": browser_id, "saveSynced": save_synced},
        )

    async def get_cookies(
        self, browser_id: str
    ) -> list[dict[str, Any]]:
        """Get the live cookies from an open browser window.

        Note: live cookies can change at any time.  Two consecutive calls
        may return different results.

        Args:
            browser_id: The window ID.

        Returns:
            A list of cookie dicts (CDP format).

        Raises:
            ApiError: If the API reports a failure.
        """
        payload = await self._client.request(
            "/browser/cookies/get", {"browserId": browser_id}
        )
        return payload.get("data") or []

    async def format_cookies(
        self, cookie: Any, hostname: str
    ) -> list[dict[str, Any]]:
        """Normalise a raw cookie string or array into standard format.

        Useful when importing cookies from an external source that may not
        include a ``domain`` field.

        Args:
            cookie: Raw cookie data.  May be a string (e.g.
                ``"key=value; key2=value2"``) or an array.
            hostname: The domain to assign to cookies that lack one, e.g.
                ``".example.com"``.

        Returns:
            A list of normalised cookie dicts.

        Raises:
            ApiError: If the API reports a failure.
        """
        payload = await self._client.request(
            "/browser/cookies/format",
            {"cookie": cookie, "hostname": hostname},
        )
        return payload.get("data") or []

    # ------------------------------------------------------------------
    # Custom methods — window arrangement / displays
    # ------------------------------------------------------------------

    async def arrange_windows(
        self,
        *,
        type: str,
        start_x: int = 0,
        start_y: int = 0,
        width: int,
        height: int,
        col: int = 3,
        space_x: int = 0,
        space_y: int = 0,
        offset_x: int = 0,
        offset_y: int = 0,
        order_by: str = "asc",
        ids: list[str] | None = None,
        seqlist: list[int] | None = None,
        screen_id: int | None = None,
    ) -> None:
        """Tile open browser windows on screen.

        Args:
            type: Layout mode.  ``"box"`` (grid) or ``"diagonal"``.
            start_x: Left edge of the tiled area in screen pixels
                (default ``0``).
            start_y: Top edge of the tiled area in screen pixels
                (default ``0``).
            width: Width of each window in pixels (min ``500``).
            height: Height of each window in pixels (min ``200``).
            col: Number of columns for ``"box"`` layout (default ``3``).
            space_x: Horizontal gap between windows in pixels
                (default ``0``).
            space_y: Vertical gap between windows in pixels
                (default ``0``).
            offset_x: Diagonal horizontal offset in pixels (default ``0``).
            offset_y: Diagonal vertical offset in pixels (default ``0``).
            order_by: Sort order — ``"asc"`` or ``"desc"`` (default
                ``"asc"``).
            ids: Window IDs to tile.  When provided, *seqlist* is ignored.
                If neither is provided all open windows are tiled.
            seqlist: Window sequence numbers to tile (used only when *ids*
                is ``None``).
            screen_id: Target monitor ID from :meth:`get_displays`.

        Raises:
            ApiError: If the API reports a failure.
        """
        body: dict[str, Any] = {
            "type": type,
            "startX": start_x,
            "startY": start_y,
            "width": width,
            "height": height,
            "col": col,
            "spaceX": space_x,
            "spaceY": space_y,
            "offsetX": offset_x,
            "offsetY": offset_y,
            "orderBy": order_by,
        }
        if ids is not None:
            body["ids"] = ids
        elif seqlist is not None:
            body["seqlist"] = seqlist
        if screen_id is not None:
            body["screenId"] = screen_id
        await self._client.request("/windowbounds", body)

    async def arrange_windows_auto(
        self, seqlist: list[int] | None = None
    ) -> None:
        """Auto-fit all open windows to the screen.

        Args:
            seqlist: Optional list of window sequence numbers to arrange.
                If not provided, all open windows are arranged.

        Raises:
            ApiError: If the API reports a failure.
        """
        body: dict[str, Any] = {"seqlist": seqlist or []}
        await self._client.request("/windowbounds/flexable", body)

    async def get_displays(self) -> list[dict[str, Any]]:
        """Return all connected monitors with their dimensions and IDs.

        Returns:
            A list of display info dicts.  Each dict includes at least
            ``id``, ``label``, ``bounds``, ``workArea``, and
            ``scaleFactor``.

        Raises:
            ApiError: If the API reports a failure.
        """
        payload = await self._client.request("/alldisplays")
        return payload.get("data") or []

    # ------------------------------------------------------------------
    # Custom methods — RPA / autopaste / utilities
    # ------------------------------------------------------------------

    async def rpa_run(self, task_id: str) -> None:
        """Start an RPA task.

        Args:
            task_id: The RPA task ID (copied from the RPA management UI).

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request("/rpa/run", {"id": task_id})

    async def rpa_stop(self, task_id: str) -> None:
        """Stop a running RPA task.

        Args:
            task_id: The RPA task ID.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request("/rpa/stop", {"id": task_id})

    async def autopaste(self, browser_id: str, url: str) -> None:
        """Simulate typing the clipboard contents into the focused input.

        The browser window must be open and have a focused ``<input>`` or
        ``<textarea>`` element.

        Args:
            browser_id: The window ID.
            url: The exact URL of the page that contains the focused input.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request(
            "/autopaste", {"browserId": browser_id, "url": url}
        )

    async def read_excel(self, filepath: str) -> Any:
        """Read a local Excel file and return its contents.

        Args:
            filepath: Absolute path to the ``.xlsx`` file on the local
                machine running BitBrowser.

        Returns:
            The raw data returned by the API (typically a list of rows).

        Raises:
            ApiError: If the file cannot be read.
        """
        payload = await self._client.request(
            "/utils/readexcel", {"filepath": filepath}
        )
        return payload.get("data")

    async def read_file(self, filepath: str) -> Any:
        """Read a local text or JSON file and return its contents.

        Args:
            filepath: Absolute path to the file on the local machine
                running BitBrowser.

        Returns:
            The raw data returned by the API (a stringified file
            content — parse JSON yourself if needed).

        Raises:
            ApiError: If the file cannot be read.
        """
        payload = await self._client.request(
            "/utils/readfile", {"filepath": filepath}
        )
        return payload.get("data")


# ---------------------------------------------------------------------------
# Sync service — thin wrapper around the async service
# ---------------------------------------------------------------------------


class SyncBrowsersService:
    """Synchronous service for managing BitBrowser windows.

    Do not instantiate directly — access via
    :attr:`BitBrowserClient.browsers`.

    Every method mirrors its counterpart in :class:`AsyncBrowsersService`.
    """

    def __init__(self, client: BitBrowserClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # AIP-133  Create
    # ------------------------------------------------------------------

    def create(self, browser: Browser) -> Browser:
        """Create a new browser window.

        See :meth:`AsyncBrowsersService.create` for full documentation.
        """
        if browser.browser_finger_print is None:
            raise ValueError(
                "browser.browser_finger_print is required. "
                "Pass BrowserFingerPrint() to randomise all values."
            )
        body = browser.model_dump(by_alias=True, exclude_none=True)
        body.pop("id", None)
        payload = self._client.request("/browser/update", body)
        data = payload.get("data", {})
        return Browser(
            id=data.get("id"),
            group_id=data.get("groupId") or browser.group_id,
        )

    # ------------------------------------------------------------------
    # AIP-131  Get
    # ------------------------------------------------------------------

    def get(self, browser_id: str) -> Browser:
        """Get the full details of a browser window.

        See :meth:`AsyncBrowsersService.get` for full documentation.
        """
        payload = self._client.request("/browser/detail", {"id": browser_id})
        return Browser.model_validate(payload["data"])

    # ------------------------------------------------------------------
    # AIP-132  List
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        page: int = 0,
        page_size: int = 10,
        group_id: str | None = None,
        name: str | None = None,
        remark: str | None = None,
        seq: int | None = None,
        min_seq: int | None = None,
        max_seq: int | None = None,
        sort: str | None = None,
        owned_by_me: bool | None = None,
        opened: bool | None = None,
    ) -> ListBrowsersResponse:
        """List browser windows with pagination and optional filters.

        See :meth:`AsyncBrowsersService.list` for full documentation.
        """
        body: dict[str, Any] = {"page": page, "pageSize": page_size}
        if group_id is not None:
            body["groupId"] = group_id
        if name is not None:
            body["name"] = name
        if remark is not None:
            body["remark"] = remark
        if seq is not None:
            body["seq"] = seq
        if min_seq is not None:
            body["minSeq"] = min_seq
        if max_seq is not None:
            body["maxSeq"] = max_seq
        if sort is not None:
            body["sort"] = sort
        if owned_by_me is not None:
            body["ownedByMe"] = owned_by_me
        if opened is not None:
            body["opened"] = opened

        payload = self._client.request("/browser/list", body)
        data = payload.get("data", {})
        rows: list[dict[str, Any]] = data.get("list", [])
        return ListBrowsersResponse(
            browsers=[Browser.model_validate(row) for row in rows],
            total=data.get("total", len(rows)),
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # AIP-134  Update
    # ------------------------------------------------------------------

    def update(self, browser: Browser) -> None:
        """Update fields on an existing browser window.

        See :meth:`AsyncBrowsersService.update` for full documentation.
        """
        if not browser.id:
            raise ValueError("browser.id is required for update.")
        self._client.request(
            "/browser/update",
            browser.model_dump(by_alias=True, exclude_none=True),
        )

    def batch_update(
        self,
        ids: list[str],
        *,
        browser: Browser | None = None,
        **fields: Any,
    ) -> None:
        """Update specific fields across multiple browser windows at once.

        See :meth:`AsyncBrowsersService.batch_update` for full documentation.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        body: dict[str, Any] = {"ids": ids}
        if browser is not None:
            partial = browser.model_dump(by_alias=True, exclude_none=True)
            partial.pop("id", None)
            body.update(partial)
        body.update(fields)
        self._client.request("/browser/update/partial", body)

    # ------------------------------------------------------------------
    # AIP-135  Delete
    # ------------------------------------------------------------------

    def delete(self, browser_id: str) -> None:
        """Permanently delete a browser window.

        See :meth:`AsyncBrowsersService.delete` for full documentation.
        """
        self._client.request("/browser/delete", {"id": browser_id})

    def batch_delete(self, ids: list[str]) -> None:
        """Permanently delete up to 100 browser windows at once.

        See :meth:`AsyncBrowsersService.batch_delete` for full documentation.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        self._client.request("/browser/delete/ids", {"ids": ids})

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — lifecycle
    # ------------------------------------------------------------------

    def open(
        self,
        browser_id: str,
        *,
        args: list[str] | None = None,
        queue: bool = False,
        ignore_default_urls: bool = False,
        new_page_url: str | None = None,
    ) -> OpenResult:
        """Open a browser window and return its automation endpoints.

        See :meth:`AsyncBrowsersService.open` for full documentation.
        """
        body: dict[str, Any] = {"id": browser_id, "args": args or [], "queue": queue}
        if ignore_default_urls:
            body["ignoreDefaultUrls"] = True
        if new_page_url is not None:
            body["newPageUrl"] = new_page_url
        payload = self._client.request("/browser/open", body)
        return OpenResult.model_validate(payload["data"])

    def close(self, browser_id: str) -> None:
        """Close an open browser window.

        See :meth:`AsyncBrowsersService.close` for full documentation.
        """
        self._client.request("/browser/close", {"id": browser_id})

    def close_all(self) -> None:
        """Close all currently open browser windows.

        See :meth:`AsyncBrowsersService.close_all` for full documentation.
        """
        self._client.request("/browser/close/all")

    def reset_close_state(self, browser_id: str) -> None:
        """Reset a window stuck in "opening" or "closing" state.

        See :meth:`AsyncBrowsersService.reset_close_state` for full documentation.
        """
        self._client.request("/browser/closing/reset", {"id": browser_id})

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — proxy
    # ------------------------------------------------------------------

    def update_proxy(
        self,
        ids: list[str],
        *,
        proxy_method: int,
        proxy_type: str,
        host: str,
        port: int,
        proxy_user_name: str = "",
        proxy_password: str = "",
        ip_check_service: str = "ip123in",
        refresh_proxy_url: str | None = None,
        dynamic_ip_url: str | None = None,
        dynamic_ip_channel: str | None = None,
        is_dynamic_ip_change_ip: bool | None = None,
        is_ipv6: bool = False,
    ) -> None:
        """Batch-update proxy settings.

        See :meth:`AsyncBrowsersService.update_proxy` for full documentation.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        body: dict[str, Any] = {
            "ids": ids,
            "proxyMethod": proxy_method,
            "proxyType": proxy_type,
            "host": host,
            "port": port,
            "proxyUserName": proxy_user_name,
            "proxyPassword": proxy_password,
            "ipCheckService": ip_check_service,
            "isIpv6": is_ipv6,
        }
        if refresh_proxy_url is not None:
            body["refreshProxyUrl"] = refresh_proxy_url
        if dynamic_ip_url is not None:
            body["dynamicIpUrl"] = dynamic_ip_url
        if dynamic_ip_channel is not None:
            body["dynamicIpChannel"] = dynamic_ip_channel
        if is_dynamic_ip_change_ip is not None:
            body["isDynamicIpChangeIp"] = is_dynamic_ip_change_ip
        self._client.request("/browser/proxy/update", body)

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — PID queries
    # ------------------------------------------------------------------

    def get_pids(self, ids: list[str]) -> dict[str, int]:
        """Return the OS PIDs for the given window IDs.

        See :meth:`AsyncBrowsersService.get_pids` for full documentation.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        payload = self._client.request("/browser/pids", {"ids": ids})
        return payload.get("data") or {}

    def get_all_pids(self) -> dict[str, int]:
        """Return the OS PIDs for all open windows.

        See :meth:`AsyncBrowsersService.get_all_pids` for full documentation.
        """
        payload = self._client.request("/browser/pids/all")
        return payload.get("data") or {}

    def get_alive_pids(self, ids: list[str]) -> dict[str, int]:
        """Return PIDs for the given windows, verifying each process is alive.

        See :meth:`AsyncBrowsersService.get_alive_pids` for full documentation.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        payload = self._client.request("/browser/pids/alive", {"ids": ids})
        return payload.get("data") or {}

    # ------------------------------------------------------------------
    # AIP-136  Custom methods — fingerprint
    # ------------------------------------------------------------------

    def random_fingerprint(self, browser_id: str) -> BrowserFingerPrint:
        """Randomise the fingerprint of a window and return the new values.

        See :meth:`AsyncBrowsersService.random_fingerprint` for full documentation.
        """
        payload = self._client.request(
            "/browser/fingerprint/random", {"browserId": browser_id}
        )
        return BrowserFingerPrint.model_validate(payload["data"])

    # ------------------------------------------------------------------
    # Custom methods — group / remark / close / ports
    # ------------------------------------------------------------------

    def batch_update_group(
        self, browser_ids: list[str], group_id: str
    ) -> None:
        """Move multiple windows into a group.

        See :meth:`AsyncBrowsersService.batch_update_group` for full
        documentation.
        """
        self._client.request(
            "/browser/group/update",
            {"groupId": group_id, "browserIds": browser_ids},
        )

    def batch_update_remark(
        self, browser_ids: list[str], remark: str
    ) -> None:
        """Set the same remark on multiple windows.

        See :meth:`AsyncBrowsersService.batch_update_remark` for full
        documentation.
        """
        self._client.request(
            "/browser/remark/update",
            {"browserIds": browser_ids, "remark": remark},
        )

    def close_by_seqs(self, seqs: list[int]) -> None:
        """Close windows identified by their sequence numbers.

        See :meth:`AsyncBrowsersService.close_by_seqs` for full
        documentation.
        """
        self._client.request("/browser/close/byseqs", {"seqs": seqs})

    def get_ports(self) -> dict[str, str]:
        """Return the debug ports for all open windows.

        See :meth:`AsyncBrowsersService.get_ports` for full documentation.
        """
        payload = self._client.request("/browser/ports")
        return payload.get("data") or {}

    # ------------------------------------------------------------------
    # Custom methods — cache
    # ------------------------------------------------------------------

    def clear_cache(self, ids: list[str]) -> None:
        """Clear all cache data for the given windows.

        See :meth:`AsyncBrowsersService.clear_cache` for full documentation.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        self._client.request("/cache/clear", {"ids": ids})

    def clear_cache_except_extensions(self, ids: list[str]) -> None:
        """Clear cache for the given windows, preserving extension storage.

        See :meth:`AsyncBrowsersService.clear_cache_except_extensions` for
        full documentation.
        """
        if not ids:
            raise ValueError("ids must not be empty.")
        self._client.request("/cache/clear/exceptExtensions", {"ids": ids})

    # ------------------------------------------------------------------
    # Custom methods — proxy check
    # ------------------------------------------------------------------

    def check_proxy(
        self,
        host: str,
        port: int,
        proxy_type: str,
        proxy_user_name: str = "",
        proxy_password: str = "",
        *,
        ip_check_service: str = "ip123in",
        check_exists: int = 0,
    ) -> dict[str, Any]:
        """Test whether a proxy is reachable and return IP info.

        See :meth:`AsyncBrowsersService.check_proxy` for full documentation.
        """
        body: dict[str, Any] = {
            "host": host,
            "port": port,
            "proxyType": proxy_type,
            "proxyUserName": proxy_user_name,
            "proxyPassword": proxy_password,
            "ipCheckService": ip_check_service,
            "checkExists": check_exists,
        }
        payload = self._client.request("/checkagent", body)
        return payload.get("data") or {}

    # ------------------------------------------------------------------
    # Custom methods — cookies
    # ------------------------------------------------------------------

    def set_cookies(
        self, browser_id: str, cookies: list[dict[str, Any]]
    ) -> None:
        """Import cookies into a browser window.

        See :meth:`AsyncBrowsersService.set_cookies` for full documentation.
        """
        self._client.request(
            "/browser/cookies/set",
            {"browserId": browser_id, "cookies": cookies},
        )

    def clear_cookies(
        self, browser_id: str, *, save_synced: bool = True
    ) -> None:
        """Delete all cookies for a browser window.

        See :meth:`AsyncBrowsersService.clear_cookies` for full documentation.
        """
        self._client.request(
            "/browser/cookies/clear",
            {"browserId": browser_id, "saveSynced": save_synced},
        )

    def get_cookies(
        self, browser_id: str
    ) -> list[dict[str, Any]]:
        """Retrieve all cookies for a browser window.

        See :meth:`AsyncBrowsersService.get_cookies` for full documentation.
        """
        payload = self._client.request(
            "/browser/cookies/get", {"browserId": browser_id}
        )
        return payload.get("data") or []

    def format_cookies(
        self, cookie: str, hostname: str
    ) -> list[dict[str, Any]]:
        """Convert a raw cookie string into structured cookie objects.

        See :meth:`AsyncBrowsersService.format_cookies` for full
        documentation.
        """
        payload = self._client.request(
            "/browser/cookies/format",
            {"cookie": cookie, "hostname": hostname},
        )
        return payload.get("data") or []

    # ------------------------------------------------------------------
    # Custom methods — window arrangement / displays
    # ------------------------------------------------------------------

    def arrange_windows(
        self,
        *,
        type: str,
        start_x: int = 0,
        start_y: int = 0,
        width: int,
        height: int,
        col: int = 3,
        space_x: int = 0,
        space_y: int = 0,
        offset_x: int = 0,
        offset_y: int = 0,
        order_by: str = "asc",
        ids: list[str] | None = None,
        seqlist: list[int] | None = None,
        screen_id: int | None = None,
    ) -> None:
        """Tile open browser windows on screen.

        See :meth:`AsyncBrowsersService.arrange_windows` for full
        documentation.
        """
        body: dict[str, Any] = {
            "type": type,
            "startX": start_x,
            "startY": start_y,
            "width": width,
            "height": height,
            "col": col,
            "spaceX": space_x,
            "spaceY": space_y,
            "offsetX": offset_x,
            "offsetY": offset_y,
            "orderBy": order_by,
        }
        if ids is not None:
            body["ids"] = ids
        elif seqlist is not None:
            body["seqlist"] = seqlist
        if screen_id is not None:
            body["screenId"] = screen_id
        self._client.request("/windowbounds", body)

    def arrange_windows_auto(
        self, seqlist: list[int] | None = None
    ) -> None:
        """Auto-fit all open windows to the screen.

        See :meth:`AsyncBrowsersService.arrange_windows_auto` for full
        documentation.
        """
        body: dict[str, Any] = {"seqlist": seqlist or []}
        self._client.request("/windowbounds/flexable", body)

    def get_displays(self) -> list[dict[str, Any]]:
        """Return all connected monitors with their dimensions and IDs.

        See :meth:`AsyncBrowsersService.get_displays` for full documentation.
        """
        payload = self._client.request("/alldisplays")
        return payload.get("data") or []

    # ------------------------------------------------------------------
    # Custom methods — RPA / autopaste / utilities
    # ------------------------------------------------------------------

    def rpa_run(self, task_id: str) -> None:
        """Start an RPA task.

        See :meth:`AsyncBrowsersService.rpa_run` for full documentation.
        """
        self._client.request("/rpa/run", {"id": task_id})

    def rpa_stop(self, task_id: str) -> None:
        """Stop a running RPA task.

        See :meth:`AsyncBrowsersService.rpa_stop` for full documentation.
        """
        self._client.request("/rpa/stop", {"id": task_id})

    def autopaste(self, browser_id: str, url: str) -> None:
        """Simulate typing the clipboard contents into the focused input.

        See :meth:`AsyncBrowsersService.autopaste` for full documentation.
        """
        self._client.request(
            "/autopaste", {"browserId": browser_id, "url": url}
        )

    def read_excel(self, filepath: str) -> Any:
        """Read a local Excel file and return its contents.

        See :meth:`AsyncBrowsersService.read_excel` for full documentation.
        """
        payload = self._client.request(
            "/utils/readexcel", {"filepath": filepath}
        )
        return payload.get("data")

    def read_file(self, filepath: str) -> Any:
        """Read a local text or JSON file and return its contents.

        See :meth:`AsyncBrowsersService.read_file` for full documentation.
        """
        payload = self._client.request(
            "/utils/readfile", {"filepath": filepath}
        )
        return payload.get("data")
