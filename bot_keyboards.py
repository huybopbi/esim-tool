from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📱 Công cụ eSIM", callback_data="create_link_qr"),
            InlineKeyboardButton("🔍 Check ICCID", callback_data="check_iccid"),
        ],
        [
            InlineKeyboardButton("❓ Hướng dẫn", callback_data="guide_menu"),
        ],
    ]

    if is_admin:
        keyboard.append([
            InlineKeyboardButton("🛠 Quản trị kho eSIM", callback_data="storage_menu"),
        ])

    return InlineKeyboardMarkup(keyboard)


def build_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
    ])


def build_guide_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📱 iPhone", callback_data="iphone_guide"),
            InlineKeyboardButton("🤖 Android", callback_data="android_guide"),
        ],
        [
            InlineKeyboardButton("✅ Thiết bị hỗ trợ", callback_data="check_device"),
        ],
        [
            InlineKeyboardButton("🆘 Lỗi thường gặp", callback_data="support"),
        ],
        [
            InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu"),
        ],
    ])


def build_storage_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏪 Về Menu Kho", callback_data="storage_menu")],
        [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")],
    ])


def build_storage_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Thêm eSIM", callback_data="add_esim"),
            InlineKeyboardButton("📋 Xem Kho", callback_data="view_available"),
        ],
        [
            InlineKeyboardButton("🎯 Sử dụng eSIM", callback_data="use_esim"),
            InlineKeyboardButton("📊 eSIM Đã dùng", callback_data="view_used"),
        ],
        [
            InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu"),
        ],
    ])
