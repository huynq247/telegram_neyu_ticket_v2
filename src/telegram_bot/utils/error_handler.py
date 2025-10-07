"""
Error Handler Utility
Centralized error handling with menu redirect
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Utility class for handling errors and redirecting to menu"""
    
    @staticmethod
    async def handle_error_with_menu(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception,
        error_context: str,
        keyboards = None,
        auth_service = None
    ) -> int:
        """
        Handle error and show menu to user
        
        Args:
            update: Telegram update
            context: Telegram context
            error: Exception that occurred
            error_context: Context description (e.g., "creating ticket")
            keyboards: Bot keyboards utility (optional)
            auth_service: Auth service (optional)
            
        Returns:
            ConversationHandler.END
        """
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        
        # Log the error
        logger.error(f"Error {error_context} for user {user_id}: {error}", exc_info=True)
        
        # Error message
        error_message = (
            f"❌ <b>Có lỗi xảy ra</b>\n\n"
            f"Đã xảy ra lỗi khi {error_context}.\n"
            f"Vui lòng thử lại sau hoặc liên hệ admin nếu lỗi tiếp diễn.\n\n"
            f"🏠 Quay lại menu chính để tiếp tục."
        )
        
        try:
            # Get keyboard if available
            keyboard = None
            if keyboards and auth_service:
                is_valid, user_data = auth_service.validate_session(user_id)
                if is_valid:
                    keyboard = keyboards.get_main_menu_keyboard()
            
            # Send error message with or without keyboard
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    error_message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            elif update.message:
                await update.message.reply_text(
                    error_message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        except Exception as send_error:
            logger.error(f"Error sending error message: {send_error}")
            # Fallback: try to send simple message
            try:
                if update.message:
                    await update.message.reply_text(
                        "❌ Có lỗi xảy ra. Vui lòng sử dụng /menu để quay lại.",
                        parse_mode='HTML'
                    )
            except:
                pass
        
        return ConversationHandler.END
    
    @staticmethod
    async def send_menu_after_error(
        update: Update,
        keyboards,
        auth_service,
        error_message: str = None
    ) -> None:
        """
        Send menu to user after handling error
        
        Args:
            update: Telegram update
            keyboards: Bot keyboards utility
            auth_service: Auth service
            error_message: Optional custom error message
        """
        user_id = update.effective_user.id
        
        # Default error message
        if not error_message:
            error_message = (
                "❌ <b>Có lỗi xảy ra</b>\n\n"
                "Đã xảy ra lỗi khi xử lý yêu cầu của bạn.\n"
                "Vui lòng thử lại sau.\n\n"
            )
        
        # Get user info and menu
        is_valid, user_data = auth_service.validate_session(user_id)
        
        if is_valid:
            keyboard = keyboards.get_main_menu_keyboard()
            user_type = user_data.get('user_type', 'unknown')
            type_display = ""
            
            if user_type == 'admin_helpdesk':
                type_display = "Admin"
            elif user_type == 'portal_user':
                type_display = "Portal User"
            else:
                type_display = "User"
            
            menu_text = (
                f"{error_message}"
                f"🏠 <b>Main Menu</b>\n\n"
                f"👤 Logged in as: <b>{user_data['name']}</b>\n"
                f"📧 Email: {user_data['email']}\n"
                f"🔑 Type: <b>{type_display}</b>\n\n"
                "Choose an option below:"
            )
            
            try:
                if update.callback_query:
                    await update.callback_query.message.reply_text(
                        menu_text,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                elif update.message:
                    await update.message.reply_text(
                        menu_text,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Error sending menu: {e}")
        else:
            # User not logged in
            try:
                message = (
                    f"{error_message}"
                    "🔒 You need to login first.\n"
                    "Use /login to authenticate."
                )
                if update.message:
                    await update.message.reply_text(message, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Error sending login message: {e}")
