import asyncio
from src.browser.manager import create_camoufox_context
from src.extractors.json_extractor import ResponseCollector
from src.utils.logger import get_logger, RunTracker

logger = get_logger(__name__)

TARGET_URL = "https://www.topcv.vn/"

async def run_search_scraper():
    tracker = RunTracker(task_name="topcv_job_scraper")

    async with create_camoufox_context(target_url=TARGET_URL, block_media=True) as context:
        page = await context.new_page()

        collector = ResponseCollector(
            page=page,
            url_keyword="/api-featured-jobs",         
            target_key_path="jobs",       
            output_file="data/processed/jobs.json", 
            unique_id_key="id",               
            selected_fields=["address", "id", "salary", "title"]  
        )

        collector.start_listening()
        logger.info("Bắt đầu scrape topcv job, url_keyword='%s'", "/api-featured-jobs")

        try:
            logger.info("Đang mở trang: %s", TARGET_URL)
            await page.goto(TARGET_URL)
            got = await collector.wait_for_next_response(timeout=20.0)
            if got:
                tracker.record_success()
            else:
                tracker.record_error(target="page_1", error=TimeoutError("Không nhận được response trang 1"))

        except Exception as e:
            logger.exception("Lỗi không mong muốn trong run_search_scraper: %s", e)
            tracker.record_error(target="run_search_scraper", error=e)

        finally:
            collector.stop_listening()
            collector.save_to_json()
            tracker.save_summary()


if __name__ == "__main__":
    asyncio.run(run_search_scraper())