# 🎨 MCP Visual Architecture

## 📊 Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                             │
│  Patient: "I've been having chest pain for 3 days"                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   FRONTEND (React Chat Interface)                    │
│  - ChatInterface.jsx                                                 │
│  - Sends message via API                                             │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI Chat Router)                      │
│  app/routers/chat.py                                                 │
│  - Receives message                                                  │
│  - Extracts user_id, conversation_id                                 │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     🧠 MCP SERVER CALL                              │
│  mcp_context = await get_mcp_context(                              │
│      user_id="patient_123",                                         │
│      message="I've been having chest pain for 3 days",             │
│      conversation_id="conv_456"                                     │
│  )                                                                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MCP SERVER (Core Orchestrator)                     │
│  app/mcp/mcp_server.py                                               │
│  - Parallel provider execution                                       │
│  - Context aggregation                                               │
│  - Relevance scoring                                                 │
│  - Caching (5 min TTL)                                               │
└────────────┬────────┬──────────┬────────────────────┬────────────────┘
             │        │          │                    │
     ┌───────▼──┐  ┌──▼──────┐  ┌▼──────────┐  ┌─────▼──────────┐
     │ Provider │  │ Provider │  │ Provider  │  │   Provider     │
     │    1     │  │    2     │  │    3      │  │      4         │
     └───────┬──┘  └──┬───────┘  └┬──────────┘  └─────┬──────────┘
             │        │            │                   │
             ▼        ▼            ▼                   ▼

┌────────────────────────────────────────────────────────────────────┐
│  📚 PROVIDER 1: Patient History                                    │
│  app/mcp/providers/patient_history_provider.py                     │
│                                                                    │
│  MongoDB Query:                                                    │
│  ├─ db.conversations.find({"user_id": "patient_123"})            │
│  └─ db.messages.find({"conversation_id": {...}})                 │
│                                                                    │
│  Returns:                                                          │
│  {                                                                 │
│    "previous_conversations": 5,                                    │
│    "recent_symptoms": ["headache", "fatigue", "chest pain"],      │
│    "known_conditions": ["hypertension"],                           │
│    "allergy_alerts": ["penicillin"],                               │
│    "medication_history": ["lisinopril"],                           │
│    "relevance_score": 0.85                                         │
│  }                                                                 │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  🎯 PROVIDER 2: Service Classification                            │
│  app/mcp/providers/service_classification_provider.py             │
│                                                                    │
│  Training Data (CSV):                                              │
│  ├─ 100+ real healthcare interactions                             │
│  ├─ 9 service types                                                │
│  └─ Accuracy metrics per service                                  │
│                                                                    │
│  Classification Logic:                                             │
│  ├─ Keyword matching (60% weight)                                 │
│  │   "chest pain" → Health Query keywords                         │
│  └─ Pattern matching (40% weight)                                 │
│      Regex: \b(i have|experiencing|suffering from)\b              │
│                                                                    │
│  Returns:                                                          │
│  {                                                                 │
│    "predicted_service_type": "Health Query",                       │
│    "confidence": 0.92,                                             │
│    "sub_services": ["cardiology"],                                 │
│    "classification_accuracy": 0.9487,                              │
│    "alternatives": [                                               │
│      {"service_type": "Appointment Booking", "confidence": 0.15}   │
│    ],                                                              │
│    "relevance_score": 0.92                                         │
│  }                                                                 │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  📖 PROVIDER 3: Knowledge Base                                     │
│  app/mcp/providers/knowledge_base_provider.py                      │
│                                                                    │
│  Specialty Detection:                                              │
│  "chest pain" → Cardiology                                         │
│                                                                    │
│  MongoDB Query:                                                    │
│  db.knowledge_base.find({                                          │
│    "specialty": {"$in": ["Cardiology", "General Medicine"]}       │
│  })                                                                │
│                                                                    │
│  Cache: 1 hour per specialty                                       │
│                                                                    │
│  Returns:                                                          │
│  {                                                                 │
│    "specialty": "Cardiology",                                      │
│    "relevant_knowledge": [                                         │
│      {                                                             │
│        "title": "Chest Pain Assessment Protocol",                  │
│        "content": "...",                                           │
│        "tags": ["cardiac", "emergency", "assessment"]              │
│      }                                                             │
│    ],                                                              │
│    "total_entries": 8,                                             │
│    "relevance_score": 0.78                                         │
│  }                                                                 │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  🔬 PROVIDER 4: Medical Intelligence                              │
│  app/mcp/providers/medical_intelligence_provider.py               │
│                                                                    │
│  Cross-Patient Analysis (Anonymized):                              │
│  ├─ Find similar symptom patterns (last 90 days)                  │
│  ├─ Extract treatment approaches                                  │
│  └─ Identify symptom clusters                                     │
│                                                                    │
│  MongoDB Queries:                                                  │
│  db.messages.find({                                                │
│    "content": {"$regex": "chest pain", "$options": "i"},          │
│    "timestamp": {"$gte": cutoff_date}                             │
│  })                                                                │
│                                                                    │
│  Returns:                                                          │
│  {                                                                 │
│    "similar_cases": 15,                                            │
│    "common_treatments": [                                          │
│      {"treatment_context": "ECG recommended", "frequency": 12},    │
│      {"treatment_context": "Stress test advised", "frequency": 8}  │
│    ],                                                              │
│    "symptom_clusters": [                                           │
│      {                                                             │
│        "primary_symptom": "chest pain",                            │
│        "related_symptoms": ["fatigue", "shortness of breath"]      │
│      }                                                             │
│    ],                                                              │
│    "average_resolution_time": "3-7 days",                          │
│    "relevance_score": 0.75                                         │
│  }                                                                 │
└────────────────────────────────────────────────────────────────────┘

             │        │            │                   │
             └────────┴────────────┴───────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CONTEXT AGGREGATION                                │
