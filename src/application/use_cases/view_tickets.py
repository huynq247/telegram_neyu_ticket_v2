"""
Use case for viewing tickets with filtering and pagination.
Contains business logic for ticket listing and access control.
"""
from typing import List, Optional
from ..dto import (
    ViewTicketsRequest,
    ViewTicketsResponse, 
    GetTicketDetailsRequest,
    GetTicketDetailsResponse,
    TicketDTO
)
from ...domain.repositories import TicketRepository, CommentRepository, UserRepository
from ...domain.services import TicketDomainService
from ...domain.entities.ticket import TicketStatus, TicketPriority
from ...domain.entities.user import UserRole


class ViewTicketsUseCase:
    """Use case for viewing and searching tickets"""
    
    def __init__(
        self,
        ticket_repository: TicketRepository,
        comment_repository: CommentRepository,
        user_repository: UserRepository
    ):
        self.ticket_repository = ticket_repository
        self.comment_repository = comment_repository
        self.user_repository = user_repository
    
    async def execute(self, request: ViewTicketsRequest) -> ViewTicketsResponse:
        """Execute the view tickets use case"""
        
        # 1. Get the requesting user
        user = await self.user_repository.get_by_email(request.user_email)
        if not user:
            raise ValueError(f"User {request.user_email} not found")
        
        # 2. Validate filters
        status_filter = None
        if request.status_filter:
            try:
                status_filter = TicketStatus(request.status_filter)
            except ValueError:
                raise ValueError(f"Invalid status filter: {request.status_filter}")
        
        priority_filter = None
        if request.priority_filter:
            try:
                priority_filter = TicketPriority(request.priority_filter)
            except ValueError:
                raise ValueError(f"Invalid priority filter: {request.priority_filter}")
        
        # 3. Get tickets based on user role and permissions
        if user.can_view_all_tickets():
            # Admin/Manager can see all tickets
            if status_filter:
                tickets = await self.ticket_repository.get_tickets_by_status(status_filter, request.limit)
            else:
                # Get recent tickets across all users
                tickets = await self._get_all_recent_tickets(request.limit)
        else:
            # Regular users and agents see their own tickets
            tickets = await self.ticket_repository.get_recent_tickets(request.user_email, request.limit)
        
        # 4. Apply additional filters
        if priority_filter:
            tickets = [t for t in tickets if t.priority == priority_filter]
        
        # 5. Filter tickets user can actually access
        accessible_tickets = []
        for ticket in tickets:
            if TicketDomainService.can_user_access_ticket(user, ticket):
                accessible_tickets.append(ticket)
        
        # 6. Convert to DTOs
        ticket_dtos = [TicketDTO.from_domain(ticket) for ticket in accessible_tickets]
        
        # 7. Get total count for pagination
        total_count = await self._get_total_accessible_ticket_count(user)
        
        # 8. Determine if there are more tickets
        has_more = len(accessible_tickets) == request.limit
        
        return ViewTicketsResponse(
            tickets=ticket_dtos,
            total_count=total_count,
            has_more=has_more
        )
    
    async def get_ticket_details(self, request: GetTicketDetailsRequest) -> GetTicketDetailsResponse:
        """Get detailed information about a specific ticket"""
        
        # 1. Get the ticket
        ticket = await self.ticket_repository.get_by_number(request.ticket_number)
        if not ticket:
            raise ValueError(f"Ticket {request.ticket_number} not found")
        
        # 2. Get the requesting user
        user = await self.user_repository.get_by_email(request.user_email)
        if not user:
            raise ValueError(f"User {request.user_email} not found")
        
        # 3. Check access permissions
        if not TicketDomainService.can_user_access_ticket(user, ticket):
            raise PermissionError("User cannot access this ticket")
        
        # 4. Get additional information
        can_modify = TicketDomainService.can_user_modify_ticket(user, ticket)
        can_view_comments = True  # If user can access ticket, they can view comments
        can_add_comments = can_view_comments  # Same logic for now
        
        # 5. Get comment count
        comment_count = await self.comment_repository.get_comment_count_by_ticket(request.ticket_number)
        
        # 6. Convert to DTO
        ticket_dto = TicketDTO.from_domain(ticket)
        
        return GetTicketDetailsResponse(
            ticket=ticket_dto,
            user_can_modify=can_modify,
            user_can_view_comments=can_view_comments,
            user_can_add_comments=can_add_comments,
            comment_count=comment_count
        )
    
    async def search_tickets(
        self, 
        user_email: str, 
        query: str, 
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        limit: int = 20
    ) -> List[TicketDTO]:
        """Search tickets with filters"""
        
        # 1. Get the requesting user
        user = await self.user_repository.get_by_email(user_email)
        if not user:
            raise ValueError(f"User {user_email} not found")
        
        # 2. Validate filters
        status_enum = None
        if status_filter:
            try:
                status_enum = TicketStatus(status_filter)
            except ValueError:
                raise ValueError(f"Invalid status filter: {status_filter}")
        
        priority_enum = None
        if priority_filter:
            try:
                priority_enum = TicketPriority(priority_filter)
            except ValueError:
                raise ValueError(f"Invalid priority filter: {priority_filter}")
        
        # 3. Search tickets
        tickets = await self.ticket_repository.search_tickets(
            query=query,
            user_email=user_email,
            status_filter=status_enum,
            priority_filter=priority_enum,
            limit=limit
        )
        
        # 4. Filter by user permissions
        accessible_tickets = []
        for ticket in tickets:
            if TicketDomainService.can_user_access_ticket(user, ticket):
                accessible_tickets.append(TicketDTO.from_domain(ticket))
        
        return accessible_tickets
    
    async def get_ticket_summary_for_user(self, user_email: str) -> dict:
        """Get summary statistics for user's tickets"""
        user = await self.user_repository.get_by_email(user_email)
        if not user:
            raise ValueError(f"User {user_email} not found")
        
        # Get ticket counts by status
        status_counts = await self.ticket_repository.get_ticket_count_by_status(user_email)
        
        # Get overdue tickets
        if user.role in [UserRole.AGENT, UserRole.ADMIN, UserRole.MANAGER]:
            overdue_tickets = await self.ticket_repository.get_overdue_tickets(user_email)
        else:
            overdue_tickets = await self.ticket_repository.get_overdue_tickets()
            # Filter to only tickets user can see
            user_overdue = []
            for ticket in overdue_tickets:
                if TicketDomainService.can_user_access_ticket(user, ticket):
                    user_overdue.append(ticket)
            overdue_tickets = user_overdue
        
        return {
            'status_counts': status_counts,
            'overdue_count': len(overdue_tickets),
            'overdue_tickets': [TicketDTO.from_domain(t) for t in overdue_tickets[:5]],  # Top 5
            'total_accessible': sum(status_counts.values()),
            'user_role': user.role.value
        }
    
    async def _get_all_recent_tickets(self, limit: int) -> List:
        """Get recent tickets across all users (admin/manager only)"""
        # This would need a repository method to get all recent tickets
        # For now, get by status
        open_tickets = await self.ticket_repository.get_tickets_by_status(TicketStatus.OPEN, limit // 2)
        in_progress_tickets = await self.ticket_repository.get_tickets_by_status(TicketStatus.IN_PROGRESS, limit // 2)
        
        all_tickets = open_tickets + in_progress_tickets
        
        # Sort by updated date
        all_tickets.sort(key=lambda t: t.updated_date, reverse=True)
        
        return all_tickets[:limit]
    
    async def _get_total_accessible_ticket_count(self, user) -> int:
        """Get total count of tickets user can access"""
        # This is a simplified implementation
        # In a real system, this would be more sophisticated
        if user.can_view_all_tickets():
            # Admin/Manager - count all tickets
            status_counts = await self.ticket_repository.get_ticket_count_by_status("")
            return sum(status_counts.values()) if status_counts else 0
        else:
            # Regular user/agent - count their tickets
            status_counts = await self.ticket_repository.get_ticket_count_by_status(user.email)
            return sum(status_counts.values()) if status_counts else 0