from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Tạo Link & QR", callback_data="create_link_qr"),
            InlineKeyboardButton("🏪 Kho eSIM", callback_data="storage_menu"),
        ],
        [
            InlineKeyboardButton("🔍 Check ICCID", callback_data="check_iccid"),
        ],
    ])


def build_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
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
