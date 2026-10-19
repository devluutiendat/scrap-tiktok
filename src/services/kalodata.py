import os
import sys
import json
import requests
from dotenv import load_dotenv
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

headers = {
    "secret-key": SECRET_KEY,
    "Content-Type": "application/json;charset=utf-8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

def _load_existing(file: str) -> list:
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _save_file(file: str, data: list):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_kalo_data(payload_data: object, url: str, file: str, id_name: str) -> dict:

    req_headers = headers.copy()
    req_headers["secret-key"] = SECRET_KEY

    try:
        response = requests.post(url, headers=req_headers, json=payload_data, timeout=30)
        logger.info("POST %s -> status=%d", url, response.status_code)

        try:
            result = response.json()
        except json.JSONDecodeError:
            logger.error("Response không phải định dạng JSON. Body: %s", response.text[:500])
            return None

        if not result:
            logger.warning("Response rỗng từ %s", url)
            return result

        raw_data = result.get("data", result)
        logger.debug("success=%s | raw_data type=%s", result.get('success'), type(raw_data).__name__)

        if isinstance(raw_data, list):
            new_items = raw_data
            logger.debug("data là list, số item nhận về: %d", len(new_items))

        elif isinstance(raw_data, dict):
            if id_name in raw_data:
                new_items = [raw_data]
                logger.debug("data là object đơn, id_name='%s' value='%s'", id_name, raw_data.get(id_name))
            else:
                new_items = next(
                    (v for v in raw_data.values() if isinstance(v, list)),
                    []
                )
                logger.debug("data là dict, tìm list con → %d item", len(new_items))

        else:
            logger.warning("raw_data không nhận diện được (type=%s), bỏ qua.", type(raw_data).__name__)
            return result

        if not new_items:
            logger.warning("Không có item nào để xử lý từ %s", url)
            return {"added": 0, "skipped": 0, "result": result}

        # --- Dedup ---
        existing = _load_existing(file)
        existing_ids = {item.get(id_name) for item in existing if isinstance(item, dict)}
        logger.debug("File hiện tại có %d item", len(existing))

        added = []
        skipped = 0
        for item in new_items:
            item_id = item.get(id_name) if isinstance(item, dict) else None
            if item_id is not None and item_id in existing_ids:
                skipped += 1
                print("BỎ QUA (đã tồn tại)")
            else:
                existing.append(item)
                if item_id is not None:
                    existing_ids.add(item_id)
                added.append(item)
                logger.debug("Thêm mới item id='%s'", item_id)

        _save_file(file, existing)
        logger.info("Thêm mới: %d item | Bỏ qua (trùng %s): %d item | Tổng trong file: %d",
                    len(added), id_name, skipped, len(existing))
        logger.info("Đã lưu dữ liệu vào %s", file)

        return {"added": len(added), "skipped": skipped, "result": result}

    except requests.exceptions.RequestException as e:
        logger.exception("Lỗi khi gửi request tới %s: %s", url, e)
        return None

URL = "https://www.kalodata.com/openapi/v1/tiktok/creator/rank"
OUTPUT_FILE = "creators.json"

def get_creator_list(page_number: int = 1, category_id: list = []) -> int:

    payload = {
        "region": "VN",
        "language": "vi-VN",
        "currency": "VND",
        "date_range": "last7Day",
        "sort_field": {
            "field": "revenue",
            "type": "DESC",
        },
        "category_ids": category_id,
        "category_id_list": ",".join(str(c) for c in category_id),
        "page_size": 100,
        "page_number": page_number,
    }

    logger.info("[creators] Đang lấy trang %d...", page_number)
    resp = get_kalo_data(
        payload_data=payload,
        url=URL,
        file=OUTPUT_FILE,
        id_name="creator_id",
    )

    if resp is None:
        logger.error("[creators] Lỗi khi gọi API, dừng lại.")
        return 0, 0

    added = resp.get("added", 0)
    skipped = resp.get("skipped", 0)
    fetched_count = added + skipped
    return added, fetched_count

def scrape_all_creators(category_id: list = []):

    page = 1
    total_added = 0

    logger.info("Bắt đầu thu thập danh sách Creator... Danh mục: %s", category_id)

    while True:
        added, fetched_count = get_creator_list(page_number=page, category_id=category_id)
        total_added += added
        logger.info("Trang %d: nhận %d creator (thêm mới: %d, tổng mới: %d)",
                    page, fetched_count, added, total_added)

        if fetched_count < 100:
            logger.info("Trang %d: số lượng data nhận về (%d) < 100 → Dừng vòng lặp.",
                        page, fetched_count)
            break

        page += 1

    logger.info("Hoàn tất! Tổng số creator mới thêm: %d", total_added)
