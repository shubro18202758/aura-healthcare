"""
Response caching middleware for FastAPI using Redis
"""
import hashlib
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.database import get_redis


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache GET request responses in Redis
    """
    
    def __init__(
        self,
        app: ASGIApp,
        default_ttl: int = 300,  # 5 minutes default
        cache_key_prefix: str = "aura:cache:",
        excluded_paths: list = None
    ):
        super().__init__(app)
        self.default_ttl = default_ttl
        self.cache_key_prefix = cache_key_prefix
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth",  # Don't cache authentication
            "/api/chat/send",  # Don't cache chat messages
        ]
    
    def _should_cache(self, request: Request) -> bool:
        """Check if the request should be cached"""
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        # Skip excluded paths
        for path in self.excluded_paths:
            if request.url.path.startswith(path):
                return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request"""
        # Include method, path, and query params in cache key
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Add user info if authenticated
        if hasattr(request.state, "user"):
            key_parts.append(str(request.state.user.get("id", "")))
        
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{self.cache_key_prefix}{key_hash}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and cache the response if applicable"""
        
        # Check if we should cache this request
        if not self._should_cache(request):
            return await call_next(request)
        
        # Try to get cached response
        cache_key = self._generate_cache_key(request)
        redis = await get_redis()
        
        try:
            cached_data = await redis.get(cache_key)
            
            if cached_data:
                # Return cached response
                data = json.loads(cached_data)
                return JSONResponse(
                    content=data.get("content"),
                    status_code=data.get("status_code", 200),
                    headers={**data.get("headers", {}), "X-Cache": "HIT"}
                )
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
        
        # Get fresh response
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Parse JSON content
                content = json.loads(body.decode())
                
                # Prepare cache data
                cache_data = {
                    "content": content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
                
                # Determine TTL based on endpoint
                ttl = self.default_ttl
                if "/dashboard" in request.url.path:
                    ttl = 120  # 2 minutes for dashboard stats
                elif "/reports" in request.url.path:
                    ttl = 600  # 10 minutes for reports list
                elif "/knowledge" in request.url.path:
                    ttl = 1800  # 30 minutes for knowledge base
                
                # Store in cache
                await redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(cache_data)
                )
                
                # Return response with cache miss header
                return JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers={**dict(response.headers), "X-Cache": "MISS"}
                )
            except Exception as e:
                print(f"⚠️ Cache write error: {e}")
                # Return original response if caching fails
                return response
        
        return response


async def invalidate_cache_pattern(pattern: str = "*"):
    """
    Utility function to invalidate cached responses by pattern
    
    Usage:
        await invalidate_cache_pattern("aura:cache:*/dashboard*")
    """
    redis = await get_redis()
    try:
        keys = await redis.keys(f"aura:cache:{pattern}")
        if keys:
            await redis.delete(*keys)
            print(f"🧹 Invalidated {len(keys)} cache entries")
    except Exception as e:
        print(f"⚠️ Cache invalidation error: {e}")
