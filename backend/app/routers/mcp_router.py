"""
MCP (Model Context Protocol) Router
Provides API endpoints for testing and monitoring MCP functionality
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from pydantic import BaseModel

from app.routers.auth import get_current_active_user
from app.models import User
from app.mcp.mcp_server import mcp_server, get_mcp_context

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class MCPContextRequest(BaseModel):
    """Request model for getting MCP context"""
    message: str
    conversation_id: Optional[str] = None
    context_types: Optional[List[str]] = None
    max_tokens: int = 2000


class ClassificationRequest(BaseModel):
    """Request model for service classification"""
    message: str
    conversation_id: Optional[str] = None


@router.post("/context")
async def get_context(
    request: MCPContextRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive MCP context for a message
    
    Returns context from all providers:
    - Patient History
    - Service Classification
    - Knowledge Base
    - Medical Intelligence
    """
    try:
        context = await get_mcp_context(
            user_id=current_user.user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            context_types=request.context_types
        )
        
        return {
            "success": True,
            "context": context
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP context error: {str(e)}"
        )


@router.post("/classify")
async def classify_interaction(
    request: ClassificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Classify interaction type using MCP
    
    Returns:
    - Service type (Health Query, Appointment, Insurance, etc.)
    - Confidence score
    - Sub-services
    - Alternative classifications
    """
    try:
        classification = await mcp_server.classify_interaction(
            user_id=current_user.user_id,
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        return {
            "success": True,
            "classification": classification
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification error: {str(e)}"
        )


@router.get("/insights")
async def get_patient_insights(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive patient insights
    
    Returns:
    - Conversation history summary
    - Symptom patterns
    - Medical intelligence insights
    """
    try:
        insights = await mcp_server.get_patient_insights(current_user.user_id)
        
        return {
            "success": True,
            "insights": insights
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insights error: {str(e)}"
        )


@router.get("/stats")
async def get_mcp_stats():
    """
    Get MCP system statistics
    
    Returns:
    - Provider status
    - Classification accuracy
    - Cache statistics
    """
    try:
        # Get classification stats
        if "service_classification" in mcp_server.providers:
            provider = mcp_server.providers["service_classification"]
            classification_stats = provider.get_classification_stats()
        else:
            classification_stats = {}
        
        # Get provider status
        provider_status = {
            name: "initialized" if provider else "unavailable"
            for name, provider in mcp_server.providers.items()
        }
        
        # Cache stats
        cache_stats = {
            "total_cached_contexts": len(mcp_server.cache),
            "cache_ttl_seconds": mcp_server.cache_ttl
        }
        
        return {
            "success": True,
            "mcp_initialized": mcp_server.initialized,
            "providers": provider_status,
            "classification_stats": classification_stats,
            "cache_stats": cache_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats error: {str(e)}"
        )


@router.get("/health")
async def mcp_health_check():
    """
    Check MCP system health
    """
    try:
        providers_ok = all(
            provider is not None 
            for provider in mcp_server.providers.values()
        )
        
        return {
            "success": True,
            "status": "healthy" if mcp_server.initialized and providers_ok else "degraded",
            "initialized": mcp_server.initialized,
            "providers_count": len(mcp_server.providers),
            "providers_status": {
                name: "ok" if provider else "unavailable"
                for name, provider in mcp_server.providers.items()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
