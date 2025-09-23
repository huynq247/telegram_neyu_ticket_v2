"""
PostgreSQL implementation of TicketRepository.
Moves database-specific logic to infrastructure layer.
"""
from typing import List, Optional
from datetime import datetime
import asyncpg
from ...domain.repositories import TicketRepository
from ...domain.entities.ticket import Ticket, TicketStatus, TicketPriority


class PostgreSQLTicketRepository(TicketRepository):
    """PostgreSQL implementation of TicketRepository"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    async def get_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Get ticket by number"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE number = $1
            """
            row = await conn.fetchrow(query, ticket_number)
            
            if not row:
                return None
            
            return self._row_to_ticket(row)
    
    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ID"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE id = $1
            """
            row = await conn.fetchrow(query, ticket_id)
            
            if not row:
                return None
            
            return self._row_to_ticket(row)
    
    async def get_tickets_by_creator(self, creator_email: str, limit: int = 50) -> List[Ticket]:
        """Get tickets created by user"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE create_uid_email = $1
                ORDER BY create_date DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, creator_email, limit)
            
            return [self._row_to_ticket(row) for row in rows]
    
    async def get_tickets_by_assignee(self, assignee_email: str, limit: int = 50) -> List[Ticket]:
        """Get tickets assigned to user"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE user_id_email = $1
                ORDER BY create_date DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, assignee_email, limit)
            
            return [self._row_to_ticket(row) for row in rows]
    
    async def get_recent_tickets(self, user_email: str, limit: int = 10) -> List[Ticket]:
        """Get user's recent tickets (created or assigned)"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE create_uid_email = $1 OR user_id_email = $1
                ORDER BY write_date DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, user_email, limit)
            
            return [self._row_to_ticket(row) for row in rows]
    
    async def get_tickets_by_status(self, status: TicketStatus, limit: int = 50) -> List[Ticket]:
        """Get tickets by status"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE state = $1
                ORDER BY create_date DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, status.value, limit)
            
            return [self._row_to_ticket(row) for row in rows]
    
    async def get_overdue_tickets(self, assignee_email: Optional[str] = None) -> List[Ticket]:
        """Get overdue tickets, optionally filtered by assignee"""
        async with self.pool.acquire() as conn:
            base_query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE state NOT IN ('Resolved', 'Closed')
            """
            
            if assignee_email:
                query = base_query + " AND user_id_email = $1 ORDER BY create_date ASC"
                rows = await conn.fetch(query, assignee_email)
            else:
                query = base_query + " ORDER BY create_date ASC"
                rows = await conn.fetch(query)
            
            # Filter overdue tickets using business logic
            tickets = [self._row_to_ticket(row) for row in rows]
            return [ticket for ticket in tickets if ticket.is_overdue]
    
    async def search_tickets(
        self, 
        query: str, 
        user_email: str,
        status_filter: Optional[TicketStatus] = None,
        priority_filter: Optional[TicketPriority] = None,
        limit: int = 20
    ) -> List[Ticket]:
        """Search tickets by title/description"""
        async with self.pool.acquire() as conn:
            base_query = """
                SELECT number, subject as title, description, state as status, 
                       priority, create_uid_email as creator_email, 
                       user_id_email as assignee_email, create_date, 
                       write_date as updated_date, date_closed as resolved_date
                FROM helpdesk_ticket 
                WHERE (create_uid_email = $1 OR user_id_email = $1)
                  AND (subject ILIKE $2 OR description ILIKE $2)
            """
            
            params = [user_email, f"%{query}%"]
            param_count = 2
            
            if status_filter:
                param_count += 1
                base_query += f" AND state = ${param_count}"
                params.append(status_filter.value)
            
            if priority_filter:
                param_count += 1
                base_query += f" AND priority = ${param_count}"
                params.append(priority_filter.value)
            
            param_count += 1
            base_query += f" ORDER BY write_date DESC LIMIT ${param_count}"
            params.append(limit)
            
            rows = await conn.fetch(base_query, *params)
            
            return [self._row_to_ticket(row) for row in rows]
    
    async def save(self, ticket: Ticket) -> Ticket:
        """Save ticket (create or update)"""
        async with self.pool.acquire() as conn:
            # Check if ticket exists
            existing = await self.get_by_number(ticket.number)
            
            if existing:
                # Update existing ticket
                query = """
                    UPDATE helpdesk_ticket 
                    SET subject = $1, description = $2, state = $3, 
                        priority = $4, user_id_email = $5, write_date = $6,
                        date_closed = $7
                    WHERE number = $8
                """
                await conn.execute(
                    query,
                    ticket.title,
                    ticket.description, 
                    ticket.status.value,
                    ticket.priority.value,
                    ticket.assignee_email,
                    ticket.updated_date,
                    ticket.resolved_date,
                    ticket.number
                )
            else:
                # Create new ticket
                query = """
                    INSERT INTO helpdesk_ticket 
                    (number, subject, description, state, priority, 
                     create_uid_email, user_id_email, create_date, write_date)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                await conn.execute(
                    query,
                    ticket.number,
                    ticket.title,
                    ticket.description,
                    ticket.status.value,
                    ticket.priority.value,
                    ticket.creator_email,
                    ticket.assignee_email,
                    ticket.created_date,
                    ticket.updated_date
                )
            
            return ticket
    
    async def delete(self, ticket_number: str) -> bool:
        """Delete ticket by number"""
        async with self.pool.acquire() as conn:
            query = "DELETE FROM helpdesk_ticket WHERE number = $1"
            result = await conn.execute(query, ticket_number)
            return result == "DELETE 1"
    
    async def get_ticket_count_by_status(self, user_email: str) -> dict:
        """Get count of tickets by status for user"""
        async with self.pool.acquire() as conn:
            if user_email:
                query = """
                    SELECT state, COUNT(*) as count
                    FROM helpdesk_ticket 
                    WHERE create_uid_email = $1 OR user_id_email = $1
                    GROUP BY state
                """
                rows = await conn.fetch(query, user_email)
            else:
                query = """
                    SELECT state, COUNT(*) as count
                    FROM helpdesk_ticket 
                    GROUP BY state
                """
                rows = await conn.fetch(query)
            
            return {row['state']: row['count'] for row in rows}
    
    def _row_to_ticket(self, row) -> Ticket:
        """Convert database row to Ticket entity"""
        return Ticket(
            number=row['number'],
            title=row['title'] or '',
            description=row['description'] or '',
            status=TicketStatus(row['status']) if row['status'] else TicketStatus.OPEN,
            priority=TicketPriority(row['priority']) if row['priority'] else TicketPriority.MEDIUM,
            creator_email=row['creator_email'] or '',
            assignee_email=row['assignee_email'],
            created_date=row['create_date'] if row['create_date'] else datetime.now(),
            updated_date=row['updated_date'] if row['updated_date'] else datetime.now(),
            resolved_date=row['resolved_date']
        )