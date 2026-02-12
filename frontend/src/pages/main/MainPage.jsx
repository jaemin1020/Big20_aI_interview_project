import React, { useEffect, useState } from 'react';
import PremiumButton from '../../components/ui/PremiumButton';

const CountUp = ({ end, duration = 2000, suffix = '', decimals = 0, delay = 0 }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime;
    let animationFrame;
    let timer;

    const animate = (time) => {
      if (!startTime) startTime = time;
      const progress = time - startTime;
      const percentage = Math.min(progress / duration, 1);

      // Easing: easeOutExpo
      const ease = percentage === 1 ? 1 : 1 - Math.pow(2, -10 * percentage);

      setCount(ease * end);

      if (percentage < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    timer = setTimeout(() => {
      animationFrame = requestAnimationFrame(animate);
    }, delay * 1000);

    return () => {
      cancelAnimationFrame(animationFrame);
      clearTimeout(timer);
    };
  }, [end, duration, delay]);

  return <>{count.toFixed(decimals)}{suffix}</>;
};

const MainPage = ({
  onStartInterview,
  onLogin,
  onRegister,
  user,
  onLogout,
  onAbout
}) => {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="main-container" style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      paddingTop: '72px',
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      zIndex: 0,
    }}>
      {/* Abstract Background Shapes */}
      <div className="bg-shape shape-1" />
      <div className="bg-shape shape-2" />
      <div className="bg-grid" />

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="brand-badge animate-fade-in-up">
            <span className="badge-dot"></span>
            <span className="badge-text">No.1 AI Interview Solution</span>
          </div>


          <h1 className="hero-title animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            면접의 <span className="text-gradient">새로운 기준</span>,<br />
            AI로 완벽하게.
          </h1>

          <p className="hero-description animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
            225개 글로벌 기업의 합격 데이터를 학습한 AI 면접관이<br className="mobile-break" />
            당신의 잠재력을 분석하고 합격률을 예측합니다.
          </p>

          <div className="cta-group animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <PremiumButton
              onClick={onStartInterview}
              style={{ padding: '1.2rem 3rem', fontSize: '1.2rem' }}
            >
              무료로 시작하기
            </PremiumButton>
            <button className="secondary-button" onClick={onAbout}>
              <span>작동 원리 보기</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          <div className="trust-badges animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
            <div className="trust-item">
              <span className="trust-number">
                <CountUp end={225} suffix="+" duration={2000} delay={0.5} />
              </span>
              <span className="trust-label">검증된 기업 데이터</span>
            </div>
            <div className="trust-divider"></div>
            <div className="trust-item">
              <span className="trust-number">
                <CountUp end={1.2} suffix="M+" decimals={1} duration={2000} delay={0.7} />
              </span>
              <span className="trust-label">누적 데이터</span>
            </div>
            <div className="trust-divider"></div>
            <div className="trust-item">
              <span className="trust-number">
                <CountUp end={4.9} suffix="/5" decimals={1} duration={2000} delay={0.9} />
              </span>
              <span className="trust-label">사용자 평점</span>
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="character-container floating">
            <div className="glow-effect"></div>
            <img
              src="/hero_char.png"
              alt="AI Interviewer"
              className="character-image"
              style={{
                transform: `translateY(${scrollY * 0.1}px)`
              }}
            />

            {/* Floating Cards Elements */}
            <div className="float-card card-1 glass-effect">
              <div className="card-icon">🧠</div>
              <div className="card-text">
                <div className="card-title">심층 분석</div>
                <div className="card-desc">답변 논리성 평가</div>
              </div>
            </div>

            <div className="float-card card-2 glass-effect">
              <div className="card-icon">📊</div>
              <div className="card-text">
                <div className="card-title">실시간 피드백</div>
                <div className="card-desc">발화 습관 교정</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Ticker Section */}
      <div className="ticker-wrap">
        <div className="ticker">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="ticker-item-group">
              <span>질문은 같지 않습니다. 당신이 다르니까.</span>
              <span className="separator">✦</span>
              <span>기업에 맞추고, 당신에게 맞춘다.</span>
              <span className="separator">✦</span>
              <span>정답이 아닌 사고를 평가합니다.</span>
              <span className="separator">✦</span>
              <span>공통 질문이 아닌, 당신만의 면접.</span>
              <span className="separator">✦</span>
              <span>225개 기업 데이터 기반 맞춤 인터뷰.</span>
              <span className="separator">✦</span>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        /* Setup & Utilities */
        :root {
          --hero-padding: max(5vh, 4rem);
          /* Ticker Colors - Light Theme Default */
          --ticker-bg: #0f172a;
          --ticker-text: #ffffff;
        }

        /* Dark Theme Override for Ticker */
        body.dark-theme {
          --ticker-bg: #f8fafc;
          --ticker-text: #0f172a;
        }

        .main-container {
          font-family: 'Outfit', 'Pretendard', sans-serif;
          overflow-x: hidden;
        }

        /* Background Shapes */
        .bg-shape {
          position: absolute;
          border-radius: 50%;
          filter: blur(100px);
          z-index: 0;
          opacity: 0.6;
          animation: shape-float 20s infinite alternate cubic-bezier(0.4, 0, 0.2, 1);
        }
        .shape-1 {
          top: -10%;
          left: -10%;
          width: 50vw;
          height: 50vw;
          background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        }
        .shape-2 {
          bottom: 10%;
          right: -5%;
          width: 40vw;
          height: 40vw;
          background: radial-gradient(circle, rgba(168, 85, 247, 0.1) 0%, transparent 70%);
          animation-delay: -10s;
        }

        .bg-grid {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-image: linear-gradient(rgba(15, 23, 42, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(15, 23, 42, 0.03) 1px, transparent 1px);
          background-size: 40px 40px;
          z-index: 0;
          mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
          -webkit-mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
        }

        body.dark-theme .bg-grid {
          background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        }

        /* Hero Section Layout */
        .hero-section {
          display: flex;
          align-items: center;
          justify-content: space-between;
          height: 100%;
          padding: 0 var(--hero-padding);
          max-width: 1400px;
          margin: 0 auto;
          position: relative;
          z-index: 1;
          gap: 4rem;
        }

        .hero-content {
          flex: 1;
          max-width: 650px;
          z-index: 2;
        }

        .hero-visual {
          flex: 1;
          height: 90vh;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
        }

        /* Hero Content Elements */
        .brand-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.8rem;
          padding: 0.6rem 1.2rem;
          background: rgba(255, 255, 255, 0.5);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(99, 102, 241, 0.2);
          border-radius: 100px;
          margin-bottom: 1rem;
          box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        .badge-dot {
          width: 8px;
          height: 8px;
          background: var(--primary);
          border-radius: 50%;
          box-shadow: 0 0 10px var(--primary);
        }
        .badge-text {
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--text-muted);
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .hero-logo {
          height: 60px;
          width: auto;
          margin-bottom: 1rem;
          display: block;
        }

        .hero-title {
          font-size: clamp(3rem, 5vw, 4.5rem);
          font-weight: 800;
          line-height: 1.1;
          letter-spacing: -0.02em;
          color: var(--text-main);
          margin-bottom: 0.5rem;
        }

        .hero-description {
          font-size: 1.25rem;
          line-height: 1.6;
          color: var(--text-muted);
          margin-bottom: 1.5rem;
          max-width: 90%;
          word-break: keep-all;
        }

        /* Buttons */
        .cta-group {
          display: flex;
          gap: 1.5rem;
          align-items: center;
          margin-bottom: 2rem;
        }

        .secondary-button {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 1rem 2rem;
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text-main);
          background: rgba(255, 255, 255, 0.5);
          border: 1px solid var(--glass-border);
          border-radius: 100px;
          cursor: pointer;
          transition: all 0.3s ease;
          backdrop-filter: blur(4px);
        }
        .secondary-button:hover {
          background: rgba(255, 255, 255, 0.8);
          transform: translateY(-2px);
          border-color: var(--primary);
          color: var(--primary);
        }

        /* Trust Badges */
        .trust-badges {
          display: flex;
          align-items: center;
          gap: 2rem;
          padding-top: 1.5rem;
          border-top: 1px solid var(--glass-border);
        }
        .trust-item {
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
        }
        .trust-number {
          font-size: 1.5rem;
          font-weight: 800;
          color: var(--text-main);
        }
        .trust-label {
          font-size: 0.875rem;
          color: var(--text-muted);
          font-weight: 500;
        }
        .trust-divider {
          width: 1px;
          height: 30px;
          background: var(--glass-border);
        }

        /* Hero Visual & Character */
        .character-container {
          position: relative;
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .character-image {
          width: 90%;
          height: auto;
          max-height: 100%;
          object-fit: cover;
          border-radius: 40px;
          filter: drop-shadow(0 20px 40px rgba(0,0,0,0.15));

          /* Natural blending with vignette mask */
          mask-image: radial-gradient(ellipse at center, black 60%, transparent 100%);
          -webkit-mask-image: radial-gradient(ellipse at center, black 60%, transparent 100%);

          transform: scale(1.05);
          z-index: 10;
          transition: transform 0.3s ease;
        }

        .glow-effect {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 60%;
          height: 60%;
          background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
          opacity: 0.2;
          filter: blur(60px);
          z-index: 0;
        }

        /* Floating Cards */
        .float-card {
          position: absolute;
          padding: 1rem 1.5rem;
          border-radius: 20px;
          display: flex;
          align-items: center;
          gap: 1rem;
          z-index: 20;
          animation: float 6s ease-in-out infinite;
          background: var(--glass-bg);
          border: 1px solid rgba(255,255,255,0.4);
          box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .card-1 {
          top: 20%;
          left: 0;
          animation-delay: 0s;
        }
        .card-2 {
          bottom: 25%;
          right: 5%;
          animation-delay: -3s;
        }

        .card-icon {
          font-size: 1.5rem;
          background: rgba(255,255,255,0.5);
          width: 40px;
          height: 40px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .card-title {
          font-weight: 700;
          font-size: 0.9rem;
          color: var(--text-main);
        }
        .card-desc {
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        /* Ticker */
        .ticker-wrap {
          position: absolute;
          bottom: 0;
          width: 100%;
          overflow: hidden;
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          border-top: 1px solid var(--glass-border);
          padding: 1.2rem 0;
          z-index: 5;
        }

        .ticker {
          display: flex;
          white-space: nowrap;
          animation: ticker 60s linear infinite;
        }

        .ticker-item-group {
          display: flex;
          align-items: center;
          gap: 4rem;
          padding-right: 4rem;
        }

        .ticker span {
          color: var(--text-muted);
          font-size: 1.1rem;
          font-weight: 600;
          letter-spacing: 0.05em;
          transition: color 0.3s ease;
        }

        .ticker .separator {
          color: var(--primary);
          font-size: 0.8rem;
          opacity: 0.7;
        }

        /* Animations */
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-15px); }
        }
        @keyframes shape-float {
          0% { transform: translate(0, 0) rotate(0deg); }
          100% { transform: translate(5%, 5%) rotate(5deg); }
        }

        .animate-fade-in-up {
          opacity: 0;
          transform: translateY(20px);
          animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
        }
        @keyframes fadeInUp {
          to { opacity: 1; transform: translateY(0); }
        }

        /* Mobile Responsive */
        @media (max-width: 1024px) {
          .hero-section {
            flex-direction: column;
            padding-top: 100px;
            text-align: center;
            gap: 2rem;
          }
          .hero-content {
            display: flex;
            flex-direction: column;
            align-items: center;
          }
          .hero-visual {
            height: 60vh;
            width: 100%;
          }
          .character-image {
            height: 100%;
            max-width: 100%;
          }
          .hero-title {
            font-size: 2.5rem;
          }
          .cta-group {
            justify-content: center;
          }
          .trust-badges {
            justify-content: center;
            width: 100%;
          }
          .float-card {
            display: none; /* Hide float cards on mobile for cleaner look */
          }
          .shape-1 { width: 80vw; height: 80vw; }
          .shape-2 { width: 70vw; height: 70vw; }
        }

        /* Dark Mode Adjustments */
        body.dark-theme .secondary-button {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
          border-color: rgba(255, 255, 255, 0.1);
        }
        body.dark-theme .secondary-button:hover {
          background: rgba(255, 255, 255, 0.2);
        }
        body.dark-theme .trust-number {
          color: #fff;
        }
      `}</style>
    </div>
  );
};

export default MainPage;