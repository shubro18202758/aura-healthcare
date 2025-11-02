import { useState } from 'react';
import { Send, Sparkles, FileText, Loader, MessageSquare, BookOpen, GitCompare } from 'lucide-react';
import { analyzeReport, summarizeReport } from '../services/api';
import './ReportAnalyzer.css';

const SUMMARY_TYPES = [
  { value: 'brief', label: '📝 Brief Summary', description: '3-4 sentence overview' },
  { value: 'detailed', label: '📄 Detailed Summary', description: 'Comprehensive analysis' },
  { value: 'key_findings', label: '🔍 Key Findings', description: 'Top findings in bullets' },
  { value: 'urgent', label: '⚠️ Urgent Items', description: 'Critical findings only' },
  { value: 'differential', label: '🩺 Differential Diagnoses', description: 'Possible conditions' },
  { value: 'recommendations', label: '💊 Recommendations', description: 'Tests and follow-ups' },
];

const QUICK_QUERIES = [
  "What are the main symptoms reported?",
  "Are there any urgent findings?",
  "What tests were recommended?",
  "Summarize the key clinical points",
  "What medications were discussed?",
  "Are there any red flags?",
];

function ReportAnalyzer({ reportId }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('query'); // query, summary
  const [selectedSummaryType, setSelectedSummaryType] = useState('brief');
  const [conversation, setConversation] = useState([]);
  const [error, setError] = useState(null);

  const handleQuery = async (queryText = query) => {
    if (!queryText.trim() || loading) return;

    const userMessage = {
      type: 'user',
      content: queryText,
      timestamp: new Date().toISOString()
    };

    setConversation(prev => [...prev, userMessage]);
    setQuery('');
    setLoading(true);
    setError(null);

    try {
      const response = await analyzeReport(reportId, queryText);
      
      const aiMessage = {
        type: 'ai',
        content: response.response,
        timestamp: response.timestamp
      };

      setConversation(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error('Error analyzing report:', err);
      setError(err.response?.data?.detail || 'Failed to analyze report');
      
      const errorMessage = {
        type: 'error',
        content: 'Sorry, I encountered an error analyzing the report.',
        timestamp: new Date().toISOString()
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSummary = async () => {
    setLoading(true);
    setError(null);
    
    const summaryRequest = {
      type: 'summary',
      content: `Generating ${selectedSummaryType} summary...`,
      timestamp: new Date().toISOString()
    };
    
    setConversation(prev => [...prev, summaryRequest]);

    try {
      const response = await summarizeReport(reportId, selectedSummaryType);
      
      const summaryMessage = {
        type: 'ai',
        content: response.summary,
        summaryType: selectedSummaryType,
        timestamp: response.timestamp
      };

      setConversation(prev => [...prev.slice(0, -1), summaryMessage]);
    } catch (err) {
      console.error('Error generating summary:', err);
      setError(err.response?.data?.detail || 'Failed to generate summary');
      setConversation(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuery = (quickQuery) => {
    setQuery(quickQuery);
    handleQuery(quickQuery);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  return (
    <div className="report-analyzer">
      <div className="analyzer-header">
        <div className="header-content">
          <Sparkles size={24} className="header-icon" />
          <div>
            <h3>AI Report Assistant</h3>
            <p>Ask questions or generate summaries about this medical report</p>
          </div>
        </div>
        
        <div className="analyzer-tabs">
          <button
            className={`tab-btn ${activeTab === 'query' ? 'active' : ''}`}
            onClick={() => setActiveTab('query')}
          >
            <MessageSquare size={16} />
            Ask Questions
          </button>
          <button
            className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            <BookOpen size={16} />
            Generate Summary
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {activeTab === 'query' && (
        <div className="query-section">
          {conversation.length === 0 && (
            <div className="empty-state">
              <Sparkles size={48} />
              <h4>Ask me anything about this report</h4>
              <p>I can help you understand symptoms, findings, recommendations, and more.</p>
              
              <div className="quick-queries">
                <p className="quick-queries-label">Quick questions:</p>
                {QUICK_QUERIES.map((q, idx) => (
                  <button
                    key={idx}
                    className="quick-query-btn"
                    onClick={() => handleQuickQuery(q)}
                    disabled={loading}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {conversation.length > 0 && (
            <div className="conversation">
              {conversation.map((msg, idx) => (
                <div key={idx} className={`message ${msg.type}`}>
                  <div className="message-icon">
                    {msg.type === 'user' ? '👨‍⚕️' : msg.type === 'error' ? '❌' : '🤖'}
                  </div>
                  <div className="message-content">
                    <div className="message-text">{msg.content}</div>
                    <div className="message-time">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="message ai">
                  <div className="message-icon">🤖</div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="query-input-container">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about this report..."
              disabled={loading}
              rows={2}
            />
            <button
              onClick={() => handleQuery()}
              disabled={!query.trim() || loading}
              className="send-btn"
            >
              {loading ? <Loader size={20} className="spin" /> : <Send size={20} />}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'summary' && (
        <div className="summary-section">
          <div className="summary-types">
            <h4>Select Summary Type</h4>
            <div className="summary-grid">
              {SUMMARY_TYPES.map((type) => (
                <button
                  key={type.value}
                  className={`summary-type-card ${selectedSummaryType === type.value ? 'selected' : ''}`}
                  onClick={() => setSelectedSummaryType(type.value)}
                >
                  <div className="summary-type-label">{type.label}</div>
                  <div className="summary-type-desc">{type.description}</div>
                </button>
              ))}
            </div>
            
            <button
              className="generate-summary-btn"
              onClick={handleSummary}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader size={20} className="spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  Generate Summary
                </>
              )}
            </button>
          </div>

          {conversation.filter(msg => msg.type === 'ai' || msg.type === 'summary').length > 0 && (
            <div className="summary-results">
              <h4>Generated Summaries</h4>
              {conversation.filter(msg => msg.type === 'ai' || msg.type === 'summary').map((msg, idx) => (
                <div key={idx} className="summary-result">
                  <div className="summary-result-header">
                    <FileText size={18} />
                    <span>
                      {SUMMARY_TYPES.find(t => t.value === msg.summaryType)?.label || 'Summary'}
                    </span>
                    <span className="summary-time">
                      {new Date(msg.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="summary-result-content">
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ReportAnalyzer;
