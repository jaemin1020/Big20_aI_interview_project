import React, { useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer
} from 'recharts';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const ResultPage = ({ results, report, interview, onReset }) => {
  const resultRef = useRef(null);

  // 1. 계산: 종합 점수 (Evaluate report or calculate average)
  const averageScore = report?.overall_score || (results && results.length > 0
    ? Math.round(results.reduce((acc, curr) => acc + (curr.evaluation?.score || 0), 0) / results.length)
    : 0);

  // 2. 차트 데이터 준비 (더미 데이터 + 실제 분석 데이터 매핑 필요)
  // 실제 API에서 세부 역량 점수가 오면 그것을 연동. 없을 경우 랜덤/기본값 사용.
  const chartData = [
    { subject: '기술 이해도', A: report?.technical_score || 85, fullMark: 100 },
    { subject: '문제 해결', A: 92, fullMark: 100 }, // 예시
    { subject: '의사소통', A: report?.communication_score || 78, fullMark: 100 },
    { subject: '성장 가능성', A: 88, fullMark: 100 }, // 예시
    { subject: '문화 적합성', A: report?.cultural_fit_score || 80, fullMark: 100 },
  ];

  const handleDownloadPDF = async () => {
    if (!resultRef.current) return;

    try {
      const canvas = await html2canvas(resultRef.current, {
        scale: 2, // 고화질
        useCORS: true,
        backgroundColor: '#111827' // 다크 모드 배경 유지
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`interview_report_${interview?.id || 'result'}.pdf`);
    } catch (err) {
      console.error("PDF Download failed:", err);
      alert("PDF 저장 중 오류가 발생했습니다.");
    }
  };

  return (
    <div className="result-container animate-fade-in" style={{
      flex: 1,
      width: '100%',
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '4rem 1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '2rem'
    }}>
      {/* 1. 헤더 메시지 */}
      <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <h1 className="text-gradient">면접 결과 분석</h1>
        <p style={{ color: 'var(--text-muted)' }}>AI 면접관이 분석한 귀하의 면접 결과 리포트입니다.</p>
      </div>

      <div ref={resultRef} style={{ display: 'flex', flexDirection: 'column', gap: '2rem', background: 'var(--bg-color)', padding: '1rem', borderRadius: '12px' }}>

        {/* 2. 지원 정보 표시 영역 */}
        <GlassCard style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>지원 회사</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{interview?.company_name || '회사명 미상'}</span>
            </div>
            <div style={{ width: '1px', height: '40px', background: 'var(--glass-border)' }}></div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>지원 직무</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{interview?.position || '직무 미상'}</span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginRight: '10px' }}>
              {interview?.created_at ? new Date(interview.created_at).toLocaleDateString() : new Date().toLocaleDateString()}
            </span>
            <span style={{
              padding: '6px 12px',
              borderRadius: '20px',
              background: '#10b98122',
              color: '#10b981',
              fontSize: '0.9rem',
              fontWeight: 'bold',
              border: '1px solid #10b98144'
            }}>
              분석 완료
            </span>
          </div>
        </GlassCard>

        {/* 3. 분석 안내 문구 */}
        <div style={{
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          padding: '1rem',
          borderRadius: '8px',
          textAlign: 'center',
          color: 'var(--text-main)',
          fontSize: '0.95rem'
        }}>
          💡 본 분석 결과는 지원 회사의 인재상, 비전 및 해당 직무의 핵심 요구 역량을 기준으로 AI가 종합 분석한 결과입니다.
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>

          {/* 6. 종합 평가 & 7. 역량 레이더 차트 */}
          <GlassCard style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <h3 style={{ alignSelf: 'flex-start', borderLeft: '4px solid var(--primary)', paddingLeft: '10px', marginBottom: '1rem' }}>종합 역량 분석</h3>

            <div style={{ width: '100%', height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar
                    name="My Score"
                    dataKey="A"
                    stroke="var(--primary)"
                    fill="var(--primary)"
                    fillOpacity={0.6}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <span style={{ fontSize: '3rem', fontWeight: '900', color: 'var(--text-main)' }}>{averageScore}</span>
              <span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}> / 100</span>
              <p style={{ color: 'var(--primary)', fontWeight: 'bold', marginTop: '0.5rem' }}>
                {averageScore >= 80 ? 'Excellent' : averageScore >= 60 ? 'Good' : 'Needs Improvement'}
              </p>
            </div>
          </GlassCard>

          {/* 4. 직무 역량 & 5. 인성 태도 평가 (간략 카드) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <GlassCard style={{ padding: '1.5rem', flex: 1 }}>
              <h3 style={{ borderLeft: '4px solid #3b82f6', paddingLeft: '10px', marginBottom: '1rem' }}>직무 역량 평가</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <SkillBar label="기술 이해도" score={report?.technical_score || 85} color="#3b82f6" />
                <SkillBar label="문제 해결 능력" score={92} color="#3b82f6" />
                <SkillBar label="직무 관련 경험" score={88} color="#3b82f6" />
              </div>
            </GlassCard>

            <GlassCard style={{ padding: '1.5rem', flex: 1 }}>
              <h3 style={{ borderLeft: '4px solid #10b981', paddingLeft: '10px', marginBottom: '1rem' }}>인성 및 태도 평가</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <SkillBar label="의사소통 능력" score={report?.communication_score || 78} color="#10b981" />
                <SkillBar label="책임감" score={95} color="#10b981" />
                <SkillBar label="성장 의지" score={90} color="#10b981" />
              </div>
            </GlassCard>
          </div>
        </div>

        {/* 8. 종합 피드백 영역 */}
        <GlassCard style={{ padding: '2rem' }}>
          <h3 style={{ borderLeft: '4px solid #f59e0b', paddingLeft: '10px', marginBottom: '1rem' }}>종합 피드백</h3>
          <div style={{ lineHeight: '1.6', color: 'var(--text-main)', fontSize: '1rem' }}>
            {report?.summary_text
              ? report.summary_text.split('\n').map((line, i) => <p key={i} style={{ marginBottom: '0.5rem' }}>{line}</p>)
              : <p>면접 전반에 걸쳐 우수한 역량을 보여주셨습니다. 특히 기술적인 질문에 대한 답변이 구체적이고 논리적이었습니다. 다만, 일부 상황 대처 질문에서는 조금 더 유연한 사고를 보여주면 좋겠습니다.</p>
            }
          </div>
        </GlassCard>

        {/* 질문별 상세 결과 (기존 유지) */}
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>질문별 상세 분석</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {results && results.map((result, idx) => (
              <GlassCard key={idx} style={{ padding: '2rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '50px 1fr', gap: '1.5rem' }}>
                  <div style={{
                    width: '40px', height: '40px', background: 'var(--primary)', color: 'white',
                    borderRadius: '12px', display: 'flex', justifyContent: 'center', alignItems: 'center',
                    fontWeight: '800', fontSize: '1.1rem'
                  }}>{idx + 1}</div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-main)' }}>{result.question}</h3>
                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                      <p style={{ margin: 0, color: 'var(--text-main)' }}>{result.answer || '답변 없음'}</p>
                    </div>
                    {/* 평가 피드백 */}
                    <div style={{ background: 'rgba(16, 185, 129, 0.05)', padding: '1rem', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.1)' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#10b981', display: 'block', marginBottom: '0.5rem' }}>AI 평가</span>
                      <p style={{ margin: 0, fontSize: '0.95rem' }}>
                        {result.evaluation ? (typeof result.evaluation === 'object' ? result.evaluation.feedback : result.evaluation) : '분석 중...'}
                      </p>
                    </div>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>

      </div>

      {/* 9. 하단 버튼 영역 */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '2rem' }}>
        <PremiumButton onClick={onReset} style={{ padding: '1rem 3rem' }}>
          목록으로 돌아가기
        </PremiumButton>
        <PremiumButton variant="secondary" onClick={handleDownloadPDF} style={{ padding: '1rem 3rem' }}>
          📄 PDF 리포트 저장
        </PremiumButton>
      </div>

    </div>
  );
};

// Helper Component for Skill Bar
const SkillBar = ({ label, score, color }) => (
  <div>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '0.9rem' }}>
      <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{label}</span>
      <span style={{ color: 'var(--text-muted)' }}>{score}/100</span>
    </div>
    <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
      <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: '4px' }}></div>
    </div>
  </div>
);

export default ResultPage;
