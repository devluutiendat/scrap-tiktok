import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import BrowserContext, Page, Route

from config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _is_profile_ready(profile_dir: Path) -> bool:

    if not profile_dir.exists():
        return False
    return any(profile_dir.iterdir())


async def _wait_for_page_close(page: Page) -> None:
    closed_event: asyncio.Event = asyncio.Event()
    page.on("close", lambda _: closed_event.set())
    await closed_event.wait()


async def _block_heavy_resources(route: Route) -> None:
    if route.request.resource_type in {"image", "media", "font"}:
        logger.debug(
            "Block resource: type=%s url=%s",
            route.request.resource_type,
            route.request.url[:80],
        )
        await route.abort()
    else:
        await route.continue_()



@asynccontextmanager
async def create_camoufox_context(
    target_url: str,
    block_media: bool = True,
    login_timeout: float = 300.0,
) -> AsyncIterator[BrowserContext]:

    profile_dir: Path = settings.BROWSER_PROFILE_PATH
    profile_dir.mkdir(parents=True, exist_ok=True)

    already_logged_in: bool = _is_profile_ready(profile_dir)

    if already_logged_in:
        headless = True
        logger.info(
            "Tìm thấy profile tại '%s' → chạy ngầm (headless=True)", profile_dir
        )
    else:
        headless = False
        logger.info(
            "Chưa có profile tại '%s' → mở giao diện để đăng nhập (headless=False)",
            profile_dir,
        )

    async with AsyncCamoufox(
        headless=headless,
        persistent_context=True,
        user_data_dir=str(profile_dir),
        locale="vi-VN",
        os="windows",
        geoip=True,
    ) as browser:
        context: BrowserContext = browser

        context.set_default_timeout(settings.BROWSER_TIMEOUT)
        context.set_default_navigation_timeout(settings.BROWSER_TIMEOUT)

        if block_media:
            logger.debug("Bật chế độ block media/image/font")
            await context.route("**/*", _block_heavy_resources)

        if not already_logged_in:
            page: Page = await context.new_page()
            logger.info("Đang mở trang đăng nhập: %s", target_url)
            await page.goto(target_url)

            logger.info(
                "⏳ Vui lòng đăng nhập trong vòng %.0f giây. "
                "Đóng cửa sổ browser khi xong để tiếp tục.",
                login_timeout,
            )

            try:
                await asyncio.wait_for(
                    _wait_for_page_close(page),
                    timeout=login_timeout,
                )
                logger.info("✅ Cửa sổ đã đóng — kết thúc phiên đăng nhập.")
            except asyncio.TimeoutError:
                logger.warning(
                    "⏰ Hết %gs chờ — tiếp tục với trạng thái hiện tại.",
                    login_timeout,
                )

            logger.info(
                "💾 Profile đã lưu vào: %s — lần sau sẽ chạy headless=True.",
                profile_dir,
            )

        try:
            yield context
        finally:
            logger.info("Đang đóng Camoufox context...")

