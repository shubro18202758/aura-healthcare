"""
TTS Router for AURA Healthcare System
Provides Text-to-Speech functionality with multiple voice options
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Literal

from app.services.tts_service import get_tts_service, TTSService, VoiceType, VOICE_PROFILES
from app.database import get_database
from app.routers.auth import get_current_active_user
from app.models import User
from app.models.user_preferences import UserPreferences, TTSPreferences


router = APIRouter(prefix="/api/tts", tags=["tts"])
security = HTTPBearer()


# Pydantic models
class TTSRequest(BaseModel):
    text: str
    voice_type: VoiceType = "sara"
    language: str = "en"


class VoiceUpdateRequest(BaseModel):
    voice_type: VoiceType


class TTSPreferencesUpdate(BaseModel):
    enabled: Optional[bool] = None
    voice_type: Optional[VoiceType] = None
    auto_play: Optional[bool] = None
    playback_speed: Optional[float] = None
    volume: Optional[float] = None


@router.post("/convert")
async def convert_text_to_speech(
    request: TTSRequest,
    current_user: User = Depends(get_current_active_user),
    tts_service: TTSService = Depends(get_tts_service)
):
    """
    Convert text to speech with specified voice
    
    Returns base64 encoded audio data
    """
    try:
        result = await tts_service.text_to_speech(
            text=request.text,
            voice_type=request.voice_type,
            language=request.language,
            return_base64=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate audio"
            )
        
        return {
            "success": True,
            "audio_data": result["audio_data"],
            "voice_type": result["voice_type"],
            "voice_info": result["voice_info"],
            "audio_size": result["audio_size"],
            "format": "mp3"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS conversion failed: {str(e)}"
        )


@router.get("/voices")
async def get_available_voices(
    current_user: User = Depends(get_current_active_user),
    tts_service: TTSService = Depends(get_tts_service)
):
    """
    Get list of available TTS voices
    
    Returns voice profiles with descriptions
    """
    voices_info = await tts_service.get_available_voices()
    
    return {
        "success": True,
        "voices": voices_info["voices"],
        "default": voices_info["default"],
        "engines_available": voices_info["engines"]
    }


@router.get("/preferences")
async def get_tts_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's TTS preferences
    """
    try:
        db = await get_database()
        
        # Fetch user preferences
        prefs_doc = await db.user_preferences.find_one({"user_id": current_user.user_id})
        
        if not prefs_doc:
            # Return default preferences
            default_prefs = UserPreferences(user_id=current_user.user_id)
            return {
                "success": True,
                "preferences": default_prefs.tts.dict()
            }
        
        prefs = UserPreferences(**prefs_doc)
        return {
            "success": True,
            "preferences": prefs.tts.dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
        )


@router.put("/preferences")
async def update_tts_preferences(
    update: TTSPreferencesUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user's TTS preferences
    """
    try:
        db = await get_database()
        
        # Fetch or create user preferences
        prefs_doc = await db.user_preferences.find_one({"user_id": current_user.user_id})
        
        if prefs_doc:
            prefs = UserPreferences(**prefs_doc)
        else:
            prefs = UserPreferences(user_id=current_user.user_id)
        
        # Update TTS preferences
        if update.enabled is not None:
            prefs.tts.enabled = update.enabled
        if update.voice_type is not None:
            prefs.tts.voice_type = update.voice_type
        if update.auto_play is not None:
            prefs.tts.auto_play = update.auto_play
        if update.playback_speed is not None:
            prefs.tts.playback_speed = max(0.5, min(2.0, update.playback_speed))
        if update.volume is not None:
            prefs.tts.volume = max(0.0, min(1.0, update.volume))
        
        # Save to database
        from datetime import datetime
        prefs.updated_at = datetime.utcnow()
        
        await db.user_preferences.update_one(
            {"user_id": current_user.user_id},
            {"$set": prefs.dict()},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "TTS preferences updated",
            "preferences": prefs.tts.dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.post("/set-voice/{voice_type}")
async def set_default_voice(
    voice_type: VoiceType,
    current_user: User = Depends(get_current_active_user)
):
    """
    Quick endpoint to set default voice type
    """
    try:
        db = await get_database()
        
        # Fetch or create user preferences
        prefs_doc = await db.user_preferences.find_one({"user_id": current_user.user_id})
        
        if prefs_doc:
            prefs = UserPreferences(**prefs_doc)
        else:
            prefs = UserPreferences(user_id=current_user.user_id)
        
        # Update voice type
        prefs.tts.voice_type = voice_type
        
        from datetime import datetime
        prefs.updated_at = datetime.utcnow()
        
        await db.user_preferences.update_one(
            {"user_id": current_user.user_id},
            {"$set": prefs.dict()},
            upsert=True
        )
        
        return {
            "success": True,
            "message": f"Default voice set to {VOICE_PROFILES[voice_type]['name']}",
            "voice_type": voice_type,
            "voice_info": VOICE_PROFILES[voice_type]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set voice: {str(e)}"
        )


@router.delete("/cache")
async def clear_audio_cache(
    current_user: User = Depends(get_current_active_user),
    tts_service: TTSService = Depends(get_tts_service)
):
    """
    Clear cached audio files (admin only in production)
    """
    try:
        deleted = await tts_service.clear_cache(older_than_hours=24)
        
        return {
            "success": True,
            "message": f"Cleared {deleted} cached audio files"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )
