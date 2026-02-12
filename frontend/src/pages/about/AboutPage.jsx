import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import PersonalizedInterviewSystemImage from '../../assets/PersonalizedInterviewSystem.png';

const AboutPage = ({ onBack }) => {
    return (
        <div className="about-container animate-fade-in" style={{
            flex: 1,
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '4rem 1rem',
            gap: '3rem',
            background: 'var(--bg-gradient)',
            overflowY: 'auto'
        }}>
            <div style={{ maxWidth: '1100px', width: '100%', display: 'flex', flexDirection: 'column', gap: '4rem' }}>

                {/* Section 1: VictorView 브랜드 소개 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out both' }}>
                    <GlassCard style={{ display: 'flex', gap: '3rem', padding: '4rem', alignItems: 'center' }}>
                        <div style={{ flex: 1.5 }}>
                            <h2 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '1.5rem', fontFamily: "'Outfit', sans-serif", color: 'var(--primary)' }}>
                                VictorView는 무엇인가?
                            </h2>
                            <p style={{ fontSize: '1.1rem', lineHeight: '1.8', color: 'var(--text-main)', opacity: 0.9 }}>
                                VictorView는 AI 기반 멀티모달 면접 분석 기술을 활용하여 지원자의 역량을 객관적으로 평가하는 지능형 인터뷰 플랫폼입니다.
                                공통 질문 중심의 기존 모의면접을 넘어, 기업 인재상과 지원자의 경험 데이터를 결합하여 맞춤형 면접 환경을 제공합니다.
                            </p>
                        </div>
                        <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '24px', padding: '2rem', textAlign: 'center' }}>
                            <img src="/logo.png" alt="VictorView Logo" style={{ width: '100%', height: 'auto', animation: 'subtle-pulse 4s infinite ease-in-out' }} />
                            <p style={{ marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>브랜드 로고</p>
                        </div>
                    </GlassCard>
                </section>

                {/* Section 2: 개인 맞춤형 면접 시스템 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.2s both' }}>
                    <GlassCard style={{ display: 'flex', gap: '3rem', padding: '4rem', alignItems: 'center', flexDirection: 'row-reverse' }}>
                        <div style={{ flex: 1.5 }}>
                            <h2 style={{ fontSize: '2.2rem', fontWeight: '700', marginBottom: '1.5rem', fontFamily: "'Outfit', sans-serif" }}>
                                개인 맞춤형 면접 시스템
                            </h2>
                            <p style={{ fontSize: '1.1rem', marginBottom: '1.5rem', opacity: 0.8 }}>
                                VictorView는 지원자의 이력, 경험, 답변 패턴을 분석하여 개인 맞춤 질문을 생성합니다.
                            </p>
                            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {['이력서 기반 질문 자동 생성', '답변 흐름 기반 꼬리 질문 생성', '성향 및 커뮤니케이션 패턴 분석'].map((item, i) => (
                                    <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', fontSize: '1.05rem', fontWeight: '500' }}>
                                        <span style={{ color: 'var(--primary)' }}>✓</span> {item}
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '24px', height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                            <img
                                src={PersonalizedInterviewSystemImage}
                                alt="개인 맞춤형 면접 시스템"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'contain',
                                    padding: '1rem'
                                }}
                            />
                        </div>
                    </GlassCard>
                </section>

                {/* Section 3: 기업 맞춤형 HR 연동 솔루션 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.4s both' }}>
                    <GlassCard style={{ padding: '4rem' }}>
                        <div style={{ display: 'flex', gap: '3rem', alignItems: 'flex-start' }}>
                            <div style={{ flex: 1.5 }}>
                                <h2 style={{ fontSize: '2.2rem', fontWeight: '700', marginBottom: '1.5rem', fontFamily: "'Outfit', sans-serif" }}>
                                    기업 맞춤형 HR 연동 솔루션
                                </h2>
                                <p style={{ fontSize: '1.1rem', marginBottom: '2rem', opacity: 0.8 }}>
                                    VictorView는 향후 기업 HR 시스템과 연동 가능한 구조로 설계되어 있습니다.
                                </p>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                                    <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                                        {['ATS(채용 관리 시스템) 연동 가능', '기업 맞춤 평가 루브릭 설정', '대규모 지원자 선별 자동화', '채용 데이터 분석 지원'].map((item, i) => (
                                            <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.95rem' }}>
                                                <span style={{ color: 'var(--secondary)' }}>✓</span> {item}
                                            </li>
                                        ))}
                                    </ul>
                                    <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                                        {['기업 맞춤 AI 면접관 구축', '기업별 LLM 파인튜닝', '채용 데이터 분석 플랫폼 확장', 'HR 시스템 통합 솔루션 제공'].map((item, i) => (
                                            <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.95rem' }}>
                                                <span style={{ color: 'var(--secondary)' }}>✓</span> {item}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                            <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '24px', height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                                    <span style={{ fontSize: '3rem' }}>🏢</span>
                                    <p>기업 맞춤 면접 관련 이미지</p>
                                </div>
                            </div>
                        </div>
                    </GlassCard>
                </section>

                {/* Section 4: AI 멀티모달 역량 분석 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.6s both' }}>
                    <GlassCard style={{ display: 'flex', gap: '3rem', padding: '4rem', alignItems: 'center' }}>
                        <div style={{ flex: 1.5 }}>
                            <h2 style={{ fontSize: '2.2rem', fontWeight: '700', marginBottom: '1.5rem', fontFamily: "'Outfit', sans-serif" }}>
                                AI 멀티모달 역량 분석
                            </h2>
                            <p style={{ fontSize: '1.1rem', marginBottom: '2rem', opacity: 0.8 }}>
                                VictorView는 단순 답변 평가가 아닌 다양한 신호를 종합 분석합니다.
                            </p>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem' }}>
                                <div>
                                    <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>✓ 비언어 행동 분석</h4>
                                    <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.9rem', opacity: 0.7, lineHeight: '1.6' }}>
                                        <li>표정 변화 분석</li>
                                        <li>시선 처리 분석</li>
                                        <li>태도 및 몰입도 평가</li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>✓ 음성 분석</h4>
                                    <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.9rem', opacity: 0.7, lineHeight: '1.6' }}>
                                        <li>발화 속도 분석</li>
                                        <li>음성 안정성 분석</li>
                                        <li>긴장도 및 자신감 추정</li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>✓ 비언어 행동 분석</h4>
                                    <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.9rem', opacity: 0.7, lineHeight: '1.6' }}>
                                        <li>표정 변화 분석</li>
                                        <li>시선 처리 분석</li>
                                        <li>태도 및 몰입도 평가</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '24px', height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                                <span style={{ fontSize: '3rem' }}>📊</span>
                                <p>AI 멀티모달 관련 이미지</p>
                            </div>
                        </div>
                    </GlassCard>
                </section>

                {/* Section 5: VictorView 미래 확장 방향 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.8s both', marginBottom: '4rem' }}>
                    <GlassCard style={{ padding: '4rem' }}>
                        <div style={{ display: 'flex', gap: '3rem', alignItems: 'center' }}>
                            <div style={{ flex: 1.5 }}>
                                <h2 style={{ fontSize: '2.2rem', fontWeight: '700', marginBottom: '1.5rem', fontFamily: "'Outfit', sans-serif" }}>
                                    VictorView 미래 확장 방향
                                </h2>
                                <p style={{ fontSize: '1.1rem', marginBottom: '2.5rem', opacity: 0.8 }}>
                                    VictorView는 AI 면접 플랫폼을 넘어 지능형 채용 평가 솔루션으로 확장됩니다.
                                </p>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                                    {[
                                        '기업 맞춤 AI 면접관 구축',
                                        '기업 인재상 기반 맞춤 면접 시스템',
                                        '채용 데이터 분석 플랫폼 확장',
                                        'HR 시스템 통합 솔루션 제공'
                                    ].map((text, i) => (
                                        <div key={i} style={{
                                            background: 'rgba(255,255,255,0.05)',
                                            padding: '1.5rem 1rem',
                                            borderRadius: '16px',
                                            textAlign: 'center',
                                            fontSize: '0.9rem',
                                            fontWeight: '600',
                                            border: '1px solid var(--glass-border)',
                                            transition: 'all 0.3s ease',
                                            cursor: 'default'
                                        }} className="future-box">
                                            {text}
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '24px', height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                                    <img src="/more.png" alt="Future Expansion" style={{ maxWidth: '100%', borderRadius: '16px' }} />
                                    <p style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>AI 멀티모달 관련 이미지</p>
                                </div>
                            </div>
                        </div>
                    </GlassCard>
                </section>

                <div style={{ textAlign: 'center', paddingBottom: '4rem' }}>
                    <PremiumButton onClick={onBack} style={{ padding: '16px 48px' }}>
                        돌아가기
                    </PremiumButton>
                </div>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
        .future-box:hover {
          transform: translateY(-5px);
          background: rgba(255, 255, 255, 0.1);
          border-color: var(--primary);
          color: var(--primary);
        }
        @keyframes subtle-pulse {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.1)); }
          50% { transform: scale(1.05); filter: drop-shadow(0 0 30px rgba(99, 102, 241, 0.3)); }
        }
      `}} />
        </div>
    );
};

export default AboutPage;
