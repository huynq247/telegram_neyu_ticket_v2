"""
Use case for viewing comments on a ticket.
Contains pure business logic for comment viewing with proper authorization.
"""
from typing import List, Optional
from ..dto import (
    ViewCommentsRequest, 
    ViewCommentsResponse, 
    CommentDTO, 
    TicketDTO
)
from ...domain.repositories import TicketRepository, CommentRepository, UserRepository
from ...domain.services import CommentDomainService, TicketDomainService
from ...domain.entities.comment import CommentType
from ...domain.entities.user import UserRole


class ViewCommentsUseCase:
    """Use case for viewing comments on a ticket"""
    
    def __init__(
        self,
        ticket_repository: TicketRepository,
        comment_repository: CommentRepository,
        user_repository: UserRepository
    ):
        self.ticket_repository = ticket_repository
        self.comment_repository = comment_repository
        self.user_repository = user_repository
    
    async def execute(self, request: ViewCommentsRequest) -> ViewCommentsResponse:
        """Execute the view comments use case"""
        
        # 1. Validate and get the ticket
        ticket = await self.ticket_repository.get_by_number(request.ticket_number)
        if not ticket:
            raise ValueError(f"Ticket {request.ticket_number} not found")
        
        # 2. Get the requesting user
        user = await self.user_repository.get_by_email(request.user_email)
        if not user:
            raise ValueError(f"User {request.user_email} not found")
        
        # 3. Check if user can access this ticket
        if not TicketDomainService.can_user_access_ticket(user, ticket):
            raise PermissionError("User cannot access this ticket")
        
        # 4. Get comments for the ticket
        comment_type_filter = None
        if request.comment_type_filter:
            try:
                comment_type_filter = CommentType(request.comment_type_filter)
            except ValueError:
                raise ValueError(f"Invalid comment type: {request.comment_type_filter}")
        
        comments = await self.comment_repository.get_by_ticket_number(
            request.ticket_number,
            request.user_email,
            comment_type_filter
        )
        
        # 5. Filter comments based on user permissions
        filtered_comments = CommentDomainService.filter_comments_by_permissions(
            comments, user, ticket
        )
        
        # 6. Convert domain entities to DTOs
        ticket_dto = TicketDTO.from_domain(ticket)
        comment_dtos = [CommentDTO.from_domain(comment) for comment in filtered_comments]
        
        # 7. Check user permissions for adding comments
        can_add_public_comment = CommentDomainService.can_user_add_comment(
            user, ticket, CommentType.PUBLIC
        )
        can_add_internal_comment = CommentDomainService.can_user_add_comment(
            user, ticket, CommentType.INTERNAL
        )
        
        # 8. Get total comment count (for pagination info)
        total_count = await self.comment_repository.get_comment_count_by_ticket(
            request.ticket_number
        )
        
        return ViewCommentsResponse(
            ticket=ticket_dto,
            comments=comment_dtos,
            total_count=total_count,
            user_can_add_comment=can_add_public_comment,
            user_can_add_internal_comment=can_add_internal_comment
        )
    
    async def get_recent_ticket_numbers_for_user(self, user_email: str, limit: int = 10) -> List[str]:
        """Get recent ticket numbers that user can access"""
        recent_tickets = await self.ticket_repository.get_recent_tickets(user_email, limit)
        return [ticket.number for ticket in recent_tickets]
    
    async def search_tickets_for_comments(
        self, 
        user_email: str, 
        query: str, 
        limit: int = 10
    ) -> List[TicketDTO]:
        """Search tickets that user can access for comment viewing"""
        
        user = await self.user_repository.get_by_email(user_email)
        if not user:
            raise ValueError(f"User {user_email} not found")
        
        # Search tickets
        tickets = await self.ticket_repository.search_tickets(
            query=query,
            user_email=user_email,
            limit=limit
        )
        
        # Filter tickets user can access and convert to DTOs
        accessible_tickets = []
        for ticket in tickets:
            if TicketDomainService.can_user_access_ticket(user, ticket):
                accessible_tickets.append(TicketDTO.from_domain(ticket))
        
        return accessible_tickets