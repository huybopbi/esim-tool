# 🤖 eSIM Support Bot

Bot Telegram hỗ trợ tạo link cài đặt, QR code eSIM và quản lý kho eSIM.

## ✨ Tính năng chính

### 🔗 Tạo Link & QR Code
Tự động nhận diện và xử lý nhiều định dạng:
- **LPA String:** `LPA:1$rsp.truphone.com$CODE123`
- **URL ảnh QR:** `https://example.com/qr.png`
- **SM-DP+ Address:** `rsp.truphone.com`

**Kết quả:**
- ✅ Link cài đặt cho iPhone (iOS 17.4+)
- ✅ QR code để quét (iPhone & Android)

### 🏪 Kho eSIM (Chỉ Admin)
- Thêm eSIM vào kho (LPA/URL/SM-DP+)
- Sử dụng eSIM từ kho
- Tracking: ai dùng, khi nào

## 🔐 Phân quyền

| Chức năng | Mọi người | Admin |
|-----------|:---------:|:-----:|
| 🔗 Tạo Link & QR | ✅ | ✅ |
| 🏪 Kho eSIM | ❌ | ✅ |

## 🚀 Cài đặt

### 1. Clone repo
```bash
git clone https://github.com/huybopbi/esim-tool.git
cd esim-tool
```

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình
```bash
cp config.example.py config.py
```

Chỉnh sửa `config.py`:
```python
BOT_TOKEN = "your_bot_token_here"
ADMIN_IDS = [123456789]  # Telegram user ID của bạn
```

### 4. Chạy bot
```bash
python bot.py
```

## 📁 Cấu trúc dự án

```
esim-tool/
├── bot.py                    # Bot Telegram chính
├── config.py                 # Config (không commit)
├── config.example.py         # Template config
├── esim_tools.py             # Xử lý eSIM (link, QR)
├── esim_storage.py           # Quản lý kho eSIM
├── esim_storage.db           # Database SQLite
├── requirements.txt          # Dependencies
└── README.md
```

## 📱 Commands

| Command | Mô tả |
|---------|-------|
| `/start` | Khởi động bot |
| `/help` | Xem hướng dẫn |
| `/cancel` | Hủy thao tác |
| `/myid` | Lấy User ID |

## 🔒 Bảo mật

Các file **KHÔNG** được commit lên GitHub:
- `config.py` - Chứa BOT_TOKEN
- `esim_storage.db` - Database eSIM

## 📄 License

MIT License

---

**⭐ Star repo nếu hữu ích!**
