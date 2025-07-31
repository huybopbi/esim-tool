# 🤖 eSIM Support Bot

Bot Telegram hỗ trợ cài đặt eSIM cho iPhone và Android với các công cụ chuyên nghiệp.

## ✨ Tính năng chính

### 🔧 Công cụ eSIM
- **🔗 Tạo Link Cài eSIM** - Tạo link cài đặt nhanh cho iPhone từ SM-DP+ address
- **📱 Tạo QR Code** - Tạo QR code eSIM từ SM-DP+ address và mã kích hoạt  
- **🔍 Phân Tích QR** - Tách thông tin SM-DP+ và activation code từ QR code
- **📋 Link từ QR** - Chuyển đổi QR code thành link cài đặt

### 📱 Hỗ trợ thiết bị
- **iPhone:** XS/XR trở lên (iOS 12.1+)
- **Android:** 9.0+ với hỗ trợ eSIM

### 🆘 Hỗ trợ khách hàng
- Hướng dẫn cài đặt chi tiết
- Khắc phục sự cố thường gặp
- Kiểm tra tương thích thiết bị

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

### 5. Chạy bot
```bash
python bot.py
```

## 🔒 Bảo mật

- ⚠️ **KHÔNG BAO GIỜ** commit file `config.py` chứa token thật
- Sử dụng file `config.example.py` làm template  
- File `config.py` đã được thêm vào `.gitignore`

## 📖 Hướng dẫn sử dụng

### Tạo Link Cài eSIM cho iPhone
1. Chọn **🔗 Tạo Link Cài eSIM**
2. Nhập SM-DP+ Address (ví dụ: `rsp.truphone.com`)
3. Nhập Activation Code (tùy chọn)
4. Nhận link cài đặt: `https://esimsetup.apple.com/esim_qrcode_provisioning?carddata=...`

### Tạo QR Code eSIM
1. Chọn **📱 Tạo QR Code**
2. Nhập SM-DP+ Address
3. Nhập Activation Code (tùy chọn)
4. Nhận QR code để quét trên thiết bị

### Phân Tích QR Code
1. Chọn **🔍 Phân Tích QR**
2. Gửi text data từ QR code
3. Xem thông tin chi tiết:
   - SM-DP+ Address
   - Activation Code
   - Định dạng QR
   - Trạng thái hợp lệ

### Tạo Link từ QR Code
1. Chọn **📋 Link từ QR**
2. Gửi dữ liệu QR (LPA string, SM-DP+ address, URL)
3. Nhận link cài đặt cho iPhone

## 🔧 Cấu trúc dự án

```
esim-tool/
├── bot.py              # Bot Telegram chính
├── config.py           # Cấu hình bot
├── database.py         # Quản lý database SQLite
├── esim_tools.py       # Các công cụ xử lý eSIM
├── requirements.txt    # Thư viện Python
└── README.md          # Tài liệu này
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

#### `extract_sm_dp_and_activation(qr_data)`
Tách thông tin từ QR data
- **Returns**: Dict với sm_dp_address, activation_code, format_type

#### `validate_sm_dp_address(sm_dp_address)`
Kiểm tra tính hợp lệ của SM-DP+ address
- **Returns**: (bool, message)

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    device_type TEXT,
    device_model TEXT,
    created_at TIMESTAMP,
    last_active TIMESTAMP
);
```

### eSIM Requests Table
```sql
CREATE TABLE esim_requests (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    provider TEXT,
    country TEXT,
    plan_type TEXT,
    status TEXT,
    request_date TIMESTAMP
);
```

## 🔒 Bảo mật

- Bot token được bảo vệ qua environment variables
- Admin commands chỉ cho phép user được ủy quyền
- Dữ liệu người dùng được mã hóa trong database
- Validation đầu vào để tránh injection attacks

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

### QR Code không tạo được
- Kiểm tra thư viện `qrcode` và `Pillow`
- Đảm bảo SM-DP+ address hợp lệ
- Kiểm tra activation code format

### Database lỗi
```bash
# Xóa database cũ
rm esim_bot.db

# Khởi động lại bot
python bot.py
```

## 📞 Hỗ trợ

### Commands Bot
- `/start` - Khởi động bot và xem menu
- `/help` - Hướng dẫn sử dụng
- `/cancel` - Hủy thao tác hiện tại
- `/stats` - Thống kê (chỉ admin)

### Liên hệ
- Tạo issue trên GitHub
- Telegram: @your_support_username

## 📄 License

MIT License - Xem file LICENSE để biết chi tiết.

## 🔄 Changelog

### v1.0.0 (2024)
- ✅ Tạo link cài eSIM cho iPhone
- ✅ Tạo QR code từ SM-DP+ address
- ✅ Phân tích và tách thông tin QR
- ✅ Chuyển đổi QR thành link cài đặt
- ✅ Database SQLite
- ✅ Hướng dẫn cài đặt chi tiết

## 🚀 Roadmap

### v1.1.0
- [ ] Đọc QR code từ ảnh (pyzbar)
- [ ] Tích hợp API nhà cung cấp eSIM
- [ ] Export/Import cấu hình
- [ ] Multi-language support

### v1.2.0
- [ ] Web dashboard
- [ ] Bulk QR generation
- [ ] Analytics và reporting
- [ ] Docker deployment

---

**⭐ Nếu bot hữu ích, hãy star repo này!** 