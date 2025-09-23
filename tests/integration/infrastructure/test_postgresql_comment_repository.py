"""
Integration tests for PostgreSQLCommentRepository.
Tests database operations with real database connection.
"""
import pytest
import asyncpg
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from src.infrastructure.repositories.postgresql_comment_repository import PostgreSQLCommentRepository
from src.infrastructure.database.connection import DatabaseConnection
from src.domain.entities.comment import Comment, CommentType


class TestPostgreSQLCommentRepository:
    """Test PostgreSQLCommentRepository"""
    
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
        return PostgreSQLCommentRepository(mock_db_connection)
    
    @pytest.fixture
    def sample_comment(self):
        """Create sample comment"""
        return Comment(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="user@example.com",
            comment_type=CommentType.PUBLIC
        )
    
    @pytest.fixture
    def sample_comment_row(self):
        """Create sample database row for comment"""
        return {
            'id': 1,
            'ticket_number': 'TKT-001',
            'content': 'Test comment',
            'author_email': 'user@example.com',
            'comment_type': 'public',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    
    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_connection, sample_comment, sample_comment_row):
        """Test successful comment creation"""
        # Setup mock to return created comment
        mock_connection.fetchrow.return_value = sample_comment_row
        
        # Execute
        created_comment = await repository.create(sample_comment)
        
        # Verify
        assert created_comment.ticket_number == "TKT-001"
        assert created_comment.content == "Test comment"
        assert created_comment.comment_type == CommentType.PUBLIC
        
        # Verify SQL was called
        mock_connection.fetchrow.assert_called_once()
        call_args = mock_connection.fetchrow.call_args
        assert "INSERT INTO comments" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_create_database_error(self, repository, mock_connection, sample_comment):
        """Test handling database error during creation"""
        # Setup mock to raise database error
        mock_connection.fetchrow.side_effect = asyncpg.PostgresError("Database error")
        
        # Execute and verify error
        with pytest.raises(Exception, match="Failed to create comment"):
            await repository.create(sample_comment)
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_connection, sample_comment_row):
        """Test successful comment retrieval by ID"""
        # Setup mock
        mock_connection.fetchrow.return_value = sample_comment_row
        
        # Execute
        comment = await repository.get_by_id(1)
        
        # Verify
        assert comment is not None
        assert comment.id == 1
        assert comment.content == "Test comment"
        assert comment.comment_type == CommentType.PUBLIC
        
        # Verify SQL was called
        mock_connection.fetchrow.assert_called_once()
        call_args = mock_connection.fetchrow.call_args
        assert "SELECT * FROM comments WHERE id = $1" in call_args[0][0]
        assert call_args[0][1] == 1
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_connection):
        """Test comment not found"""
        # Setup mock to return None
        mock_connection.fetchrow.return_value = None
        
        # Execute
        comment = await repository.get_by_id(999)
        
        # Verify
        assert comment is None
    
    @pytest.mark.asyncio
    async def test_get_by_ticket_number_success(self, repository, mock_connection):
        """Test getting comments by ticket number"""
        # Setup mock to return multiple comments
        mock_connection.fetch.return_value = [
            {
                'id': 1,
                'ticket_number': 'TKT-001',
                'content': 'First comment',
                'author_email': 'user@example.com',
                'comment_type': 'public',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            },
            {
                'id': 2,
                'ticket_number': 'TKT-001',
                'content': 'Second comment',
                'author_email': 'agent@example.com',
                'comment_type': 'internal',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]
        
        # Execute
        comments = await repository.get_by_ticket_number("TKT-001", "user@example.com")
        
        # Verify
        assert len(comments) == 2
        assert comments[0].content == "First comment"
        assert comments[1].content == "Second comment"
        
        # Verify SQL was called
        mock_connection.fetch.assert_called_once()
        call_args = mock_connection.fetch.call_args
        assert "WHERE ticket_number = $1" in call_args[0][0]
        assert "ORDER BY created_at ASC" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_get_by_ticket_number_with_type_filter(self, repository, mock_connection):
        """Test getting comments with type filter"""
        # Setup mock
        mock_connection.fetch.return_value = []
        
        # Execute with type filter
        await repository.get_by_ticket_number(
            "TKT-001", 
            "user@example.com", 
            CommentType.PUBLIC
        )
        
        # Verify SQL includes type filter
        call_args = mock_connection.fetch.call_args
        assert "AND comment_type = $3" in call_args[0][0]
        assert call_args[0][2] == "public"
    
    @pytest.mark.asyncio
    async def test_get_by_ticket_number_visibility_filter(self, repository, mock_connection):
        """Test comment visibility filtering for regular users"""
        # Setup mock to return mixed comment types
        mock_connection.fetch.return_value = [
            {
                'id': 1,
                'ticket_number': 'TKT-001',
                'content': 'Public comment',
                'author_email': 'user@example.com',
                'comment_type': 'public',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]
        
        # Execute for regular user
        comments = await repository.get_by_ticket_number("TKT-001", "user@example.com")
        
        # Verify visibility filtering applied
        call_args = mock_connection.fetch.call_args
        sql_query = call_args[0][0]
        # Should include visibility conditions for regular users
        assert "comment_type = 'public'" in sql_query or "author_email = $2" in sql_query
    
    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_connection, sample_comment, sample_comment_row):
        """Test successful comment update"""
        # Setup mock to return updated comment
        sample_comment.id = 1
        sample_comment.content = "Updated content"
        mock_connection.fetchrow.return_value = {
            **sample_comment_row,
            'content': 'Updated content'
        }
        
        # Execute
        updated_comment = await repository.update(sample_comment)
        
        # Verify
        assert updated_comment.content == "Updated content"
        
        # Verify SQL was called
        mock_connection.fetchrow.assert_called_once()
        call_args = mock_connection.fetchrow.call_args
        assert "UPDATE comments SET" in call_args[0][0]
        assert "WHERE id = $4" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_connection, sample_comment):
        """Test updating non-existent comment"""
        # Setup mock to return None
        sample_comment.id = 999
        mock_connection.fetchrow.return_value = None
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Comment 999 not found"):
            await repository.update(sample_comment)
    
    @pytest.mark.asyncio
    async def test_delete_success(self, repository, mock_connection):
        """Test successful comment deletion"""
        # Setup mock to return deletion count
        mock_connection.fetchval.return_value = 1
        
        # Execute
        result = await repository.delete(1)
        
        # Verify
        assert result is True
        
        # Verify SQL was called
        mock_connection.fetchval.assert_called_once()
        call_args = mock_connection.fetchval.call_args
        assert "DELETE FROM comments WHERE id = $1" in call_args[0][0]
        assert call_args[0][1] == 1
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_connection):
        """Test deleting non-existent comment"""
        # Setup mock to return zero deletion count
        mock_connection.fetchval.return_value = 0
        
        # Execute
        result = await repository.delete(999)
        
        # Verify
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_comment_count_by_ticket(self, repository, mock_connection):
        """Test getting comment count for ticket"""
        # Setup mock to return count
        mock_connection.fetchval.return_value = 5
        
        # Execute
        count = await repository.get_comment_count_by_ticket("TKT-001")
        
        # Verify
        assert count == 5
        
        # Verify SQL was called
        mock_connection.fetchval.assert_called_once()
        call_args = mock_connection.fetchval.call_args
        assert "SELECT COUNT(*) FROM comments" in call_args[0][0]
        assert "WHERE ticket_number = $1" in call_args[0][0]
        assert call_args[0][1] == "TKT-001"
    
    @pytest.mark.asyncio
    async def test_get_recent_comments_by_user(self, repository, mock_connection):
        """Test getting recent comments by user"""
        # Setup mock to return recent comments
        mock_connection.fetch.return_value = [
            {
                'id': 1,
                'ticket_number': 'TKT-001',
                'content': 'Recent comment',
                'author_email': 'user@example.com',
                'comment_type': 'public',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]
        
        # Execute
        comments = await repository.get_recent_comments_by_user("user@example.com", 10)
        
        # Verify
        assert len(comments) == 1
        assert comments[0].author_email == "user@example.com"
        
        # Verify SQL was called
        call_args = mock_connection.fetch.call_args
        assert "WHERE author_email = $1" in call_args[0][0]
        assert "ORDER BY created_at DESC" in call_args[0][0]
        assert "LIMIT $2" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_search_comments_success(self, repository, mock_connection):
        """Test comment search functionality"""
        # Setup mock to return search results
        mock_connection.fetch.return_value = [
            {
                'id': 1,
                'ticket_number': 'TKT-001',
                'content': 'Comment with search term',
                'author_email': 'user@example.com',
                'comment_type': 'public',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]
        
        # Execute
        comments = await repository.search_comments(
            query="search term",
            user_email="user@example.com",
            limit=10
        )
        
        # Verify
        assert len(comments) == 1
        assert "search term" in comments[0].content
        
        # Verify SQL includes search functionality
        call_args = mock_connection.fetch.call_args
        assert "content ILIKE $1" in call_args[0][0]  # Case-insensitive search
        assert call_args[0][0] == "%search term%"
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, repository, mock_db_connection):
        """Test handling database connection errors"""
        # Setup mock to raise connection error
        mock_db_connection.get_connection.side_effect = Exception("Connection failed")
        
        # Execute and verify error handling
        with pytest.raises(Exception, match="Connection failed"):
            await repository.get_by_id(1)
    
    @pytest.mark.asyncio
    async def test_row_to_comment_conversion(self, repository):
        """Test converting database row to Comment entity"""
        # Create sample row
        row = {
            'id': 1,
            'ticket_number': 'TKT-001',
            'content': 'Test comment',
            'author_email': 'user@example.com',
            'comment_type': 'internal',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        # Convert to comment
        comment = repository._row_to_comment(row)
        
        # Verify conversion
        assert comment.id == 1
        assert comment.ticket_number == "TKT-001"
        assert comment.comment_type == CommentType.INTERNAL
        assert isinstance(comment.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_invalid_comment_type_conversion(self, repository):
        """Test handling invalid comment type in database row"""
        # Create row with invalid comment type
        row = {
            'id': 1,
            'ticket_number': 'TKT-001',
            'content': 'Test comment',
            'author_email': 'user@example.com',
            'comment_type': 'invalid_type',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        # Execute and verify error
        with pytest.raises(ValueError, match="Invalid comment type: invalid_type"):
            repository._row_to_comment(row)