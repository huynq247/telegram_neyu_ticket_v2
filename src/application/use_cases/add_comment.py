"""
Use case for adding comments to a ticket.
Contains pure business logic for comment creation with validation and notifications.
"""
from typing import List
from ..dto import AddCommentRequest, AddCommentResponse, CommentDTO
from ...domain.repositories import TicketRepository, CommentRepository, UserRepository
from ...domain.services import CommentDomainService, TicketDomainService, NotificationDomainService
from ...domain.entities.comment import Comment, CommentType
from ...domain.entities.user import UserRole


class AddCommentUseCase:
    """Use case for adding comments to tickets"""
    
    def __init__(
        self,
        ticket_repository: TicketRepository,
        comment_repository: CommentRepository,
        user_repository: UserRepository
    ):
        self.ticket_repository = ticket_repository
        self.comment_repository = comment_repository
        self.user_repository = user_repository
    
    async def execute(self, request: AddCommentRequest) -> AddCommentResponse:
        """Execute the add comment use case"""
        
        # 1. Validate and get the ticket
        ticket = await self.ticket_repository.get_by_number(request.ticket_number)
        if not ticket:
            raise ValueError(f"Ticket {request.ticket_number} not found")
        
        # 2. Get the requesting user
        user = await self.user_repository.get_by_email(request.author_email)
        if not user:
            raise ValueError(f"User {request.author_email} not found")
        
        # 3. Validate comment type
        try:
            comment_type = CommentType(request.comment_type)
        except ValueError:
            raise ValueError(f"Invalid comment type: {request.comment_type}")
        
        # 4. Check if user can add this type of comment
        if not CommentDomainService.can_user_add_comment(user, ticket, comment_type):
            raise PermissionError(f"User cannot add {comment_type.value} comments to this ticket")
        
        # 5. Validate parent comment if this is a reply
        if request.parent_comment_id:
            parent_comment = await self.comment_repository.get_by_id(request.parent_comment_id)
            if not parent_comment:
                raise ValueError(f"Parent comment {request.parent_comment_id} not found")
            
            if parent_comment.ticket_number != request.ticket_number:
                raise ValueError("Parent comment must be from the same ticket")
            
            # Check if user can view the parent comment
            if not CommentDomainService.can_user_view_comment(user, parent_comment, ticket):
                raise PermissionError("User cannot reply to this comment")
        
        # 6. Create the comment domain entity
        if comment_type == CommentType.PUBLIC:
            comment = Comment.create_public_comment(
                ticket_number=request.ticket_number,
                content=request.content,
                author_email=request.author_email,
                parent_comment_id=request.parent_comment_id
            )
        elif comment_type == CommentType.INTERNAL:
            comment = Comment.create_internal_comment(
                ticket_number=request.ticket_number,
                content=request.content,
                author_email=request.author_email
            )
        else:
            # System comments should not be created through this use case
            raise ValueError("System comments cannot be created directly")
        
        # 7. Save the comment
        saved_comment = await self.comment_repository.save(comment)
        
        # 8. Update user's last active date
        user.update_last_active()
        await self.user_repository.save(user)
        
        # 9. Handle notifications
        notification_sent = await self._handle_notifications(saved_comment, ticket, user)
        
        # 10. Create success message
        success_message = self._create_success_message(saved_comment, ticket)
        
        # 11. Convert to DTO and return response
        comment_dto = CommentDTO.from_domain(saved_comment)
        
        return AddCommentResponse(
            comment=comment_dto,
            notification_sent=notification_sent,
            success_message=success_message
        )
    
    async def _handle_notifications(self, comment: Comment, ticket, user) -> bool:
        """Handle notifications for new comment"""
        try:
            # Get list of users to notify
            notify_emails = CommentDomainService.should_notify_on_comment(comment, ticket)
            
            # TODO: Implement actual notification sending
            # For now, just simulate notification logic
            notification_count = 0
            
            for email in notify_emails:
                notify_user = await self.user_repository.get_by_email(email)
                if notify_user and NotificationDomainService.should_send_notification(notify_user, "comment_added"):
                    # TODO: Send actual notification (email, telegram, etc.)
                    notification_count += 1
            
            return notification_count > 0
            
        except Exception as e:
            # Don't fail the whole operation if notifications fail
            # TODO: Log the error
            return False
    
    def _create_success_message(self, comment: Comment, ticket) -> str:
        """Create success message for comment addition"""
        if comment.comment_type == CommentType.INTERNAL:
            return f"✅ Internal comment added to ticket {ticket.number}"
        elif comment.parent_comment_id:
            return f"✅ Reply added to ticket {ticket.number}"
        else:
            return f"✅ Comment added to ticket {ticket.number}"
    
    async def get_comment_templates(self, user_email: str, ticket_number: str) -> List[str]:
        """Get comment templates based on user role and ticket context"""
        user = await self.user_repository.get_by_email(user_email)
        if not user:
            return []
        
        ticket = await self.ticket_repository.get_by_number(ticket_number)
        if not ticket:
            return []
        
        templates = []
        
        # Common templates for all users
        templates.extend([
            "Thanks for the update!",
            "Could you provide more details about this issue?",
            "I'm working on this now.",
        ])
        
        # Role-specific templates
        if user.role in [UserRole.AGENT, UserRole.ADMIN]:
            templates.extend([
                "This issue has been resolved. Please let me know if you need anything else.",
                "I've escalated this to our technical team for further investigation.",
                "Could you please try the solution and let me know if it works?",
                "This is a known issue. We're working on a fix.",
            ])
        
        if user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            templates.extend([
                "Assigning this to our specialist team.",
                "This requires additional approval. I'll get back to you shortly.",
                "Closing this ticket as resolved.",
            ])
        
        return templates
    
    async def validate_comment_content(self, content: str, user_email: str) -> List[str]:
        """Validate comment content and return any warnings"""
        warnings = []
        
        # Check content length
        if len(content.strip()) < 5:
            warnings.append("Comment seems very short. Consider adding more detail.")
        
        if len(content) > 2000:
            warnings.append("Comment is quite long. Consider breaking it into multiple comments.")
        
        # Check for potentially sensitive information
        sensitive_keywords = ["password", "credit card", "ssn", "social security"]
        content_lower = content.lower()
        
        for keyword in sensitive_keywords:
            if keyword in content_lower:
                warnings.append(f"⚠️ Warning: Comment may contain sensitive information ({keyword})")
        
        # Check for profanity or inappropriate content (basic check)
        inappropriate_words = ["damn", "hell"]  # This would be more comprehensive in real app
        for word in inappropriate_words:
            if word in content_lower:
                warnings.append("⚠️ Warning: Please keep comments professional")
                break
        
        return warnings