"""
Data Transfer Objects (DTOs) for application layer.
These objects transfer data between layers without exposing domain entities.
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from ...domain.entities.ticket import TicketStatus, TicketPriority
from ...domain.entities.comment import CommentType
from ...domain.entities.user import UserRole


@dataclass
class TicketDTO:
    """Data transfer object for Ticket"""
    number: str
    title: str
    description: str
    status: str
    priority: str
    creator_email: str
    assignee_email: Optional[str]
    created_date: datetime
    updated_date: datetime
    resolved_date: Optional[datetime]
    is_overdue: bool
    
    @classmethod
    def from_domain(cls, ticket) -> 'TicketDTO':
        """Create DTO from domain entity"""
        return cls(
            number=ticket.number,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status.value,
            priority=ticket.priority.value,
            creator_email=ticket.creator_email,
            assignee_email=ticket.assignee_email,
            created_date=ticket.created_date,
            updated_date=ticket.updated_date,
            resolved_date=ticket.resolved_date,
            is_overdue=ticket.is_overdue
        )
    
    @property
    def display_title(self) -> str:
        """Get formatted title for display"""
        return f"[{self.number}] {self.title}"
    
    @property
    def status_emoji(self) -> str:
        """Get emoji for status"""
        emoji_map = {
            "Open": "🟢",
            "In Progress": "🟡", 
            "Resolved": "🔵",
            "Closed": "⚫"
        }
        return emoji_map.get(self.status, "❓")
    
    @property
    def priority_emoji(self) -> str:
        """Get emoji for priority"""
        emoji_map = {
            "Low": "🟢",
            "Medium": "🟡",
            "High": "🟠", 
            "Urgent": "🔴"
        }
        return emoji_map.get(self.priority, "❓")


@dataclass
class CommentDTO:
    """Data transfer object for Comment"""
    id: Optional[int]
    ticket_number: str
    content: str
    author_email: str
    comment_type: str
    created_date: datetime
    updated_date: Optional[datetime]
    is_edited: bool
    parent_comment_id: Optional[int]
    is_recent: bool
    display_author: str
    preview_content: str
    
    @classmethod
    def from_domain(cls, comment) -> 'CommentDTO':
        """Create DTO from domain entity"""
        return cls(
            id=comment.id,
            ticket_number=comment.ticket_number,
            content=comment.content,
            author_email=comment.author_email,
            comment_type=comment.comment_type.value,
            created_date=comment.created_date,
            updated_date=comment.updated_date,
            is_edited=comment.is_edited,
            parent_comment_id=comment.parent_comment_id,
            is_recent=comment.is_recent,
            display_author=comment.display_author,
            preview_content=comment.preview_content
        )
    
    @property
    def type_emoji(self) -> str:
        """Get emoji for comment type"""
        emoji_map = {
            "public": "💬",
            "internal": "🔒",
            "system": "🤖"
        }
        return emoji_map.get(self.comment_type, "💬")
    
    @property
    def formatted_date(self) -> str:
        """Get formatted date for display"""
        return self.created_date.strftime("%Y-%m-%d %H:%M")


@dataclass
class UserDTO:
    """Data transfer object for User"""
    email: str
    name: str
    role: str
    is_active: bool
    telegram_user_id: Optional[int]
    telegram_username: Optional[str]
    created_date: datetime
    last_active_date: Optional[datetime]
    display_name: str
    short_email: str
    role_display: str
    
    @classmethod
    def from_domain(cls, user) -> 'UserDTO':
        """Create DTO from domain entity"""
        return cls(
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            telegram_user_id=user.telegram_user_id,
            telegram_username=user.telegram_username,
            created_date=user.created_date,
            last_active_date=user.last_active_date,
            display_name=user.display_name,
            short_email=user.short_email,
            role_display=user.role_display
        )
    
    @property
    def status_emoji(self) -> str:
        """Get emoji for user status"""
        return "🟢" if self.is_active else "⚫"


# Request/Response DTOs for use cases

@dataclass
class ViewCommentsRequest:
    """Request DTO for viewing comments"""
    ticket_number: str
    user_email: str
    comment_type_filter: Optional[str] = None


@dataclass 
class ViewCommentsResponse:
    """Response DTO for viewing comments"""
    ticket: TicketDTO
    comments: List[CommentDTO]
    total_count: int
    user_can_add_comment: bool
    user_can_add_internal_comment: bool


@dataclass
class AddCommentRequest:
    """Request DTO for adding comment"""
    ticket_number: str
    content: str
    author_email: str
    comment_type: str = "public"
    parent_comment_id: Optional[int] = None


@dataclass
class AddCommentResponse:
    """Response DTO for adding comment"""
    comment: CommentDTO
    notification_sent: bool
    success_message: str


@dataclass
class ViewTicketsRequest:
    """Request DTO for viewing tickets"""
    user_email: str
    status_filter: Optional[str] = None
    priority_filter: Optional[str] = None
    limit: int = 10


@dataclass
class ViewTicketsResponse:
    """Response DTO for viewing tickets"""
    tickets: List[TicketDTO]
    total_count: int
    has_more: bool


@dataclass
class GetTicketDetailsRequest:
    """Request DTO for getting ticket details"""
    ticket_number: str
    user_email: str


@dataclass
class GetTicketDetailsResponse:
    """Response DTO for getting ticket details"""
    ticket: TicketDTO
    user_can_modify: bool
    user_can_view_comments: bool
    user_can_add_comments: bool
    comment_count: int