"""
Authentication Handler Module
Handle user login conversation flow with Odoo authentication
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..services.auth_service import OdooAuthService
from ..utils.formatters import BotFormatters

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
            await update.message.reply_text(
                f"✅ You are already logged in as *{user_data['name']}*\n"
                f"📧 Email: {user_data['email']}\n\n"
                "Use /logout to logout or /menu to access features.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Start login process
        welcome_message = (
            "🔐 *Login to Odoo Account*\n\n"
            "Please enter your Odoo email address to continue:\n\n"
            "💡 Use the same credentials you use to login to Odoo system.\n"
            "Type /cancel to abort login."
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        # Initialize login session
        self.login_sessions[user.id] = {
            'telegram_user': user,
            'step': 'waiting_email'
        }
        
        logger.info(f"User {user.id} ({user.username}) started login process")
        return 1  # WAITING_EMAIL state
    
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
                "Example: user@company.com"
            )
            return 1  # Stay in WAITING_EMAIL state
        
        # Store email in login session
        if user.id not in self.login_sessions:
            await update.message.reply_text("❌ Login session expired. Please use /login to start again.")
            return ConversationHandler.END
        
        self.login_sessions[user.id]['email'] = email
        self.login_sessions[user.id]['step'] = 'waiting_password'
        
        await update.message.reply_text(
            f"📧 Email: `{email}`\n\n"
            "🔑 Now please enter your Odoo password:\n\n"
            "⚠️ *Security Note:* Your password will not be stored, only used for authentication.",
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user.id} provided email: {email}")
        return 2  # WAITING_PASSWORD state
    
    async def receive_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle password input and authenticate with Odoo
        
        Returns:
            -1: End conversation (success or failure)
        """
        user = update.effective_user
        password = update.message.text.strip()
        
        # Get login session
        if user.id not in self.login_sessions:
            await update.message.reply_text("❌ Login session expired. Please use /login to start again.")
            return ConversationHandler.END
        
        login_session = self.login_sessions[user.id]
        email = login_session.get('email')
        
        if not email:
            await update.message.reply_text("❌ Email not found. Please use /login to start again.")
            return ConversationHandler.END
        
        # Delete the password message for security
        try:
            await update.message.delete()
        except Exception:
            pass  # Message might already be deleted
        
        # Show authentication in progress
        processing_message = await update.effective_chat.send_message(
            "🔄 Authenticating with Odoo...\n"
            "Please wait a moment."
        )
        
        try:
            # Authenticate with Odoo
            success, user_data, error_message = self.auth_service.authenticate_user(email, password)
            
            if success:
                # Create user session
                session_token = self.auth_service.create_session(user.id, user_data)
                
                # Success message
                success_text = (
                    f"✅ *Authentication Successful!*\n\n"
                    f"👤 Welcome, *{user_data['name']}*\n"
                    f"📧 Email: {user_data['email']}\n"
                    f"🏢 Company: {user_data.get('company_id', 'N/A')}\n\n"
                )
                
                # Add permissions info from user_data
                if user_data.get('is_helpdesk_manager'):
                    success_text += "👑 *Helpdesk Manager* - Full access\n"
                elif user_data.get('is_helpdesk_user'):
                    success_text += "� *Helpdesk User* - Standard access\n"
                else:
                    success_text += "👤 *User* - Basic access\n"
                
                success_text += "\nUse /menu to access ticket features!"
                
                await processing_message.edit_text(success_text, parse_mode='Markdown')
                
                logger.info(f"User {user.id} ({email}) authenticated successfully")
                
            else:
                # Authentication failed
                error_text = (
                    "❌ *Authentication Failed*\n\n"
                    f"Error: {error_message}\n\n"
                    "Please check your credentials and try again.\n"
                    "Use /login to retry."
                )
                
                await processing_message.edit_text(error_text, parse_mode='Markdown')
                
                logger.warning(f"Authentication failed for {user.id} ({email}): {error_message}")
        
        except Exception as e:
            logger.error(f"Error during authentication for {user.id}: {e}")
            await processing_message.edit_text(
                "❌ *System Error*\n\n"
                "An error occurred during authentication.\n"
                "Please try again later or contact support.",
                parse_mode='Markdown'
            )
        
        finally:
            # Clean up login session
            if user.id in self.login_sessions:
                del self.login_sessions[user.id]
        
        return ConversationHandler.END
    
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
    
    async def cancel_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    
    def _validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def require_authentication(self, func):
        """Decorator to require authentication for bot commands"""
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            
            # Check if user is authenticated
            is_valid, user_data = self.auth_service.validate_session(user.id)
            
            if not is_valid:
                await update.message.reply_text(
                    "🔐 *Authentication Required*\n\n"
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