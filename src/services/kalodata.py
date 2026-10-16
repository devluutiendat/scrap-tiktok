import os
import sys
import json
import requests
from dotenv import load_dotenv
load_dotenv()

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
        print(f"Status Code: {response.status_code}")

        try:
            result = response.json()
        except json.JSONDecodeError:
            print("Response không phải định dạng JSON:")
            print(response.text)
            return None

        if not result:
            print("Response rỗng.")
            return result

        raw_data = result.get("data", result)
        print(f"[DEBUG] success={result.get('success')} | raw_data type={type(raw_data).__name__}")

        if isinstance(raw_data, list):
            new_items = raw_data
            print(f"[DEBUG] data là list, số item nhận về: {len(new_items)}")

        elif isinstance(raw_data, dict):
            if id_name in raw_data:
                new_items = [raw_data]
                print(f"[DEBUG] data là object đơn, id_name='{id_name}' value='{raw_data.get(id_name)}'")
            else:
                new_items = next(
                    (v for v in raw_data.values() if isinstance(v, list)),
                    []
                )
                print(f"[DEBUG] data là dict, tìm list con → {len(new_items)} item")

        else:
            print(f"[DEBUG] raw_data không nhận diện được (type={type(raw_data).__name__}), bỏ qua.")
            return result

        if not new_items:
            print("[WARN] Không có item nào để xử lý.")
            return {"added": 0, "skipped": 0, "result": result}

        # --- Dedup ---
        existing = _load_existing(file)
        existing_ids = {item.get(id_name) for item in existing if isinstance(item, dict)}
        print(f"[DEBUG] File hiện tại có {len(existing)} item | existing_ids={existing_ids}")

        added = []
        skipped = 0
        for item in new_items:
            item_id = item.get(id_name) if isinstance(item, dict) else None
            print(f"[DEBUG] Xử lý item id_name='{id_name}' value='{item_id}'", end=" → ")
            if item_id is not None and item_id in existing_ids:
                skipped += 1
                print("BỎ QUA (đã tồn tại)")
            else:
                existing.append(item)
                if item_id is not None:
                    existing_ids.add(item_id)
                added.append(item)
                print("THÊM MỚI")

        _save_file(file, existing)
        print(f"\nThêm mới: {len(added)} item | Bỏ qua (trùng {id_name}): {skipped} item")
        print(f"Tổng số item trong file: {len(existing)}")
        print(f"Đã lưu dữ liệu vào {file}")

        return {"added": len(added), "skipped": skipped, "result": result}

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi request: {e}")
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

    print(f"\n[creators] Đang lấy trang {page_number}...")
    resp = get_kalo_data(
        payload_data=payload,
        url=URL,
        file=OUTPUT_FILE,
        id_name="creator_id",
    )

    if resp is None:
        print("[creators] Lỗi khi gọi API, dừng lại.")
        return 0, 0

    added = resp.get("added", 0)
    skipped = resp.get("skipped", 0)
    fetched_count = added + skipped
    return added, fetched_count

def scrape_all_creators(category_id: list = []):

    page = 1
    total_added = 0

    print("Bắt đầu thu thập danh sách Creator...")
    print(f"Danh mục: {category_id}")

    while True:
        added, fetched_count = get_creator_list(page_number=page, category_id=category_id)
        total_added += added
        print(f"[main] Trang {page}: nhận {fetched_count} creator (thêm mới: {added}, tổng mới: {total_added})")

        if fetched_count < 100:
            print(f"\n[main] Trang {page}: Số lượng data nhận về ({fetched_count}) < 100 → Dừng vòng lặp.")
            break

        page += 1

    print("\n" + "=" * 50)
    print(f"Hoàn tất! Tổng số creator mới thêm: {total_added}")
    print("=" * 50)