"""
Enhanced Session Manager with Inactivity Timeout
Handles user sessions with automatic timeout based on user activity
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)

class SessionType(Enum):
    """Different types of sessions with different timeout rules"""
    SMART_AUTH = "smart_auth"
    MANUAL_LOGIN = "manual_login" 
    ADMIN_SESSION = "admin_session"

class EnhancedSessionManager:
    """Enhanced session management with inactivity timeout"""
    
    def __init__(self):
        self.active_sessions = {}
        self.logger = logging.getLogger(__name__)
        
        # Timeout configurations for different session types
        self.timeout_rules = {
            SessionType.SMART_AUTH: {
                'max_inactive_hours': 24,        # 24h không hoạt động → logout
                'warning_threshold_hours': 20,   # 20h → warning message
                'activity_extend_hours': 12      # Mỗi activity → extend 12h
            },
            SessionType.MANUAL_LOGIN: {
                'max_inactive_hours': 48,        # Manual login → longer timeout
                'warning_threshold_hours': 40,
                'activity_extend_hours': 24
            },
            SessionType.ADMIN_SESSION: {
                'max_inactive_hours': 8,         # Admin → shorter timeout (security)
                'warning_threshold_hours': 6,
                'activity_extend_hours': 4
            }
        }
        
        # Track activities that should extend session
        self.activity_weights = {
            'login': 1.0,
            'smart_login': 0.8,
            'command': 0.5,
            'callback': 0.4,
            'conversation': 0.6,
            'ticket_action': 0.8
        }
    
    def create_session(self, telegram_user_id: int, odoo_user_data: Dict[str, Any], 
                      session_type: SessionType = SessionType.MANUAL_LOGIN) -> str:
        """Create session with inactivity tracking"""
        
        # Get timeout rules for session type
        rules = self.timeout_rules[session_type]
        
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Calculate timeouts
        now = datetime.now()
        inactive_timeout = now + timedelta(hours=rules['max_inactive_hours'])
        warning_time = now + timedelta(hours=rules['warning_threshold_hours'])
        
        # Create enhanced session
        session_data = {
            'token': session_token,
            'session_type': session_type.value,
            'odoo_user': odoo_user_data,
            
            # Timing info
            'created_at': now,
            'last_activity': now,
            'inactive_timeout': inactive_timeout,
            'warning_sent_at': None,
            'warning_threshold': warning_time,
            
            # Activity tracking
            'activity_count': 0,
            'last_activity_type': 'login',
            'activity_extend_hours': rules['activity_extend_hours'],
            'total_activity_score': 1.0,
            
            # Session status
            'is_active': True,
            'warned_about_timeout': False,
            'expires_at': now + timedelta(hours=rules['max_inactive_hours'] * 2)  # Hard limit
        }
        
        self.active_sessions[telegram_user_id] = session_data
        
        self.logger.info(
            f"Created {session_type.value} session for user {telegram_user_id}, "
            f"inactive timeout: {inactive_timeout}, hard expiry: {session_data['expires_at']}"
        )
        
        return session_token
    
    def track_activity(self, telegram_user_id: int, activity_type: str, 
                      activity_context: str = None) -> bool:
        """Track user activity and extend session if needed"""
        
        session = self.active_sessions.get(telegram_user_id)
        if not session or not session['is_active']:
            return False
        
        now = datetime.now()
        
        # Determine activity weight
        base_activity = activity_type.split(':')[0]  # Extract base type from "command:menu"
        weight = self.activity_weights.get(base_activity, 0.3)
        
        # Update activity tracking
        session['last_activity'] = now
        session['activity_count'] += 1
        session['last_activity_type'] = activity_type
        session['total_activity_score'] += weight
        
        # Calculate extension based on activity weight and type
        extend_hours = session['activity_extend_hours']
        
        # Significant activities get full extension
        if weight >= 0.8:
            extension_hours = extend_hours
        elif weight >= 0.5:
            extension_hours = extend_hours * 0.7
        else:
            extension_hours = extend_hours * 0.3
        
        # Calculate new timeout
        new_timeout = now + timedelta(hours=extension_hours)
        
        # Only extend if new timeout is later than current AND within hard limit
        hard_limit = session['expires_at']
        if new_timeout > session['inactive_timeout'] and new_timeout <= hard_limit:
            old_timeout = session['inactive_timeout']
            session['inactive_timeout'] = min(new_timeout, hard_limit)
            
            # Reset warning if session was extended significantly
            if session['warned_about_timeout'] and extension_hours >= 2:
                session['warned_about_timeout'] = False
                session['warning_sent_at'] = None
                
                # Recalculate warning threshold
                rules = self.timeout_rules[SessionType(session['session_type'])]
                session['warning_threshold'] = now + timedelta(
                    hours=rules['warning_threshold_hours'] * 0.8
                )
            
            self.logger.debug(
                f"Extended session for user {telegram_user_id} from {old_timeout} to {session['inactive_timeout']} "
                f"(activity: {activity_type}, weight: {weight})"
            )
        
        return True
    
    def validate_session(self, telegram_user_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate user session with timeout check"""
        
        session = self.active_sessions.get(telegram_user_id)
        if not session:
            return False, None
        
        now = datetime.now()
        
        # Check hard expiry first
        if now > session['expires_at']:
            self.logger.info(
                f"Session hard expired for user {telegram_user_id}. "
                f"Expired at: {session['expires_at']}"
            )
            session['is_active'] = False
            self.revoke_session(telegram_user_id)
            return False, None
        
        # Check inactivity timeout
        if now > session['inactive_timeout']:
            self.logger.info(
                f"Session expired for user {telegram_user_id} due to inactivity. "
                f"Last activity: {session['last_activity']}"
            )
            session['is_active'] = False
            self.revoke_session(telegram_user_id)
            return False, None
        
        # Update last activity check
        session['last_activity'] = now
        
        return True, session['odoo_user']
    
    def check_session_timeout(self, telegram_user_id: int) -> Tuple[bool, Optional[str]]:
        """Check if session needs warning or has timed out"""
        
        session = self.active_sessions.get(telegram_user_id)
        if not session:
            return False, "No active session"
        
        now = datetime.now()
        
        # Check hard expiry
        if now > session['expires_at']:
            session['is_active'] = False
            self.revoke_session(telegram_user_id)
            return False, "Session hard expired"
        
        # Check inactivity timeout
        if now > session['inactive_timeout']:
            session['is_active'] = False
            self.revoke_session(telegram_user_id)
            return False, "Session expired due to inactivity"
        
        # Check if warning should be sent
        if (not session['warned_about_timeout'] and 
            now > session['warning_threshold']):
            
            session['warned_about_timeout'] = True
            session['warning_sent_at'] = now
            
            return True, "warning_needed"
        
        return True, None
    
    def get_session_info(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed session information"""
        
        session = self.active_sessions.get(telegram_user_id)
        if not session:
            return None
        
        now = datetime.now()
        
        return {
            'session_type': session['session_type'],
            'created_at': session['created_at'],
            'last_activity': session['last_activity'],
            'inactive_timeout': session['inactive_timeout'],
            'expires_at': session['expires_at'],
            'activity_count': session['activity_count'],
            'total_activity_score': session['total_activity_score'],
            'is_active': session['is_active'],
            'warned_about_timeout': session['warned_about_timeout'],
            'time_until_timeout': session['inactive_timeout'] - now,
            'time_until_hard_expiry': session['expires_at'] - now
        }
    
    def revoke_session(self, telegram_user_id: int) -> bool:
        """Revoke user session"""
        
        if telegram_user_id in self.active_sessions:
            session = self.active_sessions[telegram_user_id]
            session_type = session.get('session_type', 'unknown')
            activity_count = session.get('activity_count', 0)
            
            del self.active_sessions[telegram_user_id]
            
            self.logger.info(
                f"Session revoked for user {telegram_user_id} "
                f"(type: {session_type}, activities: {activity_count})"
            )
            return True
        return False
    
    def extend_session(self, telegram_user_id: int, hours: int) -> bool:
        """Manually extend session (admin function)"""
        
        session = self.active_sessions.get(telegram_user_id)
        if not session or not session['is_active']:
            return False
        
        now = datetime.now()
        new_timeout = session['inactive_timeout'] + timedelta(hours=hours)
        
        # Don't exceed hard limit
        if new_timeout <= session['expires_at']:
            session['inactive_timeout'] = new_timeout
            session['warned_about_timeout'] = False
            session['warning_sent_at'] = None
            
            self.logger.info(f"Manually extended session for user {telegram_user_id} by {hours} hours")
            return True
        
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions - called by cleanup service"""
        
        now = datetime.now()
        expired_sessions = []
        
        for user_id, session in self.active_sessions.items():
            if (not session['is_active'] or 
                now > session['expires_at'] or 
                now > session['inactive_timeout']):
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            self.revoke_session(user_id)
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_all_active_sessions(self) -> Dict[int, Dict[str, Any]]:
        """Get all active sessions (admin function)"""
        
        active = {}
        for user_id, session in self.active_sessions.items():
            if session['is_active']:
                active[user_id] = self.get_session_info(user_id)
        
        return active