"""
Domain entities representing core business objects.
These are pure Python classes with business logic, no external dependencies.
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class TicketStatus(Enum):
    """Ticket status enumeration"""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class TicketPriority(Enum):
    """Ticket priority enumeration"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


@dataclass
class Ticket:
    """Ticket domain entity with business logic"""
    
    number: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    creator_email: str
    assignee_email: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    resolved_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate business rules after initialization"""
        if not self.number or not self.number.strip():
            raise ValueError("Ticket number cannot be empty")
        
        if not self.title or not self.title.strip():
            raise ValueError("Ticket title cannot be empty")
        
        if not self.creator_email or "@" not in self.creator_email:
            raise ValueError("Valid creator email is required")
    
    def assign_to(self, assignee_email: str) -> None:
        """Assign ticket to a user"""
        if not assignee_email or "@" not in assignee_email:
            raise ValueError("Valid assignee email is required")
        
        self.assignee_email = assignee_email
        self.updated_date = datetime.now()
    
    def change_status(self, new_status: TicketStatus) -> None:
        """Change ticket status with business rules"""
        if new_status == TicketStatus.RESOLVED and self.status != TicketStatus.IN_PROGRESS:
            raise ValueError("Ticket must be in progress before resolving")
        
        if new_status == TicketStatus.CLOSED and self.status != TicketStatus.RESOLVED:
            raise ValueError("Ticket must be resolved before closing")
        
        old_status = self.status
        self.status = new_status
        self.updated_date = datetime.now()
        
        if new_status == TicketStatus.RESOLVED and old_status != TicketStatus.RESOLVED:
            self.resolved_date = datetime.now()
    
    def change_priority(self, new_priority: TicketPriority) -> None:
        """Change ticket priority"""
        self.priority = new_priority
        self.updated_date = datetime.now()
    
    def can_be_viewed_by(self, user_email: str) -> bool:
        """Business rule: who can view this ticket"""
        return (
            self.creator_email == user_email or 
            self.assignee_email == user_email or
            self._is_admin_user(user_email)
        )
    
    def can_be_modified_by(self, user_email: str) -> bool:
        """Business rule: who can modify this ticket"""
        return (
            self.assignee_email == user_email or
            self._is_admin_user(user_email)
        )
    
    def _is_admin_user(self, user_email: str) -> bool:
        """Check if user has admin privileges (placeholder for business logic)"""
        # TODO: Implement actual admin check
        admin_domains = ["admin.com", "support.com"]
        return any(domain in user_email for domain in admin_domains)
    
    @property
    def is_overdue(self) -> bool:
        """Check if ticket is overdue (business rule placeholder)"""
        if self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return False
        
        # TODO: Implement actual SLA calculation
        days_since_created = (datetime.now() - self.created_date).days
        
        sla_days = {
            TicketPriority.URGENT: 1,
            TicketPriority.HIGH: 3,
            TicketPriority.MEDIUM: 7,
            TicketPriority.LOW: 14
        }
        
        return days_since_created > sla_days.get(self.priority, 7)
    
    @property
    def display_title(self) -> str:
        """Get formatted title for display"""
        return f"[{self.number}] {self.title}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'number': self.number,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority.value,
            'creator_email': self.creator_email,
            'assignee_email': self.assignee_email,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat(),
            'resolved_date': self.resolved_date.isoformat() if self.resolved_date else None,
            'is_overdue': self.is_overdue
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Ticket':
        """Create ticket from dictionary"""
        return cls(
            number=data['number'],
            title=data['title'],
            description=data['description'],
            status=TicketStatus(data['status']),
            priority=TicketPriority(data['priority']),
            creator_email=data['creator_email'],
            assignee_email=data.get('assignee_email'),
            created_date=datetime.fromisoformat(data['created_date']),
            updated_date=datetime.fromisoformat(data['updated_date']),
            resolved_date=datetime.fromisoformat(data['resolved_date']) if data.get('resolved_date') else None
        )