"""
User Service Module
Quản lý dữ liệu user và session
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UserService:
    """Service quản lý user data và session"""
    
    def __init__(self):
        # Dictionary để lưu trữ dữ liệu tạm thời của user
        self.user_data = {}
    
    def init_user_data(self, user, chat_id: int) -> None:
        """
        Initialize new user data
        
        Args:
            user: Telegram user object
            chat_id: Chat ID
        """
        self.user_data[user.id] = {
            'chat_id': chat_id,
            'user_id': user.id,
            'username': user.username or user.first_name,
            'first_name': user.first_name
        }
        logger.info(f"Initialized user data for {user.id}")
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Lấy dữ liệu user
        
        Args:
            user_id: User ID
            
        Returns:
            User data dictionary
        """
        return self.user_data.get(user_id, {})
    
    def update_user_data(self, user_id: int, key: str, value: Any) -> None:
        """
        Update user data
        
        Args:
            user_id: User ID
            key: Key to update
            value: New value
        """
        if user_id in self.user_data:
            self.user_data[user_id][key] = value
            logger.debug(f"Updated user {user_id} data: {key} = {value}")
        else:
            logger.warning(f"User {user_id} data not found for update")
    
    def clear_user_data(self, user_id: int) -> None:
        """
        Clear user data
        
        Args:
            user_id: User ID
        """
        if user_id in self.user_data:
            del self.user_data[user_id]
            logger.info(f"Cleared user data for {user_id}")
    
    def has_user_data(self, user_id: int) -> bool:
        """
        Check if user has data
        
        Args:
            user_id: User ID
            
        Returns:
            True if has data
        """
        return user_id in self.user_data
    
    def get_destination_from_callback(self, callback_data: str) -> str:
        """
        Mapping callback data thành destination name
        
        Args:
            callback_data: Callback data từ button
            
        Returns:
            Destination name
        """
        destination_map = {
            'dest_Vietnam': 'Vietnam',
            'dest_Thailand': 'Thailand',
            'dest_India': 'India',
            'dest_Philippines': 'Philippines',
            'dest_Malaysia': 'Malaysia',
            'dest_Indonesia': 'Indonesia'
        }
        return destination_map.get(callback_data, 'Vietnam')