"""
Abstract repository interface for Ticket entity.
Defines the contract for ticket data access operations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.ticket import Ticket, TicketStatus, TicketPriority


class TicketRepository(ABC):
    """Abstract repository interface for Ticket entity"""
    
    @abstractmethod
    async def get_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Get ticket by number"""
        pass
    
    @abstractmethod
    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ID"""
        pass
    
    @abstractmethod
    async def get_tickets_by_creator(self, creator_email: str, limit: int = 50) -> List[Ticket]:
        """Get tickets created by user"""
        pass
    
    @abstractmethod
    async def get_tickets_by_assignee(self, assignee_email: str, limit: int = 50) -> List[Ticket]:
        """Get tickets assigned to user"""
        pass
    
    @abstractmethod
    async def get_recent_tickets(self, user_email: str, limit: int = 10) -> List[Ticket]:
        """Get user's recent tickets (created or assigned)"""
        pass
    
    @abstractmethod
    async def get_tickets_by_status(self, status: TicketStatus, limit: int = 50) -> List[Ticket]:
        """Get tickets by status"""
        pass
    
    @abstractmethod
    async def get_overdue_tickets(self, assignee_email: Optional[str] = None) -> List[Ticket]:
        """Get overdue tickets, optionally filtered by assignee"""
        pass
    
    @abstractmethod
    async def search_tickets(
        self, 
        query: str, 
        user_email: str,
        status_filter: Optional[TicketStatus] = None,
        priority_filter: Optional[TicketPriority] = None,
        limit: int = 20
    ) -> List[Ticket]:
        """Search tickets by title/description"""
        pass
    
    @abstractmethod
    async def save(self, ticket: Ticket) -> Ticket:
        """Save ticket (create or update)"""
        pass
    
    @abstractmethod
    async def delete(self, ticket_number: str) -> bool:
        """Delete ticket by number"""
        pass
    
    @abstractmethod
    async def get_ticket_count_by_status(self, user_email: str) -> dict:
        """Get count of tickets by status for user"""
        pass