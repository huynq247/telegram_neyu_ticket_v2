"""
Menu Handler Module
Handles all menu-related functionality including menu callbacks, help, logout, and navigation
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class MenuHandler:
    """Handler for menu-related functionality"""
    
    def __init__(self, auth_service, keyboards, formatters, user_service):
        """
        Initialize menu handler
        
        Args:
            auth_service: Authentication service
            keyboards: Bot keyboards utility
            formatters: Bot formatters utility  
            user_service: User service
        """
        self.auth_service = auth_service
        self.keyboards = keyboards
        self.formatters = formatters
        self.user_service = user_service
    
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
        
        # Handle different menu options - menu_new_ticket and menu_my_tickets handled by conversations
        if callback_data == "menu_help":
            await self.handle_help_callback(query, context)
        elif callback_data == "menu_logout":
            await self.handle_logout_callback(query, context)
        else:
            await query.edit_message_text("❓ Unknown menu option.")
    

    
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
        
        await query.edit_message_text(help_text, parse_mode='HTML')
    
    async def handle_logout_callback(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle logout callback from menu"""
        user = query.from_user
        
        # Check if user is logged in
        is_valid, user_data = self.auth_service.validate_session(user.id)
        
        if not is_valid:
            await query.edit_message_text(
                "ℹ️ You are not currently logged in.\n"
                "Use /login to authenticate."
            )
            return
        
        # Revoke session
        success = self.auth_service.revoke_session(user.id)
        
        if success:
            await query.edit_message_text(
                f"✅ Successfully logged out.\n\n"
                f"Goodbye, *{user_data['name']}*!\n\n"
                "Use /login to authenticate again.",
                parse_mode='HTML'
            )
            logger.info(f"User {user.id} ({user_data['email']}) logged out from menu")
        else:
            await query.edit_message_text("❌ Error during logout. Please try again.")
    
    async def handle_back_to_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle back to menu callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Clear user data when going back to menu
        self.user_service.clear_user_data(user_id)
        
        # Check authentication
        is_valid, user_data = self.auth_service.validate_session(user_id)
        
        if is_valid:
            keyboard = self.keyboards.get_main_menu_keyboard()
            menu_text = (
                f"🏠 <b>Main Menu</b>\n\n"
                f"👤 Logged in as: <b>{user_data['name']}</b>\n"
                f"📧 Email: {user_data['email']}\n\n"
                "Choose an option below:"
            )
            await query.edit_message_text(
                menu_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                "🔐 Your session has expired. Please use /login to authenticate again."
            )
        
        from telegram.ext import ConversationHandler
        return ConversationHandler.END