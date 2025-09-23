"""
Unit tests for AddCommentUseCase.
Tests business logic with mocked repositories.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.application.use_cases.add_comment import AddCommentUseCase
from src.application.dto import AddCommentRequest, AddCommentResponse
from src.domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from src.domain.entities.comment import Comment, CommentType
from src.domain.entities.user import User, UserRole


class TestAddCommentUseCase:
    """Test AddCommentUseCase"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        ticket_repo = Mock()
        comment_repo = Mock()
        user_repo = Mock()
        
        # Configure async methods
        ticket_repo.get_by_number = AsyncMock()
        ticket_repo.update = AsyncMock()
        
        comment_repo.create = AsyncMock()
        comment_repo.get_comment_count_by_ticket = AsyncMock()
        
        user_repo.get_by_email = AsyncMock()
        
        return ticket_repo, comment_repo, user_repo
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mocked dependencies"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        return AddCommentUseCase(ticket_repo, comment_repo, user_repo)
    
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
    def sample_agent(self):
        """Create sample agent user"""
        return User(
            email="agent@example.com",
            name="Agent User",
            role=UserRole.AGENT
        )
    
    @pytest.mark.asyncio
    async def test_execute_success_user_comment(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test successful comment addition by user"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        comment_repo.get_comment_count_by_ticket.return_value = 1
        
        # Mock comment creation
        created_comment = Comment(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="user@example.com"
        )
        comment_repo.create.return_value = created_comment
        
        # Create request
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="user@example.com"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify response
        assert isinstance(response, AddCommentResponse)
        assert response.comment.content == "Test comment"
        assert response.comment.author_email == "user@example.com"
        assert response.comment.comment_type == CommentType.PUBLIC.value
        assert response.total_comments == 1
        
        # Verify repository calls
        ticket_repo.get_by_number.assert_called_once_with("TKT-001")
        user_repo.get_by_email.assert_called_once_with("user@example.com")
        comment_repo.create.assert_called_once()
        comment_repo.get_comment_count_by_ticket.assert_called_once_with("TKT-001")
    
    @pytest.mark.asyncio
    async def test_execute_success_agent_internal_comment(self, use_case, mock_repositories, sample_ticket, sample_agent):
        """Test successful internal comment by agent"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_agent
        comment_repo.get_comment_count_by_ticket.return_value = 1
        
        # Mock comment creation
        created_comment = Comment(
            ticket_number="TKT-001",
            content="Internal note",
            author_email="agent@example.com",
            comment_type=CommentType.INTERNAL
        )
        comment_repo.create.return_value = created_comment
        
        # Create request for internal comment
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Internal note",
            author_email="agent@example.com",
            comment_type="internal"
        )
        
        # Execute use case
        response = await use_case.execute(request)
        
        # Verify response
        assert response.comment.comment_type == CommentType.INTERNAL.value
        
        # Verify comment created with internal type
        created_comment_arg = comment_repo.create.call_args[0][0]
        assert created_comment_arg.comment_type == CommentType.INTERNAL
    
    @pytest.mark.asyncio
    async def test_execute_ticket_not_found(self, use_case, mock_repositories):
        """Test error when ticket not found"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = None
        
        # Create request
        request = AddCommentRequest(
            ticket_number="NONEXISTENT",
            content="Test comment",
            author_email="user@example.com"
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
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="nonexistent@example.com"
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
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="other@example.com"
        )
        
        # Execute and verify permission error
        with pytest.raises(PermissionError, match="User cannot add comments to this ticket"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_invalid_comment_type(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test error with invalid comment type"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        
        # Create request with invalid comment type
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="user@example.com",
            comment_type="invalid_type"
        )
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Invalid comment type: invalid_type"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_user_cannot_add_internal_comment(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test regular user cannot add internal comments"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        
        # Create request for internal comment by regular user
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Internal note",
            author_email="user@example.com",
            comment_type="internal"
        )
        
        # Execute and verify permission error
        with pytest.raises(PermissionError, match="User cannot add internal comments"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_empty_content(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test validation error for empty content"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        
        # Create request with empty content
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="",
            author_email="user@example.com"
        )
        
        # Execute and verify validation error
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_content_too_long(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test validation error for content too long"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        
        # Create request with very long content
        long_content = "x" * 5001  # Exceeds 5000 character limit
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content=long_content,
            author_email="user@example.com"
        )
        
        # Execute and verify validation error
        with pytest.raises(ValueError, match="Comment content is too long"):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_updates_ticket_last_activity(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test that adding comment updates ticket's last activity"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        comment_repo.get_comment_count_by_ticket.return_value = 1
        
        # Mock comment creation
        created_comment = Comment(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="user@example.com"
        )
        comment_repo.create.return_value = created_comment
        
        # Create request
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="user@example.com"
        )
        
        # Execute use case
        await use_case.execute(request)
        
        # Verify ticket was updated (last activity timestamp)
        ticket_repo.update.assert_called_once()
        updated_ticket = ticket_repo.update.call_args[0][0]
        assert updated_ticket.number == "TKT-001"
    
    @pytest.mark.asyncio
    async def test_execute_repository_error_handling(self, use_case, mock_repositories, sample_ticket, sample_user):
        """Test handling of repository errors"""
        ticket_repo, comment_repo, user_repo = mock_repositories
        
        # Setup mocks
        ticket_repo.get_by_number.return_value = sample_ticket
        user_repo.get_by_email.return_value = sample_user
        
        # Make comment creation fail
        comment_repo.create.side_effect = Exception("Database error")
        
        # Create request
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="user@example.com"
        )
        
        # Execute and verify error propagation
        with pytest.raises(Exception, match="Database error"):
            await use_case.execute(request)
        
        # Verify ticket was not updated if comment creation failed
        ticket_repo.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_admin_can_add_to_any_ticket(self, use_case, mock_repositories, sample_ticket):
        """Test admin can add comments to any ticket"""
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
        comment_repo.get_comment_count_by_ticket.return_value = 1
        
        # Mock comment creation
        created_comment = Comment(
            ticket_number="TKT-001",
            content="Admin comment",
            author_email="admin@example.com"
        )
        comment_repo.create.return_value = created_comment
        
        # Create request (admin commenting on user's ticket)
        request = AddCommentRequest(
            ticket_number="TKT-001",
            content="Admin comment",
            author_email="admin@example.com"
        )
        
        # Execute use case - should not raise permission error
        response = await use_case.execute(request)
        
        # Verify admin can add comment
        assert response.comment.content == "Admin comment"
        assert response.comment.author_email == "admin@example.com"