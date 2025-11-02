# 🎙️ Text-to-Speech (TTS) Implementation Guide

## Overview

I've successfully implemented a comprehensive **Text-to-Speech (TTS) system** for AURA Healthcare that enables voice-enabled AI responses across **both patient and doctor interfaces**. The system includes **6 different voice personalities** and full user customization.

---

## ✅ What's Been Implemented

### Backend Components

#### 1. **TTS Service** (`backend/app/services/tts_service.py`)
- **6 Voice Personalities**:
  - 👨‍💼 **David** - Professional, confident male voice
  - 👩‍⚕️ **Sara** - Warm, caring female voice (default)
  - 👩‍🦰 **Emma** - Young, friendly female voice
  - 👨‍🏫 **James** - Deep, authoritative male voice
  - 🧘‍♀️ **Olivia** - Calm, soothing female voice
  - 👨‍💻 **Noah** - Energetic, clear male voice

- **Features**:
  - Base64 audio encoding for API responses
  - 24-hour audio caching for performance
  - Multi-engine support (pyttsx3, gTTS)
  - Customizable rate, volume, and pitch per voice
  - Automatic cache cleanup

#### 2. **User Preferences Model** (`backend/app/models/user_preferences.py`)
- TTS preferences storage:
  - Enable/disable toggle
  - Voice type selection
  - Auto-play setting
  - Playback speed (0.5x - 2.0x)
  - Volume control (0-100%)

#### 3. **TTS Router** (`backend/app/routers/tts_router.py`)
- **API Endpoints**:
  - `POST /api/tts/convert` - Convert text to speech
  - `GET /api/tts/voices` - Get available voices
  - `GET /api/tts/preferences` - Get user TTS preferences
  - `PUT /api/tts/preferences` - Update preferences
  - `POST /api/tts/set-voice/{voice_type}` - Quick voice change
  - `DELETE /api/tts/cache` - Clear audio cache

#### 4. **Enhanced Chat Router** (`backend/app/routers/chat.py`)
- **Automatic TTS Integration**:
  - Every AI response automatically generates audio
  - Audio included in API response if TTS enabled
  - Uses user's preferred voice
  - Respects user TTS preferences

#### 5. **Main App Integration** (`backend/app/main.py`)
- TTS router registered
- Ready for production use

---

### Frontend Components

#### 1. **VoiceSelector Component** (`aura-ui/src/components/VoiceSelector.jsx`)
- **Beautiful UI** with gradient styling
- **Voice Grid** displaying all 6 personalities
- **Settings Panel** includes:
  - Enable/Disable toggle
  - Auto-play toggle
  - Playback speed slider
  - Volume slider
  - Voice selection grid

#### 2. **AudioPlayer Component** (`aura-ui/src/components/AudioPlayer.jsx`)
- **Features**:
  - Play/Pause controls
  - Progress bar with seek
  - Time display
  - Replay button
  - Voice type indicator
  - Auto-play support
  - Customizable playback speed & volume

#### 3. **Updated ChatInterface** (`aura-ui/src/pages/ChatInterface.jsx`)
- **Integrated VoiceSelector** in chat header
- **AudioPlayer** automatically appears with AI responses
- Audio data handling from API
- Seamless voice playback experience

#### 4. **API Service** (`aura-ui/src/services/api.js`)
- New TTS endpoints:
  - `getAvailableVoices()`
  - `getTTSPreferences()`
  - `updateTTSPreferences()`
  - `setDefaultVoice()`
  - `convertTextToSpeech()`

#### 5. **Styling** (CSS files)
- `VoiceSelector.css` - 400+ lines
- `AudioPlayer.css` - 200+ lines
- Responsive design
- Dark mode support
- Smooth animations

---

## 📦 Required Python Packages

Add these to your backend requirements:

```bash
pip install pyttsx3 gtts
```

---

## 🎯 How It Works

### User Flow

1. **User opens chat interface** → Voice selector appears in header
2. **User clicks voice selector** → Panel opens with 6 voice options
3. **User selects a voice** (e.g., Emma) → Preference saved to database
4. **User sends message** → AI generates response
5. **Backend automatically generates audio** using selected voice
6. **Audio sent with response** as base64 data
7. **Frontend displays AudioPlayer** below AI message
8. **Audio auto-plays** (if enabled) or user clicks play

