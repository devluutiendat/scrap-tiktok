# 🕷️ Crapy — Web Scraping Toolkit

Công cụ thu thập và phân tích dữ liệu từ các nền tảng web sử dụng Camoufox (chống bot) và Playwright async.
Hỗ trợ scrape cả **API response** (SPA) lẫn **HTML trực tiếp** (SSR).

## ✨ Tính năng

- **Bắt API Response tự động** — `ResponseCollector` lắng nghe mọi network response khớp URL keyword, trích xuất JSON theo key path tùy chọn
- **Scrape HTML (SSR)** — `HtmlExtractor` đọc DOM sau khi JS render xong, parse bằng BeautifulSoup4 + lxml theo `FieldRule` khai báo sẵn
- **Phân trang tự động** — `PaginationConfig` tự động click "Trang sau" với delay ngẫu nhiên giống người thật
- **Chống bot (Anti-detection)** — Camoufox với fingerprint giả lập, chặn ảnh/font/video để tăng tốc crawl
- **Quản lý session bền vững** — lần đầu mở trình duyệt thủ công để đăng nhập, các lần sau chạy headless tự động
- **Lọc trùng lặp (Dedup)** — tự động bỏ qua bản ghi đã tồn tại theo `unique_id_key`
- **Transform field** — gọi callable tùy ý trên giá trị thô (strip, int, regex, v.v.)
- **Lưu kết quả JSON** — output lưu vào `data/processed/` tự động
- **Theo dõi run (RunTracker)** — ghi lại số thành công/lỗi và lưu summary mỗi lần chạy
- **Logging chuẩn** — console + file rotating, screenshot tự động khi có lỗi browser

## 📁 Cấu trúc dự án

```
crapy/
├── main.py                          # Entry point — scrape TopCV jobs (SSR + API)
├── config/
│   └── settings.py                  # Cấu hình tập trung (python-dotenv)
├── src/
│   ├── __init__.py
│   ├── browser/
│   │   └── manager.py               # Camoufox context factory, stealth browser, session
│   ├── extractors/
│   │   ├── __init__.py              # Export ResponseCollector, HtmlExtractor, FieldRule
│   │   ├── json_extractor.py        # ResponseCollector — bắt & trích xuất API response JSON
│   │   └── html_extractor.py        # HtmlExtractor — parse HTML trang SSR (BeautifulSoup4)
│   ├── models/                       # (Mở rộng) Pydantic/dataclass models
│   ├── services/
│   │   ├── kalodata.py               # Gọi API Kalodata — lấy danh sách Creator TikTok Shop
│   │   └── search.py                 # Tìm kiếm danh mục TikTok Shop từ file Excel
│   ├── storage/                      # (Mở rộng) SQLite async adapters
│   └── utils/
│       └── logger.py                # get_logger(), RunTracker, log_browser_exception()
├── tests/
│   ├── conftest.py                  # pytest sys.path config
│   └── test_html_extractor.py       # 8 unit tests cho HtmlExtractor (coverage 72%)
├── data/
│   ├── processed/                   # Dữ liệu đã xử lý (jobs.json, ...)
│   └── browser_profile/             # Persistent browser session (tự sinh, không commit)
├── logs/
│   ├── app.log                       # Log toàn bộ (INFO+), rotating 5MB
│   ├── errors.log                    # Chỉ log ERROR+, rotating 5MB
│   └── run_history.jsonl            # Lịch sử mỗi lần chạy (JSON Lines)
├── .agents/
│   └── skills/
│       └── update-readme/           # Skill tự động cập nhật README sau khi code
├── .env                              # Biến môi trường (KHÔNG commit)
├── .env.example                     # Template env (PHẢI commit)
├── GEMINI.md                         # Quy tắc AI cho dự án này
├── requirements.txt
└── README.md
```

## 🚀 Cài đặt

### 1. Clone repo