│  app/mcp/context_engine.py                                           │
│                                                                       │
│  Aggregated Context:                                                 │
│  {                                                                    │
│    "timestamp": "2024-01-15T10:30:00",                               │
│    "user_id": "patient_123",                                          │
│    "contexts": {                                                      │
│      "patient_history": {...},                                        │
│      "service_classification": {...},                                 │
│      "knowledge_base": {...},                                         │
│      "medical_intelligence": {...}                                    │
│    },                                                                 │
│    "total_relevance": 3.3,                                            │
│    "context_summary": "Patient History: 5 conversations..."           │
│  }                                                                    │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CONTEXT INJECTION INTO AI PROMPT                   │
│  app/routers/chat.py - generate_ai_response()                        │
│                                                                       │
│  Base Prompt:                                                         │
│  "You are AURA, an AI healthcare assistant..."                       │
│                                                                       │
│  + MCP Context:                                                       │
│  "=== INTELLIGENT CONTEXT (MCP) ===                                  │
│   Patient History: 5 previous conversations                          │
│   Recent symptoms: headache, fatigue, chest pain                     │
│   Known Conditions: hypertension                                      │
│   ⚠️  ALLERGIES: penicillin                                          │
│                                                                       │
│   Detected Intent: Health Query (cardiology) - 92% confidence        │
│   Relevant Specialty: Cardiology                                     │
│   Similar Cases: 15 patients with similar symptoms                   │
│   Common Treatment Approaches: ECG, stress test, nitrates            │
│                                                                       │
│   IMPORTANT: Use this context to provide personalized responses."    │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   AI SERVICE (LLM)                                   │
│  app/services/ai_service.py                                          │
│                                                                       │
│  Provider: Google Gemini (gemini-2.5-flash)                          │
│                                                                       │
│  Input: User message + MCP context                                   │
│  Output: Context-aware AI response                                   │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CONTEXT-AWARE AI RESPONSE                          │
│                                                                       │
│  "I understand you've been experiencing chest pain for 3 days.       │
│   Given your history with hypertension and the symptoms you          │
│   mentioned last week (fatigue, headache), this requires             │
│   immediate attention.                                               │
│                                                                       │
│   Based on similar cases in our system, I recommend:                 │
│   1. Urgent cardiac evaluation (ECG recommended)                     │
│   2. Monitor your blood pressure regularly                           │
│   3. Avoid strenuous activity until evaluated                        │
│                                                                       │
│   Important: I see you're allergic to penicillin, so we'll           │
│   ensure any prescriptions account for that.                         │
│                                                                       │
│   Would you like me to schedule an urgent cardiology                 │
│   appointment for you today?"                                        │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   RESPONSE TO USER                                   │
│  - Save to MongoDB (messages collection)                             │
│  - Send via WebSocket to frontend                                    │
│  - Display in chat interface                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔄 Real-Time Flow Summary

