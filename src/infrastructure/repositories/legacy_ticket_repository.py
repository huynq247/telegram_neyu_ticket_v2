"""
Legacy repository wrapper that handles both new Clean Architecture tables and legacy Odoo tables.
Provides migration path from old postgresql_connector.py logic.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.repositories.ticket_repository import TicketRepository
from ...domain.repositories.comment_repository import CommentRepository
from ...domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from ...domain.entities.comment import Comment, CommentType
from ..database.connection import DatabaseConnection
from ..database.schema_service import DatabaseSchemaService
from ..adapters.legacy_data_adapter import LegacyDataAdapter

logger = logging.getLogger(__name__)


class LegacyTicketRepository(TicketRepository):
    """Repository that handles both legacy Odoo tables and new clean tables"""
    
    def __init__(self, 
                 db_connection: DatabaseConnection,
                 schema_service: DatabaseSchemaService,
                 legacy_adapter: LegacyDataAdapter):
        """
        Initialize legacy-compatible repository
        
        Args:
            db_connection: Database connection
            schema_service: Schema inspection service
            legacy_adapter: Legacy data adapter
        """
        self.db_connection = db_connection
        self.schema_service = schema_service
        self.legacy_adapter = legacy_adapter
        self._use_legacy_tables = None
    
    async def _detect_table_structure(self) -> bool:
        """
        Detect whether to use legacy Odoo tables or new clean tables
        
        Returns:
            True if should use legacy tables, False for new tables
        """
        if self._use_legacy_tables is not None:
            return self._use_legacy_tables
        
        # Check if new clean tables exist
        has_tickets_table = await self.schema_service.check_table_exists('tickets')
        has_helpdesk_table = await self.schema_service.check_table_exists('helpdesk_ticket')
        
        if has_tickets_table:
            logger.info("Using new clean architecture tables")
            self._use_legacy_tables = False
        elif has_helpdesk_table:
            logger.info("Using legacy Odoo tables")
            self._use_legacy_tables = True
        else:
            logger.warning("No ticket tables found, will attempt to create new tables")
            self._use_legacy_tables = False
        
        return self._use_legacy_tables
    
    async def create(self, ticket: Ticket) -> Ticket:
        """Create a new ticket"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._create_legacy_ticket(ticket)
        else:
            return await self._create_clean_ticket(ticket)
    
    async def _create_clean_ticket(self, ticket: Ticket) -> Ticket:
        """Create ticket in new clean table"""
        try:
            query = """
            INSERT INTO tickets (number, title, description, status, priority, 
                               creator_email, created_at, updated_at, last_activity_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, number, title, description, status, priority, 
                     creator_email, created_at, updated_at, last_activity_at
            """
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    ticket.number,
                    ticket.title,
                    ticket.description,
                    ticket.status.value,
                    ticket.priority.value,
                    ticket.creator_email,
                    ticket.created_at,
                    ticket.updated_at,
                    ticket.last_activity_at or ticket.updated_at
                )
                
                return self._row_to_ticket(dict(row))
                
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            raise Exception(f"Failed to create ticket: {e}")
    
    async def _create_legacy_ticket(self, ticket: Ticket) -> Ticket:
        """Create ticket in legacy Odoo table"""
        try:
            # This would insert into helpdesk_ticket with Odoo-compatible structure
            query = """
            INSERT INTO helpdesk_ticket (name, description, stage_id, priority,
                                       partner_email, create_date, write_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, name, description, stage_id, priority, partner_email, create_date, write_date
            """
            
            # Map clean architecture values to legacy format
            legacy_stage_id = self._status_to_legacy_stage_id(ticket.status)
            legacy_priority = self._priority_to_legacy_priority(ticket.priority)
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    ticket.title,
                    ticket.description,
                    legacy_stage_id,
                    legacy_priority,
                    ticket.creator_email,
                    ticket.created_at,
                    ticket.updated_at
                )
                
                # Convert back to domain entity
                legacy_row = dict(row)
                legacy_row['number'] = f"TKT-{legacy_row['id']}"  # Generate number
                return self.legacy_adapter.legacy_ticket_to_domain(legacy_row)
                
        except Exception as e:
            logger.error(f"Failed to create legacy ticket: {e}")
            raise Exception(f"Failed to create legacy ticket: {e}")
    
    async def get_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Get ticket by number"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._get_legacy_ticket_by_number(ticket_number)
        else:
            return await self._get_clean_ticket_by_number(ticket_number)
    
    async def _get_clean_ticket_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Get ticket from clean table"""
        try:
            query = """
            SELECT id, number, title, description, status, priority,
                   creator_email, assignee_email, created_at, updated_at, last_activity_at
            FROM tickets 
            WHERE number = $1
            """
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(query, ticket_number)
                
                if row:
                    return self._row_to_ticket(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting ticket {ticket_number}: {e}")
            return None
    
    async def _get_legacy_ticket_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Get ticket from legacy Odoo table"""
        try:
            # Try multiple legacy table structures
            queries = [
                """
                SELECT id, name, number, description, stage_id, priority,
                       partner_email, create_date, write_date
                FROM helpdesk_ticket 
                WHERE number = $1
                """,
                """
                SELECT id, name, description, stage_id, priority,
                       partner_email, create_date, write_date
                FROM helpdesk_ticket 
                WHERE id = $1
                """
            ]
            
            # Extract ID from ticket number if needed
            ticket_id = ticket_number.split('-')[-1] if '-' in ticket_number else ticket_number
            
            async with self.db_connection.get_connection() as conn:
                for query in queries:
                    try:
                        row = await conn.fetchrow(query, ticket_number if 'number' in query else int(ticket_id))
                        if row:
                            legacy_row = dict(row)
                            if 'number' not in legacy_row:
                                legacy_row['number'] = f"TKT-{legacy_row['id']}"
                            return self.legacy_adapter.legacy_ticket_to_domain(legacy_row)
                    except Exception:
                        continue
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting legacy ticket {ticket_number}: {e}")
            return None
    
    async def get_recent_tickets(self, user_email: str, limit: int = 10, 
                               status_filter: Optional[TicketStatus] = None) -> List[Ticket]:
        """Get recent tickets for user"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._get_recent_legacy_tickets(user_email, limit, status_filter)
        else:
            return await self._get_recent_clean_tickets(user_email, limit, status_filter)
    
    async def _get_recent_clean_tickets(self, user_email: str, limit: int,
                                      status_filter: Optional[TicketStatus] = None) -> List[Ticket]:
        """Get recent tickets from clean table"""
        try:
            query = """
            SELECT id, number, title, description, status, priority,
                   creator_email, assignee_email, created_at, updated_at, last_activity_at
            FROM tickets 
            WHERE creator_email = $1
            """
            params = [user_email]
            
            if status_filter:
                query += " AND status = $2"
                params.append(status_filter.value)
            
            query += " ORDER BY last_activity_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            async with self.db_connection.get_connection() as conn:
                rows = await conn.fetch(query, *params)
                
                tickets = []
                for row in rows:
                    ticket = self._row_to_ticket(dict(row))
                    if ticket:
                        tickets.append(ticket)
                
                return tickets
                
        except Exception as e:
            logger.error(f"Error getting recent tickets for {user_email}: {e}")
            return []
    
    async def _get_recent_legacy_tickets(self, user_email: str, limit: int,
                                       status_filter: Optional[TicketStatus] = None) -> List[Ticket]:
        """Get recent tickets from legacy table"""
        try:
            # Use legacy adapter to migrate tickets
            migrated_tickets = await self.legacy_adapter.migrate_legacy_tickets(limit * 2)  # Get extra for filtering
            
            # Filter by user email and status
            filtered_tickets = []
            for ticket in migrated_tickets:
                if ticket.creator_email.lower() == user_email.lower():
                    if not status_filter or ticket.status == status_filter:
                        filtered_tickets.append(ticket)
                        if len(filtered_tickets) >= limit:
                            break
            
            return filtered_tickets
            
        except Exception as e:
            logger.error(f"Error getting recent legacy tickets for {user_email}: {e}")
            return []
    
    def _status_to_legacy_stage_id(self, status: TicketStatus) -> int:
        """Convert TicketStatus to legacy Odoo stage_id"""
        mapping = {
            TicketStatus.OPEN: 1,
            TicketStatus.IN_PROGRESS: 2,
            TicketStatus.RESOLVED: 3,
            TicketStatus.CLOSED: 4,
            TicketStatus.CANCELLED: 5,
        }
        return mapping.get(status, 1)
    
    def _priority_to_legacy_priority(self, priority: TicketPriority) -> str:
        """Convert TicketPriority to legacy Odoo priority"""
        mapping = {
            TicketPriority.LOW: '0',
            TicketPriority.MEDIUM: '1',
            TicketPriority.HIGH: '2',
            TicketPriority.URGENT: '3',
        }
        return mapping.get(priority, '1')
    
    def _row_to_ticket(self, row: Dict[str, Any]) -> Ticket:
        """Convert database row to Ticket entity"""
        try:
            # Handle status conversion
            status_value = row.get('status', 'open')
            if isinstance(status_value, str):
                status = TicketStatus(status_value)
            else:
                status = TicketStatus.OPEN
            
            # Handle priority conversion
            priority_value = row.get('priority', 'medium')
            if isinstance(priority_value, str):
                priority = TicketPriority(priority_value)
            else:
                priority = TicketPriority.MEDIUM
            
            ticket = Ticket(
                number=row['number'],
                title=row.get('title', row.get('name', 'Untitled')),
                description=row.get('description', ''),
                status=status,
                priority=priority,
                creator_email=row.get('creator_email', row.get('partner_email', '')),
                assignee_email=row.get('assignee_email'),
                created_at=row.get('created_at', row.get('create_date')),
                updated_at=row.get('updated_at', row.get('write_date')),
                last_activity_at=row.get('last_activity_at')
            )
            
            if 'id' in row:
                ticket.id = row['id']
            
            return ticket
            
        except Exception as e:
            logger.error(f"Error converting row to ticket: {e}")
            raise ValueError(f"Invalid ticket data: {e}")
    
    async def update(self, ticket: Ticket) -> Ticket:
        """Update ticket"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._update_legacy_ticket(ticket)
        else:
            return await self._update_clean_ticket(ticket)
    
    async def _update_clean_ticket(self, ticket: Ticket) -> Ticket:
        """Update ticket in clean table"""
        try:
            query = """
            UPDATE tickets 
            SET title = $2, description = $3, status = $4, priority = $5,
                assignee_email = $6, updated_at = $7, last_activity_at = $8
            WHERE number = $1
            RETURNING id, number, title, description, status, priority,
                     creator_email, assignee_email, created_at, updated_at, last_activity_at
            """
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    ticket.number,
                    ticket.title,
                    ticket.description,
                    ticket.status.value,
                    ticket.priority.value,
                    ticket.assignee_email,
                    datetime.now(),
                    datetime.now()
                )
                
                if not row:
                    raise ValueError(f"Ticket {ticket.number} not found")
                
                return self._row_to_ticket(dict(row))
                
        except Exception as e:
            logger.error(f"Failed to update ticket {ticket.number}: {e}")
            raise Exception(f"Failed to update ticket: {e}")
    
    async def _update_legacy_ticket(self, ticket: Ticket) -> Ticket:
        """Update ticket in legacy table"""
        # Implementation for legacy table updates
        # This would involve more complex Odoo-specific logic
        raise NotImplementedError("Legacy ticket updates require Odoo-specific implementation")
    
    async def delete(self, ticket_number: str) -> bool:
        """Delete ticket"""
        use_legacy = await self._detect_table_structure()
        
        try:
            if use_legacy:
                query = "DELETE FROM helpdesk_ticket WHERE number = $1 OR id = $2"
                ticket_id = ticket_number.split('-')[-1] if '-' in ticket_number else ticket_number
                params = [ticket_number, int(ticket_id)]
            else:
                query = "DELETE FROM tickets WHERE number = $1"
                params = [ticket_number]
            
            async with self.db_connection.get_connection() as conn:
                result = await conn.execute(query, *params)
                
                # Check if any rows were affected
                rows_affected = int(result.split()[-1]) if result else 0
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to delete ticket {ticket_number}: {e}")
            return False
    
    async def search_tickets(self, query: str, user_email: str, limit: int = 10,
                           status_filter: Optional[TicketStatus] = None,
                           priority_filter: Optional[TicketPriority] = None) -> List[Ticket]:
        """Search tickets"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            # For legacy, get all tickets and filter in memory (not ideal but works)
            all_tickets = await self._get_recent_legacy_tickets(user_email, limit * 5)
            
            # Simple text search
            matching_tickets = []
            query_lower = query.lower()
            
            for ticket in all_tickets:
                if (query_lower in ticket.title.lower() or 
                    query_lower in ticket.description.lower()):
                    
                    if status_filter and ticket.status != status_filter:
                        continue
                    if priority_filter and ticket.priority != priority_filter:
                        continue
                    
                    matching_tickets.append(ticket)
                    if len(matching_tickets) >= limit:
                        break
            
            return matching_tickets
        else:
            return await self._search_clean_tickets(query, user_email, limit, status_filter, priority_filter)
    
    async def _search_clean_tickets(self, query: str, user_email: str, limit: int,
                                  status_filter: Optional[TicketStatus] = None,
                                  priority_filter: Optional[TicketPriority] = None) -> List[Ticket]:
        """Search tickets in clean table"""
        try:
            sql_query = """
            SELECT id, number, title, description, status, priority,
                   creator_email, assignee_email, created_at, updated_at, last_activity_at
            FROM tickets 
            WHERE creator_email = $1 
            AND (title ILIKE $2 OR description ILIKE $2)
            """
            params = [user_email, f"%{query}%"]
            
            if status_filter:
                sql_query += f" AND status = ${len(params) + 1}"
                params.append(status_filter.value)
            
            if priority_filter:
                sql_query += f" AND priority = ${len(params) + 1}"
                params.append(priority_filter.value)
            
            sql_query += f" ORDER BY last_activity_at DESC LIMIT ${len(params) + 1}"
            params.append(limit)
            
            async with self.db_connection.get_connection() as conn:
                rows = await conn.fetch(sql_query, *params)
                
                tickets = []
                for row in rows:
                    ticket = self._row_to_ticket(dict(row))
                    if ticket:
                        tickets.append(ticket)
                
                return tickets
                
        except Exception as e:
            logger.error(f"Error searching tickets: {e}")
            return []
    
    async def get_all_tickets(self, limit: Optional[int] = None) -> List[Ticket]:
        """Get all tickets (admin function)"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self.legacy_adapter.migrate_legacy_tickets(limit or 1000)
        else:
            try:
                query = """
                SELECT id, number, title, description, status, priority,
                       creator_email, assignee_email, created_at, updated_at, last_activity_at
                FROM tickets 
                ORDER BY last_activity_at DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                async with self.db_connection.get_connection() as conn:
                    rows = await conn.fetch(query)
                    
                    tickets = []
                    for row in rows:
                        ticket = self._row_to_ticket(dict(row))
                        if ticket:
                            tickets.append(ticket)
                    
                    return tickets
                    
            except Exception as e:
                logger.error(f"Error getting all tickets: {e}")
                return []