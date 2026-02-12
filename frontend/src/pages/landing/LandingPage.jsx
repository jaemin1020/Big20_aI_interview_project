import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const LandingPage = ({
  startInterview,
  handleLogout
}) => {
  return (
    <div className="landing-container animate-fade-in" style={{
<<<<<<< HEAD
<<<<<<< HEAD
      flex: 1,
=======
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
<<<<<<< HEAD
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
<<<<<<< HEAD
<<<<<<< HEAD
      width: '100%'
    }}>
      <GlassCard style={{ textAlign: 'center', maxWidth: '800px', width: '100%' }}>
        <div style={{ marginBottom: '3rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="logo-wrapper" style={{ width: '200px' }}>
              <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
            </div>
=======
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
      padding: '2rem',
      boxSizing: 'border-box'
    }}>
      {/* Background overlay if needed, or rely on body bg */}

      <div className="content-wrapper" style={{
        maxWidth: '800px',
        width: '100%',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '3rem'
      }}>

        {/* Header Section */}
        <div className="header-section">
          <div className="logo-wrapper" style={{ width: '180px', marginBottom: '1.5rem', margin: '0 auto' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
<<<<<<< HEAD
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
          </div>
          <h1 className="text-gradient" style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '1rem' }}>
            모의면접 시작하기
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem' }}>
            실전과 같은 환경에서 AI 면접관과 함께<br />당신의 역량을 확인해보세요.
          </p>
        </div>

<<<<<<< HEAD
<<<<<<< HEAD
        <div style={{
          border: '1px solid var(--glass-border)',
          borderRadius: '16px',
          padding: '1.5rem',
          textAlign: 'left',
          marginBottom: '2.5rem',
          background: 'rgba(255, 255, 255, 0.03)'
        }}>
          <ul style={{
            margin: 0,
            paddingLeft: '1.2rem',
            color: 'var(--text-main)',
            fontSize: '1rem',
            lineHeight: '1.8',
            listStyleType: 'disc'
          }}>
            <li>예상 소요시간 : 20분</li>
            <li>진행 방식 : 영상 또는 음성 응답</li>
            <li>중간 종료 가능</li>
          </ul>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <PremiumButton
            onClick={() => startInterview()}
            style={{ padding: '16px 60px', fontSize: '1.2rem' }}
          >
            면접 시작
          </PremiumButton>
        </div>
      </GlassCard>
=======
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
        {/* Info Grid */}
        <div className="info-grid" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1.5rem',
          width: '100%',
          marginBottom: '1rem'
        }}>
          {[
            { label: '소요 시간', value: '약 20분', icon: '⏱️' },
            { label: '진행 방식', value: '영상/음성', icon: '🎥' },
            { label: '참고 사항', value: '중간 종료 가능', icon: '💡' }
          ].map((item, idx) => (
            <div key={idx} style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(10px)',
              border: '1px solid var(--glass-border)',
              borderRadius: '20px',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'transform 0.3s ease'
            }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-5px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <span style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{item.icon}</span>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{item.label}</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-main)' }}>{item.value}</span>
            </div>
          ))}
        </div>

        {/* Action Button */}
        <PremiumButton
          onClick={() => startInterview()}
          style={{
            padding: '1.2rem 4rem',
            fontSize: '1.3rem',
            boxShadow: '0 20px 40px rgba(var(--primary-h), var(--primary-s), var(--primary-l), 0.3)'
          }}
        >
          면접 시작하기
        </PremiumButton>
      </div>
<<<<<<< HEAD
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
    </div>
  );
};

export default LandingPage;