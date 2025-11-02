"""
Patient History Context Provider
Fetches and processes patient's complete conversation history
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bson import ObjectId

from app.database import get_database
from app.mcp.context_engine import ContextEngine


class PatientHistoryProvider:
    """
    Provides context from patient's full conversation history
    
    Features:
    - Complete conversation history retrieval
    - Symptom pattern extraction
    - Medication/allergy tracking
    - Recent activity analysis
    """
    
    def __init__(self):
        self.db = None
        self.engine = ContextEngine()
        
    async def initialize(self):
        """Initialize database connection"""
        self.db = await get_database()
        print("✅ Patient History Provider initialized")
    
    async def get_context(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get patient history context
        
        Returns:
            - previous_conversations: List of past conversations
            - recent_symptoms: Extracted symptoms
            - medication_history: Medications mentioned
            - allergy_alerts: Known allergies
            - relevance_score: Context relevance (0-1)
        """
        try:
            # Get all conversations for this user
            conversations_cursor = self.db.conversations.find({
                "user_id": user_id
            }).sort("created_at", -1).limit(50)
            
            conversations = await conversations_cursor.to_list(length=50)
            
            # Get messages from recent conversations
            recent_messages = []
            conversation_ids = [str(conv["_id"]) for conv in conversations[:10]]
            
            if conversation_ids:
                messages_cursor = self.db.messages.find({
                    "conversation_id": {"$in": conversation_ids}
                }).sort("timestamp", -1).limit(100)
                
                recent_messages = await messages_cursor.to_list(length=100)
            
            # Extract symptoms from message history
            symptoms = set()
            medications = set()
            conditions = set()
            
            for msg in recent_messages:
                content = msg.get("content", "")
                entities = self.engine.extract_medical_entities(content)
                symptoms.update(entities["symptoms"])
                medications.update(entities["medications"])
                conditions.update(entities["conditions"])
            
            # Get user profile for allergies
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            allergies = user.get("allergies", []) if user else []
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance(
                message,
                list(symptoms),
                list(medications),
                conversations
            )
            
            context = {
                "source": "patient_history",
                "user_id": user_id,
                "previous_conversations": [
                    {
                        "id": str(conv["_id"]),
                        "created_at": conv.get("created_at", "").isoformat() if hasattr(conv.get("created_at", ""), "isoformat") else str(conv.get("created_at", "")),
                        "topic": conv.get("topic", "General"),
                        "message_count": conv.get("message_count", 0)
                    }
                    for conv in conversations[:10]
                ],
                "recent_symptoms": list(symptoms)[:10],
                "medication_history": list(medications)[:10],
                "known_conditions": list(conditions)[:5],
                "allergy_alerts": allergies,
                "total_conversations": len(conversations),
                "total_messages": len(recent_messages),
                "relevance_score": relevance_score,
                "timestamp": datetime.now().isoformat()
            }
            
            return context
            
        except Exception as e:
            print(f"❌ Patient History Provider error: {e}")
            return {
                "source": "patient_history",
                "error": str(e),
                "relevance_score": 0.0
            }
    
    def _calculate_relevance(
        self,
        message: str,
        symptoms: List[str],
        medications: List[str],
        conversations: List[Dict]
    ) -> float:
        """Calculate how relevant history is to current message"""
        score = 0.0
        message_lower = message.lower()
        
        # Check if message mentions past symptoms
        for symptom in symptoms:
            if symptom in message_lower:
                score += 0.2
        
        # Check if message mentions medications
        for med in medications:
            if med in message_lower:
                score += 0.2
        
        # Recency boost
        if conversations:
            latest = conversations[0].get("created_at")
            if latest:
                try:
                    if isinstance(latest, str):
                        latest = datetime.fromisoformat(latest)
                    age_days = (datetime.now() - latest).days
                    if age_days < 7:
                        score += 0.3
                    elif age_days < 30:
                        score += 0.1
                except:
                    pass
        
        # Conversation count boost
        if len(conversations) > 5:
            score += 0.2
        
        return min(score, 1.0)
    
    async def get_patient_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive patient summary"""
        try:
            # Get user profile
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"error": "User not found"}
            
            # Get conversation count
            conv_count = await self.db.conversations.count_documents({"user_id": user_id})
            
            # Get message count
            conversations = await self.db.conversations.find({"user_id": user_id}).to_list(length=1000)
            conv_ids = [str(conv["_id"]) for conv in conversations]
            
            msg_count = 0
            if conv_ids:
                msg_count = await self.db.messages.count_documents({
                    "conversation_id": {"$in": conv_ids}
                })
            
            summary = {
                "user_id": user_id,
                "name": user.get("name", "Unknown"),
                "email": user.get("email", ""),
                "role": user.get("role", "patient"),
                "total_conversations": conv_count,
                "total_messages": msg_count,
                "member_since": user.get("created_at", "").isoformat() if hasattr(user.get("created_at", ""), "isoformat") else str(user.get("created_at", "")),
                "allergies": user.get("allergies", []),
                "specialty": user.get("specialty", None) if user.get("role") == "doctor" else None
            }
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}
