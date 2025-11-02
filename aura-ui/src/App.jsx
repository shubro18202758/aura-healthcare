import { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import './App.css';

// Lazy load heavy components for better initial load time
const PatientDashboard = lazy(() => import('./pages/PatientDashboard'));
const DoctorDashboard = lazy(() => import('./pages/DoctorDashboard'));
const ChatInterface = lazy(() => import('./pages/ChatInterface'));
const Reports = lazy(() => import('./pages/Reports'));

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('aura_token');
    const userData = localStorage.getItem('aura_user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('aura_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('aura_token');
    localStorage.removeItem('aura_user');
  };

  // Loading fallback component
  const LoadingFallback = () => (
    <div className="loading-screen">
      <div className="loading-spinner"></div>
      <h2>AURA Healthcare</h2>
    </div>
  );

  if (loading) {
    return <LoadingFallback />;
  }

  return (
    <Router>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route 
            path="/" 
            element={!user ? <LandingPage /> : <Navigate to="/dashboard" />} 
          />
          <Route 
            path="/login" 
            element={!user ? <Login onLogin={handleLogin} /> : <Navigate to="/dashboard" />} 
          />
          <Route 
            path="/dashboard" 
            element={
              user ? (
                user.role === 'patient' ? (
                  <PatientDashboard user={user} onLogout={handleLogout} />
                ) : (
                  <DoctorDashboard user={user} onLogout={handleLogout} />
                )
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/chat/:conversationId?" 
            element={user ? <ChatInterface user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/reports" 
            element={user ? <Reports user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} 
          />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;
