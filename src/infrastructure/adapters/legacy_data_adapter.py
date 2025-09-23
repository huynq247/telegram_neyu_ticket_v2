"""
Legacy data adapter service.
Handles mapping between legacy Odoo database structure and new Clean Architecture entities.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from ...domain.entities.comment import Comment, CommentType
from ...domain.entities.user import User, UserRole
from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class LegacyDataAdapter:
    """Adapter for mapping legacy Odoo data to domain entities"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize legacy data adapter
        
        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection
    
    def map_legacy_ticket_status(self, stage_id: Optional[int]) -> TicketStatus:
        """
        Map legacy Odoo stage_id to TicketStatus enum
        
        Args:
            stage_id: Legacy stage ID from Odoo
            
        Returns:
            TicketStatus enum value
        """
        # Odoo helpdesk stage mapping
        stage_mapping = {
            1: TicketStatus.OPEN,      # New
            2: TicketStatus.IN_PROGRESS, # In Progress
            3: TicketStatus.RESOLVED,   # Solved/Waiting
            4: TicketStatus.CLOSED,     # Done
            5: TicketStatus.CANCELLED,  # Cancelled
        }
        
        return stage_mapping.get(stage_id, TicketStatus.OPEN)
    
    def map_legacy_ticket_priority(self, priority_str: Optional[str]) -> TicketPriority:
        """
        Map legacy Odoo priority string to TicketPriority enum
        
        Args:
            priority_str: Legacy priority string
            
        Returns:
            TicketPriority enum value
        """
        if not priority_str:
            return TicketPriority.MEDIUM
        
        priority_mapping = {
            '0': TicketPriority.LOW,
            '1': TicketPriority.MEDIUM,
            '2': TicketPriority.HIGH,
            '3': TicketPriority.URGENT,
            'low': TicketPriority.LOW,
            'medium': TicketPriority.MEDIUM,
            'high': TicketPriority.HIGH,
            'urgent': TicketPriority.URGENT,
        }
        
        return priority_mapping.get(priority_str.lower(), TicketPriority.MEDIUM)
    
    def map_legacy_comment_type(self, message_type: Optional[str], subtype_id: Optional[int]) -> CommentType:
        """
        Map legacy Odoo mail_message type to CommentType enum
        
        Args:
            message_type: Legacy message type
            subtype_id: Legacy subtype ID
            
        Returns:
            CommentType enum value
        """
        # Odoo mail message types
        if message_type == 'comment':
            return CommentType.PUBLIC
        elif message_type == 'notification':
            return CommentType.INTERNAL
        elif subtype_id in [1, 2]:  # Common internal subtypes
            return CommentType.INTERNAL
        else:
            return CommentType.PUBLIC
    
    def legacy_ticket_to_domain(self, legacy_row: Dict[str, Any]) -> Optional[Ticket]:
        """
        Convert legacy database row to Ticket domain entity
        
        Args:
            legacy_row: Raw database row from legacy table
            
        Returns:
            Ticket domain entity or None if conversion fails
        """
        try:
            # Handle different legacy table structures
            ticket_number = legacy_row.get('number') or legacy_row.get('name') or f"TKT-{legacy_row.get('id')}"
            title = legacy_row.get('name') or legacy_row.get('subject') or 'Untitled Ticket'
            description = legacy_row.get('description') or legacy_row.get('body') or ''
            
            # Clean HTML from description if present
            description = self._clean_html(description)
            
            # Map status
            stage_id = legacy_row.get('stage_id') or legacy_row.get('state_id')
            status = self.map_legacy_ticket_status(stage_id)
            
            # Map priority
            priority_str = legacy_row.get('priority') or '1'
            priority = self.map_legacy_ticket_priority(priority_str)
            
            # Get email
            creator_email = (
                legacy_row.get('partner_email') or 
                legacy_row.get('email_from') or 
                legacy_row.get('user_email') or 
                'unknown@example.com'
            )
            
            # Get timestamps
            created_at = legacy_row.get('create_date') or datetime.now()
            updated_at = legacy_row.get('write_date') or created_at
            
            # Create domain entity
            ticket = Ticket(
                number=ticket_number,
                title=title,
                description=description,
                status=status,
                priority=priority,
                creator_email=creator_email,
                created_at=created_at,
                updated_at=updated_at
            )
            
            # Set ID if available
            if 'id' in legacy_row:
                ticket.id = legacy_row['id']
            
            return ticket
            
        except Exception as e:
            logger.error(f"Error converting legacy ticket: {e}")
            return None
    
    def legacy_comment_to_domain(self, legacy_row: Dict[str, Any]) -> Optional[Comment]:
        """
        Convert legacy mail_message row to Comment domain entity
        
        Args:
            legacy_row: Raw database row from legacy mail_message table
            
        Returns:
            Comment domain entity or None if conversion fails
        """
        try:
            # Get ticket number/ID
            ticket_number = legacy_row.get('res_id')  # Odoo res_id points to ticket
            if isinstance(ticket_number, int):
                ticket_number = f"TKT-{ticket_number}"
            
            # Get content
            content = legacy_row.get('body') or legacy_row.get('content') or ''
            content = self._clean_html(content)
            
            if not content.strip():
                return None  # Skip empty comments
            
            # Get author email
            author_email = (
                legacy_row.get('email_from') or 
                legacy_row.get('author_email') or 
                'system@example.com'
            )
            
            # Map comment type
            message_type = legacy_row.get('message_type')
            subtype_id = legacy_row.get('subtype_id')
            comment_type = self.map_legacy_comment_type(message_type, subtype_id)
            
            # Get timestamps
            created_at = legacy_row.get('create_date') or datetime.now()
            updated_at = legacy_row.get('write_date') or created_at
            
            # Create domain entity
            comment = Comment(
                ticket_number=ticket_number,
                content=content,
                author_email=author_email,
                comment_type=comment_type,
                created_at=created_at,
                updated_at=updated_at
            )
            
            # Set ID if available
            if 'id' in legacy_row:
                comment.id = legacy_row['id']
            
            return comment
            
        except Exception as e:
            logger.error(f"Error converting legacy comment: {e}")
            return None
    
    def _clean_html(self, html_content: str) -> str:
        """
        Clean HTML tags from content (simple implementation)
        
        Args:
            html_content: HTML content string
            
        Returns:
            Plain text content
        """
        if not html_content:
            return ''
        
        # Simple HTML tag removal
        import re
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        
        # Replace HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
        }
        
        for entity, replacement in html_entities.items():
            clean_text = clean_text.replace(entity, replacement)
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text.strip())
        
        return clean_text
    
    async def migrate_legacy_tickets(self, limit: int = 100) -> List[Ticket]:
        """
        Migrate tickets from legacy Odoo tables to domain entities
        
        Args:
            limit: Maximum number of tickets to migrate
            
        Returns:
            List of migrated Ticket entities
        """
        try:
            # Try different common Odoo table structures
            possible_queries = [
                # Standard Odoo helpdesk table
                """
                SELECT id, name, number, description, stage_id, priority,
                       partner_email, create_date, write_date
                FROM helpdesk_ticket 
                ORDER BY create_date DESC 
                LIMIT $1
                """,
                
                # Alternative helpdesk table structure
                """
                SELECT id, name, description, state_id as stage_id, priority,
                       email_from as partner_email, create_date, write_date
                FROM project_issue
                ORDER BY create_date DESC 
                LIMIT $1
                """,
                
                # Generic ticket table
                """
                SELECT id, name, subject as name, body as description, 
                       stage_id, priority, email_from as partner_email,
                       create_date, write_date
                FROM mail_thread
                WHERE model = 'helpdesk.ticket'
                ORDER BY create_date DESC 
                LIMIT $1
                """
            ]
            
            migrated_tickets = []
            
            async with self.db_connection.get_connection() as conn:
                for query in possible_queries:
                    try:
                        rows = await conn.fetch(query, limit)
                        
                        for row in rows:
                            ticket = self.legacy_ticket_to_domain(dict(row))
                            if ticket:
                                migrated_tickets.append(ticket)
                        
                        if migrated_tickets:
                            logger.info(f"Successfully migrated {len(migrated_tickets)} tickets using query")
                            break
                            
                    except Exception as e:
                        logger.debug(f"Query failed, trying next: {e}")
                        continue
            
            return migrated_tickets[:limit]  # Ensure we don't exceed limit
            
        except Exception as e:
            logger.error(f"Error migrating legacy tickets: {e}")
            return []
    
    async def migrate_legacy_comments(self, ticket_number: str) -> List[Comment]:
        """
        Migrate comments for a specific ticket from legacy tables
        
        Args:
            ticket_number: Ticket number to get comments for
            
        Returns:
            List of migrated Comment entities
        """
        try:
            # Extract ticket ID from number
            ticket_id = ticket_number.split('-')[-1] if '-' in ticket_number else ticket_number
            
            query = """
            SELECT id, res_id, body, message_type, subtype_id,
                   email_from, create_date, write_date
            FROM mail_message 
            WHERE model = 'helpdesk.ticket' AND res_id = $1
            ORDER BY create_date ASC
            """
            
            migrated_comments = []
            
            async with self.db_connection.get_connection() as conn:
                rows = await conn.fetch(query, int(ticket_id))
                
                for row in rows:
                    comment = self.legacy_comment_to_domain(dict(row))
                    if comment:
                        migrated_comments.append(comment)
            
            logger.info(f"Migrated {len(migrated_comments)} comments for ticket {ticket_number}")
            return migrated_comments
            
        except Exception as e:
            logger.error(f"Error migrating legacy comments for {ticket_number}: {e}")
            return []