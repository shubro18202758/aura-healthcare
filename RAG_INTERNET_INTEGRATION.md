# 🌐 RAG Knowledge Base - Internet Integration

## Overview
The AURA Healthcare system now automatically fetches medical knowledge from trusted internet sources to populate the RAG (Retrieval-Augmented Generation) knowledge base. This ensures that AI responses are grounded in real, up-to-date medical information.

## 📚 Data Sources

### 1. **PubMed (Research Articles)**
- **Source**: NCBI E-utilities API
- **Coverage**: 80+ research articles across 8 medical topics
- **Topics**:
  - Diabetes treatment guidelines
  - Hypertension management
  - Cardiovascular disease prevention
  - Cancer screening recommendations
  - Mental health disorders treatment
  - Infectious disease prevention
  - Nutrition and diet recommendations
  - Vaccine safety and efficacy
- **API**: Free, no API key required
- **URL**: https://eutils.ncbi.nlm.nih.gov

### 2. **WHO (World Health Organization)**
- **Source**: WHO website scraping
- **Coverage**: 3 guideline pages
- **Topics**:
  - COVID-19 technical guidance
  - Diabetes health topics
  - Hypertension fact sheets
- **Access**: Public web scraping
- **URL**: https://www.who.int

### 3. **CDC (Centers for Disease Control)**
- **Source**: CDC website scraping
- **Coverage**: 4 guideline pages
- **Topics**:
  - Diabetes basics
  - Blood pressure management
  - Heart disease prevention
  - Cancer prevention strategies
- **Access**: Public web scraping
- **URL**: https://www.cdc.gov

### 4. **RxNorm (Drug Information)**
- **Source**: RxNorm/DailyMed API (NLM)
- **Coverage**: 10 common medications
- **Drugs**:
  - Metformin, Lisinopril, Amlodipine
  - Atorvastatin, Omeprazole, Levothyroxine
  - Metoprolol, Albuterol, Ibuprofen, Acetaminophen
- **API**: Free, no API key required
- **URL**: https://rxnav.nlm.nih.gov

### 5. **MedlinePlus (Medical Conditions)**
- **Source**: MedlinePlus Connect API (NLM)
- **Coverage**: 8 common medical conditions
- **Conditions**:
  - Diabetes, Hypertension, Asthma, Depression
  - Arthritis, Heart Disease, Obesity, Anxiety
- **API**: Free, no API key required
- **URL**: https://connect.medlineplus.gov

## 🔧 Technical Implementation

### Architecture
```
Medical Knowledge Fetcher Service
├── PubMed Fetcher (NCBI E-utilities)
│   ├── esearch - Search for article IDs
│   ├── esummary - Get article metadata
│   └── efetch - Retrieve full abstracts (XML)
├── WHO Guideline Scraper
├── CDC Guideline Scraper
├── RxNorm Drug Info Fetcher
└── MedlinePlus Condition Info Fetcher
```

### Key Components

#### 1. **MedicalKnowledgeFetcher Service**
Location: `backend/app/services/medical_knowledge_fetcher.py`

Main class that coordinates fetching from all sources:
```python
class MedicalKnowledgeFetcher:
    async def fetch_comprehensive_knowledge() -> List[Dict]:
        # Fetches 100+ documents from all sources concurrently
        pass
```

#### 2. **RAG Knowledge Management API**
Location: `backend/app/routers/rag_knowledge.py`

Admin-only endpoints for managing the knowledge base:
- `POST /api/admin/rag/populate/comprehensive` - Fetch all knowledge
- `POST /api/admin/rag/populate/custom` - Fetch specific knowledge
- `GET /api/admin/rag/populate/status` - Check fetch status
- `POST /api/admin/rag/documents/add` - Manually add documents
- `GET /api/admin/rag/documents/count` - Get document count
- `POST /api/admin/rag/documents/search` - Search knowledge base
- `DELETE /api/admin/rag/documents/clear` - Clear all documents

#### 3. **Enhanced RAG Engine**
Location: `backend/app/core/rag_engine.py`

New methods added:
```python
async def add_documents(documents: List[Dict])
async def search(query: str, limit: int = 10)
async def get_collection_info()
async def clear_collection()
```

## 🚀 Usage Guide

### Prerequisites
1. Backend server running (`http://localhost:8000`)
2. Qdrant vector database running (Docker container on port 6333)
3. Admin access token

### Quick Start

#### Option 1: Using the Test Script
```bash
python populate_rag.py
```
Follow the prompts to:
1. Enter your admin token
2. Trigger comprehensive knowledge fetch
3. Monitor progress
4. Verify with test search

#### Option 2: Using cURL

1. **Get Admin Token**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

2. **Trigger Comprehensive Fetch**:
```bash
curl -X POST http://localhost:8000/api/admin/rag/populate/comprehensive \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

3. **Check Status**:
```bash
curl http://localhost:8000/api/admin/rag/populate/status \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

4. **Get Document Count**:
```bash
curl http://localhost:8000/api/admin/rag/documents/count \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

5. **Test Search**:
```bash
curl -X POST "http://localhost:8000/api/admin/rag/documents/search?query=diabetes&limit=5" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Custom Knowledge Fetch

