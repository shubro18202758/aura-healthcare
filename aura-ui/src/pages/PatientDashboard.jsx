import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MessageCircle, FileText, Calendar, Activity, Heart, 
  LogOut, Plus, Clock, TrendingUp, User
} from 'lucide-react';
import { getPatientProfile, getPatientConversations, createConversation, getDashboardStats } from '../services/api';
import './PatientDashboard.css';

function PatientDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalConsultations: 0,
    activeSession: 0,
    healthScore: 0,
  });

  useEffect(() => {
    loadDashboardData();
    // Reduced polling frequency to 2 minutes for better performance
    const interval = setInterval(loadDashboardData, 120000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [profileData, conversationsData, statsData] = await Promise.all([
        getPatientProfile().catch(() => ({ full_name: user.email })),
        getPatientConversations().catch(() => []),
        getDashboardStats().catch(() => ({
          total_consultations: 0,
          active_sessions: 0,
          health_score: 100
        })),
      ]);

      setProfile(profileData);
      setConversations(conversationsData);
      
      // Use real-time stats from backend
      setStats({
        totalConsultations: statsData.total_consultations || 0,
        activeSession: statsData.active_sessions || 0,
        healthScore: statsData.health_score || 100,
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewConsultation = async () => {
    try {
      const response = await createConversation(
        user.user_id,
        'en',
        'Hello, I would like to consult with you.'
      );
      
      if (response.conversation) {
        navigate(`/chat/${response.conversation.conversation_id}`);
      }
    } catch (error) {
      console.error('Error creating consultation:', error);
      alert('Failed to start consultation. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Animated Background */}
      <div className="dashboard-bg">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
        <div className="gradient-orb orb-4"></div>
      </div>

      <nav className="dashboard-nav fade-in">
        <div className="nav-brand">
          <div className="logo-wrapper">
            <Heart size={32} fill="currentColor" />
          </div>
          <h2>AURA</h2>
        </div>
        <div className="nav-user">
          <div className="user-info">
            <div className="user-avatar">
              <User size={20} />
            </div>
            <div>
              <p className="user-name">{profile?.full_name || user.email}</p>
              <p className="user-role">
                Patient
                {profile?.specialty && ` • ${profile.specialty.replace(/_/g, ' ')}`}
              </p>
            </div>
          </div>
          <button className="btn btn-secondary" onClick={onLogout}>
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="dashboard-header slide-in">
          <div className="header-content">
            <div className="header-badge">
              <Activity size={16} strokeWidth={2.5} />
              <span>AI-Powered Healthcare</span>
            </div>
            <h1 className="gradient-text">Welcome back, {profile?.full_name?.split(' ')[0] || user.email.split('@')[0]}! 👋</h1>
            <p className="header-subtitle">Your comprehensive health dashboard powered by advanced AI diagnostics</p>
          </div>
          <button className="btn btn-primary btn-glow" onClick={handleNewConsultation}>
            <Plus size={20} />
            New Consultation
          </button>
        </div>

        <div className="stats-grid fade-in">
          <div className="stat-card modern-card">
            <div className="stat-background stat-bg-1"></div>
            <div className="stat-icon-wrapper">
              <div className="stat-icon stat-icon-blue">
                <MessageCircle size={28} strokeWidth={2.5} />
              </div>
            </div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.totalConsultations}</h3>
              <p className="stat-label">Total Consultations</p>
            </div>
            <div className="stat-decoration"></div>
          </div>

          <div className="stat-card modern-card">
            <div className="stat-background stat-bg-2"></div>
            <div className="stat-icon-wrapper">
              <div className="stat-icon stat-icon-green">
                <FileText size={28} strokeWidth={2.5} />
              </div>
            </div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.activeSession}</h3>
              <p className="stat-label">Active Sessions</p>
            </div>
            <div className="stat-decoration"></div>
          </div>

          <div className="stat-card modern-card">
            <div className="stat-background stat-bg-3"></div>
            <div className="stat-icon-wrapper">
              <div className="stat-icon stat-icon-pink">
                <TrendingUp size={28} strokeWidth={2.5} />
              </div>
            </div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.healthScore}%</h3>
              <p className="stat-label">Health Score</p>
              <div className="health-progress">
                <div 
                  className="health-progress-bar" 
                  style={{ width: `${stats.healthScore}%` }}
                ></div>
              </div>
            </div>
            <div className="stat-decoration"></div>
          </div>
        </div>

        <div className="dashboard-grid">
          <div className="conversations-section modern-card slide-in">
            <div className="section-header">
              <h2 className="section-title">Recent Consultations</h2>
              <button className="btn btn-secondary btn-glow-secondary" onClick={() => navigate('/chat')}>
                View All
              </button>
            </div>

            {conversations.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <MessageCircle size={56} strokeWidth={2} />
                </div>
                <h3>No consultations yet</h3>
                <p>Start your first AI-powered health consultation with our advanced medical assistant</p>
                <button className="btn btn-primary btn-glow" onClick={handleNewConsultation}>
                  <Plus size={20} />
                  Start Consultation
                </button>
              </div>
            ) : (
              <div className="conversations-list">
                {conversations.slice(0, 5).map((conv) => (
                  <div 
                    key={conv.conversation_id} 
                    className="conversation-item"
                    onClick={() => navigate(`/chat/${conv.conversation_id}`)}
                  >
                    <div className="conversation-icon">
                      <Activity size={20} />
                    </div>
                    <div className="conversation-details">
                      <h4>Health Consultation</h4>
                      <p>
                        <Clock size={14} />
                        {new Date(conv.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className={`conversation-status status-${conv.status}`}>
                      {conv.status === 'active' ? 'Active' : 'Completed'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="quick-actions-section glass-card slide-in">
            <h2>Quick Actions</h2>
            <div className="quick-actions">
              <button 
                className="action-btn"
                onClick={handleNewConsultation}
              >
                <div className="action-icon" style={{ background: 'rgba(99, 102, 241, 0.2)' }}>
                  <MessageCircle size={24} color="var(--primary)" />
                </div>
                <h3>New Consultation</h3>
                <p>Talk to AI assistant</p>
              </button>

              <button 
                className="action-btn"
                onClick={() => navigate('/reports')}
              >
                <div className="action-icon" style={{ background: 'rgba(16, 185, 129, 0.2)' }}>
                  <FileText size={24} color="var(--success)" />
                </div>
                <h3>My Reports</h3>
                <p>View health reports</p>
              </button>

              <button className="action-btn">
                <div className="action-icon" style={{ background: 'rgba(245, 158, 11, 0.2)' }}>
                  <Calendar size={24} color="var(--warning)" />
                </div>
                <h3>Appointments</h3>
                <p>Schedule visit</p>
              </button>

              <button className="action-btn">
                <div className="action-icon" style={{ background: 'rgba(236, 72, 153, 0.2)' }}>
                  <Activity size={24} color="var(--accent)" />
                </div>
                <h3>Health Tracker</h3>
                <p>Monitor vitals</p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PatientDashboard;
