"""
Telegram Bot Formatters Module
Chứa các function format message và text
"""
from typing import Dict, Any

class BotFormatters:
    """Class chứa các formatting methods"""
    
    # Emoji mapping cho destinations
    DESTINATION_EMOJIS = {
        'Vietnam': '🇻🇳',
        'Thailand': '🇹🇭', 
        'India': '🇮🇳',
        'Philippines': '🇵🇭',
        'Malaysia': '🇲🇾',
        'Indonesia': '🇮🇩'
    }
    
    # Priority mapping
    PRIORITY_MAP = {
        'priority_high': (3, '🔴 Cao'),
        'priority_medium': (2, '🟡 Trung bình'),
        'priority_low': (1, '🟢 Thấp')
    }
    
    # Status emojis
    STATUS_EMOJIS = {
        'new': '🆕',
        'assigned': '👤',
        'solved': '✅',
        'closed': '🔒'
    }
    
    # Priority emojis
    PRIORITY_EMOJIS = {
        0: '⚫',
        1: '🟢',
        2: '🟡',
        3: '🔴'
    }
    
    @staticmethod
    def format_welcome_message(first_name: str) -> str:
        """Format welcome message"""
        return (
            f"Chào mừng {first_name}! 👋\n"
            "Tôi là bot hỗ trợ tạo ticket.\n"
            "Sử dụng các lệnh sau:\n\n"
            "/newticket - Tạo ticket mới\n"
            "/mytickets - Xem tickets của bạn\n"
            "/help - Hướng dẫn sử dụng"
        )
    
    @staticmethod
    def format_help_message() -> str:
        """Format help message"""
        return (
            "📋 *Hướng dẫn sử dụng Bot*\n\n"
            "🆕 */newticket* - Tạo ticket hỗ trợ mới\n"
            "📝 */mytickets* - Xem danh sách tickets của bạn\n"
            "❓ */help* - Hiển thị hướng dẫn này\n\n"
            "💡 *Cách tạo ticket:*\n"
            "1. Gõ /newticket\n"
            "2. Chọn điểm đến\n"
            "3. Nhập mô tả vấn đề\n"
            "4. Chọn độ ưu tiên\n"
            "5. Xác nhận tạo ticket\n\n"
            "✅ Bạn sẽ nhận được thông báo khi ticket được xử lý xong!"
        )
    
    @staticmethod
    def format_destination_selection() -> str:
        """Format destination selection message"""
        return (
            "🌍 *Chọn điểm đến cho ticket:*\n\n"
            "Vui lòng chọn quốc gia/khu vực mà bạn cần hỗ trợ:"
        )
    
    @staticmethod
    def format_destination_selected(destination: str) -> str:
        """Format destination selected message"""
        emoji = BotFormatters.DESTINATION_EMOJIS.get(destination, '🌍')
        return (
            f"✅ Đã chọn: {emoji} *{destination}*\n\n"
            "📝 Vui lòng nhập mô tả chi tiết vấn đề của bạn:"
        )
    
    @staticmethod
    def format_priority_selection() -> str:
        """Format priority selection message"""
        return (
            "⚡ *Chọn độ ưu tiên cho ticket:*\n\n"
            "🔴 *Cao* - Vấn đề khẩn cấp, cần xử lý ngay\n"
            "🟡 *Trung bình* - Vấn đề quan trọng, xử lý trong ngày\n"
            "🟢 *Thấp* - Vấn đề thông thường, xử lý khi có thời gian"
        )
    
    @staticmethod
    def format_ticket_confirmation(user_data: Dict[str, Any], priority_text: str) -> str:
        """Format ticket confirmation message"""
        destination = user_data.get('destination', 'Vietnam')
        emoji = BotFormatters.DESTINATION_EMOJIS.get(destination, '🌍')
        
        return (
            "📋 *Xác nhận thông tin ticket:*\n\n"
            f"👤 *Người tạo:* {user_data['first_name']}\n"
            f"🌍 *Điểm đến:* {emoji} {destination}\n"
            f"📝 *Mô tả:* {user_data['description']}\n"
            f"⚡ *Độ ưu tiên:* {priority_text}\n\n"
            "Xác nhận tạo ticket?"
        )
    
    @staticmethod
    def format_ticket_success(result: Dict[str, Any], user_data: Dict[str, Any]) -> str:
        """Format ticket creation success message"""
        destination = user_data.get('destination', 'Vietnam')
        emoji = BotFormatters.DESTINATION_EMOJIS.get(destination, '🌍')
        
        ticket_number = result.get('ticket_number', f"#{result['ticket_id']}")
        ticket_name = result.get('ticket_name', 'From Telegram')
        destination_code = result.get('destination_code', destination[:2].upper())
        
        return (
            "✅ *Ticket đã được tạo thành công!*\n\n"
            f"🎫 *Mã ticket:* `{ticket_number}`\n"
            f"📝 *Tên:* {ticket_name}\n"
            f"🌍 *Điểm đến:* {emoji} {destination} ({destination_code})\n"
            f"📄 *Mô tả:* {user_data['description'][:100]}...\n\n"
            "Chúng tôi sẽ xử lý và thông báo kết quả cho bạn sớm nhất!"
        )
    
    @staticmethod
    def format_ticket_error(error_message: str) -> str:
        """Format ticket creation error message"""
        return (
            "❌ *Lỗi tạo ticket!*\n\n"
            f"📝 *Lỗi:* {error_message}\n\n"
            "Vui lòng thử lại sau hoặc liên hệ admin."
        )
    
    @staticmethod
    def format_tickets_list(tickets: list) -> str:
        """Format tickets list message"""
        if not tickets:
            return (
                "📋 Bạn chưa có ticket nào.\n"
                "Sử dụng /newticket để tạo ticket mới."
            )
        
        message = "📋 *Danh sách tickets của bạn:*\n\n"
        
        for ticket in tickets[-10:]:  # Hiển thị 10 tickets gần nhất
            status_emoji = BotFormatters.STATUS_EMOJIS.get(
                ticket.get('stage', 'new'), '❓'
            )
            priority_emoji = BotFormatters.PRIORITY_EMOJIS.get(
                ticket.get('priority', 1), '🟡'
            )
            
            message += (
                f"{status_emoji} *{ticket.get('name', 'Unknown')}*\n"
                f"🎫 `{ticket.get('ticket_number', 'N/A')}`\n"
                f"{priority_emoji} Priority: {ticket.get('priority', 1)}\n"
                f"📅 {ticket.get('create_date', 'N/A')}\n\n"
            )
        
        if len(message) > 4000:
            message = message[:4000] + "\n\n... (hiển thị 10 tickets gần nhất)"
        
        return message