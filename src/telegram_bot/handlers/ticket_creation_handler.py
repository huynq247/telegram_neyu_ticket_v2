"""
Ticket Creation Handler Module
Handles the complete ticket creation conversation flow
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.telegram_bot.utils.formatters import BotFormatters
from src.telegram_bot.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

# States
WAITING_DESTINATION = 0
WAITING_TITLE = 1
WAITING_DESCRIPTION = 2
WAITING_PRIORITY = 3

class TicketCreationHandler:
    """Handler for ticket creation conversation flow"""
    
    def __init__(self, auth_service, keyboards, formatters, user_service, ticket_service):
        """
        Initialize ticket creation handler
        
        Args:
            auth_service: Authentication service
            keyboards: Bot keyboards utility
            formatters: Bot formatters utility
            user_service: User service
            ticket_service: Ticket service
        """
        self.auth_service = auth_service
        self.keyboards = keyboards
        self.formatters = formatters
        self.user_service = user_service
        self.ticket_service = ticket_service
    
    async def new_ticket_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Bắt đầu tạo ticket mới"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Check authentication
        if not self.auth_service.is_authenticated(user.id):
            await update.message.reply_text(
                "🔒 You need to login first to create tickets.\n"
                "Use /login to authenticate.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Initialize user data
        self.user_service.init_user_data(user, chat_id)
        
        # Show destination selection
        keyboard = self.keyboards.get_destination_keyboard()
        message = BotFormatters.format_destination_selection()
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return WAITING_DESTINATION
    
    async def handle_new_ticket_callback(self, update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle new ticket creation from menu button"""
        # When called from conversation handler, update is Update object
        # When called from menu callback, update is Update object with callback_query
        query = update.callback_query
        user = query.from_user
        chat_id = query.message.chat_id
        
        logger.info(f"handle_new_ticket_callback: user_id={user.id}, callback_data={query.data}")
        
        # Check authentication
        if not self.auth_service.is_authenticated(user.id):
            await query.edit_message_text(
                "🔒 You need to login first to create tickets.\n"
                "Use /login to authenticate.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Initialize user data
        self.user_service.init_user_data(user, chat_id)
        
        # Show destination selection
        keyboard = self.keyboards.get_destination_keyboard()
        message = BotFormatters.format_destination_selection()

        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return WAITING_DESTINATION
    
    async def destination_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý callback chọn destination"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        destination = query.data.replace('dest_', '')
        
        logger.info(f"destination_callback: user_id={user_id}, destination={destination}, callback_data={query.data}")
        
        # Store destination
        self.user_service.update_user_data(user_id, 'destination', destination)
        
        # Request title (new step)
        try:
            message = BotFormatters.format_title_request(destination)
            logger.info(f"Formatted title request message for destination: {destination}")
            
            await query.edit_message_text(message, parse_mode='HTML')
            logger.info(f"Successfully sent title request to user {user_id}")
            
            return WAITING_TITLE
        except Exception as e:
            logger.error(f"Error in destination_callback for user {user_id}: {e}", exc_info=True)
            return await ErrorHandler.handle_error_with_menu(
                update, context, e, "chọn destination",
                self.keyboards, self.auth_service
            )
    
    async def title_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý tin nhắn title"""
        try:
            user_id = update.effective_user.id
            title = update.message.text
            
            # Store title
            self.user_service.update_user_data(user_id, 'title', title)
            
            # Get destination for next message
            user_data = self.user_service.get_user_data(user_id)
            destination = user_data.get('destination', 'Vietnam')
            
            # Request description
            message = BotFormatters.format_description_request(destination)
            
            await update.message.reply_text(
                message,
                parse_mode='HTML'
            )
            
            return WAITING_DESCRIPTION
        except Exception as e:
            logger.error(f"Error in title_handler: {e}", exc_info=True)
            return await ErrorHandler.handle_error_with_menu(
                update, context, e, "xử lý title",
                self.keyboards, self.auth_service
            )
    
    async def description_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý tin nhắn mô tả"""
        try:
            user_id = update.effective_user.id
            description = update.message.text
            
            # Store description
            self.user_service.update_user_data(user_id, 'description', description)
            
            # Request priority
            keyboard = self.keyboards.get_priority_keyboard()
            message = BotFormatters.format_priority_selection()
            
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return WAITING_PRIORITY
        except Exception as e:
            logger.error(f"Error in description_handler: {e}", exc_info=True)
            return await ErrorHandler.handle_error_with_menu(
                update, context, e, "xử lý description",
                self.keyboards, self.auth_service
            )
    
    async def priority_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý callback chọn priority"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            priority_callback = query.data
            
            # Get priority info
            priority_code, priority_text = self.ticket_service.get_priority_info(priority_callback)
            
            # Store priority
            self.user_service.update_user_data(user_id, 'priority', priority_code)
            user_data = self.user_service.get_user_data(user_id)
            
            # Show confirmation
            keyboard = self.keyboards.get_confirmation_keyboard()
            message = BotFormatters.format_ticket_confirmation(user_data, priority_text)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return WAITING_PRIORITY
        except Exception as e:
            logger.error(f"Error in priority_callback: {e}", exc_info=True)
            return await ErrorHandler.handle_error_with_menu(
                update, context, e, "chọn priority",
                self.keyboards, self.auth_service
            )
    
    async def confirm_ticket_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý xác nhận tạo ticket"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "cancel_ticket":
            await query.edit_message_text("❌ Đã hủy tạo ticket.")
            self.user_service.clear_user_data(user_id)
            
            # Auto redirect to menu after cancel
            is_valid, user_data = self.auth_service.validate_session(user_id)
            if is_valid:
                keyboard = self.keyboards.get_main_menu_keyboard()
                menu_text = (
                    f"🏠 <b>Main Menu</b>\n\n"
                    f"👤 Logged in as: <b>{user_data['name']}</b>\n"
                    f"📧 Email: {user_data['email']}\n\n"
                    "Choose an option below:"
                )
                await query.message.reply_text(menu_text, reply_markup=keyboard, parse_mode='HTML')
            
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
                    message = BotFormatters.format_ticket_success(result, user_data)
                    keyboard = self.keyboards.get_back_to_menu_keyboard()
                    logger.info(f"Ticket created successfully for user {user_id}")
                    await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
                else:
                    message = BotFormatters.format_ticket_error(result.get('message', 'Unknown error'))
                    logger.error(f"Failed to create ticket for user {user_id}")
                    await query.edit_message_text(message, parse_mode='HTML')
                
                # Clear user data
                self.user_service.clear_user_data(user_id)
                
            except Exception as e:
                logger.error(f"Exception creating ticket for user {user_id}: {e}", exc_info=True)
                self.user_service.clear_user_data(user_id)
                
                # Send error message and redirect to menu
                await ErrorHandler.send_menu_after_error(
                    update, self.keyboards, self.auth_service,
                    "❌ <b>Có lỗi xảy ra khi tạo ticket</b>\n\n"
                    "Vui lòng thử lại sau hoặc liên hệ admin nếu lỗi tiếp diễn.\n\n"
                )
        
        return ConversationHandler.END
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Hủy tạo ticket"""
        user_id = update.effective_user.id
        self.user_service.clear_user_data(user_id)
        
        await update.message.reply_text("❌ Đã hủy tạo ticket.")
        
        # Auto redirect to menu after cancel
        is_valid, user_data = self.auth_service.validate_session(user_id)
        if is_valid:
            keyboard = self.keyboards.get_main_menu_keyboard()
            menu_text = (
                f"🏠 <b>Main Menu</b>\n\n"
                f"👤 Logged in as: <b>{user_data['name']}</b>\n"
                f"📧 Email: {user_data['email']}\n\n"
                "Choose an option below:"
            )
            await update.message.reply_text(menu_text, reply_markup=keyboard, parse_mode='HTML')
        
        return ConversationHandler.END
