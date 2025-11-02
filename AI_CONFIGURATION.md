# 🤖 AI Configuration Guide for AURA Framework

## Overview
This guide explains how to integrate LLM API keys to enable cutting-edge generative AI features in the AURA Healthcare Framework.

## 🔑 When to Add API Keys

### Phase 1: After Basic Services Implementation
- **Timing**: After we implement the AI Service and RAG Engine
- **What gets enabled**: Basic AI-powered responses and medical knowledge retrieval

### Phase 2: Before Testing AI Features
- **Timing**: Before running AI-enhanced conversations and report generation
- **What gets enabled**: Full generative capabilities, advanced diagnostics, multilingual AI

---

## 🎯 Supported LLM Providers

### 1. **OpenAI (Recommended for Production)**
```env
# Add to .env file
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

**Features Enabled**:
- ✅ GPT-4 Turbo for medical consultations
- ✅ Advanced reasoning for diagnosis assistance
- ✅ High-quality embeddings for RAG
- ✅ Function calling for structured outputs
- ✅ JSON mode for report generation

**Cost**: ~$0.01-0.03 per request (GPT-4 Turbo)

### 2. **Anthropic Claude (Best for Medical Ethics)**
```env
# Add to .env file
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-opus-20240229
```

**Features Enabled**:
- ✅ Claude 3 Opus for ethical medical advice
- ✅ 200K context window for long conversations
- ✅ Superior reasoning for complex cases
- ✅ Built-in safety for healthcare domain

**Cost**: ~$0.015-0.075 per request (Claude 3 Opus)

### 3. **HuggingFace (Best for Privacy & Local Deployment)**
```env
# Add to .env file
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-70B-Instruct
```

**Features Enabled**:
- ✅ Open-source medical models
- ✅ Local deployment option
- ✅ HIPAA-compliant (data stays private)
- ✅ Free/low-cost inference

**Cost**: Free tier available, $0.0005-0.002 per request

### 4. **Azure OpenAI (Best for Enterprise)**
```env
# Add to .env file
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Features Enabled**:
- ✅ Enterprise-grade security
- ✅ HIPAA/GDPR compliance
- ✅ Private endpoints
- ✅ Advanced monitoring

### 5. **Google Gemini (Best for Multimodal)**
```env
# Add to .env file
GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_MODEL=gemini-1.5-pro
```

**Features Enabled**:
- ✅ Image analysis (X-rays, scans)
- ✅ Long context (1M tokens)
- ✅ Multimodal medical analysis
- ✅ Free tier available

---

## 📝 Step-by-Step Configuration

### Step 1: Choose Your LLM Provider(s)

**For Hackathon Demo** (Quick Start):
```bash
# Option A: OpenAI (easiest, most reliable)
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Option B: HuggingFace (free tier)
HUGGINGFACE_API_KEY=hf_your-key-here
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**For Production** (Best Quality):
```bash
# Primary: OpenAI for main features
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Fallback: Anthropic for complex cases
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# Embeddings: OpenAI for RAG
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

### Step 2: Update .env File

1. Open `.env` file in LOOP directory
2. Find the AI configuration section
3. Uncomment and add your API keys:

```bash
# ===================================
# AI & LLM Configuration
# ===================================

# OpenAI Configuration (Primary LLM)
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# Anthropic Configuration (Optional - Fallback)
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=2000

# HuggingFace Configuration (Optional - Local Models)
HUGGINGFACE_API_KEY=your-key-here
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-70B-Instruct

# AI Feature Flags
ENABLE_AI_RESPONSES=true
ENABLE_RAG=true
ENABLE_NLP=true
ENABLE_REPORT_GENERATION=true
```

### Step 3: Verify Configuration

After adding keys, restart the backend:

```powershell
cd c:\Users\sayan\Downloads\LOOP\backend
python -m app.main
```

Look for these success messages:
```
✅ OpenAI API configured
✅ RAG Engine initialized with vector store
✅ NLP Service loaded
✅ AI Service ready
```

---

## 🚀 AI Features Breakdown

### 1. **AI-Powered Chat Responses**
**Enabled by**: OpenAI/Anthropic/HuggingFace API key
```python
# What it does:
- Understands patient symptoms in natural language
- Asks relevant follow-up questions
- Provides empathetic, medically-informed responses
- Detects urgency and escalates to doctors
- Supports 15+ languages
```

### 2. **RAG (Retrieval-Augmented Generation)**
**Enabled by**: OpenAI Embeddings + Vector DB (Qdrant)
```python
# What it does:
- Retrieves relevant medical knowledge from database
- Grounds AI responses in factual medical literature
- Reduces hallucinations
- Provides source citations
- Updates knowledge without retraining
```

