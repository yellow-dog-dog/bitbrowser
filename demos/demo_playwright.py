"""demo_playwright.py — Open a browser window via BitBrowser and drive it
with Playwright over CDP.

Steps:
  1. Create a browser window with a custom fingerprint.
  2. Open the window and receive the WebSocket debugger URL.
  3. Connect Playwright to the running Chromium instance.
  4. Navigate to example.com and print the page title.
  5. Take a screenshot.
  6. Disconnect and close the window.
  7. Delete the demo window.

Run from the repo root::

    uv run python bitbrowser/demos/demo_playwright.py

Dependencies (declared in bitbrowser/pyproject.toml):
    playwright>=1.44
    bitbrowser  (this workspace member)
"""

from __future__ import annotations

import asyncio

from playwright.async_api import async_playwright

from bitbrowser import AsyncBitBrowserClient, Browser, BrowserFingerPrint


async def main() -> None:
    async with AsyncBitBrowserClient() as client:
        # ------------------------------------------------------------------
        # Step 1 — create the browser window
        # ------------------------------------------------------------------
        fp = BrowserFingerPrint(
            core_version="130",
            ostype="PC",
            os="Win32",
            language_type=0,
            languages="en-US,en",
            canvas=1,
            webgl=1,
            audio=1,
        )
        browser_model = Browser(
            name="playwright-demo",
            remark="Created by demo_playwright.py",
            browser_finger_print=fp,
        )
        created = await client.browsers.create(browser_model)
        browser_id = created.id
        print(f"Window created: {browser_id!r}")

        # ------------------------------------------------------------------
        # Step 2 — open the window and get the CDP endpoint
        # ------------------------------------------------------------------
        result = await client.browsers.open(browser_id, queue=True)
        ws_url = result.ws
        print(f"CDP WebSocket: {ws_url}")

        # ------------------------------------------------------------------
        # Step 3 — connect Playwright
        # ------------------------------------------------------------------
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(ws_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Step 4 — navigate and read the title
            await page.goto("https://example.com")
            title = await page.title()
            print(f"Page title: {title!r}")

            # Step 5 — screenshot
            screenshot_path = "demo_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path!r}")

            # Step 6 — disconnect (does NOT close the Chromium process)
            await browser.close()

        # ------------------------------------------------------------------
        # Step 7 — close and delete the window via BitBrowser API
        # ------------------------------------------------------------------
        await client.browsers.close(browser_id)
        print("Window closed via API")

        await client.browsers.delete(browser_id)
        print("Window deleted. Done.")


if __name__ == "__main__":
    asyncio.run(main())
