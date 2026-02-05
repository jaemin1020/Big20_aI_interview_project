import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const ResultPage = ({ results, onReset }) => {
  // Calculate average score if results exist
  const averageScore = results && results.length > 0 
    ? Math.round(results.reduce((acc, curr) => acc + (curr.evaluation?.score || 0), 0) / results.length)
    : 0;

  return (
    <div className="result-container animate-fade-in" style={{ 
      width: '100%', 
      maxWidth: '1200px', 
      margin: '0 auto', 
      paddingTop: '6rem', 
      paddingBottom: '4rem' 
    }}>
      {/* Overview Section: SCR-25 Style */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: '2rem', marginBottom: '3rem' }}>
        <GlassCard style={{ padding: '2.5rem', textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1.5rem' }}>종합 분석 점수</h2>
          <div style={{ 
            width: '180px', 
            height: '180px', 
            borderRadius: '50%', 
            border: '8px solid rgba(var(--primary-rgb, 59, 130, 246), 0.1)',
            borderTopColor: 'var(--primary)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            marginBottom: '1.5rem',
            position: 'relative'
          }}>
            <span style={{ fontSize: '3.5rem', fontWeight: '900', color: 'var(--text-main)' }}>{averageScore}</span>
            <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 100</span>
          </div>
          <p style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--primary)' }}>우수한 실무 역량 보유</p>
        </GlassCard>

        <GlassCard style={{ padding: '2.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '2rem' }}>역량 지표 상세</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {[
              { label: '기술 전문성', score: 85, color: '#3b82f6' },
              { label: '문제 해결 능력', score: 92, color: '#10b981' },
              { label: '의사소통', score: 78, color: '#f59e0b' },
              { label: '성장 가능성', score: 88, color: '#8b5cf6' }
            ].map((trait, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.6rem', fontSize: '0.9rem' }}>
                  <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{trait.label}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{trait.score}%</span>
                </div>
                <div style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${trait.score}%`, 
                    height: '100%', 
                    background: trait.color, 
                    borderRadius: '10px',
                    boxShadow: `0 0 10px ${trait.color}44`
                  }}></div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <h2 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '1.5rem', paddingLeft: '0.5rem' }}>질문별 상세 분석</h2>
      
      {/* Detailed Items */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {results && results.map((result, idx) => (
          <GlassCard key={idx} style={{ padding: '2rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '50px 1fr', gap: '1.5rem' }}>
              <div style={{ 
                width: '40px', 
                height: '40px', 
                background: 'var(--primary)', 
                color: 'white', 
                borderRadius: '12px', 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                fontWeight: '800',
                fontSize: '1.1rem'
              }}>{idx + 1}</div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--text-main)', lineHeight: '1.4' }}>{result.question}</h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '2rem' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.8rem' }}>나의 답변</span>
                    <p style={{ fontSize: '1.05rem', lineHeight: '1.6', color: 'var(--text-main)', margin: 0 }}>{result.answer || '답변 데이터가 없습니다.'}</p>
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ background: 'rgba(16, 185, 129, 0.08)', padding: '1.2rem', borderRadius: '16px', border: '1px solid rgba(16, 185, 129, 0.1)' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#10b981', textTransform: 'uppercase', display: 'block', marginBottom: '0.6rem' }}>AI Feedback</span>
                      <p style={{ fontSize: '0.95rem', lineHeight: '1.5', margin: 0, color: 'var(--text-main)' }}>
                        {result.evaluation ? (typeof result.evaluation === 'object' ? result.evaluation.feedback : result.evaluation) : '분석 중...'}
                      </p>
                    </div>
                    {result.emotion && (
                      <div style={{ background: 'rgba(59, 130, 246, 0.08)', padding: '1rem', borderRadius: '16px', border: '1px solid rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                        <span style={{ fontSize: '1.2rem' }}>📊</span>
                        <div>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>주요 감정</span>
                          <span style={{ fontSize: '0.9rem', fontWeight: '600' }}>{result.emotion.dominant_emotion}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '3rem' }}>
        <PremiumButton onClick={onReset} style={{ padding: '1.2rem 3rem', fontSize: '1.1rem' }}>대시보드로 돌아가기</PremiumButton>
        <PremiumButton variant="secondary" style={{ padding: '1.2rem 3rem', fontSize: '1.1rem', border: '1px solid var(--glass-border)' }}>PDF 리포트 저장</PremiumButton>
      </div>
    </div>
  );
};

export default ResultPage;
