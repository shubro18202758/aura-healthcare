"""
AURA Healthcare - Configuration Management
"""

from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file explicitly
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """Application Settings"""
    
    # Application Info
    APP_NAME: str = "AURA Healthcare"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGODB_URL: str = "mongodb://localhost:27017"  # Alias
    DATABASE_NAME: str = "aura_healthcare"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Vector Database
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "medical_knowledge"
    
    # AI Models
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-1.5-pro"
    GOOGLE_REPORTS_API_KEY: str = ""  # Separate API key for report analysis
    GOOGLE_REPORTS_MODEL: str = "gemini-2.5-flash"  # Model for report summaries
    DEFAULT_AI_PROVIDER: str = "openai"
    AI_MODEL: str = "gpt-4"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 1000
    EMBEDDING_MODEL: str = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract"
    LOCAL_MODEL_PATH: str = "./models/biomedical-llm"
    USE_LOCAL_MODEL: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    @field_validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["*"]  # Default to allow all if empty
            return [x.strip() for x in v.split(",")]
        return v
    
    # File Upload
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt", "png", "jpg", "jpeg"]
    
    # Medical NLP
    SPACY_MODEL: str = "en_core_web_sm"
    MEDICAL_ENTITIES: List[str] = ["DISEASE", "SYMPTOM", "MEDICATION", "TREATMENT", "ANATOMY"]
    SENTIMENT_THRESHOLD: float = 0.7
    
    # RAG Engine
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.75
    CONTEXT_WINDOW: int = 4096
    
    # Conversation
    MAX_CONVERSATION_HISTORY: int = 20
    CONVERSATION_TIMEOUT: int = 1800  # 30 minutes
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = [
        "en", "es", "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "or", "as"
    ]
    
    # Doctor Dashboard
    SPECIALTY_TEMPLATES: List[str] = [
        "cardiology", "neurology", "pediatrics", "orthopedics", "general"
    ]
    REPORT_FORMAT: str = "pdf"
    AUTO_GENERATE_SUMMARY: bool = True
    
    # Performance
    REDIS_CACHE_TTL: int = 3600
    ENABLE_RESPONSE_CACHE: bool = True
    MAX_CONCURRENT_CONVERSATIONS: int = 100
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 1000
    
    # Features
    ENABLE_VOICE: bool = True
    ENABLE_RAG: bool = False
    ENABLE_NLP: bool = True
    
    # Demo Mode
    DEMO_MODE: bool = True
    MOCK_AI_RESPONSES: bool = False
    POPULATE_SAMPLE_DATA: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get settings instance (for dependency injection)"""
    return settings

# Create necessary directories
def init_directories():
    """Initialize required directories"""
    directories = [
        settings.UPLOAD_DIR,
        "./data/medical_knowledge",
        "./data/vector_db",
        "./logs",
        "./models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Initialized directories")

init_directories()
