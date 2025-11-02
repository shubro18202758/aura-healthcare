# 🧠 Enable RAG (Retrieval-Augmented Generation) in AURA

## ✅ Current Status
- ✅ Python packages installed: `langchain-community`, `qdrant-client`
- ❌ Qdrant vector database not running

## 🔍 What is RAG?
RAG allows the AI to:
- Search through medical knowledge bases
- Retrieve relevant medical documents
- Provide more accurate, context-aware responses
- Access clinical guidelines and research papers

## 🚀 How to Enable RAG

### Option 1: Docker (Recommended - Easiest)

1. **Install Docker Desktop** (if not installed):
   - Download: https://www.docker.com/products/docker-desktop/

2. **Run Qdrant in Docker**:
   ```powershell
   docker run -d -p 6333:6333 -p 6334:6334 `
     -v ${PWD}/qdrant_storage:/qdrant/storage:z `
     qdrant/qdrant
   ```

3. **Restart backend** - RAG will initialize automatically!
   ```powershell
   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Option 2: Docker Compose (Best for Production)

1. **Update docker-compose.yml** - Add Qdrant service:
   ```yaml
   services:
     # ... existing services ...
     
     qdrant:
       image: qdrant/qdrant:latest
       container_name: aura_qdrant
       ports:
         - "6333:6333"  # REST API
         - "6334:6334"  # gRPC API
       volumes:
         - ./qdrant_storage:/qdrant/storage
       restart: unless-stopped
   ```

2. **Start all services**:
   ```powershell
   docker-compose up -d
   ```

### Option 3: Standalone Installation (Windows)

1. **Download Qdrant**:
   - Visit: https://github.com/qdrant/qdrant/releases
   - Download the Windows executable

2. **Run Qdrant**:
   ```powershell
   # Extract and run
   .\qdrant.exe
   ```

3. **Qdrant will start on**: http://localhost:6333

## 🔧 Configuration

RAG settings are in `backend/app/config.py`:

```python
# Qdrant Vector Database
QDRANT_URL: str = "http://localhost:6333"
QDRANT_API_KEY: str = ""  # Optional for local setup
QDRANT_COLLECTION: str = "medical_knowledge"
```

## 📊 Verify RAG is Running

1. **Check Qdrant is accessible**:
   ```powershell
   curl http://localhost:6333/collections
   ```

2. **Restart backend** and look for:
   ```
   ✅ RAG Engine initialized successfully
   ```
   Instead of:
   ```
   ⚠️  RAG engine initialization skipped: RAG dependencies missing
   ```

## 📚 Populate Medical Knowledge

Once RAG is running, you can add medical documents:

```python
# Example: Add medical documents to RAG
POST /api/admin/rag/documents
{
  "documents": [
    {
      "content": "Medical guideline or research paper text...",
      "metadata": {
        "source": "WHO Guidelines",
        "category": "treatment",
        "date": "2024-01-01"
      }
    }
  ]
}
```

## 🎯 What RAG Enables

Once enabled, your AI will:
- ✅ Search through medical knowledge bases
- ✅ Retrieve relevant clinical guidelines
- ✅ Provide evidence-based responses
- ✅ Cite sources for medical information
- ✅ Handle complex medical queries better

## 🔗 Useful Links

- **Qdrant Docs**: https://qdrant.tech/documentation/
- **Qdrant Docker**: https://hub.docker.com/r/qdrant/qdrant
- **LangChain Docs**: https://python.langchain.com/docs/

## 🐛 Troubleshooting

### "Connection refused to localhost:6333"
- Qdrant is not running
- Start Qdrant with Docker or standalone

### "RAG engine initialization skipped"
- Check if Qdrant is accessible: `curl http://localhost:6333`
- Verify QDRANT_URL in config.py

### "No collections found"
- This is normal on first run
- Collections are created when you add documents

## 📝 Quick Start Commands

```powershell
# 1. Start Qdrant (Docker)
docker run -d -p 6333:6333 qdrant/qdrant

# 2. Verify Qdrant is running
curl http://localhost:6333/collections

# 3. Restart backend
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 4. Check logs for "✅ RAG Engine initialized"
```

---

**Note**: RAG is optional. Your app works perfectly without it, but RAG makes the AI smarter by giving it access to a medical knowledge base!
