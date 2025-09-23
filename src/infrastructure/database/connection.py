"""
Database connection management for PostgreSQL.
Handles connection pooling and configuration.
"""
import asyncpg
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages PostgreSQL database connections"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        min_connections: int = 5,
        max_connections: int = 20
    ) -> None:
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                min_size=min_connections,
                max_size=max_connections,
                command_timeout=60
            )
            logger.info(f"Connected to PostgreSQL database: {host}:{port}/{database}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    def get_pool(self) -> asyncpg.Pool:
        """Get connection pool"""
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.pool
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            if not self.pool:
                return False
            
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def execute_query(self, query: str, *args) -> None:
        """Execute a query (for migrations, etc.)"""
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)
    
    async def fetch_query(self, query: str, *args) -> list:
        """Fetch query results"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)


# Global database instance
db = DatabaseConnection()


async def get_database() -> DatabaseConnection:
    """Get database instance (dependency injection helper)"""
    return db