import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MessageCircle, FileText, Users, Activity, Heart, 
  LogOut, TrendingUp, User, Clock, BookOpen, FileCheck
} from 'lucide-react';
import { getDoctorProfile, getDoctorPatients, getDoctorStats } from '../services/api';
import KnowledgeBase from '../components/KnowledgeBase';
import ReportViewer from '../components/ReportViewer';
import './DoctorDashboard.css';

function DoctorDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({
    totalPatients: 0,
    activeConsultations: 0,
    reportsGenerated: 0,
    satisfactionRate: 100,
  });

  useEffect(() => {
    loadDashboardData();
    // Reduced polling frequency to 2 minutes for better performance
    // Only poll when dashboard tab is active
    const interval = activeTab === 'dashboard' 
      ? setInterval(loadDashboardData, 120000)
      : null;
    return () => {
      if (interval) clearInterval(interval);
    };
    // eslint-disable-next-line
  }, [activeTab]);

  const loadDashboardData = async () => {
    try {
      const [profileData, patientsData, statsData] = await Promise.all([
        getDoctorProfile().catch(() => ({ full_name: user.email })),
        getDoctorPatients().catch(() => []),
        getDoctorStats().catch(() => ({
          total_patients: 0,
          active_consultations: 0,
          reports_generated: 0,
          satisfaction_rate: 100
        })),
      ]);

      setProfile(profileData);
      setPatients(patientsData);
      
      // Use real-time stats from backend
      setStats({
        totalPatients: statsData.total_patients || 0,
        activeConsultations: statsData.active_consultations || 0,
        reportsGenerated: statsData.reports_generated || 0,
        satisfactionRate: statsData.satisfaction_rate || 100,
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
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
      <div className="doctor-dashboard-bg">
        <div className="doctor-gradient-orb doctor-orb-1"></div>
        <div className="doctor-gradient-orb doctor-orb-2"></div>
        <div className="doctor-gradient-orb doctor-orb-3"></div>
        <div className="doctor-gradient-orb doctor-orb-4"></div>
      </div>

      <nav className="dashboard-nav fade-in">
        <div className="nav-brand">
          <Heart size={32} fill="currentColor" />
          <h2>AURA</h2>
        </div>
        <div className="nav-user">
          <div className="user-info">
            <div className="user-avatar doctor-avatar">
              <User size={20} />
            </div>
            <div>
              <p className="user-name">Dr. {profile?.full_name || user.email}</p>
              <p className="user-role">Healthcare Provider</p>
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
          <div>
            <h1>Welcome, Dr. {profile?.full_name?.split(' ')[0] || 'Doctor'}! 👨‍⚕️</h1>
            <p>Here's your practice overview for today</p>
          </div>
        </div>

        <div className="dashboard-tabs">
          <button 
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={20} />
            Dashboard
          </button>
          <button 
            className={`tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <FileCheck size={20} />
            Medical Reports
          </button>
          <button 
            className={`tab-btn ${activeTab === 'knowledge' ? 'active' : ''}`}
            onClick={() => setActiveTab('knowledge')}
          >
            <BookOpen size={20} />
            Knowledge Base
          </button>
        </div>

        {activeTab === 'reports' ? (
          <ReportViewer />
        ) : activeTab === 'knowledge' ? (
          <KnowledgeBase user={user} />
        ) : (
          <>
            <div className="stats-grid fade-in">
              <div className="stat-card glass-card">
                <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.2)' }}>
                  <Users size={24} color="var(--primary)" />
                </div>
                <div className="stat-content">
                  <h3>{stats.totalPatients}</h3>
                  <p>Total Patients</p>
                </div>
              </div>

          <div className="stat-card glass-card">
            <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.2)' }}>
              <MessageCircle size={24} color="var(--success)" />
            </div>
            <div className="stat-content">
              <h3>{stats.activeConsultations}</h3>
              <p>Active Consultations</p>
            </div>
          </div>

          <div className="stat-card glass-card">
            <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.2)' }}>
              <FileText size={24} color="var(--warning)" />
            </div>
            <div className="stat-content">
              <h3>{stats.reportsGenerated}</h3>
              <p>Reports Generated</p>
            </div>
          </div>

          <div className="stat-card glass-card">
            <div className="stat-icon" style={{ background: 'rgba(236, 72, 153, 0.2)' }}>
              <TrendingUp size={24} color="var(--accent)" />
            </div>
            <div className="stat-content">
              <h3>{stats.satisfactionRate}%</h3>
              <p>Satisfaction Rate</p>
            </div>
          </div>
        </div>

        <div className="dashboard-grid">
          <div className="patients-section glass-card slide-in">
            <div className="section-header">
              <h2>Recent Patients</h2>
              <button className="btn btn-secondary">
                View All
              </button>
            </div>

            {patients.length === 0 ? (
              <div className="empty-state">
                <Users size={48} color="var(--text-muted)" />
                <h3>No patients yet</h3>
                <p>Patients will appear here as they start consultations</p>
              </div>
            ) : (
              <div className="patients-list">
                {patients.slice(0, 5).map((patient) => (
                  <div key={patient.id} className="patient-item">
                    <div className="patient-avatar">
                      <User size={20} />
                    </div>
                    <div className="patient-details">
                      <h4>{patient.full_name}</h4>
                      <p>
                        <Clock size={14} />
                        Last visit: {new Date(patient.last_visit).toLocaleDateString()}
                      </p>
                    </div>
                    <button 
                      className="btn btn-primary"
                      onClick={() => navigate(`/reports?patient=${patient.id}`)}
                    >
                      <FileText size={16} />
                      View Reports
                    </button>
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
                onClick={() => navigate('/reports')}
              >
                <div className="action-icon" style={{ background: 'rgba(99, 102, 241, 0.2)' }}>
                  <FileText size={24} color="var(--primary)" />
                </div>
                <h3>View Reports</h3>
                <p>Patient health reports</p>
              </button>

              <button className="action-btn">
                <div className="action-icon" style={{ background: 'rgba(16, 185, 129, 0.2)' }}>
                  <Activity size={24} color="var(--success)" />
                </div>
                <h3>AI Insights</h3>
                <p>Generated insights</p>
              </button>

              <button className="action-btn">
                <div className="action-icon" style={{ background: 'rgba(245, 158, 11, 0.2)' }}>
                  <Users size={24} color="var(--warning)" />
                </div>
                <h3>Patient List</h3>
                <p>Manage patients</p>
              </button>

              <button className="action-btn">
                <div className="action-icon" style={{ background: 'rgba(236, 72, 153, 0.2)' }}>
                  <MessageCircle size={24} color="var(--accent)" />
                </div>
                <h3>Consultations</h3>
                <p>Active sessions</p>
              </button>
            </div>
          </div>
        </div>
          </>
        )}
      </div>
    </div>
  );
}

export default DoctorDashboard;
