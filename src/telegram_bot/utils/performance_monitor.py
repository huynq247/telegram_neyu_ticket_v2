"""
Performance monitoring utility for identifying bottlenecks during multi-user usage.
Simple response time logging and basic metrics collection.
"""

import logging
import time
import asyncio
from functools import wraps
from typing import Dict, Any, Callable, Optional
from collections import defaultdict, deque
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Simple performance metrics collector"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.response_times = defaultdict(lambda: deque(maxlen=max_history))
        self.call_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.slow_operations = deque(maxlen=100)  # Track slowest operations
        self.start_time = datetime.now()
    
    def record_response_time(self, operation: str, duration: float, success: bool = True):
        """Record response time for an operation"""
        self.response_times[operation].append(duration)
        self.call_counts[operation] += 1
        
        if not success:
            self.error_counts[operation] += 1
        
        # Track slow operations (> 2 seconds)
        if duration > 2.0:
            self.slow_operations.append({
                'operation': operation,
                'duration': duration,
                'timestamp': datetime.now(),
                'success': success
            })
            logger.warning(f"Slow operation detected: {operation} took {duration:.2f}s")
    
    def get_stats(self, operation: str = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if operation:
            # Stats for specific operation
            times = list(self.response_times[operation])
            if not times:
                return {'operation': operation, 'no_data': True}
            
            return {
                'operation': operation,
                'call_count': self.call_counts[operation],
                'error_count': self.error_counts[operation],
                'avg_response_time': sum(times) / len(times),
                'min_response_time': min(times),
                'max_response_time': max(times),
                'error_rate': self.error_counts[operation] / self.call_counts[operation] if self.call_counts[operation] > 0 else 0
            }
        else:
            # Overall stats
            total_calls = sum(self.call_counts.values())
            total_errors = sum(self.error_counts.values())
            
            # Get average response times per operation
            operation_stats = {}
            for op in self.response_times.keys():
                times = list(self.response_times[op])
                if times:
                    operation_stats[op] = {
                        'calls': self.call_counts[op],
                        'avg_time': sum(times) / len(times),
                        'errors': self.error_counts[op]
                    }
            
            return {
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'total_calls': total_calls,
                'total_errors': total_errors,
                'overall_error_rate': total_errors / total_calls if total_calls > 0 else 0,
                'operations': operation_stats,
                'slow_operations_count': len(self.slow_operations),
                'recent_slow_operations': list(self.slow_operations)[-5:]  # Last 5 slow operations
            }
    
    def log_performance_summary(self):
        """Log a performance summary"""
        stats = self.get_stats()
        logger.info(f"Performance Summary - Uptime: {stats['uptime_seconds']:.0f}s, "
                   f"Total calls: {stats['total_calls']}, "
                   f"Error rate: {stats['overall_error_rate']:.1%}, "
                   f"Slow operations: {stats['slow_operations_count']}")

# Global metrics instance
_metrics = PerformanceMetrics()

def monitor_performance(operation_name: str = None):
    """
    Decorator to monitor performance of functions/methods.
    
    Args:
        operation_name: Custom name for the operation (default: function name)
    
    Usage:
        @monitor_performance("user_authentication")
        async def authenticate_user(self, ...):
            # function code
    """
    
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                _metrics.record_response_time(op_name, duration, success)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                _metrics.record_response_time(op_name, duration, success)
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator

def get_performance_stats(operation: str = None) -> Dict[str, Any]:
    """Get performance statistics"""
    return _metrics.get_stats(operation)

def log_performance_summary():
    """Log performance summary"""
    _metrics.log_performance_summary()

# Pre-configured decorators for common operations
monitor_auth = monitor_performance("authentication")
monitor_db = monitor_performance("database_operation")
monitor_api = monitor_performance("api_call")