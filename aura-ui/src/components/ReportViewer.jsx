import { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  FileText, Download, Eye, Clock, CheckCircle, AlertCircle,
  RefreshCw, Filter, Search, Calendar, User, FileCheck, Sparkles
} from 'lucide-react';
import { 
  getReport,
  getPatientReports
} from '../services/api';
import ReportAnalyzer from './ReportAnalyzer';
import { useDebounce } from '../hooks/usePerformance';
import './ReportViewer.css';

const EXPORT_FORMATS = [
  { value: 'html', label: 'HTML Document', icon: '🌐', color: '#3b82f6' },
  { value: 'txt', label: 'Plain Text', icon: '📄', color: '#10b981' },
  { value: 'json', label: 'JSON Data', icon: '📊', color: '#f59e0b' },
  { value: 'pdf', label: 'PDF (Coming Soon)', icon: '📕', color: '#ef4444', disabled: true },
  { value: 'docx', label: 'Word Doc (Coming Soon)', icon: '📘', color: '#8b5cf6', disabled: true },
];

function ReportViewer() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);
  const [viewingReport, setViewingReport] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeModalTab, setActiveModalTab] = useState('details');

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const loadReports = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPatientReports();
      setReports(data || []);
    } catch (error) {
      console.error('Error loading reports:', error);
      setError('Failed to load reports');
      setReports([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleViewReport = useCallback(async (reportId) => {
    try {
      const report = await getReport(reportId);
      setSelectedReport(report);
      setViewingReport(true);
    } catch (error) {
      console.error('Error loading report:', error);
      setError('Failed to load report details');
    }
  }, []);

  const handleExportReport = async (reportId, format) => {
    if (format === 'pdf' || format === 'docx') {
      setError(`${format.toUpperCase()} export is coming soon! Please use HTML, TXT, or JSON formats.`);
      setTimeout(() => setError(null), 5000);
      return;
    }

    try {
      const token = localStorage.getItem('aura_token');
      const response = await fetch(
        `http://127.0.0.1:8000/api/reports/${reportId}/export?format=${format}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Get filename from Content-Disposition header or create default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `medical_report_${reportId}.${format}`;
      if (contentDisposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSuccess(`Report exported as ${format.toUpperCase()}!`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error('Error exporting report:', error);
      setError('Failed to export report');
      setTimeout(() => setError(null), 3000);
    }
  };

  // Debounced search term to prevent excessive filtering
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Memoize filtered reports to prevent unnecessary recalculations
  const filteredReports = useMemo(() => 
    reports.filter(report => {
      const matchesSearch = 
        report.report_id.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        (report.summary && report.summary.toLowerCase().includes(debouncedSearchTerm.toLowerCase()));
      
      const matchesStatus = 
        statusFilter === 'all' || 
        report.status.toLowerCase() === statusFilter.toLowerCase();
      
      return matchesSearch && matchesStatus;
    }),
    [reports, debouncedSearchTerm, statusFilter]
  );

  const formatDate = useCallback((dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, []);

  if (loading) {
    return (
      <div className="report-viewer-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading reports...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="report-viewer-container">
      {/* Header */}
      <div className="reports-header">
        <div className="header-title">
          <FileCheck size={28} color="var(--accent)" />
          <div>
            <h2>Medical Reports</h2>
            <p>AI-generated comprehensive medical reports with doctor review</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="reports-filters glass-card">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="filter-group">
          <Filter size={18} />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All Status</option>
            <option value="draft">Draft</option>
            <option value="finalized">Finalized</option>
          </select>
        </div>

        <button 
          className="btn btn-primary"
          onClick={loadReports}
          disabled={loading}
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="message-banner error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {success && (
        <div className="message-banner success-banner">
          <CheckCircle size={20} />
          <span>{success}</span>
          <button onClick={() => setSuccess(null)}>×</button>
        </div>
      )}

      {/* Reports List */}
      {filteredReports.length === 0 ? (
        <div className="empty-state glass-card">
          <FileText size={64} color="var(--text-muted)" />
          <h3>No Reports Found</h3>
          <p>
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your filters' 
              : 'Reports will appear here after consultations'}
          </p>
        </div>
      ) : (
        <div className="reports-grid">
          {filteredReports.map((report) => (
            <div key={report.report_id} className="report-card glass-card">
              <div className="report-card-header">
                <div className="report-icon">
                  <FileText size={24} />
                </div>
                <div className="report-meta">
                  <h4>Medical Report</h4>
                  <p className="report-id">ID: {report.report_id.substring(7, 20)}...</p>
                </div>
                <div className={`status-badge ${report.status.toLowerCase()}`}>
                  {report.status === 'FINALIZED' ? (
                    <CheckCircle size={16} />
                  ) : (
                    <Clock size={16} />
                  )}
                  {report.status}
                </div>
              </div>

              <div className="report-card-body">
                <div className="report-info-row">
                  <Calendar size={16} />
                  <span>{formatDate(report.generated_at)}</span>
                </div>
                
                {report.metadata && (
                  <div className="report-stats">
                    <div className="stat">
                      <span className="stat-value">{report.metadata.total_messages || 0}</span>
                      <span className="stat-label">Messages</span>
                    </div>
                    <div className="stat">
                      <span className="stat-value">{report.metadata.total_documents || 0}</span>
                      <span className="stat-label">Documents</span>
                    </div>
                    <div className="stat">
                      <span className="stat-value">{report.metadata.ai_confidence || 'N/A'}</span>
                      <span className="stat-label">Confidence</span>
                    </div>
                  </div>
                )}

                <div className="report-summary">
                  <p>{report.summary}</p>
                </div>
              </div>

              <div className="report-card-actions">
                <button 
                  className="btn btn-secondary"
                  onClick={() => handleViewReport(report.report_id)}
                >
                  <Eye size={18} />
                  View Report
                </button>
                
                <div className="export-dropdown">
                  <button className="btn btn-primary">
                    <Download size={18} />
                    Export
                  </button>
                  <div className="export-menu">
                    {EXPORT_FORMATS.map((format) => (
                      <button
                        key={format.value}
                        className="export-option"
                        onClick={() => handleExportReport(report.report_id, format.value)}
                        disabled={format.disabled}
                        style={{ opacity: format.disabled ? 0.5 : 1 }}
                      >
                        <span className="format-icon">{format.icon}</span>
                        <span>{format.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Report Detail Modal */}
      {viewingReport && selectedReport && (
        <div className="modal-overlay" onClick={() => setViewingReport(false)}>
          <div className="modal-content report-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Medical Report</h3>
              <button onClick={() => setViewingReport(false)}>×</button>
            </div>

            {/* Modal Tabs */}
            <div className="modal-tabs">
              <button 
                className={`modal-tab ${activeModalTab === 'details' ? 'active' : ''}`}
                onClick={() => setActiveModalTab('details')}
              >
                <FileText size={18} />
                Report Details
              </button>
              <button 
                className={`modal-tab ${activeModalTab === 'ai' ? 'active' : ''}`}
                onClick={() => setActiveModalTab('ai')}
              >
                <Sparkles size={18} />
                Ask AI Assistant
              </button>
            </div>

            {/* Details Tab */}
            {activeModalTab === 'details' && (
              <>
                <div className="modal-body">
                  <div className="report-detail-header">
                    <div className="detail-row">
                      <strong>Report ID:</strong>
                      <span>{selectedReport.report_id}</span>
                    </div>
                    <div className="detail-row">
                      <strong>Status:</strong>
                      <span className={`status-badge ${selectedReport.status.toLowerCase()}`}>
                        {selectedReport.status}
                      </span>
                    </div>
                    <div className="detail-row">
                      <strong>Generated:</strong>
                      <span>{formatDate(selectedReport.generated_at)}</span>
                    </div>
                    <div className="detail-row">
                      <strong>Type:</strong>
                      <span>{selectedReport.report_type}</span>
                    </div>
                  </div>

                  <div className="report-section">
                    <h4>Summary</h4>
                    <div className="section-content">
                      {selectedReport.summary}
                    </div>
                  </div>

                  <div className="report-section">
                    <h4>Detailed Findings</h4>
                    <div className="section-content findings">
                      {selectedReport.findings}
                    </div>
                  </div>

                  {selectedReport.doctor_notes && (
                    <div className="report-section">
                      <h4>Doctor's Notes</h4>
                      <div className="section-content">
                        {selectedReport.doctor_notes}
                      </div>
                    </div>
                  )}

                  {selectedReport.metadata && (
                    <div className="report-section">
                      <h4>Report Metadata</h4>
                      <div className="metadata-grid">
                        <div className="metadata-item">
                          <strong>Messages Analyzed:</strong>
                          <span>{selectedReport.metadata.total_messages || 'N/A'}</span>
                        </div>
                        <div className="metadata-item">
                          <strong>Documents Reviewed:</strong>
                          <span>{selectedReport.metadata.total_documents || 'N/A'}</span>
                        </div>
                        <div className="metadata-item">
                          <strong>AI Confidence:</strong>
                          <span>{selectedReport.metadata.ai_confidence || 'N/A'}</span>
                        </div>
                        <div className="metadata-item">
                          <strong>Generated By:</strong>
                          <span>{selectedReport.metadata.generated_by || 'System'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="modal-footer">
                  <div className="export-buttons">
                    {EXPORT_FORMATS.map((format) => (
                      <button
                        key={format.value}
                        className="btn btn-secondary"
                        onClick={() => handleExportReport(selectedReport.report_id, format.value)}
                        disabled={format.disabled}
                        style={{ 
                          opacity: format.disabled ? 0.5 : 1,
                          cursor: format.disabled ? 'not-allowed' : 'pointer'
                        }}
                      >
                        <span>{format.icon}</span>
                        {format.label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* AI Assistant Tab */}
            {activeModalTab === 'ai' && (
              <div className="modal-body ai-assistant-body">
                <ReportAnalyzer reportId={selectedReport.report_id} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ReportViewer;
