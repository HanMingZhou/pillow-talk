"""Rate limiting service

Implements sliding window rate limiting for API requests.
"""
import time
import asyncio
from typing import Dict, List, Optional
from collections import defaultdict
import structlog

from ..utils.exceptions import RateLimitError


logger = structlog.get_logger(__name__)


class RateLimiter:
    """Rate limiter using sliding window algorithm
    
    Tracks request counts per IP address and API key within time windows.
    Thread-safe using asyncio locks.
    """
    
    def __init__(
        self,
        ip_limit_per_minute: int = 60,
        api_key_limit_per_minute: int = 100,
        window_size_seconds: int = 60,
        cleanup_interval_seconds: int = 300
    ):
        """Initialize rate limiter
        
        Args:
            ip_limit_per_minute: Maximum requests per IP per minute
            api_key_limit_per_minute: Maximum requests per API key per minute
            window_size_seconds: Time window size in seconds
            cleanup_interval_seconds: Interval for cleaning up expired records
        """
        self.ip_limit = ip_limit_per_minute
        self.api_key_limit = api_key_limit_per_minute
        self.window_size = window_size_seconds
        self.cleanup_interval = cleanup_interval_seconds
        
        # Storage for request timestamps
        # Format: {identifier: [timestamp1, timestamp2, ...]}
        self.ip_requests: Dict[str, List[float]] = defaultdict(list)
        self.api_key_requests: Dict[str, List[float]] = defaultdict(list)
        
        # Locks for thread safety
        self.ip_lock = asyncio.Lock()
        self.api_key_lock = asyncio.Lock()
        
        # Last cleanup time
        self.last_cleanup = time.time()
        
        logger.info(
            "Rate limiter initialized",
            ip_limit=ip_limit_per_minute,
            api_key_limit=api_key_limit_per_minute,
            window_size=window_size_seconds
        )
    
    async def check_rate_limit(
        self,
        ip_address: str,
        api_key: Optional[str] = None
    ) -> bool:
        """Check if request is within rate limits
        
        Args:
            ip_address: Client IP address
            api_key: API key (if provided)
            
        Returns:
            True if request is allowed
            
        Raises:
            RateLimitError: If rate limit is exceeded
            
        Examples:
            >>> limiter = RateLimiter()
            >>> await limiter.check_rate_limit("192.168.1.1", "sk-123")
            True
        """
        current_time = time.time()
        
        # Check IP rate limit
        async with self.ip_lock:
            if not await self._check_limit(
                identifier=ip_address,
                requests=self.ip_requests,
                limit=self.ip_limit,
                current_time=current_time,
                identifier_type="IP"
            ):
                logger.warning(
                    "IP rate limit exceeded",
                    ip_address=ip_address,
                    limit=self.ip_limit
                )
                raise RateLimitError(
                    f"Rate limit exceeded for IP {ip_address}. "
                    f"Maximum {self.ip_limit} requests per minute allowed."
                )
            
            # Record the request
            self.ip_requests[ip_address].append(current_time)
        
        # Check API key rate limit (if provided)
        if api_key:
            async with self.api_key_lock:
                if not await self._check_limit(
                    identifier=api_key,
                    requests=self.api_key_requests,
                    limit=self.api_key_limit,
                    current_time=current_time,
                    identifier_type="API key"
                ):
                    logger.warning(
                        "API key rate limit exceeded",
                        api_key_prefix=api_key[:10],
                        limit=self.api_key_limit
                    )
                    raise RateLimitError(
                        f"Rate limit exceeded for API key. "
                        f"Maximum {self.api_key_limit} requests per minute allowed."
                    )
                
                # Record the request
                self.api_key_requests[api_key].append(current_time)
        
        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            asyncio.create_task(self.cleanup_expired())
        
        logger.debug(
            "Rate limit check passed",
            ip_address=ip_address,
            has_api_key=api_key is not None
        )
        
        return True
    
    async def _check_limit(
        self,
        identifier: str,
        requests: Dict[str, List[float]],
        limit: int,
        current_time: float,
        identifier_type: str
    ) -> bool:
        """Check if identifier is within rate limit
        
        Uses sliding window algorithm.
        
        Args:
            identifier: IP address or API key
            requests: Request storage dictionary
            limit: Rate limit
            current_time: Current timestamp
            identifier_type: Type of identifier (for logging)
            
        Returns:
            True if within limit, False if exceeded
        """
        # Get request timestamps for this identifier
        timestamps = requests.get(identifier, [])
        
        # Remove timestamps outside the window
        window_start = current_time - self.window_size
        valid_timestamps = [ts for ts in timestamps if ts > window_start]
        
        # Update storage with valid timestamps
        requests[identifier] = valid_timestamps
        
        # Check if limit is exceeded
        request_count = len(valid_timestamps)
        
        logger.debug(
            "Rate limit check",
            identifier_type=identifier_type,
            identifier=identifier[:20] if len(identifier) > 20 else identifier,
            request_count=request_count,
            limit=limit,
            within_limit=request_count < limit
        )
        
        return request_count < limit
    
    async def cleanup_expired(self) -> None:
        """Clean up expired request records
        
        Removes timestamps outside the sliding window to prevent memory growth.
        """
        current_time = time.time()
        window_start = current_time - self.window_size
        
        logger.debug("Starting rate limiter cleanup")
        
        # Clean up IP requests
        async with self.ip_lock:
            cleaned_ips = 0
            for ip_address in list(self.ip_requests.keys()):
                timestamps = self.ip_requests[ip_address]
                valid_timestamps = [ts for ts in timestamps if ts > window_start]
                
                if not valid_timestamps:
                    # No valid timestamps, remove the entry
                    del self.ip_requests[ip_address]
                    cleaned_ips += 1
                else:
                    self.ip_requests[ip_address] = valid_timestamps
        
        # Clean up API key requests
        async with self.api_key_lock:
            cleaned_keys = 0
            for api_key in list(self.api_key_requests.keys()):
                timestamps = self.api_key_requests[api_key]
                valid_timestamps = [ts for ts in timestamps if ts > window_start]
                
                if not valid_timestamps:
                    # No valid timestamps, remove the entry
                    del self.api_key_requests[api_key]
                    cleaned_keys += 1
                else:
                    self.api_key_requests[api_key] = valid_timestamps
        
        self.last_cleanup = current_time
        
        logger.info(
            "Rate limiter cleanup completed",
            cleaned_ips=cleaned_ips,
            cleaned_keys=cleaned_keys,
            remaining_ips=len(self.ip_requests),
            remaining_keys=len(self.api_key_requests)
        )
    
    async def get_remaining_requests(
        self,
        ip_address: str,
        api_key: Optional[str] = None
    ) -> Dict[str, int]:
        """Get remaining requests for IP and API key
        
        Args:
            ip_address: Client IP address
            api_key: API key (if provided)
            
        Returns:
            Dictionary with remaining requests for IP and API key
            
        Examples:
            >>> limiter = RateLimiter()
            >>> remaining = await limiter.get_remaining_requests("192.168.1.1", "sk-123")
            >>> print(remaining)
            {'ip': 58, 'api_key': 98}
        """
        current_time = time.time()
        window_start = current_time - self.window_size
        
        result = {}
        
        # Get remaining requests for IP
        async with self.ip_lock:
            ip_timestamps = self.ip_requests.get(ip_address, [])
            valid_ip_timestamps = [ts for ts in ip_timestamps if ts > window_start]
            result['ip'] = max(0, self.ip_limit - len(valid_ip_timestamps))
        
        # Get remaining requests for API key
        if api_key:
            async with self.api_key_lock:
                key_timestamps = self.api_key_requests.get(api_key, [])
                valid_key_timestamps = [ts for ts in key_timestamps if ts > window_start]
                result['api_key'] = max(0, self.api_key_limit - len(valid_key_timestamps))
        
        return result
    
    async def reset_limits(
        self,
        ip_address: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> None:
        """Reset rate limits for specific IP or API key
        
        Useful for testing or manual intervention.
        
        Args:
            ip_address: IP address to reset (None to reset all IPs)
            api_key: API key to reset (None to reset all keys)
            
        Examples:
            >>> limiter = RateLimiter()
            >>> await limiter.reset_limits(ip_address="192.168.1.1")
            >>> await limiter.reset_limits(api_key="sk-123")
            >>> await limiter.reset_limits()  # Reset all
        """
        if ip_address:
            async with self.ip_lock:
                if ip_address in self.ip_requests:
                    del self.ip_requests[ip_address]
                    logger.info("Reset rate limit for IP", ip_address=ip_address)
        else:
            async with self.ip_lock:
                self.ip_requests.clear()
                logger.info("Reset all IP rate limits")
        
        if api_key:
            async with self.api_key_lock:
                if api_key in self.api_key_requests:
                    del self.api_key_requests[api_key]
                    logger.info("Reset rate limit for API key", api_key_prefix=api_key[:10])
        elif ip_address is None:
            # Only clear all keys if no specific identifier was provided
            async with self.api_key_lock:
                self.api_key_requests.clear()
                logger.info("Reset all API key rate limits")
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics
        
        Returns:
            Dictionary with statistics
            
        Examples:
            >>> limiter = RateLimiter()
            >>> stats = limiter.get_stats()
            >>> print(stats)
            {'tracked_ips': 10, 'tracked_keys': 5, ...}
        """
        return {
            'tracked_ips': len(self.ip_requests),
            'tracked_keys': len(self.api_key_requests),
            'ip_limit_per_minute': self.ip_limit,
            'api_key_limit_per_minute': self.api_key_limit,
            'window_size_seconds': self.window_size,
            'last_cleanup': self.last_cleanup
        }
