"""
Memory optimization utilities for improving concurrent user capacity.
Simple memory management and cleanup helpers.
"""

import gc
import logging
import weakref
from typing import Dict, Any, Optional, Set
from functools import wraps
import time

logger = logging.getLogger(__name__)

class MemoryManager:
    """Simple memory management helper"""
    
    def __init__(self):
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        self._weak_refs: Set[weakref.ref] = set()
    
    def register_for_cleanup(self, obj):
        """Register an object for automatic cleanup"""
        def cleanup_callback(ref):
            self._weak_refs.discard(ref)
        
        weak_ref = weakref.ref(obj, cleanup_callback)
        self._weak_refs.add(weak_ref)
    
    def force_cleanup(self):
        """Force garbage collection and cleanup"""
        # Remove dead weak references
        dead_refs = {ref for ref in self._weak_refs if ref() is None}
        self._weak_refs -= dead_refs
        
        # Force garbage collection
        collected = gc.collect()
        
        logger.info(f"Memory cleanup: {collected} objects collected, {len(self._weak_refs)} objects tracked")
        self.last_cleanup = time.time()
    
    def maybe_cleanup(self):
        """Perform cleanup if interval has passed"""
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self.force_cleanup()

# Global memory manager
_memory_manager = MemoryManager()

def memory_optimized(cleanup_after: bool = False):
    """
    Decorator to add memory optimization to functions.
    
    Args:
        cleanup_after: Whether to run cleanup after function execution
    """
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                if cleanup_after:
                    _memory_manager.maybe_cleanup()
        
        return wrapper
    return decorator

def optimize_dict(data: Dict[str, Any], keep_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Optimize dictionary by removing None values and keeping only specified keys.
    
    Args:
        data: Dictionary to optimize
        keep_keys: Set of keys to keep (if None, keeps all non-None values)
    
    Returns:
        Optimized dictionary
    """
    if keep_keys:
        # Keep only specified keys that exist and are not None
        return {k: v for k, v in data.items() if k in keep_keys and v is not None}
    else:
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}

def cleanup_session_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize session data by keeping only essential fields.
    
    Args:
        session_data: Session data dictionary
    
    Returns:
        Optimized session data
    """
    essential_keys = {
        'user_id', 'email', 'user_type', 'login_time', 
        'last_activity', 'telegram_id', 'username', 'auth_method'
    }
    
    return optimize_dict(session_data, essential_keys)

class SessionCleanup:
    """Helper for cleaning up expired sessions"""
    
    @staticmethod
    def clean_expired_sessions(sessions: Dict[str, Dict[str, Any]], max_age_hours: int = 24) -> int:
        """
        Remove expired sessions from memory.
        
        Args:
            sessions: Dictionary of sessions
            max_age_hours: Maximum age of sessions in hours
        
        Returns:
            Number of sessions removed
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        expired_keys = []
        for session_id, session_data in sessions.items():
            last_activity = session_data.get('last_activity', 0)
            if current_time - last_activity > max_age_seconds:
                expired_keys.append(session_id)
        
        # Remove expired sessions
        for key in expired_keys:
            del sessions[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired sessions")
        
        return len(expired_keys)

def force_memory_cleanup():
    """Force immediate memory cleanup"""
    _memory_manager.force_cleanup()

def register_for_cleanup(obj):
    """Register object for automatic cleanup"""
    _memory_manager.register_for_cleanup(obj)