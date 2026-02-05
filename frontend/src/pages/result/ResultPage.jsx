import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const ResultPage = ({ results, onReset }) => {
  return (
    <div className="result-container animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 className="text-gradient" style={{ fontSize: '3rem' }}>면접 분석 결과</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem' }}>AI가 분석한 귀하의 역량 및 피드백 리포트입니다.</p>
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
