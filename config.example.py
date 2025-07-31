import os
from telegram.constants import ParseMode

# =============================================================================
# BOT CONFIGURATION
# =============================================================================

# Bot Token từ @BotFather (THAY ĐỔI TOKEN CỦA BẠN)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Admin IDs (có thể để trống nếu không cần)
ADMIN_IDS = [123456789]  # Thay bằng Telegram user ID của bạn

# =============================================================================
# MESSAGES
# =============================================================================

MESSAGES = {
    'welcome': """🤖 **CHÀO MỪNG ĐẾN BOT eSIM SUPPORT**

🔧 **Các công cụ hỗ trợ:**
• 🔗 Tạo link cài eSIM nhanh cho iPhone
• 📱 Tạo QR code cho iPhone & Android  
• 🔍 Phân tích dữ liệu QR code
• 📋 Tạo link cài từ QR code

📱 Chọn chức năng bên dưới để bắt đầu!""",

    'iphone_guide': """📱 **HƯỚNG DẪN CÀI eSIM CHO iPHONE**

**Yêu cầu:**
• iPhone XS/XR trở lên
• iOS 12.1 trở lên
• Kết nối WiFi ổn định

**Cách cài đặt:**
1. Mở **Cài đặt** → **Cellular/Di động**
2. Chọn **Add Cellular Plan**
3. Quét QR code hoặc mở link
4. Làm theo hướng dẫn trên màn hình

**Lưu ý:**
• Một số nhà mạng yêu cầu mã kích hoạt
• eSIM chỉ hoạt động khi được kích hoạt
• Có thể mất 5-15 phút để hoàn tất""",

    'android_guide': """🤖 **HƯỚNG DẪN CÀI eSIM CHO ANDROID**

**Thiết bị hỗ trợ:**
• Samsung Galaxy S20+ trở lên
• Google Pixel 3 trở lên  
• OnePlus 7T Pro trở lên

**Cách cài đặt:**
1. Mở **Cài đặt** → **Network & Internet**
2. Chọn **SIM** → **Add SIM**
3. Chọn **Download a SIM instead?**
4. Quét QR code hoặc nhập thông tin thủ công

**Lưu ý:**
• Giao diện có thể khác nhau giữa các hãng
• Cần kết nối WiFi ổn định
• Liên hệ nhà mạng nếu gặp lỗi"""
}

# =============================================================================
# DEVICE COMPATIBILITY
# =============================================================================

# iPhone models hỗ trợ eSIM
IPHONE_ESIM_MODELS = [
    "iPhone XS", "iPhone XS Max", "iPhone XR",
    "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max",
    "iPhone SE (2020)", "iPhone SE (3rd generation)",
    "iPhone 12", "iPhone 12 mini", "iPhone 12 Pro", "iPhone 12 Pro Max",
    "iPhone 13", "iPhone 13 mini", "iPhone 13 Pro", "iPhone 13 Pro Max", 
    "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max",
    "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max"
]

# Android brands/models hỗ trợ eSIM  
ANDROID_ESIM_BRANDS = {
    "Samsung": [
        "Galaxy S20", "Galaxy S20+", "Galaxy S20 Ultra",
        "Galaxy S21", "Galaxy S21+", "Galaxy S21 Ultra", 
        "Galaxy S22", "Galaxy S22+", "Galaxy S22 Ultra",
        "Galaxy S23", "Galaxy S23+", "Galaxy S23 Ultra",
        "Galaxy Note20", "Galaxy Note20 Ultra",
        "Galaxy Z Fold2", "Galaxy Z Fold3", "Galaxy Z Fold4", "Galaxy Z Fold5",
        "Galaxy Z Flip", "Galaxy Z Flip3", "Galaxy Z Flip4", "Galaxy Z Flip5"
    ],
    "Google": [
        "Pixel 3", "Pixel 3 XL", "Pixel 3a", "Pixel 3a XL",
        "Pixel 4", "Pixel 4 XL", "Pixel 4a", "Pixel 4a 5G",
        "Pixel 5", "Pixel 5a", "Pixel 6", "Pixel 6 Pro", 
        "Pixel 6a", "Pixel 7", "Pixel 7 Pro", "Pixel 7a",
        "Pixel 8", "Pixel 8 Pro", "Pixel Fold"
    ],
    "OnePlus": [
        "7T Pro", "8", "8 Pro", "8T", "9", "9 Pro", "9RT",
        "10 Pro", "10T", "11", "11R", "Nord 2T"
    ]
} 