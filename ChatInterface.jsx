import React, { useState, useEffect, useRef } from 'react';
import { Send, Upload, Mic, MicOff, FileText, AlertCircle } from 'lucide-react';
import './ChatInterface.css';

const ChatInterface = ({ conversationId, patientId, onConversationComplete }) => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationStatus, setConversationStatus] = useState('connecting');
  const [progress, setProgress] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  
  const messagesEndRef = useRef(null);
  const websocketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    initializeWebSocket();
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeWebSocket = () => {
    const wsUrl = `ws://localhost:8000/api/chat/ws/${conversationId}`;
    websocketRef.current = new WebSocket(wsUrl);

    websocketRef.current.onopen = () => {
      console.log('WebSocket connected');
      setConversationStatus('connected');
      addSystemMessage('Welcome! I\'m AURA, your AI healthcare assistant. I\'ll be asking you some questions to help your doctor understand your condition better.');
    };

    websocketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    websocketRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setConversationStatus('disconnected');
    };

    websocketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConversationStatus('error');
    };
  };

  const handleWebSocketMessage = (data) => {
    const { type, content, progress: msgProgress, summary } = data;

    switch (type) {
      case 'question':
        addAIMessage(content, 'question');
        if (msgProgress) setProgress(msgProgress);
        break;
      
      case 'answer':
        addAIMessage(content, 'answer');
        break;
      
      case 'summary':
        addAIMessage(content, 'completion');
        if (summary && onConversationComplete) {
          onConversationComplete(summary);
        }
        break;
      
      case 'error':
        addSystemMessage(content, 'error');
        break;
      
      default:
        console.log('Unknown message type:', type);
    }
    
    setIsLoading(false);
  };

  const addMessage = (content, sender, messageType = 'text') => {
    const newMessage = {
      id: Date.now(),
      content,
      sender,
      messageType,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addAIMessage = (content, messageType = 'text') => {
    addMessage(content, 'ai', messageType);
  };

  const addUserMessage = (content, messageType = 'text') => {
    addMessage(content, 'user', messageType);
  };

  const addSystemMessage = (content, messageType = 'system') => {
    addMessage(content, 'system', messageType);
  };

  const sendMessage = () => {
    if (!currentMessage.trim() || !websocketRef.current) return;

    const message = currentMessage.trim();
    addUserMessage(message);
    
    setIsLoading(true);
    websocketRef.current.send(JSON.stringify({
      message,
      type: 'response'
    }));
    
    setCurrentMessage('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      const audioChunks = [];
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await processAudioMessage(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      addSystemMessage('Unable to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudioMessage = async (audioBlob) => {
    // For demo purposes, show a placeholder
    // In real implementation, convert speech to text using Web Speech API or backend service
    addUserMessage('[Audio message recorded - processing...]', 'audio');
    
    // Simulate processing
    setTimeout(() => {
      const sampleResponses = [
        "I have been experiencing headaches for the past few days",
        "The pain is moderate, around 5 out of 10",
        "It's mostly in the front of my head and gets worse in the evening"
      ];
      const response = sampleResponses[Math.floor(Math.random() * sampleResponses.length)];
      
      // Replace the placeholder with processed text
      setMessages(prev => prev.map(msg => 
        msg.content === '[Audio message recorded - processing...]' 
          ? { ...msg, content: response, messageType: 'text' }
          : msg
      ));
      
      // Send the processed text
      if (websocketRef.current) {
        websocketRef.current.send(JSON.stringify({
          message: response,
          type: 'response'
        }));
      }
    }, 2000);
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    files.forEach(processFile);
  };

  const processFile = async (file) => {
    const fileInfo = {
      id: Date.now(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading'
    };
    
    setUploadedFiles(prev => [...prev, fileInfo]);
    addUserMessage(`📄 Uploaded: ${file.name}`, 'file');
    
    try {
      // Read file content
      const content = await readFileContent(file);
      
      // Send to backend for processing
      const response = await fetch(`/api/chat/conversation/${conversationId}/upload-document`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          file_content: content,
          file_type: file.type
        })
      });
      
      const result = await response.json();
      
      if (response.ok) {
        // Update file status
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileInfo.id 
            ? { ...f, status: 'processed', extractedInfo: result }
            : f
        ));
        
        addSystemMessage(`✅ Successfully processed ${file.name}. Extracted ${result.extracted_entities?.length || 0} medical entities.`);
      } else {
        throw new Error(result.detail || 'Upload failed');
      }
    } catch (error) {
      console.error('File processing error:', error);
      setUploadedFiles(prev => prev.map(f => 
        f.id === fileInfo.id ? { ...f, status: 'error' } : f
      ));
      addSystemMessage(`❌ Failed to process ${file.name}: ${error.message}`, 'error');
    }
  };

  const readFileContent = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour12: true,
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getMessageIcon = (messageType) => {
    switch (messageType) {
      case 'question': return '❓';
      case 'answer': return '💡';
      case 'completion': return '✅';
      case 'error': return '❌';
      case 'audio': return '🎵';
      case 'file': return '📄';
      default: return '';
    }
  };

  if (conversationStatus === 'error') {
    return (
      <div className="chat-interface error-state">
        <div className="error-message">
          <AlertCircle size={48} />
          <h3>Connection Error</h3>
          <p>Unable to connect to the healthcare assistant. Please try again.</p>
          <button onClick={initializeWebSocket} className="retry-button">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      {/* Header */}
      <div className="chat-header">
        <div className="header-info">
          <div className="assistant-avatar">🤖</div>
          <div>
            <h3>AURA Healthcare Assistant</h3>
            <span className={`status ${conversationStatus}`}>
              {conversationStatus === 'connected' ? '🟢 Connected' : '🟡 Connecting...'}
            </span>
          </div>
        </div>
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress * 100}%` }}
            />
          </div>
          <span className="progress-text">{Math.round(progress * 100)}% Complete</span>
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-content">
              <div className="message-header">
                <span className="message-icon">
                  {getMessageIcon(message.messageType)}
                </span>
                <span className="message-type">
                  {message.sender === 'ai' ? 'AURA' : 
                   message.sender === 'user' ? 'You' : 'System'}
                </span>
                <span className="message-time">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <div className="message-text">
                {message.content}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message ai loading">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="uploaded-files">
          <h4>📁 Uploaded Documents</h4>
          {uploadedFiles.map((file) => (
            <div key={file.id} className={`file-item ${file.status}`}>
              <FileText size={16} />
              <span className="file-name">{file.name}</span>
              <span className={`file-status ${file.status}`}>
                {file.status === 'uploading' && '⏳'}
                {file.status === 'processed' && '✅'}
                {file.status === 'error' && '❌'}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="input-area">
        <div className="input-container">
          <textarea
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your response..."
            rows={1}
            disabled={conversationStatus !== 'connected'}
          />
          
          <div className="input-actions">
            <button
              className="action-button file-upload"
              onClick={() => fileInputRef.current?.click()}
              title="Upload medical documents"
            >
              <Upload size={20} />
            </button>
            
            <button
              className={`action-button voice-input ${isRecording ? 'recording' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              title={isRecording ? 'Stop recording' : 'Voice input'}
            >
              {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            
            <button
              className="action-button send-message"
              onClick={sendMessage}
              disabled={!currentMessage.trim() || conversationStatus !== 'connected'}
              title="Send message"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />
      </div>

      {/* Connection Status */}
      {conversationStatus === 'connecting' && (
        <div className="connection-overlay">
          <div className="connection-message">
            <div className="spinner"></div>
            <p>Connecting to AURA Healthcare Assistant...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;