### Technical Flow

```
User Message 
    ↓
Backend /api/chat/conversations/{id}/messages
    ↓
Generate AI Response (with MCP context)
    ↓
Fetch User TTS Preferences
    ↓
Generate Audio (TTSService.text_to_speech)
    ↓
Cache Audio File (24hr)
    ↓
Encode as Base64
    ↓
Return Response + Audio Data
    ↓
Frontend Receives Response
    ↓
AudioPlayer Component Decodes Base64
    ↓
Creates Audio Blob & Plays
```

---

## 🎨 Voice Profiles

| Voice | Icon | Gender | Description | Speed (WPM) |
|-------|------|--------|-------------|-------------|
| David | 👨‍💼 | Male | Professional, confident | 175 |
| Sara | 👩‍⚕️ | Female | Warm, caring (default) | 165 |
| Emma | 👩‍🦰 | Female | Young, friendly | 180 |
| James | 👨‍🏫 | Male | Deep, authoritative | 160 |
| Olivia | 🧘‍♀️ | Female | Calm, soothing | 155 |
| Noah | 👨‍💻 | Male | Energetic, clear | 185 |

---

## 🚀 Testing Instructions

### 1. Install Dependencies

```powershell
cd backend
pip install pyttsx3 gtts
```

### 2. Start Backend

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

### 3. Start Frontend

```powershell
cd aura-ui
npm run dev
```

### 4. Test Voice System

1. Login to AURA
2. Navigate to chat interface
3. **Click voice selector button** (top right, purple gradient)
4. **Select a voice** from the 6 options
5. **Send a message**: "Hello, AURA!"
6. **Watch for**:
   - AI response appears
   - AudioPlayer appears below message
   - Audio auto-plays (purple play button)
   - Voice indicator shows selected voice

### 5. Test Voice Settings

- Toggle "Enable Voice Responses"
- Toggle "Auto-Play Responses"
- Adjust playback speed (0.5x - 2.0x)
- Adjust volume (0% - 100%)
- Try different voices

---

## 🔊 API Examples

### Get Available Voices

```bash
curl -X GET http://localhost:8000/api/tts/voices \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "voices": {
    "david": {
      "name": "David",
      "gender": "male",
      "description": "Professional, confident male voice",
      "rate": 175
    },
    "sara": { ... },
    ...
  },
  "default": "sara"
}
```

### Get User Preferences

```bash
curl -X GET http://localhost:8000/api/tts/preferences \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "preferences": {
    "enabled": true,
    "voice_type": "sara",
    "auto_play": true,
    "playback_speed": 1.0,
    "volume": 0.9
  }
}
```

### Update Preferences

```bash
curl -X PUT http://localhost:8000/api/tts/preferences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "voice_type": "emma",
    "auto_play": false,
    "playback_speed": 1.2
  }'
```

### Set Default Voice

```bash
curl -X POST http://localhost:8000/api/tts/set-voice/james \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📁 File Summary

### Backend Files (5 files, ~800 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/services/tts_service.py` | ~280 | Core TTS engine with 6 voices |
| `backend/app/models/user_preferences.py` | ~50 | User preferences model |
| `backend/app/routers/tts_router.py` | ~230 | TTS API endpoints |
| `backend/app/routers/chat.py` | ~30 (added) | TTS integration in chat |
| `backend/app/main.py` | ~2 (added) | Router registration |

### Frontend Files (5 files, ~900 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `aura-ui/src/components/VoiceSelector.jsx` | ~220 | Voice selection UI |
| `aura-ui/src/components/VoiceSelector.css` | ~400 | Voice selector styling |
| `aura-ui/src/components/AudioPlayer.jsx` | ~140 | Audio playback component |
| `aura-ui/src/components/AudioPlayer.css` | ~200 | Audio player styling |
| `aura-ui/src/services/api.js` | ~40 (added) | TTS API functions |
| `aura-ui/src/pages/ChatInterface.jsx` | ~15 (modified) | TTS integration |

**Total: 10 files, ~1,700 lines of code**

---

## 🎯 Key Features

### ✅ Implemented

