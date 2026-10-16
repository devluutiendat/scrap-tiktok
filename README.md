# 🛒 Scrap TikTok Shop

Công cụ thu thập dữ liệu TikTok Shop — tìm kiếm danh mục sản phẩm và cào danh sách Creator theo danh mục thông qua API Kalodata.

## ✨ Tính năng

- **Tìm kiếm danh mục TikTok Shop** — tra cứu nhanh từ file Excel chứa toàn bộ danh mục TikTok Shop Việt Nam
- **Cào danh sách Creator** — tự động phân trang, gọi API Kalodata để lấy danh sách Creator xếp hạng theo doanh thu
- **Chống trùng lặp (Dedup)** — tự động bỏ qua Creator đã tồn tại trong file JSON, chỉ thêm mới
- **Quản lý trình duyệt** — module Playwright sẵn sàng cho các tác vụ scraping nâng cao

## 📁 Cấu trúc dự án

```
crapy/
├── main.py                          # Entry point — CLI tương tác
├── config/
│   └── settings.py                  # Cấu hình chung (đang mở rộng)
├── src/
│   ├── brower/
│   │   └── manager.py               # Quản lý Playwright browser context
│   ├── extractors/                   # (Dự kiến) Trích xuất dữ liệu từ HTML
│   ├── models/                       # (Dự kiến) Định nghĩa data model
│   ├── services/
│   │   ├── kalodata.py               # Gọi API Kalodata — lấy & lưu Creator
│   │   └── search.py                 # Tìm kiếm danh mục từ file Excel
│   └── storage/
│       └── TikTok_Shop_Category.xlsx # Dữ liệu danh mục TikTok Shop VN
├── data/
│   ├── raw/                          # Dữ liệu thô
│   └── processed/                    # Dữ liệu đã xử lý
├── .env                              # Biến môi trường (không commit)
├── .gitignore
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

### 4. Cài Playwright browsers (nếu cần dùng module browser)

```bash
playwright install chromium
```

### 5. Cấu hình `.env`

Tạo file `.env` ở thư mục gốc với nội dung:

```env
# Kalodata API
SECRET_KEY=your_kalodata_secret_key

# Google Sheets (nếu cần)
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT=service_account.json

# ERP
ERP_BASE_URL=https://your-erp-url.com
API_KEY_ERP=your_erp_api_key

# Gmail (nếu cần)
GMAIL_USER=
GMAIL_APP_PASSWORD=

# Gemini AI (nếu cần)
GEMINI_API_KEY=your_gemini_api_key
```

## 📖 Sử dụng

### Chạy chương trình với từ khóa tìm kiếm

```bash
python main.py <từ khóa danh mục>
```

**Ví dụ:**

```bash
python main.py "thời trang"
```

### Luồng hoạt động

1. Chương trình tìm kiếm danh mục TikTok Shop khớp với từ khóa
2. Hiển thị danh sách kết quả (ID, tên danh mục, danh mục cha, có phải danh mục lá)
3. Người dùng chọn danh mục muốn cào (nhập STT, cách nhau bằng dấu phẩy) hoặc nhấn Enter để lấy tất cả danh mục lá
4. Tự động gọi API Kalodata để thu thập Creator theo danh mục đã chọn
5. Kết quả được lưu vào file `creators.json` (tự động dedup)

### Ví dụ output

```
 CÔNG CỤ TÌM KIẾM DANH MỤC TIKTOK SHOP
Tìm thấy 5 kết quả phù hợp với từ khóa 'thời trang':

1. [ID: 601234]
   - Tên danh mục: Thời trang nữ
   - Danh mục cha: Thời trang
   - Là danh mục lá: True
--------------------------------------------------

Nhập STT danh mục muốn cào (cách nhau bằng dấu phẩy, ví dụ: 1,3).
Để trống và nhấn Enter → lấy tất cả danh mục lá (Là danh mục lá = True):
Chọn: 1

Đang cào 1 danh mục: ['Thời trang nữ']
Bắt đầu thu thập danh sách Creator...
```

## 🔧 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.10+ |
| HTTP Client | `requests` |
| Đọc Excel | `pandas` + `openpyxl` |
| Browser Automation | `playwright` |
| Quản lý env | `python-dotenv` |
| API dữ liệu | [Kalodata OpenAPI](https://www.kalodata.com) |

## 📝 Ghi chú

- File `creators.json` được lưu ở thư mục gốc, chứa danh sách Creator đã cào (dedup theo `creator_id`)
- File `TikTok_Shop_Category.xlsx` chứa toàn bộ danh mục TikTok Shop VN — nguồn từ [TikTok Shop Partner Center API](https://partner.tiktokshop.com)
- Các thư mục `extractors/` và `models/` hiện đang trống, dự kiến mở rộng cho các tính năng scraping nâng cao
