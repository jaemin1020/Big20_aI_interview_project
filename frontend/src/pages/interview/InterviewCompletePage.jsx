import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const InterviewCompletePage = ({ isReportLoading, onCheckResult, onExit }) => {
  return (
    <div className="complete-container animate-fade-in" style={{ 
      width: '100%',
      maxWidth: '900px',
      margin: '0 auto',
      paddingTop: '8rem',
      paddingBottom: '4rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '2rem'
    }}>
      {/* 1. 면접 종료 헤더 영역 */}
      <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '900', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
          INTERVIEW <span className="text-gradient">FINISHED</span>
        </h1>
        <p style={{ fontSize: '1.2rem', color: 'var(--primary)', fontWeight: '700' }}>
          면접 세션이 정상적으로 종료되었습니다.
        </p>
      </div>

      {/* 2 & 3. 안내 및 요약 영역 */}
      <GlassCard style={{ padding: '3rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '3rem', alignItems: 'center' }}>
          
          {/* Left Side: 절차 완료 안내 */}
          <div style={{ textAlign: 'left' }}>
            <h2 style={{ fontSize: '1.6rem', fontWeight: '800', marginBottom: '1.5rem', color: 'var(--text-main)' }}>
              모든 면접 절차가 완료되었습니다
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem', lineHeight: '1.8', marginBottom: '2rem' }}>
              지원자님의 소중한 답변이 모두 기록되었습니다.<br/>
              이제 AI 분석 리포트를 통해 면접 답변의 핵심 키워드, 역량 지표, 그리고 맞춤형 피드백을 확인하실 수 있습니다.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--primary)', fontWeight: '600' }}>
              <span>결과 확인 화면으로 이동하여 상세 리포트를 확인하세요.</span>
            </div>
          </div>

          {/* Right Side: 진행 현황 및 요약 */}
          <div style={{ 
            background: 'rgba(255, 255, 255, 0.03)', 
            borderRadius: '24px', 
            padding: '2rem', 
            border: '1px solid var(--glass-border)',
            textAlign: 'center'
          }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: '1.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              분석 및 평가 진행 현황
            </h3>
            
            <div style={{ position: 'relative', width: '120px', height: '120px', margin: '0 auto 1.5rem' }}>
              <div className={`spinner ${isReportLoading ? '' : 'hidden'}`} style={{ 
                width: '100%', 
                height: '100%', 
                margin: 0,
                borderWidth: '6px',
                borderColor: 'var(--primary) transparent transparent transparent',
                display: isReportLoading ? 'block' : 'none'
              }}></div>
              <div style={{ 
                position: 'absolute', 
                top: 0, 
                left: 0, 
                width: '100%', 
                height: '100%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                fontSize: '2rem'
              }}>
                {isReportLoading ? '🧠' : '✅'}
              </div>
            </div>

            <p style={{ fontWeight: '800', color: isReportLoading ? 'var(--primary)' : '#10b981', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              {isReportLoading ? 'AI 분석 리포트 생성 중' : '리포트 생성 완료'}
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              {isReportLoading ? '답변 데이터를 심층 분석하고 있습니다...' : '지금 바로 분석 결과를 확인해보세요.'}
            </p>

            <div style={{ textAlign: 'left', display: 'inline-block', width: 'fit-content' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#10b981', fontSize: '0.9rem', fontWeight: '600' }}>
                <span>●</span>
                <span>면접 결과 전송 완료</span>
              </div>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px', 
                color: isReportLoading ? 'var(--text-muted)' : '#10b981', 
                fontSize: '0.9rem',
                fontWeight: '600',
                opacity: isReportLoading ? 0.6 : 1
              }}>
                <span>●</span>
                <span>결과 분석 {isReportLoading ? '진행 중' : '완료'}</span>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* 4 & 5. 버튼 영역 */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', alignItems: 'center' }}>
        <PremiumButton 
          variant="secondary" 
          onClick={onExit}
          style={{ padding: '1.2rem 3rem', fontSize: '1.1rem', minWidth: '200px', border: '1px solid var(--glass-border)' }}
        >
          홈으로 이동 (종료)
        </PremiumButton>
        
        <PremiumButton 
          onClick={onCheckResult}
          disabled={isReportLoading}
          style={{ 
            padding: '1.2rem 4rem', 
            fontSize: '1.2rem', 
            minWidth: '280px',
            boxShadow: !isReportLoading ? '0 10px 30px var(--primary-shadow)' : 'none'
          }}
        >
          {isReportLoading ? '분석 대기 중...' : '결과 확인하기'}
        </PremiumButton>
      </div>
    </div>
  );
};

export default InterviewCompletePage;
