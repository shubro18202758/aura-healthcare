"""
Compression middleware for FastAPI to reduce response size
"""
import gzip
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to compress responses using gzip
    """
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 500,  # Minimum response size to compress (bytes)
        compression_level: int = 6  # Compression level 1-9 (higher = more compression, slower)
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
    
    def should_compress(self, request: Request, response: Response) -> bool:
        """Check if the response should be compressed"""
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return False
        
        # Check content type - only compress text-based content
        content_type = response.headers.get("content-type", "")
        compressible_types = [
            "text/",
            "application/json",
            "application/javascript",
            "application/xml",
        ]
        
        if not any(ct in content_type for ct in compressible_types):
            return False
        
        # Check if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and compress the response if applicable"""
        response = await call_next(request)
        
        if not self.should_compress(request, response):
            return response
        
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Only compress if body is large enough
        if len(body) < self.minimum_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # Compress the response
        compressed_body = gzip.compress(body, compresslevel=self.compression_level)
        
        # Calculate compression ratio
        original_size = len(body)
        compressed_size = len(compressed_body)
        ratio = (1 - compressed_size / original_size) * 100
        
        # Update headers
        headers = dict(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(compressed_size)
        headers["x-compression-ratio"] = f"{ratio:.1f}%"
        
        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )
