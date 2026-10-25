---
name: code-cleanup
description: >-
  Kích hoạt sau mỗi lần thay đổi code để dọn dẹp các phần thừa:
  import không dùng, dead code, biến/tham số/method không còn được tham chiếu,
  comment lỗi thời, và các artifact debug tạm thời còn sót lại.
  Dùng khi: người dùng yêu cầu "dọn code", "xóa phần thừa", "cleanup", hoặc
  sau khi hoàn thành refactor/thêm tính năng mới.
---

# Code Cleanup Skill

Thực hiện dọn dẹp code sau mỗi lần thay đổi để đảm bảo codebase luôn gọn gàng,
không có dead code hay import thừa.

---

## Bước 1 — Xác định phạm vi cleanup

Đọc các file đã được chỉnh sửa gần nhất (từ context hiện tại hoặc yêu cầu của user).
Với mỗi file Python cần cleanup, thực hiện các bước 2–6 dưới đây.

---

## Bước 2 — Phát hiện import không dùng

Chạy lệnh sau cho từng file cần kiểm tra:

```powershell
.venv\Scripts\python.exe -m pyflakes <path/to/file.py>
```

Nếu chưa có `pyflakes`:
```powershell
.venv\Scripts\pip install pyflakes --quiet
```

Kết quả sẽ liệt kê từng dòng import thừa theo dạng:
```
file.py:3:1: 'os' imported but unused
```

**Xóa toàn bộ import được báo là `imported but unused`.**

> Ngoại lệ: Giữ lại import nếu có comment `# noqa` hoặc được dùng trong `TYPE_CHECKING`.

---

## Bước 3 — Phát hiện biến / tham số / method không dùng

Sau khi xóa import thừa, chạy lại pyflakes để bắt thêm:
- `local variable 'x' is assigned to but never used`
- `undefined name 'x'` (import bị xóa nhưng vẫn còn dùng — cần khôi phục)

Xử lý từng cảnh báo:
- **`assigned to but never used`** → Xóa dòng gán hoặc đổi tên thành `_` nếu là loop variable.
- **`undefined name`** → Khôi phục import tương ứng (đã xóa nhầm).

---

## Bước 4 — Kiểm tra dead code thủ công

Dùng `grep_search` để tìm các dấu hiệu dead code:

| Pattern cần tìm | Ý nghĩa |
|---|---|
| `# TODO`, `# FIXME`, `# HACK` | Comment tạm chưa giải quyết — báo cáo cho user |
| `pass` trong class/function không rỗng | Block thừa |
| Method/function định nghĩa nhưng không gọi ở đâu | Candidate để xóa (hỏi user trước) |
| Flag boolean như `_needs_screenshot`, `_pending_*` còn sót | State tạm không còn dùng |

> **Quan trọng**: Chỉ tự xóa những gì chắc chắn không dùng. Nếu nghi ngờ,
> **hỏi user** trước khi xóa method/class.

---

## Bước 5 — Dọn comment lỗi thời

Tìm và cập nhật các comment không còn đúng với code hiện tại:

- Comment mô tả logic cũ đã bị thay thế
- Docstring tham chiếu đến tham số/method đã xóa
- Comment `# Đánh dấu cần X — sẽ được gọi bởi Y` nếu flow đã thay đổi

**Không xóa comment/docstring hợp lệ** — chỉ cập nhật khi chắc chắn sai.

---

## Bước 6 — Xác nhận syntax hợp lệ

Sau khi cleanup, chạy kiểm tra cú pháp:

```powershell
.venv\Scripts\python.exe -m py_compile <path/to/file.py> && Write-Host "OK"
```

Nếu có lỗi syntax → sửa trước khi báo hoàn thành.

Sau đó chạy import test để đảm bảo module vẫn importable:

```powershell
.venv\Scripts\python.exe -c "import <module.path>; print('Import OK')"
```

---

## Bước 7 — Báo cáo kết quả

Tóm tắt những gì đã xóa/cập nhật theo format:

```
### Cleanup: <tên file>
- ❌ Xóa import: `from x import Y` (không dùng)
- ❌ Xóa biến: `_needs_screenshot` (đã thay bằng `_pending_snapshot_html`)
- 📝 Cập nhật comment dòng 45: mô tả cũ → mô tả mới
- ✅ Giữ nguyên: `_pending_snapshot_html` (vẫn được dùng)
```

Nếu không có gì cần xóa → báo: `✅ <file> đã sạch, không có dead code.`

---

## Lưu ý quan trọng

- **Không tự refactor** ngoài phạm vi cleanup được yêu cầu.
- **Không xóa** method/class mà không hỏi user nếu không chắc chắn.
- **Không xóa** comment/docstring kể cả khi có vẻ thừa — chỉ cập nhật khi sai.
- Luôn chạy **pyflakes + py_compile** để verify sau khi xóa.
