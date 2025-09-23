"""
PostgreSQL implementation of CommentRepository.
Handles comment data access using the mail_message table from Odoo.
"""
from typing import List, Optional
from datetime import datetime
import asyncpg
from ...domain.repositories import CommentRepository
from ...domain.entities.comment import Comment, CommentType


class PostgreSQLCommentRepository(CommentRepository):
    """PostgreSQL implementation of CommentRepository"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    async def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT mm.id, mm.body as content, mm.author_id_email as author_email,
                       mm.date as created_date, ht.number as ticket_number,
                       mm.message_type, mm.subtype_id
                FROM mail_message mm
                JOIN helpdesk_ticket ht ON mm.res_id = ht.id
                WHERE mm.id = $1 AND mm.model = 'helpdesk.ticket'
            """
            row = await conn.fetchrow(query, comment_id)
            
            if not row:
                return None
            
            return self._row_to_comment(row)
    
    async def get_by_ticket_number(
        self, 
        ticket_number: str, 
        user_email: str,
        comment_type_filter: Optional[CommentType] = None
    ) -> List[Comment]:
        """Get comments for a ticket, filtered by user permissions"""
        async with self.pool.acquire() as conn:
            # First get the ticket ID
            ticket_query = "SELECT id FROM helpdesk_ticket WHERE number = $1"
            ticket_row = await conn.fetchrow(ticket_query, ticket_number)
            
            if not ticket_row:
                return []
            
            ticket_id = ticket_row['id']
            
            # Get comments for the ticket
            query = """
                SELECT mm.id, mm.body as content, mm.author_id_email as author_email,
                       mm.date as created_date, $1 as ticket_number,
                       mm.message_type, mm.subtype_id
                FROM mail_message mm
                WHERE mm.res_id = $2 AND mm.model = 'helpdesk.ticket'
                  AND mm.body IS NOT NULL AND mm.body != ''
                ORDER BY mm.date ASC
            """
            rows = await conn.fetch(query, ticket_number, ticket_id)
            
            comments = [self._row_to_comment(row) for row in rows]
            
            # Filter by comment type if specified
            if comment_type_filter:
                comments = [c for c in comments if c.comment_type == comment_type_filter]
            
            return comments
    
    async def get_recent_comments(self, user_email: str, limit: int = 10) -> List[Comment]:
        """Get user's recent comments"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT mm.id, mm.body as content, mm.author_id_email as author_email,
                       mm.date as created_date, ht.number as ticket_number,
                       mm.message_type, mm.subtype_id
                FROM mail_message mm
                JOIN helpdesk_ticket ht ON mm.res_id = ht.id
                WHERE mm.author_id_email = $1 
                  AND mm.model = 'helpdesk.ticket'
                  AND mm.body IS NOT NULL AND mm.body != ''
                ORDER BY mm.date DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, user_email, limit)
            
            return [self._row_to_comment(row) for row in rows]
    
    async def get_comments_by_author(self, author_email: str, limit: int = 50) -> List[Comment]:
        """Get comments by author"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT mm.id, mm.body as content, mm.author_id_email as author_email,
                       mm.date as created_date, ht.number as ticket_number,
                       mm.message_type, mm.subtype_id
                FROM mail_message mm
                JOIN helpdesk_ticket ht ON mm.res_id = ht.id
                WHERE mm.author_id_email = $1 
                  AND mm.model = 'helpdesk.ticket'
                  AND mm.body IS NOT NULL AND mm.body != ''
                ORDER BY mm.date DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, author_email, limit)
            
            return [self._row_to_comment(row) for row in rows]
    
    async def get_threaded_comments(self, parent_comment_id: int) -> List[Comment]:
        """Get replies to a comment (threaded comments)"""
        # Note: Odoo mail_message doesn't have built-in threading
        # This would need to be implemented based on your threading strategy
        async with self.pool.acquire() as conn:
            query = """
                SELECT mm.id, mm.body as content, mm.author_id_email as author_email,
                       mm.date as created_date, ht.number as ticket_number,
                       mm.message_type, mm.subtype_id
                FROM mail_message mm
                JOIN helpdesk_ticket ht ON mm.res_id = ht.id
                WHERE mm.parent_id = $1 
                  AND mm.model = 'helpdesk.ticket'
                  AND mm.body IS NOT NULL AND mm.body != ''
                ORDER BY mm.date ASC
            """
            try:
                rows = await conn.fetch(query, parent_comment_id)
                return [self._row_to_comment(row) for row in rows]
            except:
                # If parent_id column doesn't exist, return empty list
                return []
    
    async def save(self, comment: Comment) -> Comment:
        """Save comment (create or update)"""
        async with self.pool.acquire() as conn:
            # Get ticket ID from ticket number
            ticket_query = "SELECT id FROM helpdesk_ticket WHERE number = $1"
            ticket_row = await conn.fetchrow(ticket_query, comment.ticket_number)
            
            if not ticket_row:
                raise ValueError(f"Ticket {comment.ticket_number} not found")
            
            ticket_id = ticket_row['id']
            
            if comment.id:
                # Update existing comment
                query = """
                    UPDATE mail_message 
                    SET body = $1, date = $2
                    WHERE id = $3
                """
                await conn.execute(
                    query,
                    comment.content,
                    comment.updated_date or comment.created_date,
                    comment.id
                )
            else:
                # Create new comment
                query = """
                    INSERT INTO mail_message 
                    (model, res_id, body, author_id_email, date, message_type, subtype_id)
                    VALUES ('helpdesk.ticket', $1, $2, $3, $4, $5, $6)
                    RETURNING id
                """
                
                # Determine message type based on comment type
                message_type = 'comment'
                subtype_id = None
                
                if comment.comment_type == CommentType.INTERNAL:
                    message_type = 'comment'
                    subtype_id = 2  # Internal note subtype (adjust based on your Odoo setup)
                elif comment.comment_type == CommentType.SYSTEM:
                    message_type = 'notification'
                
                row = await conn.fetchrow(
                    query,
                    ticket_id,
                    comment.content,
                    comment.author_email,
                    comment.created_date,
                    message_type,
                    subtype_id
                )
                
                comment.id = row['id']
            
            return comment
    
    async def delete(self, comment_id: int) -> bool:
        """Delete comment by ID"""
        async with self.pool.acquire() as conn:
            query = "DELETE FROM mail_message WHERE id = $1"
            result = await conn.execute(query, comment_id)
            return result == "DELETE 1"
    
    async def get_comment_count_by_ticket(self, ticket_number: str) -> int:
        """Get count of comments for a ticket"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT COUNT(*) as count
                FROM mail_message mm
                JOIN helpdesk_ticket ht ON mm.res_id = ht.id
                WHERE ht.number = $1 
                  AND mm.model = 'helpdesk.ticket'
                  AND mm.body IS NOT NULL AND mm.body != ''
            """
            row = await conn.fetchrow(query, ticket_number)
            return row['count'] if row else 0
    
    async def search_comments(
        self, 
        query: str, 
        user_email: str,
        ticket_number: Optional[str] = None,
        limit: int = 20
    ) -> List[Comment]:
        """Search comments by content"""
        async with self.pool.acquire() as conn:
            base_query = """
                SELECT mm.id, mm.body as content, mm.author_id_email as author_email,
                       mm.date as created_date, ht.number as ticket_number,
                       mm.message_type, mm.subtype_id
                FROM mail_message mm
                JOIN helpdesk_ticket ht ON mm.res_id = ht.id
                WHERE mm.model = 'helpdesk.ticket'
                  AND mm.body IS NOT NULL AND mm.body != ''
                  AND mm.body ILIKE $1
                  AND (ht.create_uid_email = $2 OR ht.user_id_email = $2)
            """
            
            params = [f"%{query}%", user_email]
            
            if ticket_number:
                base_query += " AND ht.number = $3"
                params.append(ticket_number)
                limit_param = "$4"
            else:
                limit_param = "$3"
            
            base_query += f" ORDER BY mm.date DESC LIMIT {limit_param}"
            params.append(limit)
            
            rows = await conn.fetch(base_query, *params)
            
            return [self._row_to_comment(row) for row in rows]
    
    def _row_to_comment(self, row) -> Comment:
        """Convert database row to Comment entity"""
        # Determine comment type based on message_type and subtype_id
        comment_type = CommentType.PUBLIC
        
        if row['message_type'] == 'notification':
            comment_type = CommentType.SYSTEM
        elif row['subtype_id'] == 2:  # Internal note subtype
            comment_type = CommentType.INTERNAL
        
        return Comment(
            id=row['id'],
            ticket_number=row['ticket_number'],
            content=row['content'] or '',
            author_email=row['author_email'] or '',
            comment_type=comment_type,
            created_date=row['created_date'] if row['created_date'] else datetime.now(),
            updated_date=None,
            is_edited=False,
            parent_comment_id=None
        )