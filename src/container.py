"""
Dependency injection container for wiring up all application layers.
Provides centralized configuration and dependency management.
"""
import asyncio
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

# Domain
from .domain.repositories.ticket_repository import TicketRepository
from .domain.repositories.comment_repository import CommentRepository
from .domain.repositories.user_repository import UserRepository

# Application
from .application import ViewCommentsUseCase, AddCommentUseCase, ViewTicketsUseCase

# Infrastructure
from .infrastructure.database.connection import DatabaseConnection
from .infrastructure.database.schema_service import DatabaseSchemaService
from .infrastructure.adapters.legacy_data_adapter import LegacyDataAdapter
from .infrastructure.repositories.legacy_ticket_repository import LegacyTicketRepository
from .infrastructure.repositories.legacy_comment_repository import LegacyCommentRepository

# Presentation
from .presentation import (
    CommentHandler,
    CommentFormatter,
    CommentKeyboards,
    TicketFormatter,
    TicketKeyboards
)

logger = logging.getLogger(__name__)


class DependencyContainer:
    """Dependency injection container for the application"""
    
    def __init__(self):
        self._database: Optional[DatabaseConnection] = None
        self._repositories: Dict[str, Any] = {}
        self._use_cases: Dict[str, Any] = {}
        self._handlers: Dict[str, Any] = {}
        self._formatters: Dict[str, Any] = {}
        self._keyboards: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize all dependencies"""
        if self._initialized:
            logger.warning("Container already initialized")
            return
        
        try:
            # Initialize database
            await self._setup_database(config)
            
            # Initialize repositories
            self._setup_repositories()
            
            # Initialize use cases
            self._setup_use_cases()
            
            # Initialize presentation layer
            self._setup_presentation_layer()
            
            self._initialized = True
            logger.info("Dependency container initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize dependency container: {e}")
            await self.cleanup()
            raise
    
    async def _setup_database(self, config: Dict[str, Any]) -> None:
        """Setup database connection"""
        db_config = config.get('database', {})
        
        self._database = DatabaseConnection()
        await self._database.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('database', 'postgres'),
            username=db_config.get('username', 'postgres'),
            password=db_config.get('password', ''),
            min_connections=db_config.get('min_connections', 5),
            max_connections=db_config.get('max_connections', 20)
        )
        
        # Health check
        if not await self._database.health_check():
            raise RuntimeError("Database health check failed")
    
    def _setup_repositories(self) -> None:
        """Setup repository implementations"""
        if not self._database:
            raise RuntimeError("Database not initialized")
        
        pool = self._database.get_pool()
        
        # Create repository implementations
        # Create infrastructure services
        schema_service = DatabaseSchemaService(self._db_connection)
        legacy_adapter = LegacyDataAdapter(self._db_connection)
        
        # Create repositories with legacy support
        self._repositories['ticket'] = LegacyTicketRepository(
            self._db_connection, schema_service, legacy_adapter
        )
        self._repositories['comment'] = LegacyCommentRepository(
            self._db_connection, schema_service, legacy_adapter
        )
        
        # TODO: Implement UserRepository when user management is added
        # self._repositories['user'] = PostgreSQLUserRepository(pool)
        
        logger.info("Repositories initialized")
    
    def _setup_use_cases(self) -> None:
        """Setup application use cases"""
        ticket_repo = self._repositories['ticket']
        comment_repo = self._repositories['comment']
        
        # TODO: Add user repository when implemented
        user_repo = None  # self._repositories['user']
        
        # Create use cases
        self._use_cases['view_comments'] = ViewCommentsUseCase(
            ticket_repository=ticket_repo,
            comment_repository=comment_repo,
            user_repository=user_repo
        )
        
        self._use_cases['add_comment'] = AddCommentUseCase(
            ticket_repository=ticket_repo,
            comment_repository=comment_repo,
            user_repository=user_repo
        )
        
        self._use_cases['view_tickets'] = ViewTicketsUseCase(
            ticket_repository=ticket_repo,
            comment_repository=comment_repo,
            user_repository=user_repo
        )
        
        logger.info("Use cases initialized")
    
    def _setup_presentation_layer(self) -> None:
        """Setup presentation layer components"""
        # Create formatters
        self._formatters['comment'] = CommentFormatter()
        self._formatters['ticket'] = TicketFormatter()
        
        # Create keyboards
        self._keyboards['comment'] = CommentKeyboards()
        self._keyboards['ticket'] = TicketKeyboards()
        
        # Create handlers
        self._handlers['comment'] = CommentHandler(
            view_comments_use_case=self._use_cases['view_comments'],
            add_comment_use_case=self._use_cases['add_comment'],
            formatter=self._formatters['comment'],
            keyboards=self._keyboards['comment']
        )
        
        logger.info("Presentation layer initialized")
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            if self._database:
                await self._database.disconnect()
                self._database = None
            
            self._repositories.clear()
            self._use_cases.clear()
            self._handlers.clear()
            self._formatters.clear()
            self._keyboards.clear()
            
            self._initialized = False
            logger.info("Dependency container cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Getters for dependencies
    
    def get_database(self) -> DatabaseConnection:
        """Get database connection"""
        if not self._database:
            raise RuntimeError("Database not initialized")
        return self._database
    
    def get_repository(self, name: str) -> Any:
        """Get repository by name"""
        if name not in self._repositories:
            raise ValueError(f"Repository '{name}' not found")
        return self._repositories[name]
    
    def get_use_case(self, name: str) -> Any:
        """Get use case by name"""
        if name not in self._use_cases:
            raise ValueError(f"Use case '{name}' not found")
        return self._use_cases[name]
    
    def get_handler(self, name: str) -> Any:
        """Get handler by name"""
        if name not in self._handlers:
            raise ValueError(f"Handler '{name}' not found")
        return self._handlers[name]
    
    def get_formatter(self, name: str) -> Any:
        """Get formatter by name"""
        if name not in self._formatters:
            raise ValueError(f"Formatter '{name}' not found")
        return self._formatters[name]
    
    def get_keyboard(self, name: str) -> Any:
        """Get keyboard by name"""
        if name not in self._keyboards:
            raise ValueError(f"Keyboard '{name}' not found")
        return self._keyboards[name]
    
    # Convenience getters for common dependencies
    
    def get_comment_handler(self) -> CommentHandler:
        """Get comment handler"""
        return self.get_handler('comment')
    
    def get_view_comments_use_case(self) -> ViewCommentsUseCase:
        """Get view comments use case"""
        return self.get_use_case('view_comments')
    
    def get_add_comment_use_case(self) -> AddCommentUseCase:
        """Get add comment use case"""
        return self.get_use_case('add_comment')
    
    def get_ticket_repository(self) -> TicketRepository:
        """Get ticket repository"""
        return self.get_repository('ticket')
    
    def get_comment_repository(self) -> CommentRepository:
        """Get comment repository"""
        return self.get_repository('comment')
    
    @property
    def is_initialized(self) -> bool:
        """Check if container is initialized"""
        return self._initialized
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all components"""
        health = {}
        
        try:
            # Database health
            health['database'] = await self._database.health_check() if self._database else False
            
            # Repository health (basic check)
            health['repositories'] = len(self._repositories) > 0
            
            # Use cases health
            health['use_cases'] = len(self._use_cases) > 0
            
            # Handlers health
            health['handlers'] = len(self._handlers) > 0
            
            # Overall health
            health['overall'] = all(health.values())
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health['overall'] = False
        
        return health


# Global container instance
_container: Optional[DependencyContainer] = None


async def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    global _container
    
    if _container is None:
        raise RuntimeError("Dependency container not initialized. Call initialize_container() first.")
    
    if not _container.is_initialized:
        raise RuntimeError("Dependency container not properly initialized")
    
    return _container


async def initialize_container(config: Dict[str, Any]) -> DependencyContainer:
    """Initialize the global dependency container"""
    global _container
    
    if _container is not None:
        logger.warning("Container already exists, cleaning up first")
        await _container.cleanup()
    
    _container = DependencyContainer()
    await _container.initialize(config)
    
    return _container


async def cleanup_container() -> None:
    """Cleanup the global dependency container"""
    global _container
    
    if _container is not None:
        await _container.cleanup()
        _container = None


@asynccontextmanager
async def container_lifespan(config: Dict[str, Any]):
    """Context manager for container lifecycle"""
    container = None
    try:
        container = await initialize_container(config)
        yield container
    finally:
        if container:
            await container.cleanup()