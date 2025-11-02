"""
Chat Router for AURA Healthcare System
Handles real-time messaging, conversation management, and AI-powered responses
Enhanced with Model Context Protocol (MCP) for intelligent context injection
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel

from app.database import get_database
from app.config import get_settings
from app.models import User, Role
from app.models.conversation import Message, Conversation, MessageRole, ConversationStatus
from app.routers.auth import get_current_active_user, require_role

# Import MCP System
from app.mcp.mcp_server import mcp_server, get_mcp_context

# Import TTS System
from app.services.tts_service import get_tts_service
from app.models.user_preferences import UserPreferences

router = APIRouter(prefix="/api/chat", tags=["chat"])
security = HTTPBearer()
settings = get_settings()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_conversations: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        self.active_conversations[conversation_id] = websocket
        
    def disconnect(self, conversation_id: str):
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
            
    async def send_message(self, message: dict, conversation_id: str):
        if conversation_id in self.active_conversations:
            await self.active_conversations[conversation_id].send_json(message)

manager = ConnectionManager()

# Pydantic models
class ChatMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    language: str = "en"

class ConversationCreate(BaseModel):
    patient_id: str
    initial_message: Optional[str] = None
    language: str = "en"

class HandoffRequest(BaseModel):
    conversation_id: str
    doctor_id: str
    reason: Optional[str] = None

# Helper functions
async def get_or_create_conversation(
    patient_id: str,
    language: str = "en",
    initial_message: Optional[str] = None
) -> Conversation:
    """Get existing active conversation or create new one"""
    db = await get_database()
    
    existing = await db.conversations.find_one({
        "patient_id": patient_id,
        "status": {"$in": ["active", "waiting"]}
    })
    
    if existing:
        return Conversation(**existing)
    
    conversation = Conversation(
        conversation_id=f"conv_{datetime.utcnow().timestamp()}_{patient_id}",
        patient_id=patient_id,
        language=language,
        status=ConversationStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await db.conversations.insert_one(conversation.dict())
    
    if initial_message:
        message = Message(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            conversation_id=conversation.conversation_id,
            sender_role=MessageRole.PATIENT,
            content=initial_message,
            timestamp=datetime.utcnow()
        )
        await db.messages.insert_one(message.dict())
    
    return conversation

async def get_knowledge_base_context(specialty: str, db) -> str:
    """Fetch knowledge base context for a specific specialty"""
    if not specialty:
        return ""
    
    try:
        # Fetch active knowledge base entries for the specialty
        query = {"specialty": specialty, "is_active": True}
        cursor = db.knowledge_base.find(query).limit(10)
        entries = await cursor.to_list(length=10)
        
        if not entries:
            return ""
        
        # Build context from knowledge base
        context_parts = []
        context_parts.append(f"\n\n=== Medical Specialty Context: {specialty.upper()} ===")
        
        for entry in entries:
            context_parts.append(f"\nTopic: {entry['topic']}")
            context_parts.append(f"Key Questions to Consider:")
            for q in entry['questions'][:5]:  # Limit to 5 questions per topic
                context_parts.append(f"  - {q}")
            context_parts.append(f"Context: {entry['context'][:300]}...")  # Limit context length
            context_parts.append(f"Keywords: {', '.join(entry['keywords'][:5])}")
        
        return "\n".join(context_parts)
    except Exception as e:
        print(f"Error fetching knowledge base context: {e}")
        return ""

async def generate_ai_response(message_content: str, conversation_id: str, language: str = "en", patient_specialty: str = None, user_id: str = None) -> str:
    """
    Generate AI response using the AI service with MCP-enhanced context
    
    MCP provides:
    - Full patient history context
    - Service classification and auto-routing
    - Specialty-specific knowledge base
    - Cross-patient medical intelligence
    """
    try:
        from app.main import app
        if hasattr(app.state, 'ai_service') and app.state.ai_service:
            # Build base context
            base_context = f"You are AURA, an AI healthcare assistant. Respond in a friendly, professional manner. Language: {language}. Keep responses concise and helpful."
            
            # ===== MCP CONTEXT INJECTION =====
            mcp_context_str = ""
            service_classification = None
            
            if user_id:
                try:
                    # Get comprehensive MCP context
                    print(f"🔍 Fetching MCP context for user {user_id}...")
                    mcp_context = await get_mcp_context(
                        user_id=user_id,
                        message=message_content,
                        conversation_id=conversation_id
                    )
                    
                    # Extract service classification
                    if "contexts" in mcp_context and "service_classification" in mcp_context["contexts"]:
                        service_classification = mcp_context["contexts"]["service_classification"]
                        print(f"📊 Service classified as: {service_classification.get('predicted_service_type')} (confidence: {service_classification.get('confidence', 0):.1%})")
                    
                    # Add MCP context summary to prompt
                    if mcp_context.get("context_summary"):
                        mcp_context_str = f"\n\n=== INTELLIGENT CONTEXT (MCP) ===\n{mcp_context['context_summary']}"
                        
                        # Add detailed context from each provider
                        contexts = mcp_context.get("contexts", {})
                        
                        # Patient History
                        if "patient_history" in contexts:
                            hist = contexts["patient_history"]
                            if hist.get("recent_symptoms"):
                                mcp_context_str += f"\n\nPatient's Recent Symptoms: {', '.join(hist['recent_symptoms'][:5])}"
                            if hist.get("known_conditions"):
                                mcp_context_str += f"\nKnown Conditions: {', '.join(hist['known_conditions'])}"
                            if hist.get("allergy_alerts"):
                                mcp_context_str += f"\n⚠️  ALLERGIES: {', '.join(hist['allergy_alerts'])}"
                        
                        # Service Classification
                        if service_classification:
                            mcp_context_str += f"\n\nDetected Intent: {service_classification['predicted_service_type']}"
                            if service_classification.get("sub_services"):
                                mcp_context_str += f" ({', '.join(service_classification['sub_services'])})"
                        
                        # Knowledge Base
                        if "knowledge_base" in contexts:
                            kb = contexts["knowledge_base"]
                            if kb.get("specialty"):
                                mcp_context_str += f"\n\nRelevant Specialty: {kb['specialty']}"
                        
                        # Medical Intelligence
                        if "medical_intelligence" in contexts:
                            mi = contexts["medical_intelligence"]
                            if mi.get("similar_cases", 0) > 0:
                                mcp_context_str += f"\n\nSimilar Cases: {mi['similar_cases']} patients with similar symptoms"
                                if mi.get("common_treatments"):
                                    mcp_context_str += f"\nCommon Treatment Approaches: {len(mi['common_treatments'])} documented"
                        
                        mcp_context_str += "\n\nIMPORTANT: Use this context to provide more personalized, accurate, and contextually relevant responses. Reference the patient's history when appropriate."
                    
                    print(f"✅ MCP context fetched (relevance: {mcp_context.get('total_relevance', 0):.2f})")
                    
                except Exception as mcp_error:
                    print(f"⚠️  MCP context error (continuing without): {mcp_error}")
            
            # Add specialty-specific knowledge base context (legacy support)
            kb_context = ""
            if patient_specialty and not mcp_context_str:  # Only use if MCP didn't provide context
                db = await get_database()
                kb_context = await get_knowledge_base_context(patient_specialty, db)
                if kb_context:
                    base_context += f"\n\n{kb_context}"
                    base_context += f"\n\nIMPORTANT: Use the above specialty-specific questions and context to guide your conversation with the patient. Ask relevant questions from the knowledge base when appropriate."
            
            # Combine all context
            full_context = base_context + mcp_context_str + kb_context
            
            # Generate AI response
            response = await app.state.ai_service.generate_response(
                message_content,
                context=full_context
            )
            
            return response
        else:
            return "Hello! I'm AURA, your AI healthcare assistant. How can I help you today?"
    except Exception as e:
        print(f"❌ AI response generation error: {e}")
        import traceback
        traceback.print_exc()
        return "I'm experiencing technical difficulties. Please try again or contact support."

# REST API endpoints
@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new conversation"""
    if current_user.role == Role.PATIENT and current_user.user_id != request.patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    conversation = await get_or_create_conversation(
        patient_id=request.patient_id,
        language=request.language,
        initial_message=request.initial_message
    )
    
    if request.initial_message:
        # Get patient's specialty for knowledge base context
        patient_specialty = current_user.specialty if current_user.role == Role.PATIENT else None
        
        ai_response = await generate_ai_response(
            request.initial_message,
            conversation.conversation_id,
            request.language,
            patient_specialty,
            user_id=request.patient_id  # Pass user_id for MCP context
        )
        
        db = await get_database()
        ai_message = Message(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            conversation_id=conversation.conversation_id,
            sender_role=MessageRole.AI,
            content=ai_response,
            timestamp=datetime.utcnow()
        )
        await db.messages.insert_one(ai_message.dict())
        
        return {
            "conversation": conversation.dict(),
            "initial_response": ai_response
        }
    
    return {"conversation": conversation.dict()}

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get conversation details"""
    db = await get_database()
    
    conversation = await db.conversations.find_one({"conversation_id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user.role == Role.PATIENT and conversation["patient_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = await db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1).to_list(length=None)
    
    # Convert ObjectId to string for JSON serialization
    if conversation.get("_id"):
        conversation["_id"] = str(conversation["_id"])
    
    for msg in messages:
        if msg.get("_id"):
            msg["_id"] = str(msg["_id"])
    
    return {
        "conversation": conversation,
        "messages": messages
    }

@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send a message in a conversation"""
    db = await get_database()
    
    conversation = await db.conversations.find_one({"conversation_id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user.role == Role.PATIENT and conversation["patient_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get patient's specialty for knowledge base context
    patient_specialty = None
    if current_user.role == Role.PATIENT:
        patient_specialty = current_user.specialty
    else:
        # If doctor is sending message, get patient's specialty from their profile
        patient = await db.users.find_one({"user_id": conversation["patient_id"]})
        if patient:
            patient_specialty = patient.get("specialty")
    
    user_message = Message(
        message_id=f"msg_{datetime.utcnow().timestamp()}",
        conversation_id=conversation_id,
        sender_role=MessageRole.PATIENT if current_user.role == Role.PATIENT else MessageRole.DOCTOR,
        sender_id=current_user.user_id,
        content=request.message,
        timestamp=datetime.utcnow()
    )
    await db.messages.insert_one(user_message.dict())
    
    # Track patient activity
    if current_user.role == Role.PATIENT:
        from app.services.activity_tracker import get_activity_tracker
        from app.models.activity import ActivityType
        tracker = await get_activity_tracker()
        session_id = await tracker.get_active_session(current_user.user_id)
        await tracker.log_activity(
            patient_id=current_user.user_id,
            patient_name=current_user.full_name,
            activity_type=ActivityType.CHAT_MESSAGE,
            description=f"Sent chat message: {request.message[:50]}...",
            session_id=session_id,
            metadata={"conversation_id": conversation_id, "message_length": len(request.message)}
        )
    
    # Use patient_id for MCP context (not doctor_id)
    context_user_id = conversation["patient_id"]
    
    ai_response = await generate_ai_response(
        request.message,
        conversation_id,
        request.language,
        patient_specialty,
        user_id=context_user_id  # Pass patient_id for MCP context
    )
    
    ai_message = Message(
        message_id=f"msg_{datetime.utcnow().timestamp() + 0.001}",
        conversation_id=conversation_id,
        sender_role=MessageRole.AI,
        content=ai_response,
        timestamp=datetime.utcnow()
    )
    await db.messages.insert_one(ai_message.dict())
    
    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {"updated_at": datetime.utcnow()}}
    )
    
    # ===== TTS AUDIO GENERATION =====
    audio_data = None
    voice_type = "sara"  # Default voice
    
    try:
        # Get user's TTS preferences
        prefs_doc = await db.user_preferences.find_one({"user_id": current_user.user_id})
        if prefs_doc:
            prefs = UserPreferences(**prefs_doc)
            if prefs.tts.enabled:
                voice_type = prefs.tts.voice_type
                
                # Generate TTS audio for AI response
                tts_service = await get_tts_service()
                tts_result = await tts_service.text_to_speech(
                    text=ai_response,
                    voice_type=voice_type,
                    language=request.language,
                    return_base64=True
                )
                
                if tts_result:
                    audio_data = tts_result.get("audio_data")
                    print(f"🔊 TTS audio generated for {voice_type} voice ({tts_result.get('audio_size', 0)} bytes)")
    except Exception as tts_error:
        print(f"⚠️  TTS generation error (continuing without audio): {tts_error}")
    
    response_data = {
        "user_message": user_message.dict(),
        "ai_response": ai_message.dict()
    }
    
    # Add audio data if generated
    if audio_data:
        response_data["audio"] = {
            "data": audio_data,
            "voice_type": voice_type,
            "format": "mp3"
        }
    
    return response_data
