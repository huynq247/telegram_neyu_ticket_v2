"""
Auto Logout Service
Automatically logs out users after 10 minutes of inactivity
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class AutoLogoutService:
    """Service to handle automatic logout after inactivity"""
    
    def __init__(self, auth_service, telegram_handler, inactive_minutes: int = 10):
        """
        Initialize auto-logout service
        
        Args:
            auth_service: Authentication service instance
            telegram_handler: Telegram bot handler for sending messages
            inactive_minutes: Minutes of inactivity before auto-logout (default: 10)
        """
        self.auth_service = auth_service
        self.telegram_handler = telegram_handler
        self.inactive_minutes = inactive_minutes
        self.inactive_seconds = inactive_minutes * 60
        
        # Track last activity time for each user
        self.last_activity: Dict[int, datetime] = {}
        
        # Track if user was warned
        self.warned_users: Dict[int, bool] = {}
        
        # Warning threshold (2 minutes before logout)
        self.warning_threshold_seconds = 120
        
        # Monitoring task
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        self.logger = logging.getLogger(__name__)
    
    def track_activity(self, user_id: int) -> None:
        """
        Track user activity
        
        Args:
            user_id: Telegram user ID
        """
        self.last_activity[user_id] = datetime.now()
        self.logger.debug(f"Tracked activity for user {user_id}")
        
        # Reset warning flag when user is active again
        if user_id in self.warned_users:
            self.warned_users[user_id] = False
    
    def get_inactive_seconds(self, user_id: int) -> Optional[int]:
        """
        Get seconds since last activity
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Seconds since last activity, or None if no activity tracked
        """
        if user_id not in self.last_activity:
            return None
        
        last_time = self.last_activity[user_id]
        elapsed = (datetime.now() - last_time).total_seconds()
        return int(elapsed)
    
    def should_warn(self, user_id: int) -> bool:
        """
        Check if user should receive inactivity warning
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user should be warned
        """
        if user_id in self.warned_users and self.warned_users[user_id]:
            return False  # Already warned
        
        inactive_seconds = self.get_inactive_seconds(user_id)
        if inactive_seconds is None:
            return False
        
        # Warn if inactive for (timeout - warning_threshold)
        warn_at = self.inactive_seconds - self.warning_threshold_seconds
        return inactive_seconds >= warn_at
    
    def should_logout(self, user_id: int) -> bool:
        """
        Check if user should be logged out
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user should be auto-logged out
        """
        inactive_seconds = self.get_inactive_seconds(user_id)
        if inactive_seconds is None:
            return False
        
        return inactive_seconds >= self.inactive_seconds
    
    async def send_warning(self, user_id: int) -> None:
        """
        Send inactivity warning to user and end any active conversations
        
        Args:
            user_id: Telegram user ID
        """
        try:
            # End any active conversation state to prevent conflicts
            # This allows user to interact with buttons after warning
            from telegram.ext import ConversationHandler
            
            # Get user's conversation states and end them
            if hasattr(self.telegram_handler, 'application') and self.telegram_handler.application:
                # Clear conversation state for this user
                for handler in self.telegram_handler.application.handlers.get(0, []):
                    if isinstance(handler, ConversationHandler):
                        # End conversation for this user
                        if user_id in handler.conversations:
                            handler.update_state(ConversationHandler.END, (user_id, user_id))
                            self.logger.debug(f"Ended conversation state for user {user_id} due to inactivity warning")
            
            remaining_seconds = self.warning_threshold_seconds
            remaining_minutes = remaining_seconds // 60
            
            warning_message = (
                f"⚠️ *Inactivity Warning*\n\n"
                f"You have been inactive for {self.inactive_minutes - 2} minutes.\n"
                f"You will be automatically logged out in *{remaining_minutes} minutes* "
                f"if no activity is detected.\n\n"
                f"💡 *Tip:* Use /menu or /start to continue using the bot."
            )
            
            await self.telegram_handler.application.bot.send_message(
                chat_id=user_id,
                text=warning_message,
                parse_mode='Markdown'
            )
            
            # Mark user as warned
            self.warned_users[user_id] = True
            self.logger.info(f"Sent inactivity warning to user {user_id} and cleared conversation state")
            
        except Exception as e:
            self.logger.error(f"Error sending warning to user {user_id}: {e}")
    
    async def auto_logout_user(self, user_id: int) -> bool:
        """
        Automatically logout user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if logout successful
        """
        try:
            # Get user info before logout
            user_info = self.auth_service.get_user_info(user_id)
            
            if not user_info:
                self.logger.debug(f"User {user_id} not logged in, skipping auto-logout")
                return False
            
            # End any active conversation state before logout
            from telegram.ext import ConversationHandler
            
            if hasattr(self.telegram_handler, 'application') and self.telegram_handler.application:
                # Clear ALL conversation states for this user
                try:
                    for group_id, handlers in self.telegram_handler.application.handlers.items():
                        for handler in handlers:
                            if isinstance(handler, ConversationHandler):
                                # End conversation for all possible conversation keys
                                # Key format: (user_id, user_id) for private chats
                                try:
                                    # Try to end with user_id key
                                    if user_id in handler.conversations:
                                        del handler.conversations[user_id]
                                        self.logger.debug(f"Cleared conversation state (key={user_id}) for user {user_id}")
                                    
                                    # Also try tuple key format
                                    tuple_key = (user_id, user_id)
                                    if tuple_key in handler.conversations:
                                        del handler.conversations[tuple_key]
                                        self.logger.debug(f"Cleared conversation state (key={tuple_key}) for user {user_id}")
                                    
                                    self.logger.info(f"✅ Ended all conversation states for user {user_id} before auto-logout")
                                except Exception as conv_err:
                                    self.logger.debug(f"Could not end conversation for user {user_id}: {conv_err}")
                except Exception as handler_err:
                    self.logger.warning(f"Error accessing conversation handlers: {handler_err}")
            
            # Send logout notification BEFORE actually logging out
            logout_message = (
                f"🚪 <b>Auto Logout</b>\n\n"
                f"You have been automatically logged out due to "
                f"{self.inactive_minutes} minutes of inactivity.\n\n"
                f"Use /login to log in again or /start to see available commands."
            )
            
            await self.telegram_handler.application.bot.send_message(
                chat_id=user_id,
                text=logout_message,
                parse_mode='HTML'
            )
            
            # Small delay to ensure message is sent before logout
            await asyncio.sleep(0.5)
            
            # Perform logout using revoke_session (synchronous method)
            success = self.auth_service.revoke_session(user_id)
            
            if success:
                if user_id in self.last_activity:
                    del self.last_activity[user_id]
                if user_id in self.warned_users:
                    del self.warned_users[user_id]
                
                self.logger.info(f"Auto-logged out user {user_id} after {self.inactive_minutes}min of inactivity")
                return True
            else:
                self.logger.warning(f"Failed to auto-logout user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error auto-logging out user {user_id}: {e}")
            return False
    
    async def check_inactive_users(self) -> None:
        """Check all users for inactivity and handle logouts"""
        
        users_to_check = list(self.last_activity.keys())
        
        if users_to_check:
            self.logger.debug(f"Checking {len(users_to_check)} users for inactivity")
        
        for user_id in users_to_check:
            try:
                # Check if user is authenticated
                user_info = self.auth_service.get_user_info(user_id)
                if not user_info:
                    # User not logged in, remove from tracking
                    if user_id in self.last_activity:
                        del self.last_activity[user_id]
                    if user_id in self.warned_users:
                        del self.warned_users[user_id]
                    self.logger.debug(f"User {user_id} not logged in, removed from tracking")
                    continue
                
                # Get inactive seconds
                inactive_seconds = self.get_inactive_seconds(user_id)
                if inactive_seconds:
                    self.logger.debug(f"User {user_id} inactive for {inactive_seconds}s (timeout: {self.inactive_seconds}s)")
                
                # Check if should logout (no warning, just logout directly at 10 minutes)
                if self.should_logout(user_id):
                    self.logger.info(f"User {user_id} reached timeout, logging out...")
                    await self.auto_logout_user(user_id)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error checking user {user_id}: {e}")
    
    async def monitor_loop(self) -> None:
        """Background task to monitor user inactivity"""
        
        self.logger.info(f"Auto-logout monitor started (timeout: {self.inactive_minutes}min)")
        
        try:
            while self.is_running:
                await self.check_inactive_users()
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            self.logger.info("Auto-logout monitor cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Error in auto-logout monitor: {e}")
    
    def start_monitoring(self) -> None:
        """Start the inactivity monitoring task"""
        if self.is_running:
            self.logger.warning("Auto-logout monitor already running")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self.monitor_loop())
        self.logger.info("Auto-logout monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop the inactivity monitoring task"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
        
        self.logger.info("Auto-logout monitoring stopped")
    
    def get_status(self) -> Dict:
        """
        Get service status
        
        Returns:
            Dictionary with service status information
        """
        return {
            'is_running': self.is_running,
            'inactive_timeout_minutes': self.inactive_minutes,
            'warning_threshold_seconds': self.warning_threshold_seconds,
            'tracked_users': len(self.last_activity),
            'warned_users': sum(1 for warned in self.warned_users.values() if warned)
        }
