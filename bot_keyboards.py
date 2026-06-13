from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📱 Công cụ eSIM", callback_data="create_link_qr"),
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


def build_result_actions_keyboard(
    is_admin: bool = False,
    can_save: bool = False,
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔁 Tạo mã khác", callback_data="create_link_qr"),
            InlineKeyboardButton("❓ Hướng dẫn", callback_data="guide_menu"),
        ],
    ]

    if is_admin:
        admin_row = []
        if can_save:
            admin_row.append(
                InlineKeyboardButton("➕ Lưu vào kho", callback_data="save_last_esim")
            )
        admin_row.append(
            InlineKeyboardButton("🏪 Về kho eSIM", callback_data="storage_menu")
        )
        keyboard.append(admin_row)

    keyboard.append([
        InlineKeyboardButton("🏠 Menu chính", callback_data="back_to_menu"),
    ])

    return InlineKeyboardMarkup(keyboard)


def build_storage_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Thêm eSIM khác", callback_data="add_esim"),
            InlineKeyboardButton("📋 Xem kho", callback_data="view_available"),
        ],
        [
            InlineKeyboardButton("🎯 Sử dụng eSIM", callback_data="use_esim"),
            InlineKeyboardButton("🏪 Về Menu Kho", callback_data="storage_menu"),
        ],
        [
            InlineKeyboardButton("🏠 Menu chính", callback_data="back_to_menu"),
        ],
    ])


def build_optional_activation_code_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Bỏ qua mã kích hoạt", callback_data="skip_activation_code")],
        [InlineKeyboardButton("❌ Hủy", callback_data="cancel_add_esim")],
    ])


def build_optional_description_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Bỏ qua mô tả", callback_data="skip_esim_description")],
        [InlineKeyboardButton("❌ Hủy", callback_data="cancel_add_esim")],
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
            InlineKeyboardButton("📦 Thêm hàng loạt", callback_data="bulk_add_esim"),
        ],
        [
            InlineKeyboardButton("📋 Xem Kho", callback_data="view_available"),
            InlineKeyboardButton("📊 eSIM Đã dùng", callback_data="view_used"),
        ],
        [
            InlineKeyboardButton("🎯 Sử dụng eSIM", callback_data="use_esim"),
        ],
        [
            InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu"),
        ],
    ])


def build_bulk_smdp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 rsp.esim.exchange", callback_data="bulk_smdp_1")],
        [InlineKeyboardButton("🌐 rsp.billionconnect.com", callback_data="bulk_smdp_2")],
        [InlineKeyboardButton("✍️ Nhập SM-DP+ khác", callback_data="bulk_smdp_custom")],
        [InlineKeyboardButton("❌ Hủy", callback_data="cancel_add_esim")],
    ])


def build_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Hủy", callback_data="cancel_add_esim")],
    ])


def build_use_note_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Bỏ qua ghi chú", callback_data="skip_use_note")],
        [InlineKeyboardButton("❌ Hủy", callback_data="cancel_use_esim")],
    ])
