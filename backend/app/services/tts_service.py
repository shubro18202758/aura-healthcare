"""
Text-to-Speech Service for AURA Healthcare System
Provides 6 different voice options for AI responses
Supports both patient and doctor interfaces
"""

import os
import hashlib
import asyncio
from typing import Optional, Literal
from pathlib import Path
import base64
from datetime import datetime, timedelta

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️  pyttsx3 not installed. Install with: pip install pyttsx3")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️  gTTS not installed. Install with: pip install gtts")


# Voice type definitions
VoiceType = Literal["david", "sara", "emma", "james", "olivia", "noah"]

VOICE_PROFILES = {
    "david": {
        "name": "David",
        "gender": "male",
        "description": "Professional, confident male voice",
        "rate": 175,  # Words per minute
        "volume": 0.9,
        "pitch": 1.0
    },
    "sara": {
        "name": "Sara",
        "gender": "female",
        "description": "Warm, caring female voice",
        "rate": 165,
        "volume": 0.95,
        "pitch": 1.1
    },
    "emma": {
        "name": "Emma",
        "gender": "female",
        "description": "Young, friendly female voice",
        "rate": 180,
        "volume": 0.9,
        "pitch": 1.2
    },
    "james": {
        "name": "James",
        "gender": "male",
        "description": "Deep, authoritative male voice",
        "rate": 160,
        "volume": 0.95,
        "pitch": 0.85
    },
    "olivia": {
        "name": "Olivia",
        "gender": "female",
        "description": "Calm, soothing female voice",
        "rate": 155,
        "volume": 0.9,
        "pitch": 1.05
    },
    "noah": {
        "name": "Noah",
        "gender": "male",
        "description": "Energetic, clear male voice",
        "rate": 185,
        "volume": 0.9,
        "pitch": 1.05
    }
}


class TTSService:
    """
    Text-to-Speech service with multiple voice options
    
    Features:
    - 6 different voice personalities
    - Audio caching for performance
    - Multiple TTS engine support (pyttsx3, gTTS)
    - Base64 audio encoding for API responses
    """
    
    def __init__(self):
        self.cache_dir = Path("audio_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=24)  # Cache audio for 24 hours
        self.engine = None
        
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
            except Exception as e:
                print(f"⚠️  Could not initialize pyttsx3: {e}")
                self.engine = None
    
    def _get_cache_key(self, text: str, voice_type: VoiceType, language: str) -> str:
        """Generate cache key for audio file"""
        content = f"{text}_{voice_type}_{language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.mp3"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached audio is still valid"""
        if not cache_path.exists():
            return False
        
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - file_time < self.cache_duration
    
    async def text_to_speech(
        self,
        text: str,
        voice_type: VoiceType = "sara",
        language: str = "en",
        return_base64: bool = True
    ) -> Optional[dict]:
        """
        Convert text to speech with specified voice
        
        Args:
            text: Text to convert
            voice_type: Voice personality (david, sara, emma, james, olivia, noah)
            language: Language code (en, es, fr, etc.)
            return_base64: If True, return base64 encoded audio
        
        Returns:
            dict with audio_data (base64), audio_url, voice_info, or None if failed
        """
        if not text or not text.strip():
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(text, voice_type, language)
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            print(f"✅ Using cached audio for voice {voice_type}")
            return await self._load_cached_audio(cache_path, voice_type, return_base64)
        
        # Generate new audio
        try:
            if GTTS_AVAILABLE and language != "en":
                # Use gTTS for non-English languages
                audio_path = await self._generate_gtts(text, language, cache_path)
            elif TTS_AVAILABLE and self.engine:
                # Use pyttsx3 for English with voice customization
                audio_path = await self._generate_pyttsx3(text, voice_type, cache_path)
            elif GTTS_AVAILABLE:
                # Fallback to gTTS for English
                audio_path = await self._generate_gtts(text, language, cache_path)
            else:
                print("⚠️  No TTS engine available")
                return None
            
            if audio_path and audio_path.exists():
                return await self._load_cached_audio(audio_path, voice_type, return_base64)
            
        except Exception as e:
            print(f"❌ TTS generation error: {e}")
            return None
        
        return None
    
    async def _generate_pyttsx3(
        self,
        text: str,
        voice_type: VoiceType,
        output_path: Path
    ) -> Optional[Path]:
        """Generate audio using pyttsx3 with voice customization"""
        try:
            profile = VOICE_PROFILES[voice_type]
            
            # Configure voice settings
            self.engine.setProperty('rate', profile['rate'])
            self.engine.setProperty('volume', profile['volume'])
            
            # Try to select voice by gender
            voices = self.engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if profile['gender'] in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            # Save to file
            self.engine.save_to_file(text, str(output_path))
            self.engine.runAndWait()
            
            return output_path if output_path.exists() else None
            
        except Exception as e:
            print(f"❌ pyttsx3 generation error: {e}")
            return None
    
    async def _generate_gtts(
        self,
        text: str,
        language: str,
        output_path: Path
    ) -> Optional[Path]:
        """Generate audio using gTTS (Google Text-to-Speech)"""
        try:
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(output_path))
            return output_path if output_path.exists() else None
            
        except Exception as e:
            print(f"❌ gTTS generation error: {e}")
            return None
    
    async def _load_cached_audio(
        self,
        audio_path: Path,
        voice_type: VoiceType,
        return_base64: bool
    ) -> dict:
        """Load and encode cached audio file"""
        try:
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            result = {
                "voice_type": voice_type,
                "voice_info": VOICE_PROFILES[voice_type],
                "audio_size": len(audio_bytes),
                "cached": True
            }
            
            if return_base64:
                result["audio_data"] = base64.b64encode(audio_bytes).decode('utf-8')
            else:
                result["audio_path"] = str(audio_path)
            
            return result
            
        except Exception as e:
            print(f"❌ Error loading cached audio: {e}")
            return None
    
    async def get_available_voices(self) -> dict:
        """Get list of available voices with descriptions"""
        return {
            "voices": VOICE_PROFILES,
            "default": "sara",
            "engines": {
                "pyttsx3": TTS_AVAILABLE,
                "gtts": GTTS_AVAILABLE
            }
        }
    
    async def clear_cache(self, older_than_hours: int = 24):
        """Clear old cached audio files"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            deleted = 0
            
            for file_path in self.cache_dir.glob("*.mp3"):
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    deleted += 1
            
            print(f"🧹 Cleared {deleted} cached audio files")
            return deleted
            
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return 0
    
    def get_voice_info(self, voice_type: VoiceType) -> dict:
        """Get information about a specific voice"""
        return VOICE_PROFILES.get(voice_type, VOICE_PROFILES["sara"])


# Global TTS service instance
tts_service = TTSService()


async def get_tts_service() -> TTSService:
    """Get TTS service instance"""
    return tts_service
