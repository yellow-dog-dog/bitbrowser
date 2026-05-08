"""demo_groups_tags.py — CRUD walk-through for groups and tags.

Creates a group, creates two tags, creates a browser window inside the group,
binds the tags to the window, then lists everything and cleans up.

Run from the repo root::

    uv run python bitbrowser/demos/demo_groups_tags.py
"""

from __future__ import annotations

import asyncio

from bitbrowser import AsyncBitBrowserClient, Browser, BrowserFingerPrint, Group, Tag


async def main() -> None:
    async with AsyncBitBrowserClient() as client:
        # ------------------------------------------------------------------
        # Groups — create
        # ------------------------------------------------------------------
        print("=== Groups ===")
        group = await client.groups.add(
            Group(group_name="Demo Group", sort_num=99)
        )
        print(f"Created group: id={group.id!r}, name={group.group_name!r}")

        # Edit the group name
        group.group_name = "Demo Group (edited)"
        await client.groups.edit(group)
        print(f"Renamed group to {group.group_name!r}")

        # List all groups
        resp = await client.groups.list(page=0, page_size=50)
        print(f"Total groups: {resp.total}")
        for g in resp.groups:
            marker = " ← ours" if g.id == group.id else ""
            print(f"  [{g.id}] {g.group_name}{marker}")

        # ------------------------------------------------------------------
        # Tags — create
        # ------------------------------------------------------------------
        print("\n=== Tags ===")
        tag_a = await client.tags.create(
            Tag(tag_name="demo-blue", tag_color="#2196F3")
        )
        tag_b = await client.tags.create(
            Tag(tag_name="demo-green", tag_color="#4CAF50")
        )
        print(f"Created tags: {tag_a.id!r}, {tag_b.id!r}")

        # List all tags
        all_tags = await client.tags.list()
        print(f"Total tags: {len(all_tags)}")

        # ------------------------------------------------------------------
        # Browser window — create inside the demo group
        # ------------------------------------------------------------------
        print("\n=== Browser window ===")
        browser = await client.browsers.create(
            Browser(
                name="groups-tags-demo",
                group_id=group.id,
                browser_finger_print=BrowserFingerPrint(),
            )
        )
        print(f"Created window: id={browser.id!r}, group_id={group.id!r}")

        # Bind both tags to the window
        await client.tags.update_relation(
            browser.id,
            add_tag_ids=[tag_a.id, tag_b.id],
        )
        print(f"Bound tags {tag_a.id!r} and {tag_b.id!r} to window")

        # Unbind tag_b
        await client.tags.update_relation(
            browser.id,
            remove_tag_ids=[tag_b.id],
        )
        print(f"Unbound tag {tag_b.id!r}")

        # ------------------------------------------------------------------
        # Clean up — order matters: remove window first, then tags, then group
        # ------------------------------------------------------------------
        print("\n=== Clean up ===")
        await client.browsers.delete(browser.id)
        print("Deleted window")

        await client.tags.delete([tag_a.id, tag_b.id])
        print("Deleted tags")

        await client.groups.delete(group.id)
        print("Deleted group")

        print("\nAll done.")


if __name__ == "__main__":
    asyncio.run(main())
