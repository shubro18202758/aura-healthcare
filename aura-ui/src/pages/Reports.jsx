import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Heart, User } from 'lucide-react';
import ReportViewer from '../components/ReportViewer';
import './Reports.css';

function Reports({ user }) {
  const navigate = useNavigate();

  return (
    <div className="reports-container">
      <nav className="dashboard-nav fade-in">
        <div className="nav-brand">
          <Heart size={32} fill="currentColor" />
          <h2>AURA</h2>
        </div>
        <div className="nav-user">
          <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
            <ArrowLeft size={18} />
            Dashboard
          </button>
          <div className="user-info">
            <div className="user-avatar">
              <User size={20} />
            </div>
            <span>{user.email}</span>
          </div>
        </div>
      </nav>

      <div className="reports-content">
        <ReportViewer />
      </div>
    </div>
  );
}

export default Reports;
