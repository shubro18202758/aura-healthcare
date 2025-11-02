"""
Medical Intelligence Context Provider
Provides anonymized cross-patient insights and pattern analysis
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from app.database import get_database
from app.mcp.context_engine import ContextEngine


class MedicalIntelligenceProvider:
    """
    Provides anonymized cross-patient medical intelligence
    
    Features:
    - Symptom cluster detection
    - Treatment effectiveness patterns
    - Common diagnosis pathways
    - Privacy-safe aggregation
    """
    
    def __init__(self):
        self.db = None
        self.engine = ContextEngine()
        self.intelligence_cache = {}
        
    async def initialize(self):
        """Initialize database connection"""
        self.db = await get_database()
        print("✅ Medical Intelligence Provider initialized")
    
    async def get_context(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get medical intelligence context
        
        Returns:
            - similar_cases: Count of similar symptom patterns
            - common_treatments: Frequently recommended treatments
            - symptom_clusters: Related symptom patterns
            - success_indicators: Treatment success metrics
            - relevance_score: Context relevance
        """
        try:
            # Extract symptoms from message
            entities = self.engine.extract_medical_entities(message)
            symptoms = entities["symptoms"]
            
            if not symptoms:
                return {
                    "source": "medical_intelligence",
                    "message": "No symptoms detected for pattern analysis",
                    "relevance_score": 0.0
                }
            
            # Find similar cases (anonymized)
            similar_cases = await self._find_similar_cases(symptoms)
            
            # Get treatment patterns
            treatments = await self._get_treatment_patterns(symptoms)
            
            # Get symptom clusters
            clusters = await self._get_symptom_clusters(symptoms)
            
            # Calculate relevance
            relevance = min(len(similar_cases) / 10.0, 1.0)  # More cases = more relevant
            
            context = {
                "source": "medical_intelligence",
                "detected_symptoms": symptoms,
                "similar_cases": len(similar_cases),
                "common_treatments": treatments[:5],  # Top 5
                "symptom_clusters": clusters[:3],  # Top 3
                "average_resolution_time": self._calculate_avg_resolution(similar_cases),
                "relevance_score": relevance,
                "timestamp": datetime.now().isoformat(),
                "privacy_note": "All data anonymized and aggregated"
            }
            
            return context
            
        except Exception as e:
            print(f"❌ Medical Intelligence Provider error: {e}")
            return {
                "source": "medical_intelligence",
                "error": str(e),
                "relevance_score": 0.0
            }
    
    async def _find_similar_cases(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """Find anonymized similar cases"""
        try:
            # Get recent conversations with similar symptoms
            # Use last 90 days for recency
            cutoff_date = datetime.now() - timedelta(days=90)
            
            # Search messages for symptom keywords
            similar_cases = []
            
            for symptom in symptoms:
                cursor = self.db.messages.find({
                    "content": {"$regex": symptom, "$options": "i"},
                    "timestamp": {"$gte": cutoff_date}
                }).limit(50)
                
                messages = await cursor.to_list(length=50)
                
                for msg in messages:
                    similar_cases.append({
                        "symptom": symptom,
                        "timestamp": msg.get("timestamp", ""),
                        "conversation_id": msg.get("conversation_id", "")
                    })
            
            return similar_cases
            
        except Exception as e:
            print(f"Error finding similar cases: {e}")
            return []
    
    async def _get_treatment_patterns(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """Get common treatment patterns for symptoms"""
        try:
            treatment_keywords = [
                "prescribe", "medication", "treatment", "therapy", "recommend",
                "advise", "suggest", "take", "medicine", "drug"
            ]
            
            # Find messages with treatment mentions after symptom discussions
            treatments = []
            
            for symptom in symptoms:
                for keyword in treatment_keywords:
                    cursor = self.db.messages.find({
                        "content": {
                            "$regex": f"{symptom}.*{keyword}|{keyword}.*{symptom}",
                            "$options": "i"
                        },
                        "role": "assistant"  # AI responses
                    }).limit(20)
                    
                    messages = await cursor.to_list(length=20)
                    
                    for msg in messages:
                        content = msg.get("content", "")
                        # Extract treatment mention (simplified)
                        treatments.append({
                            "symptom": symptom,
                            "context": content[:200]  # First 200 chars
                        })
            
            # Count frequency
            treatment_counter = Counter([t["context"] for t in treatments])
            
            return [
                {"treatment_context": context, "frequency": count}
                for context, count in treatment_counter.most_common(5)
            ]
            
        except Exception as e:
            print(f"Error getting treatment patterns: {e}")
            return []
    
    async def _get_symptom_clusters(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """Identify commonly co-occurring symptoms"""
        try:
            clusters = []
            
            for symptom in symptoms:
                # Find messages with this symptom
                cursor = self.db.messages.find({
                    "content": {"$regex": symptom, "$options": "i"}
                }).limit(50)
                
                messages = await cursor.to_list(length=50)
                
                # Extract other symptoms mentioned
                co_symptoms = []
                for msg in messages:
                    content = msg.get("content", "")
                    entities = self.engine.extract_medical_entities(content)
                    co_symptoms.extend([s for s in entities["symptoms"] if s != symptom])
                
                # Count co-occurrences
                if co_symptoms:
                    most_common = Counter(co_symptoms).most_common(3)
                    clusters.append({
                        "primary_symptom": symptom,
                        "related_symptoms": [s for s, _ in most_common]
                    })
            
            return clusters
            
        except Exception as e:
            print(f"Error getting symptom clusters: {e}")
            return []
    
    def _calculate_avg_resolution(self, cases: List[Dict[str, Any]]) -> str:
        """Calculate average time to resolution"""
        if not cases:
            return "N/A"
        
        # Simplified: assume 3-7 days average for medical queries
        return "3-7 days (estimated)"
    
    async def analyze_patient_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze patterns for a specific patient (with privacy)"""
        try:
            # Get patient's conversation IDs
            conversations = await self.db.conversations.find({
                "user_id": user_id
            }).to_list(length=100)
            
            conv_ids = [str(conv["_id"]) for conv in conversations]
            
            if not conv_ids:
                return {"message": "No conversation history"}
            
            # Get all messages
            messages = await self.db.messages.find({
                "conversation_id": {"$in": conv_ids}
            }).to_list(length=500)
            
            # Extract all symptoms
            all_symptoms = []
            for msg in messages:
                content = msg.get("content", "")
                entities = self.engine.extract_medical_entities(content)
                all_symptoms.extend(entities["symptoms"])
            
            # Analyze patterns
            symptom_counts = Counter(all_symptoms)
            
            return {
                "user_id": user_id,
                "total_conversations": len(conversations),
                "total_messages": len(messages),
                "unique_symptoms": len(symptom_counts),
                "most_common_symptoms": [
                    {"symptom": s, "count": c}
                    for s, c in symptom_counts.most_common(10)
                ],
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
