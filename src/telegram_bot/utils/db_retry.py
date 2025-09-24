"""
Database retry utility for handling temporary connection issues during high load.
Simple and maintainable retry logic for production scenarios.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Any
import time

logger = logging.getLogger(__name__)

class DatabaseRetryConfig:
    """Configuration for database retry logic"""
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2.0
    MAX_DELAY = 10.0  # maximum delay between retries

def with_db_retry(max_retries: int = None, retry_delay: float = None):
    """
    Decorator to add retry logic to database operations.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 1.0)
    
    Usage:
        @with_db_retry()
        async def some_db_operation(self, ...):
            # database operation code
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            _max_retries = max_retries or DatabaseRetryConfig.MAX_RETRIES
            _retry_delay = retry_delay or DatabaseRetryConfig.RETRY_DELAY
            
            last_exception = None
            
            for attempt in range(_max_retries + 1):
                try:
                    # Try the database operation
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt == _max_retries:
                        logger.error(f"Database operation {func.__name__} failed after {_max_retries + 1} attempts: {str(e)}")
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        _retry_delay * (DatabaseRetryConfig.BACKOFF_MULTIPLIER ** attempt),
                        DatabaseRetryConfig.MAX_DELAY
                    )
                    
                    logger.warning(f"Database operation {func.__name__} attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f}s")
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            _max_retries = max_retries or DatabaseRetryConfig.MAX_RETRIES
            _retry_delay = retry_delay or DatabaseRetryConfig.RETRY_DELAY
            
            last_exception = None
            
            for attempt in range(_max_retries + 1):
                try:
                    # Try the database operation
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt == _max_retries:
                        logger.error(f"Database operation {func.__name__} failed after {_max_retries + 1} attempts: {str(e)}")
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        _retry_delay * (DatabaseRetryConfig.BACKOFF_MULTIPLIER ** attempt),
                        DatabaseRetryConfig.MAX_DELAY
                    )
                    
                    logger.warning(f"Database operation {func.__name__} attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f}s")
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator

# Pre-configured decorators for common use cases
db_retry = with_db_retry()  # Default configuration
db_retry_fast = with_db_retry(max_retries=2, retry_delay=0.5)  # For quick operations
db_retry_slow = with_db_retry(max_retries=5, retry_delay=2.0)  # For complex operations