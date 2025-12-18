# 🤖 eSIM Support Bot

Bot Telegram hỗ trợ tạo link cài đặt và QR code eSIM cho iPhone và Android với giao diện đơn giản và tự động nhận diện thông minh.

## ✨ Tính năng chính

### 🔗 Tạo Link & QR (Tự động nhận diện)
Bot tự động nhận diện và xử lý **5 định dạng** khác nhau:

1. **📝 LPA String**
   - Định dạng: `LPA:1$rsp.truphone.com$CODE123`
   - Tự động tạo link cài đặt + QR code

2. **📎 URL ảnh QR**
   - Ví dụ: `https://api.hisimtravel.com/images/abc123`
   - Bot tự động tải ảnh, đọc QR code và tạo link + QR mới

3. **🔗 URL text (carddata)**
   - Ví dụ: `https://esimsetup.apple.com/esim_qrcode_provisioning?carddata=...`
   - Tự động extract thông tin và tạo link + QR

4. **🔧 SM-DP+ Address**
   - Ví dụ: `rsp.truphone.com`
   - Tự động tạo link + QR (có thể thêm activation code)

5. **📋 QR data (text)**
   - Paste bất kỳ dữ liệu QR code nào
   - Bot tự động phân tích và tạo link + QR

**Kết quả:**
- ✅ Link cài đặt cho iPhone (iOS 17.4+)
- ✅ QR code để quét (iPhone & Android)
- ✅ Thông tin chi tiết (SM-DP+, Activation Code, LPA String)

### 🏪 Kho eSIM (Quản lý thông minh)

**Thêm eSIM vào kho:**
- Tự động nhận diện: LPA String, URL ảnh QR, hoặc SM-DP+ Address
- Thêm mô tả tùy chọn
- Lưu trữ an toàn trong SQLite database

**Sử dụng eSIM:**
- Xem danh sách eSIM có sẵn
- Chọn eSIM để tạo QR code và link cài đặt
- Tự động chuyển sang trạng thái "Đã sử dụng"
- Tracking: ai dùng, khi nào

**Xem lịch sử:**
- Danh sách eSIM đã sử dụng
- Thông tin người dùng và thời gian

### 📱 Hỗ trợ thiết bị
- **iPhone:** XS/XR trở lên (iOS 12.1+)
- **Android:** 9.0+ với hỗ trợ eSIM

## 🚀 Cài đặt

