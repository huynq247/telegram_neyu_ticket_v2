"""
Unit tests for Comment domain entity.
Tests business logic and validation rules.
"""
import pytest
from datetime import datetime, timedelta
from src.domain.entities.comment import Comment, CommentType


class TestComment:
    """Test Comment domain entity"""
    
    def test_create_valid_comment(self):
        """Test creating a valid comment"""
        comment = Comment(
            ticket_number="TKT-001",
            content="This is a test comment",
            author_email="test@example.com"
        )
        
        assert comment.ticket_number == "TKT-001"
        assert comment.content == "This is a test comment"
        assert comment.author_email == "test@example.com"
        assert comment.comment_type == CommentType.PUBLIC
        assert not comment.is_edited
        assert comment.parent_comment_id is None
    
    def test_comment_validation_empty_ticket_number(self):
        """Test validation fails for empty ticket number"""
        with pytest.raises(ValueError, match="Ticket number cannot be empty"):
            Comment(
                ticket_number="",
                content="Valid content",
                author_email="test@example.com"
            )
    
    def test_comment_validation_empty_content(self):
        """Test validation fails for empty content"""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            Comment(
                ticket_number="TKT-001",
                content="",
                author_email="test@example.com"
            )
    
    def test_comment_validation_short_content(self):
        """Test validation fails for too short content"""
        with pytest.raises(ValueError, match="Comment must be at least 5 characters long"):
            Comment(
                ticket_number="TKT-001",
                content="Hi",
                author_email="test@example.com"
            )
    
    def test_comment_validation_long_content(self):
        """Test validation fails for too long content"""
        long_content = "x" * 5001
        with pytest.raises(ValueError, match="Comment cannot exceed 5000 characters"):
            Comment(
                ticket_number="TKT-001",
                content=long_content,
                author_email="test@example.com"
            )
    
    def test_comment_validation_invalid_email(self):
        """Test validation fails for invalid email"""
        with pytest.raises(ValueError, match="Valid author email is required"):
            Comment(
                ticket_number="TKT-001",
                content="Valid content",
                author_email="invalid-email"
            )
    
    def test_edit_comment_content(self):
        """Test editing comment content"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Original content",
            author_email="test@example.com"
        )
        
        # Edit as the author
        comment.edit_content("Updated content", "test@example.com")
        
        assert comment.content == "Updated content"
        assert comment.is_edited
        assert comment.updated_date is not None
    
    def test_edit_comment_unauthorized(self):
        """Test editing comment fails for unauthorized user"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Original content",
            author_email="test@example.com"
        )
        
        with pytest.raises(PermissionError, match="User cannot edit this comment"):
            comment.edit_content("Updated content", "other@example.com")
    
    def test_can_be_viewed_by_author(self):
        """Test comment can be viewed by author"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Test content",
            author_email="test@example.com"
        )
        
        assert comment.can_be_viewed_by("test@example.com")
    
    def test_can_be_viewed_by_assignee(self):
        """Test public comment can be viewed by assignee"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Test content",
            author_email="test@example.com",
            comment_type=CommentType.PUBLIC
        )
        
        assert comment.can_be_viewed_by("assignee@example.com", user_is_assignee=True)
    
    def test_internal_comment_visibility(self):
        """Test internal comment visibility rules"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Internal note",
            author_email="agent@example.com",
            comment_type=CommentType.INTERNAL
        )
        
        # Author can view
        assert comment.can_be_viewed_by("agent@example.com")
        
        # Assignee can view
        assert comment.can_be_viewed_by("assignee@example.com", user_is_assignee=True)
        
        # Regular user cannot view
        assert not comment.can_be_viewed_by("user@example.com", user_is_assignee=False)
    
    def test_system_comment_visibility(self):
        """Test system comment visibility"""
        comment = Comment(
            ticket_number="TKT-001",
            content="System generated message",
            author_email="system@internal",
            comment_type=CommentType.SYSTEM
        )
        
        # System comments visible to all
        assert comment.can_be_viewed_by("anyone@example.com")
    
    def test_can_be_edited_within_time_limit(self):
        """Test comment can be edited within time limit"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Test content",
            author_email="test@example.com"
        )
        
        # Should be editable immediately
        assert comment.can_be_edited_by("test@example.com")
    
    def test_cannot_be_edited_after_time_limit(self):
        """Test comment cannot be edited after time limit"""
        # Create comment with old timestamp
        old_date = datetime.now() - timedelta(hours=25)
        comment = Comment(
            ticket_number="TKT-001",
            content="Test content",
            author_email="test@example.com"
        )
        comment.created_date = old_date
        
        # Should not be editable after 24 hours
        assert not comment.can_be_edited_by("test@example.com")
    
    def test_system_comment_cannot_be_edited(self):
        """Test system comments cannot be edited"""
        comment = Comment(
            ticket_number="TKT-001",
            content="System message",
            author_email="system@internal",
            comment_type=CommentType.SYSTEM
        )
        
        assert not comment.can_be_edited_by("admin@example.com")
    
    def test_is_recent_property(self):
        """Test is_recent property"""
        # Recent comment
        comment = Comment(
            ticket_number="TKT-001",
            content="Test content",
            author_email="test@example.com"
        )
        
        assert comment.is_recent
        
        # Old comment
        old_date = datetime.now() - timedelta(hours=2)
        comment.created_date = old_date
        
        assert not comment.is_recent
    
    def test_display_author_property(self):
        """Test display_author property"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Test content",
            author_email="john.doe@example.com"
        )
        
        assert comment.display_author == "John Doe"
        
        # System comment
        system_comment = Comment(
            ticket_number="TKT-001",
            content="System message",
            author_email="system@internal",
            comment_type=CommentType.SYSTEM
        )
        
        assert system_comment.display_author == "System"
    
    def test_preview_content_property(self):
        """Test preview_content property"""
        # Short content
        short_comment = Comment(
            ticket_number="TKT-001",
            content="Short",
            author_email="test@example.com"
        )
        
        assert short_comment.preview_content == "Short"
        
        # Long content
        long_content = "x" * 150
        long_comment = Comment(
            ticket_number="TKT-001",
            content=long_content,
            author_email="test@example.com"
        )
        
        assert len(long_comment.preview_content) == 100
        assert long_comment.preview_content.endswith("...")
    
    def test_factory_methods(self):
        """Test factory methods for creating different comment types"""
        # Public comment
        public_comment = Comment.create_public_comment(
            "TKT-001",
            "Public message",
            "user@example.com"
        )
        
        assert public_comment.comment_type == CommentType.PUBLIC
        
        # Internal comment
        internal_comment = Comment.create_internal_comment(
            "TKT-001",
            "Internal note",
            "agent@example.com"
        )
        
        assert internal_comment.comment_type == CommentType.INTERNAL
        
        # System comment
        system_comment = Comment.create_system_comment(
            "TKT-001",
            "System message"
        )
        
        assert system_comment.comment_type == CommentType.SYSTEM
        assert system_comment.author_email == "system@internal"
    
    def test_to_dict_conversion(self):
        """Test converting comment to dictionary"""
        comment = Comment(
            ticket_number="TKT-001",
            content="Test content",
            author_email="test@example.com"
        )
        comment.id = 123
        
        comment_dict = comment.to_dict()
        
        assert comment_dict['id'] == 123
        assert comment_dict['ticket_number'] == "TKT-001"
        assert comment_dict['content'] == "Test content"
        assert comment_dict['author_email'] == "test@example.com"
        assert comment_dict['comment_type'] == CommentType.PUBLIC.value
        assert 'is_recent' in comment_dict
        assert 'display_author' in comment_dict
    
    def test_from_dict_conversion(self):
        """Test creating comment from dictionary"""
        comment_data = {
            'id': 123,
            'ticket_number': 'TKT-001',
            'content': 'Test content',
            'author_email': 'test@example.com',
            'comment_type': CommentType.PUBLIC.value,
            'created_date': datetime.now().isoformat(),
            'is_edited': False
        }
        
        comment = Comment.from_dict(comment_data)
        
        assert comment.id == 123
        assert comment.ticket_number == "TKT-001"
        assert comment.content == "Test content"
        assert comment.author_email == "test@example.com"
        assert comment.comment_type == CommentType.PUBLIC