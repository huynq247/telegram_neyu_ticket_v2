"""
Activity Tracker Middleware
Tracks user activities to extend session timeouts automatically
"""
import logging
from typing import Set, Dict, List
from telegram import Update
from telegram.ext import ContextTypes
from .enhanced_session_manager import EnhancedSessionManager

logger = logging.getLogger(__name__)

class ActivityTracker:
    """Track user activities for session management"""
    
    def __init__(self, session_manager: EnhancedSessionManager):
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)
        
        # Commands that extend session (high value activities)
        self.active_commands = {
            '/menu', '/new_ticket', '/my_tickets', '/help', 
            '/status', '/me', '/logout'
        }
        
        # Callback patterns that extend session
        self.active_callback_patterns = [
            'menu_', 'ticket_', 'confirm_', 'cancel_', 
            'destination_', 'priority_', 'back_to_menu'
        ]
        
        # Conversation states that extend session
        self.active_conversations = {
            'ticket_creation', 'view_tickets', 'ticket_details',
            'authentication', 'help_system'
        }
        
        # Commands that don't extend session (to prevent spam)
        self.passive_commands = {'/start'}
        
        # Track recent activities to prevent spam
        self.recent_activities: Dict[int, List[str]] = {}
        self.activity_window_seconds = 30
    
    async def track_command_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   command_name: str) -> bool:
        """Track command-based activity"""
        
        if not update.effective_user:
            return False
        
        user_id = update.effective_user.id
        
        # Skip passive commands
        if command_name in self.passive_commands:
            return False
        
        # Check for spam
        if self._is_spam_activity(user_id, f"command:{command_name}"):
            return False
        
        # Track active commands
        if command_name in self.active_commands:
            success = self.session_manager.track_activity(
                user_id, 
                f"command:{command_name}",
                f"Command executed: {command_name}"
            )
            
            if success:
                self.logger.debug(f"Tracked command activity: {command_name} for user {user_id}")
            
            return success
        
        return False
    
    async def track_callback_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    callback_data: str) -> bool:
        """Track callback query activity"""
        
        if not update.effective_user:
            return False
        
        user_id = update.effective_user.id
        
        # Check for spam
        if self._is_spam_activity(user_id, f"callback:{callback_data}"):
            return False
        
        # Check if callback should extend session
        for pattern in self.active_callback_patterns:
            if callback_data.startswith(pattern):
                success = self.session_manager.track_activity(
                    user_id, 
                    f"callback:{callback_data}",
                    f"Callback interaction: {callback_data}"
                )
                
                if success:
                    self.logger.debug(f"Tracked callback activity: {callback_data} for user {user_id}")
                
                return success
        
        return False
    
    async def track_conversation_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                        conversation_name: str, state: str = None) -> bool:
        """Track conversation flow activity"""
        
        if not update.effective_user:
            return False
        
        user_id = update.effective_user.id
        
        # Create activity identifier
        activity_id = f"conversation:{conversation_name}"
        if state:
            activity_id += f":{state}"
        
        # Check for spam
        if self._is_spam_activity(user_id, activity_id):
            return False
        
        # Track active conversations
        if conversation_name in self.active_conversations:
            success = self.session_manager.track_activity(
                user_id, 
                activity_id,
                f"Conversation flow: {conversation_name} -> {state or 'active'}"
            )
            
            if success:
                self.logger.debug(f"Tracked conversation activity: {conversation_name} for user {user_id}")
            
            return success
        
        return False
    
    async def track_ticket_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  action: str, ticket_id: str = None) -> bool:
        """Track ticket-related activities (high value)"""
        
        if not update.effective_user:
            return False
        
        user_id = update.effective_user.id
        
        # Ticket activities are high value
        activity_id = f"ticket_action:{action}"
        if ticket_id:
            activity_id += f":{ticket_id}"
        
        success = self.session_manager.track_activity(
            user_id, 
            activity_id,
            f"Ticket action: {action} on {ticket_id or 'new ticket'}"
        )
        
        if success:
            self.logger.debug(f"Tracked ticket activity: {action} for user {user_id}")
        
        return success
    
    async def track_custom_activity(self, user_id: int, activity_type: str, 
                                  context: str = None) -> bool:
        """Track custom activity type"""
        
        # Check for spam
        if self._is_spam_activity(user_id, activity_type):
            return False
        
        success = self.session_manager.track_activity(user_id, activity_type, context)
        
        if success:
            self.logger.debug(f"Tracked custom activity: {activity_type} for user {user_id}")
        
        return success
    
    def _is_spam_activity(self, user_id: int, activity: str) -> bool:
        """Check if activity is spam (same activity within short time window)"""
        
        import time
        current_time = time.time()
        
        # Initialize user activity tracking
        if user_id not in self.recent_activities:
            self.recent_activities[user_id] = []
        
        user_activities = self.recent_activities[user_id]
        
        # Clean old activities
        cutoff_time = current_time - self.activity_window_seconds
        user_activities[:] = [
            (timestamp, act) for timestamp, act in user_activities 
            if timestamp > cutoff_time
        ]
        
        # Check for recent same activity
        recent_same_activities = [
            (timestamp, act) for timestamp, act in user_activities 
            if act == activity and timestamp > cutoff_time
        ]
        
        # If same activity within window, consider spam
        if len(recent_same_activities) >= 3:  # Allow max 3 same activities per window
            self.logger.debug(f"Spam detected for user {user_id}: {activity}")
            return True
        
        # Add current activity
        user_activities.append((current_time, activity))
        
        # Keep only recent activities (memory management)
        if len(user_activities) > 50:
            user_activities[:] = user_activities[-30:]
        
        return False
    
    def get_user_activity_summary(self, user_id: int) -> Dict:
        """Get activity summary for user (debug/admin function)"""
        
        session_info = self.session_manager.get_session_info(user_id)
        if not session_info:
            return {'error': 'No active session'}
        
        recent_activities = self.recent_activities.get(user_id, [])
        
        return {
            'session_type': session_info['session_type'],
            'total_activities': session_info['activity_count'],
            'activity_score': session_info['total_activity_score'],
            'last_activity': session_info['last_activity'],
            'recent_activities_count': len(recent_activities),
            'time_until_timeout': session_info['time_until_timeout'],
            'is_warned': session_info['warned_about_timeout']
        }
    
    def cleanup_old_activity_data(self):
        """Clean up old activity tracking data"""
        
        import time
        current_time = time.time()
        cutoff_time = current_time - (self.activity_window_seconds * 2)
        
        cleaned_users = 0
        for user_id in list(self.recent_activities.keys()):
            user_activities = self.recent_activities[user_id]
            
            # Remove old activities
            user_activities[:] = [
                (timestamp, act) for timestamp, act in user_activities 
                if timestamp > cutoff_time
            ]
            
            # Remove empty entries
            if not user_activities:
                del self.recent_activities[user_id]
                cleaned_users += 1
        
        if cleaned_users > 0:
            self.logger.debug(f"Cleaned activity data for {cleaned_users} users")
    
    async def middleware_wrapper(self, handler_func, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Middleware wrapper for automatic activity tracking"""
        
        # Execute the original handler
        result = await handler_func(update, context)
        
        # Try to track activity based on update type
        if update.message and update.message.text:
            if update.message.text.startswith('/'):
                command = update.message.text.split()[0]
                await self.track_command_activity(update, context, command)
        
        elif update.callback_query:
            await self.track_callback_activity(update, context, update.callback_query.data)
        
        return result