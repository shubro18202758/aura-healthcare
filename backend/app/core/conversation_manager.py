"""
AURA Healthcare - Conversation Manager
Handles conversation flow, context management, and AI-human handoff
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from app.config import settings
from app.database import get_redis

class ConversationManager:
    """Manages patient-doctor conversations with context awareness"""
    
    def __init__(self):
        self.redis_client = None
        self.max_history = settings.MAX_CONVERSATION_HISTORY
        self.timeout = settings.CONVERSATION_TIMEOUT
        
    async def initialize(self):
        """Initialize conversation manager"""
        self.redis_client = get_redis()
        print("✅ Conversation Manager initialized")
    
    async def start_conversation(
        self,
        patient_id: str,
        doctor_id: Optional[str] = None,
        specialty: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Start a new conversation"""
        
        conversation = {
            "id": self._generate_conversation_id(),
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "specialty": specialty,
            "language": language,
            "status": "active",
            "mode": "ai" if not doctor_id else "human",
            "started_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "messages": [],
            "context": {
                "patient_info_collected": False,
                "urgency_level": "normal",
                "key_symptoms": [],
                "mentioned_medications": [],
                "follow_up_needed": False
            }
        }
        
        # Store in Redis for quick access
        await self._save_conversation(conversation)
        
        return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        sender: str,
        message: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Add a message to conversation"""
        
        conversation = await self.get_conversation(conversation_id)
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        message_obj = {
            "id": self._generate_message_id(),
            "sender": sender,
            "message": message,
            "type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        conversation["messages"].append(message_obj)
        conversation["last_activity"] = datetime.utcnow().isoformat()
        
        # Trim history if needed
        if len(conversation["messages"]) > self.max_history:
            conversation["messages"] = conversation["messages"][-self.max_history:]
        
        # Update context based on message
        await self._update_context(conversation, message_obj)
        
        await self._save_conversation(conversation)
        
        return message_obj
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation from Redis"""
        try:
            data = self.redis_client.get(f"conversation:{conversation_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error retrieving conversation: {e}")
            return None
    
    async def get_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context for AI"""
        conversation = await self.get_conversation(conversation_id)
        
        if not conversation:
            return {}
        
        # Build context from conversation history
        recent_messages = conversation["messages"][-10:]  # Last 10 messages
        
        context = {
            "conversation_id": conversation_id,
            "patient_id": conversation["patient_id"],
            "doctor_id": conversation["doctor_id"],
            "specialty": conversation["specialty"],
            "language": conversation["language"],
            "mode": conversation["mode"],
            "urgency_level": conversation["context"].get("urgency_level", "normal"),
            "key_symptoms": conversation["context"].get("key_symptoms", []),
            "mentioned_medications": conversation["context"].get("mentioned_medications", []),
            "recent_messages": recent_messages,
            "message_count": len(conversation["messages"])
        }
        
        return context
    
    async def handoff_to_doctor(self, conversation_id: str, doctor_id: str):
        """Hand off AI conversation to human doctor"""
        conversation = await self.get_conversation(conversation_id)
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation["doctor_id"] = doctor_id
        conversation["mode"] = "human"
        conversation["handoff_at"] = datetime.utcnow().isoformat()
        
        # Add system message
        await self.add_message(
            conversation_id,
            "system",
            f"Conversation transferred to doctor",
            "system"
        )
        
        await self._save_conversation(conversation)
    
    async def end_conversation(self, conversation_id: str, reason: str = "completed"):
        """End a conversation"""
        conversation = await self.get_conversation(conversation_id)
        
        if not conversation:
            return
        
        conversation["status"] = "ended"
        conversation["ended_at"] = datetime.utcnow().isoformat()
        conversation["end_reason"] = reason
        
        await self._save_conversation(conversation)
        
        # Schedule for archival (move to MongoDB)
        # This would be handled by a background task
    
    async def _update_context(self, conversation: Dict, message: Dict):
        """Update conversation context based on new message"""
        
        # Extract key information from message
        text = message["message"].lower()
        
        # Check for urgency indicators
        urgent_keywords = ["severe", "emergency", "urgent", "critical", "chest pain", 
                          "difficulty breathing", "unconscious", "bleeding heavily"]
        
        if any(keyword in text for keyword in urgent_keywords):
            conversation["context"]["urgency_level"] = "high"
        
        # This would integrate with NLP service for better extraction
        # For now, basic keyword matching
    
    async def _save_conversation(self, conversation: Dict):
        """Save conversation to Redis"""
        try:
            conversation_id = conversation["id"]
            self.redis_client.setex(
                f"conversation:{conversation_id}",
                self.timeout,
                json.dumps(conversation)
            )
        except Exception as e:
            print(f"Error saving conversation: {e}")
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID"""
        from uuid import uuid4
        return f"conv_{uuid4().hex[:12]}"
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        from uuid import uuid4
        return f"msg_{uuid4().hex[:12]}"
    
    async def get_active_conversations(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Get all active conversations for a doctor"""
        # This would query MongoDB for production
        # For now, return empty list
        return []
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Generate a summary of the conversation"""
        conversation = await self.get_conversation(conversation_id)
        
        if not conversation:
            return {}
        
        message_count = len(conversation["messages"])
        
        summary = {
            "conversation_id": conversation_id,
            "patient_id": conversation["patient_id"],
            "doctor_id": conversation["doctor_id"],
            "status": conversation["status"],
            "started_at": conversation["started_at"],
            "duration_minutes": self._calculate_duration(conversation),
            "message_count": message_count,
            "urgency_level": conversation["context"].get("urgency_level"),
            "key_symptoms": conversation["context"].get("key_symptoms", []),
            "follow_up_needed": conversation["context"].get("follow_up_needed", False)
        }
        
        return summary
    
    def _calculate_duration(self, conversation: Dict) -> int:
        """Calculate conversation duration in minutes"""
        try:
            start = datetime.fromisoformat(conversation["started_at"])
            last = datetime.fromisoformat(conversation["last_activity"])
            duration = (last - start).total_seconds() / 60
            return int(duration)
        except:
            return 0

# Global instance
conversation_manager = ConversationManager()
