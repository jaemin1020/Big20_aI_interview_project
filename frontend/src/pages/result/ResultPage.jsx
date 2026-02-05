import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const ResultPage = ({ results, onReset }) => {
  return (
<<<<<<< HEAD
    <div className="result-container animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 className="text-gradient" style={{ fontSize: '3rem' }}>면접 분석 결과</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem' }}>AI가 분석한 귀하의 역량 및 피드백 리포트입니다.</p>
=======
    <div className="result-container animate-fade-in" style={{ 
      flex: 1,
      width: '100%', 
      maxWidth: '1200px', 
      margin: '0 auto', 
      padding: '6rem 0 4rem',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center'
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
>>>>>>> fcf5dd1 (fix 박스 중앙 위치 fix)
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {results.map((result, idx) => (
          <GlassCard key={idx} className="result-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1rem' }}>
              <h3 style={{ margin: 0, color: 'var(--primary)' }}>질문 {idx + 1}. {result.question}</h3>
              {result.emotion && (
                <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '6px 14px', borderRadius: '50px', fontSize: '0.85rem', fontWeight: '600' }}>
                  😊 주요 감정: {result.emotion.dominant_emotion}
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              <div>
                <h4 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>귀하의 답변</h4>
                <p style={{ lineHeight: '1.6' }}>{result.answer || '답변 내용 없음'}</p>
              </div>
              <div style={{ background: 'rgba(16, 185, 129, 0.05)', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(16, 185, 129, 0.1)' }}>
                <h4 style={{ color: 'var(--secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>AI 피드백</h4>
                {typeof result.evaluation === 'object' ? (
                  <div style={{ fontSize: '0.95rem', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                    <p><strong>점수:</strong> {result.evaluation.score} / 100</p>
                    <p>{result.evaluation.feedback}</p>
                    <div>
                      <strong>핵심 키워드:</strong>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                        {result.evaluation.keywords?.map((kw, i) => (
                          <span key={i} style={{ background: 'rgba(255,255,255,0.05)', padding: '4px 10px', borderRadius: '4px', fontSize: '0.8rem' }}>#{kw}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p>{result.evaluation}</p>
                )}
              </div>
            </div>
          </GlassCard>
        ))}

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '2rem' }}>
          <PremiumButton onClick={onReset} style={{ padding: '16px 40px' }}>처음으로 돌아가기</PremiumButton>
          <PremiumButton variant="secondary" style={{ padding: '16px 40px' }}>리포트 PDF 저장</PremiumButton>
        </div>
      </div>
    </div>
  );
};

export default ResultPage;
