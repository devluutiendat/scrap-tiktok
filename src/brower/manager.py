from contextlib import asynccontextmanager
from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Route


class PlaywrightConfig:
    HEADLESS: bool = False
    SLOW_MO: int = 0
    TIMEOUT: int = 30000

    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    PROXY: Optional[dict] = None

    BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}


async def _block_heavy_resources(route: Route):
    if route.request.resource_type in PlaywrightConfig.BLOCKED_RESOURCE_TYPES:
        await route.abort()
    else:
        await route.continue_()


@asynccontextmanager
async def create_playwright_context(block_media: bool = True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=PlaywrightConfig.HEADLESS,
            slow_mo=PlaywrightConfig.SLOW_MO,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )

        context = await browser.new_context(
            user_agent=PlaywrightConfig.USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            screen={"width": 1920, "height": 1080},
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
            proxy=PlaywrightConfig.PROXY,
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

        context.set_default_timeout(PlaywrightConfig.TIMEOUT)
        context.set_default_navigation_timeout(PlaywrightConfig.TIMEOUT)

        if block_media:
            await context.route("**/*", _block_heavy_resources)

        try:
            yield context
        finally:
            await context.close()
            await browser.close()