import asyncio
from src.utils.logger import get_logger, RunTracker

logger = get_logger(__name__)

async def run_search_scraper():
    tracker = RunTracker(task_name="")

if __name__ == "__main__":
    asyncio.run(run_search_scraper())