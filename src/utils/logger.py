# src/utils/logger.py
import json
import logging
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
from playwright.async_api import Page

LOG_DIR = Path("logs")
SCREENSHOT_DIR = LOG_DIR / "screenshots"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "scraper") -> logging.Logger:
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    app_file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    app_file_handler.setLevel(logging.INFO)
    app_file_handler.setFormatter(formatter)

    error_file_handler = RotatingFileHandler(
        LOG_DIR / "errors.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(app_file_handler)
    logger.addHandler(error_file_handler)

    return logger

async def log_browser_exception(
    logger: logging.Logger,
    error: Exception,
    context_msg: str,
    page: Optional[Page] = None
):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = None

    if page and not page.is_closed():
        try:
            screenshot_file = SCREENSHOT_DIR / f"error_{timestamp}.png"
            await page.screenshot(path=str(screenshot_file), full_page=True)
            screenshot_path = str(screenshot_file)
        except Exception as sc_err:
            logger.warning(f"Không thể chụp ảnh màn hình lúc lỗi: {sc_err}")

    error_details = (
        f"{context_msg} | Lỗi: {type(error).__name__}: {error}"
        + (f" | Ảnh chụp: {screenshot_path}" if screenshot_path else "")
        + f"\n{traceback.format_exc()}"
    )
    logger.error(error_details)


class RunTracker:
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.start_time = datetime.now()
        self.items_scraped = 0
        self.errors: list[Dict[str, Any]] = []
        self.logger = get_logger()

    def record_success(self, count: int = 1):
        self.items_scraped += count

    def record_error(self, target: str, error: Exception):
        self.errors.append({
            "time": datetime.now().isoformat(),
            "target": target,
            "error_type": type(error).__name__,
            "message": str(error)
        })

    def clear_errors(self) -> None:
        """Xóa toàn bộ errors đã ghi — dùng khi fallback thành công và muốn trạng thái là SUCCESS."""
        self.errors.clear()

    def save_summary(self):
        end_time = datetime.now()
        duration = round((end_time - self.start_time).total_seconds(), 2)
        status = "SUCCESS" if not self.errors else ("PARTIAL" if self.items_scraped > 0 else "FAILED")

        summary = {
            "task_name": self.task_name,
            "status": status,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_items_scraped": self.items_scraped,
            "total_errors": len(self.errors),
            "error_list": self.errors
        }

        history_file = LOG_DIR / "run_history.jsonl"
        with open(history_file, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")

        self.logger.info(
            f"=== KẾT THÚC CA CHẠY [{self.task_name}] | Trạng thái: {status} | "
            f"Thời gian: {duration}s | Thu thập: {self.items_scraped} | Lỗi: {len(self.errors)} ==="
        )