### 1. Yêu cầu hệ thống
```bash
Python 3.8+
```

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Tạo Telegram Bot
1. Nhắn tin cho [@BotFather](https://t.me/BotFather) trên Telegram
2. Gửi `/newbot` và làm theo hướng dẫn
3. Lưu lại Bot Token

### 4. Cấu hình
```bash
# Copy file config mẫu
cp config.example.py config.py

# Chỉnh sửa config.py với thông tin của bạn
```

Hoặc sử dụng environment variables:
```bash
export BOT_TOKEN="your_bot_token_here"
```

Thiết lập quyền admin (chỉ admin mới dùng được bot):
```python
# Trong config.py
ADMIN_IDS = [123456789]  # Telegram user_id của bạn
```

**Lấy User ID:**
```bash
# Chạy bot và gửi /myid để lấy user ID của bạn
python bot.py
```

### 5. Chạy bot
```bash
python bot.py
```

## 🔒 Bảo mật

- ⚠️ **KHÔNG BAO GIỜ** commit file `config.py` chứa token thật
- Sử dụng file `config.example.py` làm template  
- File `config.py` đã được thêm vào `.gitignore`
- Chỉ user có ID trong `ADMIN_IDS` mới sử dụng được bot

## 📖 Hướng dẫn sử dụng

### Menu chính (2 chức năng)

```
┌─────────────────────────────────┐
│  🔗 Tạo Link & QR  │  🏪 Kho eSIM  │
└─────────────────────────────────┘
```

### 🔗 Tạo Link & QR Code

**Bước 1:** Chọn "🔗 Tạo Link & QR"

**Bước 2:** Gửi một trong các định dạng sau:

**Ví dụ 1 - LPA String:**
```
LPA:1$rsp.truphone.com$CODE123
```

**Ví dụ 2 - URL ảnh QR:**
```
https://api.hisimtravel.com/images/abc123
```

**Ví dụ 3 - SM-DP+ Address:**
```
rsp.truphone.com
```

**Kết quả:** Bot tự động nhận diện và trả về:
- 🔗 Link cài đặt iPhone
- 📱 QR code để quét
- 📋 Thông tin chi tiết

### 🏪 Quản lý Kho eSIM

**Thêm eSIM vào kho:**
1. Chọn "🏪 Kho eSIM"
2. Chọn "➕ Thêm eSIM"
3. Gửi dữ liệu (LPA/URL/SM-DP+)
4. Bot tự động nhận diện và lưu
5. Thêm mô tả (tùy chọn)

**Sử dụng eSIM từ kho:**
1. Chọn "🏪 Kho eSIM"
2. Chọn "🎯 Sử dụng eSIM"
3. Chọn eSIM từ danh sách
4. Nhận QR code và link cài đặt
5. eSIM tự động chuyển sang "Đã sử dụng"

**Xem danh sách:**
- "📋 Xem Kho" - eSIM có sẵn
- "📊 eSIM Đã dùng" - Lịch sử sử dụng

## 🔧 Cấu trúc dự án

```
esim-bot/
├── bot.py              # Bot Telegram chính
├── config.py           # Cấu hình bot (KHÔNG commit token thật)
├── config.example.py   # Template cấu hình
├── esim_storage.py     # Quản lý kho eSIM (SQLite)
├── esim_tools.py       # Công cụ xử lý eSIM (link, QR, phân tích)
├── requirements.txt    # Thư viện Python
├── esim_storage.db     # Database SQLite (tự động tạo)
└── README.md           # Tài liệu này
```

## 📱 Các định dạng eSIM được hỗ trợ

### LPA Format
```
LPA:1$sm-dp-plus.address$activation-code
```

### SM-DP+ Address
```
rsp.truphone.com
esim.example.com
```

### URL Format
```
https://esimsetup.apple.com/esim_qrcode_provisioning?carddata=...
https://api.hisimtravel.com/images/abc123
```

## 🛠️ API Reference

### eSIMTools Class

#### `create_iphone_install_link(sm_dp_address, activation_code=None)`
Tạo link cài đặt eSIM cho iPhone
- **sm_dp_address**: Địa chỉ SM-DP+ server
- **activation_code**: Mã kích hoạt (tùy chọn)
- **Returns**: URL cài đặt

#### `create_qr_from_sm_dp(sm_dp_address, activation_code=None)`
Tạo QR code từ thông tin eSIM
- **Returns**: (BytesIO image, LPA string)

#### `create_qr_from_lpa(lpa_string)`
Tạo QR code từ LPA string
- **Returns**: (BytesIO image, LPA string)

#### `extract_sm_dp_and_activation(qr_data)`
Tách thông tin từ QR data
- **Returns**: Dict với sm_dp_address, activation_code, format_type

#### `decode_qr_from_image(image_data)`
Đọc QR code từ dữ liệu ảnh (sử dụng OpenCV)
- **Returns**: QR data string

#### `analyze_qr_image(image_data)`
Phân tích QR code từ ảnh
- **Returns**: Dict với thông tin chi tiết

#### `validate_sm_dp_address(sm_dp_address)`
Kiểm tra tính hợp lệ của SM-DP+ address
- **Returns**: (bool, message)

#### `validate_lpa_string(lpa_string)`
Kiểm tra tính hợp lệ của LPA string
- **Returns**: (bool, message)

### eSIMStorage Class

#### `add_esim(sm_dp_address, activation_code, description)`
Thêm eSIM vào kho
- **Returns**: esim_id

#### `add_esim_from_lpa(lpa_string, description)`
Thêm eSIM từ LPA string
- **Returns**: esim_id

#### `get_available_esims()`
Lấy danh sách eSIM có sẵn
- **Returns**: List[eSIMEntry]

#### `get_used_esims()`
Lấy danh sách eSIM đã sử dụng
- **Returns**: List[eSIMEntry]

#### `mark_esim_used(esim_id, used_by)`
Đánh dấu eSIM đã sử dụng
- **Returns**: bool

#### `get_storage_stats()`
Lấy thống kê kho eSIM
- **Returns**: Dict với total, available, used

## 🗄️ Database Schema

File: `esim_storage.db`

```sql
CREATE TABLE IF NOT EXISTS esim_entries (
    id TEXT PRIMARY KEY,
    sm_dp_address TEXT NOT NULL,
    activation_code TEXT,
    description TEXT,
    added_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'available', -- available | used
    used_date TEXT,
    used_by TEXT,
    lpa_string TEXT
);

CREATE INDEX IF NOT EXISTS idx_status ON esim_entries(status);
CREATE INDEX IF NOT EXISTS idx_added_date ON esim_entries(added_date);
```

## 🔒 Bảo mật

- Chỉ user có mặt trong `ADMIN_IDS` mới sử dụng được bot (toàn bộ tính năng)
- Token bot: dùng env var hoặc `config.py` (đừng commit token thật)
- Input validation: kiểm tra LPA/SM-DP+ trước khi xử lý
- Database: SQLite với index để tối ưu performance

## 🚨 Khắc phục sự cố

### Bot không khởi động
```bash
# Kiểm tra token
echo $BOT_TOKEN

# Kiểm tra dependencies
pip install -r requirements.txt

# Chạy với debug
python -u bot.py
```

### QR Code không đọc được từ ảnh
- Bot sử dụng OpenCV QRCodeDetector (không cần pyzbar)
- Đảm bảo ảnh rõ nét, không bị mờ
- Thử với ảnh khác hoặc gửi LPA string trực tiếp

### Database lỗi
```bash
# Xóa database cũ (nếu cần reset)
rm esim_storage.db

# Khởi động lại bot (database sẽ tự động tạo)
python bot.py
```

### Không nhận diện được định dạng
- Kiểm tra định dạng LPA: `LPA:1$...$...`
- Kiểm tra URL có thể truy cập được
- Kiểm tra SM-DP+ address hợp lệ (domain format)

## 📞 Commands Bot

- `/start` - Khởi động bot và xem menu
- `/help` - Xem hướng dẫn sử dụng
- `/cancel` - Hủy thao tác hiện tại
- `/myid` - Lấy Telegram User ID (để config admin)

## 🎯 Tính năng nổi bật

### ✨ Tự động nhận diện thông minh
- Không cần chọn menu phức tạp
- Bot tự động phát hiện loại dữ liệu
- Xử lý 5 định dạng khác nhau

### 🚀 Giao diện tối giản
- Chỉ 2 buttons chính
- UX đơn giản, dễ sử dụng
- Workflow nhanh chóng

### 🤖 Xử lý QR thông minh
- Đọc QR từ ảnh URL
- Sử dụng OpenCV (không cần pyzbar)
- Fallback thông minh khi gặp lỗi

### 📦 Quản lý kho hiệu quả
- Lưu trữ SQLite
- Tracking sử dụng
- Thống kê chi tiết

## 📄 License

MIT License - Xem file LICENSE để biết chi tiết.

## 🔄 Changelog

### v2.0.0 (2025) - Major Update
- ✅ **Đơn giản hóa menu:** Chỉ còn 2 buttons chính
- ✅ **Tự động nhận diện:** Hỗ trợ 5 định dạng khác nhau
- ✅ **Gộp chức năng:** Tạo Link & QR trong 1 chức năng
- ✅ **Hỗ trợ URL ảnh QR:** Tải và đọc QR từ URL
- ✅ **OpenCV fallback:** Không cần pyzbar
- ✅ **Kho eSIM thông minh:** Tự động nhận diện khi thêm

### v1.1.0 (2025)
- ✅ Thêm LPA string: tạo link và QR trực tiếp từ LPA
- ✅ Kho eSIM: thêm/sử dụng/theo dõi, tự chuyển sang Đã dùng
- ✅ Chỉ admin (ADMIN_IDS) mới dùng được bot
- ✅ Cải thiện xử lý editMessage khi nguồn là ảnh (fallback sendMessage)

### v1.0.0 (2024)
- ✅ Tạo link cài eSIM cho iPhone
- ✅ Tạo QR code từ SM-DP+ address
- ✅ Phân tích và tách thông tin QR
- ✅ Chuyển đổi QR thành link cài đặt
- ✅ Hướng dẫn cài đặt chi tiết

## 🚀 Roadmap

### v2.1.0
- [ ] Hỗ trợ nhiều ngôn ngữ
- [ ] Export/Import kho eSIM
- [ ] Thống kê chi tiết hơn
- [ ] Backup tự động

### v3.0.0
- [ ] Web dashboard
- [ ] API endpoints
- [ ] Bulk operations
- [ ] Docker deployment

---

**⭐ Nếu bot hữu ích, hãy star repo này!**

**💡 Có câu hỏi? Tạo issue trên GitHub!**
