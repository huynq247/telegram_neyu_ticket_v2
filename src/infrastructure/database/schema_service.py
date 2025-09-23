"""
Database schema inspection and migration utilities.
Replaces the legacy postgresql_connector schema discovery logic.
"""
import asyncpg
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .connection import DatabaseConnection

logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """Database table information"""
    name: str
    schema: str
    columns: List[Dict[str, Any]]
    row_count: Optional[int] = None


@dataclass
class ColumnInfo:
    """Database column information"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    is_primary_key: bool = False
    is_foreign_key: bool = False


class DatabaseSchemaService:
    """Service for database schema inspection and management"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize schema service
        
        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection
    
    async def get_all_tables(self, schema: str = 'public') -> List[str]:
        """
        Get all table names in schema
        
        Args:
            schema: Database schema name
            
        Returns:
            List of table names
        """
        try:
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = $1 AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
            
            async with self.db_connection.get_connection() as conn:
                rows = await conn.fetch(query, schema)
                tables = [row['table_name'] for row in rows]
                
            logger.info(f"Found {len(tables)} tables in schema '{schema}'")
            return tables
            
        except Exception as e:
            logger.error(f"Error getting tables from schema '{schema}': {e}")
            return []
    
    async def find_helpdesk_tables(self) -> List[str]:
        """
        Find tables related to helpdesk/ticketing system
        
        Returns:
            List of potential helpdesk table names
        """
        try:
            all_tables = await self.get_all_tables()
            
            # Keywords that indicate helpdesk-related tables
            helpdesk_keywords = [
                'helpdesk', 'ticket', 'support', 'issue', 'request',
                'mail_message', 'mail_thread', 'ir_attachment'
            ]
            
            helpdesk_tables = []
            for table in all_tables:
                table_lower = table.lower()
                for keyword in helpdesk_keywords:
                    if keyword in table_lower:
                        helpdesk_tables.append(table)
                        break
            
            logger.info(f"Found {len(helpdesk_tables)} potential helpdesk tables")
            return helpdesk_tables
            
        except Exception as e:
            logger.error(f"Error finding helpdesk tables: {e}")
            return []
    
    async def describe_table(self, table_name: str, schema: str = 'public') -> Optional[TableInfo]:
        """
        Get detailed table information including columns
        
        Args:
            table_name: Name of the table
            schema: Database schema name
            
        Returns:
            TableInfo object or None if table not found
        """
        try:
            # Get column information
            column_query = """
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
                CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT ku.table_name, ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku 
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
            ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
            LEFT JOIN (
                SELECT ku.table_name, ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku 
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
            ) fk ON c.table_name = fk.table_name AND c.column_name = fk.column_name
            WHERE c.table_name = $1 AND c.table_schema = $2
            ORDER BY c.ordinal_position
            """
            
            async with self.db_connection.get_connection() as conn:
                rows = await conn.fetch(column_query, table_name, schema)
                
                if not rows:
                    logger.warning(f"Table '{table_name}' not found in schema '{schema}'")
                    return None
                
                columns = []
                for row in rows:
                    column = ColumnInfo(
                        name=row['column_name'],
                        data_type=row['data_type'],
                        is_nullable=row['is_nullable'] == 'YES',
                        default_value=row['column_default'],
                        is_primary_key=row['is_primary_key'],
                        is_foreign_key=row['is_foreign_key']
                    )
                    columns.append(column.__dict__)
                
                # Get row count
                count_query = f"SELECT COUNT(*) FROM {schema}.{table_name}"
                row_count = await conn.fetchval(count_query)
                
                table_info = TableInfo(
                    name=table_name,
                    schema=schema,
                    columns=columns,
                    row_count=row_count
                )
                
                logger.info(f"Described table '{table_name}': {len(columns)} columns, {row_count} rows")
                return table_info
                
        except Exception as e:
            logger.error(f"Error describing table '{table_name}': {e}")
            return None
    
    async def check_table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """
        Check if a table exists in the schema
        
        Args:
            table_name: Name of the table
            schema: Database schema name
            
        Returns:
            True if table exists
        """
        try:
            query = """
            SELECT COUNT(*)
            FROM information_schema.tables 
            WHERE table_name = $1 AND table_schema = $2
            """
            
            async with self.db_connection.get_connection() as conn:
                count = await conn.fetchval(query, table_name, schema)
                return count > 0
                
        except Exception as e:
            logger.error(f"Error checking table existence '{table_name}': {e}")
            return False
    
    async def get_table_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample data from a table
        
        Args:
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            List of sample rows
        """
        try:
            query = f"SELECT * FROM {table_name} LIMIT $1"
            
            async with self.db_connection.get_connection() as conn:
                rows = await conn.fetch(query, limit)
                
                # Convert to list of dictionaries
                sample_data = [dict(row) for row in rows]
                
                logger.info(f"Retrieved {len(sample_data)} sample rows from '{table_name}'")
                return sample_data
                
        except Exception as e:
            logger.error(f"Error getting sample data from '{table_name}': {e}")
            return []
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get general database information
        
        Returns:
            Dictionary with database info
        """
        try:
            async with self.db_connection.get_connection() as conn:
                # Get PostgreSQL version
                version = await conn.fetchval("SELECT version()")
                
                # Get database name
                db_name = await conn.fetchval("SELECT current_database()")
                
                # Get user name
                user_name = await conn.fetchval("SELECT current_user")
                
                # Get total table count
                table_count = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                info = {
                    'version': version,
                    'database_name': db_name,
                    'current_user': user_name,
                    'table_count': table_count,
                    'connection_status': 'connected'
                }
                
                logger.info(f"Database info retrieved: {db_name} ({table_count} tables)")
                return info
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {'connection_status': 'error', 'error': str(e)}
    
    async def create_tickets_table_if_not_exists(self) -> bool:
        """
        Create tickets table if it doesn't exist (for new installations)
        
        Returns:
            True if successful
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                number VARCHAR(50) UNIQUE NOT NULL,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                status VARCHAR(50) NOT NULL DEFAULT 'open',
                priority VARCHAR(50) NOT NULL DEFAULT 'medium',
                creator_email VARCHAR(200) NOT NULL,
                assignee_email VARCHAR(200),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_tickets_number ON tickets(number);
            CREATE INDEX IF NOT EXISTS idx_tickets_creator_email ON tickets(creator_email);
            CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
            CREATE INDEX IF NOT EXISTS idx_tickets_last_activity ON tickets(last_activity_at);
            """
            
            async with self.db_connection.get_connection() as conn:
                await conn.execute(create_table_sql)
                
            logger.info("Tickets table created/verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tickets table: {e}")
            return False
    
    async def create_comments_table_if_not_exists(self) -> bool:
        """
        Create comments table if it doesn't exist (for new installations)
        
        Returns:
            True if successful
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                author_email VARCHAR(200) NOT NULL,
                comment_type VARCHAR(50) NOT NULL DEFAULT 'public',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (ticket_number) REFERENCES tickets(number)
            );
            
            CREATE INDEX IF NOT EXISTS idx_comments_ticket_number ON comments(ticket_number);
            CREATE INDEX IF NOT EXISTS idx_comments_author_email ON comments(author_email);
            CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at);
            """
            
            async with self.db_connection.get_connection() as conn:
                await conn.execute(create_table_sql)
                
            logger.info("Comments table created/verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating comments table: {e}")
            return False