"""
Domain services for complex business logic that doesn't belong to a single entity.
These services coordinate between entities and enforce business rules.
"""
from typing import List, Optional
from ..entities.ticket import Ticket, TicketStatus, TicketPriority
from ..entities.comment import Comment, CommentType
from ..entities.user import User, UserRole


class TicketDomainService:
    """Domain service for ticket-related business logic"""
    
    @staticmethod
    def can_user_access_ticket(user: User, ticket: Ticket) -> bool:
        """Determine if user can access a ticket"""
        return user.can_view_ticket(ticket.creator_email, ticket.assignee_email)
    
    @staticmethod
    def can_user_modify_ticket(user: User, ticket: Ticket) -> bool:
        """Determine if user can modify a ticket"""
        return user.can_modify_ticket(ticket.creator_email, ticket.assignee_email)
    
    @staticmethod
    def get_next_assignee(ticket: Ticket, available_agents: List[User]) -> Optional[User]:
        """Business logic for auto-assigning tickets"""
        if not available_agents:
            return None
        
        # Filter active agents
        active_agents = [agent for agent in available_agents if agent.is_active and agent.role == UserRole.AGENT]
        
        if not active_agents:
            return None
        
        # Simple round-robin assignment (in real app, this could be more sophisticated)
        # For now, return first available agent
        return active_agents[0]
    
    @staticmethod
    def calculate_priority_from_keywords(title: str, description: str) -> TicketPriority:
        """Auto-calculate priority based on content keywords"""
        content = f"{title} {description}".lower()
        
        # Urgent keywords
        urgent_keywords = ["urgent", "critical", "down", "outage", "emergency", "asap"]
        if any(keyword in content for keyword in urgent_keywords):
            return TicketPriority.URGENT
        
        # High priority keywords
        high_keywords = ["high", "important", "priority", "soon", "broken"]
        if any(keyword in content for keyword in high_keywords):
            return TicketPriority.HIGH
        
        # Low priority keywords
        low_keywords = ["low", "minor", "later", "when possible", "enhancement"]
        if any(keyword in content for keyword in low_keywords):
            return TicketPriority.LOW
        
        # Default to medium priority
        return TicketPriority.MEDIUM
    
    @staticmethod
    def should_auto_escalate(ticket: Ticket) -> bool:
        """Determine if ticket should be auto-escalated"""
        if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return False
        
        # Business rule: escalate if high/urgent priority and overdue
        if ticket.priority in [TicketPriority.HIGH, TicketPriority.URGENT] and ticket.is_overdue:
            return True
        
        return False
    
    @staticmethod
    def get_allowed_status_transitions(current_status: TicketStatus, user_role: UserRole) -> List[TicketStatus]:
        """Get allowed status transitions based on current status and user role"""
        transitions = {
            TicketStatus.OPEN: {
                UserRole.AGENT: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED],
                UserRole.ADMIN: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED],
                UserRole.MANAGER: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED]
            },
            TicketStatus.IN_PROGRESS: {
                UserRole.AGENT: [TicketStatus.OPEN, TicketStatus.RESOLVED],
                UserRole.ADMIN: [TicketStatus.OPEN, TicketStatus.RESOLVED, TicketStatus.CLOSED],
                UserRole.MANAGER: [TicketStatus.OPEN, TicketStatus.RESOLVED, TicketStatus.CLOSED]
            },
            TicketStatus.RESOLVED: {
                UserRole.USER: [TicketStatus.OPEN],  # Users can reopen resolved tickets
                UserRole.AGENT: [TicketStatus.OPEN, TicketStatus.CLOSED],
                UserRole.ADMIN: [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.CLOSED],
                UserRole.MANAGER: [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.CLOSED]
            },
            TicketStatus.CLOSED: {
                UserRole.ADMIN: [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED],
                UserRole.MANAGER: [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED]
            }
        }
        
        return transitions.get(current_status, {}).get(user_role, [])


