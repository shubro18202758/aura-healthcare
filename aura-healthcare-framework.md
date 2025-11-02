# AURA Healthcare Framework - Hackathon Ready Implementation

## Project Structure

```
aura-healthcare/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── doctor.py
│   │   │   ├── patient.py
│   │   │   ├── conversation.py
│   │   │   └── report.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── doctor.py
│   │   │   ├── patient.py
│   │   │   ├── chat.py
│   │   │   └── reports.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py
│   │   │   ├── nlp_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── document_processor.py
│   │   │   └── report_generator.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── helpers.py
│   │   │   └── constants.py
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── rag_engine.py
│   │       ├── conversation_manager.py
│   │       └── medical_nlp.py
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── doctor/
│   │   │   ├── patient/
│   │   │   └── chat/
│   │   ├── pages/
│   │   │   ├── DoctorDashboard.jsx
│   │   │   ├── PatientInterface.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   └── ReportsView.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── websocket.js
│   │   ├── utils/
│   │   │   ├── constants.js
│   │   │   └── helpers.js
│   │   ├── App.jsx
│   │   ├── index.js
│   │   └── package.json
├── data/
│   ├── medical_knowledge/
│   │   ├── medical_pdfs/
│   │   └── processed_docs/
│   ├── uploads/
│   └── vector_db/
└── scripts/
    ├── setup.py
    ├── populate_knowledge_base.py
    └── run_dev.sh
```

## Quick Setup Guide

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- 8GB+ RAM (for local LLM)

### Installation Commands

```bash
# Clone repository
git clone <your-repo-url>
cd aura-healthcare

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment setup
cp .env.example .env
# Edit .env with your configurations

# Start services
docker-compose up -d  # Vector DB & MongoDB
python scripts/setup.py  # Initialize databases
```

## Core Components Implementation

### 1. Backend Configuration Files

#### requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
sqlalchemy==2.0.23
pymongo==4.6.0
pydantic==2.5.0
langchain==0.0.350
langchain-community==0.0.10
sentence-transformers==2.2.2
qdrant-client==1.6.9
transformers==4.35.2
torch==2.1.1
openai==1.3.7
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.25.2
websockets==12.0
aiofiles==23.2.1
python-dotenv==1.0.0
pandas==2.1.4
numpy==1.25.2
scikit-learn==1.3.2
spacy==3.7.2
pypdf2==3.0.1
python-docx==1.1.0
```

#### .env.example
```env
# Database
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=aura_healthcare

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key

# AI Models
OPENAI_API_KEY=your_openai_key
HUGGINGFACE_API_KEY=your_hf_key
LOCAL_MODEL_PATH=./models/biomedical-llm

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Settings
DEBUG=True
CORS_ORIGINS=["http://localhost:3000"]
```

### 2. Core Backend Files

#### backend/app/main.py
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os

from app.routers import auth, doctor, patient, chat, reports
from app.core.rag_engine import RAGEngine
from app.services.ai_service import AIService
from app.database import init_db

# Global instances
rag_engine = None
ai_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global rag_engine, ai_service
    
    print("🚀 Initializing AURA Healthcare System...")
    
    # Initialize database
    await init_db()
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    await rag_engine.initialize()
    
    # Initialize AI service
    ai_service = AIService()
    await ai_service.initialize()
    
    app.state.rag_engine = rag_engine
    app.state.ai_service = ai_service
    
    print("✅ AURA System Ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down AURA System...")

app = FastAPI(
    title="AURA Healthcare API",
    description="AI-Powered Healthcare Communication Framework",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", ["http://localhost:3000"]).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(doctor.router, prefix="/api/doctor", tags=["doctor"])
app.include_router(patient.router, prefix="/api/patient", tags=["patient"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

# Static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {"message": "AURA Healthcare API - Ready to heal with AI! 🏥🤖"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

#### backend/app/core/rag_engine.py
```python
import os
from typing import List, Dict, Any, Optional
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Qdrant
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from qdrant_client import QdrantClient
import asyncio

class RAGEngine:
    """Retrieval-Augmented Generation Engine for Medical Knowledge"""
    
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.llm = None
        self.qa_chain = None
        self.qdrant_client = None
        
    async def initialize(self):
        """Initialize RAG components"""
        try:
            # Initialize embeddings (medical domain optimized)
            self.embeddings = HuggingFaceEmbeddings(
                model_name="microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # Initialize Qdrant client
            self.qdrant_client = QdrantClient(
                url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                api_key=os.getenv("QDRANT_API_KEY")
            )
            
            # Initialize vector store
            self.vector_store = Qdrant(
                client=self.qdrant_client,
                collection_name="medical_knowledge",
                embeddings=self.embeddings,
            )
            
            # Initialize LLM (using local biomedical model)
            model_path = os.getenv("LOCAL_MODEL_PATH", "./models/biomedical-llm")
            if os.path.exists(model_path):
                self.llm = LlamaCpp(
                    model_path=model_path,
                    temperature=0.1,
                    max_tokens=2000,
                    top_p=0.95,
                    verbose=False,
                    n_ctx=4096,
                )
            else:
                # Fallback to OpenAI
                from langchain.llms import OpenAI
                self.llm = OpenAI(
                    temperature=0.1,
                    max_tokens=2000,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
            
            # Create QA chain
            self._setup_qa_chain()
            
            print("✅ RAG Engine initialized successfully")
            
        except Exception as e:
            print(f"❌ RAG Engine initialization failed: {e}")
            raise
    
    def _setup_qa_chain(self):
        """Setup the Question-Answering chain"""
        medical_prompt = PromptTemplate(
            template="""You are AURA, an AI medical assistant. Use the following medical knowledge to provide accurate, helpful responses.

Context: {context}