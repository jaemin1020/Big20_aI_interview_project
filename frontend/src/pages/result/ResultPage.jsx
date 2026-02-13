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
// html2canvas & jsPDF removed for vector print support

const ResultPage = ({ results, report, interview, onReset }) => {
  const resultRef = useRef(null);

  // Helper to safely get text content
  const getText = (data, defaultText) => data || defaultText;

  // Chart Data Preparation (6 Axes) using actual AI scores from report and details_json
  const chartData = [
    { subject: '기술 이해도', A: report?.technical_score || 85, fullMark: 100 },
    { subject: '직무 경험', A: report?.details_json?.experience_score || 88, fullMark: 100 },
    { subject: '문제 해결', A: report?.details_json?.problem_solving_score || 92, fullMark: 100 },
    { subject: '의사소통', A: report?.communication_score || 80, fullMark: 100 },
    { subject: '책임감', A: report?.details_json?.responsibility_score || 95, fullMark: 100 },
    { subject: '성장 의지', A: report?.details_json?.growth_score || 90, fullMark: 100 },
  ];

  const handleDownloadPDF = () => {
    window.print();
  };

  return (
    <>
      <style>
        {`
          @media print {
            @page { margin: 10mm; size: A4 portrait; }
            html, body {
              width: 210mm;
              height: 100%;
              background: white !important;
              color: black !important;
              font-size: 10pt; /* 전체 폰트 크기 축소 */
              line-height: 1.3;
            }
            .no-print, header, nav, .premium-button { display: none !important; }

            /* 컨테이너 여백 제거 및 너비 최대화 */
            .result-container {
              width: 100% !important;
              max-width: none !important;
              padding: 0 !important;
              margin: 0 !important;
            }

            /* 제목 섹션 축소 */
            h1 { font-size: 18pt !important; margin-bottom: 5px !important; }
            h3 { font-size: 14pt !important; margin-bottom: 10px !important; padding-bottom: 5px !important; }
            p { color: #333 !important; margin-bottom: 5px !important; }

            /* 새 페이지 강제 분리 클래스 */
            .page-break-before {
              page-break-before: always !important;
              break-before: page !important;
              margin-top: 20mm !important;
            }

            /* 카드 스타일 및 내부 요소 잘림 방지 */
            .glass-card, div[class*="GlassCard"] {
              break-inside: avoid-page; /* 페이지 중간 잘림 방지 (강력) */
              background: white !important;
              border: 1px solid #ddd !important;
              box-shadow: none !important;
              padding: 10mm !important; /* 패딩 축소 */
              margin-bottom: 10px !important; /* 카드 간 간격 축소 */
              border-radius: 8px !important;
              page-break-inside: avoid;
            }

            /* 새 페이지 강제 분리 클래스 */
            .page-break-before {
              page-break-before: always !important;
              break-before: page !important;
              margin-top: 20mm !important; /* 페이지 넘김 후 여백 */
            }

            /* 내부 항목 단위로도 잘림 방지 (FeedbackItem 등) */
            .glass-card > div > div,
            .glass-card div,
            li,
            h3,
            p {
              break-inside: avoid;
              page-break-inside: avoid;
            }


            /* 피드백 아이템 그리드 형태로 변경하여 공간 절약 */
            .glass-card > div[style*="display: grid"] {
              display: grid !important;
              grid-template-columns: 1fr 1fr; /* 2단 배열 */
              gap: 10px !important;
            }

            /* 로고 및 아이콘 크기 조정 */
            span[role="img"] { display: none; } /* 이모지 숨김 (선택사항) */

            /* 차트(SVG) 스타일 보정 */
            .recharts-wrapper svg {
              overflow: visible !important;
            }
            .recharts-polar-grid-angle line,
            .recharts-polar-grid-concentric path {
              stroke: #ccc !important; /* 그리드 라인을 회색으로 */
              stroke-opacity: 1 !important;
            }
            .recharts-text {
              fill: #000 !important; /* 텍스트를 검정색으로 */
            }
            .recharts-layer path[name="My Score"] {
              stroke: #2563eb !important; /* 데이터 라인을 파란색으로 */
              fill: #2563eb !important;
              fill-opacity: 0.3 !important;
            }

          }
        `}
      </style>
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

        {/* 0. AI Summary (위원장 총평) */}
        {report?.summary_text && (
          <GlassCard style={{ padding: '2rem', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
            <h3 style={{ color: 'var(--primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🎙️</span> 시니어 위원장 총평
            </h3>
            <p style={{ fontSize: '1.15rem', lineHeight: '1.8', color: 'var(--text-main)', fontWeight: '500', wordBreak: 'keep-all' }}>
              "{report.summary_text}"
            </p>
          </GlassCard>
        )}

        <div ref={resultRef} style={{ display: 'flex', flexDirection: 'column', gap: '2rem', background: 'var(--bg-color)', padding: '2rem', borderRadius: '16px' }}>

          {/* 1. Interview Info */}
          <GlassCard style={{ padding: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem', borderLeft: '4px solid var(--primary)' }}>
            <div style={{ display: 'flex', gap: '3rem', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>지원 회사</span>
                <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{report?.company_name || interview?.company_name || '회사명 미상'}</span>
              </div>
              <div style={{ width: '1px', height: '50px', background: 'var(--glass-border)' }}></div>
              <div>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>지원 직무</span>
                <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{report?.position || interview?.position || '직무 미상'}</span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>면접 일자</span>
              <span style={{ fontSize: '1.1rem', fontWeight: '600' }}>
                {report?.interview_date
                  ? new Date(report.interview_date).toLocaleDateString()
                  : (interview?.created_at ? new Date(interview.created_at).toLocaleDateString() : new Date().toLocaleDateString())}
              </span>
            </div>
          </GlassCard>


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
                content={getText(report?.details_json?.technical_feedback || report?.technical_feedback, "지원하신 기술 스택에 대한 상세 분석이 진행 중입니다.")}
              />
              <FeedbackItem
                title="직무 관련 경험"
                content={getText(report?.details_json?.experience_feedback, "수행하신 프로젝트 경험에 대한 AI 분석 결과입니다.")}
              />
              <FeedbackItem
                title="문제 해결 능력"
                content={getText(report?.details_json?.problem_solving_feedback, "문제 상황 대처 및 해결 논리에 대한 AI 분석 결과입니다.")}
              />
            </div>
          </GlassCard>

          {/* 3. 인성 및 태도 평가 (Text Feedback) */}
          <GlassCard className="page-break-before" style={{ padding: '2rem' }}>
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
                content={getText(report?.details_json?.communication_feedback || report?.communication_feedback, "답변 과정에서의 전달력과 의사소통 스타일에 대한 분석 결과입니다.")}
              />
              <FeedbackItem
                title="책임감"
                content={getText(report?.details_json?.responsibility_feedback, "업무 임하는 태도와 책임감에 대한 AI 분석 결과입니다.")}
              />
              <FeedbackItem
                title="성장 의지"
                content={getText(report?.details_json?.growth_feedback, "자기계발 의지와 발전 가능성에 대한 AI 분석 결과입니다.")}
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
        <div className="no-print" style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '2rem' }}>
          <PremiumButton onClick={onReset} style={{ padding: '1rem 3rem', minWidth: '200px' }}>
            처음으로 돌아가기
          </PremiumButton>
          <PremiumButton variant="secondary" onClick={handleDownloadPDF} style={{ padding: '1rem 3rem', minWidth: '200px' }}>
            📄 리포트 저장 (PDF)
          </PremiumButton>
        </div>

      </div>
    </>
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