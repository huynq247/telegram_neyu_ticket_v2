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
from .handlers.view_ticket_handler import ViewTicketHandler
from .services.ticket_service import TicketService
from .services.user_service import UserService
from .services.auth_service import OdooAuthService
from .handlers.auth_handler import AuthHandler
from .utils.keyboards import BotKeyboards
from .utils.formatters import BotFormatters
from .utils.validators import BotValidators

logger = logging.getLogger(__name__)

# States cho conversation
WAITING_DESTINATION, WAITING_DESCRIPTION, WAITING_PRIORITY = range(3)
# Authentication states
WAITING_EMAIL, WAITING_PASSWORD = range(1, 3)

class TelegramBotHandler:
    """Main Bot Handler - Modular Version"""
    
    def __init__(self, token: str, ticket_manager, odoo_config: dict):
        """
        Khởi tạo Bot Handler with Authentication
        
        Args:
            token: Telegram Bot Token
            ticket_manager: Instance của TicketManager
            odoo_config: Odoo configuration for authentication
        """
        self.token = token
        self.ticket_manager = ticket_manager
        self.application = None
        self.running = False
        
        # Initialize authentication service
        odoo_url = f"http://{odoo_config['host']}:{odoo_config['port']}"
        self.auth_service = OdooAuthService(odoo_url, odoo_config['database'])
        self.auth_handler = AuthHandler(self.auth_service)
        
        # Initialize modules
        self.start_handler = StartHandler()
        self.ticket_service = TicketService(ticket_manager)
        self.user_service = UserService()
        self.keyboards = BotKeyboards()
        self.formatters = BotFormatters()
        self.validators = BotValidators()
        
        # Initialize view ticket handler
        self.view_ticket_handler = ViewTicketHandler(
            self.ticket_service, 
            self.formatters, 
            self.keyboards, 
            self.auth_service
        )
    
    # ===============================
    # AUTHENTICATION-AWARE COMMANDS
    # ===============================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command with authentication awareness"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"User {user.username} ({user_id}) started the bot")
        
        # Check if user is authenticated
        is_valid, user_data = self.auth_service.validate_session(user_id)
        
        if is_valid:
            # User is authenticated - show main menu
            welcome_message = (
                f"👋 Welcome back, *{user_data['name']}*!\n\n"
                f"📧 {user_data['email']}\n"
                f"🔐 You are logged in\n\n"
                "Choose an option below:"
            )
            
            keyboard = self.keyboards.get_main_menu_keyboard()
            await update.message.reply_text(
                welcome_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            # User needs to login
            welcome_message = (
                f"👋 Welcome to *Neyu Ticket Bot*, {user.first_name}!\n\n"
                "🔐 Please login with your Odoo account to access ticket features.\n\n"
                "Available commands:\n"
                "• /login - Login with your Odoo account\n"
                "• /help - Show all available commands\n\n"
                "💡 *Note:* You need to authenticate before creating or managing tickets."
            )
            
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command with authentication awareness"""
        user_id = update.effective_user.id
        is_valid, user_data = self.auth_service.validate_session(user_id)
        
        if is_valid:
            # Authenticated user help
            help_text = (
                "🤖 *Neyu Ticket Bot - Available Commands*\n\n"
                
                "🎫 *Ticket Commands:*\n"
                "• /menu - Show main menu\n"
                "• /newticket - Create a new ticket\n"
                "• /mytickets - View your tickets\n\n"
                
                "🔐 *Account:*\n"
                "• /logout - Logout from your account\n\n"
                
                "ℹ️ *General:*\n"
                "• /help - Show this help message\n"
                "• /cancel - Cancel current operation\n\n"
                
                f"👤 Logged in as: *{user_data['name']}*"
            )
        else:
            # Non-authenticated user help
            help_text = (
                "🤖 *Neyu Ticket Bot - Available Commands*\n\n"
                
                "🔐 *Authentication:*\n"
                "• /login - Login with your Odoo account\n\n"
                
                "ℹ️ *General:*\n"
                "• /help - Show this help message\n"
                "• /start - Show welcome message\n\n"
                
                "💡 *Note:* You need to login before accessing ticket features."
            )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /menu command - requires authentication"""
        user_id = update.effective_user.id
        
        # Check authentication
        is_valid, user_data = self.auth_service.validate_session(user_id)
        
        if not is_valid:
            await update.message.reply_text(
                "🔐 You need to login first. Use /login to authenticate with your Odoo account."
            )
            return
        
        # Show authenticated menu
        keyboard = self.keyboards.get_main_menu_keyboard()
        
        menu_text = (
            f"🏠 *Main Menu*\n\n"
            f"👤 Logged in as: *{user_data['name']}*\n"
            f"📧 Email: {user_data['email']}\n\n"
            "Choose an option below:"
        )
        
        await update.message.reply_text(
            menu_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle menu button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        callback_data = query.data
        
        # Check authentication for all menu actions
        is_valid, user_data = self.auth_service.validate_session(user_id)
        
        if not is_valid:
            await query.edit_message_text(
                "🔐 Your session has expired. Please use /login to authenticate again."
            )
            return
        
        logger.info(f"Menu callback: {callback_data} from user {user_id}")
        
        # Handle different menu options
        if callback_data == "menu_new_ticket":
            await self.handle_new_ticket_callback(query, context)
        elif callback_data == "menu_my_tickets":
            await self.handle_my_tickets_callback(query, context)
        elif callback_data == "menu_help":
            await self.handle_help_callback(query, context)
        else:
            await query.edit_message_text("❓ Unknown menu option.")
    
    async def handle_new_ticket_callback(self, update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle new ticket creation from menu button"""
        if hasattr(update, 'callback_query'):
            query = update.callback_query
            user = query.from_user
            chat_id = query.message.chat_id
            
            # Initialize user data
            self.user_service.init_user_data(user, chat_id)
            
            # Show destination selection
            keyboard = self.keyboards.get_destination_keyboard()
            message = self.formatters.format_destination_selection()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            return WAITING_DESTINATION
        else:
            # Called from command, use original logic
            return await self.new_ticket_command(update, context)
    
    async def handle_my_tickets_callback(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle my tickets callback - call the same function as /mytickets command"""
        try:
            # Create update with callback query - copy from original update
            fake_update = Update(
                update_id=0, 
                callback_query=query,
                effective_user=query.from_user,
                effective_chat=query.message.chat
            )
            
            # Call the exact same handler as /mytickets command
            await self.view_ticket_handler.view_tickets_command(fake_update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_my_tickets_callback: {e}")
            await query.edit_message_text(
                "❌ Error occurred while loading tickets."
            )
    
    async def handle_view_tickets_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle view tickets callback from menu"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Check authentication
        if not self.view_ticket_handler._is_authenticated(user_id):
            await query.edit_message_text(
                "🔒 You need to login first. Use /login to authenticate.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        try:
            chat_id = str(query.message.chat_id)
            
            # Get paginated tickets - use user_id and auth_service
            pagination_data = await self.ticket_service.get_paginated_tickets(user_id, self.auth_service, page=1, per_page=5)
            
            # Format message
            message = self.formatters.format_paginated_tickets(pagination_data)
            
            # Get keyboard
            keyboard = self.keyboards.get_ticket_list_keyboard(
                current_page=pagination_data.get('current_page', 1),
                total_pages=pagination_data.get('total_pages', 1),
                has_tickets=len(pagination_data.get('tickets', [])) > 0
            )
            
            # Update user state
            user_state = self.view_ticket_handler._get_user_state(user_id)
            user_state['current_page'] = 1
            user_state['last_tickets'] = pagination_data.get('tickets', [])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            return self.view_ticket_handler.VIEWING_LIST
            
        except Exception as e:
            logger.error(f"Error in handle_view_tickets_callback: {e}")
            await query.edit_message_text("❌ Error occurred while loading tickets.")
            return ConversationHandler.END
    
    async def handle_help_callback(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle help callback"""
        user_id = query.from_user.id
        is_valid, user_data = self.auth_service.validate_session(user_id)
        
        if is_valid:
            help_text = (
                "🤖 *Neyu Ticket Bot Help*\n\n"
                
                "🎫 *Ticket Features:*\n"
                "• Create tickets for 6 countries\n"
                "• Set priority levels (Low, Medium, High)\n"
                "• Track your ticket status\n\n"
                
                "💡 *Tips:*\n"
                "• Provide clear descriptions for faster resolution\n"
                "• Use appropriate priority levels\n\n"
                
                f"👤 Logged in as: *{user_data['name']}*"
            )
        else:
            help_text = (
                "🤖 *Neyu Ticket Bot Help*\n\n"
                
                "🔐 *Authentication Required*\n"
                "Please use /login to access ticket features.\n\n"
                
                "💡 *Available Commands:*\n"
                "• /login - Login with Odoo account\n"
                "• /help - Show this help message"
            )
        
        await query.edit_message_text(help_text, parse_mode='Markdown')
    
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
                result = await self.ticket_service.create_ticket(user_data, destination, user_id, self.auth_service)
                
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
    
# Old my_tickets_command removed - now handled by ViewTicketHandler
    
    async def cancel_auth_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel authentication process"""
        await update.message.reply_text(
            "🚫 Authentication cancelled. Use /login to try again."
        )
        return ConversationHandler.END
    
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
            entry_points=[
                CommandHandler('newticket', self.new_ticket_command),
                CallbackQueryHandler(self.handle_new_ticket_callback, pattern='^menu_new_ticket$')
            ],
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
                CommandHandler('start', self.start_command)
            ]
        )
        
        # Authentication conversation handler
        auth_conversation_handler = ConversationHandler(
            entry_points=[CommandHandler('login', self.auth_handler.login_command)],
            states={
                WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.receive_email)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.receive_password)],
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel_auth_command),
                CommandHandler('start', self.start_handler.start_command)
            ]
        )

        # View tickets conversation handler
        view_tickets_conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler('mytickets', self.view_ticket_handler.view_tickets_command),
                CallbackQueryHandler(self.handle_view_tickets_callback, pattern='^menu_my_tickets$'),
                MessageHandler(filters.Regex(r'^/detail_\d+$'), self.view_ticket_handler.handle_ticket_detail_command)
            ],
            states={
                self.view_ticket_handler.VIEWING_LIST: [
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^(view_page_|view_filter_|view_search|back_to_menu)'),
                ],
                self.view_ticket_handler.FILTERING: [
                    CallbackQueryHandler(self.view_ticket_handler.handle_filter_callback, 
                                       pattern='^(filter_|view_back_to_list)'),
                ],
                self.view_ticket_handler.SEARCHING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.view_ticket_handler.handle_search_input),
                ],
                self.view_ticket_handler.VIEWING_DETAIL: [
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^view_back_to_list$'),
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.view_ticket_handler.cancel_view),
                CommandHandler('start', self.start_command)
            ]
        )

        # Add all handlers
        self.application.add_handler(auth_conversation_handler)
        self.application.add_handler(view_tickets_conversation_handler)
        self.application.add_handler(conversation_handler)
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('menu', self.menu_command))
        self.application.add_handler(CommandHandler('logout', self.auth_handler.logout_command))
        
        # Add callback query handlers for menu buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_callback, pattern='^menu_(help)$'))
        
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