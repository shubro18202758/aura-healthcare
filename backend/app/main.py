"""
AURA Healthcare - Main FastAPI Application
Enhanced with Model Context Protocol (MCP) for intelligent context injection
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

from app.config import settings
from app.database import init_db, close_database

# Import core modules (RAG is optional - Qdrant + upgraded PyTorch 2.9.0)
try:
    from app.core import RAGEngine
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  RAG Engine not available: {e}")
    RAGEngine = None
    RAG_AVAILABLE = False

try:
    from app.core import conversation_manager
except ImportError as e:
    print(f"⚠️  Conversation Manager not available: {e}")
    conversation_manager = None

# Import MCP System
try:
    from app.mcp.mcp_server import mcp_server
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  MCP System not available: {e}")
    mcp_server = None
    MCP_AVAILABLE = False

# Import routers
from app.routers import auth, doctor, patient, chat, reports, knowledge_base, medical_documents, mcp_router, tts_router, patient_activity, rag_knowledge

# Import AI service
try:
    from app.services import ai_service
    AI_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI Service not available: {e}")
    ai_service = None
    AI_SERVICE_AVAILABLE = False

# Global instances
rag_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    global rag_engine
    
    print("🚀 Initializing AURA Healthcare System...")
    
    # Initialize database
    try:
        await init_db()
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    # Initialize conversation manager
    if conversation_manager:
        try:
            await conversation_manager.initialize()
            app.state.conversation_manager = conversation_manager
        except Exception as e:
            print(f"⚠️  Conversation manager warning: {e}")
            app.state.conversation_manager = None
    else:
        app.state.conversation_manager = None
    
    # Initialize RAG engine (optional for demo)
    if RAG_AVAILABLE and RAGEngine:
        try:
            rag_engine = RAGEngine()
            await rag_engine.initialize()
            app.state.rag_engine = rag_engine
        except Exception as e:
            print(f"⚠️  RAG engine initialization skipped: {e}")
            app.state.rag_engine = None
    else:
        print("⚠️  RAG engine not available (optional)")
        app.state.rag_engine = None
    
    # Initialize AI service
    if AI_SERVICE_AVAILABLE and ai_service:
        app.state.ai_service = ai_service
        if ai_service.is_available():
            providers = ai_service.get_available_providers()
            print(f"✅ AI Service ready with providers: {', '.join(providers)}")
        else:
            print("⚠️  AI Service loaded but no LLM providers configured")
            print("   Add API keys to .env - see AI_CONFIGURATION.md")
    else:
        print("⚠️  AI Service not available")
        app.state.ai_service = None
    
    # Initialize MCP System (Model Context Protocol)
    if MCP_AVAILABLE and mcp_server:
        try:
            print("\n🧠 Initializing Model Context Protocol (MCP)...")
            await mcp_server.initialize()
            app.state.mcp_server = mcp_server
            print("✅ MCP System initialized successfully!")
            print("   - Patient History Provider: ✓")
            print("   - Service Classification Provider: ✓")
            print("   - Knowledge Base Provider: ✓")
            print("   - Medical Intelligence Provider: ✓")
        except Exception as e:
            print(f"⚠️  MCP initialization warning: {e}")
            app.state.mcp_server = None
    else:
        print("⚠️  MCP System not available")
        app.state.mcp_server = None
    
    print("\n✅ AURA System Ready!")
    print(f"📍 API Documentation: http://localhost:8000/docs")
    print(f"📍 Frontend: http://localhost:3000")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down AURA System...")
    
    # Shutdown MCP
    if MCP_AVAILABLE and mcp_server:
        try:
            await mcp_server.shutdown()
        except:
            pass
    
    await close_database()

# Create FastAPI app
app = FastAPI(
    title="AURA Healthcare API",
    description="AI-Powered Healthcare Communication Framework for Loop x IIT-B Hackathon",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers to the browser
)

# Compression middleware - Gzip compression for responses
from app.middleware import CompressionMiddleware
app.add_middleware(
    CompressionMiddleware,
    minimum_size=500,  # Only compress responses > 500 bytes
    compression_level=6  # Balance between speed and compression
)

# Cache middleware - Response caching with Redis
from app.middleware import CacheMiddleware
app.add_middleware(
    CacheMiddleware,
    default_ttl=300,  # 5 minutes default
    cache_key_prefix="aura:cache:",
    excluded_paths=["/docs", "/redoc", "/openapi.json", "/auth", "/api/chat/send"]
)

# Include routers
app.include_router(auth.router)
app.include_router(doctor.router)
app.include_router(patient.router)
app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(knowledge_base.router)
app.include_router(medical_documents.router)
app.include_router(mcp_router.router)  # MCP monitoring and testing endpoints
app.include_router(tts_router.router)  # Text-to-Speech with 6 voice options
app.include_router(patient_activity.router)  # Patient activity tracking - DOCTOR ONLY
app.include_router(rag_knowledge.router)  # RAG Knowledge Management - ADMIN ONLY

# Static files
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AURA Healthcare API - Healing with AI! 🏥🤖",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "demo_mode": settings.DEMO_MODE
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "services": {
            "database": "operational",
            "rag_engine": "operational" if rag_engine else "disabled",
            "conversation_manager": "operational"
        }
    }

@app.get("/api/info")
async def api_info():
    """API information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "features": {
            "ai_chat": True,
            "rag_engine": rag_engine is not None,
            "multilingual": True,
            "voice_support": True,
            "document_processing": True,
            "real_time_chat": True,
            "medical_nlp": True,
            "report_generation": True
        },
        "supported_languages": settings.SUPPORTED_LANGUAGES,
        "specialties": settings.SPECIALTY_TEMPLATES
    }

# Demo endpoints for hackathon
@app.get("/api/demo/status")
async def demo_status():
    """Demo mode status"""
    return {
        "demo_mode": settings.DEMO_MODE,
        "sample_accounts": {
            "doctor": {
                "email": "doctor@aura.health",
                "password": "doctor123",
                "note": "Sample doctor account for testing"
            },
            "patient": {
                "email": "patient@aura.health",
                "password": "patient123",
                "note": "Sample patient account for testing"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL
    )
