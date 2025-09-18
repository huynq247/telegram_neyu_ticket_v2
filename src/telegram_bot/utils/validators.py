"""
Telegram Bot Validators Module
Contains validation functions for input
"""
import logging

logger = logging.getLogger(__name__)

class BotValidators:
    """Class containing validation methods"""
    
    @staticmethod
    def validate_description(description: str) -> tuple[bool, str]:
        """
        Validate ticket description
        
        Args:
            description: Description to validate
            
        Returns:
            (is_valid, error_message)
        """
        if not description or not description.strip():
            return False, "❌ Description cannot be empty."
        
        if len(description.strip()) < 10:
            return False, "❌ Description too short. Please enter at least 10 characters to describe the problem in detail."
        
        if len(description.strip()) > 2000:
            return False, "❌ Description too long. Please enter a maximum of 2000 characters."
        
        return True, ""
    
    @staticmethod
    def validate_user_data(user_data: dict) -> tuple[bool, str]:
        """
        Validate user data before creating ticket
        
        Args:
            user_data: Dictionary containing user data
            
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['destination', 'description', 'priority', 'chat_id', 'username']
        
        for field in required_fields:
            if not user_data.get(field):
                logger.error(f"Missing field {field} in user data")
                return False, f"❌ Missing required information: {field}"
        
        # Validate description
        desc_valid, desc_error = BotValidators.validate_description(user_data['description'])
        if not desc_valid:
            return False, desc_error
        
        # Validate priority
        if user_data['priority'] not in [1, 2, 3]:
            return False, "❌ Invalid priority level."
        
        return True, ""
    
    @staticmethod
    def validate_destination(destination: str) -> bool:
        """
        Validate destination
        
        Args:
            destination: Destination name
            
        Returns:
            True if valid
        """
        valid_destinations = ['Vietnam', 'Thailand', 'India', 'Philippines', 'Malaysia', 'Indonesia']
        return destination in valid_destinations