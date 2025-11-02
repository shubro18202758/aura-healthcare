# AURA Healthcare Platform 🏥

![AURA Healthcare](https://img.shields.io/badge/AURA-Healthcare-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-green?style=flat-square)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square)

**An Advanced AI-Powered Healthcare Platform with Medical Intelligence**

---

## 📋 Overview

AURA Healthcare is a comprehensive, production-ready telemedicine platform combining cutting-edge AI technologies for intelligent medical consultations, patient management, and healthcare analytics. The system integrates multiple AI providers, RAG for medical knowledge, real-time communication, and a sophisticated Model Context Protocol (MCP) for enhanced medical intelligence.

## ✨ Key Features

### 🤖 AI-Powered Medical Intelligence
- Multi-Provider AI Support (Google Gemini, OpenAI, Anthropic, Groq)
- RAG Engine with medical knowledge bases
- Real-time internet access to WHO, CDC, PubMed
- BioBERT-based semantic search

### 🧠 Model Context Protocol (MCP)
- Patient History Provider
- Service Classification
- Knowledge Base Integration  
- Medical Intelligence Context

### 💬 Real-Time Communication
- WebSocket-based live chat
- Text-to-Speech (pyttsx3, gTTS)
- Multi-language support (7+ languages)
- Session management with Redis

### 🏥 Clinical Features
- Electronic Health Records
- Appointment Scheduling
- Prescription Management
- Lab Reports & Vital Signs
- Patient Activity Tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Git

### Installation

1. **Clone Repository**
\\\ash
git clone https://github.com/shubro18202758/aura-healthcare.git
cd aura-healthcare
\\\

2. **Start Infrastructure**
\\\ash
docker-compose up -d
\\\

3. **Backend Setup**
\\\ash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
\\\

4. **Frontend Setup**
\\\ash
cd aura-ui
npm install
npm run dev
\\\

5. **Access Application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Demo Credentials
- **Doctor**: doctor@aura.health / doctor123
- **Patient**: patient@aura.health / patient123

## 🏗️ Architecture

\\\
┌──────────────┐      ┌──────────────┐      ┌───────────┐
│   Frontend   │◄────►│   Backend    │◄────►│  MongoDB  │
│  (React UI)  │      │  (FastAPI)   │      │           │
└──────────────┘      └──────────────┘      └───────────┘
        │                     │                     │
        │                     ▼                     ▼
        │             ┌──────────────┐      ┌───────────┐
        │             │  RAG Engine  │◄────►│  Qdrant   │
        │             │  (LangChain) │      │ (Vector)  │
        │             └──────────────┘      └───────────┘
        │                     │
        └────────────►┌──────────────┐      ┌───────────┐
                      │  WebSocket   │◄────►│   Redis   │
                      │    Server    │      │  (Cache)  │
                      └──────────────┘      └───────────┘
\\\

## 📚 Technology Stack

**Backend**: FastAPI, Python 3.12, MongoDB, Redis, Qdrant
**Frontend**: React 18, Vite, Axios
**AI/ML**: LangChain, BioBERT, TensorFlow, Sentence Transformers
**Infrastructure**: Docker, Nginx

## 📞 Support

**Author**: Sayandeep  
**GitHub**: [shubro18202758](https://github.com/shubro18202758)
**Email**: sayandeephaldar050405@gmail.com 

## 📝 License

MIT License - see LICENSE file for details.

---

**Made with ❤️ for better healthcare**
