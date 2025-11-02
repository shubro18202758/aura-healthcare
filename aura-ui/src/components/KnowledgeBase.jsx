import { useState, useEffect } from 'react';
import { 
  BookOpen, Plus, Edit2, Trash2, Save, X, Search, Tag, FileText
} from 'lucide-react';
import axios from 'axios';
import './KnowledgeBase.css';

function KnowledgeBase() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [formData, setFormData] = useState({
    topic: '',
    questions: [''],
    context: '',
    keywords: ['']
  });

  const API_BASE = 'http://127.0.0.1:8000';

  useEffect(() => {
    loadEntries();
    // eslint-disable-next-line
  }, []);

  const loadEntries = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('aura_token');
      const response = await axios.get(`${API_BASE}/api/knowledge-base/entries`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEntries(response.data.entries || []);
    } catch (err) {
      console.error('Error loading entries:', err);
      setError('Failed to load knowledge base entries');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayInput = (field, index, value) => {
    setFormData(prev => {
      const newArray = [...prev[field]];
      newArray[index] = value;
      return { ...prev, [field]: newArray };
    });
  };

  const addArrayField = (field) => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const removeArrayField = (field, index) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('aura_token');
      const cleanedData = {
        topic: formData.topic.trim(),
        questions: formData.questions.filter(q => q.trim()).map(q => q.trim()),
        context: formData.context.trim(),
        keywords: formData.keywords.filter(k => k.trim()).map(k => k.trim())
      };

      if (editingId) {
        await axios.put(
          `${API_BASE}/api/knowledge-base/entries/${editingId}`,
          cleanedData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSuccess('Entry updated successfully!');
      } else {
        await axios.post(
          `${API_BASE}/api/knowledge-base/entries`,
          cleanedData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSuccess('Entry created successfully!');
      }

      resetForm();
      loadEntries();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save entry');
    }
  };

  const handleEdit = (entry) => {
    setFormData({
      topic: entry.topic,
      questions: entry.questions.length > 0 ? entry.questions : [''],
      context: entry.context,
      keywords: entry.keywords.length > 0 ? entry.keywords : ['']
    });
    setEditingId(entry.entry_id);
    setShowForm(true);
  };

  const handleDelete = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this entry?')) return;

    try {
      const token = localStorage.getItem('aura_token');
      await axios.delete(`${API_BASE}/api/knowledge-base/entries/${entryId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Entry deleted successfully!');
      loadEntries();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete entry');
    }
  };

  const resetForm = () => {
    setFormData({
      topic: '',
      questions: [''],
      context: '',
      keywords: ['']
    });
    setEditingId(null);
    setShowForm(false);
  };

  const filteredEntries = entries.filter(entry =>
    entry.topic.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entry.context.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entry.keywords.some(k => k.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="kb-loading">
        <div className="loading-spinner"></div>
        <p>Loading knowledge base...</p>
      </div>
    );
  }

  return (
    <div className="knowledge-base-container">
      <div className="kb-header">
        <div className="kb-title">
          <BookOpen size={32} />
          <div>
            <h2>Knowledge Base</h2>
            <p>Manage specialty-specific medical topics and questions</p>
          </div>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowForm(true)}
        >
          <Plus size={20} />
          Add Entry
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      {showForm && (
        <div className="kb-form-overlay">
          <div className="kb-form-modal glass-card">
            <div className="modal-header">
              <h3>{editingId ? 'Edit Entry' : 'New Entry'}</h3>
              <button className="btn-icon" onClick={resetForm}>
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Topic *</label>
                <input
                  type="text"
                  placeholder="e.g., Heart Disease Prevention"
                  value={formData.topic}
                  onChange={(e) => handleInputChange('topic', e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Questions *</label>
                {formData.questions.map((question, index) => (
                  <div key={index} className="array-input">
                    <input
                      type="text"
                      placeholder={`Question ${index + 1}`}
                      value={question}
                      onChange={(e) => handleArrayInput('questions', index, e.target.value)}
                      required={index === 0}
                    />
                    {formData.questions.length > 1 && (
                      <button
                        type="button"
                        className="btn-icon btn-danger"
                        onClick={() => removeArrayField('questions', index)}
                      >
                        <X size={18} />
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => addArrayField('questions')}
                >
                  <Plus size={16} />
                  Add Question
                </button>
              </div>

              <div className="form-group">
                <label>Context *</label>
                <textarea
                  rows={4}
                  placeholder="Provide detailed context about this topic..."
                  value={formData.context}
                  onChange={(e) => handleInputChange('context', e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Keywords</label>
                {formData.keywords.map((keyword, index) => (
                  <div key={index} className="array-input">
                    <input
                      type="text"
                      placeholder={`Keyword ${index + 1}`}
                      value={keyword}
                      onChange={(e) => handleArrayInput('keywords', index, e.target.value)}
                    />
                    {formData.keywords.length > 1 && (
                      <button
                        type="button"
                        className="btn-icon btn-danger"
                        onClick={() => removeArrayField('keywords', index)}
                      >
                        <X size={18} />
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => addArrayField('keywords')}
                >
                  <Plus size={16} />
                  Add Keyword
                </button>
              </div>

              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={resetForm}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  <Save size={18} />
                  {editingId ? 'Update Entry' : 'Create Entry'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="kb-search">
        <Search size={20} />
        <input
          type="text"
          placeholder="Search entries by topic, context, or keywords..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="kb-entries">
        {filteredEntries.length === 0 ? (
          <div className="empty-state">
            <BookOpen size={48} />
            <h3>No entries found</h3>
            <p>
              {searchTerm 
                ? 'Try adjusting your search terms' 
                : 'Create your first knowledge base entry to get started'}
            </p>
          </div>
        ) : (
          <div className="entries-grid">
            {filteredEntries.map((entry) => (
              <div key={entry.entry_id} className="entry-card glass-card">
                <div className="entry-header">
                  <h3>{entry.topic}</h3>
                  <div className="entry-actions">
                    <button
                      className="btn-icon"
                      onClick={() => handleEdit(entry)}
                      title="Edit"
                    >
                      <Edit2 size={18} />
                    </button>
                    <button
                      className="btn-icon btn-danger"
                      onClick={() => handleDelete(entry.entry_id)}
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                <div className="entry-specialty">
                  <Tag size={14} />
                  <span>{entry.specialty.replace(/_/g, ' ')}</span>
                </div>

                <div className="entry-questions">
                  <strong>Questions ({entry.questions.length}):</strong>
                  <ul>
                    {entry.questions.slice(0, 3).map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                    {entry.questions.length > 3 && (
                      <li className="more">+{entry.questions.length - 3} more</li>
                    )}
                  </ul>
                </div>

                <div className="entry-context">
                  <FileText size={14} />
                  <p>{entry.context.substring(0, 150)}{entry.context.length > 150 ? '...' : ''}</p>
                </div>

                {entry.keywords.length > 0 && (
                  <div className="entry-keywords">
                    {entry.keywords.slice(0, 5).map((keyword, i) => (
                      <span key={i} className="keyword-tag">{keyword}</span>
                    ))}
                    {entry.keywords.length > 5 && (
                      <span className="keyword-tag more">+{entry.keywords.length - 5}</span>
                    )}
                  </div>
                )}

                <div className="entry-footer">
                  <small>Updated {new Date(entry.updated_at).toLocaleDateString()}</small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default KnowledgeBase;