Fetch specific content:
```bash
curl -X POST http://localhost:8000/api/admin/rag/populate/custom \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["who", "cdc"],
    "pubmed_queries": ["diabetes management", "hypertension treatment"],
    "drug_names": ["metformin", "lisinopril"],
    "conditions": ["diabetes", "hypertension"],
    "max_results_per_query": 10
  }'
```

## 📊 Expected Results

After running comprehensive fetch:
- **Total Documents**: 100+
- **PubMed Articles**: 80
- **WHO Guidelines**: 3
- **CDC Guidelines**: 4
- **Drug Information**: 10
- **Medical Conditions**: 8

### Document Structure
```json
{
  "content": "Medical text content (abstract/guideline/drug info)...",
  "metadata": {
    "source": "PubMed|WHO|CDC|RxNorm|MedlinePlus",
    "category": "research|guidelines|drug_information|medical_condition",
    "url": "Source URL",
    "fetched_at": "ISO 8601 timestamp",
    "title": "Document title",
    "pmid": "PubMed ID (for PubMed articles)",
    "rxcui": "RxNorm concept ID (for drugs)",
    "drug_name": "Drug name (for drugs)",
    "condition": "Condition name (for conditions)",
    "topic": "Topic (for WHO/CDC guidelines)"
  }
}
```

## 🔐 Security & Privacy

### API Access
- All APIs use free, public data (no API keys required)
- WHO/CDC scraping uses public web pages
- User-Agent: "AURA Healthcare System/1.0 (Medical Education)"

### Authorization
- Knowledge management endpoints require **ADMIN role**
- Only administrators can populate/modify the knowledge base
- Regular users can only query through the chat interface

### Rate Limiting
- Respects API rate limits
- Uses async/concurrent fetching for efficiency
- Implements error handling and retries

## 🔄 Update Strategy

### Initial Population
Run once during setup:
```bash
python populate_rag.py
```

### Periodic Updates
Recommended frequency: **Weekly or Monthly**

Options:
1. **Manual**: Run the populate script periodically
2. **Scheduled Task**: Use APScheduler in backend
3. **Cron Job**: Schedule script execution

### Incremental Updates
```bash
# Add specific medical topics
curl -X POST http://localhost:8000/api/admin/rag/populate/custom \
  -H "Authorization: Bearer TOKEN" \
  -d '{"pubmed_queries": ["new medical topic"]}'
```

## 📈 Performance Metrics

### Fetch Times
- **PubMed**: ~2-3 seconds per query (80 articles total)
- **WHO/CDC**: ~1-2 seconds per page (7 pages total)
- **RxNorm**: ~1 second per drug (10 drugs total)
- **MedlinePlus**: ~1 second per condition (8 conditions total)
- **Total Estimated Time**: 5-10 minutes (concurrent execution)

### Storage
- **Vector Embeddings**: ~768 dimensions per document
- **Qdrant Collection**: medical_knowledge
- **Embedding Model**: BiomedNLP-BiomedBERT-base-uncased-abstract
- **Expected Size**: ~100MB for 100+ documents

## 🐛 Troubleshooting

### Issue: "RAG dependencies missing"
**Solution**: Install dependencies
```bash
pip install langchain-community qdrant-client sentence-transformers
```

### Issue: "Qdrant connection failed"
**Solution**: Start Qdrant Docker container
```bash
docker-compose up -d qdrant
```

### Issue: "Knowledge fetch failed"
**Causes**:
1. Network connectivity issues
2. API rate limits exceeded
3. Website structure changed (scraping)

**Solution**: Check logs, retry after delay

### Issue: "No results from search"
**Causes**:
1. Knowledge base empty (not populated)
2. Query doesn't match any documents

**Solution**: Run populate script, try different queries

## 📝 Example Queries

After populating the knowledge base, try these queries:

1. **Diabetes**: "What are the symptoms of diabetes?"
2. **Hypertension**: "How to manage high blood pressure?"
3. **Heart Disease**: "What are cardiovascular disease risk factors?"
4. **Medications**: "What are the side effects of metformin?"
5. **Mental Health**: "How to treat depression?"
6. **Vaccines**: "Are COVID-19 vaccines safe?"
7. **Nutrition**: "What is a healthy diet for diabetes?"
8. **Cancer**: "What are cancer screening guidelines?"

## 🎯 Future Enhancements

### Planned Features
1. **More Sources**: 
   - UpToDate medical database
   - Mayo Clinic information
   - NIH clinical trials data
   - FDA drug approvals

2. **Smart Updates**:
   - Automatic change detection
   - Incremental updates only
   - Version tracking

3. **Quality Metrics**:
   - Source reliability scoring
   - Citation tracking
   - Freshness indicators

4. **Advanced Search**:
   - Multi-modal search (text + images)
   - Clinical decision support
   - Drug interaction checking

## 📞 Support

For issues or questions:
1. Check the backend logs: `backend/logs/`
2. Verify Qdrant status: `http://localhost:6333/dashboard`
3. Test RAG endpoint: `/api/admin/rag/documents/count`
4. Review API documentation: `http://localhost:8000/docs`

---

**Built with ❤️ for AURA Healthcare**  
*Empowering medical AI with real, trusted knowledge*