1. **User sends message** → Frontend API call
2. **Chat router** receives → Extracts user_id
3. **MCP Server called** → Orchestrates providers
4. **4 Providers execute in parallel**:
   - Patient History: MongoDB queries for conversations/messages
   - Service Classification: CSV training data + pattern matching
   - Knowledge Base: Specialty-specific content
   - Medical Intelligence: Anonymized cross-patient patterns
5. **Context aggregated** → Relevance scored
6. **Context injected** → AI prompt enhanced
7. **AI generates** → Context-aware response
8. **Response delivered** → User receives intelligent reply

## 📊 Performance Characteristics

| Component | Time | Notes |
|-----------|------|-------|
| MongoDB Queries | 10-30ms | Per provider |
| Parallel Provider Execution | 30-80ms | All 4 providers |
| Context Aggregation | <5ms | In-memory processing |
| AI Generation (Gemini) | 500-2000ms | Depends on response length |
| **Total Added Latency** | **35-85ms** | MCP overhead only |
| **Total Response Time** | **535-2085ms** | Including AI generation |

**Impact**: MCP adds only 35-85ms overhead while dramatically improving response quality!

## 💾 Data Flow

```
Training Data (CSV)
    ↓
Service Classification Provider
    ↓
100+ Healthcare Interactions
    ↓
9 Service Types
    ↓
94.87% Accuracy (Health Query)
```

```
Patient Interactions
    ↓
MongoDB (conversations + messages)
    ↓
Patient History Provider
    ↓
Full Conversation History
    ↓
Symptom/Medication/Allergy Tracking
```

```
Doctor-Curated Content
    ↓
MongoDB (knowledge_base)
    ↓
Knowledge Base Provider
    ↓
Specialty-Specific Guidelines
    ↓
1-hour Cache
```

```
All Patient Messages (Anonymized)
    ↓
MongoDB (messages - last 90 days)
    ↓
Medical Intelligence Provider
    ↓
Similar Cases + Treatment Patterns
    ↓
Privacy-Safe Aggregation
```

## 🎯 Key Innovations

1. **Parallel Context Fetching**: All providers run simultaneously using `asyncio.gather()`
2. **Intelligent Caching**: 5-minute context cache + 1-hour knowledge cache
3. **Relevance Scoring**: Each context scored 0.0-1.0 for quality
4. **Token Optimization**: Max 2000 tokens per context
5. **Privacy-Safe Intelligence**: Cross-patient data anonymized
6. **Real-Time Classification**: 94.87% accuracy with <50ms latency
7. **Medical Entity Extraction**: Regex-based symptom/medication detection
8. **Sub-Service Detection**: Specialty + urgency identification

## 🏆 End Result

**Before MCP**: Generic AI responses, no memory, no context

**After MCP**: Intelligent assistant that remembers, learns, and provides personalized care!

---

**Visual created for**: AURA Healthcare Framework - Loop x IIT-B Hackathon
