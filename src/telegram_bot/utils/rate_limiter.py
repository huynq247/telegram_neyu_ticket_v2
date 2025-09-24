"""
Simple Rate Limiter - Easy to maintain, no external dependencies
Built into bot handlers for immediate protection
"""

import time
from collections import defaultdict, deque
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SimpleRateLimiter:
    """
    Simple in-memory rate limiter
    Easy to understand and maintain
    """
    
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        """
        Args:
            max_requests: Max requests per time window
            time_window: Time window in seconds (default: 1 minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.user_requests = defaultdict(deque)
        self.last_cleanup = time.time()
    
    def is_allowed(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user request is allowed
        
        Returns:
            (is_allowed, remaining_requests)
        """
        now = time.time()
        
        # Cleanup old data every 5 minutes
        if now - self.last_cleanup > 300:
            self._cleanup_old_data(now)
            self.last_cleanup = now
        
        user_queue = self.user_requests[user_id]
        
        # Remove requests outside time window
        while user_queue and user_queue[0] <= now - self.time_window:
            user_queue.popleft()
        
        # Check rate limit
        current_requests = len(user_queue)
        if current_requests >= self.max_requests:
            remaining = 0
            allowed = False
            logger.warning(f"Rate limit exceeded for user {user_id}: {current_requests}/{self.max_requests}")
        else:
            user_queue.append(now)
            remaining = self.max_requests - current_requests - 1
            allowed = True
        
        return allowed, remaining
    
    def _cleanup_old_data(self, now: float):
        """Clean up old user data to prevent memory bloat"""
        users_to_remove = []
        
        for user_id, requests in self.user_requests.items():
            # Remove old requests
            while requests and requests[0] <= now - self.time_window:
                requests.popleft()
            
            # Remove users with no recent requests
            if not requests:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self.user_requests[user_id]
        
        if users_to_remove:
            logger.info(f"Cleaned up rate limiter data for {len(users_to_remove)} inactive users")

# Global rate limiter instance
rate_limiter = SimpleRateLimiter(max_requests=30, time_window=60)

def rate_limit_check(func):
    """
    Decorator for rate limiting Telegram handlers
    Simple and easy to apply
    """
    @wraps(func)
    async def wrapper(self, update, context, *args, **kwargs):
        user_id = update.effective_user.id
        allowed, remaining = rate_limiter.is_allowed(user_id)
        
        if not allowed:
            await update.message.reply_text(
                "⏰ **Rate limit exceeded!**\n\n"
                "You're sending too many requests. Please wait a moment before trying again.\n"
                f"Limit: 30 requests per minute\n\n"
                "💡 *Tip: Use /me for faster authentication!*",
                parse_mode='Markdown'
            )
            return
        
        # Log high usage users
        if remaining < 5:
            logger.info(f"User {user_id} has {remaining} requests remaining")
        
        return await func(self, update, context, *args, **kwargs)
    
    return wrapper