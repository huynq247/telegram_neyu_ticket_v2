"""
Abstract repository interface for Comment entity.
Defines the contract for comment data access operations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.comment import Comment, CommentType


class CommentRepository(ABC):
    """Abstract repository interface for Comment entity"""
    
    @abstractmethod
    async def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        pass
    
    @abstractmethod
    async def get_by_ticket_number(
        self, 
        ticket_number: str, 
        user_email: str,
        comment_type_filter: Optional[CommentType] = None
    ) -> List[Comment]:
        """Get comments for a ticket, filtered by user permissions"""
        pass
    
    @abstractmethod
    async def get_recent_comments(self, user_email: str, limit: int = 10) -> List[Comment]:
        """Get user's recent comments"""
        pass
    
    @abstractmethod
    async def get_comments_by_author(self, author_email: str, limit: int = 50) -> List[Comment]:
        """Get comments by author"""
        pass
    
    @abstractmethod
    async def get_threaded_comments(self, parent_comment_id: int) -> List[Comment]:
        """Get replies to a comment (threaded comments)"""
        pass
    
    @abstractmethod
    async def save(self, comment: Comment) -> Comment:
        """Save comment (create or update)"""
        pass
    
    @abstractmethod
    async def delete(self, comment_id: int) -> bool:
        """Delete comment by ID"""
        pass
    
    @abstractmethod
    async def get_comment_count_by_ticket(self, ticket_number: str) -> int:
        """Get count of comments for a ticket"""
        pass
    
    @abstractmethod
    async def search_comments(
        self, 
        query: str, 
        user_email: str,
        ticket_number: Optional[str] = None,
        limit: int = 20
    ) -> List[Comment]:
        """Search comments by content"""
        pass