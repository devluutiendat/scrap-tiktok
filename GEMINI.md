# GEMINI.md — Hướng dẫn AI cho dự án `scrap-tiktok`

> File này định nghĩa hành vi, quy tắc, và ngữ cảnh cho AI assistant khi làm việc trong dự án này.  
> AI phải đọc và tuân thủ toàn bộ nội dung file này trong mỗi phiên làm việc.

---

## 1. Tổng quan dự án

| Thuộc tính      | Giá trị                                              |
|-----------------|------------------------------------------------------|
| **Tên dự án**   | `scrap`                     |
| **Mục tiêu**    | Thu thập, phân tích và tự động hóa dữ liệu từ bất kỳ nền tảng nào  |
| **Ngôn ngữ**    | Python (chính)                                       |
| **Database**    | PostgreSQL                                           |
| **Test**        | `pytest` + `pytest-cov`                             |
| **Config**      | `python-dotenv` + `.env` (template: `.env.example`) |
| **Scraping**    | Playwright (async) + httpx/requests + BeautifulSoup |

### Phạm vi dự án
Dự án bao gồm **ba trụ cột chính**:
1. **Thu thập dữ liệu** — Scrape/crawl nội dung từ bất kỳ nên tảng nào
2. **Phân tích dữ liệu** — Xử lý, chuẩn hóa, và lưu trữ dữ liệu vào PostgreSQL

### Cấu trúc thư mục chuẩn
```
scrap/
├── src/
│   ├── browser/        # Playwright context, stealth, proxy
│   ├── extractors/     # JSON/HTML extractors, response collectors
│   ├── models/         # Pydantic models / dataclasses
│   ├── services/       # Business logic (search, profile, trending...)
│   ├── storage/        # Database adapters (PostgreSQL)
│   ├── utils/          # Helpers, decorators, retry logic
│   └── logs/           # Log handlers
├── config/
│   └── settings.py     # Cấu hình tập trung dùng python-dotenv
├── data/               # Output data (JSON, CSV tạm thời)
├── tests/              # pytest test suite
├── .env                # Biến môi trường thực (KHÔNG commit)
├── .env.example        # Template biến môi trường (PHẢI commit)
├── requirements.txt
└── main.py             # Entrypoint chính
```

---

## 2. Ngôn ngữ giao tiếp

- **AI phải luôn phản hồi bằng Tiếng Việt**, kể cả khi câu hỏi viết bằng tiếng Anh.
- Comment trong code: **Tiếng Việt** để giải thích logic nghiệp vụ, **tiếng Anh** cho tên biến/hàm/class.
- Docstring: Viết bằng **Tiếng Anh** (theo chuẩn Google style).

---

## 3. Phong cách code Python

### 3.1 Quy tắc bắt buộc
- Tuân thủ **PEP8 nghiêm ngặt** — tối đa 100 ký tự mỗi dòng.
- **Type hints bắt buộc** cho tất cả function signatures, kể cả private methods.
- **Không bao giờ dùng `Any` thay thế** cho kiểu cụ thể nếu có thể tránh được.
- Dùng `dataclass` hoặc `Pydantic BaseModel` cho data structures — không dùng `dict` thuần.

```python
# ✅ Đúng
async def fetch_profile(user_id: str, timeout: float = 10.0) -> dict[str, Any]:
    ...

# ❌ Sai — thiếu type hints
async def fetch_profile(user_id, timeout=10):
    ...
```

### 3.2 Async/Await
- **Ưu tiên dùng `async/await`** bất cứ khi nào có I/O (HTTP requests, DB, file I/O).
- Tránh `asyncio.sleep()` quá dài không có lý do — luôn comment lý do delay.
- Dùng `asyncio.gather()` để chạy song song khi không có dependency giữa các task.

```python
# ✅ Chạy song song
results = await asyncio.gather(
    fetch_trending(),
    fetch_profile(uid),
)

# ❌ Chạy tuần tự không cần thiết
r1 = await fetch_trending()
r2 = await fetch_profile(uid)
```

### 3.3 Logging
- **Dùng `logging` chuẩn** — không dùng `print()` trong production code.
- Log đủ 4 level: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- **Không bao giờ để silent errors** — mọi `except` phải có `logger.error(...)` hoặc `logger.exception(...)`.
- Format log phải có timestamp, level, module name.

```python
import logging
logger = logging.getLogger(__name__)

# ✅ Đúng
try:
    data = await fetch_data()
except Exception as e:
    logger.exception("Không thể fetch dữ liệu: %s", e)
    raise

# ❌ Sai — silent error
try:
    data = await fetch_data()
except Exception:
    pass
```

### 3.4 Cấu hình & biến môi trường
- **Không bao giờ hardcode** URL, credentials, API key, timeout, hay bất kỳ giá trị magic nào.
- Mọi cấu hình phải đi qua `config/settings.py` (dùng `python-dotenv`).
- Khi thêm biến mới vào `.env`, **bắt buộc phải thêm vào `.env.example`** với giá trị mẫu.

