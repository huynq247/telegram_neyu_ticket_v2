"""
Odoo Authentication Service Module
Handle user authentication with Odoo and session management
"""
import logging
import os
import secrets
import xmlrpc.client
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from enum import Enum

class UserType(Enum):
    """User type classification based on authentication method and permissions"""
    ADMIN_HELPDESK = "admin_helpdesk"  # XML-RPC authenticated with admin/helpdesk permissions
    PORTAL_USER = "portal_user"        # Web portal authenticated users

logger = logging.getLogger(__name__)

class OdooAuthService:
    """Service to handle Odoo user authentication and session management"""
    
    def __init__(self, odoo_xmlrpc_url: str, odoo_db: str):
        """
        Initialize Odoo Authentication Service
        
        Args:
            odoo_xmlrpc_url: Odoo XML-RPC server URL (port 8069)
            odoo_db: Odoo database name
        """
        self.odoo_xmlrpc_url = odoo_xmlrpc_url
        self.odoo_db = odoo_db
        
        # XML-RPC endpoints - Direct use of XML-RPC URL
        self.xmlrpc_url = odoo_xmlrpc_url
        self.common_endpoint = f'{self.xmlrpc_url}/xmlrpc/2/common'
        self.object_endpoint = f'{self.xmlrpc_url}/xmlrpc/2/object'
        
        logger.info(f"Using XML-RPC URL: {self.xmlrpc_url}")
        
        # Session storage (in production, use Redis or database)
        self.active_sessions = {}
        
    async def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user with Odoo credentials and classify user type
        
        Args:
            email: User's Odoo email
            password: User's Odoo password
            
        Returns:
            (success, user_data_with_type, error_message)
        """
        try:
            logger.info(f"Attempting authentication for user: {email}")
            
            # Try XML-RPC authentication first (for admin/helpdesk users)
            success, user_data, error = self._try_xmlrpc_auth(email, password)
            if success:
                # Add user type classification for XML-RPC users
                user_data['user_type'] = UserType.ADMIN_HELPDESK.value
                user_data['auth_method'] = 'xml-rpc'
                user_data['auth_timestamp'] = datetime.now().isoformat()
                
                logger.info(f"XML-RPC authentication successful for {email} - classified as ADMIN_HELPDESK")
                return success, user_data, error
            else:
                logger.warning(f"XML-RPC authentication failed for {email}: {error}")
                
                # Fallback: Try web portal authentication (for portal users)
                portal_success, portal_user_data, portal_error = await self._try_web_portal_auth(email, password)
                if portal_success:
                    # Add user type classification for portal users
                    portal_user_data['user_type'] = UserType.PORTAL_USER.value
                    portal_user_data['auth_method'] = 'web-portal'
                    portal_user_data['auth_timestamp'] = datetime.now().isoformat()
                    
                    logger.info(f"Web portal authentication successful for {email} - classified as PORTAL_USER")
                    return portal_success, portal_user_data, portal_error
                else:
                    logger.warning(f"All authentication methods failed for {email}")
                    return False, None, error or "Invalid email or password"
            
            # COMMENTED OUT - Fallback authentication no longer needed
            # fallback_users = self._get_fallback_users()
            # 
            # if email in fallback_users and password == "Neyu@2025":
            #     logger.info(f"Using fallback authentication for {email}")
            #     return True, fallback_users[email], None
            # 
            # # If no fallback user found, return authentication failure
            # logger.warning(f"Authentication failed for {email} - not in fallback users or wrong password")
            # return False, None, "Invalid email or password"
            
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return False, None, "Authentication failed due to system error"
    
    # COMMENTED OUT - Fallback authentication no longer needed with XML-RPC working
    # def _get_fallback_users(self) -> Dict[str, Dict[str, Any]]:
    #     """
    #     Get fallback users for authentication when XML-RPC is not available
    #     Easy to extend for new users
    #     
    #     Returns:
    #         Dictionary of fallback users with email as key
    #     """
    #     return {
    #         "huy.nguyen@neyu.co": {
    #             'uid': 1,
    #             'name': 'Huy Nguyen',
    #             'email': 'huy.nguyen@neyu.co',
    #             'login': 'huy.nguyen@neyu.co',
    #             'partner_id': 1,
    #             'company_id': 1,
    #             'groups': ['IT Services', 'Help Desk Manager'],
    #             'is_helpdesk_manager': True,
    #             'is_helpdesk_user': True
    #         },
    #         "huy.nguyen@ultrafresh.asia": {
    #             'uid': 3,
    #             'name': 'Huy Nguyen (Ultrafresh)',
    #             'email': 'huy.nguyen@ultrafresh.asia',
    #             'login': 'huy.nguyen@ultrafresh.asia',
    #             'partner_id': 3,
    #             'company_id': 1,
    #             'groups': ['IT Services', 'Help Desk Manager'],
    #             'is_helpdesk_manager': True,
    #             'is_helpdesk_user': True
    #         },
    #         "eric.tra@neyu.co": {
    #             'uid': 2,
    #             'name': 'Eric Tra',
    #             'email': 'eric.tra@neyu.co',
    #             'login': 'eric.tra@neyu.co',
    #             'partner_id': 2,
    #             'company_id': 1,
    #             'groups': ['Help Desk User'],
    #             'is_helpdesk_manager': False,
    #             'is_helpdesk_user': True
    #         },
    #         # Easy to add more users here when needed:
    #         # "new.user@company.com": {
    #         #     'uid': 4,
    #         #     'name': 'New User',
    #         #     'email': 'new.user@company.com',
    #         #     'login': 'new.user@company.com',
    #         #     'partner_id': 4,
    #         #     'company_id': 1,
    #         #     'groups': ['Help Desk User'],
    #         #     'is_helpdesk_manager': False,
    #         #     'is_helpdesk_user': True
    #         # }
    #     }
    
    def _try_xmlrpc_auth(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Try XML-RPC authentication with multiple endpoints
        
        Returns:
            (success, user_data, error_message)
        """
        endpoints_to_try = [
            (self.common_endpoint, self.object_endpoint),  # Direct port 8069
        ]
        
        last_error = "XML-RPC connection failed"
        
        for common_endpoint, object_endpoint in endpoints_to_try:
            try:
                logger.info(f"Trying XML-RPC authentication via: {common_endpoint}")
                
                # Connect to Odoo common endpoint
                common = xmlrpc.client.ServerProxy(common_endpoint)
                
                # Authenticate with Odoo
                uid = common.authenticate(self.odoo_db, email, password, {})
                
                if not uid:
                    logger.warning(f"Authentication failed for user: {email}")
                    return False, None, "Invalid email or password"
                
                # Get user information
                models = xmlrpc.client.ServerProxy(object_endpoint)
                
                user_data = models.execute_kw(
                    self.odoo_db, uid, password,
                    'res.users', 'read', [uid],
                    {
                        'fields': [
                            'name', 'email', 'login', 'partner_id', 
                            'groups_id', 'company_id', 'active'
                        ]
                    }
                )
                
                if not user_data or not user_data[0].get('active'):
                    logger.warning(f"User account inactive: {email}")
                    return False, None, "User account is inactive"
                
                user_info = user_data[0]
                
                # Get user groups for permissions
                group_data = models.execute_kw(
                    self.odoo_db, uid, password,
                    'res.groups', 'read', [user_info['groups_id']],
                    {'fields': ['name', 'category_id']}
                )
                
                # Format user data
                formatted_user = {
                    'uid': uid,
                    'name': user_info['name'],
                    'email': user_info['email'],
                    'login': user_info['login'],
                    'partner_id': user_info['partner_id'][0] if user_info['partner_id'] else None,
                    'company_id': user_info['company_id'][0] if user_info['company_id'] else None,
                    'groups': [group['name'] for group in group_data],
                    'is_helpdesk_manager': self._is_helpdesk_manager(group_data),
                    'is_helpdesk_user': self._is_helpdesk_user(group_data)
                }
                
                logger.info(f"XML-RPC authentication successful for user: {email} via {common_endpoint}")
                return True, formatted_user, None
                
            except xmlrpc.client.Fault as e:
                logger.error(f"Odoo XML-RPC error via {common_endpoint}: {e}")
                last_error = f"XML-RPC service error: {e}"
                continue
                
            except Exception as e:
                logger.error(f"Connection error via {common_endpoint}: {e}")
                last_error = f"Connection failed: {e}"
                continue
        
        # All endpoints failed
        return False, None, last_error
    
    def get_user_type_from_data(self, user_data: Dict[str, Any]) -> UserType:
        """
        Get user type from user data
        
        Args:
            user_data: User data from authentication
            
        Returns:
            UserType enum value
        """
        user_type_str = user_data.get('user_type', UserType.PORTAL_USER.value)
        try:
            return UserType(user_type_str)
        except ValueError:
            return UserType.PORTAL_USER
    
    def is_admin_helpdesk_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Check if user is admin or helpdesk user (XML-RPC authenticated)
        
        Args:
            user_data: User data from authentication
            
        Returns:
            True if admin/helpdesk user, False otherwise
        """
        return self.get_user_type_from_data(user_data) == UserType.ADMIN_HELPDESK
    
    def is_portal_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Check if user is portal user (web portal authenticated)
        
        Args:
            user_data: User data from authentication
            
        Returns:
            True if portal user, False otherwise
        """
        return self.get_user_type_from_data(user_data) == UserType.PORTAL_USER
    
    async def _try_web_portal_auth(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Try web portal authentication using Odoo web login endpoint
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            (success, user_data, error_message)
        """
        try:
            import asyncio
            import json
            import urllib.request
            import urllib.parse
            import urllib.error
            
            logger.info(f"Attempting web portal authentication for user: {email}")
            
            # Get Odoo URL from config
            odoo_web_url = os.getenv('ODOO_XMLRPC_URL', 'http://61.28.236.114:8069')
            
            # Use asyncio to run sync request in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._sync_web_portal_request, odoo_web_url, email, password
            )
            
            if result['success']:
                user_data = {
                    'uid': result['uid'],
                    'name': result.get('name', email.split('@')[0].title()),
                    'email': email,
                    'login': email,
                    'partner_id': result.get('partner_id'),
                    'company_id': result.get('company_id', 1),
                    'groups': result.get('groups', []),
                    'is_helpdesk_manager': self._check_helpdesk_manager_from_groups(result.get('groups', [])),
                    'is_helpdesk_user': self._check_helpdesk_user_from_groups(result.get('groups', []))
                }
                
                logger.info(f"Web portal authentication successful for user: {email}")
                return True, user_data, None
            else:
                logger.warning(f"Web portal authentication failed for {email}: {result.get('error')}")
                return False, None, result.get('error', 'Web portal authentication failed')
        except Exception as e:
            logger.error(f"Web portal authentication error for {email}: {e}")
            return False, None, f"Web portal authentication failed: {e}"
    
    def _sync_web_portal_request(self, odoo_web_url: str, email: str, password: str) -> Dict[str, Any]:
        """
        Synchronous web portal authentication request
        """
        try:
            import json
            import urllib.request
            import urllib.parse
            import urllib.error
            
            # Try different approaches
            approaches = [
                {
                    'endpoint': f"{odoo_web_url}/web/session/authenticate",
                    'data': {
                        'jsonrpc': '2.0',
                        'method': 'call',
                        'params': {
                            'db': self.odoo_db,
                            'login': email,
                            'password': password
                        },
                        'id': 1
                    }
                },
                {
                    'endpoint': f"{odoo_web_url}/jsonrpc",
                    'data': {
                        'jsonrpc': '2.0',
                        'method': 'call',
                        'params': {
                            'service': 'common',
                            'method': 'authenticate',
                            'args': [self.odoo_db, email, password, {}]
                        },
                        'id': 1
                    }
                }
            ]
            
            for i, approach in enumerate(approaches):
                try:
                    endpoint = approach['endpoint']
                    login_data = approach['data']
                    
                    # Convert to JSON
                    json_data = json.dumps(login_data).encode('utf-8')
                    
                    # Create request
                    req = urllib.request.Request(
                        endpoint,
                        data=json_data,
                        headers={
                            'Content-Type': 'application/json',
                            'Content-Length': len(json_data)
                        }
                    )
                    
                    # Make request
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            response_text = response.read().decode('utf-8')
                            result = json.loads(response_text)
                            
                            # Check if authentication successful
                            if result.get('result') and isinstance(result['result'], int) and result['result'] > 0:
                                uid = result['result']
                                
                                # Get user info (simplified)
                                logger.info(f"Web portal authentication successful for user: {email} via {endpoint}")
                                return {
                                    'success': True,
                                    'uid': uid,
                                    'name': email.split('@')[0].title(),
                                    'partner_id': None,
                                    'company_id': 1,
                                    'groups': ['Portal User']  # Default for portal users
                                }
                        
                except urllib.error.URLError as e:
                    logger.error(f"Web portal connection error via {endpoint}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Web portal request error via {endpoint}: {e}")
                    continue
            
            return {'success': False, 'error': 'All web portal endpoints failed'}
            
        except Exception as e:
            logger.error(f"Sync web portal request error: {e}")
            return {'success': False, 'error': f'Request failed: {e}'}
    
    def _check_helpdesk_manager_from_groups(self, groups: list) -> bool:
        """Check if user is helpdesk manager from group names"""
        helpdesk_manager_groups = ['Help Desk Manager', 'Helpdesk Manager', 'Support Manager']
        return any(group in helpdesk_manager_groups for group in groups if group)
    
    def _check_helpdesk_user_from_groups(self, groups: list) -> bool:
        """Check if user is helpdesk user from group names"""  
        helpdesk_user_groups = ['Help Desk User', 'Helpdesk User', 'Support User', 'Support Team']
        return any(group in helpdesk_user_groups for group in groups if group)
    
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