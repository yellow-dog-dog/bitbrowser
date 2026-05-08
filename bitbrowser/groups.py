"""GroupsService — CRUD operations for BitBrowser window groups.

Each method has an async variant in :class:`AsyncGroupsService` and a
synchronous counterpart in :class:`SyncGroupsService`.

API base path: ``/group/*``
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import Group, ListGroupsResponse

if TYPE_CHECKING:
    from ._client import AsyncBitBrowserClient, BitBrowserClient


# ---------------------------------------------------------------------------
# Async service
# ---------------------------------------------------------------------------


class AsyncGroupsService:
    """Async service for managing BitBrowser window groups.

    Do not instantiate directly — access via
    :attr:`AsyncBitBrowserClient.groups`.
    """

    def __init__(self, client: AsyncBitBrowserClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        page: int = 0,
        page_size: int = 10,
        all_groups: bool = False,
    ) -> ListGroupsResponse:
        """Return a paginated list of window groups.

        Args:
            page: Zero-based page index (default ``0``).
            page_size: Results per page, max ``100`` (default ``10``).
            all_groups: When ``True``, return every group that is
                accessible to the current account regardless of
                pagination limits.

        Returns:
            A :class:`ListGroupsResponse` with the matching groups and
            pagination metadata.

        Raises:
            ApiError: If the API reports a failure.
        """
        body: dict[str, Any] = {"page": page, "pageSize": page_size}
        if all_groups:
            body["all"] = True
        payload = await self._client.request("/group/list", body)
        data = payload.get("data", {})
        rows: list[dict[str, Any]] = data.get("list", [])
        return ListGroupsResponse(
            groups=[Group.model_validate(row) for row in rows],
            total=data.get("total", len(rows)),
            page=page,
            page_size=page_size,
        )

    async def add(self, group: Group) -> Group:
        """Create a new window group.

        Args:
            group: A :class:`Group` instance with ``group_name`` and
                ``sort_num`` set.  ``id`` is ignored.

        Returns:
            The newly created :class:`Group` with its ``id`` populated.

        Raises:
            ValueError: If ``group.group_name`` is not provided.
            ApiError: If the API reports a failure.
        """
        if not group.group_name:
            raise ValueError("group.group_name is required.")
        if group.sort_num is None:
            raise ValueError("group.sort_num is required.")
        body = group.model_dump(by_alias=True, exclude_none=True)
        body.pop("id", None)
        payload = await self._client.request("/group/add", body)
        data = payload.get("data") or {}
        created_id = data.get("id") if isinstance(data, dict) else None
        return Group(
            id=created_id,
            group_name=group.group_name,
            sort_num=group.sort_num,
        )

    async def edit(self, group: Group) -> None:
        """Update an existing window group.

        Args:
            group: A :class:`Group` with ``id``, ``group_name``, and
                ``sort_num`` set.

        Raises:
            ValueError: If ``group.id`` is not provided.
            ApiError: If the API reports a failure.
        """
        if not group.id:
            raise ValueError("group.id is required for edit.")
        if not group.group_name:
            raise ValueError("group.group_name is required for edit.")
        if group.sort_num is None:
            raise ValueError("group.sort_num is required for edit.")
        await self._client.request(
            "/group/edit",
            group.model_dump(by_alias=True, exclude_none=True),
        )

    async def delete(self, group_id: str) -> None:
        """Delete a window group.

        Args:
            group_id: The ID of the group to delete.

        Raises:
            ApiError: If the API reports a failure.
        """
        await self._client.request("/group/delete", {"id": group_id})

    async def detail(self, group_id: str) -> Group:
        """Retrieve the details of a single window group.

        Args:
            group_id: The ID of the group to fetch.

        Returns:
            A :class:`Group` populated from the API response.

        Raises:
            ApiError: If the API reports a failure (e.g. not found).
        """
        payload = await self._client.request("/group/detail", {"id": group_id})
        return Group.model_validate(payload["data"])


# ---------------------------------------------------------------------------
# Sync service — thin wrapper that replicates the async interface
# ---------------------------------------------------------------------------


class SyncGroupsService:
    """Synchronous service for managing BitBrowser window groups.

    Do not instantiate directly — access via
    :attr:`BitBrowserClient.groups`.

    Every method mirrors its counterpart in :class:`AsyncGroupsService`.
    """

    def __init__(self, client: BitBrowserClient) -> None:
        self._client = client

    def list(
        self,
        *,
        page: int = 0,
        page_size: int = 10,
        all_groups: bool = False,
    ) -> ListGroupsResponse:
        """Return a paginated list of window groups.

        See :meth:`AsyncGroupsService.list` for full documentation.
        """
        body: dict[str, Any] = {"page": page, "pageSize": page_size}
        if all_groups:
            body["all"] = True
        payload = self._client.request("/group/list", body)
        data = payload.get("data", {})
        rows: list[dict[str, Any]] = data.get("list", [])
        return ListGroupsResponse(
            groups=[Group.model_validate(row) for row in rows],
            total=data.get("total", len(rows)),
            page=page,
            page_size=page_size,
        )

    def add(self, group: Group) -> Group:
        """Create a new window group.

        See :meth:`AsyncGroupsService.add` for full documentation.
        """
        if not group.group_name:
            raise ValueError("group.group_name is required.")
        if group.sort_num is None:
            raise ValueError("group.sort_num is required.")
        body = group.model_dump(by_alias=True, exclude_none=True)
        body.pop("id", None)
        payload = self._client.request("/group/add", body)
        data = payload.get("data") or {}
        created_id = data.get("id") if isinstance(data, dict) else None
        return Group(
            id=created_id,
            group_name=group.group_name,
            sort_num=group.sort_num,
        )

    def edit(self, group: Group) -> None:
        """Update an existing window group.

        See :meth:`AsyncGroupsService.edit` for full documentation.
        """
        if not group.id:
            raise ValueError("group.id is required for edit.")
        if not group.group_name:
            raise ValueError("group.group_name is required for edit.")
        if group.sort_num is None:
            raise ValueError("group.sort_num is required for edit.")
        self._client.request(
            "/group/edit",
            group.model_dump(by_alias=True, exclude_none=True),
        )

    def delete(self, group_id: str) -> None:
        """Delete a window group.

        See :meth:`AsyncGroupsService.delete` for full documentation.
        """
        self._client.request("/group/delete", {"id": group_id})

    def detail(self, group_id: str) -> Group:
        """Retrieve the details of a single window group.

        See :meth:`AsyncGroupsService.detail` for full documentation.
        """
        payload = self._client.request("/group/detail", {"id": group_id})
        return Group.model_validate(payload["data"])
