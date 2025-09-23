"""
Infrastructure layer exports.
Contains concrete implementations of repositories and external service adapters.
"""

# Database
from .database.connection import DatabaseConnection, get_database

# Repository implementations
from .repositories.postgresql_ticket_repository import PostgreSQLTicketRepository
from .repositories.postgresql_comment_repository import PostgreSQLCommentRepository

__all__ = [
    # Database
    'DatabaseConnection',
    'get_database',
    
    # Repository implementations  
    'PostgreSQLTicketRepository',
    'PostgreSQLCommentRepository'
]