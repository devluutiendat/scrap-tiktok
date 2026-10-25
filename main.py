import asyncio
from src.browser.manager import create_camoufox_context
from src.extractors.json_extractor import ResponseCollector
from src.extractors.html_extractor import FieldRule, HtmlExtractor
from src.utils.logger import get_logger, RunTracker

logger = get_logger(__name__)

TARGET_URL = "https://www.topcv.vn/tim-viec-lam-software-engineering-tai-ha-noi-l1cr257cb258?sort=new&type_keyword=0&sba=1&category_family=r257~b258&locations=l1"

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
                tracker.record_success(count=len(collector.collected_data))
            else:
                # --- Fallback: API không trả về JSON → scrape thẳng từ HTML DOM ---
                logger.warning(
                    "ResponseCollector timeout — chuyển sang HtmlExtractor để scrape DOM."
                )

                html_extractor = HtmlExtractor(
                    page=page,
                    item_selector="div.job-item-search-result",
                    field_rules=[
                        FieldRule("title",   "div.title-block h3.title a"),
                        FieldRule("url",     "div.title-block h3.title a", attribute="href"),
                        FieldRule("salary",  "label.salary span"),
                        FieldRule("address", "a.address span.city-text"),
                    ],
                    output_file="data/processed/jobs_html_fallback.json",
                    unique_id_key="url",
                    wait_timeout=5.0,
                    snapshot_dir="logs/snapshots",
                )

                await html_extractor.extract_current_page()
                html_extractor.save_to_json()

                if html_extractor.collected_data:
                    # HTML fallback thành công — ghi đúng số items thu thập được
                    tracker.record_success(count=len(html_extractor.collected_data))
                    logger.info(
                        "HTML fallback thu thập được %d items — không ghi error API.",
                        len(html_extractor.collected_data),
                    )
                else:
                    # Cả API lẫn HTML đều thất bại → mới ghi error
                    tracker.record_error(
                        target="page_1",
                        error=RuntimeError("API timeout và HTML fallback cũng không lấy được dữ liệu"),
                    )

        except Exception as e:
            logger.exception("Lỗi không mong muốn trong run_search_scraper: %s", e)
            tracker.record_error(target="run_search_scraper", error=e)

        finally:
            collector.stop_listening()
            collector.save_to_json()
            tracker.save_summary()


if __name__ == "__main__":
    asyncio.run(run_search_scraper())