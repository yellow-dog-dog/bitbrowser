"""TagsService — CRUD and relation operations for BitBrowser window tags.

Constraints (enforced server-side):
    - Maximum 20 tags may exist at one time.
    - Each browser window may have at most 3 tags bound to it.

API base path: ``/browserTag/*``
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Tag

if TYPE_CHECKING:
    from ._client import AsyncBitBrowserClient, BitBrowserClient


# ---------------------------------------------------------------------------
# Async service
# ---------------------------------------------------------------------------


class AsyncTagsService:
    """Async service for managing BitBrowser window tags.

    Do not instantiate directly — access via
    :attr:`AsyncBitBrowserClient.tags`.
    """

    def __init__(self, client: AsyncBitBrowserClient) -> None:
        self._client = client

    async def list(self) -> list[Tag]:
        """Return all existing window tags.

        Returns:
            A list of :class:`Tag` objects (at most 20 total).

        Raises:
            ApiError: If the API reports a failure.
        """
        payload = await self._client.request("/browserTag/list")
        rows = payload.get("data") or []
        return [Tag.model_validate(row) for row in rows]

    async def create(self, tag: Tag) -> Tag:
        """Create a new window tag.

        Args:
            tag: A :class:`Tag` with ``tag_name`` (max 50 chars) and
                ``tag_color`` (``#rrggbb`` format) set.

        Returns:
            The created :class:`Tag`.  The ``id`` field will be populated
            if the API returns it; otherwise a :class:`Tag` with the
            provided name and colour is returned.

        Raises:
            ValueError: If ``tag_name`` or ``tag_color`` is not provided.
            ApiError: If the API reports a failure (e.g. tag limit reached).
        """
        if not tag.tag_name:
            raise ValueError("tag.tag_name is required.")
        if not tag.tag_color:
            raise ValueError("tag.tag_color is required.")
        body = {"tagName": tag.tag_name, "tagColor": tag.tag_color}
        payload = await self._client.request("/browserTag/create", body)
        data = payload.get("data") or {}
        created_id = data.get("id") if isinstance(data, dict) else None
        return Tag(
            id=created_id,
            tag_name=tag.tag_name,
            tag_color=tag.tag_color,
        )

    async def update(self, tag: Tag) -> None:
        """Update an existing window tag.

        Args:
            tag: A :class:`Tag` with ``id`` (32 chars), ``tag_name``, and
                ``tag_color`` all set.

        Raises:
            ValueError: If any required field is missing.
            ApiError: If the API reports a failure.
        """
        if not tag.id:
            raise ValueError("tag.id is required for update.")
        if not tag.tag_name:
            raise ValueError("tag.tag_name is required for update.")
        if not tag.tag_color:
            raise ValueError("tag.tag_color is required for update.")
        await self._client.request(
            "/browserTag/update",
            tag.model_dump(by_alias=True, exclude_none=True),
        )

    async def delete(self, tag_ids: list[str]) -> None:
        """Delete one or more window tags.

        Args:
            tag_ids: A list of tag IDs to delete.

        Raises:
            ValueError: If ``tag_ids`` is empty.
            ApiError: If the API reports a failure.
        """
        if not tag_ids:
            raise ValueError("tag_ids must not be empty.")
        await self._client.request("/browserTag/delete", {"ids": tag_ids})

    async def update_relation(
        self,
        browser_id: str,
        *,
        add_tag_ids: list[str] | None = None,
        remove_tag_ids: list[str] | None = None,
    ) -> None:
        """Update the tag bindings for a browser window.

        Pass tag IDs to *add_tag_ids* to bind them, and/or tag IDs to
        *remove_tag_ids* to unbind them.  A window may have at most 3
        tags at any time.

        Args:
            browser_id: The window ID (32 chars).
            add_tag_ids: Tag IDs to bind to the window.
            remove_tag_ids: Tag IDs to unbind from the window.

        Raises:
            ApiError: If the API reports a failure.
        """
        body = {
            "browserId": browser_id,
            "addTagIds": add_tag_ids or [],
            "removeTagIds": remove_tag_ids or [],
        }
        await self._client.request("/browserTag/updateRelation", body)


# ---------------------------------------------------------------------------
# Sync service
# ---------------------------------------------------------------------------


class SyncTagsService:
    """Synchronous service for managing BitBrowser window tags.

    Do not instantiate directly — access via
    :attr:`BitBrowserClient.tags`.

    Every method mirrors its counterpart in :class:`AsyncTagsService`.
    """

    def __init__(self, client: BitBrowserClient) -> None:
        self._client = client

    def list(self) -> list[Tag]:
        """Return all existing window tags.

        See :meth:`AsyncTagsService.list` for full documentation.
        """
        payload = self._client.request("/browserTag/list")
        rows = payload.get("data") or []
        return [Tag.model_validate(row) for row in rows]

    def create(self, tag: Tag) -> Tag:
        """Create a new window tag.

        See :meth:`AsyncTagsService.create` for full documentation.
        """
        if not tag.tag_name:
            raise ValueError("tag.tag_name is required.")
        if not tag.tag_color:
            raise ValueError("tag.tag_color is required.")
        body = {"tagName": tag.tag_name, "tagColor": tag.tag_color}
        payload = self._client.request("/browserTag/create", body)
        data = payload.get("data") or {}
        created_id = data.get("id") if isinstance(data, dict) else None
        return Tag(
            id=created_id,
            tag_name=tag.tag_name,
            tag_color=tag.tag_color,
        )

    def update(self, tag: Tag) -> None:
        """Update an existing window tag.

        See :meth:`AsyncTagsService.update` for full documentation.
        """
        if not tag.id:
            raise ValueError("tag.id is required for update.")
        if not tag.tag_name:
            raise ValueError("tag.tag_name is required for update.")
        if not tag.tag_color:
            raise ValueError("tag.tag_color is required for update.")
        self._client.request(
            "/browserTag/update",
            tag.model_dump(by_alias=True, exclude_none=True),
        )

    def delete(self, tag_ids: list[str]) -> None:
        """Delete one or more window tags.

        See :meth:`AsyncTagsService.delete` for full documentation.
        """
        if not tag_ids:
            raise ValueError("tag_ids must not be empty.")
        self._client.request("/browserTag/delete", {"ids": tag_ids})

    def update_relation(
        self,
        browser_id: str,
        *,
        add_tag_ids: list[str] | None = None,
        remove_tag_ids: list[str] | None = None,
    ) -> None:
        """Update the tag bindings for a browser window.

        See :meth:`AsyncTagsService.update_relation` for full documentation.
        """
        body = {
            "browserId": browser_id,
            "addTagIds": add_tag_ids or [],
            "removeTagIds": remove_tag_ids or [],
        }
        self._client.request("/browserTag/updateRelation", body)