### 3. **Medical NLP & Entity Extraction**
**Enabled by**: HuggingFace Transformers (local) or OpenAI
```python
# What it does:
- Extracts symptoms, conditions, medications
- Medical Named Entity Recognition (NER)
- Sentiment analysis for mental health screening
- Intent classification
- Multi-language support
```

### 4. **Automated Report Generation**
**Enabled by**: OpenAI GPT-4 or Claude 3
```python
# What it does:
- Generates structured medical reports
- ICD-10 code suggestions
- Treatment plan recommendations
- Prescription formatting
- PDF export with medical formatting
```

### 5. **Doctor Assistance & Diagnostic Support**
**Enabled by**: OpenAI GPT-4 or Claude 3 Opus
```python
# What it does:
- Differential diagnosis suggestions
- Medical literature search
- Treatment protocol recommendations
- Drug interaction checking
- Clinical decision support
```

---

## 💰 Cost Estimation

### Hackathon Demo (1 day, 100 conversations)
- **OpenAI GPT-4 Turbo**: ~$5-10
- **HuggingFace**: Free (inference API)
- **Total**: $5-10

### Production (1000 patients/month)
- **AI Conversations**: ~$300-500/month
- **Report Generation**: ~$100-200/month
- **RAG Embeddings**: ~$50/month
- **Total**: ~$450-750/month

### Cost Optimization Tips
1. Use GPT-4 Turbo (cheaper than GPT-4)
2. Cache embeddings in Qdrant (reduce API calls)
3. Use GPT-3.5 for simple queries, GPT-4 for complex
4. Set up fallback to HuggingFace for non-critical features
5. Implement rate limiting

---

## 🔒 Security Best Practices

### 1. Never Commit API Keys
```bash
# Already in .gitignore
.env
.env.local
*.key
```

### 2. Use Environment Variables
```python
# ✅ Good
api_key = os.getenv("OPENAI_API_KEY")

# ❌ Bad
api_key = "sk-proj-xxxxx"  # Never hardcode!
```

### 3. Rotate Keys Regularly
- Rotate API keys every 90 days
- Use separate keys for dev/staging/prod
- Revoke compromised keys immediately

### 4. Monitor API Usage
```python
# Set up alerts for:
- Unusual API call volume
- High error rates
- Cost thresholds exceeded
```

---

## 🧪 Testing AI Features

### Test 1: Basic AI Response
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a headache and fever",
    "conversation_id": "test-123"
  }'
```

**Expected**: AI-generated response with follow-up questions

### Test 2: RAG Knowledge Retrieval
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the symptoms of diabetes?",
    "conversation_id": "test-123"
  }'
```

**Expected**: Response with medical knowledge + source citations

### Test 3: Report Generation
```bash
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-123",
    "doctor_id": "doc-123"
  }'
```

**Expected**: Structured medical report with diagnosis

---

## 📊 AI Performance Monitoring

### Key Metrics to Track
1. **Response Quality**
   - Medical accuracy rate
   - Patient satisfaction scores
   - Doctor override rate

2. **Performance**
   - Average response time (target: <2s)
   - API error rate (target: <1%)
   - Cache hit rate (target: >70%)

3. **Costs**
   - API cost per conversation
   - Token usage trends
   - Cost per patient

---

## 🎓 Next Steps

1. **Now**: Review this guide
2. **After Implementation**: I'll tell you "✅ Ready for API keys"
3. **You Provide**: Your LLM API key(s)
4. **We Test**: Verify AI features work
5. **Go Live**: Demo at hackathon!

---

## 📞 Getting API Keys

### OpenAI
1. Visit: https://platform.openai.com/api-keys
2. Sign up / Login
3. Create new secret key
4. Copy key (starts with `sk-proj-`)

### Anthropic
1. Visit: https://console.anthropic.com/
2. Sign up / Login
3. Settings → API Keys
4. Create key (starts with `sk-ant-`)

### HuggingFace
1. Visit: https://huggingface.co/settings/tokens
2. Sign up / Login
3. New token → Write access
4. Copy token (starts with `hf_`)

### Azure OpenAI
1. Azure Portal → Create OpenAI resource
2. Keys and Endpoint section
3. Copy key and endpoint

---

## ✅ Ready Checklist

Before adding API keys, ensure:
- [ ] All services implemented (AI, RAG, NLP)
- [ ] Backend server running
- [ ] MongoDB + Redis + Qdrant started
- [ ] .env file prepared
- [ ] Cost budget confirmed
- [ ] Security practices reviewed

**Current Status**: 🟡 Implementation in progress
**Next**: I'll implement all services, then notify you!

---

*Generated for AURA Healthcare Framework - Loop x IIT-B Hackathon 2025*
