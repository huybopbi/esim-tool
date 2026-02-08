import logging
import asyncio
import warnings

# Suppress các warnings không cần thiết
warnings.filterwarnings("ignore", message=".*per_message.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*pkg_resources.*", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from telegram.constants import ParseMode
import os
from io import BytesIO

from config import BOT_TOKEN, MESSAGES, ADMIN_IDS
from esim_tools import esim_tools
from esim_storage import esim_storage
from simplifytrip_api import simplifytrip_api

# Logging setup - Clean và chỉ hiển thị thông tin quan trọng
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Tắt các logging không cần thiết
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram.ext.Updater').setLevel(logging.WARNING) 
logging.getLogger('telegram.ext.Application').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# States cho conversation handlers
WAITING_SM_DP_LINK, WAITING_ACTIVATION_CODE_LINK, WAITING_SM_DP_QR, WAITING_ACTIVATION_CODE_QR, WAITING_QR_DATA, WAITING_QR_IMAGE, WAITING_LPA_STRING, WAITING_ADD_ESIM_SM_DP, WAITING_ADD_ESIM_CODE, WAITING_ADD_ESIM_DESC, WAITING_ESIM_SELECTION, WAITING_ADD_ESIM_LPA, WAITING_ADD_ESIM_LPA_DESC, WAITING_ADD_ESIM_URL, WAITING_ADD_ESIM_URL_DESC, WAITING_ICCID = range(16)

class eSIMBot:
    def __init__(self):
        self.application = None
    
    def admin_required(func):
        """Decorator để kiểm tra admin access cho callback handlers"""
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            if user_id not in ADMIN_IDS:
                await self._unauthorized_reply(update)
                return ConversationHandler.END
            return await func(self, update, context)
        return wrapper
    
    def _check_admin_access(self, update: Update):
        """Kiểm tra xem user có phải admin không"""
        user_id = update.effective_user.id
        return user_id in ADMIN_IDS
    
    async def _unauthorized_reply(self, update: Update, text: str = None):
        try:
            message = text or "❌ Bot chỉ dành cho chủ bot. Truy cập bị từ chối."
            if update.message:
                await update.message.reply_text(message)
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.reply_text(message)
        except Exception as e:
            logger.warning(f"Unauthorized reply failed: {e}")

    async def unauthorized_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Chặn mọi tin nhắn từ người không có quyền"""
        await self._unauthorized_reply(update)
        return ConversationHandler.END

    async def unauthorized_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Chặn mọi callback từ người không có quyền"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await self._unauthorized_reply(update)
            return ConversationHandler.END

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho command /start - mọi người đều dùng được"""
        user = update.effective_user
        is_admin = user.id in ADMIN_IDS
        logger.info(f"[START] User: {user.username or user.id} | Admin: {is_admin}")
        
        # Hiển thị menu đầy đủ cho tất cả mọi người
        keyboard = [
            [
                InlineKeyboardButton("🔗 Tạo Link & QR", callback_data="create_link_qr"),
                InlineKeyboardButton("🏪 Kho eSIM", callback_data="storage_menu")
            ],
            [
                InlineKeyboardButton("🔍 Check ICCID", callback_data="check_iccid")
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
        user_id = update.effective_user.id
        is_admin = user_id in ADMIN_IDS
        
        query = update.callback_query
        await query.answer()
        
        # Các chức năng mọi người đều dùng được
        if query.data == "check_iccid":
            await self.start_check_iccid(update, context)
            return
        
        if query.data == "create_link_qr":
            await self.start_create_link_qr(update, context)
            return
        
        if query.data == "back_to_menu":
            await self.show_main_menu(update, context)
            return
        
        # Các chức năng khác (Kho eSIM) - chỉ admin mới dùng được
        if not is_admin:
            await self._unauthorized_reply(update)
            return
        
        if query.data == "storage_menu":
            await self.show_storage_menu(update, context)
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
        elif query.data == "add_esim":
            await self.start_add_esim(update, context)
        elif query.data == "view_available":
            await self.view_available_esims(update, context)
        elif query.data == "use_esim":
            await self.start_use_esim(update, context)
        elif query.data == "view_used":
            await self.view_used_esims(update, context)

    
    def get_back_keyboard(self):
        """Tạo keyboard với nút Back"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
        ])
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị menu chính - đầy đủ cho tất cả mọi người"""
        # Hiển thị menu đầy đủ cho tất cả
        keyboard = [
            [
                InlineKeyboardButton("🔗 Tạo Link & QR", callback_data="create_link_qr"),
                InlineKeyboardButton("🏪 Kho eSIM", callback_data="storage_menu")
            ],
            [
                InlineKeyboardButton("🔍 Check ICCID", callback_data="check_iccid")
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
    # Tool: Tạo Link & QR (Unified)
    async def start_create_link_qr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu tạo link & QR - tự động nhận diện"""
        query = update.callback_query
        
        try:
            await query.edit_message_text(
                "🔗 **TẠO LINK & QR CODE eSIM**\n\n"
                "Vui lòng gửi **một trong các định dạng sau**:\n\n"
                "📝 **LPA String:**\n"
                "• `LPA:1$rsp.truphone.com$CODE123`\n\n"
                "📎 **URL/QR data:**\n"
                "• `https://esimsetup.apple.com/...`\n"
                "• Dữ liệu QR code (text)\n\n"
                "🔧 **SM-DP+ Address:**\n"
                "• `rsp.truphone.com`\n\n"
                "💡 **Bot sẽ tự động:**\n"
                "• Nhận diện loại dữ liệu\n"
                "• Tạo link cài đặt cho iPhone\n"
                "• Tạo QR code để quét\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                "🔗 **TẠO LINK & QR CODE eSIM**\n\n"
                "Vui lòng gửi **một trong các định dạng sau**:\n\n"
                "📝 **LPA String:**\n"
                "• `LPA:1$rsp.truphone.com$CODE123`\n\n"
                "📎 **URL/QR data:**\n"
                "• `https://esimsetup.apple.com/...`\n"
                "• Dữ liệu QR code (text)\n\n"
                "🔧 **SM-DP+ Address:**\n"
                "• `rsp.truphone.com`\n\n"
                "💡 **Bot sẽ tự động:**\n"
                "• Nhận diện loại dữ liệu\n"
                "• Tạo link cài đặt cho iPhone\n"
                "• Tạo QR code để quét\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        
        context.user_data['action'] = 'create_link_qr_auto'
        return WAITING_SM_DP_LINK
    
    async def handle_create_link_qr_auto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tự động nhận diện và tạo link & QR"""
        data = update.message.text.strip()
        
        try:
            # Detect and extract info
            if data.startswith('LPA:1$'):
                logger.info(f"Auto-detected: LPA string")
                analysis = esim_tools.extract_sm_dp_and_activation(data)
            elif data.startswith('http://') or data.startswith('https://'):
                logger.info(f"Auto-detected: URL")
                
                # Show processing message
                processing_msg = await update.message.reply_text(
                    "🔄 **Đang xử lý URL...**\n\n"
                    "⏳ Vui lòng đợi trong giây lát...",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Check if URL might be an image (contains /images/, ends with image extension, or no carddata param)
                is_likely_image = (
                    '/images/' in data.lower() or 
                    data.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or
                    'carddata=' not in data.lower()
                )
                
                # Try to extract from URL text first (only if it looks like an eSIM URL)
                if not is_likely_image and 'carddata=' in data.lower():
                    analysis = esim_tools.extract_sm_dp_and_activation(data)
                else:
                    analysis = {'sm_dp_address': '', 'activation_code': '', 'format_type': 'URL'}
                
                # If no SM-DP+ found, try downloading as image
                if not analysis['sm_dp_address']:
                    try:
                        import requests
                        logger.info(f"Trying to download image from URL")
                        
                        response = requests.get(data, timeout=30)
                        response.raise_for_status()
                        image_data = response.content
                        
                        # Analyze QR from image
                        analysis = esim_tools.analyze_qr_image(image_data)
                        
                        if not analysis['qr_detected']:
                            await processing_msg.delete()
                            await update.message.reply_text(
                                f"❌ **Không đọc được QR code từ URL**\n\n"
                                f"**Lỗi:** {analysis.get('error', 'Không xác định')}\n\n"
                                f"💡 **Gợi ý:**\n"
                                f"• Kiểm tra URL có đúng không\n"
                                f"• Thử với URL khác\n\n"
                                f"Gửi /cancel để hủy",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return WAITING_SM_DP_LINK
                        
                        logger.info(f"Successfully read QR from image URL")
                    except Exception as e:
                        await processing_msg.delete()
                        await update.message.reply_text(
                            f"❌ **Lỗi xử lý URL:** {str(e)}\n\n"
                            f"💡 **Gợi ý:**\n"
                            f"• Kiểm tra URL có thể truy cập được\n"
                            f"• Thử với URL khác\n\n"
                            f"Gửi /cancel để hủy",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return WAITING_SM_DP_LINK
                
                # Delete processing message
                try:
                    await processing_msg.delete()
                except:
                    pass
            else:
                # Try as SM-DP+ or QR data
                analysis = esim_tools.extract_sm_dp_and_activation(data)
                if not analysis['sm_dp_address']:
                    # Validate as SM-DP+
                    is_valid, message = esim_tools.validate_sm_dp_address(data)
                    if is_valid:
                        logger.info(f"Auto-detected: SM-DP+ address")
                        analysis = {'sm_dp_address': data, 'activation_code': '', 'format_type': 'SM-DP+'}
                    else:
                        await update.message.reply_text(
                            f"❌ **Không nhận diện được định dạng**\n\n"
                            f"**Dữ liệu bạn gửi:** `{data[:50]}{'...' if len(data) > 50 else ''}`\n\n"
                            f"💡 **Vui lòng gửi:**\n"
                            f"• LPA String: `LPA:1$...$...`\n"
                            f"• URL: `https://...`\n"
                            f"• SM-DP+ Address: `rsp.truphone.com`\n\n"
                            f"Gửi /cancel để hủy",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return WAITING_SM_DP_LINK
            
            if not analysis['sm_dp_address']:
                await update.message.reply_text(
                    "❌ **Không tìm thấy thông tin eSIM hợp lệ**\n\n"
                    "Vui lòng thử lại với dữ liệu khác!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_back_keyboard()
                )
                return ConversationHandler.END
            
            # Create link and QR
            sm_dp_address = analysis['sm_dp_address']
            activation_code = analysis['activation_code'] or ''
            
            # Create install link
            install_link = esim_tools.create_iphone_install_link(sm_dp_address, activation_code)
            
            # Create QR code
            qr_image, lpa_string = esim_tools.create_qr_from_sm_dp(sm_dp_address, activation_code)
            
            # Log activity
            user = update.effective_user
            logger.info(f"[CREATE QR] User: {user.username or user.id} | SM-DP+: {sm_dp_address} | Code: {activation_code or 'N/A'}")
            
            # Create response
            response = f"✅ **LINK & QR CODE ĐÃ TẠO THÀNH CÔNG**\n\n"
            response += f"📍 **SM-DP+ Address:** `{sm_dp_address}`\n"
            if activation_code:
                response += f"🔑 **Activation Code:** `{activation_code}`\n"
            response += f"📋 **LPA String:** `{lpa_string}`\n\n"
            response += f"🔗 **Link cài đặt iPhone:**\n`{install_link}`\n\n"
            response += f"**Cách sử dụng:**\n\n"
            response += f"📱 **iPhone:**\n"
            response += f"• Mở link trên iPhone (iOS 17.4+)\n"
            response += f"• Hoặc quét QR: Cài đặt → Cellular → Add Plan\n\n"
            response += f"🤖 **Android:**\n"
            response += f"• Quét QR: Cài đặt → Network → SIM → Add\n\n"
            response += f"💡 **Lưu ý:** Giữ kết nối WiFi ổn định khi cài đặt"
            
            # Send QR code with info
            await update.message.reply_photo(
                photo=qr_image,
                caption=response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi tạo link & QR:** {str(e)}\n\n"
                f"Vui lòng thử lại!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
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
        return WAITING_SM_DP_LINK
    
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
            return WAITING_SM_DP_LINK
        
        context.user_data['sm_dp_address'] = sm_dp_address
        
        await update.message.reply_text(
            "✅ SM-DP+ Address hợp lệ!\n\n"
            "Bây giờ nhập **Activation Code** (tùy chọn):\n"
            "Gửi `/skip` nếu không có mã kích hoạt\n"
            "Gửi `/cancel` để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_ACTIVATION_CODE_LINK
    
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
        return WAITING_SM_DP_QR
    
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
            return WAITING_SM_DP_QR
        
        context.user_data['sm_dp_address'] = sm_dp_address
        
        await update.message.reply_text(
            "✅ SM-DP+ Address hợp lệ!\n\n"
            "Bây giờ nhập **Activation Code** (tùy chọn):\n"
            "Gửi `/skip` nếu không có mã kích hoạt\n"
            "Gửi `/cancel` để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_ACTIVATION_CODE_QR
    
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
            "Vui lòng chọn cách gửi QR code:\n\n"
            "📝 **Gửi text:** Copy/paste dữ liệu QR\n"
            "📸 **Gửi ảnh:** Chụp ảnh hoặc gửi file ảnh QR code",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 Gửi Text", callback_data="qr_text"),
                    InlineKeyboardButton("📸 Gửi Ảnh", callback_data="qr_image")
                ],
                [InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_menu")]
            ])
        )
        return WAITING_QR_DATA

    async def handle_qr_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lựa chọn phương thức gửi QR"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "qr_text":
            await query.edit_message_text(
                "📝 **GỬI DỮ LIỆU QR CODE**\n\n"
                "Vui lòng gửi dữ liệu QR code (text):\n\n"
                "**Ví dụ:**\n"
                "• `LPA:1$rsp.truphone.com$CODE123`\n"
                "• `rsp.truphone.com`\n"
                "• `https://esimsetup.apple.com/...`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            return WAITING_QR_DATA
            
        elif query.data == "qr_image":
            await query.edit_message_text(
                "📸 **GỬI ẢNH QR CODE**\n\n"
                "Vui lòng gửi ảnh chứa QR code eSIM:\n\n"
                "📱 **Cách chụp tốt nhất:**\n"
                "• Giữ máy thẳng, không bị nghiêng\n"
                "• Đảm bảo ánh sáng đủ\n"
                "• QR code chiếm toàn bộ khung hình\n"
                "• Không bị mờ hoặc bóng\n\n"
                "🖼️ **Hỗ trợ:** JPG, PNG, GIF",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            return WAITING_QR_IMAGE
            
        return ConversationHandler.END

    async def handle_qr_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý dữ liệu QR code được gửi dưới dạng text"""
        qr_data = update.message.text.strip()
        
        try:
            # Log activity
            logger.info(f"Analyzing QR data text for user {update.effective_user.id}: {qr_data}")
            
            # Phân tích data để hiển thị thông tin
            analysis = esim_tools.extract_sm_dp_and_activation(qr_data)
            
            response = "🔍 **KẾT QUẢ PHÂN TÍCH QR CODE**\n\n"
            
            if analysis['sm_dp_address']:
                response += f"📍 **SM-DP+ Address:** `{analysis['sm_dp_address']}`\n"
            if analysis['activation_code']:
                response += f"🔑 **Activation Code:** `{analysis['activation_code']}`\n"
            
            response += f"\n📋 **Format:** {analysis['format_type'].upper()}\n"
            response += f"🔗 **Dữ liệu gốc:**\n`{analysis['original_data'][:100]}{'...' if len(analysis['original_data']) > 100 else ''}`\n\n"
            
            # Thêm link cài đặt nếu có thể
            if analysis['sm_dp_address']:
                try:
                    install_link = esim_tools.create_iphone_install_link(
                        analysis['sm_dp_address'], 
                        analysis['activation_code']
                    )
                    response += f"🔗 **Link cài đặt iPhone:**\n`{install_link}`\n\n"
                except:
                    pass
            
            response += f"💡 **Hướng dẫn cài đặt:**\n"
            response += f"📱 **iPhone:** Cài đặt → Cellular → Add Plan\n"
            response += f"🤖 **Android:** Cài đặt → Network → SIM → Add\n\n"
            response += f"✨ **Tương thích:** iPhone XS+ (iOS 12.1+), Android 9.0+"
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi phân tích QR text:** {str(e)}\n\n"
                f"💡 **Gợi ý:**\n"
                f"• Thử với dữ liệu khác\n"
                f"• Gửi dữ liệu ảnh thay thế\n"
                f"• Kiểm tra định dạng text (LPA:1$... hoặc SM-DP+ Address)",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END

    async def handle_qr_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý ảnh QR code được gửi"""
        try:
            # Hiển thị đang xử lý
            processing_msg = await update.message.reply_text(
                "🔄 **Đang phân tích ảnh QR code...**\n\n"
                "⏳ Vui lòng đợi trong giây lát...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Lấy file ảnh lớn nhất
            if update.message.photo:
                file = await update.message.photo[-1].get_file()
            elif update.message.document:
                file = await update.message.document.get_file()
            else:
                await processing_msg.edit_text(
                    "❌ **Lỗi:** Vui lòng gửi ảnh hoặc file ảnh!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return ConversationHandler.END
            
            # Download file
            file_data = await file.download_as_bytearray()
            
            # Phân tích QR từ ảnh
            analysis = esim_tools.analyze_qr_image(bytes(file_data))
            
            # Xóa message đang xử lý
            await processing_msg.delete()
            
            if not analysis['qr_detected']:
                await update.message.reply_text(
                    f"❌ **KHÔNG ĐỌC ĐƯỢC QR CODE**\n\n"
                    f"**Lỗi:** {analysis.get('error', 'Không xác định')}\n\n"
                    f"💡 **Gợi ý:**\n"
                    f"• Chụp ảnh rõ nét hơn\n"
                    f"• Đảm bảo QR code không bị cắt\n"
                    f"• Thử với ánh sáng tốt hơn\n"
                    f"• Hoặc gửi dữ liệu text thay thế",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_back_keyboard()
                )
                return ConversationHandler.END
            
            # Hiển thị kết quả phân tích
            response = "🔍 **KẾT QUẢ PHÂN TÍCH QR CODE**\n\n"
            response += f"📱 **Nguồn:** Ảnh QR code\n"
            response += f"✅ **Trạng thái:** Đọc thành công\n\n"
            
            response += f"📍 **SM-DP+ Address:**\n`{analysis['sm_dp_address']}`\n\n"
            
            if analysis['activation_code']:
                response += f"🔑 **Activation Code:**\n`{analysis['activation_code']}`\n\n"
            else:
                response += f"🔑 **Activation Code:** _Không có_\n\n"
                
            response += f"📋 **Format:** {analysis['format_type'].upper()}\n"
            response += f"🔗 **Dữ liệu gốc:**\n`{analysis['original_data'][:100]}{'...' if len(analysis['original_data']) > 100 else ''}`\n\n"
            
            # Thêm link cài đặt nếu có thể
            if analysis['sm_dp_address']:
                try:
                    install_link = esim_tools.create_iphone_install_link(
                        analysis['sm_dp_address'], 
                        analysis['activation_code']
                    )
                    response += f"🔗 **Link cài đặt iPhone:**\n`{install_link}`\n\n"
                except:
                    pass
            
            response += f"💡 **Hướng dẫn cài đặt:**\n"
            response += f"📱 **iPhone:** Cài đặt → Cellular → Add Plan\n"
            response += f"🤖 **Android:** Cài đặt → Network → SIM → Add\n\n"
            response += f"✨ **Tương thích:** iPhone XS+ (iOS 12.1+), Android 9.0+"
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi xử lý ảnh:** {str(e)}\n\n"
                f"💡 **Gợi ý:**\n"
                f"• Thử với ảnh khác\n"
                f"• Gửi dữ liệu text thay thế\n"
                f"• Kiểm tra định dạng ảnh (JPG/PNG)",
                parse_mode=ParseMode.MARKDOWN,
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
    
    # Tool 5: Tạo Link và QR từ LPA String
    async def start_from_lpa_string(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu xử lý LPA string"""
        query = update.callback_query
        await query.edit_message_text(
            "📝 **TẠO LINK VÀ QR TỪ LPA STRING**\n\n"
            "Vui lòng nhập **LPA String**:\n\n"
            "**Ví dụ:**\n"
            "• `LPA:1$rsp.truphone.com$CODE123`\n"
            "• `LPA:1$sm-dp.example.com$`\n\n"
            "**Lưu ý:** LPA string phải có định dạng `LPA:1$SM-DP+$CODE`\n\n"
            "Gửi /cancel để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['action'] = 'from_lpa_string'
        return WAITING_LPA_STRING
    
    async def handle_lpa_string(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý LPA string và tạo link + QR"""
        lpa_string = update.message.text.strip()
        
        try:
            # Log activity
            logger.info(f"Processing LPA string for user {update.effective_user.id}: {lpa_string[:50]}...")
            
            # Validate LPA string
            is_valid, message = esim_tools.validate_lpa_string(lpa_string)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ **LPA String không hợp lệ**\n\n"
                    f"**Lỗi:** {message}\n\n"
                    f"**Ví dụ đúng:**\n"
                    f"• `LPA:1$rsp.truphone.com$CODE123`\n"
                    f"• `LPA:1$sm-dp.example.com$`\n\n"
                    f"Vui lòng nhập lại LPA string hợp lệ:",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_LPA_STRING
            
            # Extract thông tin từ LPA string
            analysis = esim_tools.extract_sm_dp_and_activation(lpa_string)
            
            # Tạo QR code từ LPA string
            qr_image, _ = esim_tools.create_qr_from_lpa(lpa_string)
            
            # Tạo install link
            install_link = f"https://esimsetup.apple.com/esim_qrcode_provisioning?carddata={lpa_string}"
            
            # Tạo response message
            response = f"✅ **LINK VÀ QR ĐÃ TẠO THÀNH CÔNG**\n\n"
            response += f"📋 **LPA String:** `{lpa_string}`\n\n"
            
            if analysis['sm_dp_address']:
                response += f"📍 **SM-DP+ Address:** `{analysis['sm_dp_address']}`\n"
            if analysis['activation_code']:
                response += f"🔑 **Activation Code:** `{analysis['activation_code']}`\n"
            else:
                response += f"🔑 **Activation Code:** _Không có_\n"
            
            response += f"\n🔗 **Link cài đặt iPhone:**\n`{install_link}`\n\n"
            response += f"**Cách sử dụng:**\n\n"
            response += f"📱 **iPhone:**\n"
            response += f"• Mở link trên iPhone (iOS 17.4+)\n"
            response += f"• Hoặc quét QR: Cài đặt → Cellular → Add Plan\n\n"
            response += f"🤖 **Android:**\n"
            response += f"• Quét QR: Cài đặt → Network → SIM → Add\n\n"
            response += f"💡 **Lưu ý:** Giữ kết nối WiFi ổn định khi cài đặt"
            
            # Gửi QR code image với thông tin
            await update.message.reply_photo(
                photo=qr_image,
                caption=response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi xử lý LPA string:** {str(e)}\n\n"
                f"💡 **Gợi ý:**\n"
                f"• Kiểm tra định dạng LPA string\n"
                f"• Đảm bảo có SM-DP+ address hợp lệ\n"
                f"• Thử lại với LPA string khác",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    # Tool 6: Quản lý Kho eSIM
    async def show_storage_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị menu quản lý kho eSIM"""
        query = update.callback_query
        
        # Lấy thống kê kho
        stats = esim_storage.get_storage_stats()
        
        menu_text = f"🏪 **KHO eSIM - QUẢN LÝ**\n\n"
        menu_text += f"📊 **Thống kê:**\n"
        menu_text += f"• 📦 Tổng: {stats['total']} eSIM\n"
        menu_text += f"• ✅ Có sẵn: {stats['available']} eSIM\n"
        menu_text += f"• 🔴 Đã dùng: {stats['used']} eSIM\n\n"
        menu_text += f"**Chọn thao tác:**"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Thêm eSIM", callback_data="add_esim"),
                InlineKeyboardButton("📋 Xem Kho", callback_data="view_available")
            ],
            [
                InlineKeyboardButton("🎯 Sử dụng eSIM", callback_data="use_esim"),
                InlineKeyboardButton("📊 eSIM Đã dùng", callback_data="view_used")
            ],
            [
                InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                menu_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                menu_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def start_add_esim(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu thêm eSIM vào kho - tự động nhận diện"""
        query = update.callback_query
        
        try:
            await query.edit_message_text(
                "➕ **THÊM eSIM VÀO KHO**\n\n"
                "Vui lòng gửi **một trong các định dạng sau**:\n\n"
                "📝 **LPA String:**\n"
                "• `LPA:1$rsp.truphone.com$CODE123`\n\n"
                "📎 **URL ảnh QR:**\n"
                "• `https://api.hisimtravel.com/images/abc123`\n\n"
                "🔧 **SM-DP+ Address:**\n"
                "• `rsp.truphone.com`\n\n"
                "💡 **Bot sẽ tự động nhận diện** loại dữ liệu bạn gửi!\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                "➕ **THÊM eSIM VÀO KHO**\n\n"
                "Vui lòng gửi **một trong các định dạng sau**:\n\n"
                "📝 **LPA String:**\n"
                "• `LPA:1$rsp.truphone.com$CODE123`\n\n"
                "📎 **URL ảnh QR:**\n"
                "• `https://api.hisimtravel.com/images/abc123`\n\n"
                "🔧 **SM-DP+ Address:**\n"
                "• `rsp.truphone.com`\n\n"
                "💡 **Bot sẽ tự động nhận diện** loại dữ liệu bạn gửi!\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        
        context.user_data['action'] = 'add_esim_auto'
        return WAITING_ADD_ESIM_LPA
    
    async def handle_add_esim_auto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tự động nhận diện và xử lý dữ liệu eSIM"""
        data = update.message.text.strip()
        
        # Detect data type
        if data.startswith('LPA:1$'):
            logger.info(f"Auto-detected: LPA string")
            context.user_data['lpa_string'] = data
            return await self.handle_add_esim_lpa(update, context)
        
        elif data.startswith('http://') or data.startswith('https://'):
            logger.info(f"Auto-detected: URL")
            return await self.handle_add_esim_url(update, context)
        
        else:
            is_valid, message = esim_tools.validate_sm_dp_address(data)
            if is_valid:
                logger.info(f"Auto-detected: SM-DP+ address")
                context.user_data['sm_dp_address'] = data
                return await self.handle_add_esim_sm_dp(update, context)
            else:
                await update.message.reply_text(
                    f"❌ **Không nhận diện được định dạng**\n\n"
                    f"**Dữ liệu bạn gửi:** `{data[:50]}{'...' if len(data) > 50 else ''}`\n\n"
                    f"💡 **Vui lòng gửi một trong các định dạng:**\n"
                    f"• LPA String: `LPA:1$...$...`\n"
                    f"• URL ảnh QR: `https://...`\n"
                    f"• SM-DP+ Address: `rsp.truphone.com`\n\n"
                    f"Gửi /cancel để hủy",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_ADD_ESIM_LPA
    
    async def start_add_esim_lpa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu thêm eSIM bằng LPA string"""
        query = update.callback_query
        try:
            await query.edit_message_text(
                "📝 **THÊM eSIM BẰNG LPA STRING**\n\n"
                "Vui lòng nhập **LPA String**:\n\n"
                "**Ví dụ:**\n"
                "• `LPA:1$rsp.truphone.com$CODE123`\n"
                "• `LPA:1$sm-dp.example.com$`\n\n"
                "**Lưu ý:** Bot sẽ tự động tách thông tin từ LPA string\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                "📝 **THÊM eSIM BẰNG LPA STRING**\n\n"
                "Vui lòng nhập **LPA String**:\n\n"
                "**Ví dụ:**\n"
                "• `LPA:1$rsp.truphone.com$CODE123`\n"
                "• `LPA:1$sm-dp.example.com$`\n\n"
                "**Lưu ý:** Bot sẽ tự động tách thông tin từ LPA string\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        context.user_data['action'] = 'add_esim_lpa'
        return WAITING_ADD_ESIM_LPA
    
    async def handle_add_esim_lpa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý LPA string khi thêm eSIM"""
        lpa_string = update.message.text.strip()
        
        try:
            # Validate LPA string
            is_valid, message = esim_tools.validate_lpa_string(lpa_string)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ **LPA String không hợp lệ**\n\n"
                    f"**Lỗi:** {message}\n\n"
                    f"**Ví dụ đúng:**\n"
                    f"• `LPA:1$rsp.truphone.com$CODE123`\n"
                    f"• `LPA:1$sm-dp.example.com$`\n\n"
                    f"Vui lòng nhập lại LPA string hợp lệ:",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_ADD_ESIM_LPA
            
            # Lưu LPA string để dùng sau
            context.user_data['lpa_string'] = lpa_string
            
            # Extract thông tin để hiển thị
            analysis = esim_tools.extract_sm_dp_and_activation(lpa_string)
            
            preview_text = f"✅ **LPA STRING HỢP LỆ**\n\n"
            preview_text += f"📋 **LPA:** `{lpa_string}`\n\n"
            preview_text += f"**Thông tin đã tách:**\n"
            preview_text += f"📍 **SM-DP+:** `{analysis['sm_dp_address']}`\n"
            if analysis['activation_code']:
                preview_text += f"🔑 **Activation Code:** `{analysis['activation_code']}`\n"
            else:
                preview_text += f"🔑 **Activation Code:** _Không có_\n"
            
            preview_text += f"\n🏷️ **Nhập mô tả cho eSIM này** (tùy chọn):\n\n"
            preview_text += f"**Ví dụ:**\n"
            preview_text += f"• `eSIM Viettel 30GB`\n"
            preview_text += f"• `Vinaphone 5G Unlimited`\n\n"
            preview_text += f"Gửi `/skip` để bỏ qua mô tả\n"
            preview_text += f"Gửi `/cancel` để hủy"
            
            await update.message.reply_text(
                preview_text,
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_ADD_ESIM_LPA_DESC
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi xử lý LPA string:** {str(e)}\n\n"
                f"Vui lòng thử lại với LPA string khác!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_storage_keyboard()
            )
            return ConversationHandler.END
    
    async def handle_add_esim_lpa_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý mô tả và lưu eSIM từ LPA string vào kho"""
        description = ""
        if update.message.text.strip() != "/skip":
            description = update.message.text.strip()
        
        lpa_string = context.user_data['lpa_string']
        
        try:
            # Thêm eSIM vào kho bằng LPA string
            esim_id = esim_storage.add_esim_from_lpa(lpa_string, description)
            
            # Log activity
            user = update.effective_user
            logger.info(f"[ADD eSIM] User: {user.username or user.id} | ID: {esim_id} | Type: LPA String | Desc: {description or 'N/A'}")
            
            # Extract thông tin để hiển thị
            analysis = esim_tools.extract_sm_dp_and_activation(lpa_string)
            
            # Tạo response
            response = f"✅ **ĐÃ THÊM eSIM VÀO KHO THÀNH CÔNG**\n\n"
            response += f"🆔 **ID:** `{esim_id}`\n"
            response += f"📋 **LPA String:** `{lpa_string}`\n"
            response += f"📍 **SM-DP+:** `{analysis['sm_dp_address']}`\n"
            if analysis['activation_code']:
                response += f"🔑 **Activation Code:** `{analysis['activation_code']}`\n"
            if description:
                response += f"🏷️ **Mô tả:** {description}\n"
            response += f"\n💡 **Ghi chú:** eSIM đã được lưu vào kho và sẵn sàng sử dụng"
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_storage_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi thêm eSIM vào kho:** {str(e)}\n\n"
                f"Vui lòng thử lại sau!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    async def start_add_esim_smdp(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu thêm eSIM bằng SM-DP+ address"""
        query = update.callback_query
        try:
            await query.edit_message_text(
                "🔧 **THÊM eSIM BẰNG SM-DP+ ADDRESS**\n\n"
                "Vui lòng nhập **SM-DP+ Address**:\n\n"
                "**Ví dụ:** `rsp.truphone.com`\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                "🔧 **THÊM eSIM BẰNG SM-DP+ ADDRESS**\n\n"
                "Vui lòng nhập **SM-DP+ Address**:\n\n"
                "**Ví dụ:** `rsp.truphone.com`\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        context.user_data['action'] = 'add_esim_smdp'
        return WAITING_ADD_ESIM_SM_DP
    
    async def handle_add_esim_sm_dp(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý SM-DP+ address khi thêm eSIM"""
        sm_dp_address = update.message.text.strip()
        
        # Validate SM-DP+ address
        is_valid, message = esim_tools.validate_sm_dp_address(sm_dp_address)
        if not is_valid:
            await update.message.reply_text(
                f"❌ {message}\n\nVui lòng nhập lại SM-DP+ Address hợp lệ:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_ADD_ESIM_SM_DP
        
        context.user_data['sm_dp_address'] = sm_dp_address
        
        await update.message.reply_text(
            "✅ SM-DP+ Address hợp lệ!\n\n"
            "Bây giờ nhập **Activation Code** (tùy chọn):\n"
            "Gửi `/skip` nếu không có mã kích hoạt\n"
            "Gửi `/cancel` để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_ADD_ESIM_CODE
    
    async def handle_add_esim_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý activation code khi thêm eSIM"""
        activation_code = ""
        if update.message.text.strip() != "/skip":
            activation_code = update.message.text.strip()
        
        context.user_data['activation_code'] = activation_code
        
        await update.message.reply_text(
            "🏷️ **Nhập mô tả cho eSIM này** (tùy chọn):\n\n"
            "**Ví dụ:**\n"
            "• `eSIM Viettel 30GB`\n"
            "• `Vinaphone 5G Unlimited`\n"
            "• `eSIM cho du lịch Thái Lan`\n\n"
            "Gửi `/skip` để bỏ qua mô tả\n"
            "Gửi `/cancel` để hủy",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_ADD_ESIM_DESC
    
    async def handle_add_esim_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý mô tả và lưu eSIM vào kho"""
        description = ""
        if update.message.text.strip() != "/skip":
            description = update.message.text.strip()
        
        sm_dp_address = context.user_data['sm_dp_address']
        activation_code = context.user_data['activation_code']
        
        try:
            # Thêm eSIM vào kho
            esim_id = esim_storage.add_esim(sm_dp_address, activation_code, description)
            
            # Log activity
            user = update.effective_user
            logger.info(f"[ADD eSIM] User: {user.username or user.id} | ID: {esim_id} | SM-DP+: {sm_dp_address} | Desc: {description or 'N/A'}")
            
            # Tạo response
            response = f"✅ **ĐÃ THÊM eSIM VÀO KHO THÀNH CÔNG**\n\n"
            response += f"🆔 **ID:** `{esim_id}`\n"
            response += f"📍 **SM-DP+:** `{sm_dp_address}`\n"
            if activation_code:
                response += f"🔑 **Activation Code:** `{activation_code}`\n"
            if description:
                response += f"🏷️ **Mô tả:** {description}\n"
            response += f"\n💡 **Ghi chú:** eSIM đã được lưu vào kho và sẵn sàng sử dụng"
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_storage_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi thêm eSIM vào kho:** {str(e)}\n\n"
                f"Vui lòng thử lại sau!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    async def start_add_esim_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu thêm eSIM bằng URL"""
        query = update.callback_query
        try:
            await query.edit_message_text(
                "📎 **THÊM eSIM BẰNG URL ẢNH QR**\n\n"
                "Vui lòng nhập **URL chứa ảnh QR code eSIM**:\n\n"
                "**Ví dụ:**\n"
                "• `https://api.hisimtravel.com/images/abc123`\n"
                "• `https://example.com/qr/esim.png`\n"
                "• URL ảnh từ nhà cung cấp eSIM\n\n"
                "**Lưu ý:** Bot sẽ tự động tải ảnh và đọc QR code\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                "📎 **THÊM eSIM BẰNG URL ẢNH QR**\n\n"
                "Vui lòng nhập **URL chứa ảnh QR code eSIM**:\n\n"
                "**Ví dụ:**\n"
                "• `https://api.hisimtravel.com/images/abc123`\n"
                "• `https://example.com/qr/esim.png`\n"
                "• URL ảnh từ nhà cung cấp eSIM\n\n"
                "**Lưu ý:** Bot sẽ tự động tải ảnh và đọc QR code\n\n"
                "Gửi /cancel để hủy",
                parse_mode=ParseMode.MARKDOWN
            )
        context.user_data['action'] = 'add_esim_url'
        return WAITING_ADD_ESIM_URL
    
    async def handle_add_esim_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý URL ảnh QR khi thêm eSIM"""
        url = update.message.text.strip()
        
        # Hiển thị đang xử lý
        processing_msg = await update.message.reply_text(
            "🔄 **Đang tải và phân tích ảnh QR...**\n\n"
            "⏳ Vui lòng đợi trong giây lát...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Import requests để download ảnh
            import requests
            
            # Download ảnh từ URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            image_data = response.content
            
            # Phân tích QR từ ảnh
            analysis = esim_tools.analyze_qr_image(image_data)
            
            # Xóa message đang xử lý
            await processing_msg.delete()
            
            if not analysis['qr_detected']:
                await update.message.reply_text(
                    f"❌ **KHÔNG ĐỌC ĐƯỢC QR CODE TỪ ẢNH**\n\n"
                    f"**Lỗi:** {analysis.get('error', 'Không xác định')}\n\n"
                    f"💡 **Gợi ý:**\n"
                    f"• Kiểm tra URL có đúng không\n"
                    f"• Đảm bảo URL trỏ đến ảnh QR code\n"
                    f"• Thử với URL khác\n\n"
                    f"Vui lòng nhập lại URL hợp lệ:",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_ADD_ESIM_URL
            
            if not analysis['sm_dp_address']:
                await update.message.reply_text(
                    f"❌ **KHÔNG TÌM THẤY THÔNG TIN eSIM**\n\n"
                    f"**Lỗi:** QR code không chứa thông tin eSIM hợp lệ\n\n"
                    f"Vui lòng nhập lại URL khác:",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_ADD_ESIM_URL
            
            # Lưu thông tin để dùng sau
            context.user_data['url'] = url
            context.user_data['sm_dp_from_url'] = analysis['sm_dp_address']
            context.user_data['code_from_url'] = analysis['activation_code'] or ""
            
            # Tạo LPA string từ thông tin đã extract
            if analysis['activation_code']:
                lpa_string = f"LPA:1${analysis['sm_dp_address']}${analysis['activation_code']}"
            else:
                lpa_string = f"LPA:1${analysis['sm_dp_address']}$"
            
            context.user_data['lpa_from_url'] = lpa_string
            
            # Hiển thị preview
            preview_text = f"✅ **ĐỌC QR CODE THÀNH CÔNG**\n\n"
            preview_text += f"🔗 **URL:** `{url[:60]}{'...' if len(url) > 60 else ''}`\n"
            preview_text += f"📱 **Nguồn:** Ảnh QR code từ URL\n\n"
            preview_text += f"**Thông tin đã tách:**\n"
            preview_text += f"📍 **SM-DP+:** `{analysis['sm_dp_address']}`\n"
            if analysis['activation_code']:
                preview_text += f"🔑 **Activation Code:** `{analysis['activation_code']}`\n"
            else:
                preview_text += f"� **Atctivation Code:** _Không có_\n"
            preview_text += f"📋 **LPA String:** `{lpa_string}`\n"
            
            preview_text += f"\n🏷️ **Nhập mô tả cho eSIM này** (tùy chọn):\n\n"
            preview_text += f"**Ví dụ:**\n"
            preview_text += f"• `eSIM Viettel 30GB`\n"
            preview_text += f"• `Vinaphone 5G Unlimited`\n\n"
            preview_text += f"Gửi `/skip` để bỏ qua mô tả\n"
            preview_text += f"Gửi `/cancel` để hủy"
            
            await update.message.reply_text(
                preview_text,
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_ADD_ESIM_URL_DESC
            
        except requests.exceptions.RequestException as e:
            # Xóa processing message nếu còn
            try:
                await processing_msg.delete()
            except:
                pass
            
            await update.message.reply_text(
                f"❌ **Lỗi tải ảnh từ URL:** {str(e)}\n\n"
                f"💡 **Gợi ý:**\n"
                f"• Kiểm tra URL có đúng không\n"
                f"• Đảm bảo URL có thể truy cập được\n"
                f"• Thử lại sau vài giây\n\n"
                f"Vui lòng thử lại với URL khác!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_storage_keyboard()
            )
            return ConversationHandler.END
            
        except Exception as e:
            # Xóa processing message nếu còn
            try:
                await processing_msg.delete()
            except:
                pass
            
            await update.message.reply_text(
                f"❌ **Lỗi xử lý URL:** {str(e)}\n\n"
                f"Vui lòng thử lại với URL khác!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_storage_keyboard()
            )
            return ConversationHandler.END
    
    async def handle_add_esim_url_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý mô tả và lưu eSIM từ URL vào kho"""
        description = ""
        if update.message.text.strip() != "/skip":
            description = update.message.text.strip()
        
        lpa_string = context.user_data['lpa_from_url']
        
        try:
            # Thêm eSIM vào kho bằng LPA string
            esim_id = esim_storage.add_esim_from_lpa(lpa_string, description)
            
            # Log activity
            user = update.effective_user
            logger.info(f"[ADD eSIM] User: {user.username or user.id} | ID: {esim_id} | Type: URL | Desc: {description or 'N/A'}")
            
            # Extract thông tin để hiển thị
            sm_dp_address = context.user_data['sm_dp_from_url']
            activation_code = context.user_data['code_from_url']
            
            # Tạo response
            response = f"✅ **ĐÃ THÊM eSIM VÀO KHO THÀNH CÔNG**\n\n"
            response += f"🆔 **ID:** `{esim_id}`\n"
            response += f"📍 **SM-DP+:** `{sm_dp_address}`\n"
            if activation_code:
                response += f"🔑 **Activation Code:** `{activation_code}`\n"
            response += f"📋 **LPA String:** `{lpa_string}`\n"
            if description:
                response += f"🏷️ **Mô tả:** {description}\n"
            response += f"\n💡 **Ghi chú:** eSIM đã được lưu vào kho và sẵn sàng sử dụng"
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_storage_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi thêm eSIM vào kho:** {str(e)}\n\n"
                f"Vui lòng thử lại sau!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_back_keyboard()
            )
        
        return ConversationHandler.END
    
    async def view_available_esims(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xem danh sách eSIM có sẵn"""
        query = update.callback_query
        
        esims = esim_storage.get_available_esims()
        
        if not esims:
            try:
                await query.edit_message_text(
                    "📋 **KHO eSIM - DANH SÁCH CÓ SẴN**\n\n"
                    "❌ **Kho trống!**\n\n"
                    "Chưa có eSIM nào trong kho. Vui lòng thêm eSIM mới.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Thêm eSIM", callback_data="add_esim")],
                        [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
                    ])
                )
            except Exception as e:
                logger.warning(f"Could not edit message, sending new one: {e}")
                await query.message.reply_text(
                    "📋 **KHO eSIM - DANH SÁCH CÓ SẴN**\n\n"
                    "❌ **Kho trống!**\n\n"
                    "Chưa có eSIM nào trong kho. Vui lòng thêm eSIM mới.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Thêm eSIM", callback_data="add_esim")],
                        [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
                    ])
                )
            return
        
        # Tạo danh sách eSIM
        response = f"📋 **KHO eSIM - CÓ SẴN ({len(esims)} eSIM)**\n\n"
        
        for i, esim in enumerate(esims[:10], 1):  # Hiển thị tối đa 10 eSIM
            response += f"**{i}. ID: {esim.id}**\n"
            response += f"📍 `{esim.sm_dp_address}`\n"
            if esim.activation_code:
                response += f"🔑 `{esim.activation_code}`\n"
            if esim.description:
                response += f"🏷️ {esim.description}\n"
            response += f"📅 {esim.added_date[:10]}\n\n"
        
        if len(esims) > 10:
            response += f"... và {len(esims) - 10} eSIM khác\n\n"
        
        response += "**Chọn thao tác:**"
        
        keyboard = [
            [InlineKeyboardButton("🎯 Sử dụng eSIM", callback_data="use_esim")],
            [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def start_use_esim(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu sử dụng eSIM từ kho"""
        query = update.callback_query
        
        esims = esim_storage.get_available_esims()
        
        if not esims:
            try:
                await query.edit_message_text(
                    "🎯 **SỬ DỤNG eSIM TỪ KHO**\n\n"
                    "❌ **Không có eSIM nào trong kho!**\n\n"
                    "Vui lòng thêm eSIM vào kho trước.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Thêm eSIM", callback_data="add_esim")],
                        [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
                    ])
                )
            except Exception as e:
                logger.warning(f"Could not edit message, sending new one: {e}")
                await query.message.reply_text(
                    "🎯 **SỬ DỤNG eSIM TỪ KHO**\n\n"
                    "❌ **Không có eSIM nào trong kho!**\n\n"
                    "Vui lòng thêm eSIM vào kho trước.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Thêm eSIM", callback_data="add_esim")],
                        [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
                    ])
                )
            return ConversationHandler.END
        
        # Tạo keyboard chọn eSIM
        keyboard = []
        for esim in esims[:20]:  # Tối đa 20 eSIM
            display_text = f"{esim.id} - {esim.sm_dp_address[:25]}"
            if esim.description:
                display_text += f" ({esim.description[:15]})"
            keyboard.append([InlineKeyboardButton(display_text, callback_data=f"select_esim_{esim.id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        response = f"🎯 **CHỌN eSIM ĐỂ SỬ DỤNG**\n\n"
        response += f"📦 **Có {len(esims)} eSIM trong kho**\n\n"
        response += f"Chọn eSIM để tạo QR code và link cài đặt:"
        
        try:
            await query.edit_message_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        
        context.user_data['action'] = 'use_esim'
        return WAITING_ESIM_SELECTION
    
    async def handle_esim_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý việc chọn eSIM để sử dụng"""
        query = update.callback_query
        await query.answer()
        
        if not query.data.startswith('select_esim_'):
            return ConversationHandler.END
        
        esim_id = query.data.replace('select_esim_', '')
        
        # Lấy thông tin eSIM
        esim = esim_storage.get_esim_by_id(esim_id)
        if not esim or esim.status != 'available':
            try:
                await query.edit_message_text(
                    "❌ **eSIM không tồn tại hoặc đã được sử dụng!**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_storage_keyboard()
                )
            except Exception as e:
                logger.warning(f"Could not edit message, sending new one: {e}")
                await query.message.reply_text(
                    "❌ **eSIM không tồn tại hoặc đã được sử dụng!**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_storage_keyboard()
                )
            return ConversationHandler.END
        
        try:
            # Tạo QR code và link từ eSIM
            qr_image, lpa_string = esim_tools.create_qr_from_lpa(esim.lpa_string)
            install_link = f"https://esimsetup.apple.com/esim_qrcode_provisioning?carddata={esim.lpa_string}"
            
            # Đánh dấu eSIM đã sử dụng
            user_info = f"{update.effective_user.id} (@{update.effective_user.username})"
            success = esim_storage.mark_esim_used(esim_id, user_info)
            
            if not success:
                await query.edit_message_text(
                    "❌ **Không thể sử dụng eSIM này (có thể đã được sử dụng)!**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_storage_keyboard()
                )
                return ConversationHandler.END
            
            # Log activity
            user = update.effective_user
            logger.info(f"[USE eSIM] User: {user.username or user.id} | ID: {esim_id} | SM-DP+: {esim.sm_dp_address}")
            
            # Tạo response message
            response = f"✅ **ĐÃ SỬ DỤNG eSIM TỪ KHO**\n\n"
            response += f"🆔 **ID:** `{esim.id}`\n"
            response += f"📍 **SM-DP+:** `{esim.sm_dp_address}`\n"
            if esim.activation_code:
                response += f"🔑 **Activation Code:** `{esim.activation_code}`\n"
            if esim.description:
                response += f"🏷️ **Mô tả:** {esim.description}\n"
            
            response += f"\n📋 **LPA String:** `{esim.lpa_string}`\n"
            response += f"🔗 **Link cài đặt iPhone:**\n`{install_link}`\n\n"
            
            response += f"**Cách sử dụng:**\n\n"
            response += f"📱 **iPhone:** Mở link hoặc quét QR\n"
            response += f"🤖 **Android:** Quét QR code\n\n"
            response += f"💡 **Lưu ý:** eSIM này đã được chuyển vào mục 'Đã sử dụng'"
            
            # Gửi QR code với thông tin
            await query.message.reply_photo(
                photo=qr_image,
                caption=response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.get_storage_keyboard()
            )
            
            # Xóa message cũ
            await query.delete_message()
            
        except Exception as e:
            try:
                await query.edit_message_text(
                    f"❌ **Lỗi sử dụng eSIM:** {str(e)}\n\n"
                    f"Vui lòng thử lại!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_storage_keyboard()
                )
            except Exception as ex:
                logger.warning(f"Could not edit message, sending new one: {ex}")
                await query.message.reply_text(
                    f"❌ **Lỗi sử dụng eSIM:** {str(e)}\n\n"
                    f"Vui lòng thử lại!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_storage_keyboard()
                )
        
        return ConversationHandler.END
    
    async def view_used_esims(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xem danh sách eSIM đã sử dụng"""
        query = update.callback_query
        
        esims = esim_storage.get_used_esims()
        
        if not esims:
            try:
                await query.edit_message_text(
                    "📊 **eSIM ĐÃ SỬ DỤNG**\n\n"
                    "✅ **Chưa có eSIM nào được sử dụng!**\n\n"
                    "Danh sách này sẽ hiển thị các eSIM đã được tạo QR và link.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
                    ])
                )
            except Exception as e:
                logger.warning(f"Could not edit message, sending new one: {e}")
                await query.message.reply_text(
                    "📊 **eSIM ĐÃ SỬ DỤNG**\n\n"
                    "✅ **Chưa có eSIM nào được sử dụng!**\n\n"
                    "Danh sách này sẽ hiển thị các eSIM đã được tạo QR và link.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
                    ])
                )
            return
        
        # Tạo danh sách eSIM đã dùng
        response = f"📊 **eSIM ĐÃ SỬ DỤNG ({len(esims)} eSIM)**\n\n"
        
        for i, esim in enumerate(esims[:10], 1):  # Hiển thị tối đa 10 eSIM
            response += f"**{i}. ID: {esim.id}**\n"
            response += f"📍 `{esim.sm_dp_address}`\n"
            if esim.description:
                response += f"🏷️ {esim.description}\n"
            response += f"📅 Dùng: {esim.used_date[:10] if esim.used_date else 'N/A'}\n"
            if esim.used_by:
                response += f"👤 Bởi: {esim.used_by}\n"
            response += "\n"
        
        if len(esims) > 10:
            response += f"... và {len(esims) - 10} eSIM khác\n\n"
        
        response += "💡 **Ghi chú:** Đây là lịch sử các eSIM đã được tạo QR/link"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Về Menu Kho", callback_data="storage_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            await query.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    def get_storage_keyboard(self):
        """Tạo keyboard quay về menu kho"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏪 Về Menu Kho", callback_data="storage_menu")],
            [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
        ])
    
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
• 📝 **Từ LPA String** - Tạo link và QR từ LPA string có sẵn
• 🏪 **Kho eSIM** - Quản lý kho eSIM: thêm, sử dụng, theo dõi

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
    
    async def get_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler để lấy user ID cho debug"""
        user = update.effective_user
        response = f"🆔 **THÔNG TIN USER**\n\n"
        response += f"**User ID:** `{user.id}`\n"
        response += f"**Username:** @{user.username}\n"
        response += f"**First Name:** {user.first_name}\n"
        if user.last_name:
            response += f"**Last Name:** {user.last_name}\n"
        response += f"\n**Admin IDs configured:** `{ADMIN_IDS}`\n"
        response += f"**Is Admin:** {'✅ Yes' if user.id in ADMIN_IDS else '❌ No'}\n\n"
        response += "Copy User ID trên để cấu hình admin trong file config.py"
        
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def debug_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Debug handler để log tất cả messages"""
    
    # ==================== CHECK ICCID HANDLERS ====================
    
    async def start_check_iccid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow check ICCID"""
        query = update.callback_query
        
        keyboard = [
            [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 **CHECK THÔNG TIN eSIM**\n\n"
            "Vui lòng gửi **mã ICCID** của eSIM cần kiểm tra.\n\n"
            "📋 ICCID thường có 19-20 chữ số, bắt đầu bằng 89...\n\n"
            "Gửi /cancel để hủy",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_ICCID
    
    async def handle_iccid_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý ICCID được gửi từ user"""
        user = update.effective_user
        iccid = update.message.text.strip()
        
        logger.info(f"[CHECK ICCID] User: {user.username or user.id} | ICCID: {iccid}")
        
        # Gửi thông báo đang xử lý
        processing_msg = await update.message.reply_text(
            "⏳ Đang kiểm tra thông tin eSIM...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Gọi API
        result = simplifytrip_api.check_iccid(iccid)
        
        keyboard = [
            [InlineKeyboardButton("🔍 Check ICCID khác", callback_data="check_iccid")],
            [InlineKeyboardButton("🔙 Về Menu Chính", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if result['success']:
            # Format và gửi thông tin
            formatted_info = simplifytrip_api.format_esim_info(result['data'])
            plan_status = result['data'].get('planStatus', 'N/A')
            logger.info(f"[CHECK ICCID] Success | ICCID: {iccid} | Status: {plan_status}")
            
            await processing_msg.edit_text(
                formatted_info,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            logger.warning(f"[CHECK ICCID] Failed | ICCID: {iccid} | Error: {result['error']}")
            # Gửi thông báo lỗi
            await processing_msg.edit_text(
                f"❌ **Không thể kiểm tra ICCID**\n\n"
                f"**Lý do:** {result['error']}\n\n"
                f"**ICCID đã nhập:** `{iccid}`",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    
    def setup_handlers(self):
        """Thiết lập các handlers cho bot"""
        # Access control filters
        admin_filter = filters.User(user_id=ADMIN_IDS)
        non_admin_filter = ~filters.User(user_id=ADMIN_IDS)

        # Log admin IDs để debug

        # Command handlers
        # /start - mọi người đều dùng được
        self.application.add_handler(CommandHandler("start", self.start))
        # /help - chỉ admin
        self.application.add_handler(CommandHandler("help", self.help_command, filters=admin_filter))
        
        # Debug command để kiểm tra user ID (không cần filter admin)
        self.application.add_handler(CommandHandler("myid", self.get_user_id))
        
        # Conversation handler cho tạo link & QR (unified) - mọi người đều dùng được
        create_link_qr_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_create_link_qr, pattern="^create_link_qr$")],
            states={
                WAITING_SM_DP_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_create_link_qr_auto)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Conversation handler cho thêm eSIM vào kho
        add_esim_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_add_esim, pattern="^add_esim$")
            ],
            states={
                WAITING_ADD_ESIM_SM_DP: [MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.handle_add_esim_sm_dp)],
                WAITING_ADD_ESIM_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.handle_add_esim_code)],
                WAITING_ADD_ESIM_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.handle_add_esim_desc)],
                WAITING_ADD_ESIM_LPA: [MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.handle_add_esim_auto)],
                WAITING_ADD_ESIM_LPA_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.handle_add_esim_lpa_desc)],
                WAITING_ADD_ESIM_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.handle_add_esim_url)],
                WAITING_ADD_ESIM_URL_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.handle_add_esim_url_desc)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Conversation handler cho sử dụng eSIM từ kho
        use_esim_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_use_esim, pattern="^use_esim$")],
            states={
                WAITING_ESIM_SELECTION: [CallbackQueryHandler(self.handle_esim_selection, pattern="^select_esim_")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Conversation handler cho check ICCID - mọi người đều dùng được
        check_iccid_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_check_iccid, pattern="^check_iccid$")],
            states={
                WAITING_ICCID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_iccid_input)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Thêm các conversation handlers
        self.application.add_handler(create_link_qr_handler, group=1)
        self.application.add_handler(add_esim_handler, group=1)
        self.application.add_handler(use_esim_handler, group=1)
        self.application.add_handler(check_iccid_handler, group=1)
        
        # Button callback handler
        self.application.add_handler(CallbackQueryHandler(self.button_handler), group=1)
        
        # Catch all unauthorized callbacks (phải đặt ở group thấp hơn)
        self.application.add_handler(CallbackQueryHandler(self.unauthorized_callback), group=2)
        
        # Debug message handler (thêm cuối cùng để catch tất cả)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, self.debug_message_handler), group=3)
    
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
        
        # Startup message
        print("🤖 eSIM Support Bot đã khởi động!")
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