"""
Comment domain entity with business logic.
Pure domain model with no external dependencies.
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class CommentType(Enum):
    """Comment type enumeration"""
    INTERNAL = "internal"  # Only visible to assignee and admins
    PUBLIC = "public"      # Visible to creator and assignee
    SYSTEM = "system"      # Automatic system comments


@dataclass
class Comment:
    """Comment domain entity with business validation"""
    
    ticket_number: str
    content: str
    author_email: str
    comment_type: CommentType = CommentType.PUBLIC
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: Optional[datetime] = None
    is_edited: bool = False
    parent_comment_id: Optional[int] = None  # For threaded comments
    id: Optional[int] = None  # Set by repository
    
    def __post_init__(self):
        """Validate business rules after initialization"""
        self._validate_ticket_number()
        self._validate_content()
        self._validate_author_email()
    
    def _validate_ticket_number(self) -> None:
        """Validate ticket number format"""
        if not self.ticket_number or not self.ticket_number.strip():
            raise ValueError("Ticket number cannot be empty")
        
        # Business rule: ticket number format (could be TKT-001, HELP-123, etc.)
        if len(self.ticket_number.strip()) < 3:
            raise ValueError("Ticket number must be at least 3 characters")
    
    def _validate_content(self) -> None:
        """Validate comment content"""
        if not self.content or not self.content.strip():
            raise ValueError("Comment content cannot be empty")
        
        # Business rule: minimum content length
        if len(self.content.strip()) < 5:
            raise ValueError("Comment must be at least 5 characters long")
        
        # Business rule: maximum content length
        if len(self.content) > 5000:
            raise ValueError("Comment cannot exceed 5000 characters")
    
    def _validate_author_email(self) -> None:
        """Validate author email"""
        if not self.author_email or "@" not in self.author_email:
            raise ValueError("Valid author email is required")
    
    def edit_content(self, new_content: str, editor_email: str) -> None:
        """Edit comment content with business rules"""
        if not self.can_be_edited_by(editor_email):
            raise PermissionError("User cannot edit this comment")
        
        # Validate new content
        old_content = self.content
        self.content = new_content
        try:
            self._validate_content()
        except ValueError as e:
            # Rollback if validation fails
            self.content = old_content
            raise e
        
        self.is_edited = True
        self.updated_date = datetime.now()
    
    def can_be_viewed_by(self, user_email: str, user_is_assignee: bool = False) -> bool:
        """Business rule: who can view this comment"""
        if self.comment_type == CommentType.SYSTEM:
            return True  # System comments visible to all
        
        if self.comment_type == CommentType.INTERNAL:
            return user_is_assignee or self._is_admin_user(user_email)
        
        # PUBLIC comments visible to author, assignee, and admins
        return (
            self.author_email == user_email or
            user_is_assignee or
            self._is_admin_user(user_email)
        )
    
    def can_be_edited_by(self, user_email: str) -> bool:
        """Business rule: who can edit this comment"""
        if self.comment_type == CommentType.SYSTEM:
            return False  # System comments cannot be edited
        
        # Only author can edit within 24 hours, or admins anytime
        if self._is_admin_user(user_email):
            return True
        
        if self.author_email != user_email:
            return False
        
        # Business rule: comments can only be edited within 24 hours
        if self.created_date:
            hours_since_created = (datetime.now() - self.created_date).total_seconds() / 3600
            return hours_since_created <= 24
        
        return True
    
    def _is_admin_user(self, user_email: str) -> bool:
        """Check if user has admin privileges"""
        # TODO: Implement actual admin check
        admin_domains = ["admin.com", "support.com"]
        return any(domain in user_email for domain in admin_domains)
    
    @property
    def is_recent(self) -> bool:
        """Check if comment was created recently (within last hour)"""
        if not self.created_date:
            return False
        
        hours_since_created = (datetime.now() - self.created_date).total_seconds() / 3600
        return hours_since_created <= 1
    
    @property
    def display_author(self) -> str:
        """Get formatted author name for display"""
        if self.comment_type == CommentType.SYSTEM:
            return "System"
        
        # Extract name from email (before @)
        return self.author_email.split('@')[0].replace('.', ' ').title()
    
    @property
    def preview_content(self) -> str:
        """Get truncated content for preview"""
        if len(self.content) <= 100:
            return self.content
        
        return self.content[:97] + "..."
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'content': self.content,
            'author_email': self.author_email,
            'comment_type': self.comment_type.value,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'is_edited': self.is_edited,
            'parent_comment_id': self.parent_comment_id,
            'is_recent': self.is_recent,
            'display_author': self.display_author,
            'preview_content': self.preview_content
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Comment':
        """Create comment from dictionary"""
        return cls(
            id=data.get('id'),
            ticket_number=data['ticket_number'],
            content=data['content'],
            author_email=data['author_email'],
            comment_type=CommentType(data.get('comment_type', CommentType.PUBLIC.value)),
            created_date=datetime.fromisoformat(data['created_date']),
            updated_date=datetime.fromisoformat(data['updated_date']) if data.get('updated_date') else None,
            is_edited=data.get('is_edited', False),
            parent_comment_id=data.get('parent_comment_id')
        )
    
    @classmethod
    def create_system_comment(cls, ticket_number: str, content: str) -> 'Comment':
        """Factory method for creating system comments"""
        return cls(
            ticket_number=ticket_number,
            content=content,
            author_email="system@internal",
            comment_type=CommentType.SYSTEM
        )
    
    @classmethod
    def create_public_comment(
        cls, 
        ticket_number: str, 
        content: str, 
        author_email: str,
        parent_comment_id: Optional[int] = None
    ) -> 'Comment':
        """Factory method for creating public comments"""
        return cls(
            ticket_number=ticket_number,
            content=content,
            author_email=author_email,
            comment_type=CommentType.PUBLIC,
            parent_comment_id=parent_comment_id
        )
    
    @classmethod
    def create_internal_comment(
        cls, 
        ticket_number: str, 
        content: str, 
        author_email: str
    ) -> 'Comment':
        """Factory method for creating internal comments"""
        return cls(
            ticket_number=ticket_number,
            content=content,
            author_email=author_email,
            comment_type=CommentType.INTERNAL
        )