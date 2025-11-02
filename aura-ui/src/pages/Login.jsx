import { useState, useEffect, useRef } from 'react';
import { Heart, Mail, Lock, User, Stethoscope } from 'lucide-react';
import './Login.css';
import { login as loginApi } from '../services/api';

function Login({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('patient');
  const [specialty, setSpecialty] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [videoLoaded, setVideoLoaded] = useState(false);
  const videoRef = useRef(null);

  const specialties = [
    'CARDIOLOGY', 'NEUROLOGY', 'ORTHOPEDICS', 'PEDIATRICS', 'DERMATOLOGY',
    'PSYCHIATRY', 'ONCOLOGY', 'GASTROENTEROLOGY', 'ENDOCRINOLOGY', 'PULMONOLOGY',
    'NEPHROLOGY', 'RHEUMATOLOGY', 'OPHTHALMOLOGY', 'OTOLARYNGOLOGY', 'UROLOGY',
    'GYNECOLOGY', 'OBSTETRICS', 'ANESTHESIOLOGY', 'RADIOLOGY', 'PATHOLOGY',
    'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'GENERAL_SURGERY', 'OTHER'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await loginApi(email, password);
      localStorage.setItem('aura_token', response.access_token);
      onLogin(response.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Quick login buttons for demo - now use real API
  const quickLogin = async (demoEmail) => {
    setError('');
    setLoading(true);

    try {
      const password = demoEmail.includes('doctor') ? 'doctor123' : 'patient123';
      const response = await loginApi(demoEmail, password);
      localStorage.setItem('aura_token', response.access_token);
      onLogin(response.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  // Infinite Universe Animation Effect
  useEffect(() => {
    const canvas = videoRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;
    
    // Set canvas size to window size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create stars with depth for parallax effect
    const stars = Array.from({ length: 800 }, () => ({
      x: Math.random() * canvas.width - canvas.width / 2,
      y: Math.random() * canvas.height - canvas.height / 2,
      z: Math.random() * 1000,
      size: Math.random() * 2,
      color: `hsl(${200 + Math.random() * 100}, ${50 + Math.random() * 50}%, ${60 + Math.random() * 40}%)`
    }));

    // Create nebula particles for depth
    const nebulae = Array.from({ length: 50 }, () => ({
      x: Math.random() * canvas.width - canvas.width / 2,
      y: Math.random() * canvas.height - canvas.height / 2,
      z: Math.random() * 800,
      size: Math.random() * 100 + 50,
      color: `hsla(${240 + Math.random() * 60}, 70%, 50%, ${Math.random() * 0.1})`
    }));

    let speed = 1.2;
    
    const animate = () => {
      // Clear with trail effect for motion blur
      ctx.fillStyle = 'rgba(10, 10, 20, 0.15)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // Animate nebulae
      nebulae.forEach(nebula => {
        nebula.z -= speed * 0.3;
        if (nebula.z <= 0) {
          nebula.z = 800;
          nebula.x = Math.random() * canvas.width - canvas.width / 2;
          nebula.y = Math.random() * canvas.height - canvas.height / 2;
        }

        const scale = 1000 / (1000 - nebula.z);
        const x = centerX + nebula.x * scale;
        const y = centerY + nebula.y * scale;
        const size = nebula.size * scale;

        const gradient = ctx.createRadialGradient(x, y, 0, x, y, size);
        gradient.addColorStop(0, nebula.color);
        gradient.addColorStop(1, 'transparent');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      });

      // Animate stars (traveling through space)
      stars.forEach(star => {
        star.z -= speed;
        
        // Reset star when it passes the camera
        if (star.z <= 0) {
          star.z = 1000;
          star.x = Math.random() * canvas.width - canvas.width / 2;
          star.y = Math.random() * canvas.height - canvas.height / 2;
        }

        // 3D projection
        const scale = 1000 / (1000 - star.z);
        const x = centerX + star.x * scale;
        const y = centerY + star.y * scale;
        const size = star.size * scale;
        const opacity = Math.min(1, scale * 0.5);

        // Draw star with glow
        ctx.shadowBlur = 10 * scale;
        ctx.shadowColor = star.color;
        ctx.fillStyle = star.color;
        ctx.globalAlpha = opacity;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw motion trail for speed effect
        if (scale > 1.5) {
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(centerX + star.x * (scale - 0.3), centerY + star.y * (scale - 0.3));
          ctx.strokeStyle = star.color;
          ctx.globalAlpha = opacity * 0.3;
          ctx.lineWidth = size * 0.5;
          ctx.stroke();
        }
      });

      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
      
      animationFrameId = requestAnimationFrame(animate);
    };

    setVideoLoaded(true);
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  return (
    <div className="login-container">
      {/* Infinite Universe Canvas Background */}
      <canvas 
        ref={videoRef}
        className="universe-canvas"
        style={{
          opacity: videoLoaded ? 1 : 0
        }}
      />

      <div className="login-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      <div className="login-content fade-in">
        <div className="login-header">
          <div className="logo-container">
            <Heart className="logo-heart" size={40} fill="currentColor" />
            <h1>AURA</h1>
          </div>
          <p className="tagline">Your AI Healthcare Companion</p>
        </div>

        <div className="glass-card login-card">
          <div className="card-tabs">
            <button 
              className={`tab ${isLogin ? 'active' : ''}`}
              onClick={() => setIsLogin(true)}
            >
              Sign In
            </button>
            <button 
              className={`tab ${!isLogin ? 'active' : ''}`}
              onClick={() => setIsLogin(false)}
            >
              Sign Up
            </button>
          </div>

          {error && (
            <div className="error-message slide-in">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="input-group">
                <label>Full Name</label>
                <div className="input-wrapper">
                  <User size={20} />
                  <input
                    type="text"
                    placeholder="Enter your full name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required={!isLogin}
                  />
                </div>
              </div>
            )}

            <div className="input-group">
              <label>Email Address</label>
              <div className="input-wrapper">
                <Mail size={20} />
                <input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="input-group">
              <label>Password</label>
              <div className="input-wrapper">
                <Lock size={20} />
                <input
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            {!isLogin && (
              <>
                <div className="input-group">
                  <label>I am a</label>
                  <div className="role-selector">
                    <button
                      type="button"
                      className={`role-btn ${role === 'patient' ? 'active' : ''}`}
                      onClick={() => setRole('patient')}
                    >
                      <User size={24} />
                      Patient
                    </button>
                    <button
                      type="button"
                      className={`role-btn ${role === 'doctor' ? 'active' : ''}`}
                      onClick={() => setRole('doctor')}
                    >
                      <Stethoscope size={24} />
                      Doctor
                    </button>
                  </div>
                </div>

                <div className="input-group">
                  <label>Medical Specialty</label>
                  <div className="input-wrapper">
                    <Stethoscope size={20} />
                    <select
                      value={specialty}
                      onChange={(e) => setSpecialty(e.target.value)}
                      required={!isLogin}
                      className="specialty-select"
                    >
                      <option value="">Select your specialty...</option>
                      {specialties.map(spec => (
                        <option key={spec} value={spec}>
                          {spec.replace(/_/g, ' ')}
                        </option>
                      ))}
                    </select>
                  </div>
                  <small className="help-text">
                    {role === 'doctor' 
                      ? 'Select your area of medical practice' 
                      : 'Select your medical condition or specialty area'}
                  </small>
                </div>
              </>
            )}

            <button 
              type="submit" 
              className="btn btn-primary btn-full"
              disabled={loading}
            >
              {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="divider">
            <span>Quick Demo Access</span>
          </div>

          <div className="demo-buttons">
            <button 
              className="btn btn-secondary"
              onClick={() => quickLogin('patient@aura.health', 'patient123')}
              disabled={loading}
            >
              <User size={18} />
              Demo Patient
            </button>
            <button 
              className="btn btn-secondary"
              onClick={() => quickLogin('doctor@aura.health', 'doctor123')}
              disabled={loading}
            >
              <Stethoscope size={18} />
              Demo Doctor
            </button>
          </div>
        </div>

        <p className="login-footer">
          By continuing, you agree to AURA's Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
}

export default Login;
