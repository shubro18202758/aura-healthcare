"""
AURA Healthcare - RAG Knowledge Management API
Endpoints for fetching and managing medical knowledge in RAG
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models import Role
from app.routers.auth import require_role
from app.services.medical_knowledge_fetcher import get_medical_fetcher
from app.core import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/rag",
    tags=["RAG Knowledge Management"],
    dependencies=[Depends(require_role(Role.ADMIN))]  # Only admins can manage knowledge base
)


class DocumentInput(BaseModel):
    content: str
    metadata: Dict[str, Any]


class FetchRequest(BaseModel):
    sources: Optional[List[str]] = None  # ["pubmed", "who", "cdc", "drugs", "conditions"]
    pubmed_queries: Optional[List[str]] = None
    drug_names: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    max_results_per_query: int = 10


class FetchStatus(BaseModel):
    status: str
    message: str
    documents_fetched: int
    documents_added: int
    started_at: str
    completed_at: Optional[str] = None


# Global status tracking
fetch_status = {
    "is_fetching": False,
    "last_fetch": None
}


@router.post("/populate/comprehensive")
async def populate_comprehensive_knowledge(
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Fetch comprehensive medical knowledge from all sources and populate RAG
    This runs in the background and can take several minutes
    """
    if fetch_status["is_fetching"]:
        raise HTTPException(
            status_code=409,
            detail="Knowledge fetch is already in progress"
        )
    
    # Start background task
    background_tasks.add_task(fetch_and_populate_comprehensive)
    
    return {
        "status": "started",
        "message": "Comprehensive knowledge fetch started in background",
        "estimated_time": "5-10 minutes",
        "sources": ["PubMed", "WHO", "CDC", "RxNorm", "MedlinePlus"]
    }


