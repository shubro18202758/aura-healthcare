# 🚀 AURA Healthcare - Quick Start Guide

## ⚡ 5-Minute Setup for Hackathon Demo

### Step 1: Verify Prerequisites

Open PowerShell and check:

```powershell
python --version  # Should be 3.9+
node --version    # Should be 16+
docker --version  # Optional but recommended
```

### Step 2: Setup Environment

```powershell
# Navigate to project directory
cd LOOP

# Run the automated setup script
.\start.ps1
```

This script will:
- ✅ Check Python installation
- ✅ Create `.env` file from template
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Start the backend server

### Step 3: Access the Application

Once started, you can access:

- **API Server**: <http://localhost:8000>
- **API Documentation**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/health>

### Step 4: Test the System

#### Using API Documentation (Swagger UI)

1. Open <http://localhost:8000/docs> in your browser
2. Try the `/health` endpoint
3. Check `/api/info` for system features
4. View demo accounts at `/api/demo/status`

#### Using cURL

```powershell
# Health check
curl http://localhost:8000/health

# API information
curl http://localhost:8000/api/info

# Demo status
curl http://localhost:8000/api/demo/status
```

## 🗄️ Optional: Start Databases

For full functionality with MongoDB and Qdrant:

```powershell
# Start all services (MongoDB, Redis, Qdrant)
docker-compose up -d

# View running services
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 👥 Demo Accounts

### Doctor Account
- **Email**: `doctor@aura.health`
- **Password**: `doctor123`
- **Role**: Doctor (Cardiologist)

### Patient Account
- **Email**: `patient@aura.health`
- **Password**: `patient123`
- **Role**: Patient

## 🎯 Key Features to Demo

### 1. AI-Powered Conversations
- Multilingual support (15+ languages)
- Medical entity extraction
- Sentiment analysis
- Urgency detection

### 2. Doctor Dashboard
- Specialty-specific question templates
- Real-time patient conversations
- AI-generated medical reports
- Natural language queries

### 3. RAG Engine
- Medical knowledge retrieval
- Context-aware responses
- Biomedical BERT embeddings
- Vector similarity search

### 4. Real-Time Communication
- WebSocket-based chat
- Live typing indicators
- Message history
- File uploads

## 📁 Project Structure Overview

```
LOOP/
├── backend/
│   ├── app/
│   │   ├── main.py           ← Entry point
│   │   ├── config.py         ← Configuration
│   │   ├── database.py       ← DB connections
│   │   ├── models/           ← Data models
│   │   ├── routers/          ← API endpoints
│   │   ├── services/         ← Business logic
│   │   └── core/             ← Core modules
│   │       ├── rag_engine.py
│   │       ├── conversation_manager.py
│   │       └── medical_nlp.py
├── frontend/                  ← React app (coming soon)
├── data/                      ← Uploads and knowledge base
├── requirements.txt           ← Python dependencies
├── docker-compose.yml         ← Services configuration
├── start.ps1                  ← Quick start script
└── README.md                  ← Documentation
```

## 🐛 Troubleshooting

### Port Already in Use

```powershell
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Dependencies Installation Fails

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install dependencies one by one
pip install fastapi uvicorn motor pymongo redis
```

### Docker Issues

```powershell
# Restart Docker Desktop
# Then try again:
docker-compose down
docker-compose up -d
```

### Import Errors

Make sure you're running from the correct directory:

```powershell
# Backend should be run from project root
cd c:\Users\sayan\Downloads\LOOP
python backend/app/main.py

# Or from backend directory
cd backend
python -m app.main
```

## 🎓 Next Steps

### For Development

1. **Review API Docs**: <http://localhost:8000/docs>
2. **Check Models**: `backend/app/models/*.py`
3. **Explore Routers**: `backend/app/routers/*.py`
4. **Test Services**: `backend/app/services/*.py`

### For Customization

1. **Edit Configuration**: `.env` file
2. **Add Medical Knowledge**: `data/medical_knowledge/`
3. **Customize Templates**: `backend/app/models/doctor.py` (SPECIALTY_QUESTIONS)
4. **Modify Prompts**: `backend/app/core/rag_engine.py`

### For Deployment

1. **Docker Build**: `docker-compose build`
2. **Production Config**: Update `.env` with production settings
3. **Scale Services**: Modify `docker-compose.yml`
4. **Add Monitoring**: Integrate Sentry, Prometheus, etc.

## 📊 System Architecture

```
┌─────────────┐
│   Patient   │
└──────┬──────┘
       │
       ↓
┌─────────────────┐
│  Chat Interface │
└────────┬────────┘
         │
         ↓
┌───────────────────────────┐
│   FastAPI Backend         │
│  ┌──────────────────────┐ │
│  │ Conversation Manager │ │
│  └───────┬──────────────┘ │
│          │                 │
│  ┌───────┼────────┐        │
│  ↓       ↓        ↓        │
│ RAG   NLP     Database    │
└───────────────────────────┘
         │
         ↓
┌─────────────────┐
│ Doctor Dashboard│
└─────────────────┘
```

## 🎯 Hackathon Tips

1. **Demo First**: Start with `/docs` endpoint to show API
2. **Show AI**: Demonstrate conversation flow
3. **Highlight Innovation**: RAG engine, NLP, multilingual support
4. **Explain Impact**: Healthcare accessibility, language barriers
5. **Discuss Scalability**: Microservices, Docker, cloud-ready

## 📞 Support

- **Documentation**: <http://localhost:8000/docs>
- **Issues**: Create GitHub issue
- **Questions**: Check README.md

## ✅ Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created
- [ ] Backend server starts without errors
- [ ] Can access <http://localhost:8000>
- [ ] Can access <http://localhost:8000/docs>
- [ ] Health check returns "healthy"
- [ ] Docker services running (optional)

---

**Good luck with your hackathon! 🚀**

**AURA Healthcare - Healing with AI! 🏥🤖**
