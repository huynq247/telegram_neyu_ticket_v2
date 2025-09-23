"""
User domain entity for authorization and user management.
"""
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class UserRole(Enum):
    """User role enumeration"""
    USER = "user"           # Regular user - can create tickets, view own tickets
    AGENT = "agent"         # Support agent - can be assigned tickets, view assigned tickets
    ADMIN = "admin"         # Administrator - can view/modify all tickets
    MANAGER = "manager"     # Manager - can view reports, assign tickets


@dataclass
class User:
    """User domain entity with role-based permissions"""
    
    email: str
    name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    last_active_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate business rules after initialization"""
        self._validate_email()
        self._validate_name()
    
    def _validate_email(self) -> None:
        """Validate email format"""
        if not self.email or "@" not in self.email:
            raise ValueError("Valid email is required")
        
        # Basic email validation
        if len(self.email.split("@")) != 2:
            raise ValueError("Invalid email format")
    
    def _validate_name(self) -> None:
        """Validate user name"""
        if not self.name or not self.name.strip():
            raise ValueError("User name cannot be empty")
        
        if len(self.name.strip()) < 2:
            raise ValueError("User name must be at least 2 characters")
    
    def link_telegram_account(self, telegram_user_id: int, telegram_username: str) -> None:
        """Link Telegram account to user"""
        if not telegram_user_id:
            raise ValueError("Valid Telegram user ID is required")
        
        self.telegram_user_id = telegram_user_id
        self.telegram_username = telegram_username
    
    def update_last_active(self) -> None:
        """Update last active timestamp"""
        self.last_active_date = datetime.now()
    
    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
    
    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True
    
    def change_role(self, new_role: UserRole, changed_by_email: str) -> None:
        """Change user role with authorization check"""
        if not self._can_change_role(changed_by_email):
            raise PermissionError("User cannot change roles")
        
        self.role = new_role
    
    def _can_change_role(self, changed_by_email: str) -> bool:
        """Check if user can change roles (admin only)"""
        # TODO: Implement actual role check
        return "admin" in changed_by_email.lower()
    
    # Permission methods
    def can_create_tickets(self) -> bool:
        """Check if user can create tickets"""
        return self.is_active and self.role in [UserRole.USER, UserRole.AGENT, UserRole.ADMIN, UserRole.MANAGER]
    
    def can_view_ticket(self, ticket_creator_email: str, ticket_assignee_email: Optional[str] = None) -> bool:
        """Check if user can view a specific ticket"""
        if not self.is_active:
            return False
        
        # Admins and managers can view all tickets
        if self.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return True
        
        # Users can view their own tickets
        if self.email == ticket_creator_email:
            return True
        
        # Agents can view assigned tickets
        if self.role == UserRole.AGENT and self.email == ticket_assignee_email:
            return True
        
        return False
    
    def can_modify_ticket(self, ticket_creator_email: str, ticket_assignee_email: Optional[str] = None) -> bool:
        """Check if user can modify a specific ticket"""
        if not self.is_active:
            return False
        
        # Admins can modify all tickets
        if self.role == UserRole.ADMIN:
            return True
        
        # Agents can modify assigned tickets
        if self.role == UserRole.AGENT and self.email == ticket_assignee_email:
            return True
        
        return False
    
    def can_assign_tickets(self) -> bool:
        """Check if user can assign tickets to others"""
        return self.is_active and self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_view_all_tickets(self) -> bool:
        """Check if user can view all tickets"""
        return self.is_active and self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_view_reports(self) -> bool:
        """Check if user can view reports"""
        return self.is_active and self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return self.is_active and self.role == UserRole.ADMIN
    
    @property
    def display_name(self) -> str:
        """Get formatted display name"""
        return self.name.title()
    
    @property
    def short_email(self) -> str:
        """Get shortened email for display"""
        return self.email.split('@')[0]
    
    @property
    def role_display(self) -> str:
        """Get formatted role for display"""
        role_names = {
            UserRole.USER: "User",
            UserRole.AGENT: "Support Agent",
            UserRole.ADMIN: "Administrator",
            UserRole.MANAGER: "Manager"
        }
        return role_names.get(self.role, "Unknown")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'email': self.email,
            'name': self.name,
            'role': self.role.value,
            'is_active': self.is_active,
            'telegram_user_id': self.telegram_user_id,
            'telegram_username': self.telegram_username,
            'created_date': self.created_date.isoformat(),
            'last_active_date': self.last_active_date.isoformat() if self.last_active_date else None,
            'display_name': self.display_name,
            'short_email': self.short_email,
            'role_display': self.role_display
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user from dictionary"""
        return cls(
            email=data['email'],
            name=data['name'],
            role=UserRole(data.get('role', UserRole.USER.value)),
            is_active=data.get('is_active', True),
            telegram_user_id=data.get('telegram_user_id'),
            telegram_username=data.get('telegram_username'),
            created_date=datetime.fromisoformat(data['created_date']),
            last_active_date=datetime.fromisoformat(data['last_active_date']) if data.get('last_active_date') else None
        )
    
    @classmethod
    def create_from_telegram(
        cls, 
        email: str, 
        name: str, 
        telegram_user_id: int, 
        telegram_username: str,
        role: UserRole = UserRole.USER
    ) -> 'User':
        """Factory method for creating user from Telegram"""
        user = cls(email=email, name=name, role=role)
        user.link_telegram_account(telegram_user_id, telegram_username)
        return user