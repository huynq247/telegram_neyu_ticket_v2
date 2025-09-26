"""
Smart Authentication File Manager
Handles user.auth.smart file for smart authentication with file-based credentials
"""
import json
import base64
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SmartAuthFileManager:
    """Manage smart auth users from user.auth.smart file"""
    
    def __init__(self, file_path: str = "user.auth.smart"):
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
        self._users_cache = None
        self._last_modified = None
        
    def load_users(self) -> Dict:
        """Load users from file with caching"""
        try:
            # Check if file exists
            if not os.path.exists(self.file_path):
                self.logger.warning(f"Smart auth file {self.file_path} not found")
                return {}
            
            # Check if file was modified
            current_modified = os.path.getmtime(self.file_path)
            
            # Use cache if file not modified
            if (self._users_cache is not None and 
                self._last_modified == current_modified):
                return self._users_cache
            
            # Load from file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate file format
            if 'users' not in data:
                self.logger.error(f"Invalid smart auth file format: missing 'users' key")
                return {}
            
            self._users_cache = data.get('users', {})
            self._last_modified = current_modified
            
            self.logger.info(f"Loaded {len(self._users_cache)} smart auth users from {self.file_path}")
            return self._users_cache
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in smart auth file: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading smart auth file: {e}")
            return {}
    
    def get_credentials(self, telegram_user) -> Tuple[Optional[str], Optional[str]]:
        """Get email and password for telegram user"""
        users = self.load_users()
        
        if not users:
            return None, None
        
        # Try by username first
        username = telegram_user.username
        if username and username in users:
            user_config = users[username]
            
            # Check if user is active
            if user_config.get('active', True):
                email = user_config.get('email')
                encoded_password = user_config.get('encoded_password')
                
                if not email or not encoded_password:
                    self.logger.error(f"Missing email or password for user {username}")
                    return None, None
                
                try:
                    # Decode password
                    password = base64.b64decode(encoded_password).decode('utf-8')
                    
                    # Update last_used timestamp
                    self._update_last_used(username)
                    
                    self.logger.info(f"Retrieved credentials for user {username} ({email})")
                    return email, password
                    
                except Exception as e:
                    self.logger.error(f"Error decoding password for {username}: {e}")
                    return None, None
            else:
                self.logger.info(f"User {username} is disabled in smart auth")
                return None, None
        
        # Try by telegram_id if username not found
        telegram_id = telegram_user.id
        for username, user_config in users.items():
            if (user_config.get('telegram_id') == telegram_id and 
                user_config.get('active', True)):
                
                email = user_config.get('email')
                encoded_password = user_config.get('encoded_password')
                
                if not email or not encoded_password:
                    continue
                
                try:
                    password = base64.b64decode(encoded_password).decode('utf-8')
                    self._update_last_used(username)
                    
                    self.logger.info(f"Retrieved credentials for user ID {telegram_id} -> {username} ({email})")
                    return email, password
                    
                except Exception as e:
                    self.logger.error(f"Error decoding password for user ID {telegram_id}: {e}")
                    continue
        
        self.logger.info(f"No smart auth credentials found for user: {username} (ID: {telegram_id})")
        return None, None
    
    def _update_last_used(self, username: str):
        """Update last_used timestamp for user"""
        try:
            # Load full file
            if not os.path.exists(self.file_path):
                return
                
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update timestamp
            if username in data.get('users', {}):
                data['users'][username]['last_used'] = datetime.now().isoformat()
                data['updated_at'] = datetime.now().isoformat()
                
                # Save back
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                # Clear cache to reload next time
                self._users_cache = None
                
                self.logger.debug(f"Updated last_used timestamp for {username}")
                
        except Exception as e:
            self.logger.error(f"Error updating last_used for {username}: {e}")
    
    def is_user_active(self, username: str) -> bool:
        """Check if user is active"""
        users = self.load_users()
        return users.get(username, {}).get('active', False)
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get full user info"""
        users = self.load_users()
        return users.get(username)
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Get user info by Telegram ID"""
        users = self.load_users()
        for username, user_config in users.items():
            if user_config.get('telegram_id') == telegram_id:
                return {
                    'username': username,
                    **user_config
                }
        return None
    
    def list_active_users(self) -> Dict[str, Dict]:
        """List all active users"""
        users = self.load_users()
        return {
            username: user_config 
            for username, user_config in users.items() 
            if user_config.get('active', True)
        }
    
    def get_user_credentials_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user credentials by email for auth_service compatibility
        
        Args:
            email: User's email address
            
        Returns:
            User credentials dictionary or None
        """
        users = self.load_users()
        
        # In our JSON structure, users are indexed by email directly
        if email in users:
            return {
                'username': email,
                'email': email,  # Add email field explicitly
                **users[email]
            }
        
        # Fallback: search for user with explicit email field
        for username, user_data in users.items():
            if user_data.get('email') == email:
                return {
                    'username': username,
                    'email': email,
                    **user_data
                }
        
        return None
    
    def verify_password_by_email(self, email: str, password: str) -> bool:
        """
        Verify password for user by email
        
        Args:
            email: User's email
            password: Plain text password to verify
            
        Returns:
            True if password matches
        """
        try:
            user_data = self.get_user_credentials_by_email(email)
            if not user_data:
                return False
            
            # Get encoded password
            encoded_password = user_data.get('encoded_password') or user_data.get('password')
            if not encoded_password:
                return False
            
            # Decode and compare
            stored_password = self.decode_password(encoded_password)
            return stored_password == password
            
        except Exception as e:
            self.logger.error(f"Password verification error for {email}: {e}")
            return False
    
    def get_user_type(self, email: str) -> Optional[str]:
        """
        Get user type for smart auth user
        
        Args:
            email: User's email
            
        Returns:
            User type string or None
        """
        user_data = self.get_user_credentials_by_email(email)
        if user_data:
            return user_data.get('user_type', 'portal_user')  # Default to portal_user
        return None
    
    def is_admin_helpdesk_user(self, email: str) -> bool:
        """
        Check if user is admin/helpdesk type
        
        Args:
            email: User's email
            
        Returns:
            True if admin/helpdesk user
        """
        user_type = self.get_user_type(email)
        return user_type == 'admin_helpdesk'
    
    def is_portal_user(self, email: str) -> bool:
        """
        Check if user is portal type
        
        Args:
            email: User's email
            
        Returns:
            True if portal user
        """
        user_type = self.get_user_type(email)
        return user_type == 'portal_user'
    
    @staticmethod
    def encode_password(password: str) -> str:
        """Encode password for storage"""
        return base64.b64encode(password.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def decode_password(encoded_password: str) -> str:
        """Decode password from storage"""
        return base64.b64decode(encoded_password).decode('utf-8')