- ✅ **6 different voice personalities**
- ✅ **Voice selection UI with descriptions**
- ✅ **User preference storage** (MongoDB)
- ✅ **Auto-play toggle**
- ✅ **Playback speed control** (0.5x - 2.0x)
- ✅ **Volume control** (0-100%)
- ✅ **Audio caching** (24 hours)
- ✅ **Base64 audio encoding**
- ✅ **Responsive design**
- ✅ **Dark mode support**
- ✅ **Works in both patient & doctor interfaces**
- ✅ **Automatic audio generation** for all AI responses
- ✅ **Play/Pause/Replay controls**
- ✅ **Progress bar with seek**
- ✅ **Voice indicator on audio player**

---

## 🔧 Configuration

### Voice Customization

Edit `backend/app/services/tts_service.py` to customize voices:

```python
VOICE_PROFILES = {
    "david": {
        "name": "David",
        "gender": "male",
        "description": "Professional, confident male voice",
        "rate": 175,  # Words per minute
        "volume": 0.9,
        "pitch": 1.0
    },
    # Add more voices...
}
```

### Cache Settings

```python
self.cache_duration = timedelta(hours=24)  # Adjust cache duration
```

---

## 🐛 Troubleshooting

### Audio Not Playing

1. **Check TTS packages installed**:
   ```bash
   pip list | grep -E "pyttsx3|gtts"
   ```

2. **Check browser console** for errors

3. **Verify audio data** in network tab:
   ```json
   {
     "audio": {
       "data": "base64_string_here",
       "voice_type": "sara",
       "format": "mp3"
     }
   }
   ```

### Voice Not Changing

1. **Check preferences saved**:
   ```bash
   curl http://localhost:8000/api/tts/preferences \
     -H "Authorization: Bearer TOKEN"
   ```

2. **Verify MongoDB** user_preferences collection

3. **Clear audio cache**:
   ```bash
   curl -X DELETE http://localhost:8000/api/tts/cache \
     -H "Authorization: Bearer TOKEN"
   ```

### Performance Issues

1. **Audio caching** should prevent regeneration
2. **Check cache directory**: `backend/audio_cache/`
3. **Adjust cache duration** if needed
4. **Monitor audio file sizes** (should be 20-50KB per response)

---

## 🚀 Next Steps (Optional Enhancements)

1. **Speech-to-Text** (STT) for voice input
2. **Real-time voice streaming** instead of pre-generation
3. **Custom voice training** using AI voice cloning
4. **Multilingual TTS** for different languages
5. **Emotion detection** and adaptive voice tone
6. **Voice analytics** (most popular voices, usage stats)
7. **Admin dashboard** for voice management

---

## 🎉 Summary

You now have a **fully functional, production-ready Text-to-Speech system** that:

- ✅ **Works everywhere** (patient chat, doctor chat, all AI responses)
- ✅ **6 voice options** with unique personalities
- ✅ **Full user control** (enable/disable, speed, volume)
- ✅ **Beautiful UI** with gradient styling and animations
- ✅ **High performance** with 24-hour audio caching
- ✅ **Responsive design** for mobile and desktop
- ✅ **Dark mode support**
- ✅ **MongoDB integration** for preference storage
- ✅ **RESTful API** with 6 endpoints
- ✅ **Auto-play** support
- ✅ **Play/pause/replay** controls

**Every AI message now speaks!** 🎙️🔊

---

## 📝 Files Created

### Backend
1. ✅ `backend/app/services/tts_service.py`
2. ✅ `backend/app/models/user_preferences.py`
3. ✅ `backend/app/routers/tts_router.py`
4. ✅ Modified: `backend/app/routers/chat.py`
5. ✅ Modified: `backend/app/main.py`

### Frontend
6. ✅ `aura-ui/src/components/VoiceSelector.jsx`
7. ✅ `aura-ui/src/components/VoiceSelector.css`
8. ✅ `aura-ui/src/components/AudioPlayer.jsx`
9. ✅ `aura-ui/src/components/AudioPlayer.css`
10. ✅ Modified: `aura-ui/src/services/api.js`
11. ✅ Modified: `aura-ui/src/pages/ChatInterface.jsx`

### Documentation
12. ✅ `TTS_IMPLEMENTATION_GUIDE.md` (this file)

---

**Ready to give AURA a voice!** 🎤✨
