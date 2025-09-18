"""
Telegram Bot Validators Module
Chứa các function validation cho input
"""
import logging

logger = logging.getLogger(__name__)

class BotValidators:
    """Class chứa các validation methods"""
    
    @staticmethod
    def validate_description(description: str) -> tuple[bool, str]:
        """
        Validate mô tả ticket
        
        Args:
            description: Mô tả cần validate
            
        Returns:
            (is_valid, error_message)
        """
        if not description or not description.strip():
            return False, "❌ Mô tả không được để trống."
        
        if len(description.strip()) < 10:
            return False, "❌ Mô tả quá ngắn. Vui lòng nhập ít nhất 10 ký tự để mô tả vấn đề chi tiết hơn."
        
        if len(description.strip()) > 2000:
            return False, "❌ Mô tả quá dài. Vui lòng nhập tối đa 2000 ký tự."
        
        return True, ""
    
    @staticmethod
    def validate_user_data(user_data: dict) -> tuple[bool, str]:
        """
        Validate dữ liệu user trước khi tạo ticket
        
        Args:
            user_data: Dictionary chứa dữ liệu user
            
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['destination', 'description', 'priority', 'chat_id', 'username']
        
        for field in required_fields:
            if not user_data.get(field):
                logger.error(f"Missing field {field} in user data")
                return False, f"❌ Thiếu thông tin cần thiết: {field}"
        
        # Validate description
        desc_valid, desc_error = BotValidators.validate_description(user_data['description'])
        if not desc_valid:
            return False, desc_error
        
        # Validate priority
        if user_data['priority'] not in [1, 2, 3]:
            return False, "❌ Độ ưu tiên không hợp lệ."
        
        return True, ""
    
    @staticmethod
    def validate_destination(destination: str) -> bool:
        """
        Validate destination
        
        Args:
            destination: Tên destination
            
        Returns:
            True nếu hợp lệ
        """
        valid_destinations = ['Vietnam', 'Thailand', 'India', 'Philippines', 'Malaysia', 'Indonesia']
        return destination in valid_destinations