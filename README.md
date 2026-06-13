# 🤖 eSIM Support Bot

Bot Telegram hỗ trợ tạo link cài đặt eSIM, tạo/đọc QR code và quản lý kho eSIM nội bộ.

## ✨ Tính năng chính

### 📱 Công cụ eSIM
Bot tự động nhận diện và xử lý nhiều định dạng:
- **LPA String:** `LPA:1$rsp.truphone.com$CODE123`
- **URL ảnh QR:** `https://example.com/qr.png`
- **SM-DP+ Address:** `rsp.truphone.com`

Kết quả trả về:
- Link cài đặt nhanh cho iPhone
- QR code để quét trên iPhone/Android
- Các nút thao tác nhanh sau kết quả

### ❓ Trung tâm hướng dẫn
- Hướng dẫn cài eSIM cho iPhone
- Hướng dẫn cài eSIM cho Android
- Kiểm tra thiết bị hỗ trợ
- Gợi ý xử lý lỗi thường gặp

### 🏪 Kho eSIM (chỉ admin)
- Thêm eSIM vào kho từ LPA/URL/SM-DP+
- **Thêm hàng loạt:** dán nhiều eSIM cùng lúc với một SM-DP+ dùng chung
- Lưu nhanh kết quả vừa tạo vào kho
- Sử dụng eSIM từ kho: nhập **ghi chú** (tùy chọn) rồi tự động đánh dấu đã
  dùng, lưu lại ngày giờ và ghi chú
- Xem danh sách eSIM còn trống/đã dùng (kèm ICCID, ngày giờ và ghi chú)
- **Xóa eSIM** (có bước xác nhận): xóa từng eSIM, xóa hết eSIM đã dùng, hoặc
  xóa toàn bộ kho

#### 📦 Thêm eSIM hàng loạt
Trong menu Kho eSIM, bấm **"📦 Thêm hàng loạt"**:
1. Chọn **SM-DP+ dùng chung** cho cả lô — có sẵn `rsp.esim.exchange`,
   `rsp.billionconnect.com`, hoặc **"✍️ Nhập SM-DP+ khác"** để tự nhập.
2. Dán **danh sách eSIM**, mỗi eSIM cách nhau bằng **một dòng trống**:

```text
Activation Code:OZ8NB-X9008-G1LB2-xxxxx
ICCID:89851000000010674211

Activation Code:QRQNB-W2108-J1JE3-xxxx
ICCID:89851000000010674213
```

Bot dựng LPA string `LPA:1$<SM-DP+>$<Activation Code>` cho từng eSIM, lưu kèm
**ICCID**, rồi báo cáo số eSIM đã thêm và các block bị lỗi (kèm lý do).

Ghi chú:
- Nhãn không phân biệt hoa/thường (chấp nhận `Activation Code`, `Code`,
  `Mã kích hoạt`, `ICCID`, `SM-DP+`...).
- Mỗi block có thể tự khai dòng `SM-DP+:` để ghi đè SM-DP+ chung, hoặc dán
  thẳng một dòng `LPA:1$...$...`.

#### 🎯 Sử dụng eSIM từ kho
Bấm **"🎯 Sử dụng eSIM"** → chọn một eSIM → nhập **ghi chú** (tùy chọn, ví dụ
tên/khách hàng đã cài) hoặc bấm **"⏭ Bỏ qua ghi chú"**. Bot xuất QR + link cài
đặt, đồng thời chuyển eSIM sang mục **Đã dùng** kèm **ngày giờ** và **ghi chú**.
Mục **"📊 eSIM Đã dùng"** hiển thị lại ngày giờ, ghi chú và người thao tác.

#### 🗑 Xóa eSIM
Bấm **"🗑 Xóa eSIM"**. Mọi thao tác đều có **bước xác nhận** và
**không thể hoàn tác**:
- **🗑 Xóa từng eSIM:** chọn một eSIM trong danh sách (✅ có sẵn / 🔴 đã dùng) để xóa.
- **🧹 Xóa hết eSIM đã dùng:** xóa toàn bộ eSIM trạng thái đã dùng, giữ lại eSIM còn sẵn.
- **💣 Xóa toàn bộ kho:** xóa sạch toàn bộ dữ liệu kho.

> ⚠️ Nên backup `esim_storage.db` trước khi dùng **Xóa toàn bộ kho**.

> Tính năng Check ICCID/SimplifyTrip đã bị gỡ bỏ.

## 🔐 Phân quyền

