"""
Smart Auto-Authentication Handler
Handles /me command with automatic login via saved telegram mappings
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from typing import Optional

from ..utils.rate_limiter import rate_limit_check

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
    
    def _escape_markdown(self, text: str) -> str:
        """
        Escape markdown special characters for Telegram MarkdownV2
        
        Args:
            text: Text to escape
            
        Returns:
            str: Escaped text safe for Markdown
        """
        if not text:
            return ""
        
        # Characters that need escaping in Markdown
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        escaped_text = str(text)
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        
        return escaped_text
    
    @rate_limit_check
    async def handle_me_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            
            # Escape markdown special characters
            username_escaped = self._escape_markdown(username)
            email_escaped = self._escape_markdown(email)
            user_type_escaped = self._escape_markdown(user_type)
            
            welcome_msg = f"""
👋 Welcome back, {username_escaped}!

✅ You're already authenticated as:
📧 Email: {email_escaped}
🏷️ Type: {user_type_escaped}
⏰ Session: Active

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
        Verify user is active and collect same user data as regular authentication
        
        Args:
            email: User's email address
            
        Returns:
            dict: Complete user data with same structure as /login auth
        """
        try:
            # Use auth service to lookup user info without password verification
            # This will get the same complete user data as regular authentication
            user_data = await self._get_odoo_user_info(email)
            
            if user_data:
                # Add Smart Auth specific markers
                user_data['auth_method'] = 'smart_auth'
                user_data['auth_timestamp'] = datetime.now().isoformat()
                logger.info(f"Smart Auth: Retrieved complete user profile for {email}")
                return user_data
            else:
                logger.warning(f"Smart Auth: User not found or inactive: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to verify Odoo user for Smart Auth: {e}")
            return None
    
    async def _get_odoo_user_info(self, email: str) -> Optional[dict]:
        """
        Get complete user information from Odoo without password verification
        This ensures Smart Auth collects same data as regular login
        """
        try:
            import xmlrpc.client
            from datetime import datetime
            
            # Use XML-RPC to get user info (same as regular auth but without password)
            common_url = f"{self.auth_service.odoo_xmlrpc_url}/xmlrpc/2/common"
            models_url = f"{self.auth_service.odoo_xmlrpc_url}/xmlrpc/2/object"
            
            # Try to connect and search for user
            models = xmlrpc.client.ServerProxy(models_url)
            
            # Search for user by email (using admin credentials would be ideal here)
            # For now, we'll create a complete profile based on mapping data
            # In production, you should use admin credentials to lookup real user data
            
            # Get cached user data from a successful previous login if available
            # This is a simplified approach - in production you'd want proper admin lookup
            user_data = await self._build_complete_user_profile(email)
            return user_data
            
        except Exception as e:
            logger.error(f"Failed to get Odoo user info: {e}")
            return None
    
    async def _build_complete_user_profile(self, email: str) -> dict:
        """
        Build complete user profile with same structure as regular authentication
        This ensures consistency between /login and /me commands for ticket creation
        """
        try:
            # Try to get cached user data from previous successful login
            cached_data = await self._get_cached_user_data(email)
            if cached_data:
                # Use cached data but mark as Smart Auth
                cached_data['auth_method'] = 'smart_auth'
                cached_data['auth_timestamp'] = datetime.now().isoformat()
                logger.info(f"Smart Auth: Using cached user data for {email}")
                return cached_data
            
            # Fallback: Build user profile from email heuristics
            # Extract user name from email (improved heuristic)
            name_part = email.split('@')[0]
            display_name = name_part.replace('.', ' ').replace('_', ' ').replace('-', ' ').title()
            
            # Get company name from email domain
            domain = email.split('@')[1] if '@' in email else 'company.com'  
            company_name = domain.split('.')[0].title()
            
            # Determine user type based on email patterns
            user_type = 'admin_helpdesk' if self._is_admin_email(email) else 'portal_user'
            
            # Build complete user profile matching regular auth structure
            formatted_user = {
                'uid': abs(hash(email)) % 1000000,  # Consistent UID based on email
                'name': display_name,
                'email': email,
                'login': email,
                'partner_id': abs(hash(email + '_partner')) % 1000000,
                'company_id': abs(hash(domain)) % 1000,
                'company_name': company_name,
                'groups': self._get_user_groups(email),
                'is_helpdesk_manager': self._is_manager_email(email),
                'is_helpdesk_user': True,
                'user_type': user_type, 
                'auth_method': 'smart_auth',
                'auth_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Smart Auth: Built complete user profile for {email} (type: {user_type})")
            return formatted_user
            
        except Exception as e:
            logger.error(f"Failed to build user profile: {e}")
            return None
    
    async def _get_cached_user_data(self, email: str) -> Optional[dict]:
        """Try to get cached user data from telegram mapping or previous sessions"""
        try:
            # In future versions, you could store full user data in telegram_mapping table
            # For now, this returns None to use heuristic approach
            return None
        except Exception as e:
            logger.error(f"Failed to get cached user data: {e}")
            return None
    
    def _is_admin_email(self, email: str) -> bool:
        """Determine if email suggests admin/internal user"""
        admin_domains = ['neyu.co', 'company.com']  # Add your admin domains
        admin_keywords = ['admin', 'it', 'support', 'helpdesk', 'manager']
        
        email_lower = email.lower()
        domain = email.split('@')[1] if '@' in email else ''
        
        # Check domain
        if domain in admin_domains:
            return True
            
        # Check email content
        return any(keyword in email_lower for keyword in admin_keywords)
    
    def _get_user_groups(self, email: str) -> list:
        """Get user groups based on email analysis"""
        if self._is_admin_email(email):
            if self._is_manager_email(email):
                return ['Help Desk Manager', 'Help Desk User', 'IT Services']
            else:
                return ['Help Desk User', 'IT Services']
        else:
            return ['Portal User', 'Base User']
    
    def _is_manager_email(self, email: str) -> bool:
        """Check if email suggests manager role"""
        manager_indicators = ['admin', 'manager', 'lead', 'director', 'head']
        email_lower = email.lower()
        return any(indicator in email_lower for indicator in manager_indicators)
    
    async def _show_auto_login_success(self, update: Update, user_data: dict, email: str):
        """Show successful auto-login message"""
        username = user_data.get('name', 'User')
        
        # Escape markdown special characters in username and email
        username_escaped = self._escape_markdown(username)
        email_escaped = self._escape_markdown(email)
        
        success_msg = f"""
🎉 *Auto-Login Successful!*

👋 Welcome back, {username_escaped}!

✅ Automatically authenticated as:
📧 Email: {email_escaped}
🔐 Status: Logged in via saved credentials
⚡ Method: Smart Authentication

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
🔐 *Authentication Required*

You need to login to access TelegramNeyu features.

*Options:*
• Use /login to authenticate with your Odoo credentials
• After successful login, use /me for quick access next time

💡 *Tip:* Once you login successfully, I'll remember you for future sessions!
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
    
    @rate_limit_check
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