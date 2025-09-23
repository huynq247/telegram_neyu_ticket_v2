"""
Abstract repository interface for User entity.
Defines the contract for user data access operations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.user import User, UserRole


class UserRepository(ABC):
    """Abstract repository interface for User entity"""
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID"""
        pass
    
    @abstractmethod
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        pass
    
    @abstractmethod
    async def get_active_agents(self) -> List[User]:
        """Get active support agents"""
        pass
    
    @abstractmethod
    async def get_all_users(self, include_inactive: bool = False) -> List[User]:
        """Get all users"""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save user (create or update)"""
        pass
    
    @abstractmethod
    async def delete(self, email: str) -> bool:
        """Delete user by email"""
        pass
    
    @abstractmethod
    async def exists(self, email: str) -> bool:
        """Check if user exists"""
        pass
    
    @abstractmethod
    async def link_telegram_account(self, email: str, telegram_user_id: int, telegram_username: str) -> bool:
        """Link Telegram account to existing user"""
        pass