"""
Legacy comment repository that handles both new and legacy Odoo comment tables.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.repositories.comment_repository import CommentRepository
from ...domain.entities.comment import Comment, CommentType
from ..database.connection import DatabaseConnection
from ..database.schema_service import DatabaseSchemaService
from ..adapters.legacy_data_adapter import LegacyDataAdapter

logger = logging.getLogger(__name__)


class LegacyCommentRepository(CommentRepository):
    """Comment repository with legacy Odoo support"""
    
    def __init__(self, 
                 db_connection: DatabaseConnection,
                 schema_service: DatabaseSchemaService,
                 legacy_adapter: LegacyDataAdapter):
        """
        Initialize legacy-compatible comment repository
        
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
        """Detect whether to use legacy or new tables"""
        if self._use_legacy_tables is not None:
            return self._use_legacy_tables
        
        has_comments_table = await self.schema_service.check_table_exists('comments')
        has_mail_message_table = await self.schema_service.check_table_exists('mail_message')
        
        if has_comments_table:
            logger.info("Using new clean comments table")
            self._use_legacy_tables = False
        elif has_mail_message_table:
            logger.info("Using legacy Odoo mail_message table")
            self._use_legacy_tables = True
        else:
            logger.warning("No comment tables found")
            self._use_legacy_tables = False
        
        return self._use_legacy_tables
    
    async def create(self, comment: Comment) -> Comment:
        """Create a new comment"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._create_legacy_comment(comment)
        else:
            return await self._create_clean_comment(comment)
    
    async def _create_clean_comment(self, comment: Comment) -> Comment:
        """Create comment in new clean table"""
        try:
            query = """
            INSERT INTO comments (ticket_number, content, author_email, comment_type,
                                created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, ticket_number, content, author_email, comment_type,
                     created_at, updated_at
            """
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    comment.ticket_number,
                    comment.content,
                    comment.author_email,
                    comment.comment_type.value,
                    comment.created_at,
                    comment.updated_at
                )
                
                return self._row_to_comment(dict(row))
                
        except Exception as e:
            logger.error(f"Failed to create comment: {e}")
            raise Exception(f"Failed to create comment: {e}")
    
    async def _create_legacy_comment(self, comment: Comment) -> Comment:
        """Create comment in legacy Odoo mail_message table"""
        try:
            # Get ticket ID from ticket number
            ticket_id = await self._get_ticket_id_from_number(comment.ticket_number)
            if not ticket_id:
                raise ValueError(f"Ticket {comment.ticket_number} not found")
            
            # Format content as HTML (Odoo format)
            html_content = f'<div data-oe-version="1.2">{comment.content}</div>'
            
            query = """
            INSERT INTO mail_message (model, res_id, body, message_type, subtype_id,
                                    email_from, create_date, write_date)
            VALUES ('helpdesk.ticket', $1, $2, $3, NULL, $4, $5, $6)
            RETURNING id, res_id, body, message_type, email_from, create_date, write_date
            """
            
            message_type = 'notification' if comment.comment_type == CommentType.INTERNAL else 'comment'
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    ticket_id,
                    html_content,
                    message_type,
                    comment.author_email,
                    comment.created_at,
                    comment.updated_at
                )
                
                # Convert legacy row to domain entity
                legacy_row = dict(row)
                legacy_row['res_id'] = comment.ticket_number  # Use original ticket number
                return self.legacy_adapter.legacy_comment_to_domain(legacy_row)
                
        except Exception as e:
            logger.error(f"Failed to create legacy comment: {e}")
            raise Exception(f"Failed to create legacy comment: {e}")
    
    async def _get_ticket_id_from_number(self, ticket_number: str) -> Optional[int]:
        """Get ticket ID from ticket number for legacy operations"""
        try:
            queries = [
                "SELECT id FROM helpdesk_ticket WHERE number = $1",
                "SELECT id FROM helpdesk_ticket WHERE id = $1"
            ]
            
            ticket_id = ticket_number.split('-')[-1] if '-' in ticket_number else ticket_number
            
            async with self.db_connection.get_connection() as conn:
                for query in queries:
                    try:
                        result = await conn.fetchval(query, ticket_number if 'number' in query else int(ticket_id))
                        if result:
                            return result
                    except Exception:
                        continue
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting ticket ID for {ticket_number}: {e}")
            return None
    
    async def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._get_legacy_comment_by_id(comment_id)
        else:
            return await self._get_clean_comment_by_id(comment_id)
    
    async def _get_clean_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment from clean table"""
        try:
            query = """
            SELECT id, ticket_number, content, author_email, comment_type,
                   created_at, updated_at
            FROM comments 
            WHERE id = $1
            """
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(query, comment_id)
                
                if row:
                    return self._row_to_comment(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting comment {comment_id}: {e}")
            return None
    
    async def _get_legacy_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment from legacy table"""
        try:
            query = """
            SELECT id, res_id, body, message_type, subtype_id,
                   email_from, create_date, write_date
            FROM mail_message 
            WHERE id = $1 AND model = 'helpdesk.ticket'
            """
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(query, comment_id)
                
                if row:
                    return self.legacy_adapter.legacy_comment_to_domain(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting legacy comment {comment_id}: {e}")
            return None
    
    async def get_by_ticket_number(self, ticket_number: str, user_email: str,
                                 comment_type: Optional[CommentType] = None) -> List[Comment]:
        """Get comments for a ticket"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._get_legacy_comments_by_ticket(ticket_number, user_email, comment_type)
        else:
            return await self._get_clean_comments_by_ticket(ticket_number, user_email, comment_type)
    
    async def _get_clean_comments_by_ticket(self, ticket_number: str, user_email: str,
                                          comment_type: Optional[CommentType] = None) -> List[Comment]:
        """Get comments from clean table"""
        try:
            query = """
            SELECT id, ticket_number, content, author_email, comment_type,
                   created_at, updated_at
            FROM comments 
            WHERE ticket_number = $1
            """
            params = [ticket_number]
            
            if comment_type:
                query += " AND comment_type = $2"
                params.append(comment_type.value)
            
            query += " ORDER BY created_at ASC"
            
            async with self.db_connection.get_connection() as conn:
                rows = await conn.fetch(query, *params)
                
                comments = []
                for row in rows:
                    comment = self._row_to_comment(dict(row))
                    if comment and self._user_can_see_comment(comment, user_email):
                        comments.append(comment)
                
                return comments
                
        except Exception as e:
            logger.error(f"Error getting comments for ticket {ticket_number}: {e}")
            return []
    
    async def _get_legacy_comments_by_ticket(self, ticket_number: str, user_email: str,
                                           comment_type: Optional[CommentType] = None) -> List[Comment]:
        """Get comments from legacy table"""
        try:
            # Use legacy adapter to migrate comments
            comments = await self.legacy_adapter.migrate_legacy_comments(ticket_number)
            
            # Filter by comment type and visibility
            filtered_comments = []
            for comment in comments:
                if comment_type and comment.comment_type != comment_type:
                    continue
                
                if self._user_can_see_comment(comment, user_email):
                    filtered_comments.append(comment)
            
            return filtered_comments
            
        except Exception as e:
            logger.error(f"Error getting legacy comments for ticket {ticket_number}: {e}")
            return []
    
    def _user_can_see_comment(self, comment: Comment, user_email: str) -> bool:
        """Check if user can see this comment based on visibility rules"""
        # Public comments are visible to everyone
        if comment.comment_type == CommentType.PUBLIC:
            return True
        
        # Internal comments are only visible to the author or system users
        if comment.comment_type == CommentType.INTERNAL:
            return (comment.author_email.lower() == user_email.lower() or
                   'admin' in user_email.lower() or
                   'agent' in user_email.lower())
        
        return True
    
    async def update(self, comment: Comment) -> Comment:
        """Update comment"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            raise NotImplementedError("Legacy comment updates not supported")
        else:
            return await self._update_clean_comment(comment)
    
    async def _update_clean_comment(self, comment: Comment) -> Comment:
        """Update comment in clean table"""
        try:
            query = """
            UPDATE comments 
            SET content = $2, updated_at = $3
            WHERE id = $1
            RETURNING id, ticket_number, content, author_email, comment_type,
                     created_at, updated_at
            """
            
            async with self.db_connection.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    comment.id,
                    comment.content,
                    datetime.now()
                )
                
                if not row:
                    raise ValueError(f"Comment {comment.id} not found")
                
                return self._row_to_comment(dict(row))
                
        except Exception as e:
            logger.error(f"Failed to update comment {comment.id}: {e}")
            raise Exception(f"Failed to update comment: {e}")
    
    async def delete(self, comment_id: int) -> bool:
        """Delete comment"""
        use_legacy = await self._detect_table_structure()
        
        try:
            if use_legacy:
                query = "DELETE FROM mail_message WHERE id = $1 AND model = 'helpdesk.ticket'"
            else:
                query = "DELETE FROM comments WHERE id = $1"
            
            async with self.db_connection.get_connection() as conn:
                result = await conn.execute(query, comment_id)
                
                rows_affected = int(result.split()[-1]) if result else 0
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to delete comment {comment_id}: {e}")
            return False
    
    async def get_comment_count_by_ticket(self, ticket_number: str) -> int:
        """Get comment count for a ticket"""
        use_legacy = await self._detect_table_structure()
        
        if use_legacy:
            return await self._get_legacy_comment_count(ticket_number)
        else:
            return await self._get_clean_comment_count(ticket_number)
    
    async def _get_clean_comment_count(self, ticket_number: str) -> int:
        """Get comment count from clean table"""
        try:
            query = "SELECT COUNT(*) FROM comments WHERE ticket_number = $1"
            
            async with self.db_connection.get_connection() as conn:
                count = await conn.fetchval(query, ticket_number)
                return count or 0
                
        except Exception as e:
            logger.error(f"Error getting comment count for {ticket_number}: {e}")
            return 0
    
    async def _get_legacy_comment_count(self, ticket_number: str) -> int:
        """Get comment count from legacy table"""
        try:
            ticket_id = await self._get_ticket_id_from_number(ticket_number)
            if not ticket_id:
                return 0
            
            query = """
            SELECT COUNT(*) 
            FROM mail_message 
            WHERE model = 'helpdesk.ticket' AND res_id = $1
            """
            
            async with self.db_connection.get_connection() as conn:
                count = await conn.fetchval(query, ticket_id)
                return count or 0
                
        except Exception as e:
            logger.error(f"Error getting legacy comment count for {ticket_number}: {e}")
            return 0
    
    def _row_to_comment(self, row: Dict[str, Any]) -> Comment:
        """Convert database row to Comment entity"""
        try:
            # Handle comment type conversion
            comment_type_value = row.get('comment_type', 'public')
            if isinstance(comment_type_value, str):
                comment_type = CommentType(comment_type_value)
            else:
                comment_type = CommentType.PUBLIC
            
            comment = Comment(
                ticket_number=row['ticket_number'],
                content=row['content'],
                author_email=row['author_email'],
                comment_type=comment_type,
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at')
            )
            
            if 'id' in row:
                comment.id = row['id']
            
            return comment
            
        except Exception as e:
            logger.error(f"Error converting row to comment: {e}")
            raise ValueError(f"Invalid comment data: {e}")