| Chức năng | Mọi người | Admin |
|-----------|:---------:|:-----:|
| 📱 Tạo Link & QR | ✅ | ✅ |
| ❓ Hướng dẫn | ✅ | ✅ |
| 🏪 Kho eSIM | ❌ | ✅ |
| `/myid` | ✅ | ✅ |
| `/help` | ❌ | ✅ |

## 🚀 Deploy trên VPS Ubuntu/Debian

### 1. Cài system dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git libzbar0 libgl1 libglib2.0-0
```

Ghi chú:
- `libzbar0` dùng cho `pyzbar` để đọc QR nhanh hơn.
- `libgl1` và `libglib2.0-0` thường cần cho `opencv-python`.

### 2. Clone repo

```bash
git clone https://github.com/huybopbi/esim-tool.git
cd esim-tool
```

### 3. Tạo virtualenv và cài Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Tạo cấu hình

```bash
cp config.example.py config.py
nano config.py
```

Chỉnh tối thiểu:

```python
BOT_TOKEN = "your_bot_token_here"
ADMIN_IDS = [123456789]
```

Cách lấy thông tin:
- `BOT_TOKEN`: tạo bot bằng `@BotFather`.
- `ADMIN_IDS`: chạy bot rồi gửi `/myid` cho bot để lấy Telegram user ID của bạn.

Bạn cũng có thể truyền token qua environment variable `BOT_TOKEN`; giá trị env sẽ được ưu tiên hơn default trong `config.py`.

### 5. Chạy thử thủ công

```bash
source .venv/bin/activate
python3 bot.py
```

Nếu bot khởi động thành công, thử gửi `/start` trong Telegram.

### 6. Chạy lâu dài bằng systemd

Tạo service:

```bash
sudo nano /etc/systemd/system/esim-bot.service
```

Nội dung mẫu:

```ini
[Unit]
Description=eSIM Telegram Bot
After=network.target

[Service]
WorkingDirectory=/path/to/esim-tool
ExecStart=/path/to/esim-tool/.venv/bin/python bot.py
Restart=always
RestartSec=5
User=ubuntu
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Thay:
- `/path/to/esim-tool` bằng đường dẫn repo thật trên VPS.
- `User=ubuntu` bằng user đang chạy bot trên VPS.

Kích hoạt service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable esim-bot
sudo systemctl start esim-bot
sudo systemctl status esim-bot
```

Xem log realtime:

```bash
journalctl -u esim-bot -f
```

### 7. Cập nhật bot sau khi có code mới

```bash
cd /path/to/esim-tool
git pull origin master
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart esim-bot
sudo systemctl status esim-bot
```

## 🧪 Kiểm tra trước khi chạy

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall bot.py bot_constants.py bot_handlers.py bot_keyboards.py bot_user_info.py esim_tools.py esim_storage.py config.example.py
```

## 📁 Cấu trúc dự án

```text
esim-tool/
├── bot.py                    # Bot Telegram chính và conversation logic
├── bot_constants.py          # Conversation states và public callbacks
├── bot_handlers.py           # Đăng ký Telegram handlers
├── bot_keyboards.py          # Inline keyboard builders
├── bot_user_info.py          # Format phản hồi /myid
├── config.example.py         # Template config
├── config.py                 # Config thật, không commit
├── esim_tools.py             # Xử lý LPA/link/QR, parser thêm hàng loạt
├── esim_storage.py           # Quản lý kho eSIM SQLite (ICCID, ghi chú đã dùng)
├── esim_storage.db           # Database runtime, không commit
├── requirements.txt          # Python dependencies
├── tests/                    # Unit & integration tests
│   ├── test_esim_tools.py    # LPA/QR + parser thêm hàng loạt
│   ├── test_esim_storage.py  # Kho SQLite, migration, xóa
│   ├── test_bulk_flow.py     # Luồng thêm hàng loạt & dùng eSIM (ghi chú)
│   └── test_bot_security.py  # Phân quyền keyboard & /myid
└── README.md
```

## 📱 Commands

| Command | Mô tả |
|---------|-------|
| `/start` | Khởi động bot và mở menu chính |
| `/help` | Xem hướng dẫn admin |
| `/cancel` | Hủy thao tác đang nhập |
| `/myid` | Lấy Telegram user ID |

## 🔒 File cần bảo vệ/backup

Không commit các file runtime này:
- `config.py` - Chứa BOT_TOKEN và ADMIN_IDS thật
- `esim_storage.db` - Database kho eSIM

Nên backup định kỳ:

```bash
cp config.py config.py.backup
cp esim_storage.db esim_storage.db.backup
```

## 📄 License

MIT License