```bash
git clone https://github.com/devluutiendat/scrap-tiktok.git
cd scrap-tiktok
```

### 2. Tạo môi trường ảo

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình `.env`

Tạo file `.env` từ template:

```bash
cp .env.example .env
```

Điền các giá trị cần thiết:

```env
# Browser / Camoufox
BROWSER_PROFILE_DIR=data/browser_profile
BROWSER_TIMEOUT=30000

# Database
SQLITE_DB_PATH=data/scrap.db

# HTTP
REQUEST_TIMEOUT=15.0

# TikTok (nếu cần)
TIKTOK_SESSION_ID=

# Google Sheets (nếu cần)
GOOGLE_SPREADSHEET_ID=
GOOGLE_SERVICE_ACCOUNT=service_account.json

# Gmail (nếu cần)
GMAIL_USER=
GMAIL_APP_PASSWORD=

# Gemini AI (nếu cần)
GEMINI_API_KEY=
```

## 📖 Sử dụng

### Chạy scraper mặc định (TopCV jobs)

```bash
python main.py
```

### Luồng hoạt động

1. **Lần đầu chạy** — Camoufox mở trình duyệt có giao diện (headless=False) để đăng nhập thủ công. Profile lưu tự động vào `data/browser_profile/`
2. **Các lần sau** — Phát hiện profile đã có → chạy ngầm (headless=True)
3. `ResponseCollector` bắt đầu lắng nghe API `/api-featured-jobs`
4. Playwright mở `https://www.topcv.vn/` → request tự động trigger API
5. Kết quả được dedup theo `id` và lưu vào `data/processed/jobs.json`

### Sử dụng HtmlExtractor (SSR websites)

```python
from src.browser.manager import create_camoufox_context
from src.extractors import HtmlExtractor, FieldRule, PaginationConfig

async with create_camoufox_context(target_url="https://example.com") as context:
    page = await context.new_page()
    await page.goto("https://example.com/tin-tuc")

    extractor = HtmlExtractor(
        page=page,
        item_selector="article.news-item",   # CSS selector cho mỗi item
        field_rules=[
            FieldRule("title", "h3.title a"),
            FieldRule("url", "h3.title a", attribute="href"),
            FieldRule("summary", "p.description"),
            FieldRule("tags", "span.tag", multiple=True),  # List
        ],
        output_file="data/processed/news.json",
        unique_id_key="url",                  # Dedup theo URL
        pagination=PaginationConfig(
            next_button_selector="a.next-page",
            max_pages=5,
        ),
    )

    await extractor.extract_all_pages()
    extractor.save_to_json()
```

### Chạy tests

```bash
pytest tests/ -v --asyncio-mode=auto
```

## 🔧 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.10+ |
| Browser Automation | `camoufox[geoip]` >= 0.5.8 (Playwright wrapper, anti-bot) |
| HTML Parser | `beautifulsoup4` >= 4.12.0 + `lxml` >= 5.0.0 |
| HTTP Client | `requests` >= 2.31.0 |
| Đọc Excel | `pandas` >= 2.0.0 + `openpyxl` >= 3.1.0 |
| Quản lý env | `python-dotenv` >= 1.0.0 |
| Testing | `pytest` + `pytest-asyncio` + `pytest-cov` |

## 📝 Ghi chú

- `data/browser_profile/` lưu session đăng nhập — **không commit** vào git
- `logs/run_history.jsonl` ghi lịch sử từng lần chạy (status, duration, error count)
- Nếu gặp `TimeoutError` khi load trang, tăng `BROWSER_TIMEOUT` trong `.env` (đơn vị ms)
- Camoufox tải fingerprint model lần đầu (~vài giây) — bình thường
- Để xem HTML trang SSR đang dùng selector gì: mở DevTools (F12) → Elements tab → click chuột phải → Copy selector
- Chọn strategy: nếu trang có API call trong Network tab → dùng `ResponseCollector`; nếu không → dùng `HtmlExtractor`
