"""demo_fingerprint.py — Create a browser window with explicit fingerprint
settings, then randomise the fingerprint and display both states.

Run from the repo root::

    uv run python bitbrowser/demos/demo_fingerprint.py
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict

from bitbrowser import AsyncBitBrowserClient, Browser, BrowserFingerPrint


async def main() -> None:
    async with AsyncBitBrowserClient() as client:
        # ------------------------------------------------------------------
        # Step 1 — build a fingerprint with explicit values.
        # All fields are optional; omitted fields are randomised by
        # BitBrowser.  The camelCase ↔ snake_case mapping is handled
        # automatically by BrowserFingerPrint.to_api_dict().
        # ------------------------------------------------------------------
        fp = BrowserFingerPrint(
            core_version="130",
            ostype="PC",
            os="Win32",
            # Language / locale
            language_type=1,        # follow browser language
            languages="en-US,en",
            # Canvas / WebGL
            canvas=1,               # noise
            webgl=1,                # noise
            webgl_vendor="Google Inc. (NVIDIA)",
            webgl_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3080, OpenGL 4.5)",
            # Audio
            audio=1,                # noise
            # Screen
            screen_width=1920,
            screen_height=1080,
            # Fonts
            font_type=0,            # default font list
            # Misc
            do_not_track="default",
            hardware_concurrency=8,
            device_memory=8,
        )

        browser_in = Browser(
            name="fingerprint-demo",
            remark="Created by demo_fingerprint.py",
            browser_finger_print=fp,
        )

        print("Creating browser window …")
        created = await client.browsers.create(browser_in)
        print(f"  id  = {created.id}")

        # ------------------------------------------------------------------
        # Step 2 — fetch full details and display the fingerprint that was
        # actually stored.
        # ------------------------------------------------------------------
        detail = await client.browsers.get(created.id)
        stored_fp = detail.browser_finger_print
        if stored_fp:
            fp_dict = asdict(stored_fp)
            print("\nStored fingerprint (selected fields):")
            for key in (
                "core_version",
                "ostype",
                "os",
                "languages",
                "canvas",
                "webgl",
                "screen_width",
                "screen_height",
                "hardware_concurrency",
                "device_memory",
            ):
                print(f"  {key:30s} = {fp_dict.get(key)!r}")

        # ------------------------------------------------------------------
        # Step 3 — randomise the fingerprint and show the new values.
        # ------------------------------------------------------------------
        print("\nRandomising fingerprint …")
        new_fp = await client.browsers.random_fingerprint(created.id)
        new_fp_dict = asdict(new_fp)
        print("New fingerprint (selected fields):")
        for key in ("core_version", "ostype", "os", "languages"):
            print(f"  {key:30s} = {new_fp_dict.get(key)!r}")

        # ------------------------------------------------------------------
        # Step 4 — clean up.
        # ------------------------------------------------------------------
        print("\nDeleting demo window …")
        await client.browsers.delete(created.id)
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
