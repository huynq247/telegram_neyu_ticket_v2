"""
Odoo Authentication Service Module
Handle user authentication with Odoo and session management
"""
import logging
import secrets
import xmlrpc.client
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class OdooAuthService:
    """Service to handle Odoo user authentication and session management"""
    
    def __init__(self, odoo_url: str, odoo_db: str):
        """
        Initialize Odoo Authentication Service
        
        Args:
            odoo_url: Odoo server URL
            odoo_db: Odoo database name
        """
        self.odoo_url = odoo_url
        self.odoo_db = odoo_db
        
        # XML-RPC endpoints - COMMENTED OUT FOR NOW
        # Auto-detect the best endpoint (try proxy on port 80 first)
        # if ':15432' in odoo_url or ':8069' in odoo_url:
        #     # Extract host and try port 80 for proxy setup
        #     host = odoo_url.split('://')[1].split(':')[0]
        #     self.proxy_url = f"http://{host}"
        #     logger.info(f"Using proxy URL for XML-RPC: {self.proxy_url}")
        #     self.common_endpoint = f'{self.proxy_url}/xmlrpc/2/common'
        #     self.object_endpoint = f'{self.proxy_url}/xmlrpc/2/object'
        # else:
        #     self.common_endpoint = f'{odoo_url}/xmlrpc/2/common'
        #     self.object_endpoint = f'{odoo_url}/xmlrpc/2/object'
        
        # Session storage (in production, use Redis or database)
        self.active_sessions = {}
        
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user with Odoo credentials
        
        Args:
            email: User's Odoo email
            password: User's Odoo password
            
        Returns:
            (success, user_data, error_message)
        """
        try:
            logger.info(f"Attempting authentication for user: {email}")
            
            # Try XML-RPC authentication first - COMMENTED OUT FOR NOW
            # success, user_data, error = self._try_xmlrpc_auth(email, password)
            # if success:
            #     return success, user_data, error
            
            # Fallback authentication for development (until XML-RPC is fully configured)
            fallback_users = {
                "huy.nguyen@neyu.co": {
                    'uid': 1,
                    'name': 'Huy Nguyen',
                    'email': 'huy.nguyen@neyu.co',
                    'login': 'huy.nguyen@neyu.co',
                    'partner_id': 1,
                    'company_id': 1,
                    'groups': ['IT Services', 'Help Desk Manager'],
                    'is_helpdesk_manager': True,
                    'is_helpdesk_user': True
                },
                "eric.tra@neyu.co": {
                    'uid': 2,
                    'name': 'Eric Tra',
                    'email': 'eric.tra@neyu.co',
                    'login': 'eric.tra@neyu.co',
                    'partner_id': 2,
                    'company_id': 1,
                    'groups': ['Help Desk User'],
                    'is_helpdesk_manager': False,
                    'is_helpdesk_user': True
                }
            }
            
            if email in fallback_users and password == "Neyu@2025":
                logger.info(f"Using fallback authentication for {email}")
                return True, fallback_users[email], None
            
            # If no fallback user found, return authentication failure
            logger.warning(f"Authentication failed for {email} - not in fallback users or wrong password")
            return False, None, "Invalid email or password"
            
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return False, None, "Authentication failed due to system error"
    
    # COMMENTED OUT - XML-RPC Authentication temporarily disabled
    # def _try_xmlrpc_auth(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    #     """
    #     Try XML-RPC authentication with multiple endpoints
    #     
    #     Returns:
    #         (success, user_data, error_message)
    #     """
    #     endpoints_to_try = [
    #         (self.common_endpoint, self.object_endpoint),  # Proxy on port 80
    #     ]
    #     
    #     # If using proxy, also try direct port 8069 as fallback
    #     if hasattr(self, 'proxy_url'):
    #         host = self.proxy_url.replace('http://', '').replace('https://', '')
    #         direct_url = f"http://{host}:8069"
    #         endpoints_to_try.append((
    #             f"{direct_url}/xmlrpc/2/common",
    #             f"{direct_url}/xmlrpc/2/object"
    #         ))
    #     
    #     last_error = "XML-RPC connection failed"
    #     
    #     for common_endpoint, object_endpoint in endpoints_to_try:
    #         try:
    #             logger.info(f"Trying XML-RPC authentication via: {common_endpoint}")
    #             
    #             # Connect to Odoo common endpoint
    #             common = xmlrpc.client.ServerProxy(common_endpoint)
    #             
    #             # Authenticate with Odoo
    #             uid = common.authenticate(self.odoo_db, email, password, {})
    #             
    #             if not uid:
    #                 logger.warning(f"Authentication failed for user: {email}")
    #                 return False, None, "Invalid email or password"
    #             
    #             # Get user information
    #             models = xmlrpc.client.ServerProxy(object_endpoint)
    #             
    #             user_data = models.execute_kw(
    #                 self.odoo_db, uid, password,
    #                 'res.users', 'read', [uid],
    #                 {
    #                     'fields': [
    #                         'name', 'email', 'login', 'partner_id', 
    #                         'groups_id', 'company_id', 'active'
    #                     ]
    #                 }
    #             )
    #             
    #             if not user_data or not user_data[0].get('active'):
    #                 logger.warning(f"User account inactive: {email}")
    #                 return False, None, "User account is inactive"
    #             
    #             user_info = user_data[0]
    #             
    #             # Get user groups for permissions
    #             group_data = models.execute_kw(
    #                 self.odoo_db, uid, password,
    #                 'res.groups', 'read', [user_info['groups_id']],
    #                 {'fields': ['name', 'category_id']}
    #             )
    #             
    #             # Format user data
    #             formatted_user = {
    #                 'uid': uid,
    #                 'name': user_info['name'],
    #                 'email': user_info['email'],
    #                 'login': user_info['login'],
    #                 'partner_id': user_info['partner_id'][0] if user_info['partner_id'] else None,
    #                 'company_id': user_info['company_id'][0] if user_info['company_id'] else None,
    #                 'groups': [group['name'] for group in group_data],
    #                 'is_helpdesk_manager': self._is_helpdesk_manager(group_data),
    #                 'is_helpdesk_user': self._is_helpdesk_user(group_data)
    #             }
    #             
    #             logger.info(f"XML-RPC authentication successful for user: {email} via {common_endpoint}")
    #             return True, formatted_user, None
    #             
    #         except xmlrpc.client.Fault as e:
    #             logger.error(f"Odoo XML-RPC error via {common_endpoint}: {e}")
    #             last_error = f"XML-RPC service error: {e}"
    #             continue
    #             
    #         except Exception as e:
    #             logger.error(f"Connection error via {common_endpoint}: {e}")
    #             last_error = f"Connection failed: {e}"
    #             continue
    #     
    #     # All endpoints failed
    #     return False, None, last_error
    
    def create_session(self, telegram_user_id: int, odoo_user_data: Dict[str, Any]) -> str:
        """
        Create a new user session
        
        Args:
            telegram_user_id: Telegram user ID
            odoo_user_data: Odoo user information
            
        Returns:
            session_token: Unique session token
        """
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Session expires in 24 hours
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Store session
        self.active_sessions[telegram_user_id] = {
            'token': session_token,
            'odoo_user': odoo_user_data,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'last_activity': datetime.now()
        }
        
        logger.info(f"Session created for user {telegram_user_id}, expires at {expires_at}")
        return session_token
    
    def validate_session(self, telegram_user_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate user session
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            (is_valid, user_data)
        """
        session = self.active_sessions.get(telegram_user_id)
        
        if not session:
            return False, None
        
        # Check if session expired
        if datetime.now() > session['expires_at']:
            self.revoke_session(telegram_user_id)
            return False, None
        
        # Update last activity
        session['last_activity'] = datetime.now()
        
        return True, session['odoo_user']
    
    def revoke_session(self, telegram_user_id: int) -> bool:
        """
        Revoke user session
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            success: True if session was revoked
        """
        if telegram_user_id in self.active_sessions:
            del self.active_sessions[telegram_user_id]
            logger.info(f"Session revoked for user {telegram_user_id}")
            return True
        return False
    
    def get_user_info(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information from session
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            user_data: User information or None if not found/expired
        """
        is_valid, user_data = self.validate_session(telegram_user_id)
        return user_data if is_valid else None
    
    def is_authenticated(self, telegram_user_id: int) -> bool:
        """
        Check if user is authenticated
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            bool: True if user is authenticated and session is valid
        """
        is_valid, _ = self.validate_session(telegram_user_id)
        return is_valid
    
    def _is_helpdesk_manager(self, group_data: list) -> bool:
        """Check if user has helpdesk manager permissions"""
        manager_groups = ['Help Desk Manager', 'Helpdesk Manager', 'Administration / Settings']
        for group in group_data:
            if any(manager_group.lower() in group['name'].lower() for manager_group in manager_groups):
                return True
        return False
    
    def _is_helpdesk_user(self, group_data: list) -> bool:
        """Check if user has helpdesk user permissions"""
        user_groups = ['Help Desk User', 'Helpdesk User', 'Help Desk Manager', 'Helpdesk Manager']
        for group in group_data:
            if any(user_group.lower() in group['name'].lower() for user_group in user_groups):
                return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions
        
        Returns:
            count: Number of sessions cleaned up
        """
        now = datetime.now()
        expired_sessions = []
        
        for user_id, session in self.active_sessions.items():
            if now > session['expires_at']:
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            del self.active_sessions[user_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)