"""
Enhanced Smart Authentication Handler
Main handler for /me command using file-based credentials and enhanced session management
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..services.smart_auth_file_manager import SmartAuthFileManager
from ..services.enhanced_session_manager import EnhancedSessionManager, SessionType
from ..services.activity_tracker import ActivityTracker

logger = logging.getLogger(__name__)

class EnhancedSmartAuthHandler:
    """Enhanced Smart Authentication Handler with file-based credentials"""
    
    def __init__(self, auth_service, keyboards, formatters):
        self.auth_service = auth_service
        self.keyboards = keyboards
        self.formatters = formatters
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.file_manager = SmartAuthFileManager("user.auth.smart")
        self.session_manager = EnhancedSessionManager()
        self.activity_tracker = ActivityTracker(self.session_manager)
        
        # Replace auth_service session management with enhanced version
        self._integrate_with_auth_service()
    
    def _integrate_with_auth_service(self):
        """Integrate enhanced session manager with existing auth service"""
        
        # Store original methods
        self.auth_service._original_create_session = getattr(self.auth_service, 'create_session', None)
        self.auth_service._original_validate_session = getattr(self.auth_service, 'validate_session', None)
        self.auth_service._original_revoke_session = getattr(self.auth_service, 'revoke_session', None)
        
        # Replace with enhanced versions
        self.auth_service.create_session = self._enhanced_create_session
        self.auth_service.validate_session = self._enhanced_validate_session
        self.auth_service.revoke_session = self._enhanced_revoke_session
        self.auth_service.is_authenticated = self._enhanced_is_authenticated
        
        self.logger.info("Integrated enhanced session management with auth service")
    
    def _enhanced_create_session(self, telegram_user_id: int, odoo_user_data: dict, 
                               session_type: str = 'manual_login') -> str:
        """Enhanced create session using new session manager"""
        
        # Map session type string to enum
        session_type_map = {
            'smart_auth': SessionType.SMART_AUTH,
            'manual_login': SessionType.MANUAL_LOGIN,
            'admin_session': SessionType.ADMIN_SESSION
        }
        
        session_type_enum = session_type_map.get(session_type, SessionType.MANUAL_LOGIN)
        
        return self.session_manager.create_session(
            telegram_user_id, 
            odoo_user_data, 
            session_type_enum
        )
    
    def _enhanced_validate_session(self, telegram_user_id: int):
        """Enhanced validate session with activity tracking"""
        
        is_valid, user_data = self.session_manager.validate_session(telegram_user_id)
        return is_valid, user_data
    
    def _enhanced_revoke_session(self, telegram_user_id: int) -> bool:
        """Enhanced revoke session"""
        
        return self.session_manager.revoke_session(telegram_user_id)
    
    def _enhanced_is_authenticated(self, telegram_user_id: int) -> bool:
        """Enhanced authentication check"""
        
        is_valid, _ = self.session_manager.validate_session(telegram_user_id)
        return is_valid
    
    async def handle_me_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /me smart authentication command"""
        
        user = update.effective_user
        
        # Track command activity
        await self.activity_tracker.track_command_activity(update, context, '/me')
        
        self.logger.info(f"Smart auth request from user: {user.username} (ID: {user.id})")
        
        # Check if user already authenticated
        if self.auth_service.is_authenticated(user.id):
            is_valid, user_data = self.auth_service.validate_session(user.id)
            if is_valid:
                session_info = self.session_manager.get_session_info(user.id)
                
                # Extend session on /me usage
                self.session_manager.track_activity(user.id, 'smart_login_refresh', 'User used /me while already logged in')
                
                time_left = session_info['time_until_timeout']
                hours_left = int(time_left.total_seconds() / 3600)
                
                await update.message.reply_text(
                    f"✅ *Already Authenticated*\n\n"
                    f"👤 Logged in as: *{user_data['name']}*\n"
                    f"📧 Email: {user_data['email']}\n"
                    f"🔐 Session Type: {session_info['session_type'].replace('_', ' ').title()}\n"
                    f"⏰ Time Left: ~{hours_left} hours\n"
                    f"📊 Activities: {session_info['activity_count']} commands\n\n"
                    f"Use /menu to continue working.",
                    parse_mode='Markdown'
                )
                return
        
        # Get credentials from file
        email, password = self.file_manager.get_credentials(user)
        
        if email and password:
            self.logger.info(f"Found smart auth credentials for {user.username} -> {email}")
            
            try:
                # Use existing authentication flow
                success, user_data, error = await self.auth_service.authenticate_user(email, password)
                
                if success:
                    # Create smart auth session
                    session_token = self.auth_service.create_session(
                        user.id, 
                        user_data, 
                        'smart_auth'  # 24h inactivity timeout
                    )
                    
                    # Track smart login activity
                    await self.activity_tracker.track_custom_activity(
                        user.id, 
                        'smart_login', 
                        f'Smart authentication successful for {email}'
                    )
                    
                    # Get session info for display
                    session_info = self.session_manager.get_session_info(user.id)
                    
                    await update.message.reply_text(
                        f"🚀 *Smart Authentication Successful!*\n\n"
                        f"👤 Welcome back, *{user_data['name']}*!\n"
                        f"📧 {user_data['email']}\n"
                        f"🏢 {user_data.get('company_name', 'N/A')}\n\n"
                        f"⏰ Session timeout: *24 hours* of inactivity\n"
                        f"💡 Use any command to keep your session active\n\n"
                        f"Use /menu to get started.",
                        parse_mode='Markdown'
                    )
                    
                    self.logger.info(f"Smart auth SUCCESS for {email} (user: {user.username})")
                    return
                    
                else:
                    self.logger.warning(f"Smart auth FAILED for {email}: {error}")
                    
                    await update.message.reply_text(
                        f"❌ *Smart Authentication Failed*\n\n"
                        f"📧 Attempted: {email}\n"
                        f"❗ Error: {error}\n\n"
                        f"Your stored credentials might be outdated or there's a server issue.\n\n"
                        f"Please use /login to authenticate manually."
                    )
                    return
                    
            except Exception as e:
                self.logger.error(f"Smart auth ERROR for {email}: {e}")
                
                await update.message.reply_text(
                    f"⚠️ *Smart Authentication Error*\n\n"
                    f"An unexpected error occurred during authentication.\n\n"
                    f"Please try /login instead or contact support if the issue persists."
                )
                return
        
        # No credentials found - show helpful info
        self.logger.info(f"No smart auth credentials for user: {user.username} (ID: {user.id})")
        
        # Check if user exists in smart auth file but is inactive
        user_info = self.file_manager.get_user_by_telegram_id(user.id)
        if user_info and not user_info.get('active', True):
            await update.message.reply_text(
                f"🔒 *Smart Authentication Disabled*\n\n"
                f"👤 Your Telegram: @{user.username or 'unknown'}\n"
                f"🆔 Your ID: {user.id}\n"
                f"📧 Associated Email: {user_info.get('email', 'N/A')}\n\n"
                f"Your smart authentication has been temporarily disabled.\n\n"
                f"Please use /login to authenticate manually or contact admin to re-enable smart auth."
            )
            return
        
        # Completely new user - show setup info
        await update.message.reply_text(
            f"👋 *Hi {user.first_name}!*\n\n"
            f"🔍 Smart authentication is not configured for your account.\n\n"
            f"📋 *Your Information:*\n"
            f"👤 Telegram: @{user.username or 'not set'}\n"
            f"🆔 User ID: {user.id}\n"
            f"📱 Name: {user.first_name} {user.last_name or ''}\n\n"
            f"💡 *To get smart authentication:*\n"
            f"1. Contact your admin with the above information\n"
            f"2. Admin will add you to the smart auth system\n"
            f"3. Then you can use /me for instant login\n\n"
            f"🔐 For now, please use /login to authenticate manually.",
            parse_mode='Markdown'
        )
    
    async def handle_session_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle session info command for debugging/admin"""
        
        user = update.effective_user
        
        # Check if authenticated
        if not self.auth_service.is_authenticated(user.id):
            await update.message.reply_text("❌ You need to login first to view session info.")
            return
        
        # Get session info
        session_info = self.session_manager.get_session_info(user.id)
        activity_summary = self.activity_tracker.get_user_activity_summary(user.id)
        
        if not session_info:
            await update.message.reply_text("❌ No session information available.")
            return
        
        # Format time remaining
        time_left = session_info['time_until_timeout']
        hours_left = int(time_left.total_seconds() / 3600)
        minutes_left = int((time_left.total_seconds() % 3600) / 60)
        
        time_until_hard_expiry = session_info['time_until_hard_expiry']
        hard_hours_left = int(time_until_hard_expiry.total_seconds() / 3600)
        
        session_type_emoji = {
            'smart_auth': '🚀',
            'manual_login': '🔐',
            'admin_session': '👨‍💼'
        }.get(session_info['session_type'], '📱')
        
        info_message = (
            f"📊 *Session Information*\n\n"
            f"{session_type_emoji} *Type:* {session_info['session_type'].replace('_', ' ').title()}\n"
            f"🕐 *Created:* {session_info['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            f"⚡ *Last Activity:* {session_info['last_activity'].strftime('%Y-%m-%d %H:%M')}\n\n"
            f"⏰ *Timeouts:*\n"
            f"• Inactivity: {hours_left}h {minutes_left}m remaining\n"
            f"• Hard Expiry: {hard_hours_left}h remaining\n"
            f"• Warning Sent: {'✅ Yes' if session_info['warned_about_timeout'] else '❌ No'}\n\n"
            f"📈 *Activity:*\n"
            f"• Total Commands: {session_info['activity_count']}\n"
            f"• Activity Score: {session_info['total_activity_score']:.1f}\n"
            f"• Recent Activities: {activity_summary.get('recent_activities_count', 0)}\n\n"
            f"💡 Use any command to extend your session!"
        )
        
        await update.message.reply_text(info_message, parse_mode='Markdown')
    
    def get_session_manager(self) -> EnhancedSessionManager:
        """Get session manager instance (for integration with other components)"""
        return self.session_manager
    
    def get_activity_tracker(self) -> ActivityTracker:
        """Get activity tracker instance (for integration with other components)"""
        return self.activity_tracker
    
    def get_file_manager(self) -> SmartAuthFileManager:
        """Get file manager instance (for admin functions)"""
        return self.file_manager