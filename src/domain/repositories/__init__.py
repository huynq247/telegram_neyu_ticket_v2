"""
Repository interfaces for domain entities.
These are abstract interfaces defining contracts for data access.
Implementations will be in the infrastructure layer.
"""

from .ticket_repository import TicketRepository
from .comment_repository import CommentRepository
from .user_repository import UserRepository

__all__ = [
    'TicketRepository',
    'CommentRepository', 
    'UserRepository'
]