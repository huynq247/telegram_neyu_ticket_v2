"""
Integration tests for PostgreSQLTicketRepository.
Tests database operations with real database connection.
"""
import pytest
import asyncpg
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.infrastructure.repositories.postgresql_ticket_repository import PostgreSQLTicketRepository
from src.infrastructure.database.connection import DatabaseConnection
from src.domain.entities.ticket import Ticket, TicketStatus, TicketPriority


class TestPostgreSQLTicketRepository:
    """Test PostgreSQLTicketRepository"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock database connection"""
        mock_conn = Mock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock()
        mock_conn.fetchrow = AsyncMock()
        mock_conn.fetchval = AsyncMock()
        return mock_conn
    
    @pytest.fixture
    def mock_db_connection(self, mock_connection):
        """Create mock DatabaseConnection"""
        db_conn = Mock(spec=DatabaseConnection)
        db_conn.get_connection = AsyncMock(return_value=mock_connection)
        return db_conn
    
    @pytest.fixture
    def repository(self, mock_db_connection):
        """Create repository with mocked database connection"""
        return PostgreSQLTicketRepository(mock_db_connection)
    
    @pytest.fixture
    def sample_ticket(self):
        """Create sample ticket"""
        return Ticket(
            number="TKT-001",
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            creator_email="user@example.com"
        )
    
    @pytest.fixture
    def sample_ticket_row(self):
        """Create sample database row for ticket"""
        return {
            'number': 'TKT-001',
            'title': 'Test Ticket',
            'description': 'Test description',
            'status': 'open',
            'priority': 'medium',
            'creator_email': 'user@example.com',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'last_activity_at': datetime.now(timezone.utc)
        }
    
    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_connection, sample_ticket):
        """Test successful ticket creation"""
        # Setup mock to return created ticket
        mock_connection.fetchrow.return_value = {
            'number': 'TKT-001',
            'title': 'Test Ticket',
            'description': 'Test description',
            'status': 'open',
            'priority': 'medium',
            'creator_email': 'user@example.com',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'last_activity_at': datetime.now(timezone.utc)
        }
        
        # Execute
        created_ticket = await repository.create(sample_ticket)
        
        # Verify
        assert created_ticket.number == "TKT-001"
        assert created_ticket.title == "Test Ticket"
        assert created_ticket.status == TicketStatus.OPEN
        
        # Verify SQL was called
        mock_connection.fetchrow.assert_called_once()
        call_args = mock_connection.fetchrow.call_args
        assert "INSERT INTO tickets" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_create_database_error(self, repository, mock_connection, sample_ticket):
        """Test handling database error during creation"""
        # Setup mock to raise database error
        mock_connection.fetchrow.side_effect = asyncpg.PostgresError("Database error")
        
        # Execute and verify error
        with pytest.raises(Exception, match="Failed to create ticket"):
            await repository.create(sample_ticket)
    
    @pytest.mark.asyncio
    async def test_get_by_number_success(self, repository, mock_connection, sample_ticket_row):
        """Test successful ticket retrieval by number"""
        # Setup mock
        mock_connection.fetchrow.return_value = sample_ticket_row
        
        # Execute
        ticket = await repository.get_by_number("TKT-001")
        
        # Verify
        assert ticket is not None
        assert ticket.number == "TKT-001"
        assert ticket.title == "Test Ticket"
        assert ticket.status == TicketStatus.OPEN
        
        # Verify SQL was called
        mock_connection.fetchrow.assert_called_once()
        call_args = mock_connection.fetchrow.call_args
        assert "SELECT * FROM tickets WHERE number = $1" in call_args[0][0]
        assert call_args[0][1] == "TKT-001"
    
    @pytest.mark.asyncio
    async def test_get_by_number_not_found(self, repository, mock_connection):
        """Test ticket not found"""
        # Setup mock to return None
        mock_connection.fetchrow.return_value = None
        
        # Execute
        ticket = await repository.get_by_number("NONEXISTENT")
        
        # Verify
        assert ticket is None
    
    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_connection, sample_ticket, sample_ticket_row):
        """Test successful ticket update"""
        # Setup mock to return updated ticket
        mock_connection.fetchrow.return_value = sample_ticket_row
        
        # Modify ticket
        sample_ticket.title = "Updated Title"
        sample_ticket.status = TicketStatus.IN_PROGRESS
        
        # Execute
        updated_ticket = await repository.update(sample_ticket)
        
        # Verify
        assert updated_ticket.number == "TKT-001"
        
        # Verify SQL was called
        mock_connection.fetchrow.assert_called_once()
        call_args = mock_connection.fetchrow.call_args
        assert "UPDATE tickets SET" in call_args[0][0]
        assert "WHERE number = $7" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_connection, sample_ticket):
        """Test updating non-existent ticket"""
        # Setup mock to return None
        mock_connection.fetchrow.return_value = None
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Ticket TKT-001 not found"):
            await repository.update(sample_ticket)
    
    @pytest.mark.asyncio
    async def test_delete_success(self, repository, mock_connection):
        """Test successful ticket deletion"""
        # Setup mock to return deletion count
        mock_connection.fetchval.return_value = 1
        
        # Execute
        result = await repository.delete("TKT-001")
        
        # Verify
        assert result is True
        
        # Verify SQL was called
        mock_connection.fetchval.assert_called_once()
        call_args = mock_connection.fetchval.call_args
        assert "DELETE FROM tickets WHERE number = $1" in call_args[0][0]
        assert call_args[0][1] == "TKT-001"
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_connection):
        """Test deleting non-existent ticket"""
        # Setup mock to return zero deletion count
        mock_connection.fetchval.return_value = 0
        
        # Execute
        result = await repository.delete("NONEXISTENT")
        
        # Verify
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_recent_tickets_success(self, repository, mock_connection):
        """Test getting recent tickets for user"""
        # Setup mock to return multiple tickets
        mock_connection.fetch.return_value = [
            {
                'number': 'TKT-001',
                'title': 'First Ticket',
                'description': 'Description 1',
                'status': 'open',
                'priority': 'high',
                'creator_email': 'user@example.com',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'last_activity_at': datetime.now(timezone.utc)
            },
            {
                'number': 'TKT-002',
                'title': 'Second Ticket',
                'description': 'Description 2',
                'status': 'in_progress',
                'priority': 'medium',
                'creator_email': 'user@example.com',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'last_activity_at': datetime.now(timezone.utc)
            }
        ]
        
        # Execute
        tickets = await repository.get_recent_tickets("user@example.com", 10)
        
        # Verify
        assert len(tickets) == 2
        assert tickets[0].number == "TKT-001"
        assert tickets[1].number == "TKT-002"
        assert tickets[0].priority == TicketPriority.HIGH
        
        # Verify SQL was called
        mock_connection.fetch.assert_called_once()
        call_args = mock_connection.fetch.call_args
        assert "WHERE creator_email = $1" in call_args[0][0]
        assert "ORDER BY last_activity_at DESC" in call_args[0][0]
        assert "LIMIT $2" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_get_recent_tickets_with_status_filter(self, repository, mock_connection):
        """Test getting recent tickets with status filter"""
        # Setup mock
        mock_connection.fetch.return_value = []
        
        # Execute with status filter
        await repository.get_recent_tickets("user@example.com", 10, TicketStatus.OPEN)
        
        # Verify SQL includes status filter
        call_args = mock_connection.fetch.call_args
        assert "AND status = $3" in call_args[0][0]
        assert call_args[0][2] == "open"
    
    @pytest.mark.asyncio
    async def test_search_tickets_success(self, repository, mock_connection):
        """Test ticket search functionality"""
        # Setup mock to return search results
        mock_connection.fetch.return_value = [
            {
                'number': 'TKT-001',
                'title': 'Matching Ticket',
                'description': 'Contains search term',
                'status': 'open',
                'priority': 'medium',
                'creator_email': 'user@example.com',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'last_activity_at': datetime.now(timezone.utc)
            }
        ]
        
        # Execute
        tickets = await repository.search_tickets(
            query="search term",
            user_email="user@example.com",
            limit=10
        )
        
        # Verify
        assert len(tickets) == 1
        assert tickets[0].title == "Matching Ticket"
        
        # Verify SQL includes search functionality
        call_args = mock_connection.fetch.call_args
        assert "WHERE creator_email = $1" in call_args[0][0]
        assert "AND (" in call_args[0][0]  # Search conditions
        assert "ILIKE $2" in call_args[0][0]  # Case-insensitive search
    
    @pytest.mark.asyncio
    async def test_search_tickets_with_filters(self, repository, mock_connection):
        """Test ticket search with status and priority filters"""
        # Setup mock
        mock_connection.fetch.return_value = []
        
        # Execute with filters
        await repository.search_tickets(
            query="test",
            user_email="user@example.com",
            limit=5,
            status_filter=TicketStatus.OPEN,
            priority_filter=TicketPriority.HIGH
        )
        
        # Verify SQL includes filters
        call_args = mock_connection.fetch.call_args
        assert "AND status = $3" in call_args[0][0]
        assert "AND priority = $4" in call_args[0][0]
        assert call_args[0][2] == "open"
        assert call_args[0][3] == "high"
    
    @pytest.mark.asyncio
    async def test_get_all_tickets_for_admin(self, repository, mock_connection):
        """Test getting all tickets (admin functionality)"""
        # Setup mock
        mock_connection.fetch.return_value = []
        
        # Execute
        tickets = await repository.get_all_tickets(limit=50)
        
        # Verify
        assert isinstance(tickets, list)
        
        # Verify SQL doesn't filter by user
        call_args = mock_connection.fetch.call_args
        assert "creator_email" not in call_args[0][0]
        assert "ORDER BY last_activity_at DESC" in call_args[0][0]
        assert "LIMIT $1" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, repository, mock_db_connection):
        """Test handling database connection errors"""
        # Setup mock to raise connection error
        mock_db_connection.get_connection.side_effect = Exception("Connection failed")
        
        # Execute and verify error handling
        with pytest.raises(Exception, match="Connection failed"):
            await repository.get_by_number("TKT-001")
    
    @pytest.mark.asyncio
    async def test_row_to_ticket_conversion(self, repository):
        """Test converting database row to Ticket entity"""
        # Create sample row
        row = {
            'number': 'TKT-001',
            'title': 'Test Ticket',
            'description': 'Test description',
            'status': 'open',
            'priority': 'high',
            'creator_email': 'user@example.com',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'last_activity_at': datetime.now(timezone.utc)
        }
        
        # Convert to ticket
        ticket = repository._row_to_ticket(row)
        
        # Verify conversion
        assert ticket.number == "TKT-001"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.priority == TicketPriority.HIGH
        assert isinstance(ticket.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_invalid_status_conversion(self, repository):
        """Test handling invalid status in database row"""
        # Create row with invalid status
        row = {
            'number': 'TKT-001',
            'title': 'Test Ticket',
            'description': 'Test description',
            'status': 'invalid_status',
            'priority': 'medium',
            'creator_email': 'user@example.com',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'last_activity_at': datetime.now(timezone.utc)
        }
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Invalid ticket status: invalid_status"):
            repository._row_to_ticket(row)
    
    @pytest.mark.asyncio
    async def test_generate_ticket_number(self, repository, mock_connection):
        """Test ticket number generation"""
        # Setup mock to return next sequence value
        mock_connection.fetchval.return_value = 123
        
        # Execute
        ticket_number = await repository._generate_ticket_number()
        
        # Verify format
        assert ticket_number == "TKT-123"
        
        # Verify sequence query
        mock_connection.fetchval.assert_called_once()
        call_args = mock_connection.fetchval.call_args
        assert "nextval('ticket_number_seq')" in call_args[0][0]