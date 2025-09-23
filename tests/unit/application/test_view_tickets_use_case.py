"""
Unit tests for ViewTicketsUseCase.
Tests business logic with mocked repositories.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.application.use_cases.view_tickets import ViewTicketsUseCase
from src.application.dto import ViewTicketsRequest, ViewTicketsResponse
from src.domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from src.domain.entities.user import User, UserRole


class TestViewTicketsUseCase:
    """Test ViewTicketsUseCase"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        ticket_repo = Mock()
        user_repo = Mock()
        comment_repo = Mock()
        
        # Configure async methods
        ticket_repo.get_recent_tickets = AsyncMock()
        ticket_repo.search_tickets = AsyncMock()
        ticket_repo.get_by_number = AsyncMock()
        ticket_repo.get_all_tickets = AsyncMock()
        
        user_repo.get_by_email = AsyncMock()
        
        comment_repo.get_comment_count_by_ticket = AsyncMock()
        
        return ticket_repo, user_repo, comment_repo
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mocked dependencies"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        return ViewTicketsUseCase(ticket_repo, user_repo, comment_repo)
    
    @pytest.fixture
    def sample_tickets(self):
        """Create sample tickets"""
        return [
            Ticket(
                number="TKT-001",
                title="First Ticket",
                description="First description",
                status=TicketStatus.OPEN,
                priority=TicketPriority.HIGH,
                creator_email="user@example.com"
            ),
            Ticket(
                number="TKT-002", 
                title="Second Ticket",
                description="Second description",
                status=TicketStatus.IN_PROGRESS,
                priority=TicketPriority.MEDIUM,
                creator_email="user@example.com"
            )
        ]
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user"""
        return User(
            email="user@example.com",
            name="Test User",
            role=UserRole.USER
        )
    
    @pytest.fixture
    def sample_agent(self):
        """Create sample agent"""
        return User(
            email="agent@example.com",
            name="Agent User",
            role=UserRole.AGENT
        )
    
    @pytest.mark.asyncio
    async def test_execute_recent_tickets_success(self, use_case, mock_repositories, sample_tickets, sample_user):
        """Test successful recent tickets viewing"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        ticket_repo.get_recent_tickets.return_value = sample_tickets
        comment_repo.get_comment_count_by_ticket.return_value = 3
        
        # Create request for recent tickets
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="recent",
            limit=10
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify response
        assert isinstance(response, ViewTicketsResponse)
        assert len(response.tickets) == 2
        assert response.tickets[0].number == "TKT-001"
        assert all(ticket.comment_count == 3 for ticket in response.tickets)
        
        # Verify repository calls
        user_repo.get_by_email.assert_called_once_with("user@example.com")
        ticket_repo.get_recent_tickets.assert_called_once_with("user@example.com", 10)
        assert comment_repo.get_comment_count_by_ticket.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_search_tickets_success(self, use_case, mock_repositories, sample_tickets, sample_user):
        """Test successful ticket search"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        ticket_repo.search_tickets.return_value = sample_tickets[:1]  # One result
        comment_repo.get_comment_count_by_ticket.return_value = 2
        
        # Create search request
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="search",
            search_query="First Ticket"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify response
        assert len(response.tickets) == 1
        assert response.tickets[0].title == "First Ticket"
        assert response.tickets[0].comment_count == 2
        
        # Verify repository calls
        ticket_repo.search_tickets.assert_called_once_with(
            query="First Ticket",
            user_email="user@example.com",
            limit=None
        )
    
    @pytest.mark.asyncio
    async def test_execute_all_tickets_for_agent(self, use_case, mock_repositories, sample_tickets, sample_agent):
        """Test agent viewing all tickets"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_agent
        ticket_repo.get_all_tickets.return_value = sample_tickets
        comment_repo.get_comment_count_by_ticket.return_value = 1
        
        # Create request for all tickets
        request = ViewTicketsRequest(
            user_email="agent@example.com",
            view_type="all"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify response
        assert len(response.tickets) == 2
        
        # Verify repository calls
        ticket_repo.get_all_tickets.assert_called_once_with(limit=None)
    
    @pytest.mark.asyncio
    async def test_execute_user_not_found(self, use_case, mock_repositories):
        """Test error when user not found"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = None
        
        # Create request
        request = ViewTicketsRequest(
            user_email="nonexistent@example.com",
            view_type="recent"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="User nonexistent@example.com not found"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_invalid_view_type(self, use_case, mock_repositories, sample_user):
        """Test error with invalid view type"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        
        # Create request with invalid view type
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="invalid_type"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Invalid view type: invalid_type"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_search_without_query(self, use_case, mock_repositories, sample_user):
        """Test error when search requested without query"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        
        # Create search request without query
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="search"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Search query is required for search view"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_user_cannot_view_all_tickets(self, use_case, mock_repositories, sample_user):
        """Test regular user cannot view all tickets"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        
        # Create request for all tickets by regular user
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="all"
        )
        
        # Execute and verify permission error
        with pytest.raises(PermissionError, match="User cannot view all tickets"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_status_filter(self, use_case, mock_repositories, sample_user):
        """Test filtering by ticket status"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Create tickets with different statuses
        open_ticket = Ticket(
            number="TKT-001",
            title="Open Ticket",
            description="Description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            creator_email="user@example.com"
        )
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        ticket_repo.get_recent_tickets.return_value = [open_ticket]
        comment_repo.get_comment_count_by_ticket.return_value = 0
        
        # Create request with status filter
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="recent",
            status_filter="open"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify filtering
        assert len(response.tickets) == 1
        assert response.tickets[0].status == TicketStatus.OPEN.value
        
        # Verify repository called with filter
        ticket_repo.get_recent_tickets.assert_called_once_with(
            "user@example.com", 
            None,
            TicketStatus.OPEN
        )
    
    @pytest.mark.asyncio
    async def test_execute_priority_filter(self, use_case, mock_repositories, sample_user):
        """Test filtering by ticket priority"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Create high priority ticket
        high_ticket = Ticket(
            number="TKT-001",
            title="High Priority Ticket",
            description="Description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            creator_email="user@example.com"
        )
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        ticket_repo.search_tickets.return_value = [high_ticket]
        comment_repo.get_comment_count_by_ticket.return_value = 1
        
        # Create request with priority filter
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="search",
            search_query="ticket",
            priority_filter="high"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify filtering
        assert len(response.tickets) == 1
        assert response.tickets[0].priority == TicketPriority.HIGH.value
        
        # Verify repository called with filter
        ticket_repo.search_tickets.assert_called_once_with(
            query="ticket",
            user_email="user@example.com",
            limit=None,
            status_filter=None,
            priority_filter=TicketPriority.HIGH
        )
    
    @pytest.mark.asyncio
    async def test_execute_invalid_status_filter(self, use_case, mock_repositories, sample_user):
        """Test error with invalid status filter"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        
        # Create request with invalid status filter
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="recent",
            status_filter="invalid_status"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Invalid status filter: invalid_status"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_invalid_priority_filter(self, use_case, mock_repositories, sample_user):
        """Test error with invalid priority filter"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        
        # Create request with invalid priority filter
        request = ViewTicketsRequest(
            user_email="user@example.com",
            view_type="search",
            search_query="test",
            priority_filter="invalid_priority"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Invalid priority filter: invalid_priority"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_get_ticket_by_number_success(self, use_case, mock_repositories, sample_user):
        """Test getting specific ticket by number"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Create sample ticket
        ticket = Ticket(
            number="TKT-001",
            title="Test Ticket",
            description="Description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            creator_email="user@example.com"
        )
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        ticket_repo.get_by_number.return_value = ticket
        comment_repo.get_comment_count_by_ticket.return_value = 5
        
        # Execute
        result_ticket = await use_case.get_ticket_by_number("TKT-001", "user@example.com")
        
        # Verify
        assert result_ticket.number == "TKT-001"
        assert result_ticket.comment_count == 5
        
        # Verify repository calls
        user_repo.get_by_email.assert_called_once_with("user@example.com")
        ticket_repo.get_by_number.assert_called_once_with("TKT-001")
        comment_repo.get_comment_count_by_ticket.assert_called_once_with("TKT-001")
    
    @pytest.mark.asyncio
    async def test_get_ticket_by_number_not_found(self, use_case, mock_repositories, sample_user):
        """Test getting non-existent ticket"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        ticket_repo.get_by_number.return_value = None
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Ticket NONEXISTENT not found"):
            await use_case.get_ticket_by_number("NONEXISTENT", "user@example.com")
    
    @pytest.mark.asyncio
    async def test_get_ticket_by_number_permission_denied(self, use_case, mock_repositories):
        """Test permission denied when accessing unauthorized ticket"""
        ticket_repo, user_repo, comment_repo = mock_repositories
        
        # Create unauthorized user
        unauthorized_user = User(
            email="other@example.com",
            name="Other User",
            role=UserRole.USER
        )
        
        # Create ticket belonging to different user
        ticket = Ticket(
            number="TKT-001",
            title="Test Ticket",
            description="Description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            creator_email="user@example.com"
        )
        
        # Setup mocks
        user_repo.get_by_email.return_value = unauthorized_user
        ticket_repo.get_by_number.return_value = ticket
        
        # Execute and verify permission error
        with pytest.raises(PermissionError, match="User cannot access this ticket"):
            await use_case.get_ticket_by_number("TKT-001", "other@example.com")