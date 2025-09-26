"""
Session Cleanup Service
Background service to check inactive sessions, send warnings, and cleanup expired sessions
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .enhanced_session_manager import EnhancedSessionManager
from .activity_tracker import ActivityTracker

logger = logging.getLogger(__name__)

class SessionCleanupService:
    """Background service to manage session lifecycle"""
    
    def __init__(self, session_manager: EnhancedSessionManager, 
                 activity_tracker: ActivityTracker, bot_application):
        self.session_manager = session_manager
        self.activity_tracker = activity_tracker
        self.bot_application = bot_application
        self.logger = logging.getLogger(__name__)
        
        # Service configuration
        self.cleanup_task = None
        self.is_running = False
        self.check_interval = 3600  # Check every hour
        self.warning_check_interval = 1800  # Check warnings every 30 minutes
        
        # Statistics
        self.stats = {
            'total_warnings_sent': 0,
            'total_sessions_cleaned': 0,
            'last_cleanup_time': None,
            'service_start_time': None
        }
    
    def start_cleanup_service(self):
        """Start background cleanup service"""
        if self.is_running:
            self.logger.warning("Cleanup service is already running")
            return
        
        self.cleanup_task = asyncio.create_task(self._main_cleanup_loop())
        self.is_running = True
        self.stats['service_start_time'] = datetime.now()
        
        self.logger.info(
            f"Started session cleanup service - "
            f"cleanup interval: {self.check_interval}s, "
            f"warning interval: {self.warning_check_interval}s"
        )
    
    def stop_cleanup_service(self):
        """Stop background cleanup service"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.is_running = False
            
            self.logger.info(
                f"Stopped session cleanup service - "
                f"warnings sent: {self.stats['total_warnings_sent']}, "
                f"sessions cleaned: {self.stats['total_sessions_cleaned']}"
            )
    
    async def _main_cleanup_loop(self):
        """Main cleanup loop"""
        
        warning_check_counter = 0
        cleanup_check_counter = 0
        
        while True:
            try:
                current_time = datetime.now()
                
                # Check warnings more frequently than full cleanup
                if warning_check_counter <= 0:
                    await self._send_timeout_warnings()
                    warning_check_counter = self.warning_check_interval
                
                # Full cleanup less frequently
                if cleanup_check_counter <= 0:
                    await self._cleanup_expired_sessions()
                    await self._cleanup_activity_data()
                    self.stats['last_cleanup_time'] = current_time
                    cleanup_check_counter = self.check_interval
                
                # Sleep for 1 minute and update counters
                await asyncio.sleep(60)
                warning_check_counter -= 60
                cleanup_check_counter -= 60
                
            except asyncio.CancelledError:
                self.logger.info("Cleanup service cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _send_timeout_warnings(self):
        """Check all sessions and send timeout warnings"""
        
        warnings_sent = 0
        
        for user_id in list(self.session_manager.active_sessions.keys()):
            try:
                is_valid, status = self.session_manager.check_session_timeout(user_id)
                
                if status == "warning_needed":
                    success = await self._send_warning_to_user(user_id)
                    if success:
                        warnings_sent += 1
                        
            except Exception as e:
                self.logger.error(f"Error checking session timeout for user {user_id}: {e}")
        
        if warnings_sent > 0:
            self.stats['total_warnings_sent'] += warnings_sent
            self.logger.info(f"Sent timeout warnings to {warnings_sent} users")
    
    async def _send_warning_to_user(self, user_id: int) -> bool:
        """Send timeout warning to specific user"""
        
        try:
            session_info = self.session_manager.get_session_info(user_id)
            if not session_info:
                return False
            
            # Calculate time left
            time_left = session_info['time_until_timeout']
            hours_left = max(1, int(time_left.total_seconds() / 3600))
            minutes_left = max(1, int((time_left.total_seconds() % 3600) / 60))
            
            # Create warning message
            if hours_left >= 2:
                time_text = f"*{hours_left} hours*"
            else:
                time_text = f"*{hours_left}h {minutes_left}m*"
            
            session_type_text = {
                'smart_auth': '🚀 Smart Auth',
                'manual_login': '🔐 Manual Login',
                'admin_session': '👨‍💼 Admin Session'
            }.get(session_info['session_type'], '🔐 Login')
            
            warning_message = (
                f"⏰ *Session Timeout Warning*\n\n"
                f"🔓 Session Type: {session_type_text}\n"
                f"⌛ Time Remaining: {time_text}\n\n"
                f"Your session will expire soon due to inactivity.\n\n"
                f"💡 *To keep your session active:*\n"
                f"• Use /menu to access main menu\n"
                f"• Use /my_tickets to view your tickets\n"
                f"• Use /new_ticket to create a ticket\n"
                f"• Use /me for quick re-authentication\n\n"
                f"📊 Activities: {session_info['activity_count']} commands used"
            )
            
            await self.bot_application.bot.send_message(
                chat_id=user_id,
                text=warning_message,
                parse_mode='Markdown'
            )
            
            self.logger.info(f"Sent timeout warning to user {user_id} ({time_text} remaining)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send timeout warning to user {user_id}: {e}")
            return False
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        
        try:
            # Use session manager's cleanup method
            cleaned_count = self.session_manager.cleanup_expired_sessions()
            
            if cleaned_count > 0:
                self.stats['total_sessions_cleaned'] += cleaned_count
                self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}")
    
    async def _cleanup_activity_data(self):
        """Clean up old activity tracking data"""
        
        try:
            self.activity_tracker.cleanup_old_activity_data()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up activity data: {e}")
    
    async def force_cleanup_user_session(self, user_id: int, reason: str = "manual") -> bool:
        """Force cleanup specific user session (admin function)"""
        
        try:
            session_info = self.session_manager.get_session_info(user_id)
            if not session_info:
                return False
            
            # Send logout notification
            try:
                await self.bot_application.bot.send_message(
                    chat_id=user_id,
                    text=f"🔓 Your session has been terminated.\n\nReason: {reason}\n\nUse /login or /me to authenticate again."
                )
            except:
                pass  # Ignore notification failures
            
            # Revoke session
            success = self.session_manager.revoke_session(user_id)
            
            if success:
                self.logger.info(f"Force cleaned session for user {user_id} (reason: {reason})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error force cleaning session for user {user_id}: {e}")
            return False
    
    async def extend_user_session(self, user_id: int, hours: int, reason: str = "manual") -> bool:
        """Extend user session (admin function)"""
        
        try:
            success = self.session_manager.extend_session(user_id, hours)
            
            if success:
                # Send notification
                try:
                    await self.bot_application.bot.send_message(
                        chat_id=user_id,
                        text=f"⏰ Your session has been extended by {hours} hours.\n\nReason: {reason}"
                    )
                except:
                    pass  # Ignore notification failures
                
                self.logger.info(f"Extended session for user {user_id} by {hours} hours (reason: {reason})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error extending session for user {user_id}: {e}")
            return False
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        
        active_sessions = self.session_manager.get_all_active_sessions()
        
        # Calculate session type distribution
        session_types = {}
        warned_sessions = 0
        
        for user_id, session_info in active_sessions.items():
            session_type = session_info['session_type']
            session_types[session_type] = session_types.get(session_type, 0) + 1
            
            if session_info['warned_about_timeout']:
                warned_sessions += 1
        
        uptime = None
        if self.stats['service_start_time']:
            uptime = datetime.now() - self.stats['service_start_time']
        
        return {
            'is_running': self.is_running,
            'uptime': uptime,
            'check_interval': self.check_interval,
            'warning_interval': self.warning_check_interval,
            'total_warnings_sent': self.stats['total_warnings_sent'],
            'total_sessions_cleaned': self.stats['total_sessions_cleaned'],
            'last_cleanup_time': self.stats['last_cleanup_time'],
            'active_sessions_count': len(active_sessions),
            'warned_sessions_count': warned_sessions,
            'session_type_distribution': session_types
        }
    
    async def send_admin_report(self, admin_user_id: int):
        """Send admin report about session status"""
        
        try:
            stats = self.get_service_stats()
            active_sessions = self.session_manager.get_all_active_sessions()
            
            report = (
                f"📊 *Session Management Report*\n\n"
                f"🔧 Service Status: {'✅ Running' if stats['is_running'] else '❌ Stopped'}\n"
                f"⏰ Uptime: {stats['uptime']}\n"
                f"📈 Active Sessions: {stats['active_sessions_count']}\n"
                f"⚠️ Sessions with Warnings: {stats['warned_sessions_count']}\n\n"
                f"📊 *Session Types:*\n"
            )
            
            for session_type, count in stats['session_type_distribution'].items():
                emoji = {'smart_auth': '🚀', 'manual_login': '🔐', 'admin_session': '👨‍💼'}.get(session_type, '📱')
                report += f"{emoji} {session_type}: {count}\n"
            
            report += (
                f"\n📈 *Statistics:*\n"
                f"📨 Total Warnings Sent: {stats['total_warnings_sent']}\n"
                f"🧹 Total Sessions Cleaned: {stats['total_sessions_cleaned']}\n"
                f"🕐 Last Cleanup: {stats['last_cleanup_time']}"
            )
            
            await self.bot_application.bot.send_message(
                chat_id=admin_user_id,
                text=report,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending admin report: {e}")
            return False