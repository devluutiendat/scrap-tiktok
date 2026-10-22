import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from playwright.async_api import Page, Response


class ResponseCollector:

    def __init__(
        self,
        page: Page,
        url_keyword: str,                    # Tham số url_keyword: chuỗi nhận diện URL API
        target_key_path: str,                # Tham số target_key_path: đường dẫn lấy list trong JSON (VD: "data.list")
        output_file: str,                    # Đường dẫn file JSON lưu kết quả
        unique_id_key: Optional[str] = "id", # Khóa dùng để lọc trùng (nếu có)
        selected_fields: Optional[List[str]] = None, # Chỉ lọc lấy các trường mong muốn trong y
    ):
        self.page = page
        self.url_keyword = url_keyword
        self.target_key_path = target_key_path
        self.output_path = Path(output_file)
        self.unique_id_key = unique_id_key
        self.selected_fields = selected_fields

        self.collected_data: List[Dict[str, Any]] = []
        self._seen_ids: set = set()
        
        # Tín hiệu báo mỗi khi bắt được 1 gói tin mới thành công
        self.packet_received_event = asyncio.Event()

    def _extract_by_path(self, data: Dict[str, Any], path: str) -> Any:
        current = data
        for key in path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _filter_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if not self.selected_fields or not isinstance(item, dict):
            return item
        return {k: item.get(k) for k in self.selected_fields}

    async def _on_response(self, response: Response):
        if self.url_keyword not in response.url:
            return
        if response.status != 200 or response.request.method == "OPTIONS":
            return
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return

        try:
            payload = await response.json()
            extracted_y = self._extract_by_path(payload, self.target_key_path)
            if extracted_y is None:
                return
            items_list = extracted_y if isinstance(extracted_y, list) else [extracted_y]
            new_count = 0

            for item in items_list:
                if not isinstance(item, dict):
                    self.collected_data.append(item)
                    new_count += 1
                    continue

                if self.unique_id_key and self.unique_id_key in item:
                    item_id = str(item[self.unique_id_key])
                    if item_id in self._seen_ids:
                        continue
                    self._seen_ids.add(item_id)
    
                clean_item = self._filter_fields(item)
                self.collected_data.append(clean_item)
                new_count += 1

            print(f"[+] Bắt được API [{self.url_keyword}] -> Thêm {new_count} bản ghi mới (Tổng: {len(self.collected_data)})")
            
            # Phát tín hiệu báo đã nhận được dữ liệu
            self.packet_received_event.set()

        except Exception as e:
            print(f"[!] Lỗi khi xử lý JSON từ {response.url}: {e}")

    def start_listening(self):
        """Bắt đầu gắn tai nghe vào Page"""
        self.page.on("response", self._on_response)
        print(f"[*] Đang lắng nghe mọi Response chứa x='{self.url_keyword}', chờ lấy y='{self.target_key_path}'...")

    def stop_listening(self):
        """Gỡ tai nghe khỏi Page để giải phóng RAM"""
        self.page.remove_listener("response", self._on_response)

    async def wait_for_next_response(self, timeout: float = 15.0) -> bool:
        """Hàm tiện ích: Đợi cho đến khi gói tin chứa x tiếp theo nổ về"""
        self.packet_received_event.clear()
        try:
            await asyncio.wait_for(self.packet_received_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            print(f"[!] Quá thời gian chờ ({timeout}s) mà không thấy gói tin chứa '{self.url_keyword}'")
            return False

    def save_to_json(self):
        """BƯỚC 5: Lưu toàn bộ dữ liệu thu thập được vào file JSON"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, mode="w", encoding="utf-8") as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
        print(f"[✓] Đã lưu tổng cộng {len(self.collected_data)} bản ghi vào file: {self.output_path}")