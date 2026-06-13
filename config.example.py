import os

# =============================================================================
# BOT CONFIGURATION
# =============================================================================

# Bot Token từ @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Admin IDs - chỉ admin mới dùng được Kho eSIM
ADMIN_IDS = [123456789]  # Thay bằng Telegram user ID của bạn

# =============================================================================
# SIMPLIFYTRIP API (Check ICCID)
# =============================================================================

SIMPLIFYTRIP_API_URL = "https://api.simplifytrip.com/api/v1/products/iccid"
SIMPLIFYTRIP_EMAIL = "your_email@example.com"
SIMPLIFYTRIP_PASSWORD = "your_password"

# Proxy cho VPS (để trống nếu không dùng)
# Format: "http://user:pass@host:port" hoặc "http://host:port"
SIMPLIFYTRIP_PROXY = ""  # Ví dụ: "http://proxy.example.com:8080"

# =============================================================================
# MESSAGES
# =============================================================================

MESSAGES = {
    'welcome': """🤖 **CHÀO MỪNG ĐẾN BOT eSIM SUPPORT**

📱 **Công cụ eSIM**
• Tạo link cài eSIM cho iPhone
• Tạo QR code cho iPhone & Android
• Check thông tin eSIM từ ICCID

❓ **Hướng dẫn**
• Cài eSIM trên iPhone/Android
• Kiểm tra thiết bị hỗ trợ
• Gợi ý xử lý lỗi thường gặp

📱 Chọn chức năng bên dưới để bắt đầu!""",

    'iphone_guide': """📱 **HƯỚNG DẪN CÀI eSIM CHO iPHONE**

**Yêu cầu:** iPhone XS/XR+, iOS 12.1+

**Cách cài đặt:**
1. Mở **Cài đặt** → **Cellular/Di động**
2. Chọn **Add Cellular Plan**
3. Quét QR code hoặc mở link
4. Làm theo hướng dẫn trên màn hình""",

    'android_guide': """🤖 **HƯỚNG DẪN CÀI eSIM CHO ANDROID**

**Thiết bị hỗ trợ:** Samsung S20+, Pixel 3+, OnePlus 7T Pro+

**Cách cài đặt:**
1. Mở **Cài đặt** → **Network & Internet**
2. Chọn **SIM** → **Add SIM**
3. Chọn **Download a SIM instead?**
4. Quét QR code"""
}
