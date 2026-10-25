---
name: add-demo-runner
description: >-
  Sau mỗi lần hoàn thành code cho bất kỳ module/class/function nào,
  tự động thêm block demo có thể chạy trực tiếp bằng "python <file>.py".
  Kích hoạt khi: AI vừa tạo file Python mới, hoặc thêm class/function
  quan trọng vào file hiện có.
---

# Skill: Thêm Demo Runner Có Thể Chạy Ngay

## Mục đích

Mỗi file Python mới phải có 1 block demo chạy được ngay lập tức bằng:

```bash
python src/extractors/html_extractor.py
python src/browser/manager.py
```

Không phải viết script riêng, không phải mở file test — chạy thẳng file luôn.

---

## Quy tắc bắt buộc

### 1. Luôn kết thúc file bằng `if __name__ == "__main__":`

Mọi file Python được tạo ra đều **PHẢI** có block này ở cuối file.

```python
# ─── Demo / Quick-test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())
```

---

### 2. Viết hàm `_demo()` phía trên block `__main__`

Tách hàm demo riêng để dễ đọc và có thể gọi từ test.

**Cấu trúc chuẩn:**

```python
async def _demo() -> None:
    """Demo nhanh để chạy thử trực tiếp: python <tên_file>.py"""
    # Import thêm ở đây nếu cần (chỉ dùng trong demo)
    # ...
    # Dữ liệu giả lập / fixture
    # ...
    # Gọi hàm / class chính
    # ...
    # In kết quả ra màn hình rõ ràng
    print("✅ Demo hoàn thành!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())
```

---

### 3. Nếu module KHÔNG async → dùng hàm sync

```python
def _demo() -> None:
    """Demo nhanh: python <tên_file>.py"""
    ...
    print("✅ Done!")


if __name__ == "__main__":
    _demo()
```

---

## Nội dung demo phải có

Demo phải đủ để **người đọc hiểu ngay module làm gì** khi chạy:

| Thành phần | Mô tả |
|---|---|
| **Setup dữ liệu** | Dữ liệu mẫu / fixture THỰC TẾ, không dùng `...` hay `pass` |
| **Gọi hàm chính** | Gọi class/function quan trọng nhất của module |
| **In kết quả** | `print()` kết quả ra console — rõ ràng, có label |
| **Xử lý lỗi** | Wrap trong `try/except`, in lỗi nếu có |

---

## Ví dụ thực tế theo từng loại module

### Ví dụ 1: Extractor (async)

```python
async def _demo() -> None:
    """Demo HtmlExtractor với HTML tĩnh — không cần browser thật."""
    from unittest.mock import AsyncMock

    # Dữ liệu HTML mẫu
    SAMPLE_HTML = """
    <ul>
      <li class="item"><h3><a href="/1">Tiêu đề 1</a></h3><span class="price">100.000đ</span></li>
      <li class="item"><h3><a href="/2">Tiêu đề 2</a></h3><span class="price">200.000đ</span></li>
    </ul>
    """

    # Mock page — không cần mở browser
    page = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.content = AsyncMock(return_value=SAMPLE_HTML)

    extractor = HtmlExtractor(
        page=page,
        item_selector="li.item",
        field_rules=[
            FieldRule("title", "h3 a"),
            FieldRule("url", "h3 a", attribute="href"),
            FieldRule("price", "span.price"),
        ],
        output_file="data/processed/demo_output.json",
        unique_id_key="url",
    )

    count = await extractor.extract_current_page()
    print(f"✅ Trích xuất được {count} bản ghi:")
    for item in extractor.collected_data:
        print(f"   {item}")
    extractor.save_to_json()


if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())
```

### Ví dụ 2: Service / HTTP client (async)

```python
async def _demo() -> None:
    """Demo nhanh: python src/services/kalodata.py"""
    import os
    from unittest.mock import patch, AsyncMock

    # Mock HTTP để không cần API key thật
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "data": [{"id": "123", "name": "Demo Creator", "revenue": 5000000}]
        }
        mock_get.return_value.status_code = 200

        result = fetch_creators(category_id="123456", page=1)
        print(f"✅ Lấy được {len(result)} creator:")
        for c in result:
            print(f"   {c}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())
```

### Ví dụ 3: Utility / Helper (sync)

```python
def _demo() -> None:
    """Demo nhanh: python src/utils/logger.py"""
    logger = get_logger("demo")
    logger.info("Đây là log INFO")
    logger.warning("Đây là log WARNING")
    logger.error("Đây là log ERROR giả lập")
    print("✅ Log đã được ghi vào logs/app.log và logs/errors.log")


if __name__ == "__main__":
    _demo()
```

### Ví dụ 4: Dataclass / Model (sync)

```python
def _demo() -> None:
    """Demo nhanh: python src/models/job.py"""
    sample = JobModel(
        id="job_001",
        title="Python Developer",
        salary="20-30 triệu",
        address="Hà Nội",
    )
    print(f"✅ Model tạo thành công: {sample}")
    print(f"   JSON: {sample.model_dump_json(indent=2)}")


if __name__ == "__main__":
    _demo()
```

---

## Nguyên tắc mock khi demo cần external dependency

Khi demo cần browser, HTTP, DB — **KHÔNG chạy thật**, dùng mock để demo vẫn
chạy được mà không cần setup phức tạp:

```python
# Browser mock — không cần Playwright thật
from unittest.mock import AsyncMock
page = AsyncMock()
page.content = AsyncMock(return_value="<html>...</html>")

# HTTP mock — không cần internet
from unittest.mock import patch
with patch("requests.get") as m:
    m.return_value.json.return_value = {"data": [...]}
    ...

# DB mock — không cần SQLite
with patch("aiosqlite.connect") as m:
    ...
```

---

## Khi nào KHÔNG cần thêm demo runner

- File chỉ chứa constants / config (không có logic)
- File `__init__.py` thuần export
- File migration / schema

---

## Checklist trước khi hoàn thành

- [ ] Có hàm `_demo()` phía trên block `__main__`
- [ ] Demo dùng dữ liệu mẫu THỰC TẾ (không phải `...`)
- [ ] Chạy `python <file>.py` không cần setup thêm
- [ ] Output demo rõ ràng, có label, có emoji ✅/❌
- [ ] Nếu async → dùng `asyncio.run(_demo())`
- [ ] Nếu cần external dep → mock nó
