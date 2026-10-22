# 🕷️ Crapy — Web Scraping Toolkit

Công cụ thu thập và phân tích dữ liệu từ các nền tảng web sử dụng Camoufox (chống bot) và Playwright async.  
Hiện tại đang scrape **dữ liệu việc làm từ TopCV** thông qua API nội bộ.

## ✨ Tính năng

- **Bắt API Response tự động** — `ResponseCollector` lắng nghe mọi network response khớp URL keyword, tự động trích xuất dữ liệu JSON theo key path tùy chọn
- **Chống bot (Anti-detection)** — sử dụng Camoufox với fingerprint giả lập, chặn ảnh/font/video để tăng tốc crawl
- **Quản lý session bền vững** — lần đầu mở trình duyệt thủ công để đăng nhập, các lần sau chạy headless tự động
- **Lọc trùng lặp (Dedup)** — tự động bỏ qua bản ghi đã tồn tại theo `unique_id_key`
- **Chọn field linh hoạt** — chỉ trích xuất những trường cần thiết từ response JSON
- **Lưu kết quả JSON** — output lưu vào `data/processed/` tự động
- **Theo dõi run (RunTracker)** — ghi lại số lượng thành công/lỗi, lưu summary mỗi lần chạy

## 📁 Cấu trúc dự án

`
crapy/
├── main.py                          # Entry point — scrape TopCV jobs
├── config/
│   └── settings.py                  # Cấu hình tập trung (python-dotenv)
├── src/
│   ├── browser/
│   │   └── manager.py               # Camoufox context factory, stealth browser
│   ├── extractors/
│   │   └── json_extractor.py        # ResponseCollector — bắt & trích xuất API response
│   ├── models/                       # (Mở rộng) Pydantic/dataclass models
│   ├── services/                     # (Mở rộng) Business logic
│   ├── storage/                      # (Mở rộng) Database adapters
│   └── utils/
│       └── logger.py                # get_logger(), RunTracker
├── data/
│   ├── processed/                   # Dữ liệu đã xử lý (jobs.json, ...)
│   └── browser_profile/             # Persistent browser session (tự sinh, không commit)
├── logs/
│   └── errors.log                   # Log lỗi runtime
├── .agents/
│   └── skills/
│       └── update-readme/           # Skill tự động cập nhật README
├── .env                              # Biến môi trường (KHÔNG commit)
├── .env.example                     # Template env (PHẢI commit)
├── requirements.txt
└── README.md
`

## 🚀 Cài đặt

### 1. Clone repo

`ash
git clone https://github.com/devluutiendat/scrap-tiktok.git
cd scrap-tiktok
`

### 2. Tạo môi trường ảo

`ash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
`

### 3. Cài đặt dependencies

`ash
pip install -r requirements.txt
`

### 4. Cấu hình `.env`

Tạo file `.env` từ template:

`ash
cp .env.example .env
`

Nội dung `.env`:

`env
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
`

## 📖 Sử dụng

### Chạy scraper

`ash
python main.py
`

### Luồng hoạt động

1. **Lần đầu chạy** — Camoufox mở trình duyệt có giao diện (headless=False) để người dùng đăng nhập thủ công. Profile được lưu tự động vào `data/browser_profile/`
2. **Các lần sau** — Phát hiện profile đã có → chạy ngầm (headless=True)
3. `ResponseCollector` bắt đầu lắng nghe network response chứa `/api-featured-jobs`
4. Playwright mở `https://www.topcv.vn/` — request trang tự động trigger API jobs
5. Response được bắt, trích xuất các field: `address`, `id`, `salary`, `title`
6. Kết quả dedup theo `id` và lưu vào `data/processed/jobs.json`

### Output mẫu

`json
[
  {
    "address": "Hà Nội",
    "id": 123456,
    "salary": "15 - 20 triệu",
    "title": "Python Developer"
  }
]
`

## 🔧 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.10+ |
| Browser Automation | `camoufox[geoip]` >= 0.5.8 (Playwright wrapper) |
| HTTP Client | `requests` >= 2.31.0 |
| Đọc Excel | `pandas` >= 2.0.0 + `openpyxl` >= 3.1.0 |
| Quản lý env | `python-dotenv` >= 1.0.0 |

## 📝 Ghi chú

- `data/browser_profile/` lưu session đăng nhập — **không commit** vào git
- `data/processed/jobs.json` sẽ bị ghi đè mỗi lần chạy nếu không đổi tên
- Nếu gặp `TimeoutError` khi load trang, tăng `BROWSER_TIMEOUT` trong `.env` (đơn vị: ms)
- Camoufox tải fingerprint model lần đầu sử dụng (~vài giây) — bình thường
- Thư mục `models/`, `services/`, `storage/` đang trống, dự kiến mở rộng cho các tính năng scraping khác
