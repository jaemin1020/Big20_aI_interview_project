import React, { useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart, // [NEW]
  Bar, // [NEW]
  XAxis, // [NEW]
  YAxis, // [NEW]
  CartesianGrid, // [NEW]
  Tooltip, // [NEW]
  Legend // [NEW]
} from 'recharts';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { getInterviewTranscripts } from '../../api/interview'; // [NEW]

const ResultPage = ({ results, report, interview, onReset }) => {
  const resultRef = useRef(null);

  // Helper to safely get text content
  const getText = (data, defaultText) => data || defaultText;

  // Chart Data Preparation (6 Axes)
  const chartData = [
    { subject: '기술 이해도', A: report?.technical_score || 85, fullMark: 100 },
    { subject: '직무 경험', A: report?.experience_score || 88, fullMark: 100 },
    { subject: '문제 해결', A: report?.problem_solving_score || 92, fullMark: 100 },
    { subject: '의사소통', A: report?.communication_score || 80, fullMark: 100 },
    { subject: '책임감', A: report?.responsibility_score || 95, fullMark: 100 },
    { subject: '성장 의지', A: report?.growth_score || 90, fullMark: 100 },
  ];

  const handleDownloadPDF = async () => {
    if (!resultRef.current) return;

    try {
      const canvas = await html2canvas(resultRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#111827' // Dark mode background
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

  // [NEW] Vision Data State
  const [visionStats, setVisionStats] = React.useState(null);

  React.useEffect(() => {
    if (interview?.id) {
      getInterviewTranscripts(interview.id).then(transcripts => {
        // Filter user transcripts with vision analysis
        const userTranscripts = transcripts.filter(t => t.speaker === 'User' && t.vision_analysis);

        if (userTranscripts.length > 0) {
          const stats = userTranscripts.map((t, idx) => ({
            question: `Q${idx + 1}`,
            attention: t.vision_analysis.gaze_center_pct || 0,
            smile: Math.round((t.vision_analysis.avg_smile_score || 0) * 100),
            anxiety: Math.round((t.vision_analysis.avg_anxiety_score || 0) * 100)
          }));
          setVisionStats(stats);
        }
      }).catch(err => console.error("Failed to load vision stats:", err));
    }
  }, [interview]);

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
      {/* Header Message */}
      <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <h1 className="text-gradient">면접 결과 리포트</h1>
        <p style={{ color: 'var(--text-muted)' }}>AI 면접관이 분석한 역량별 상세 평가 결과입니다.</p>
      </div>

      <div ref={resultRef} style={{ display: 'flex', flexDirection: 'column', gap: '2rem', background: 'var(--bg-color)', padding: '2rem', borderRadius: '16px' }}>

        {/* 1. Interview Info */}
        <GlassCard style={{ padding: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem', borderLeft: '4px solid var(--primary)' }}>
          <div style={{ display: 'flex', gap: '3rem', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>지원 회사</span>
              <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{interview?.company_name || '회사명 미상'}</span>
            </div>
            <div style={{ width: '1px', height: '50px', background: 'var(--glass-border)' }}></div>
            <div>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>지원 직무</span>
              <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{interview?.position || '직무 미상'}</span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>면접 일자</span>
            <span style={{ fontSize: '1.1rem', fontWeight: '600' }}>
              {interview?.created_at ? new Date(interview.created_at).toLocaleDateString() : new Date().toLocaleDateString()}
            </span>
          </div>
        </GlassCard>

        {/* [NEW] Vision Analysis Chart */}
        {visionStats && (
          <GlassCard style={{ padding: '2rem' }}>
            <h3 style={{
              color: '#8b5cf6',
              borderBottom: '2px solid rgba(139, 92, 246, 0.3)',
              paddingBottom: '10px',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>👁️</span> 비언어적 태도 분석 (AI Vision)
            </h3>
            <div style={{ width: '100%', height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={visionStats} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="question" stroke="var(--text-muted)" />
                  <YAxis stroke="var(--text-muted)" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <Bar dataKey="attention" name="시선 집중도(%)" fill="#10b981" />
                  <Bar dataKey="smile" name="긍정 표정(%)" fill="#f59e0b" />
                  <Bar dataKey="anxiety" name="긴장도(%)" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p style={{ marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>
              * 각 질문별 답변 구간에서의 평균 시선 처리와 표정 변화를 AI가 분석한 결과입니다.
            </p>
          </GlassCard>
        )}

        {/* 2. 직무 역량 평가 (Text Feedback) */}
        <GlassCard style={{ padding: '2rem' }}>
          <h3 style={{
            color: '#3b82f6',
            borderBottom: '2px solid rgba(59, 130, 246, 0.3)',
            paddingBottom: '10px',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span>💻</span> 직무 역량 평가
          </h3>
          <div style={{ display: 'grid', gap: '1.5rem' }}>
            <FeedbackItem
              title="기술 이해도"
              content={getText(report?.technical_feedback, "지원자는 지원한 기술 스택(React, Node.js 등)에 대한 깊은 이해를 보여주었습니다. 특히 최신 트렌드와 라이브러리 활용에 대한 식견이 돋보이며, 이를 실제 프로젝트에 적용한 경험을 구체적으로 설명할 수 있습니다.")}
            />
            <FeedbackItem
              title="직무 관련 경험"
              content={getText(report?.experience_feedback, "과거 프로젝트 수행 경험을 통해 실무에서 발생할 수 있는 이슈들을 미리 파악하고 대비하는 능력이 우수합니다. 본인이 주도적으로 문제를 해결한 성과가 명확히 드러났습니다.")}
            />
            <FeedbackItem
              title="문제 해결 능력"
              content={getText(report?.problem_solving_feedback, "복잡한 문제 상황에서도 논리적이고 체계적으로 접근하는 사고방식을 가지고 있습니다. 원인 분석부터 해결책 도출까지의 과정이 매우 설득력 있게 전달되었습니다.")}
            />
          </div>
        </GlassCard>

        {/* 3. 인성 및 태도 평가 (Text Feedback) */}
        <GlassCard style={{ padding: '2rem' }}>
          <h3 style={{
            color: '#10b981',
            borderBottom: '2px solid rgba(16, 185, 129, 0.3)',
            paddingBottom: '10px',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span>🤝</span> 인성 및 태도 평가
          </h3>
          <div style={{ display: 'grid', gap: '1.5rem' }}>
            <FeedbackItem
              title="의사소통 능력"
              content={getText(report?.communication_feedback, "질문의 의도를 정확히 파악하고, 자신의 생각을 명료하게 전달하는 능력이 뛰어납니다. 상대방의 입장을 고려하며 대화를 이끌어가는 태도가 돋보입니다.")}
            />
            <FeedbackItem
              title="책임감"
              content={getText(report?.responsibility_feedback, "맡은 업무에 대해 끝까지 책임을 지려는 강한 의지를 보여주었습니다. 어려움에 직면했을 때 회피하지 않고 완수해내는 끈기가 인상적입니다.")}
            />
            <FeedbackItem
              title="성장 의지"
              content={getText(report?.growth_feedback, "지속적인 자기 계발을 통해 역량을 강화하려는 의지가 뚜렷합니다. 실패로부터 배우고 더 나은 방향으로 나아가려는 긍정적인 마인드셋을 갖추고 있습니다.")}
            />
          </div>
        </GlassCard>


        {/* 4. 종합 평가 (Chart + Strengths/Weaknesses) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>

          {/* 육각형 그래프 */}
          <GlassCard style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <h3 style={{ width: '100%', borderLeft: '4px solid var(--primary)', paddingLeft: '10px', marginBottom: '1rem', color: 'var(--text-main)' }}>
              종합 역량 분석표
            </h3>
            <div style={{ width: '100%', height: '350px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 13, fontWeight: 'bold' }} />
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
          </GlassCard>

          {/* 강점 & 보완점 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <GlassCard style={{ padding: '1.5rem', flex: 1 }}>
              <h4 style={{ color: '#10b981', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>🏆</span> 주요 강점
              </h4>
              <ul style={{ margin: 0, paddingLeft: '20px', lineHeight: '1.6', color: 'var(--text-main)' }}>
                {report?.strengths ? (
                  report.strengths.map((point, i) => <li key={i} style={{ marginBottom: '8px' }}>{point}</li>)
                ) : (
                  <>
                    <li>탄탄한 기초 역량을 바탕으로 한 높은 기술 이해도</li>
                    <li>논리적인 사고를 통한 문제 해결 접근 방식</li>
                    <li>팀워크를 중시하는 협력적인 태도</li>
                  </>
                )}
              </ul>
            </GlassCard>

            <GlassCard style={{ padding: '1.5rem', flex: 1 }}>
              <h4 style={{ color: '#f59e0b', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>🔥</span> 보완 필요 사항
              </h4>
              <ul style={{ margin: 0, paddingLeft: '20px', lineHeight: '1.6', color: 'var(--text-main)' }}>
                {report?.improvements ? (
                  report.improvements.map((point, i) => <li key={i} style={{ marginBottom: '8px' }}>{point}</li>)
                ) : (
                  <>
                    <li>긴장된 상황에서의 유연한 대처 능력 강화 필요</li>
                    <li>답변 시 두괄식 표현을 사용하여 명확성 높이기</li>
                    <li>구체적인 수치 데이터를 활용한 성과 어필</li>
                  </>
                )}
              </ul>
            </GlassCard>
          </div>
        </div>

      </div>

      {/* Button Area */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '2rem' }}>
        <PremiumButton onClick={onReset} style={{ padding: '1rem 3rem', minWidth: '200px' }}>
          처음으로 돌아가기
        </PremiumButton>
        <PremiumButton variant="secondary" onClick={handleDownloadPDF} style={{ padding: '1rem 3rem', minWidth: '200px' }}>
          📄 리포트 저장 (PDF)
        </PremiumButton>
      </div>

    </div>
  );
};

// Sub-component for Text Feedback items
const FeedbackItem = ({ title, content }) => (
  <div style={{
    padding: '1.2rem',
    background: 'rgba(255,255,255,0.03)',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)'
  }}>
    <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-main)', fontSize: '1.1rem' }}>{title}</h4>
    <p style={{ margin: 0, color: 'var(--text-muted)', lineHeight: '1.6', fontSize: '0.95rem' }}>{content}</p>
  </div>
);

export default ResultPage;