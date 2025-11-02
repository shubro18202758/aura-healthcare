import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Heart, Brain, Activity, Shield, Sparkles, ArrowRight, 
  CheckCircle, Users, MessageSquare, FileText, Zap,
  ChevronDown, Star, TrendingUp, Lock, Clock
} from 'lucide-react';
import './LandingPage.css';

function LandingPage() {
  const navigate = useNavigate();
  const [scrollProgress, setScrollProgress] = useState(0);
  const [activeSection, setActiveSection] = useState(0);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const heroRef = useRef(null);
  const featuresRef = useRef(null);
  const howItWorksRef = useRef(null);
  const statsRef = useRef(null);
  const ctaRef = useRef(null);
  const videoRef = useRef(null);

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
      color: `hsla(${240 + Math.random() * 60}, 80%, 60%, ${Math.random() * 0.2 + 0.1})`
    }));

    let speed = 2.5;
    
    const animate = () => {
      // Clear with trail effect for motion blur
      ctx.fillStyle = 'rgba(10, 10, 20, 0.1)';
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
        const opacity = Math.min(1, scale * 0.7);

        // Draw star with glow
        ctx.shadowBlur = 15 * scale;
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
          ctx.globalAlpha = opacity * 0.5;
          ctx.lineWidth = size * 0.8;
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

  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (window.scrollY / totalHeight) * 100;
      setScrollProgress(progress);

      // Determine active section based on scroll position
      const scrollPos = window.scrollY + window.innerHeight / 2;
      
      if (heroRef.current && scrollPos < featuresRef.current?.offsetTop) {
        setActiveSection(0);
      } else if (featuresRef.current && scrollPos < howItWorksRef.current?.offsetTop) {
        setActiveSection(1);
      } else if (howItWorksRef.current && scrollPos < statsRef.current?.offsetTop) {
        setActiveSection(2);
      } else if (statsRef.current && scrollPos < ctaRef.current?.offsetTop) {
        setActiveSection(3);
      } else {
        setActiveSection(4);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (ref) => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const features = [
    {
      icon: <MessageSquare size={32} />,
      title: "AI-Powered Conversations",
      description: "Intelligent health assistant that understands your symptoms and provides personalized guidance 24/7.",
      color: "#3b82f6",
      gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    {
      icon: <FileText size={32} />,
      title: "Smart Report Generation",
      description: "Automatically generate comprehensive medical reports with AI analysis and export in multiple formats.",
      color: "#10b981",
      gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
    },
    {
      icon: <Brain size={32} />,
      title: "Knowledge Base Integration",
      description: "Doctors create specialty-specific question banks that guide AI conversations with patients.",
      color: "#8b5cf6",
      gradient: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
    },
    {
      icon: <Activity size={32} />,
      title: "Real-Time Monitoring",
      description: "Track patient conversations, manage consultations, and monitor health trends in real-time.",
      color: "#f59e0b",
      gradient: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
    },
    {
      icon: <Shield size={32} />,
      title: "Secure & Private",
      description: "Enterprise-grade security with encrypted data storage and HIPAA-compliant infrastructure.",
      color: "#ef4444",
      gradient: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
    },
    {
      icon: <Zap size={32} />,
      title: "Lightning Fast",
      description: "Optimized performance with caching, compression, and smart polling for instant responses.",
      color: "#06b6d4",
      gradient: "linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
    }
  ];

  const howItWorks = [
    {
      step: "01",
      title: "Doctor Creates Knowledge Base",
      description: "Medical professionals add specialty-specific questions, protocols, and assessment guidelines to the system.",
      icon: <Brain size={40} />
    },
    {
      step: "02",
      title: "Patient Starts Conversation",
      description: "Patients chat with AURA AI, which uses the knowledge base to ask relevant, doctor-curated questions.",
      icon: <MessageSquare size={40} />
    },
    {
      step: "03",
      title: "AI Analyzes & Assists",
      description: "The AI processes responses, identifies patterns, and provides intelligent health guidance based on medical knowledge.",
      icon: <Sparkles size={40} />
    },
    {
      step: "04",
      title: "Reports & Handoff",
      description: "Automated reports are generated, and doctors can review cases or take over conversations when needed.",
      icon: <FileText size={40} />
    }
  ];

  const stats = [
    { number: "24/7", label: "AI Availability", icon: <Clock size={24} /> },
    { number: "10+", label: "Medical Specialties", icon: <Heart size={24} /> },
    { number: "99.9%", label: "Uptime Guarantee", icon: <TrendingUp size={24} /> },
    { number: "100%", label: "Data Encryption", icon: <Lock size={24} /> }
  ];

  return (
    <div className="landing-page">
      {/* Scroll Progress Bar */}
      <div className="scroll-progress-bar" style={{ width: `${scrollProgress}%` }} />

      {/* Animated Universe Background - Canvas-based */}
      <canvas 
        ref={videoRef}
        className="universe-canvas"
        style={{
          opacity: videoLoaded ? 1 : 0,
          filter: `blur(${scrollProgress / 25}px) brightness(${0.7 + scrollProgress / 500})`
        }}
      />

      {/* Animated Background with Orbs and Stars */}
      <div className="landing-bg">
        <div className="gradient-orb orb-1" style={{ opacity: 0.6 - scrollProgress / 200 }} />
        <div className="gradient-orb orb-2" style={{ opacity: 0.5 - scrollProgress / 250 }} />
        <div className="gradient-orb orb-3" style={{ opacity: 0.4 - scrollProgress / 300 }} />
        <div className="stars-container">
          {[...Array(50)].map((_, i) => (
            <div 
              key={i} 
              className="star" 
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
                transform: `scale(${0.5 + scrollProgress / 200})`
              }}
            />
          ))}
        </div>
      </div>

      {/* Hero Section */}
      <section ref={heroRef} className={`landing-hero ${activeSection === 0 ? 'active' : ''}`}>
        <div className="hero-content">
          <div className="hero-badge fade-in-up">
            <Sparkles size={16} />
            <span>Powered by AI • Built for Healthcare</span>
          </div>
          
          <h1 className="hero-title fade-in-up delay-1">
            Welcome to <span className="gradient-text">AURA</span>
          </h1>
          
          <p className="hero-subtitle fade-in-up delay-2">
            The Future of Healthcare Communication
          </p>
          
          <p className="hero-description fade-in-up delay-3">
            AI-powered platform that connects patients with intelligent health assistance 
            while empowering doctors with smart tools for better care delivery.
          </p>

          <div className="hero-buttons fade-in-up delay-4">
            <button className="btn-primary hover-lift" onClick={() => navigate('/login')}>
              <span>Get Started</span>
              <ArrowRight size={20} />
            </button>
            <button className="btn-secondary hover-lift" onClick={() => scrollToSection(featuresRef)}>
              <span>Learn More</span>
              <ChevronDown size={20} />
            </button>
          </div>

          <div className="hero-features fade-in-up delay-5">
            <div className="hero-feature">
              <CheckCircle size={18} />
              <span>Free Forever</span>
            </div>
            <div className="hero-feature">
              <CheckCircle size={18} />
              <span>No Credit Card</span>
            </div>
            <div className="hero-feature">
              <CheckCircle size={18} />
              <span>HIPAA Compliant</span>
            </div>
          </div>
        </div>

        {/* Floating 3D Cards */}
        <div className="hero-cards">
          <div className="floating-card card-1" style={{ transform: `translateY(${scrollProgress * 2}px)` }}>
            <Heart size={32} className="card-icon" />
            <h3>Patient Care</h3>
            <p>AI-guided consultations</p>
          </div>
          <div className="floating-card card-2" style={{ transform: `translateY(${scrollProgress * -1.5}px)` }}>
            <Activity size={32} className="card-icon" />
            <h3>Live Monitoring</h3>
            <p>Real-time health tracking</p>
          </div>
          <div className="floating-card card-3" style={{ transform: `translateY(${scrollProgress * 1.8}px)` }}>
            <Brain size={32} className="card-icon" />
            <h3>Smart AI</h3>
            <p>Medical knowledge base</p>
          </div>
        </div>

        <button 
          className="scroll-indicator"
          onClick={() => scrollToSection(featuresRef)}
        >
          <ChevronDown size={32} className="bounce" />
        </button>
      </section>

      {/* Features Section */}
      <section ref={featuresRef} className={`landing-features ${activeSection === 1 ? 'active' : ''}`}>
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">
              <span className="gradient-text">Powerful Features</span>
            </h2>
            <p className="section-subtitle">
              Everything you need for modern healthcare communication
            </p>
          </div>

          <div className="features-grid">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className="feature-card"
                style={{
                  animationDelay: `${index * 0.1}s`,
                  transform: activeSection === 1 ? 'translateY(0)' : 'translateY(50px)',
                  opacity: activeSection === 1 ? 1 : 0,
                  transition: `all 0.6s ease ${index * 0.1}s`
                }}
              >
                <div className="feature-icon-wrapper" style={{ background: feature.gradient }}>
                  <div className="feature-icon">
                    {feature.icon}
                  </div>
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
                <div className="feature-shine" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section ref={howItWorksRef} className={`landing-how-it-works ${activeSection === 2 ? 'active' : ''}`}>
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">
              How <span className="gradient-text">AURA</span> Works
            </h2>
            <p className="section-subtitle">
              Simple, intelligent, and effective healthcare workflow
            </p>
          </div>

          <div className="how-it-works-timeline">
            {howItWorks.map((step, index) => (
              <div 
                key={index} 
                className="timeline-item"
                style={{
                  transform: activeSection === 2 ? 'translateX(0)' : index % 2 === 0 ? 'translateX(-100px)' : 'translateX(100px)',
                  opacity: activeSection === 2 ? 1 : 0,
                  transition: `all 0.8s ease ${index * 0.2}s`
                }}
              >
                <div className="timeline-icon">
                  {step.icon}
                </div>
                <div className="timeline-content">
                  <div className="timeline-step">{step.step}</div>
                  <h3 className="timeline-title">{step.title}</h3>
                  <p className="timeline-description">{step.description}</p>
                </div>
                {index < howItWorks.length - 1 && (
                  <div className="timeline-connector" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section ref={statsRef} className={`landing-stats ${activeSection === 3 ? 'active' : ''}`}>
        <div className="container">
          <div className="stats-grid">
            {stats.map((stat, index) => (
              <div 
                key={index} 
                className="stat-card"
                style={{
                  transform: activeSection === 3 ? 'scale(1)' : 'scale(0.8)',
                  opacity: activeSection === 3 ? 1 : 0,
                  transition: `all 0.5s ease ${index * 0.1}s`
                }}
              >
                <div className="stat-icon">{stat.icon}</div>
                <div className="stat-number">{stat.number}</div>
                <div className="stat-label">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section ref={ctaRef} className={`landing-cta ${activeSection === 4 ? 'active' : ''}`}>
        <div className="container">
          <div className="cta-content">
            <h2 className="cta-title">
              Ready to Transform Healthcare?
            </h2>
            <p className="cta-description">
              Join AURA today and experience the future of medical communication
            </p>
            <div className="cta-buttons">
              <button className="btn-primary btn-large hover-lift" onClick={() => navigate('/login')}>
                <Users size={24} />
                <span>Start Free Trial</span>
                <ArrowRight size={24} />
              </button>
            </div>
            <div className="cta-note">
              <Star size={16} />
              <span>No credit card required • Setup in 2 minutes</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <h3>AURA Healthcare</h3>
              <p>AI-Powered Healthcare Communication Platform</p>
            </div>
            <div className="footer-links">
              <a href="#privacy">Privacy Policy</a>
              <a href="#terms">Terms of Service</a>
              <a href="#contact">Contact Us</a>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2025 AURA Healthcare. Built with ❤️ for Loop x IIT-B Hackathon.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
