import asyncio
from src.brower.manager import create_playwright_context
async def main():
    async with create_playwright_context() as context:
        page = await context.new_page()
        await page.goto("https://google.com")
        await page.wait_for_timeout(3000)
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())