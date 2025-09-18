import argparse
import asyncio

from playwright.async_api import async_playwright


async def main(url: str, timeout: int, headless: bool):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            title = await page.title()
            print({"ok": True, "title": title})
        finally:
            await browser.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://www.facebook.com/ads/library/")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--headless", type=int, default=1)
    args = ap.parse_args()
    asyncio.run(main(args.url, args.timeout, bool(args.headless)))
