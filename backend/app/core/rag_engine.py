"""
AURA Healthcare - Core RAG Engine Implementation
"""

import os
import asyncio
from typing import List, Dict, Any, Optional

# Heavy RAG dependencies (langchain, qdrant, etc.) are imported lazily inside methods

class RAGEngine:
    """Retrieval-Augmented Generation Engine for Medical Knowledge"""
    
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.llm = None
        self.qdrant_client = None
        self.prompt_template = None
        self.llm_mode = None
        
    async def initialize(self):
        """Initialize RAG components"""
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import Qdrant
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError(
                "RAG dependencies missing. Install langchain-community and qdrant-client to enable the RAG engine."
            ) from exc

        try:
            from langchain_community.llms import LlamaCpp  # Optional dependency
            llama_available = True
        except ImportError:
            llama_available = False

        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_model_name = os.getenv("GOOGLE_MODEL", "gemini-pro")

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
            if llama_available and os.path.exists(model_path):
                self.llm = LlamaCpp(
                    model_path=model_path,
                    temperature=0.1,
                    max_tokens=2000,
                    top_p=0.95,
                    verbose=False,
                    n_ctx=4096,
                )
                self.llm_mode = "llama"
            elif google_api_key:
                try:
                    import google.generativeai as genai
                except ImportError as exc:
                    raise RuntimeError(
                        "google-generativeai package missing. Install google-generativeai or provide another supported LLM."
                    ) from exc
                genai.configure(api_key=google_api_key)
                self.llm = genai.GenerativeModel(model_name=google_model_name)
                self.llm_mode = "gemini"
            else:
                # Fallback to OpenAI
                try:
                    from langchain_openai import OpenAI
                except ImportError as exc:
                    raise RuntimeError(
                        "LangChain OpenAI client missing. Install langchain-openai or provide a local model."
                    ) from exc
                openai_key = os.getenv("OPENAI_API_KEY")
                if not openai_key:
                    raise RuntimeError(
                        "OPENAI_API_KEY not set. Provide a local model path, configure Gemini, or supply an OpenAI key for RAG to run."
                    )
                self.llm = OpenAI(
                    temperature=0.1,
                    max_tokens=2000,
                    api_key=openai_key,
                )
                self.llm_mode = "openai"
            
            # Cache prompt template for manual QA flow
            self.prompt_template = (
                "You are AURA, an AI medical assistant. Use the following medical knowledge to provide accurate, helpful responses.\n\n"
                "Context: {context}\n\n"
                "Question: {question}\n\n"
                "Please provide a comprehensive, medically accurate response. If you're not certain about medical information, clearly state so and recommend consulting a healthcare professional.\n\n"
                "Response:"
            )
            
            print("✅ RAG Engine initialized successfully")
            
        except Exception as e:
            print(f"❌ RAG Engine initialization failed: {e}")
            raise
    
    async def query(self, question: str, context: str = "") -> Dict[str, Any]:
        """Query the RAG system"""
        try:
            # Enhance question with context if provided
            enhanced_question = f"{context} {question}" if context else question
            
            docs = await asyncio.to_thread(
                self.vector_store.similarity_search,
                enhanced_question,
                k=5
            )

            context_block = "\n\n".join(doc.page_content for doc in docs)
            prompt = self.prompt_template.format(
                context=context_block or "No additional context found.",
                question=question
            )

            answer_text = await asyncio.to_thread(self._invoke_llm, prompt)

            return {
                "answer": answer_text.strip(),
                "sources": [doc.metadata for doc in docs],
                "confidence": self._calculate_confidence(len(docs))
            }
        except Exception as e:
            print(f"❌ RAG query failed: {e}")
            return {
                "answer": "I apologize, but I encountered an error processing your question. Please try again or consult a healthcare professional.",
                "sources": [],
                "confidence": 0.0
            }
    
    def _invoke_llm(self, prompt: str) -> str:
        """Invoke the configured LLM and normalize the response to a string"""
        if self.llm is None:
            raise RuntimeError("LLM is not initialized")
        if self.llm_mode == "gemini":
            response = self.llm.generate_content(prompt)
            if hasattr(response, "text") and response.text:
                return response.text
            if getattr(response, "candidates", None):
                parts = []
                for candidate in response.candidates:
                    content = getattr(candidate, "content", None)
                    if content and hasattr(content, "parts"):
                        for part in content.parts:
                            text = getattr(part, "text", None)
                            if text:
                                parts.append(text)
                if parts:
                    return "\n".join(parts)
            return str(response)

        response = None
        if hasattr(self.llm, "invoke"):
            response = self.llm.invoke(prompt)
        elif callable(self.llm):
            response = self.llm(prompt)
        else:
            raise RuntimeError("Configured LLM does not support invocation")

        if isinstance(response, str):
            return response

        # Handle LangChain message or dict outputs
        if hasattr(response, "content") and isinstance(response.content, str):
            return response.content
        if hasattr(response, "text") and isinstance(response.text, str):
            return response.text
        if isinstance(response, dict):
            for key in ("text", "content", "message"):
                if isinstance(response.get(key), str):
                    return response[key]

        return str(response)

    def _calculate_confidence(self, num_sources: int) -> float:
        """Calculate a lightweight confidence score based on retrieved context"""
        if not num_sources:
            return 0.3
        return min(0.9, 0.4 + (num_sources * 0.1))
    
    async def add_documents(self, documents: List[str] | List[Dict], metadata: List[Dict] = None):
        """Add new documents to the knowledge base
        
        Args:
            documents: List of strings or List of dicts with 'content' and 'metadata' keys
            metadata: Optional list of metadata dicts (used if documents are strings)
        """
        try:
            from langchain.schema import Document
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # Handle both formats: List[str] or List[Dict]
            if documents and isinstance(documents[0], dict):
                # Documents are dicts with 'content' and 'metadata'
                texts = [doc['content'] for doc in documents]
                metadatas = [doc.get('metadata', {}) for doc in documents]
            else:
                # Documents are strings
                texts = documents
                metadatas = metadata or [{}] * len(documents)
            
            # Create LangChain documents and split
            splits = text_splitter.create_documents(texts, metadatas=metadatas)
            
            await asyncio.to_thread(
                self.vector_store.add_documents, splits
            )
            
            print(f"✅ Added {len(splits)} document chunks to knowledge base")
            return len(splits)
            
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
            raise
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base and return documents"""
        try:
            docs = await asyncio.to_thread(
                self.vector_store.similarity_search,
                query,
                k=limit
            )
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, 'score', None)
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection"""
        try:
            if not self.qdrant_client:
                raise RuntimeError("Qdrant client not initialized")
            
            collection_info = await asyncio.to_thread(
                self.qdrant_client.get_collection,
                collection_name="medical_knowledge"
            )
            
            return {
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status.name if hasattr(collection_info, 'status') else "unknown",
                "config": {
                    "vector_size": collection_info.config.params.vectors.size if hasattr(collection_info.config, 'params') else None
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get collection info: {e}")
            return {
                "vectors_count": 0,
                "error": str(e)
            }
    
    async def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            if not self.qdrant_client:
                raise RuntimeError("Qdrant client not initialized")
            
            # Delete and recreate collection
            await asyncio.to_thread(
                self.qdrant_client.delete_collection,
                collection_name="medical_knowledge"
            )
            
            # Recreate collection with same config
            from qdrant_client.models import Distance, VectorParams
            
            await asyncio.to_thread(
                self.qdrant_client.create_collection,
                collection_name="medical_knowledge",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            
            # Reinitialize vector store
            from langchain_community.vectorstores import Qdrant
            self.vector_store = Qdrant(
                client=self.qdrant_client,
                collection_name="medical_knowledge",
                embeddings=self.embeddings,
            )
            
            print("✅ Collection cleared successfully")
            
        except Exception as e:
            print(f"❌ Failed to clear collection: {e}")
            raise

# Conversation Manager
class ConversationManager:
    """Manages patient-AI conversations with context awareness"""
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
        self.conversations = {}
        self.medical_entities = {}
    
    async def start_conversation(self, patient_id: str, specialty: str, initial_questions: List[str]) -> str:
        """Start a new conversation session"""
        conversation_id = f"{patient_id}_{specialty}_{len(self.conversations)}"
        
        self.conversations[conversation_id] = {
            "patient_id": patient_id,
            "specialty": specialty,
            "questions": initial_questions,
            "current_question": 0,
            "responses": [],
            "context": {},
            "medical_history": [],
            "extracted_entities": {}
        }
        
        return conversation_id
    
    async def get_next_question(self, conversation_id: str) -> Dict[str, Any]:
        """Get the next question for the patient"""
        if conversation_id not in self.conversations:
            raise ValueError("Conversation not found")
        
        conv = self.conversations[conversation_id]
        
        if conv["current_question"] >= len(conv["questions"]):
            # Generate follow-up questions based on context
            return await self._generate_followup_question(conversation_id)
        
        question = conv["questions"][conv["current_question"]]
        
        # Optimize question for empathy and clarity
        optimized_question = await self._optimize_question(question, conv["specialty"])
        
        return {
            "question": optimized_question,
            "question_id": conv["current_question"],
            "is_followup": False,
            "progress": (conv["current_question"] + 1) / len(conv["questions"])
        }
    
    async def process_response(self, conversation_id: str, response: str) -> Dict[str, Any]:
        """Process patient response and extract medical entities"""
        if conversation_id not in self.conversations:
            raise ValueError("Conversation not found")
        
        conv = self.conversations[conversation_id]
        
        # Extract medical entities from response
        entities = await self._extract_medical_entities(response)
        
        # Store response and entities
        conv["responses"].append({
            "question_id": conv["current_question"],
            "response": response,
            "entities": entities,
            "timestamp": "now"  # Use proper timestamp
        })
        
        # Update extracted entities
        conv["extracted_entities"].update(entities)
        
        # Move to next question
        conv["current_question"] += 1
        
        # Assess if follow-up needed
        needs_followup = await self._assess_followup_need(response, entities)
        
        return {
            "processed": True,
            "entities_extracted": len(entities),
            "needs_followup": needs_followup,
            "next_available": conv["current_question"] < len(conv["questions"])
        }
    
    async def _optimize_question(self, question: str, specialty: str) -> str:
        """Optimize doctor's question for empathy and clarity"""
        optimization_prompt = f"""
        As an empathetic AI healthcare assistant specializing in {specialty}, 
        please rephrase this medical question to be more patient-friendly, 
        empathetic, and clear while maintaining medical accuracy:

        Original question: {question}

        Make it conversational, warm, and easy to understand for patients.
        """
        
        try:
            result = await self.rag_engine.query(optimization_prompt)
            return result["answer"].strip()
        except:
            return question  # Fallback to original
    
    async def _extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from patient response"""
        # Placeholder for medical NLP entity extraction
        # In real implementation, use spaCy medical models or specialized NER
        entities = {
            "symptoms": [],
            "medications": [],
            "conditions": [],
            "body_parts": [],
            "severity": [],
            "duration": []
        }
        
        # Simple keyword-based extraction for demo
        symptom_keywords = ["pain", "ache", "hurt", "fever", "nausea", "dizzy", "tired"]
        for keyword in symptom_keywords:
            if keyword in text.lower():
                entities["symptoms"].append(keyword)
        
        return entities
    
    async def _generate_followup_question(self, conversation_id: str) -> Dict[str, Any]:
        """Generate contextual follow-up questions"""
        conv = self.conversations[conversation_id]
        context = " ".join([r["response"] for r in conv["responses"][-3:]])  # Last 3 responses
        
        followup_prompt = f"""
        Based on this patient conversation context in {conv["specialty"]}:
        {context}

        Generate one relevant follow-up question to gather more specific 
        information for diagnosis. Make it empathetic and clear.
        """
        
        try:
            result = await self.rag_engine.query(followup_prompt)
            return {
                "question": result["answer"].strip(),
                "question_id": len(conv["questions"]) + len([r for r in conv["responses"] if r.get("is_followup")]),
                "is_followup": True,
                "progress": 1.0
            }
        except:
            return {
                "question": "Is there anything else you'd like to share about your symptoms?",
                "question_id": -1,
                "is_followup": True,
                "progress": 1.0
            }
    
    async def _assess_followup_need(self, response: str, entities: Dict) -> bool:
        """Assess if follow-up questions are needed"""
        # Simple heuristic: if response is very short or lacks specific entities
        if len(response.split()) < 5:
            return True
        
        if not any(entities.values()):
            return True
        
        return False
    
    async def generate_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Generate conversation summary for doctor"""
        if conversation_id not in self.conversations:
            raise ValueError("Conversation not found")
        
        conv = self.conversations[conversation_id]
        
        # Compile all responses
        full_conversation = ""
        for resp in conv["responses"]:
            q_id = resp["question_id"]
            if q_id < len(conv["questions"]):
                question = conv["questions"][q_id]
            else:
                question = "Follow-up question"
            
            full_conversation += f"Q: {question}\nA: {resp['response']}\n\n"
        
        # Generate comprehensive summary
        summary_prompt = f"""
        Create a comprehensive medical summary for a {conv["specialty"]} specialist 
        based on this patient conversation:

        {full_conversation}

        Please provide:
        1. Chief complaints and symptoms
        2. Medical history mentioned
        3. Current medications/treatments
        4. Severity and duration of symptoms
        5. Red flags or urgent concerns
        6. Recommended follow-up actions

        Format as a professional medical summary.
        """
        
        try:
            result = await self.rag_engine.query(summary_prompt)
            
            return {
                "conversation_id": conversation_id,
                "patient_id": conv["patient_id"],
                "specialty": conv["specialty"],
                "summary": result["answer"],
                "total_responses": len(conv["responses"]),
                "extracted_entities": conv["extracted_entities"],
                "confidence": result["confidence"],
                "timestamp": "now"  # Use proper timestamp
            }
        except Exception as e:
            print(f"❌ Failed to generate summary: {e}")
            return {
                "conversation_id": conversation_id,
                "error": "Failed to generate summary",
                "raw_responses": conv["responses"]
            }