import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, RotateCcw } from 'lucide-react';
import './AudioPlayer.css';

function AudioPlayer({ audioData, voiceType, autoPlay = false, playbackSpeed = 1.0, volume = 0.9 }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (audioData && audioRef.current) {
      // Convert base64 to blob and create URL
      try {
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: 'audio/mpeg' });
        const url = URL.createObjectURL(blob);
        
        audioRef.current.src = url;
        audioRef.current.playbackRate = playbackSpeed;
        audioRef.current.volume = volume;

        if (autoPlay) {
          setTimeout(() => {
            playAudio();
          }, 100);
        }

        // Cleanup
        return () => {
          URL.revokeObjectURL(url);
        };
      } catch (err) {
        console.error('Error loading audio:', err);
        setError('Failed to load audio');
      }
    }
  }, [audioData, autoPlay, playbackSpeed, volume]);

  const playAudio = async () => {
    try {
      await audioRef.current.play();
      setIsPlaying(true);
      setError(null);
    } catch (err) {
      console.error('Error playing audio:', err);
      setError('Failed to play audio');
      setIsPlaying(false);
    }
  };

  const pauseAudio = () => {
    audioRef.current.pause();
    setIsPlaying(false);
  };

  const togglePlayPause = () => {
    if (isPlaying) {
      pauseAudio();
    } else {
      playAudio();
    }
  };

  const handleTimeUpdate = () => {
    setCurrentTime(audioRef.current.currentTime);
  };

  const handleLoadedMetadata = () => {
    setDuration(audioRef.current.duration);
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleReplay = () => {
    audioRef.current.currentTime = 0;
    playAudio();
  };

  const handleSeek = (e) => {
    const seekTime = (e.target.value / 100) * duration;
    audioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!audioData) return null;

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
      />
      
      <div className="audio-player-content">
        <button
          className="audio-control-btn"
          onClick={togglePlayPause}
          disabled={error}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
        </button>

        <div className="audio-progress-container">
          <input
            type="range"
            min="0"
            max="100"
            value={duration ? (currentTime / duration) * 100 : 0}
            onChange={handleSeek}
            className="audio-progress-bar"
            disabled={error}
          />
          <div className="audio-time">
            <span>{formatTime(currentTime)}</span>
            <span>/</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        <button
          className="audio-control-btn"
          onClick={handleReplay}
          disabled={error}
          title="Replay"
        >
          <RotateCcw size={16} />
        </button>

        <div className="audio-voice-indicator">
          <Volume2 size={14} />
          <span>{voiceType}</span>
        </div>
      </div>

      {error && (
        <div className="audio-error">{error}</div>
      )}
    </div>
  );
}

export default AudioPlayer;
