"""
Application layer exports.
Provides use cases and DTOs for the application layer.
"""

# Export DTOs
from .dto import (
    TicketDTO,
    CommentDTO, 
    UserDTO,
    ViewCommentsRequest,
    ViewCommentsResponse,
    AddCommentRequest,
    AddCommentResponse,
    ViewTicketsRequest,
    ViewTicketsResponse,
    GetTicketDetailsRequest,
    GetTicketDetailsResponse
)

# Export Use Cases
from .use_cases.view_comments import ViewCommentsUseCase
from .use_cases.add_comment import AddCommentUseCase
from .use_cases.view_tickets import ViewTicketsUseCase

__all__ = [
    # DTOs
    'TicketDTO',
    'CommentDTO',
    'UserDTO', 
    'ViewCommentsRequest',
    'ViewCommentsResponse',
    'AddCommentRequest',
    'AddCommentResponse',
    'ViewTicketsRequest',
    'ViewTicketsResponse',
    'GetTicketDetailsRequest',
    'GetTicketDetailsResponse',
    
    # Use Cases
    'ViewCommentsUseCase',
    'AddCommentUseCase',
    'ViewTicketsUseCase'
]