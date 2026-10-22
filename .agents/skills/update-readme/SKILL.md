---
name: update-readme
description: >-
  Tự động quét toàn bộ codebase và viết lại README.md phản ánh đúng
  trạng thái hiện tại của dự án sau khi hoàn thành code.
  Kích hoạt khi: người dùng yêu cầu cập nhật README, hoặc sau khi
  thêm/sửa/xóa module, tính năng, dependency, hoặc cấu trúc thư mục.
---

# Skill: Tự Động Cập Nhật README.md

## Mục đích

Sau mỗi lần hoàn thành một tính năng hoặc refactor, AI phải cập nhật
`README.md` để phản ánh **chính xác** trạng thái hiện tại của dự án.
README lỗi thời gây nhầm lẫn cho người đọc — đây là lỗi nghiêm trọng.

---

## Quy trình thực hiện (BẮT BUỘC theo thứ tự)

### Bước 1 — Quét cấu trúc dự án thực tế

Dùng `list_dir` hoặc chạy lệnh tree để lấy cây thư mục THỰC TẾ:

`powershell
tree /F /A
`

Sau đó đọc từng thư mục quan trọng: `src/`, `config/`, `data/`, `logs/`.

### Bước 2 — Đọc các file quan trọng

Đọc những file sau để nắm đúng trạng thái dự án:

1. `requirements.txt` — danh sách dependencies thực tế
2. `config/settings.py` — các biến môi trường đang dùng
3. `.env.example` — template env đầy đủ
4. `main.py` — entry point, luồng chính của chương trình
5. Tất cả file trong `src/` — hiểu từng module làm gì

### Bước 3 — Viết lại README.md theo cấu trúc chuẩn

README phải có đủ các section theo thứ tự:

1. Tiêu đề + mô tả ngắn (1-2 câu)
2. ✨ Tính năng — liệt kê từ code thực tế
3. 📁 Cấu trúc dự án — cây thư mục THỰC TẾ có comment
4. 🚀 Cài đặt — clone, venv, pip install, cấu hình .env
5. 📖 Sử dụng — ví dụ lệnh chạy thực tế, luồng hoạt động
6. 🔧 Công nghệ — bảng lấy từ requirements.txt
7. 📝 Ghi chú — lưu ý quan trọng

### Bước 4 — Kiểm tra chất lượng trước khi lưu

Trước khi ghi vào file, AI phải tự kiểm tra:

- Cây thư mục có khớp với thực tế không? (không thiếu, không thừa)
- Danh sách tính năng có phản ánh đúng code hiện tại?
- Biến .env có lấy từ .env.example thực tế không?
- Bảng công nghệ có lấy từ requirements.txt thực tế không?
- Ví dụ lệnh chạy có đúng với main.py hiện tại không?
- Không có thông tin cũ/lỗi thời còn sót lại?

---

## Quy tắc viết README

### PHẢI làm
- Dùng emoji ở các heading chính (✨ 📁 🚀 📖 🔧 📝)
- Tên biến, file, lệnh đều wrap trong backtick
- Mỗi tính năng có mô tả súc tích, rõ nghĩa
- Cây thư mục comment mỗi file/folder quan trọng ở bên phải
- Ví dụ lệnh có thể chạy được ngay (không placeholder giả)

### KHÔNG được
- Bịa tính năng không có trong code
- Copy-paste cây thư mục cũ mà không kiểm tra lại
- Để biến .env không có trong .env.example
- Đề cập thư viện không có trong requirements.txt
- Xóa thông tin còn đúng mà không có lý do

---

## Khi nào kích hoạt skill này

Tự động kích hoạt khi người dùng:
- Nói "cập nhật README", "viết lại README", "update docs", "update README"
- Vừa hoàn thành thêm module/tính năng mới
- Vừa xóa hoặc đổi tên file/folder quan trọng
- Vừa thêm dependency mới vào requirements.txt
- Vừa thêm biến mới vào .env.example
