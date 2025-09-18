"""
Main Telegram Bot Handler - Modular Version
Coordinator chính điều phối các module con
"""
import asyncio
import logging
import threading
from typing import Dict, Any, Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Import các modules
from .handlers.start_handler import StartHandler
from .services.ticket_service import TicketService
from .services.user_service import UserService
from .utils.keyboards import BotKeyboards
from .utils.formatters import BotFormatters
from .utils.validators import BotValidators

logger = logging.getLogger(__name__)

# States cho conversation
WAITING_DESTINATION, WAITING_DESCRIPTION, WAITING_PRIORITY = range(3)

class TelegramBotHandler:
    """Main Bot Handler - Modular Version"""
    
    def __init__(self, token: str, ticket_manager):
        """
        Khởi tạo Bot Handler
        
        Args:
            token: Telegram Bot Token
            ticket_manager: Instance của TicketManager
        """
        self.token = token
        self.ticket_manager = ticket_manager
        self.application = None
        self.running = False
        
        # Initialize modules
        self.start_handler = StartHandler()
        self.ticket_service = TicketService(ticket_manager)
        self.user_service = UserService()
        self.keyboards = BotKeyboards()
        self.formatters = BotFormatters()
        self.validators = BotValidators()
    
    # ===============================
    # TICKET CONVERSATION HANDLERS
    # ===============================
    
    async def new_ticket_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Bắt đầu tạo ticket mới"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Initialize user data
        self.user_service.init_user_data(user, chat_id)
        
        # Show destination selection
        keyboard = self.keyboards.get_destination_keyboard()
        message = self.formatters.format_destination_selection()
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        return WAITING_DESTINATION
    
    async def destination_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý callback chọn destination"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Get destination from callback
        destination = self.user_service.get_destination_from_callback(query.data)
        self.user_service.update_user_data(user_id, 'destination', destination)
        
        # Format and send confirmation message
        message = self.formatters.format_destination_selected(destination)
        await query.edit_message_text(message, parse_mode='Markdown')
        
        return WAITING_DESCRIPTION
    
    async def description_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý tin nhắn mô tả"""
        user_id = update.effective_user.id
        description = update.message.text.strip()
        
        # Validate description
        is_valid, error_message = self.validators.validate_description(description)
        if not is_valid:
            await update.message.reply_text(error_message)
            return WAITING_DESCRIPTION
        
        # Save description
        self.user_service.update_user_data(user_id, 'description', description)
        
        # Show priority selection
        keyboard = self.keyboards.get_priority_keyboard()
        message = self.formatters.format_priority_selection()
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        return WAITING_PRIORITY
    
    async def priority_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý callback chọn độ ưu tiên"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Get priority info
        priority_code, priority_text = self.ticket_service.get_priority_info(query.data)
        self.user_service.update_user_data(user_id, 'priority', priority_code)
        
        # Get user data for confirmation
        user_data = self.user_service.get_user_data(user_id)
        
        # Format confirmation message
        confirmation_text = self.formatters.format_ticket_confirmation(user_data, priority_text)
        keyboard = self.keyboards.get_confirmation_keyboard()
        
        await query.edit_message_text(
            confirmation_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        return WAITING_PRIORITY
    
    async def confirm_ticket_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý xác nhận tạo ticket"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "cancel_ticket":
            await query.edit_message_text("❌ Đã hủy tạo ticket.")
            self.user_service.clear_user_data(user_id)
            return ConversationHandler.END
        
        if query.data == "confirm_ticket":
            try:
                # Get and validate user data
                user_data = self.user_service.get_user_data(user_id)
                is_valid, error_message = self.ticket_service.validate_ticket_data(user_data)
                
                if not is_valid:
                    await query.edit_message_text(error_message)
                    self.user_service.clear_user_data(user_id)
                    return ConversationHandler.END
                
                # Create ticket
                destination = user_data.get('destination', 'Vietnam')
                result = await self.ticket_service.create_ticket(user_data, destination)
                
                # Format response message
                if result['success']:
                    message = self.formatters.format_ticket_success(result, user_data)
                    logger.info(f"Ticket created successfully for user {user_id}")
                else:
                    message = self.formatters.format_ticket_error(result.get('message', 'Unknown error'))
                    logger.error(f"Failed to create ticket for user {user_id}")
                
                await query.edit_message_text(message, parse_mode='Markdown')
                
                # Clear user data
                self.user_service.clear_user_data(user_id)
                
            except Exception as e:
                logger.error(f"Exception creating ticket for user {user_id}: {e}")
                await query.edit_message_text(
                    "❌ Có lỗi xảy ra khi tạo ticket. Vui lòng thử lại sau."
                )
                self.user_service.clear_user_data(user_id)
        
        return ConversationHandler.END
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Hủy tạo ticket"""
        user_id = update.effective_user.id
        self.user_service.clear_user_data(user_id)
        
        await update.message.reply_text("❌ Đã hủy tạo ticket.")
        return ConversationHandler.END
    
    async def my_tickets_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xem tickets của user"""
        try:
            chat_id = str(update.effective_chat.id)
            tickets = await self.ticket_service.get_user_tickets(chat_id)
            
            message = self.formatters.format_tickets_list(tickets)
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting tickets for user: {e}")
            await update.message.reply_text(
                "❌ Có lỗi xảy ra khi lấy danh sách tickets. Vui lòng thử lại sau."
            )
    
    # ===============================
    # BOT SETUP AND MANAGEMENT
    # ===============================
    
    def setup_handlers(self):
        """Thiết lập các handler cho bot"""
        if not self.application:
            logger.error("Application chưa được khởi tạo")
            return
        
        # Conversation handler cho tạo ticket
        conversation_handler = ConversationHandler(
            entry_points=[CommandHandler('newticket', self.new_ticket_command)],
            states={
                WAITING_DESTINATION: [
                    CallbackQueryHandler(self.destination_callback, pattern='^dest_')
                ],
                WAITING_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.description_handler)
                ],
                WAITING_PRIORITY: [
                    CallbackQueryHandler(self.priority_callback, pattern='^priority_'),
                    CallbackQueryHandler(self.confirm_ticket_callback, pattern='^(confirm|cancel)_ticket$')
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel_command),
                CommandHandler('start', self.start_handler.start_command)
            ]
        )
        
        # Add all handlers
        self.application.add_handler(conversation_handler)
        self.application.add_handler(CommandHandler('start', self.start_handler.start_command))
        self.application.add_handler(CommandHandler('help', self.start_handler.help_command))
        self.application.add_handler(CommandHandler('menu', self.start_handler.menu_command))
        self.application.add_handler(CommandHandler('mytickets', self.my_tickets_command))
        
        logger.info("Đã setup handlers cho Telegram Bot")
    
    async def initialize(self) -> None:
        """Khởi tạo bot"""
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        logger.info("Telegram Bot đã được khởi tạo")
    
    async def start_polling(self) -> None:
        """Bắt đầu polling - Sử dụng threading để tránh event loop conflict"""
        if not self.application:
            await self.initialize()
        
        logger.info("Bắt đầu Telegram Bot polling...")
        
        def run_bot():
            """Run bot in separate thread"""
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.application.run_polling(drop_pending_updates=True)
                )
            except Exception as e:
                logger.error(f"Bot polling error: {e}")
            finally:
                loop.close()
        
        # Start bot in separate thread
        self.bot_thread = threading.Thread(target=run_bot, daemon=False)
        self.bot_thread.start()
        logger.info("Telegram Bot polling started successfully")
        
        # Keep function running
        self.running = True
        while self.running and hasattr(self, 'bot_thread') and self.bot_thread.is_alive():
            await asyncio.sleep(1)
    
    async def stop(self) -> None:
        """Dừng bot"""
        if self.application:
            logger.info("Đang dừng Telegram Bot...")
            try:
                self.running = False
                self.application.stop()
                
                if hasattr(self, 'bot_thread') and self.bot_thread.is_alive():
                    self.bot_thread.join(timeout=5)
                    
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
            logger.info("Telegram Bot đã dừng")