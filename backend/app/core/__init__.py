"""
AURA Healthcare Core - Module exports
Optional imports for demo mode
"""

# Only import what's available - RAG engine needs heavy dependencies
try:
    from app.core.conversation_manager import ConversationManager, conversation_manager
    HAS_CONVERSATION_MANAGER = True
except ImportError:
    ConversationManager = None
    conversation_manager = None
    HAS_CONVERSATION_MANAGER = False

try:
    from app.core.rag_engine import RAGEngine
    HAS_RAG_ENGINE = True
except ImportError:
    RAGEngine = None
    HAS_RAG_ENGINE = False

# RAG Engine and Medical NLP are optional (require langchain, torch, etc.)
__all__ = []

if HAS_CONVERSATION_MANAGER:
    __all__.extend(["ConversationManager", "conversation_manager"])

if HAS_RAG_ENGINE:
    __all__.append("RAGEngine")
