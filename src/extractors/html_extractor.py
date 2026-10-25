import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup, Tag
from playwright.async_api import Page

from src.extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

@dataclass
class FieldRule:
    name: str
    selector: str
    attribute: Optional[str] = None
    multiple: bool = False
    transform: Optional[Callable[[Any], Any]] = None


@dataclass
class PaginationConfig:
    next_button_selector: str
    max_pages: int = 0
    page_delay: float = 2.0


class HtmlExtractor(BaseExtractor):

    def __init__(
        self,
        page: Page,
        item_selector: str,
        field_rules: List[FieldRule],
        output_file: str,
        unique_id_key: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        wait_timeout: float = 15.0,
        pagination: Optional[PaginationConfig] = None,
        snapshot_dir: Optional[str] = "logs/snapshots",
    ) -> None:
        
        self.page = page
        self.item_selector = item_selector
        self.field_rules = field_rules
        self.output_path = Path(output_file)
        self.unique_id_key = unique_id_key
        # Mặc định đợi chính item_selector xuất hiện trước khi lấy HTML
        self.wait_for_selector = wait_for_selector or item_selector
        self.wait_timeout_ms = int(wait_timeout * 1000)
        self.pagination = pagination
        self.snapshot_dir: Optional[Path] = Path(snapshot_dir) if snapshot_dir else None
        self.collected_data: List[Dict[str, Any]] = []
        self._seen_ids: set = set()

    def _extract_field(self, container: Tag, rule: FieldRule) -> Any:

        def _get_value(el: Tag) -> Any:
            if rule.attribute:
                raw = el.get(rule.attribute)
            else:
                raw = el.get_text(strip=True)
            return rule.transform(raw) if (rule.transform and raw is not None) else raw

        if rule.multiple:
            # Trả về list tất cả match
            elements = container.select(rule.selector)
            return [_get_value(el) for el in elements]
        else:
            # Chỉ lấy element đầu tiên
            el = container.select_one(rule.selector)
            if el is None:
                logger.debug(
                    "Không tìm thấy selector '%s' trong item — trả về None", rule.selector
                )
                return None
            return _get_value(el)

    async def _save_debug_artifacts(self, html_content: str) -> None:

        safe_selector = "".join(
            c if c.isalnum() or c in ("-",) else "_"
            for c in self.item_selector
        ).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.snapshot_dir is not None:
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path = self.snapshot_dir / f"snapshot_{safe_selector}_{timestamp}.html"
            snapshot_path.write_text(html_content, encoding="utf-8")
            logger.warning(
                "HTML snapshot đã được lưu vào: %s — Kiểm tra lại selector '%s'.",
                snapshot_path,
                self.item_selector,
            )

        if self.snapshot_dir is not None:
            screenshot_path = self.snapshot_dir / f"screenshot_{safe_selector}_{timestamp}.png"
            try:
                await self.page.screenshot(path=str(screenshot_path), full_page=True)
                logger.warning(
                    "Màn hình đã được chụp và lưu vào: %s",
                    screenshot_path,
                )
            except Exception as exc:
                logger.error("Không thể chụp màn hình: %s", exc)

    def _parse_html(self, html_content: str) -> int:
        soup = BeautifulSoup(html_content, "lxml")
        items = soup.select(self.item_selector)

        if not items:
            logger.warning(
                "Không tìm thấy item nào với selector '%s'. "
                "Kiểm tra lại CSS selector hoặc cấu trúc HTML.",
                self.item_selector,
            )
            self._pending_snapshot_html: Optional[str] = html_content
            return 0

        new_count = 0
        for item_tag in items:
            record: Dict[str, Any] = {}
            for rule in self.field_rules:
                record[rule.name] = self._extract_field(item_tag, rule)

            if self.unique_id_key:
                uid_value = record.get(self.unique_id_key)
                if uid_value is None:
                    logger.debug(
                        "Item thiếu unique_id_key='%s', bỏ qua dedup.", self.unique_id_key
                    )
                else:
                    uid_str = str(uid_value)
                    if uid_str in self._seen_ids:
                        continue
                    self._seen_ids.add(uid_str)

            self.collected_data.append(record)
            new_count += 1

        logger.info(
            "Parse HTML -> Thêm %d bản ghi mới (Tổng: %d)",
            new_count,
            len(self.collected_data),
        )
        return new_count

    async def extract_current_page(self) -> int:
       
        logger.info(
            "Đang chờ selector '%s' xuất hiện (timeout=%dms)...",
            self.wait_for_selector,
            self.wait_timeout_ms,
        )
        try:
            await self.page.wait_for_selector(
                self.wait_for_selector,
                timeout=self.wait_timeout_ms,
            )
        except Exception:
           logger.warning(
                "Selector '%s' không xuất hiện sau %dms — "
                "vẫn lấy HTML hiện tại để phân tích và tạo debug artifacts.",
                self.wait_for_selector,
                self.wait_timeout_ms,
            )
        html_content = await self.page.content()
        # Reset pending snapshot trước mỗi lần parse
        self._pending_snapshot_html: Optional[str] = None
        count = self._parse_html(html_content)
        # Nếu _parse_html lưu html vào _pending_snapshot_html → kích hoạt debug artifacts
        if self._pending_snapshot_html is not None:
            await self._save_debug_artifacts(self._pending_snapshot_html)
        return count

    async def extract_all_pages(self) -> int:
        total_new = await self.extract_current_page()

        if self.pagination is None:
            return total_new

        page_num = 1
        while True:
            if self.pagination.max_pages > 0 and page_num >= self.pagination.max_pages:
                logger.info(
                    "Đã đạt giới hạn %d trang — dừng phân trang.", self.pagination.max_pages
                )
                break

            next_btn = self.page.locator(self.pagination.next_button_selector)
            is_visible = await next_btn.is_visible()
            if not is_visible:
                logger.info("Không tìm thấy nút trang sau — đã đến trang cuối.")
                break

            is_enabled = await next_btn.is_enabled()
            if not is_enabled:
                logger.info("Nút trang sau bị disabled — đã đến trang cuối.")
                break

            delay = self.pagination.page_delay + random.uniform(0.5, 1.5)
            logger.debug("Chờ %.1fs trước khi sang trang %d...", delay, page_num + 1)
            await asyncio.sleep(delay)

            await next_btn.click()
            page_num += 1
            logger.info("Đã click sang trang %d", page_num)

            new_count = await self.extract_current_page()
            total_new += new_count

            if new_count == 0:
                logger.warning("Trang %d không có dữ liệu mới — dừng.", page_num)
                break

        logger.info(
            "Hoàn thành: Thu thập %d bản ghi qua %d trang.", total_new, page_num
        )
        return total_new

