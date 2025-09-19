"""
Authentication Handler Module
Handle user login conversation flow with Odoo authentication
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..services.auth_service import OdooAuthService
from ..utils.formatters import BotFormatters

# Conversation states - should match bot_handler.py
WAITING_EMAIL, WAITING_PASSWORD = range(1, 3)

logger = logging.getLogger(__name__)

class AuthHandler:
    """Class to handle authentication conversation flow"""
    
    def __init__(self, auth_service: OdooAuthService):
        """
        Initialize Authentication Handler
        
        Args:
            auth_service: OdooAuthService instance
        """
        self.auth_service = auth_service
        self.formatters = BotFormatters()
        
        # Temporary storage for login process
        self.login_sessions = {}
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle /login command - start authentication flow
        
        Returns:
            WAITING_EMAIL: Next conversation state
        """
        user = update.effective_user
        
        # Check if user is already authenticated
        is_valid, user_data = self.auth_service.validate_session(user.id)
        
        if is_valid:
            message_text = (
                f"✅ You are already logged in as *{user_data['name']}*\n"
                f"📧 Email: {user_data['email']}\n\n"
                "Use /logout to logout or /menu to access features."
            )
            
            # Handle both callback query and regular message
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message_text,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    message_text,
                    parse_mode='Markdown'
                )
            return ConversationHandler.END
        
        # Start login process - simple version
        welcome_message = (
            "🔐 *Login to Odoo Account*\n\n"
            "Please enter your email address to begin:"
        )
        
        # Handle both callback query and regular message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_message,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        # Initialize login session
        self.login_sessions[user.id] = {
            'telegram_user': user,
            'step': 'waiting_email'
        }
        
        logger.info(f"User {user.id} ({user.username}) started login process")
        return WAITING_EMAIL
    
    async def receive_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle email input from user
        
        Returns:
            WAITING_PASSWORD: Next conversation state
        """
        user = update.effective_user
        email = update.message.text.strip()
        
        # Basic email validation
        if not self._validate_email(email):
            await update.message.reply_text(
                "❌ Invalid email format. Please enter a valid email address:\n\n"
                "Example: john.doe@company.com"
            )
            return WAITING_EMAIL  # Stay in WAITING_EMAIL state
        
        # Store email in session
        if user.id in self.login_sessions:
            self.login_sessions[user.id]['email'] = email
            self.login_sessions[user.id]['step'] = 'waiting_password'
        
        # Ask for password
        await update.message.reply_text(
            f"📧 Email: {email}\n\n"
            "🔒 Now enter your password:"
        )
        
        logger.info(f"User {user.id} provided email: {email}")
        return WAITING_PASSWORD
    
    async def receive_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle password input and complete authentication
        
        Returns:
            ConversationHandler.END: End conversation
        """
        user = update.effective_user
        password = update.message.text.strip()
        
        # Get stored email from session
        if user.id not in self.login_sessions:
            await update.message.reply_text(
                "❌ Session expired. Please start over with /login"
            )
            return ConversationHandler.END
        
        email = self.login_sessions[user.id].get('email')
        
        if not email:
            await update.message.reply_text(
                "❌ Email not found. Please start over with /login"
            )
            return ConversationHandler.END
        
        # Delete the message containing password for security
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete password message: {e}")
        
        # Show processing message
        processing_message = await update.get_bot().send_message(
            chat_id=update.effective_chat.id,
            text="🔄 *Authenticating...*\n\n"
                 f"📧 Email: {email}\n"
                 "⏳ Verifying credentials with Odoo...",
            parse_mode='Markdown'
        )
        
        # Attempt authentication
        is_authenticated, user_data, error_message = self.auth_service.authenticate_user(email, password)
        
        if is_authenticated:
            # Create session
            session_token = self.auth_service.create_session(user.id, user_data)
            
            if session_token:
                success_text = (
                    "✅ *Login Successful!*\n\n"
                    f"👤 Welcome, *{user_data['name']}*!\n"
                    f"📧 {email}\n"
                    f"🏢 {user_data.get('company_name', 'N/A')}\n\n"
                )
                
                # Add permissions info from user_data
                if user_data.get('is_helpdesk_manager'):
                    success_text += "👑 *Helpdesk Manager* - Full access\n"
                elif user_data.get('is_helpdesk_user'):
                    success_text += "🎫 *Helpdesk User* - Standard access\n"
                else:
                    success_text += "👤 *User* - Basic access\n"
                
                success_text += "\nUse /menu to access ticket features!"
                
                await processing_message.edit_text(success_text, parse_mode='Markdown')
                
                logger.info(f"User {user.id} ({email}) authenticated successfully")
                
            else:
                await processing_message.edit_text(
                    "❌ *Session Error*\n\n"
                    "Login succeeded but failed to create session.\n"
                    "Please try again with /login.",
                    parse_mode='Markdown'
                )
                
        else:
            # Authentication failed
            error_text = (
                "❌ *Login Failed*\n\n"
                f"Error: {error_message}\n\n"
                "Please check your credentials and try again.\n"
                "Use /login to retry."
            )
            
            await processing_message.edit_text(error_text, parse_mode='Markdown')
            
            logger.warning(f"Login failed for {user.id} ({email}): {error_message}")
        
        # Clean up login session
        self.login_sessions.pop(user.id, None)
        return ConversationHandler.END
    
    def _validate_email(self, email: str) -> bool:
        """
        Basic email validation
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email format is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def logout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /logout command"""
        user = update.effective_user
        
        # Check if user is logged in
        is_valid, user_data = self.auth_service.validate_session(user.id)
        
        if not is_valid:
            await update.message.reply_text(
                "ℹ️ You are not currently logged in.\n"
                "Use /login to authenticate."
            )
            return
        
        # Revoke session
        success = self.auth_service.revoke_session(user.id)
        
        if success:
            await update.message.reply_text(
                f"✅ Successfully logged out.\n\n"
                f"Goodbye, *{user_data['name']}*!\n\n"
                "Use /login to authenticate again.",
                parse_mode='Markdown'
            )
            logger.info(f"User {user.id} ({user_data['email']}) logged out")
        else:
            await update.message.reply_text("❌ Error during logout. Please try again.")
    
    async def cancel_auth_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle login cancellation"""
        user = update.effective_user
        
        # Clean up login session
        if user.id in self.login_sessions:
            del self.login_sessions[user.id]
        
        await update.message.reply_text(
            "❌ Login cancelled.\n\n"
            "Use /login when you're ready to authenticate."
        )
        
        logger.info(f"User {user.id} cancelled login process")
        return ConversationHandler.END
    
    # Decorator for methods that require authentication
    def require_auth(self):
        """
        Decorator to require authentication for handler methods
        
        Usage:
            @auth_handler.require_auth()
            async def some_handler(update, context):
                # This handler requires authentication
                pass
        """
        def decorator(func):
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                user_id = update.effective_user.id
                
                # Check authentication
                is_valid, user_data = self.auth_service.validate_session(user_id)
                
                if not is_valid:
                    await update.message.reply_text(
                        "🔐 *Authentication Required*\n\n"
                        "You need to be logged in to use this feature.\n\n"
                        "Please login to your Odoo account first.\n\n"
                        "Use /login to authenticate.",
                        parse_mode='Markdown'
                    )
                    return
                
                # Add user_data to context for use in the wrapped function
                context.user_data['odoo_user'] = user_data
                
                # Call the original function
                return await func(update, context, *args, **kwargs)
            
            return wrapper
        return decorator