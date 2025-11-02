import { useState, useEffect } from 'react';
import { Volume2, VolumeX, Settings } from 'lucide-react';
import { getTTSPreferences, updateTTSPreferences, getAvailableVoices } from '../services/api';
import './VoiceSelector.css';

const VOICE_ICONS = {
  david: '👨‍💼',
  sara: '👩‍⚕️',
  emma: '👩‍🦰',
  james: '👨‍🏫',
  olivia: '🧘‍♀️',
  noah: '👨‍💻'
};

function VoiceSelector({ onVoiceChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [voices, setVoices] = useState({});
  const [preferences, setPreferences] = useState({
    enabled: true,
    voice_type: 'sara',
    auto_play: true,
    playback_speed: 1.0,
    volume: 0.9
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadVoicesAndPreferences();
  }, []);

  const loadVoicesAndPreferences = async () => {
    try {
      // Load available voices
      const voicesData = await getAvailableVoices();
      if (voicesData.voices) {
        setVoices(voicesData.voices);
      }

      // Load user preferences
      const prefsData = await getTTSPreferences();
      if (prefsData.preferences) {
        setPreferences(prefsData.preferences);
      }
    } catch (error) {
      console.error('Error loading voice data:', error);
    }
  };

  const handleVoiceSelect = async (voiceType) => {
    setLoading(true);
    try {
      await updateTTSPreferences({ voice_type: voiceType });
      setPreferences({ ...preferences, voice_type: voiceType });
      
      if (onVoiceChange) {
        onVoiceChange(voiceType);
      }
      
      setIsOpen(false);
    } catch (error) {
      console.error('Error updating voice:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleEnabled = async () => {
    const newEnabled = !preferences.enabled;
    setLoading(true);
    try {
      await updateTTSPreferences({ enabled: newEnabled });
      setPreferences({ ...preferences, enabled: newEnabled });
    } catch (error) {
      console.error('Error toggling voice:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleAutoPlay = async () => {
    const newAutoPlay = !preferences.auto_play;
    setLoading(true);
    try {
      await updateTTSPreferences({ auto_play: newAutoPlay });
      setPreferences({ ...preferences, auto_play: newAutoPlay });
    } catch (error) {
      console.error('Error toggling auto-play:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = async (speed) => {
    setLoading(true);
    try {
      await updateTTSPreferences({ playback_speed: speed });
      setPreferences({ ...preferences, playback_speed: speed });
    } catch (error) {
      console.error('Error updating speed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVolumeChange = async (volume) => {
    setLoading(true);
    try {
      await updateTTSPreferences({ volume });
      setPreferences({ ...preferences, volume });
    } catch (error) {
      console.error('Error updating volume:', error);
    } finally {
      setLoading(false);
    }
  };

  const currentVoice = voices[preferences.voice_type];

  return (
    <div className="voice-selector-container">
      <button
        className={`voice-selector-trigger ${preferences.enabled ? 'enabled' : 'disabled'}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Voice Assistant Settings"
      >
        {preferences.enabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
        <span className="voice-label">
          {VOICE_ICONS[preferences.voice_type]} {currentVoice?.name || preferences.voice_type}
        </span>
        <Settings size={16} className="settings-icon" />
      </button>

      {isOpen && (
        <div className="voice-selector-panel">
          <div className="voice-panel-header">
            <h3>🎙️ Voice Assistant Settings</h3>
            <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
          </div>

          {/* Enable/Disable Toggle */}
          <div className="voice-setting-item">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={preferences.enabled}
                onChange={toggleEnabled}
                disabled={loading}
              />
              <span>Enable Voice Responses</span>
            </label>
          </div>

          {/* Auto-Play Toggle */}
          <div className="voice-setting-item">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={preferences.auto_play}
                onChange={toggleAutoPlay}
                disabled={loading || !preferences.enabled}
              />
              <span>Auto-Play Responses</span>
            </label>
          </div>

          {/* Voice Selection */}
          <div className="voice-selection-section">
            <h4>Select Voice Personality</h4>
            <div className="voices-grid">
              {Object.entries(voices).map(([key, voice]) => (
                <button
                  key={key}
                  className={`voice-option ${preferences.voice_type === key ? 'selected' : ''}`}
                  onClick={() => handleVoiceSelect(key)}
                  disabled={loading || !preferences.enabled}
                >
                  <span className="voice-icon">{VOICE_ICONS[key]}</span>
                  <span className="voice-name">{voice.name}</span>
                  <span className="voice-gender">{voice.gender}</span>
                  <p className="voice-description">{voice.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Playback Speed */}
          <div className="voice-setting-item">
            <label>
              <span>Playback Speed: {preferences.playback_speed}x</span>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={preferences.playback_speed}
                onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
                disabled={loading || !preferences.enabled}
                className="slider"
              />
              <div className="range-labels">
                <span>Slower</span>
                <span>Normal</span>
                <span>Faster</span>
              </div>
            </label>
          </div>

          {/* Volume */}
          <div className="voice-setting-item">
            <label>
              <span>Volume: {Math.round(preferences.volume * 100)}%</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={preferences.volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                disabled={loading || !preferences.enabled}
                className="slider"
              />
              <div className="range-labels">
                <span>Mute</span>
                <span>Loud</span>
              </div>
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

export default VoiceSelector;
