"""
Logging optimization utility để giảm spam logs và tối ưu performance monitoring
"""

import logging
import time
from typing import Dict, Any, Optional
from functools import wraps
from collections import defaultdict

class LogThrottler:
    """Throttle logs để tránh spam cùng một message"""
    
    def __init__(self, default_interval: int = 300):  # 5 minutes default
        self.default_interval = default_interval
        self.last_logged: Dict[str, float] = {}
        self.message_counts: Dict[str, int] = defaultdict(int)
    
    def should_log(self, message: str, interval: Optional[int] = None) -> bool:
        """
        Kiểm tra xem có nên log message này không
        
        Args:
            message: Log message
            interval: Custom interval (seconds)
        
        Returns:
            True nếu nên log, False nếu skip
        """
        current_time = time.time()
        check_interval = interval or self.default_interval
        
        # Tăng counter
        self.message_counts[message] += 1
        
        # Check last logged time
        last_time = self.last_logged.get(message, 0)
        
        if current_time - last_time >= check_interval:
            self.last_logged[message] = current_time
            return True
        
        return False
    
    def get_throttled_message(self, message: str) -> str:
        """
        Tạo message với thông tin về số lần skip
        
        Args:
            message: Original message
        
        Returns:
            Enhanced message với skip count
        """
        count = self.message_counts.get(message, 0)
        if count > 1:
            return f"{message} (đã skip {count-1} lần trong 5 phút qua)"
        return message
    
    def reset_counts(self):
        """Reset message counts"""
        self.message_counts.clear()
        self.last_logged.clear()

# Global throttler instance
_log_throttler = LogThrottler()

def throttled_log(logger, level: str, message: str, interval: Optional[int] = None):
    """
    Log message với throttling
    
    Args:
        logger: Logger instance
        level: Log level ('info', 'debug', 'warning', 'error')
        message: Message to log
        interval: Throttle interval in seconds
    """
    if _log_throttler.should_log(message, interval):
        enhanced_message = _log_throttler.get_throttled_message(message)
        getattr(logger, level)(enhanced_message)

def smart_log_info(logger, message: str, interval: int = 300):
    """Smart info logging với throttling"""
    throttled_log(logger, 'info', message, interval)

def smart_log_debug(logger, message: str, interval: int = 300):
    """Smart debug logging với throttling"""
    throttled_log(logger, 'debug', message, interval)

def smart_log_warning(logger, message: str, interval: int = 300):
    """Smart warning logging với throttling"""
    throttled_log(logger, 'warning', message, interval)

class PerformanceAwareLogger:
    """Logger wrapper với performance monitoring"""
    
    def __init__(self, logger):
        self.logger = logger
        self.throttler = LogThrottler()
    
    def info_throttled(self, message: str, interval: int = 300):
        """Info log với throttling"""
        if self.throttler.should_log(f"INFO_{message}", interval):
            enhanced = self.throttler.get_throttled_message(message)
            self.logger.info(enhanced)
    
    def debug_throttled(self, message: str, interval: int = 300):
        """Debug log với throttling"""
        if self.throttler.should_log(f"DEBUG_{message}", interval):
            enhanced = self.throttler.get_throttled_message(message)
            self.logger.debug(enhanced)
    
    def warning_throttled(self, message: str, interval: int = 300):
        """Warning log với throttling"""
        if self.throttler.should_log(f"WARNING_{message}", interval):
            enhanced = self.throttler.get_throttled_message(message)
            self.logger.warning(enhanced)
    
    def error(self, message: str):
        """Error log - không throttle vì quan trọng"""
        self.logger.error(message)
    
    def info(self, message: str):
        """Normal info log"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Normal debug log"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Normal warning log"""
        self.logger.warning(message)

def get_smart_logger(name: str) -> PerformanceAwareLogger:
    """Get smart logger instance với throttling"""
    base_logger = logging.getLogger(name)
    return PerformanceAwareLogger(base_logger)

# Utility functions
def reset_log_throttling():
    """Reset global log throttling"""
    _log_throttler.reset_counts()

def get_log_stats() -> Dict[str, Any]:
    """Get logging statistics"""
    return {
        'unique_messages': len(_log_throttler.message_counts),
        'total_attempts': sum(_log_throttler.message_counts.values()),
        'throttled_messages': list(_log_throttler.message_counts.keys())
    }