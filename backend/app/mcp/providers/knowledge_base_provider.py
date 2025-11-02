"""
Knowledge Base Context Provider
Fetches doctor-curated specialty knowledge
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Dict, List, Optional, Any
from datetime import datetime

from app.database import get_database
from app.mcp.context_engine import ContextEngine


class KnowledgeBaseProvider:
    """
    Provides doctor-curated knowledge base context
    
    Features:
    - Specialty-specific knowledge
    - Best practices from training data
    - Treatment guidelines
    - Medical protocols
    """
    
    def __init__(self):
        self.db = None
        self.engine = ContextEngine()
        self.knowledge_cache = {}
        
    async def initialize(self):
        """Initialize database connection"""
        self.db = await get_database()
        print("✅ Knowledge Base Provider initialized")
    
    async def get_context(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get knowledge base context
        
        Returns:
            - relevant_knowledge: Matching knowledge entries
            - specialty: Detected medical specialty
            - protocols: Relevant medical protocols
            - relevance_score: Context relevance
        """
        try:
            # Detect specialty from message
            specialty = self._detect_specialty(message)
            
            # Get knowledge for specialty
            knowledge_entries = await self._fetch_knowledge(specialty)
            
            # Filter relevant entries
            relevant = []
            for entry in knowledge_entries:
                relevance = self.engine.score_relevance(entry, message)
                if relevance > 0.3:
                    entry["relevance_score"] = relevance
                    relevant.append(entry)
            
            # Sort by relevance
            relevant.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # Calculate overall relevance
            overall_relevance = sum(e.get("relevance_score", 0) for e in relevant[:5]) / 5 if relevant else 0.0
            
            context = {
                "source": "knowledge_base",
                "specialty": specialty,
                "relevant_knowledge": relevant[:10],  # Top 10
                "total_entries": len(knowledge_entries),
                "matched_entries": len(relevant),
                "relevance_score": overall_relevance,
                "timestamp": datetime.now().isoformat()
            }
            
            return context
            
        except Exception as e:
            print(f"❌ Knowledge Base Provider error: {e}")
            return {
                "source": "knowledge_base",
                "error": str(e),
                "relevance_score": 0.0
            }
    
    def _detect_specialty(self, message: str) -> str:
        """Detect medical specialty from message"""
        message_lower = message.lower()
        
        specialty_keywords = {
            "Cardiology": ["heart", "cardiac", "blood pressure", "chest pain", "arrhythmia"],
            "Dermatology": ["skin", "rash", "acne", "eczema", "psoriasis"],
            "Orthopedics": ["bone", "joint", "fracture", "sprain", "arthritis"],
            "Neurology": ["headache", "migraine", "seizure", "brain", "nerve"],
            "Gastroenterology": ["stomach", "digestion", "nausea", "diarrhea", "gut"],
            "Respiratory": ["cough", "breathing", "asthma", "lung", "bronchitis"],
            "Pediatrics": ["child", "baby", "infant", "kid", "pediatric"],
            "Gynecology": ["pregnancy", "menstrual", "gynecological", "women"],
            "Psychiatry": ["mental", "depression", "anxiety", "stress", "psychiatric"]
        }
        
        for specialty, keywords in specialty_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return specialty
        
        return "General Medicine"
    
    async def _fetch_knowledge(self, specialty: str) -> List[Dict[str, Any]]:
        """Fetch knowledge entries for specialty"""
        try:
            # Check cache
            if specialty in self.knowledge_cache:
                cache_entry = self.knowledge_cache[specialty]
                age = (datetime.now() - cache_entry["timestamp"]).seconds
                if age < 3600:  # 1 hour cache
                    return cache_entry["data"]
            
            # Fetch from database
            cursor = self.db.knowledge_base.find({
                "specialty": {"$in": [specialty, "General Medicine"]}
            }).limit(100)
            
            entries = await cursor.to_list(length=100)
            
            # Process entries
            knowledge = []
            for entry in entries:
                knowledge.append({
                    "id": str(entry.get("_id", "")),
                    "title": entry.get("title", ""),
                    "content": entry.get("content", ""),
                    "specialty": entry.get("specialty", specialty),
                    "tags": entry.get("tags", []),
                    "created_by": entry.get("created_by", ""),
                    "created_at": entry.get("created_at", "").isoformat() if hasattr(entry.get("created_at", ""), "isoformat") else str(entry.get("created_at", ""))
                })
            
            # Cache result
            self.knowledge_cache[specialty] = {
                "data": knowledge,
                "timestamp": datetime.now()
            }
            
            return knowledge
            
        except Exception as e:
            print(f"Error fetching knowledge: {e}")
            return []
    
    async def get_specialty_guidelines(self, specialty: str) -> Dict[str, Any]:
        """Get comprehensive guidelines for a specialty"""
        try:
            knowledge = await self._fetch_knowledge(specialty)
            
            # Group by tags
            by_tags = {}
            for entry in knowledge:
                for tag in entry.get("tags", []):
                    if tag not in by_tags:
                        by_tags[tag] = []
                    by_tags[tag].append(entry)
            
            return {
                "specialty": specialty,
                "total_entries": len(knowledge),
                "categories": list(by_tags.keys()),
                "guidelines_by_category": by_tags
            }
            
        except Exception as e:
            return {"error": str(e)}
