import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, ArrowLeft, Mic, Paperclip, Bot, User as UserIcon, Heart, FileText, MessageSquare } from 'lucide-react';
import { getConversation, sendMessage, autoGenerateReport } from '../services/api';
import MedicalDocuments from '../components/MedicalDocuments';
import VoiceSelector from '../components/VoiceSelector';
import AudioPlayer from '../components/AudioPlayer';
import './ChatInterface.css';

function ChatInterface({ user }) {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'documents'
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (conversationId) {
      loadConversation();
    }
    // eslint-disable-next-line
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const loadConversation = useCallback(async () => {
    try {
      const data = await getConversation(conversationId);
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  }, [conversationId]);

  const handleSendMessage = useCallback(async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      content: inputMessage,
      sender_role: 'patient',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setIsTyping(true);

    try {
      const response = await sendMessage(conversationId, inputMessage);
      
      // Create AI message with audio if available
      const aiMessage = {
        content: response.ai_response.content,
        sender_role: 'ai',
        timestamp: response.ai_response.timestamp,
      };
      
      // Add audio data if TTS is enabled and audio is provided
      if (response.audio) {
        aiMessage.audio = response.audio;
      }
      
      setMessages(prev => [...prev, aiMessage]);

      // Trigger auto-generation of report in the background (no need to wait)
      // This will silently attempt to generate a report if criteria are met
      autoGenerateReport(conversationId).catch(() => {
        // Silently fail - report generation is optional background task
      });
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        content: 'Sorry, I encountered an error. Please try again.',
        sender_role: 'ai',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  }, [inputMessage, loading, conversationId]);

  // Memoize formatted messages to prevent unnecessary re-renders
  const formattedMessages = useMemo(() => 
    messages.map((msg, index) => ({
      ...msg,
      key: `${msg.timestamp}-${index}`,
      formattedTime: new Date(msg.timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    })),
    [messages]
  );

  return (
    <div className="chat-container">
      <div className="chat-header fade-in">
        <div className="chat-header-left">
          <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
            <ArrowLeft size={20} />
          </button>
          <div className="chat-title">
            <div className="chat-avatar">
              <Bot size={24} />
            </div>
            <div>
              <h3>AURA AI Assistant</h3>
              <p className="status-online">
                <span className="status-dot"></span>
                Online
              </p>
            </div>
          </div>
        </div>
        <div className="chat-header-right">
          <VoiceSelector onVoiceChange={(voice) => console.log('Voice changed to:', voice)} />
          <div className="user-info">
            <span>{user.email}</span>
            <div className="user-avatar-small">
              <UserIcon size={16} />
            </div>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="chat-tabs">
        <button 
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={18} />
          <span>Chat</span>
        </button>
        <button 
          className={`tab-btn ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          <FileText size={18} />
          <span>Medical Documents</span>
        </button>
      </div>

      {activeTab === 'chat' ? (
        <>
          <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome fade-in">
            <div className="welcome-icon">
              <Heart size={64} color="var(--accent)" fill="var(--accent)" />
            </div>
            <h2>Welcome to AURA! 👋</h2>
            <p>I'm your AI healthcare assistant. I'm here to help you with:</p>
            <div className="welcome-features">
              <div className="feature">💬 Symptom assessment</div>
              <div className="feature">📋 Health information</div>
              <div className="feature">🩺 Medical guidance</div>
              <div className="feature">📊 Health tracking</div>
            </div>
            <p className="welcome-prompt">How can I help you today?</p>
          </div>
        ) : (
          <div className="messages-list">
            {formattedMessages.map((msg) => (
              <div 
                key={msg.key}
                className={`message ${msg.sender_role === 'ai' ? 'message-ai' : 'message-user'} slide-in`}
              >
                <div className="message-avatar">
                  {msg.sender_role === 'ai' ? (
                    <Bot size={20} />
                  ) : (
                    <UserIcon size={20} />
                  )}
                </div>
                <div className="message-content">
                  <div className="message-bubble">
                    {msg.content}
                  </div>
                  {msg.audio && (
                    <AudioPlayer 
                      audioData={msg.audio.data}
                      voiceType={msg.audio.voice_type}
                      autoPlay={true}
                    />
                  )}
                  <span className="message-time">
                    {msg.formattedTime}
                  </span>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="message message-ai slide-in">
                <div className="message-avatar">
                  <Bot size={20} />
                </div>
                <div className="message-content">
                  <div className="message-bubble typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

          <form className="chat-input-container" onSubmit={handleSendMessage}>
            <div className="chat-input-wrapper glass-card">
              <button type="button" className="input-action-btn" title="Attach file">
                <Paperclip size={20} />
              </button>
              <input
                type="text"
                placeholder="Type your message..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={loading}
                className="chat-input"
              />
              <button type="button" className="input-action-btn" title="Voice input">
                <Mic size={20} />
              </button>
              <button 
                type="submit" 
                className="btn btn-primary send-btn"
                disabled={loading || !inputMessage.trim()}
              >
                <Send size={20} />
              </button>
            </div>
          </form>
        </>
      ) : (
        <div className="documents-tab-content">
          <MedicalDocuments conversationId={conversationId} />
        </div>
      )}
    </div>
  );
}

export default ChatInterface;
