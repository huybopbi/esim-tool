import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from telegram.constants import ParseMode
import os
from io import BytesIO

from config import BOT_TOKEN, MESSAGES, ADMIN_IDS
from esim_tools import esim_tools

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(WAITING_SM_DP, WAITING_ACTIVATION_CODE, WAITING_QR_DATA, 
 WAITING_DEVICE_MODEL, WAITING_SUPPORT_ISSUE) = range(5)

class eSIMBot:
    def __init__(self):
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho command /start"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        # Tạo keyboard menu chính
        keyboard = [
            [
                InlineKeyboardButton("🔗 Tạo Link Cài eSIM", callback_data="create_link"),
                InlineKeyboardButton("📱 Tạo QR Code", callback_data="create_qr")
            ],
            [
                InlineKeyboardButton("🔍 Phân Tích QR", callback_data="analyze_qr"),
                InlineKeyboardButton("📋 Link từ QR", callback_data="link_from_qr")
            ],
            [
                InlineKeyboardButton("📱 Kiểm tra Thiết bị", callback_data="check_device"),
                InlineKeyboardButton("🆘 Hỗ Trợ", callback_data="support")
            ],
            [
                InlineKeyboardButton("📖 Hướng Dẫn iPhone", callback_data="iphone_guide"),
                InlineKeyboardButton("🤖 Hướng Dẫn Android", callback_data="android_guide")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            MESSAGES['welcome'],
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho các button callback"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "create_link":
            await self.start_create_link(update, context)
        elif query.data == "create_qr":
            await self.start_create_qr(update, context)
        elif query.data == "analyze_qr":
            await self.start_analyze_qr(update, context)
        elif query.data == "link_from_qr":
            await self.start_link_from_qr(update, context)
        elif query.data == "check_device":
            await self.start_check_device(update, context)
        elif query.data == "support":
            await self.start_support(update, context)
        elif query.data == "iphone_guide":
            try:
                await query.edit_message_text(
                    MESSAGES['iphone_guide'],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_back_keyboard()
                )
            except Exception as e:
                logger.warning(f"Could not edit message: {e}")
                await query.message.reply_text(
                    MESSAGES['iphone_guide'],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_back_keyboard()
                )
        elif query.data == "android_guide":
            try:
                await query.edit_message_text(
                    MESSAGES['android_guide'],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_back_keyboard()
                )
            except Exception as e:
                logger.warning(f"Could not edit message: {e}")
                await query.message.reply_text(
                    MESSAGES['android_guide'],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_back_keyboard()
                )
        elif query.data == "back_to_menu":
            await self.show_main_menu(update, context)
    
    def get_back_keyboard(self):
        """Tạo keyboard với nút Back"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
        ])
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị menu chính"""
        keyboard = [
            [
                InlineKeyboardButton("🔗 Tạo Link Cài eSIM", callback_data="create_link"),
                InlineKeyboardButton("📱 Tạo QR Code", callback_data="create_qr")
            ],
            [
                InlineKeyboardButton("🔍 Phân Tích QR", callback_data="analyze_qr"),
                InlineKeyboardButton("📋 Link từ QR", callback_data="link_from_qr")
            ],
            [
                InlineKeyboardButton("📱 Kiểm tra Thiết bị", callback_data="check_device"),
                InlineKeyboardButton("🆘 Hỗ Trợ", callback_data="support")
            ],
            [
                InlineKeyboardButton("📖 Hướng Dẫn iPhone", callback_data="iphone_guide"),
                InlineKeyboardButton("🤖 Hướng Dẫn Android", callback_data="android_guide")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        
        try:
            # Thử edit message text trước
            await query.edit_message_text(
                MESSAGES['welcome'],
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            # Nếu không edit được (message có photo/file), gửi message mới
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                MESSAGES['welcome'],
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    # Tool 1: Tạo link cài eSIM cho iPhone
    async def start_create_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu tạo link cài eSIM"""
        query = update.callback_query
        await query.edit_message_text(
            "🔗 **TẠO LINK CÀI eSIM CHO IPHONE**\n\n"
            "Vui lòng nhập **SM-DP+ Address**:\n"
            "Ví dụ: `rsp.truphone.com`\n\n"
            "Gửi /cancel để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_SM_DP
    
    async def handle_sm_dp_for_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý SM-DP+ address cho tạo link"""
        sm_dp_address = update.message.text.strip()
        
        # Validate SM-DP+ address
        is_valid, message = esim_tools.validate_sm_dp_address(sm_dp_address)
        if not is_valid:
            await update.message.reply_text(
                f"❌ {message}\n\nVui lòng nhập lại SM-DP+ Address hợp lệ:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_SM_DP
        
        context.user_data['sm_dp_address'] = sm_dp_address
        
        await update.message.reply_text(
            "✅ SM-DP+ Address hợp lệ!\n\n"
            "Bây giờ nhập **Activation Code** (tùy chọn):\n"
            "Gửi `/skip` nếu không có mã kích hoạt\n"
            "Gửi `/cancel` để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_ACTIVATION_CODE
    
    async def handle_activation_code_for_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý activation code cho tạo link"""
        activation_code = None
        if update.message.text.strip() != "/skip":
            activation_code = update.message.text.strip()
        
        sm_dp_address = context.user_data['sm_dp_address']
        
        try:
            # Tạo link cài đặt
            install_link = esim_tools.create_iphone_install_link(sm_dp_address, activation_code)
            
            # Log activity
            logger.info(f"Created install link for user {update.effective_user.id}: {sm_dp_address}")
            
            # Tạo response message
            response = f"✅ **LINK CÀI eSIM ĐÃ TẠO THÀNH CÔNG**\n\n"
            response += f"📍 **SM-DP+ Address:** `{sm_dp_address}`\n"
            if activation_code:
                response += f"🔑 **Activation Code:** `{activation_code}`\n"
            response += f"\n🔗 **Link cài đặt:**\n`{install_link}`\n\n"
            response += "**Cách sử dụng:**\n"
            response += "1. Mở link trên iPhone\n"
            response += "2. Chọn 'Allow' khi được hỏi\n"
            response += "3. Làm theo hướng dẫn cài đặt\n\n"
            response += "💡 **Yêu cầu:** iPhone XS/XR+ với iOS 17.4+ (Universal Link)\n"
            response += "📱 **Fallback:** iOS 12.1+ có thể dùng QR code thay thế"
            
            # Tạo keyboard với options
            keyboard = [
                [InlineKeyboardButton("📱 Tạo QR Code", callback_data="create_qr")],
                [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi tạo link: {str(e)}\n\nVui lòng thử lại!",
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    # Tool 2: Tạo QR Code
    async def start_create_qr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu tạo QR code"""
        query = update.callback_query
        await query.edit_message_text(
            "📱 **TẠO QR CODE eSIM**\n\n"
            "Vui lòng nhập **SM-DP+ Address**:\n"
            "Ví dụ: `rsp.truphone.com`\n\n"
            "Gửi /cancel để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['action'] = 'create_qr'
        return WAITING_SM_DP
    
    async def handle_sm_dp_for_qr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý SM-DP+ address cho tạo QR"""
        sm_dp_address = update.message.text.strip()
        
        # Validate SM-DP+ address
        is_valid, message = esim_tools.validate_sm_dp_address(sm_dp_address)
        if not is_valid:
            await update.message.reply_text(
                f"❌ {message}\n\nVui lòng nhập lại SM-DP+ Address hợp lệ:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_SM_DP
        
        context.user_data['sm_dp_address'] = sm_dp_address
        
        await update.message.reply_text(
            "✅ SM-DP+ Address hợp lệ!\n\n"
            "Bây giờ nhập **Activation Code** (tùy chọn):\n"
            "Gửi `/skip` nếu không có mã kích hoạt\n"
            "Gửi `/cancel` để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_ACTIVATION_CODE
    
    async def handle_activation_code_for_qr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý activation code cho tạo QR"""
        activation_code = None
        if update.message.text.strip() != "/skip":
            activation_code = update.message.text.strip()
        
        sm_dp_address = context.user_data['sm_dp_address']
        
        try:
            # Tạo QR code
            qr_image, lpa_string = esim_tools.create_qr_from_sm_dp(sm_dp_address, activation_code)
            
            # Log activity
            logger.info(f"Created QR code for user {update.effective_user.id}: {sm_dp_address}")
            
            # Tạo response message
            response = f"✅ **QR CODE eSIM ĐÃ TẠO THÀNH CÔNG**\n\n"
            response += f"📍 **SM-DP+ Address:** `{sm_dp_address}`\n"
            if activation_code:
                response += f"🔑 **Activation Code:** `{activation_code}`\n"
            response += f"📋 **LPA String:** `{lpa_string}`\n\n"
            response += "**Cách sử dụng:**\n"
            response += "📱 **iPhone:** Cài đặt → Cellular → Add Cellular Plan → Quét QR\n"
            response += "🤖 **Android:** Cài đặt → Network & Internet → SIM → Download SIM\n\n"
            response += "💡 **Lưu ý:** Giữ kết nối WiFi ổn định khi cài đặt"
            
            # Gửi QR code image
            await update.message.reply_photo(
                photo=qr_image,
                caption=response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi tạo QR code: {str(e)}\n\nVui lòng thử lại!",
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    # Tool 3: Phân tích QR Code
    async def start_analyze_qr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu phân tích QR code"""
        query = update.callback_query
        await query.edit_message_text(
            "🔍 **PHÂN TÍCH QR CODE eSIM**\n\n"
            "Vui lòng gửi:\n"
            "• 📷 Ảnh QR code\n"
            "• 📋 Text data từ QR\n"
            "• 🔗 Link eSIM\n\n"
            "Gửi /cancel để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_QR_DATA
    
    async def handle_qr_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý phân tích QR data"""
        # TODO: Thêm xử lý ảnh QR code với thư viện pyzbar
        if update.message.text:
            qr_data = update.message.text.strip()
        else:
            await update.message.reply_text(
                "❌ Chức năng đọc QR từ ảnh đang được phát triển.\n"
                "Vui lòng gửi text data từ QR code.",
                reply_markup=self.get_back_keyboard()
            )
            return ConversationHandler.END
        
        try:
            # Log activity
            logger.info(f"Analyzing QR for user {update.effective_user.id}")
            
            # Phân tích QR data
            analysis = esim_tools.create_detailed_qr_info(qr_data)
            
            response = f"🔍 **PHÂN TÍCH QR CODE eSIM**\n\n"
            response += f"📋 **Dữ liệu gốc:** `{analysis['original_data'][:50]}...`\n"
            response += f"📁 **Định dạng:** {analysis['format_type']}\n"
            
            if analysis['sm_dp_address']:
                response += f"📍 **SM-DP+ Address:** `{analysis['sm_dp_address']}`\n"
            
            if analysis['activation_code']:
                response += f"🔑 **Activation Code:** `{analysis['activation_code']}`\n"
            
            response += f"✅ **Trạng thái:** {'Hợp lệ' if analysis['is_valid'] else 'Không hợp lệ'}\n\n"
            
            if analysis.get('install_methods'):
                response += "**Phương thức cài đặt:**\n"
                for method in analysis['install_methods']:
                    response += f"• {method}\n"
                response += "\n"
            
            if analysis.get('notes'):
                response += "**Ghi chú:**\n"
                for note in analysis['notes']:
                    response += f"• {note}\n"
            
            # Tạo keyboard với options
            keyboard = []
            if analysis['is_valid']:
                keyboard.append([
                    InlineKeyboardButton("🔗 Tạo Link Cài", callback_data="link_from_qr"),
                    InlineKeyboardButton("📱 Tạo QR Mới", callback_data="create_qr")
                ])
            keyboard.append([InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi phân tích QR: {str(e)}\n\nVui lòng kiểm tra lại dữ liệu!",
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    # Tool 4: Tạo link từ QR
    async def start_link_from_qr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu tạo link từ QR data"""
        query = update.callback_query
        await query.edit_message_text(
            "📋 **TẠO LINK TỪ QR CODE**\n\n"
            "Vui lòng gửi dữ liệu QR code:\n"
            "• LPA string (LPA:1$...)\n"
            "• SM-DP+ Address\n"
            "• URL eSIM\n\n"
            "Gửi /cancel để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['action'] = 'link_from_qr'
        return WAITING_QR_DATA
    
    async def handle_link_from_qr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tạo link từ QR data"""
        qr_data = update.message.text.strip()
        
        try:
            # Log activity
            logger.info(f"Creating link from QR for user {update.effective_user.id}")
            
            # Tạo link cài đặt từ QR data
            install_link = esim_tools.create_install_link_from_qr(qr_data)
            
            # Phân tích data để hiển thị thông tin
            analysis = esim_tools.extract_sm_dp_and_activation(qr_data)
            
            response = f"✅ **LINK CÀI ĐẶT ĐÃ TẠO THÀNH CÔNG**\n\n"
            
            if analysis['sm_dp_address']:
                response += f"📍 **SM-DP+ Address:** `{analysis['sm_dp_address']}`\n"
            if analysis['activation_code']:
                response += f"🔑 **Activation Code:** `{analysis['activation_code']}`\n"
            
            response += f"\n🔗 **Link cài đặt:**\n`{install_link}`\n\n"
            response += "**Cách sử dụng:**\n"
            response += "1. Mở link trên iPhone\n"
            response += "2. Chọn 'Allow' khi được hỏi\n"
            response += "3. Làm theo hướng dẫn cài đặt\n\n"
            response += "💡 **Yêu cầu:** iPhone XS/XR+ với iOS 17.4+ (Universal Link)\n"
            response += "📱 **Fallback:** iOS 12.1+ có thể dùng QR code thay thế"
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi tạo link: {str(e)}\n\nVui lòng kiểm tra lại dữ liệu QR!",
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    # Device check và Support placeholders
    async def start_check_device(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kiểm tra thiết bị hỗ trợ eSIM"""
        query = update.callback_query
        message_text = ("📱 **KIỂM TRA THIẾT BỊ HỖ TRỢ eSIM**\n\n"
                       "**iPhone hỗ trợ eSIM:**\n"
                       "• iPhone XS, XS Max, XR trở lên\n"
                       "• iOS 12.1 trở lên\n\n"
                       "**Android hỗ trợ eSIM:**\n"
                       "• Samsung Galaxy S20+ trở lên\n"
                       "• Google Pixel 3 trở lên\n"
                       "• OnePlus 7T Pro trở lên\n\n"
                       "💡 **Cách kiểm tra:**\n"
                       "📱 **iPhone:** Cài đặt → Cellular → Add Cellular Plan\n"
                       "🤖 **Android:** Cài đặt → Network & Internet → SIM")
        
        try:
            await query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        except Exception as e:
            logger.warning(f"Could not edit message: {e}")
            await query.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
    
    async def start_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hỗ trợ khách hàng"""
        query = update.callback_query
        message_text = ("🆘 **HỖ TRỢ KHÁCH HÀNG**\n\n"
                       "**Vấn đề thường gặp:**\n\n"
                       "🔧 **Lỗi kích hoạt:**\n"
                       "• Kiểm tra kết nối WiFi\n"
                       "• Restart thiết bị\n"
                       "• Thử lại sau 5-10 phút\n\n"
                       "📶 **Mất sóng:**\n"
                       "• Kiểm tra Data Roaming\n"
                       "• Chọn mạng thủ công\n"
                       "• Reset Network Settings\n\n"
                       "💬 **Liên hệ hỗ trợ:**\n"
                       "• Gửi /help để xem hướng dẫn\n"
                       "• Mô tả chi tiết vấn đề gặp phải")
        
        try:
            await query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        except Exception as e:
            logger.warning(f"Could not edit message: {e}")
            await query.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
    
    # Handlers khác
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho command /cancel"""
        await update.message.reply_text(
            "❌ Đã hủy thao tác.",
            reply_markup=self.get_back_keyboard()
        )
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho command /help"""
        help_text = """
🤖 **eSIM SUPPORT BOT - HƯỚNG DẪN SỬ DỤNG**

**🔧 Các công cụ chính:**
• 🔗 **Tạo Link Cài eSIM** - Tạo link cài nhanh cho iPhone
• 📱 **Tạo QR Code** - Tạo QR code từ SM-DP+ và mã kích hoạt
• 🔍 **Phân Tích QR** - Tách thông tin từ QR code eSIM
• 📋 **Link từ QR** - Chuyển QR code thành link cài đặt

**📱 Hỗ trợ thiết bị:**
• iPhone XS/XR trở lên (iOS 12.1+)
• Android 9.0+ có hỗ trợ eSIM

**📞 Hỗ trợ:**
Gửi /start để xem menu chính
Gửi /cancel để hủy thao tác hiện tại
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.get_back_keyboard()
        )
    
    def setup_handlers(self):
        """Thiết lập các handlers cho bot"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Conversation handler cho tạo link
        create_link_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_create_link, pattern="^create_link$")],
            states={
                WAITING_SM_DP: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_sm_dp_for_link)],
                WAITING_ACTIVATION_CODE: [MessageHandler(filters.TEXT, self.handle_activation_code_for_link)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Conversation handler cho tạo QR
        create_qr_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_create_qr, pattern="^create_qr$")],
            states={
                WAITING_SM_DP: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_sm_dp_for_qr)],
                WAITING_ACTIVATION_CODE: [MessageHandler(filters.TEXT, self.handle_activation_code_for_qr)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Conversation handler cho phân tích QR
        analyze_qr_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_analyze_qr, pattern="^analyze_qr$")],
            states={
                WAITING_QR_DATA: [MessageHandler(filters.TEXT | filters.PHOTO, self.handle_qr_analysis)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Conversation handler cho link từ QR
        link_from_qr_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_link_from_qr, pattern="^link_from_qr$")],
            states={
                WAITING_QR_DATA: [MessageHandler(filters.TEXT, self.handle_link_from_qr)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Thêm các conversation handlers
        self.application.add_handler(create_link_handler)
        self.application.add_handler(create_qr_handler)
        self.application.add_handler(analyze_qr_handler)
        self.application.add_handler(link_from_qr_handler)
        
        # Button callback handler
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def set_bot_commands(self):
        """Thiết lập menu commands cho bot"""
        commands = [
            BotCommand("start", "Khởi động bot và xem menu chính"),
            BotCommand("help", "Xem hướng dẫn sử dụng"),
            BotCommand("cancel", "Hủy thao tác hiện tại")
        ]
        
        try:
            await self.application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        except Exception as e:
            logger.warning(f"Could not set bot commands: {e}")
    
    def run(self):
        """Chạy bot"""
        # Tạo application
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Thiết lập handlers
        self.setup_handlers()
        
        # Chạy bot
        print("🤖 eSIM Support Bot đã khởi động!")
        print("📱 Sẵn sàng hỗ trợ cài đặt eSIM...")
        print("💡 Nhấn Ctrl+C để dừng bot")
        
        # Chạy bot với polling
        self.application.run_polling(drop_pending_updates=True)

def main():
    """Hàm main"""
    if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Lỗi: Chưa cấu hình BOT_TOKEN!")
        print("Vui lòng:")
        print("1. Tạo bot mới với @BotFather trên Telegram")
        print("2. Lấy token và set environment variable: BOT_TOKEN=your_token")
        print("3. Hoặc sửa trực tiếp trong file config.py")
        return
    
    # Tạo và chạy bot
    bot = eSIMBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot đã dừng bởi người dùng")
        print("👋 Tạm biệt!")
    except Exception as e:
        print(f"❌ Lỗi khởi động: {e}")
        logger.error(f"Startup error: {e}")

if __name__ == '__main__':
    main() 