"""
Unit tests for ViewCommentsUseCase.
Tests business logic with mocked repositories.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.application.use_cases.view_comments import ViewCommentsUseCase
from src.application.dto import ViewCommentsRequest, ViewCommentsResponse
from src.domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from src.domain.entities.comment import Comment, CommentType
from src.domain.entities.user import User, UserRole


class TestViewCommentsUseCase:
    """Test ViewCommentsUseCase"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        ticket_repo = Mock()
        comment_repo = Mock()
        user_repo = Mock()
        
        # Configure async methods
        ticket_repo.get_by_number = AsyncMock()
        ticket_repo.get_recent_tickets = AsyncMock()
        ticket_repo.search_tickets = AsyncMock()
        
        comment_repo.get_by_ticket_number = AsyncMock()
        comment_repo.get_comment_count_by_ticket = AsyncMock()
        
        user_repo.get_by_email = AsyncMock()
        
        return ticket_repo, comment_repo, user_repo
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mocked dependencies"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        return ViewCommentsUseCase(ticket_repo, comment_repo, user_repo)
    
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
    def sample_user(self):
        """Create sample user"""
        return User(
            email="user@example.com",
            name="Test User",
            role=UserRole.USER
        )
    
    @pytest.fixture
    def sample_comments(self):
        """Create sample comments"""
        return [
            Comment(
                ticket_number="TKT-001",
                content="First comment",
                author_email="user@example.com"
            ),
            Comment(
                ticket_number="TKT-001",
                content="Second comment",
                author_email="agent@example.com",
                comment_type=CommentType.PUBLIC
            )
        ]
    
    @pytest.mark.asyncio
    async def test_execute_success(self, use_case, mock_repositories, sample_ticket, sample_user, sample_comments):
        """Test successful comment viewing"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        comment_repo.get_by_ticket_number.return_value = sample_comments
        comment_repo.get_comment_count_by_ticket.return_value = len(sample_comments)
        
        # Create request
        request = ViewCommentsRequest(
            ticket_number="TKT-001",
            user_email="user@example.com"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify response
        assert isinstance(response, ViewCommentsResponse)
        assert response.ticket.number == "TKT-001"
        assert len(response.comments) == 2
        assert response.total_count == 2
        assert response.user_can_add_comment
        
        # Verify repository calls
        ticket_repo.get_by_number.assert_called_once_with("TKT-001")
        user_repo.get_by_email.assert_called_once_with("user@example.com")
        comment_repo.get_by_ticket_number.assert_called_once()
        comment_repo.get_comment_count_by_ticket.assert_called_once_with("TKT-001")
    
    @pytest.mark.asyncio
    async def test_execute_ticket_not_found(self, use_case, mock_repositories):
        """Test error when ticket not found"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = None
        
        # Create request
        request = ViewCommentsRequest(
            ticket_number="NONEXISTENT",
            user_email="user@example.com"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Ticket NONEXISTENT not found"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_user_not_found(self, use_case, mock_repositories, sample_ticket):
        """Test error when user not found"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = None
        
        # Create request
        request = ViewCommentsRequest(
            ticket_number="TKT-001",
            user_email="nonexistent@example.com"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="User nonexistent@example.com not found"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_permission_denied(self, use_case, mock_repositories, sample_ticket):
        """Test permission denied for unauthorized user"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Create different user who cannot access the ticket
        unauthorized_user = User(
            email="other@example.com",
            name="Other User",
            role=UserRole.USER
        )
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = unauthorized_user
        
        # Create request
        request = ViewCommentsRequest(
            ticket_number="TKT-001",
            user_email="other@example.com"
        )
        
        # Execute and verify permission error
        with pytest.raises(PermissionError, match="User cannot access this ticket"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_with_comment_type_filter(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test filtering comments by type"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Create mixed comment types
        public_comment = Comment(
            ticket_number="TKT-001",
            content="Public comment",
            author_email="user@example.com",
            comment_type=CommentType.PUBLIC
        )
        
        internal_comment = Comment(
            ticket_number="TKT-001",
            content="Internal note",
            author_email="agent@example.com",
            comment_type=CommentType.INTERNAL
        )
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        comment_repo.get_by_ticket_number.return_value = [public_comment]  # Only public returned
        comment_repo.get_comment_count_by_ticket.return_value = 2  # Total count
        
        # Create request with filter
        request = ViewCommentsRequest(
            ticket_number="TKT-001",
            user_email="user@example.com",
            comment_type_filter="public"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify filtering
        assert len(response.comments) == 1
        assert response.comments[0].comment_type == CommentType.PUBLIC.value
        
        # Verify repository called with filter
        comment_repo.get_by_ticket_number.assert_called_once_with(
            "TKT-001",
            "user@example.com",
            CommentType.PUBLIC
        )
    
    @pytest.mark.asyncio
    async def test_execute_invalid_comment_type_filter(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test error with invalid comment type filter"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        
        # Create request with invalid filter
        request = ViewCommentsRequest(
            ticket_number="TKT-001",
            user_email="user@example.com",
            comment_type_filter="invalid_type"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Invalid comment type: invalid_type"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_get_recent_ticket_numbers_for_user(self, use_case, mock_repositories, sample_ticket):
        """Test getting recent ticket numbers for user"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mock
        ticket_repo.get_recent_tickets.return_value = [sample_ticket]
        
        # Execute
        ticket_numbers = await use_case.get_recent_ticket_numbers_for_user("user@example.com", 5)
        
        # Verify
        assert ticket_numbers == ["TKT-001"]
        ticket_repo.get_recent_tickets.assert_called_once_with("user@example.com", 5)
    
    @pytest.mark.asyncio
    async def test_search_tickets_for_comments(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test searching tickets for comment viewing"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        user_repo.get_by_email.return_value = sample_user
        ticket_repo.search_tickets.return_value = [sample_ticket]
        
        # Execute
        tickets = await use_case.search_tickets_for_comments("user@example.com", "test query")
        
        # Verify
        assert len(tickets) == 1
        assert tickets[0].number == "TKT-001"
        
        # Verify repository calls
        user_repo.get_by_email.assert_called_once_with("user@example.com")
        ticket_repo.search_tickets.assert_called_once_with(
            query="test query",
            user_email="user@example.com",
            limit=10
        )
    
    @pytest.mark.asyncio
    async def test_search_tickets_user_not_found(self, use_case, mock_repositories):
        """Test search tickets when user not found"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mock
        user_repo.get_by_email.return_value = None
        
        # Execute and verify error
        with pytest.raises(ValueError, match="User nonexistent@example.com not found"):
            await use_case.search_tickets_for_comments("nonexistent@example.com", "query")
    
    @pytest.mark.asyncio
    async def test_admin_can_view_all_tickets(self, use_case, mock_repositories, sample_ticket):
        """Test admin user can view tickets they didn't create"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Create admin user
        admin_user = User(
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN
        )
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = admin_user
        comment_repo.get_by_ticket_number.return_value = []
        comment_repo.get_comment_count_by_ticket.return_value = 0
        
        # Create request (admin viewing user's ticket)
        request = ViewCommentsRequest(
            ticket_number="TKT-001",
            user_email="admin@example.com"
        )
        
        # Execute use case - should not raise permission error
        response = await use_case.execute(request)
        
        # Verify admin can access
        assert response.ticket.number == "TKT-001"
        assert response.user_can_add_internal_comment  # Admin can add internal comments