class CommentDomainService:
    """Domain service for comment-related business logic"""
    
    @staticmethod
    def can_user_view_comment(user: User, comment: Comment, ticket: Ticket) -> bool:
        """Determine if user can view a specific comment"""
        # Check if user can access the ticket first
        if not TicketDomainService.can_user_access_ticket(user, ticket):
            return False
        
        # Check comment-specific permissions
        user_is_assignee = ticket.assignee_email == user.email
        return comment.can_be_viewed_by(user.email, user_is_assignee)
    
    @staticmethod
    def can_user_add_comment(user: User, ticket: Ticket, comment_type: CommentType) -> bool:
        """Determine if user can add a comment to a ticket"""
        # User must be able to access the ticket
        if not TicketDomainService.can_user_access_ticket(user, ticket):
            return False
        
        # Internal comments can only be added by agents/admins
        if comment_type == CommentType.INTERNAL:
            return user.role in [UserRole.AGENT, UserRole.ADMIN, UserRole.MANAGER]
        
        # System comments can only be added programmatically
        if comment_type == CommentType.SYSTEM:
            return False
        
        # Public comments can be added by anyone with ticket access
        return True
    
    @staticmethod
    def should_notify_on_comment(comment: Comment, ticket: Ticket) -> List[str]:
        """Determine who should be notified when a comment is added"""
        notify_emails = []
        
        # Always notify ticket creator (unless they're the comment author)
        if ticket.creator_email != comment.author_email:
            notify_emails.append(ticket.creator_email)
        
        # Always notify assignee (unless they're the comment author)
        if ticket.assignee_email and ticket.assignee_email != comment.author_email:
            notify_emails.append(ticket.assignee_email)
        
        # For internal comments, don't notify the ticket creator (unless they're admin/agent)
        if comment.comment_type == CommentType.INTERNAL:
            # Remove creator if they're not admin/agent
            # TODO: Check creator's role in real implementation
            pass
        
        return list(set(notify_emails))  # Remove duplicates
    
    @staticmethod
    def filter_comments_by_permissions(
        comments: List[Comment], 
        user: User, 
        ticket: Ticket
    ) -> List[Comment]:
        """Filter comments based on user permissions"""
        filtered_comments = []
        
        for comment in comments:
            if CommentDomainService.can_user_view_comment(user, comment, ticket):
                filtered_comments.append(comment)
        
        return filtered_comments
    
    @staticmethod
    def get_comment_threading_info(comments: List[Comment]) -> dict:
        """Organize comments into threaded structure"""
        threads = {}
        root_comments = []
        
        for comment in comments:
            if comment.parent_comment_id is None:
                root_comments.append(comment)
                threads[comment.id] = []
            else:
                if comment.parent_comment_id not in threads:
                    threads[comment.parent_comment_id] = []
                threads[comment.parent_comment_id].append(comment)
        
        return {
            'root_comments': root_comments,
            'threads': threads
        }


class NotificationDomainService:
    """Domain service for notification business logic"""
    
    @staticmethod
    def should_send_notification(user: User, notification_type: str) -> bool:
        """Determine if notification should be sent to user"""
        if not user.is_active:
            return False
        
        # Business rules for notification preferences
        # TODO: Implement user notification preferences
        return True
    
    @staticmethod
    def get_notification_priority(ticket: Ticket, event_type: str) -> str:
        """Determine notification priority based on ticket and event"""
        if ticket.priority == TicketPriority.URGENT:
            return "high"
        elif ticket.priority == TicketPriority.HIGH:
            return "medium"
        else:
            return "normal"
    
    @staticmethod
    def format_notification_message(ticket: Ticket, event_type: str, **kwargs) -> str:
        """Format notification message based on event type"""
        messages = {
            "ticket_created": f"New ticket created: {ticket.display_title}",
            "ticket_assigned": f"Ticket assigned to you: {ticket.display_title}",
            "ticket_updated": f"Ticket updated: {ticket.display_title}",
            "comment_added": f"New comment on ticket: {ticket.display_title}",
            "status_changed": f"Ticket status changed: {ticket.display_title} -> {ticket.status.value}"
        }
        
        return messages.get(event_type, f"Update on ticket: {ticket.display_title}")