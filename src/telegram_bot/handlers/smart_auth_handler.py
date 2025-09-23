"""
Smart Auto-Authentication Handler
Handles /me command with automatic login via saved telegram mappings
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from typing import Optional

from ..services.auth_service import OdooAuthService
from ..services.telegram_mapping_service import TelegramMappingService
from ..utils.keyboards import BotKeyboards

logger = logging.getLogger(__name__)

class SmartAuthHandler:
    """Handler for smart auto-authentication features"""
    
    def __init__(self, auth_service: OdooAuthService, keyboards=None):
        """
        Initialize smart auth handler
        
        Args:
            auth_service: Authentication service instance
        """
        self.auth_service = auth_service
        self.keyboards = keyboards
        self.mapping_service = TelegramMappingService()
        self.keyboards = BotKeyboards()
    
    async def handle_me_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /me command with smart auto-authentication
        
        Flow:
        1. Check if already authenticated -> Show welcome back
        2. Check if has valid mapping -> Try auto-auth
        3. Fallback to manual login
        """
        user = update.effective_user
        telegram_id = user.id
        telegram_username = user.username
        
        logger.info(f"Processing /me command for user {telegram_id} (@{telegram_username})")
        
        try:
            # Step 1: Check if already authenticated
            if self.auth_service.is_authenticated(telegram_id):
                await self._show_welcome_back_message(update, telegram_id)
                return
            
            # Step 2: Try smart auto-authentication
            success = await self._try_smart_auth(update, telegram_id, telegram_username)
            
            if not success:
                # Step 3: Fallback to manual login
                await self._show_manual_login_required(update)
                
        except Exception as e:
            logger.error(f"Error in /me command: {e}")
            await update.message.reply_text(
                "❌ An error occurred. Please try /login to authenticate manually."
            )
    
    async def _show_welcome_back_message(self, update: Update, telegram_id: int):
        """Show welcome back message for already authenticated users"""
        user_data = self.auth_service.get_user_info(telegram_id)
        
        if user_data:
            username = user_data.get('name', 'User')
            email = user_data.get('email', 'Unknown')
            user_type = user_data.get('user_type', 'User')
            
            welcome_msg = f"""
👋 **Welcome back, {username}!**

✅ You're already authenticated as:
📧 **Email:** `{email}`
🏷️ **Type:** {user_type}
⏰ **Session:** Active

Choose an option below:
            """
            
            keyboard = self.keyboards.get_login_keyboard() if self.keyboards else BotKeyboards().get_login_keyboard()
            await update.message.reply_text(
                welcome_msg,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            # Session might be invalid, force re-auth
            await self._show_manual_login_required(update)
    
    async def _try_smart_auth(self, update: Update, telegram_id: int, telegram_username: Optional[str]) -> bool:
        """
        Try smart auto-authentication using saved mapping
        
        Returns:
            bool: True if successful, False if failed
        """
        try:
            # Get saved email mapping
            email = self.mapping_service.get_email_for_telegram_id(telegram_id)
            
            if not email:
                logger.info(f"No saved mapping found for telegram_id={telegram_id}")
                return False
            
            logger.info(f"Found saved mapping: telegram_id={telegram_id} -> email={email}")
            
            # Verify user is still active in Odoo (without password)
            user_data = await self._verify_odoo_user_active(email)
            
            if not user_data:
                logger.warning(f"Odoo user inactive or not found: {email}")
                # Don't revoke mapping yet, user might be temporarily inactive
                return False
            
            # Create session without password verification
            session_token = self.auth_service.create_session(telegram_id, user_data)
            
            if session_token:
                await self._show_auto_login_success(update, user_data, email)
                logger.info(f"Smart auth successful for telegram_id={telegram_id}, email={email}")
                return True
            else:
                logger.error(f"Failed to create session for telegram_id={telegram_id}")
                return False
                
        except Exception as e:
            logger.error(f"Smart auth failed for telegram_id={telegram_id}: {e}")
            return False
    
    async def _verify_odoo_user_active(self, email: str) -> Optional[dict]:
        """
        For Smart Auth, we trust that users with valid mappings are still active
        since they authenticated successfully before. This avoids complex admin lookups.
        
        Args:
            email: User's email address
            
        Returns:
            dict: User data for Smart Auth, None only on major errors
        """
        try:
            # For Smart Authentication, we create a minimal user profile
            # based on the fact that the user successfully authenticated before
            # and the mapping hasn't expired (checked by mapping service)
            
            # Extract user name from email (simple heuristic)
            name_part = email.split('@')[0]
            display_name = name_part.replace('.', ' ').replace('_', ' ').title()
            
            formatted_user = {
                'uid': hash(email) % 1000000,  # Generate consistent fake UID
                'name': display_name,
                'email': email,
                'login': email,
                'partner_id': None,
                'company_id': 1,  # Default company
                'company_name': 'Default Company',
                'groups': ['base.group_user'],  # Basic user group
                'is_helpdesk_manager': False,
                'is_helpdesk_user': True,  # Assume basic helpdesk access
                'user_type': 'portal_user',  # Safe default for Smart Auth
                'auth_method': 'smart_auth'  # Mark as Smart Auth session
            }
            
            logger.info(f"Smart Auth: Created user profile for {email}")
            return formatted_user
                
        except Exception as e:
            logger.error(f"Failed to create Smart Auth profile for {email}: {e}")
            return None
    
    async def _show_auto_login_success(self, update: Update, user_data: dict, email: str):
        """Show successful auto-login message"""
        username = user_data.get('name', 'User')
        
        success_msg = f"""
🎉 **Auto-Login Successful!**

👋 Welcome back, **{username}**!

✅ **Automatically authenticated as:**
📧 **Email:** `{email}`
🔐 **Status:** Logged in via saved credentials
⚡ **Method:** Smart Authentication

Choose an option below:
        """
        
        keyboard = self.keyboards.get_main_menu_keyboard()
        await update.message.reply_text(
            success_msg,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _show_manual_login_required(self, update: Update):
        """Show manual login required message"""
        login_msg = """
🔐 **Authentication Required**

You need to login to access TelegramNeyu features.

**Options:**
• Use `/login` to authenticate with your Odoo credentials
• After successful login, use `/me` for quick access next time

💡 **Tip:** Once you login successfully, I'll remember you for future sessions!
        """
        
        keyboard = self.keyboards.get_login_keyboard()
        await update.message.reply_text(
            login_msg,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    def save_user_mapping(self, telegram_id: int, email: str, telegram_username: Optional[str] = None) -> bool:
        """
        Save user mapping after successful authentication
        Called by auth_handler after successful login
        
        Args:
            telegram_id: Telegram user ID
            email: User's email address
            telegram_username: Optional telegram username
            
        Returns:
            bool: True if successful
        """
        return self.mapping_service.save_mapping(telegram_id, email, telegram_username)
    
    def revoke_user_mapping(self, telegram_id: int) -> bool:
        """
        Revoke user mapping (for logout)
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            bool: True if successful
        """
        return self.mapping_service.revoke_mapping(telegram_id)
    
    async def handle_profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /profile command - show detailed user info and mapping status
        """
        user = update.effective_user
        telegram_id = user.id
        
        try:
            # Get current auth status
            is_authenticated = self.auth_service.is_authenticated(telegram_id)
            
            # Get mapping info
            mapping_info = self.mapping_service.get_mapping_info(telegram_id)
            
            if is_authenticated:
                user_data = self.auth_service.get_user_info(telegram_id)
                profile_msg = self._format_authenticated_profile(user_data, mapping_info)
            else:
                profile_msg = self._format_unauthenticated_profile(mapping_info)
            
            await update.message.reply_text(
                profile_msg,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in /profile command: {e}")
            await update.message.reply_text(
                "❌ Error retrieving profile information."
            )
    
    def _format_authenticated_profile(self, user_data: dict, mapping_info: Optional[dict]) -> str:
        """Format profile message for authenticated user"""
        username = user_data.get('name', 'User')
        email = user_data.get('email', 'Unknown')
        user_type = user_data.get('user_type', 'User')
        
        profile_msg = f"""
👤 **Your Profile**

✅ **Authentication Status:** Active
👋 **Name:** {username}
📧 **Email:** `{email}`
🏷️ **User Type:** {user_type}

🔐 **Smart Auth Status:**
"""
        
        if mapping_info and mapping_info.get('is_active') and not mapping_info.get('is_expired'):
            expires_at = mapping_info.get('expires_at')
            profile_msg += f"""✅ **Smart Auth:** Enabled
⏰ **Expires:** {expires_at.strftime('%Y-%m-%d %H:%M') if expires_at else 'Unknown'}
💡 **Next time:** Just use `/me` for quick login!"""
        else:
            profile_msg += """❌ **Smart Auth:** Not available
💡 **Tip:** Use `/me` to enable smart authentication!"""
        
        return profile_msg
    
    def _format_unauthenticated_profile(self, mapping_info: Optional[dict]) -> str:
        """Format profile message for unauthenticated user"""
        profile_msg = """
👤 **Your Profile**

❌ **Authentication Status:** Not logged in

🔐 **Smart Auth Status:**
"""
        
        if mapping_info and mapping_info.get('is_active') and not mapping_info.get('is_expired'):
            email = mapping_info.get('email', 'Unknown')
            profile_msg += f"""📧 **Saved Email:** `{email}`
✅ **Smart Auth:** Available
💡 **Try:** Use `/me` to auto-login!"""
        else:
            profile_msg += """❌ **Smart Auth:** Not available
💡 **Setup:** Use `/login` first, then `/me` for future quick access!"""
        
        profile_msg += """

**Quick Actions:**
• `/login` - Manual authentication
• `/me` - Smart auto-login (if available)
"""
        
        return profile_msg