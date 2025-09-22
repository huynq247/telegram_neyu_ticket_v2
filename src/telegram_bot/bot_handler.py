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
from .handlers.menu_handler import MenuHandler
from .handlers.ticket_creation_handler import TicketCreationHandler, WAITING_DESTINATION, WAITING_DESCRIPTION, WAITING_PRIORITY
from .services.ticket_service import TicketService
from .services.user_service import UserService
from .services.auth_service import OdooAuthService
from .handlers.auth_handler import AuthHandler
from .utils.keyboards import BotKeyboards
from .utils.formatters import BotFormatters
from .utils.validators import BotValidators

logger = logging.getLogger(__name__)

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
        
        # Initialize authentication service with XML-RPC URL
        self.auth_service = OdooAuthService(odoo_config['xmlrpc_url'], odoo_config['database'])
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
        
        # Initialize menu handler
        self.menu_handler = MenuHandler(
            self.auth_service,
            self.keyboards,
            self.formatters,
            self.user_service
        )
        
        # Initialize ticket creation handler
        self.ticket_creation_handler = TicketCreationHandler(
            self.auth_service,
            self.keyboards,
            self.formatters,
            self.user_service,
            self.ticket_service
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
                parse_mode='HTML'
            )
        else:
            # User needs to login
            welcome_message = (
                f"👋 Welcome to *Neyu Ticket Bot*, {user.first_name}!\n\n"
                "🔐 Please login with your Odoo account to access ticket features.\n\n"
                "Available commands:\n"
                "• /login - Login with your Odoo account\n"
                "• /help - Show all available commands\n"
                "• Just type 'hi' or 'hello' to show this menu again\n\n"
                "💡 *Note:* You need to authenticate before creating or managing tickets."
            )
            
            keyboard = self.keyboards.get_login_keyboard()
            await update.message.reply_text(
                welcome_message, 
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
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
                "• /login - Login with your Odoo account\n"
                "  └ Step-by-step or quick login (`email:password`)\n\n"
                
                "ℹ️ *General:*\n"
                "• /help - Show this help message\n"
                "• /start - Show welcome message\n"
                "• Just type 'hi' or 'hello' - Same as /start\n\n"
                
                "⚡ *Quick Login Tip:*\n"
                "Use format `email:password` for faster authentication!\n\n"
                
                "💡 *Note:* You need to login before accessing ticket features."
            )
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
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
            parse_mode='HTML'
        )
    

    

    

    

    

        
        return ConversationHandler.END
    
    # ===============================
    # TICKET CONVERSATION HANDLERS
    # ===============================

    
