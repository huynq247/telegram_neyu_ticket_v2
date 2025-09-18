"""
Telegram Bot Handler Module
Xử lý tin nhắn từ Telegram và tương tác với người dùng
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

logger = logging.getLogger(__name__)

# States cho conversation
WAITING_DESCRIPTION, WAITING_PRIORITY = range(2)

class TelegramBotHandler:
    """Class xử lý Telegram Bot"""
    
    def __init__(self, token: str, ticket_manager):
        """
        Khởi tạo Telegram Bot Handler
        
        Args:
            token: Token của Telegram Bot
            ticket_manager: Instance của TicketManager
        """
        self.token = token
        self.ticket_manager = ticket_manager
        self.application = None
        
        # Dictionary để lưu trữ dữ liệu tạm thời của user
        self.user_data = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /start"""
        user = update.effective_user
        welcome_message = (
            f"Chào mừng {user.first_name}! 👋\n\n"
            "Tôi là bot hỗ trợ tạo ticket.\n"
            "Sử dụng các lệnh sau:\n\n"
            "/newticket - Tạo ticket mới\n"
            "/mytickets - Xem tickets của bạn\n"
            "/help - Hướng dẫn sử dụng"
        )
        
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} ({user.username}) bắt đầu sử dụng bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /help"""
        help_text = (
            "📋 *Hướng dẫn sử dụng Bot*\n\n"
            "🆕 */newticket* - Tạo ticket hỗ trợ mới\n"
            "📝 */mytickets* - Xem danh sách tickets của bạn\n"
            "❓ */help* - Hiển thị hướng dẫn này\n\n"
            "💡 *Cách tạo ticket:*\n"
            "1. Gõ /newticket\n"
            "2. Nhập tiêu đề và mô tả vấn đề\n"
            "3. Chọn độ ưu tiên\n"
            "4. Xác nhận tạo ticket\n\n"
            "✅ Bạn sẽ nhận được thông báo khi ticket được xử lý xong!"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def new_ticket_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Bắt đầu tạo ticket mới"""
        user = update.effective_user
        
        # Khởi tạo dữ liệu user
        self.user_data[user.id] = {
            'user_id': user.id,
            'username': user.username or user.first_name,
            'chat_id': update.effective_chat.id,
            'first_name': user.first_name,
            'last_name': user.last_name or ''
        }
        
        await update.message.reply_text(
            "🎫 *Tạo ticket mới*\n\n"
            "Vui lòng mô tả vấn đề bạn gặp phải:\n"
            "(Gõ /cancel để hủy)",
            parse_mode='Markdown'
        )
        
        return WAITING_DESCRIPTION
    
    async def receive_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Nhận mô tả từ user"""
        user_id = update.effective_user.id
        description = update.message.text
        
        # Lưu mô tả
        self.user_data[user_id]['description'] = description
        
        # Tạo keyboard cho độ ưu tiên
        keyboard = [
            [InlineKeyboardButton("🔴 Cao", callback_data="priority_high")],
            [InlineKeyboardButton("🟡 Trung bình", callback_data="priority_medium")],
            [InlineKeyboardButton("🟢 Thấp", callback_data="priority_low")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ Đã nhận mô tả của bạn!\n\n"
            "Vui lòng chọn độ ưu tiên cho ticket:",
            reply_markup=reply_markup
        )
        
        return WAITING_PRIORITY
    
    async def priority_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý callback chọn độ ưu tiên"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        priority_map = {
            'priority_high': ('3', '🔴 Cao'),
            'priority_medium': ('2', '🟡 Trung bình'),
            'priority_low': ('1', '🟢 Thấp')
        }
        
        priority_code, priority_text = priority_map.get(query.data, ('2', '🟡 Trung bình'))
        self.user_data[user_id]['priority'] = priority_code
        
        # Hiển thị thông tin ticket để xác nhận
        user_data = self.user_data[user_id]
        confirmation_text = (
            "📋 *Xác nhận thông tin ticket:*\n\n"
            f"👤 *Người tạo:* {user_data['first_name']}\n"
            f"📝 *Mô tả:* {user_data['description']}\n"
            f"⚡ *Độ ưu tiên:* {priority_text}\n\n"
            "Xác nhận tạo ticket?"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Xác nhận", callback_data="confirm_ticket")],
            [InlineKeyboardButton("❌ Hủy", callback_data="cancel_ticket")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            confirmation_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return WAITING_PRIORITY
    
    async def confirm_ticket_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xác nhận tạo ticket"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "cancel_ticket":
            await query.edit_message_text("❌ Đã hủy tạo ticket.")
            if user_id in self.user_data:
                del self.user_data[user_id]
            return ConversationHandler.END
        
        if query.data == "confirm_ticket":
            try:
                # Tạo ticket qua TicketManager
                user_data = self.user_data[user_id]
                ticket_data = {
                    'title': f"Ticket từ Telegram - {user_data['username']}",
                    'description': user_data['description'],
                    'telegram_chat_id': str(user_data['chat_id']),
                    'priority': int(user_data['priority'])  # Ensure integer
                }
                
                result = await self.ticket_manager.create_ticket(ticket_data)
                
                if result['success']:
                    ticket_id = result['ticket_id']
                    success_message = (
                        "✅ *Ticket đã được tạo thành công!*\n\n"
                        f"🎫 *Mã ticket:* #{ticket_id}\n"
                        f"📝 *Mô tả:* {user_data['description'][:100]}...\n\n"
                        "Chúng tôi sẽ xử lý và thông báo kết quả cho bạn sớm nhất!"
                    )
                    logger.info(f"Tạo ticket thành công ID: {ticket_id} cho user {user_id}")
                else:
                    success_message = (
                        "❌ *Lỗi tạo ticket!*\n\n"
                        f"📝 *Lỗi:* {result['message']}\n\n"
                        "Vui lòng thử lại sau hoặc liên hệ admin."
                    )
                    logger.error(f"Lỗi tạo ticket cho user {user_id}: {result['message']}")
                
                await query.edit_message_text(success_message, parse_mode='Markdown')
                
                # Xóa dữ liệu tạm
                if user_id in self.user_data:
                    del self.user_data[user_id]
                
                logger.info(f"Tạo ticket thành công ID: {ticket_id} cho user {user_id}")
                
            except Exception as e:
                logger.error(f"Lỗi tạo ticket cho user {user_id}: {e}")
                await query.edit_message_text(
                    "❌ Có lỗi xảy ra khi tạo ticket. Vui lòng thử lại sau."
                )
        
        return ConversationHandler.END
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Hủy tạo ticket"""
        user_id = update.effective_user.id
        if user_id in self.user_data:
            del self.user_data[user_id]
        
        await update.message.reply_text("❌ Đã hủy tạo ticket.")
        return ConversationHandler.END
    
    async def my_tickets_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xem tickets của user"""
        user_id = update.effective_user.id
        
        try:
            tickets = await self.ticket_manager.get_user_tickets(str(user_id))
            
            if not tickets:
                await update.message.reply_text(
                    "📝 Bạn chưa có ticket nào.\n"
                    "Sử dụng /newticket để tạo ticket mới."
                )
                return
            
            tickets_text = "📋 *Danh sách tickets của bạn:*\n\n"
            
            for ticket in tickets[:10]:  # Hiển thị tối đa 10 tickets
                stage_emoji = "🔄" if ticket.get('stage_id', [False, ''])[1] != 'Done' else "✅"
                tickets_text += (
                    f"{stage_emoji} *#{ticket['id']}* - {ticket['name'][:50]}...\n"
                    f"📅 {ticket.get('create_date', 'N/A')}\n\n"
                )
            
            await update.message.reply_text(tickets_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Lỗi lấy tickets cho user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Có lỗi khi lấy danh sách tickets. Vui lòng thử lại sau."
            )
    
    async def send_ticket_completion_notification(self, chat_id: str, ticket_info: Dict[str, Any]) -> bool:
        """
        Gửi thông báo ticket hoàn thành
        
        Args:
            chat_id: ID chat Telegram
            ticket_info: Thông tin ticket
            
        Returns:
            True nếu gửi thành công
        """
        try:
            message = (
                "🎉 *Ticket của bạn đã được xử lý xong!*\n\n"
                f"🎫 *Mã ticket:* #{ticket_info['id']}\n"
                f"📝 *Tiêu đề:* {ticket_info['name']}\n"
                f"✅ *Trạng thái:* Hoàn thành\n"
                f"📅 *Ngày hoàn thành:* {ticket_info.get('write_date', 'N/A')}\n\n"
                "Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi!"
            )
            
            await self.application.bot.send_message(
                chat_id=int(chat_id),
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Gửi thông báo hoàn thành ticket {ticket_info['id']} cho chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi gửi thông báo hoàn thành ticket: {e}")
            return False
    
    async def unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý tin nhắn không xác định"""
        await update.message.reply_text(
            "🤔 Tôi không hiểu tin nhắn của bạn.\n"
            "Sử dụng /help để xem hướng dẫn."
        )
    
    def setup_handlers(self) -> None:
        """Thiết lập các handlers cho bot"""
        # Conversation handler cho tạo ticket
        ticket_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("newticket", self.new_ticket_command)],
            states={
                WAITING_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_description)
                ],
                WAITING_PRIORITY: [
                    CallbackQueryHandler(self.priority_callback, pattern="^priority_"),
                    CallbackQueryHandler(self.confirm_ticket_callback, pattern="^(confirm_ticket|cancel_ticket)$")
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)]
        )
        
        # Thêm handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("mytickets", self.my_tickets_command))
        self.application.add_handler(ticket_conv_handler)
        self.application.add_handler(MessageHandler(filters.TEXT, self.unknown_message))
    
    async def initialize(self) -> None:
        """Khởi tạo bot"""
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        logger.info("Telegram Bot đã được khởi tạo")
    
    async def start_polling(self) -> None:
        """Bắt đầu polling"""
        if not self.application:
            await self.initialize()
        
        logger.info("Bắt đầu Telegram Bot polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
    
    async def stop(self) -> None:
        """Dừng bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram Bot đã dừng")