```python
# config/settings.py
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
TIKTOK_SESSION_ID: str = os.getenv("TIKTOK_SESSION_ID", "")
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "15.0"))
```

### 3.5 Dependencies
- **Không thêm thư viện mới** mà không hỏi ý kiến trước.
- Ưu tiên dùng thư viện **đã có trong `requirements.txt`**.
- Nếu cần thư viện mới: đề xuất và giải thích lý do, chờ xác nhận rồi mới thêm vào `requirements.txt`.

---

## 4. Quy tắc bảo toàn code

### 4.1 Không xóa comment/docstring
- **Tuyệt đối không xóa** bất kỳ comment hay docstring nào đã có, kể cả khi refactor.
- Nếu logic thay đổi, **cập nhật comment** cho phù hợp thay vì xóa.

### 4.2 Luôn giải thích thay đổi
Khi sửa code, AI phải:
1. Nêu rõ **lý do** thay đổi
2. Mô tả **tác động** có thể xảy ra
3. Chỉ ra **điểm khác biệt** so với code cũ

### 4.3 Không tự ý refactor lớn
- Chỉ thay đổi đúng phần được yêu cầu.
- Nếu phát hiện vấn đề khác cần sửa, **hỏi trước**, không tự động sửa.

---

## 5. Kiểm thử (Testing)

- **Luôn viết unit test** kèm theo mọi function/class mới tạo.
- Framework: `pytest` + `pytest-cov`
- Test file đặt trong `tests/`, tên file: `test_<module_name>.py`
- Coverage target: **>= 80%** cho mọi module mới
- Mock external calls (HTTP, DB) — không gọi API thật trong test

```python
# tests/test_json_extractor.py
import pytest
from unittest.mock import AsyncMock, patch
from src.extractors.json_extractor import ResponseCollector

@pytest.mark.asyncio
async def test_collector_filters_duplicates():
    """Verify ResponseCollector deduplicates correctly by unique_id_key."""
    ...
```

---

## 6. Database (PostgreSQL)

- Dùng **asyncpg** hoặc **SQLAlchemy async** cho kết nối PostgreSQL.
- Mọi truy vấn phải dùng **parameterized queries** — không bao giờ format string SQL trực tiếp.
- Có migration script cho schema changes — không sửa DB tay.

```python
# ✅ Đúng — parameterized
await conn.execute("INSERT INTO videos (id, title) VALUES ($1, $2)", vid_id, title)

# ❌ Sai — SQL injection risk
await conn.execute(f"INSERT INTO videos (id, title) VALUES ('{vid_id}', '{title}')")
```

---

## 7. Scraping / Browser Automation

- Dùng **Playwright async** là phương thức ưu tiên cho scraping cần JavaScript.
- Luôn có **retry logic** với exponential backoff cho HTTP requests.
- Giả lập hành vi người dùng: thêm delay ngẫu nhiên, không crawl quá nhanh.
- Quản lý session/cookie cẩn thận — lưu vào file, không hardcode.

```python
# ✅ Delay ngẫu nhiên giống người thật
import random
await asyncio.sleep(random.uniform(1.0, 3.0))  # Nghỉ ngẫu nhiên 1-3 giây
```

---

## 8. Git & Bảo mật

- **Không bao giờ commit** file `.env`, session cookies, hay API keys.
- Đảm bảo `.gitignore` có: `.env`, `*.session`, `data/raw/`, `__pycache__/`, `.venv/`
- Message commit: tiếng Anh, theo format `type(scope): description` (Conventional Commits)

```
feat(extractor): add field selection support for ResponseCollector
fix(browser): handle timeout on pagination click
chore(deps): add asyncpg to requirements.txt
```

---

## 9. Quy trình làm việc với AI

Khi nhận yêu cầu, AI phải:

1. **Đọc lại context** — hiểu code hiện tại trước khi đề xuất
2. **Đề xuất hướng giải quyết** — không code ngay nếu yêu cầu mơ hồ
3. **Implement** — theo đúng phong cách đã định nghĩa ở trên
4. **Kèm test** — luôn viết unit test cho code mới
5. **Giải thích thay đổi** — tóm tắt những gì đã thay đổi và tại sao

### Những điều AI KHÔNG được làm
- Xóa comment/docstring cũ
- Hardcode giá trị cấu hình
- Dùng `print()` thay vì `logging`
- Thêm thư viện mới không hỏi trước
- Bỏ qua exceptions (silent errors)
- Viết code thiếu type hints
- Tự refactor code ngoài phạm vi yêu cầu

---

*Cập nhật lần cuối: 2026-10-18 | Dự án: devluutiendat/scrap*