# Old my_tickets_command removed - now handled by ViewTicketHandler
    
    async def cancel_auth_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel authentication process"""
        await update.message.reply_text(
            "🚫 Authentication cancelled. Use /login to try again."
        )
        return ConversationHandler.END
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "show_help":
            # Show help
            await self.help_command(update, context)
        elif query.data == "back_to_menu":
            # Return to start menu
            await self.start_command(update, context)
    
    # ===============================
    # BOT SETUP AND MANAGEMENT
    # ===============================
    
    def setup_handlers(self):
        """Thiết lập các handler cho bot"""
        if not self.application:
            logger.error("Application chưa được khởi tạo")
            return
        
        # Conversation handler cho tạo ticket - using ticket creation handler
        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler('newticket', self.ticket_creation_handler.new_ticket_command),
                CallbackQueryHandler(self.ticket_creation_handler.handle_new_ticket_callback, pattern='^menu_new_ticket$')
            ],
            states={
                WAITING_DESTINATION: [
                    CallbackQueryHandler(self.ticket_creation_handler.destination_callback, pattern='^dest_'),
                    CallbackQueryHandler(self.menu_handler.handle_back_to_menu_callback, pattern='^back_to_menu$')
                ],
                WAITING_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.ticket_creation_handler.description_handler)
                ],
                WAITING_PRIORITY: [
                    CallbackQueryHandler(self.ticket_creation_handler.priority_callback, pattern='^priority_'),
                    CallbackQueryHandler(self.ticket_creation_handler.confirm_ticket_callback, pattern='^(confirm|cancel)_ticket$')
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.ticket_creation_handler.cancel_command),
                CommandHandler('menu', self.menu_command),
                CommandHandler('start', self.start_command)
            ]
        )
        
        # Authentication conversation handler
        auth_conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler('login', self.auth_handler.login_command),
                CallbackQueryHandler(self.auth_handler.login_command, pattern='^start_login$')
            ],
            states={
                WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.receive_email)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.receive_password)],
            },
            fallbacks=[
                CommandHandler('cancel', self.auth_handler.cancel_auth_command),
                CommandHandler('menu', self.menu_command),
                CommandHandler('start', self.start_command)
            ]
        )

        # View tickets conversation handler
        view_tickets_conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler('mytickets', self.view_ticket_handler.view_tickets_command),
                CallbackQueryHandler(self.view_ticket_handler.view_tickets_command, pattern='^menu_my_tickets$'),
                MessageHandler(filters.Regex(r'^/detail_\d+$'), self.view_ticket_handler.handle_ticket_detail_command)
            ],
            states={
                self.view_ticket_handler.VIEWING_LIST: [
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^(view_page_\d+|view_page_info|view_search|view_back_to_list|back_to_menu)$'),
                    CallbackQueryHandler(self.view_ticket_handler.handle_view_comments,
                                       pattern='^view_comments$'),
                    MessageHandler(filters.Regex(r'^/detail_\d+$'), self.view_ticket_handler.handle_ticket_detail_command)
                ],
                self.view_ticket_handler.SEARCHING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.view_ticket_handler.handle_search_input),
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^view_back_to_list$'),
                ],
                self.view_ticket_handler.VIEWING_DETAIL: [
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^view_back_to_list$'),
                    MessageHandler(filters.Regex(r'^/detail_\d+$'), self.view_ticket_handler.handle_ticket_detail_command)
                ],
                self.view_ticket_handler.WAITING_TICKET_NUMBER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.view_ticket_handler.handle_ticket_number_input),
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^back_to_tickets$'),
                ],
                self.view_ticket_handler.VIEWING_COMMENTS: [
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^(back_to_tickets|back_to_comments)$'),
                    CallbackQueryHandler(self.view_ticket_handler.handle_add_comment,
                                       pattern='^add_comment$'),
                ],
                self.view_ticket_handler.WAITING_ADD_COMMENT_TICKET: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.view_ticket_handler.handle_add_comment_ticket_input),
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^back_to_tickets$'),
                ],
                self.view_ticket_handler.WAITING_COMMENT_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.view_ticket_handler.handle_comment_text_input),
                    CallbackQueryHandler(self.view_ticket_handler.handle_ticket_list_callback, 
                                       pattern='^(back_to_tickets|back_to_comments)$'),
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.view_ticket_handler.cancel_view),
                CommandHandler('menu', self.menu_command),
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
        
        # Add "hi" message handler - works like /start
        self.application.add_handler(MessageHandler(filters.Regex(r'^(hi|Hi|HI|hello|Hello|HELLO|xin chào|chào)$'), self.start_command))
        
        # Add fallback handler for detail commands
        self.application.add_handler(
            MessageHandler(filters.Regex(r'^/detail_\d+$'), self.view_ticket_handler.handle_ticket_detail_command)
        )
        
        # Add callback query handlers for welcome screen help button only (start_login handled by auth conversation)
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern='^show_help$'))
        
        # Add callback query handlers for menu buttons (excluding menu_my_tickets and menu_new_ticket - handled by conversations)
        self.application.add_handler(CallbackQueryHandler(self.menu_handler.handle_menu_callback, pattern='^menu_(help|logout)$'))
        
        # Add global handler for back_to_menu (fallback when not in conversation)
        self.application.add_handler(CallbackQueryHandler(self.menu_handler.handle_back_to_menu_callback, pattern='^back_to_menu$'))
        
        logger.info("Đã setup handlers cho Telegram Bot")
    
    async def initialize(self) -> None:
        """Khởi tạo bot"""
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        logger.info("Telegram Bot đã được khởi tạo")
    
    async def start_polling(self) -> None:
        """Bắt đầu polling - Manual lifecycle management"""
        if not self.application:
            await self.initialize()
        
        logger.info("Bắt đầu Telegram Bot polling...")
        
        try:
            self.running = True
            
            # Manual lifecycle management to avoid event loop conflicts
            async with self.application:
                await self.application.start()
                await self.application.updater.start_polling(drop_pending_updates=True)
                
                # Keep running until stopped
                while self.running:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            # Don't re-raise to allow graceful shutdown
        finally:
            self.running = False
            logger.info("Bot polling stopped")
    
    async def stop(self) -> None:
        """Dừng bot"""
        logger.info("Đang dừng Telegram Bot...")
        try:
            self.running = False
            
            # Stop updater if running
            if self.application and hasattr(self.application, 'updater'):
                if self.application.updater.running:
                    await self.application.updater.stop()
                    
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
        logger.info("Telegram Bot đã dừng")