"""
Domain entities, repositories, and services.
This package contains the core business logic with no external dependencies.
"""

# Export main entities
from .entities.ticket import Ticket, TicketStatus, TicketPriority
from .entities.comment import Comment, CommentType
from .entities.user import User, UserRole

# Export repository interfaces
from .repositories import (
    TicketRepository,
    CommentRepository, 
    UserRepository
)

# Export domain services
from .services import (
    TicketDomainService,
    CommentDomainService,
    NotificationDomainService
)

__all__ = [
    # Entities
    'Ticket', 'TicketStatus', 'TicketPriority',
    'Comment', 'CommentType', 
    'User', 'UserRole',
    
    # Repository interfaces
    'TicketRepository',
    'CommentRepository',
    'UserRepository',
    
    # Domain services
    'TicketDomainService',
    'CommentDomainService',
    'NotificationDomainService'
]