@router.post("/populate/custom")
async def populate_custom_knowledge(
    request: FetchRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Fetch specific medical knowledge based on custom parameters
    """
    if fetch_status["is_fetching"]:
        raise HTTPException(
            status_code=409,
            detail="Knowledge fetch is already in progress"
        )
    
    background_tasks.add_task(fetch_and_populate_custom, request)
    
    return {
        "status": "started",
        "message": "Custom knowledge fetch started in background",
        "parameters": request.dict()
    }


@router.get("/populate/status")
async def get_fetch_status() -> Dict[str, Any]:
    """
    Get the current status of knowledge fetching
    """
    return {
        "is_fetching": fetch_status["is_fetching"],
        "last_fetch": fetch_status["last_fetch"]
    }


@router.post("/documents/add")
async def add_documents_to_rag(documents: List[DocumentInput]) -> Dict[str, Any]:
    """
    Manually add documents to RAG knowledge base
    """
    try:
        from app.main import app
        rag_engine: RAGEngine = app.state.rag_engine
        
        if not rag_engine:
            raise HTTPException(
                status_code=503,
                detail="RAG engine not available"
            )
        
        # Convert to format expected by RAG engine
        formatted_docs = [
            {
                "content": doc.content,
                "metadata": doc.metadata
            }
            for doc in documents
        ]
        
        # Add to RAG
        await rag_engine.add_documents(formatted_docs)
        
        return {
            "status": "success",
            "message": f"Added {len(documents)} documents to RAG knowledge base",
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error adding documents to RAG: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add documents: {str(e)}"
        )


@router.get("/documents/count")
async def get_document_count() -> Dict[str, Any]:
    """
    Get the count of documents in RAG knowledge base
    """
    try:
        from app.main import app
        rag_engine: RAGEngine = app.state.rag_engine
        
        if not rag_engine:
            raise HTTPException(
                status_code=503,
                detail="RAG engine not available"
            )
        
        # Get count from Qdrant
        collection_info = await rag_engine.get_collection_info()
        
        return {
            "status": "success",
            "total_documents": collection_info.get("vectors_count", 0),
            "collection": "medical_knowledge"
        }
        
    except Exception as e:
        logger.error(f"Error getting document count: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document count: {str(e)}"
        )


@router.post("/documents/search")
async def search_knowledge_base(
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search the RAG knowledge base
    """
    try:
        from app.main import app
        rag_engine: RAGEngine = app.state.rag_engine
        
        if not rag_engine:
            raise HTTPException(
                status_code=503,
                detail="RAG engine not available"
            )
        
        # Search RAG
        results = await rag_engine.search(query, limit=limit)
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.delete("/documents/clear")
async def clear_knowledge_base() -> Dict[str, Any]:
    """
    Clear all documents from RAG knowledge base
    WARNING: This action cannot be undone!
    """
    try:
        from app.main import app
        rag_engine: RAGEngine = app.state.rag_engine
        
        if not rag_engine:
            raise HTTPException(
                status_code=503,
                detail="RAG engine not available"
            )
        
        # Clear collection
        await rag_engine.clear_collection()
        
        return {
            "status": "success",
            "message": "Knowledge base cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing knowledge base: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear knowledge base: {str(e)}"
        )


# ==================== Background Tasks ====================

async def fetch_and_populate_comprehensive():
    """Background task to fetch comprehensive knowledge"""
    global fetch_status
    
    fetch_status["is_fetching"] = True
    started_at = datetime.utcnow()
    documents_fetched = 0
    documents_added = 0
    
    try:
        logger.info("Starting comprehensive knowledge fetch...")
        
        # Get fetcher
        fetcher = await get_medical_fetcher()
        
        # Fetch all documents
        documents = await fetcher.fetch_comprehensive_knowledge()
        documents_fetched = len(documents)
        
        logger.info(f"Fetched {documents_fetched} documents from online sources")
        
        # Add to RAG in batches
        from app.main import app
        rag_engine: RAGEngine = app.state.rag_engine
        
        if rag_engine and documents:
            batch_size = 50
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                await rag_engine.add_documents(batch)
                documents_added += len(batch)
                logger.info(f"Added batch {i//batch_size + 1}, total documents: {documents_added}")
        
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        fetch_status["last_fetch"] = {
            "status": "completed",
            "documents_fetched": documents_fetched,
            "documents_added": documents_added,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": duration
        }
        
        logger.info(f"Comprehensive knowledge fetch completed in {duration:.2f}s")
        logger.info(f"Documents fetched: {documents_fetched}, added to RAG: {documents_added}")
        
    except Exception as e:
        logger.error(f"Error in comprehensive knowledge fetch: {e}")
        fetch_status["last_fetch"] = {
            "status": "failed",
            "error": str(e),
            "documents_fetched": documents_fetched,
            "documents_added": documents_added,
            "started_at": started_at.isoformat()
        }
    
    finally:
        fetch_status["is_fetching"] = False


async def fetch_and_populate_custom(request: FetchRequest):
    """Background task to fetch custom knowledge"""
    global fetch_status
    
    fetch_status["is_fetching"] = True
    started_at = datetime.utcnow()
    documents_fetched = 0
    documents_added = 0
    
    try:
        logger.info(f"Starting custom knowledge fetch: {request.dict()}")
        
        fetcher = await get_medical_fetcher()
        all_documents = []
        
        # Fetch based on request parameters
        if request.pubmed_queries:
            for query in request.pubmed_queries:
                docs = await fetcher.fetch_pubmed_articles(query, request.max_results_per_query)
                all_documents.extend(docs)
        
        if request.sources:
            if "who" in request.sources:
                docs = await fetcher.fetch_who_guidelines()
                all_documents.extend(docs)
            
            if "cdc" in request.sources:
                docs = await fetcher.fetch_cdc_guidelines()
                all_documents.extend(docs)
        
        if request.drug_names:
            for drug in request.drug_names:
                docs = await fetcher.fetch_drug_information(drug)
                all_documents.extend(docs)
        
        if request.conditions:
            for condition in request.conditions:
                docs = await fetcher.fetch_medlineplus_info(condition)
                all_documents.extend(docs)
        
        documents_fetched = len(all_documents)
        logger.info(f"Fetched {documents_fetched} documents")
        
        # Add to RAG
        from app.main import app
        rag_engine: RAGEngine = app.state.rag_engine
        
        if rag_engine and all_documents:
            await rag_engine.add_documents(all_documents)
            documents_added = len(all_documents)
        
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        fetch_status["last_fetch"] = {
            "status": "completed",
            "documents_fetched": documents_fetched,
            "documents_added": documents_added,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": duration
        }
        
        logger.info(f"Custom knowledge fetch completed in {duration:.2f}s")
        
    except Exception as e:
        logger.error(f"Error in custom knowledge fetch: {e}")
        fetch_status["last_fetch"] = {
            "status": "failed",
            "error": str(e),
            "documents_fetched": documents_fetched,
            "documents_added": documents_added,
            "started_at": started_at.isoformat()
        }
    
    finally:
        fetch_status["is_fetching"] = False
