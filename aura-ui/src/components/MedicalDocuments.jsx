import { useState, useEffect } from 'react';
import { 
  Upload, FileText, X, File, Image, FileCheck, 
  Heart, Brain, Pill, TestTube, Stethoscope, FileX2,
  Download, Trash2, Plus, Check, AlertCircle
} from 'lucide-react';
import { 
  uploadMedicalDocument, 
  getMedicalDocuments, 
  deleteMedicalDocument,
  getDocumentSummary 
} from '../services/api';
import './MedicalDocuments.css';

const DOCUMENT_TYPES = [
  { value: 'lab_report', label: 'Lab Report', icon: TestTube, color: '#10b981' },
  { value: 'prescription', label: 'Prescription', icon: Pill, color: '#3b82f6' },
  { value: 'xray', label: 'X-Ray', icon: Brain, color: '#8b5cf6' },
  { value: 'mri', label: 'MRI Scan', icon: Brain, color: '#ec4899' },
  { value: 'ct_scan', label: 'CT Scan', icon: Brain, color: '#f59e0b' },
  { value: 'other', label: 'Other', icon: FileText, color: '#6b7280' },
];

const ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'txt', 'csv', 'xlsx', 'dcm'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

function MedicalDocuments({ conversationId }) {
  const [documents, setDocuments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  const [uploadForm, setUploadForm] = useState({
    file: null,
    documentType: 'lab_report',
    description: '',
    tags: [],
    tagInput: '',
  });

  useEffect(() => {
    if (conversationId) {
      loadDocuments();
      loadSummary();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await getMedicalDocuments(conversationId);
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error loading documents:', error);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const data = await getDocumentSummary(conversationId);
      setSummary(data);
    } catch (error) {
      console.error('Error loading summary:', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (file) => {
    setError(null);
    
    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError(`File size exceeds 10MB limit. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
      return;
    }
    
    // Validate file extension
    const extension = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError(`File type .${extension} is not allowed. Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return;
    }
    
    setUploadForm({ ...uploadForm, file });
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleAddTag = () => {
    if (uploadForm.tagInput.trim() && !uploadForm.tags.includes(uploadForm.tagInput.trim())) {
      setUploadForm({
        ...uploadForm,
        tags: [...uploadForm.tags, uploadForm.tagInput.trim()],
        tagInput: '',
      });
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setUploadForm({
      ...uploadForm,
      tags: uploadForm.tags.filter(tag => tag !== tagToRemove),
    });
  };

  const handleUpload = async () => {
    if (!uploadForm.file) {
      setError('Please select a file');
      return;
    }
    
    try {
      setUploading(true);
      setUploadProgress(0);
      setError(null);
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);
      
      await uploadMedicalDocument(
        conversationId,
        uploadForm.file,
        uploadForm.documentType,
        uploadForm.description,
        uploadForm.tags
      );
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setSuccess('Document uploaded successfully!');
      setTimeout(() => {
        setShowUploadModal(false);
        setUploadForm({
          file: null,
          documentType: 'lab_report',
          description: '',
          tags: [],
          tagInput: '',
        });
        setUploadProgress(0);
        setSuccess(null);
        loadDocuments();
        loadSummary();
      }, 1500);
      
    } catch (error) {
      console.error('Error uploading document:', error);
      setError(error.response?.data?.detail || 'Failed to upload document');
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }
    
    try {
      await deleteMedicalDocument(documentId);
      setSuccess('Document deleted successfully');
      setTimeout(() => setSuccess(null), 3000);
      loadDocuments();
      loadSummary();
    } catch (error) {
      console.error('Error deleting document:', error);
      setError('Failed to delete document');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDocumentIcon = (docType) => {
    const type = DOCUMENT_TYPES.find(t => t.value === docType);
    return type ? type.icon : FileText;
  };

  const getDocumentColor = (docType) => {
    const type = DOCUMENT_TYPES.find(t => t.value === docType);
    return type ? type.color : '#6b7280';
  };

  return (
    <div className="medical-documents-container">
      {/* Header */}
      <div className="documents-header">
        <div className="header-title">
          <FileCheck size={24} color="var(--accent)" />
          <div>
            <h3>Medical Documents</h3>
            <p>Upload and manage your medical records, test results, and prescriptions</p>
          </div>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowUploadModal(true)}
        >
          <Plus size={20} />
          Upload Document
        </button>
      </div>

      {/* Summary */}
      {summary && summary.total_documents > 0 && (
        <div className="documents-summary glass-card">
          <h4>Document Summary</h4>
          <div className="summary-stats">
            <div className="summary-stat">
              <FileText size={20} color="var(--accent)" />
              <div>
                <span className="stat-value">{summary.total_documents}</span>
                <span className="stat-label">Total Documents</span>
              </div>
            </div>
            {Object.entries(summary.by_type || {}).map(([type, count]) => {
              const docType = DOCUMENT_TYPES.find(t => t.value === type);
              const Icon = docType?.icon || FileText;
              return (
                <div key={type} className="summary-stat">
                  <Icon size={20} color={docType?.color} />
                  <div>
                    <span className="stat-value">{count}</span>
                    <span className="stat-label">{docType?.label || type}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error/Success Messages */}
      {error && (
        <div className="message-banner error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
          <button onClick={() => setError(null)}><X size={16} /></button>
        </div>
      )}
      
      {success && (
        <div className="message-banner success-banner">
          <Check size={20} />
          <span>{success}</span>
          <button onClick={() => setSuccess(null)}><X size={16} /></button>
        </div>
      )}

      {/* Documents List */}
      <div className="documents-list">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <FileX2 size={64} color="var(--text-muted)" />
            <h3>No Documents Yet</h3>
            <p>Upload your medical documents to help provide better care</p>
            <button 
              className="btn btn-primary"
              onClick={() => setShowUploadModal(true)}
            >
              <Plus size={20} />
              Upload Your First Document
            </button>
          </div>
        ) : (
          <div className="documents-grid">
            {documents.map((doc) => {
              const Icon = getDocumentIcon(doc.document_type);
              const color = getDocumentColor(doc.document_type);
              
              return (
                <div key={doc.document_id} className="document-card glass-card">
                  <div className="document-icon" style={{ backgroundColor: `${color}20` }}>
                    <Icon size={32} color={color} />
                  </div>
                  <div className="document-info">
                    <h4>{doc.file_name}</h4>
                    <p className="document-type">
                      {DOCUMENT_TYPES.find(t => t.value === doc.document_type)?.label || doc.document_type}
                    </p>
                    {doc.description && (
                      <p className="document-description">{doc.description}</p>
                    )}
                    <div className="document-meta">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{formatDate(doc.uploaded_at)}</span>
                    </div>
                    {doc.tags && doc.tags.length > 0 && (
                      <div className="document-tags">
                        {doc.tags.map((tag, idx) => (
                          <span key={idx} className="tag">{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="document-actions">
                    <button 
                      className="btn-icon"
                      onClick={() => window.open(`http://127.0.0.1:8000${doc.file_path}`, '_blank')}
                      title="View Document"
                    >
                      <Download size={18} />
                    </button>
                    <button 
                      className="btn-icon btn-danger"
                      onClick={() => handleDelete(doc.document_id)}
                      title="Delete Document"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upload Medical Document</h3>
              <button onClick={() => setShowUploadModal(false)}>
                <X size={24} />
              </button>
            </div>
            
            <div className="modal-body">
              {/* File Drop Zone */}
              <div 
                className={`file-drop-zone ${dragActive ? 'drag-active' : ''} ${uploadForm.file ? 'file-selected' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input').click()}
              >
                <input
                  id="file-input"
                  type="file"
                  style={{ display: 'none' }}
                  onChange={handleFileInputChange}
                  accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
                />
                {uploadForm.file ? (
                  <div className="file-selected-info">
                    <FileCheck size={48} color="var(--success)" />
                    <p className="file-name">{uploadForm.file.name}</p>
                    <p className="file-size">{formatFileSize(uploadForm.file.size)}</p>
                    <button 
                      className="btn btn-secondary"
                      onClick={(e) => {
                        e.stopPropagation();
                        setUploadForm({ ...uploadForm, file: null });
                      }}
                    >
                      Change File
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload size={48} color="var(--text-muted)" />
                    <p>Drag and drop your file here or click to browse</p>
                    <p className="file-requirements">
                      Supported: {ALLOWED_EXTENSIONS.join(', ')} (Max 10MB)
                    </p>
                  </>
                )}
              </div>

              {/* Document Type */}
              <div className="form-group">
                <label>Document Type *</label>
                <div className="document-type-grid">
                  {DOCUMENT_TYPES.map((type) => {
                    const Icon = type.icon;
                    return (
                      <button
                        key={type.value}
                        className={`type-option ${uploadForm.documentType === type.value ? 'selected' : ''}`}
                        style={{ 
                          borderColor: uploadForm.documentType === type.value ? type.color : 'transparent',
                          backgroundColor: uploadForm.documentType === type.value ? `${type.color}10` : 'transparent'
                        }}
                        onClick={() => setUploadForm({ ...uploadForm, documentType: type.value })}
                      >
                        <Icon size={24} color={type.color} />
                        <span>{type.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Description */}
              <div className="form-group">
                <label>Description (Optional)</label>
                <textarea
                  placeholder="Add any relevant details about this document..."
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  rows={3}
                />
              </div>

              {/* Tags */}
              <div className="form-group">
                <label>Tags (Optional)</label>
                <div className="tags-input">
                  <input
                    type="text"
                    placeholder="Add tags (e.g., urgent, follow-up)"
                    value={uploadForm.tagInput}
                    onChange={(e) => setUploadForm({ ...uploadForm, tagInput: e.target.value })}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  />
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={handleAddTag}
                  >
                    Add
                  </button>
                </div>
                {uploadForm.tags.length > 0 && (
                  <div className="tags-list">
                    {uploadForm.tags.map((tag, idx) => (
                      <span key={idx} className="tag">
                        {tag}
                        <button onClick={() => handleRemoveTag(tag)}>
                          <X size={14} />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Upload Progress */}
              {uploading && (
                <div className="upload-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p>{uploadProgress}% uploaded</p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowUploadModal(false)}
                disabled={uploading}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={!uploadForm.file || uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Document'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MedicalDocuments;
