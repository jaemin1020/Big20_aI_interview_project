import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import PersonalizedInterviewSystemImage from '../../assets/PersonalizedInterviewSystem.png';
import HRIntegrationSolutionImage from '../../assets/HRIntegrationSolution.png';
import AnalysisImage from '../../assets/analysis.png';
import FutureExpansionImage from '../../assets/Future Expansion.png';

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
            <div style={{ maxWidth: '1000px', width: '100%', display: 'flex', flexDirection: 'column', gap: '3rem' }}>

                {/* Section 1: BictorView 브랜드 소개 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out both' }}>
                    <GlassCard style={{ display: 'flex', gap: '2rem', padding: '3rem', alignItems: 'center' }}>
                        <div style={{ flex: 1.5 }}>
                            <h2 style={{ fontSize: '2.2rem', fontWeight: '800', marginBottom: '1rem', fontFamily: "'Outfit', sans-serif", color: 'var(--primary)' }}>
                                BictorView는 무엇인가?
                            </h2>
                            <div style={{ fontSize: '1.1rem', lineHeight: '1.8', color: 'var(--text-main)', opacity: 0.9 }}>
                                <p style={{ marginBottom: '1rem' }}>
                                    <strong style={{ color: 'var(--primary)', fontWeight: '700' }}>BictorView</strong>는 AI 기반 <span style={{ background: 'rgba(99, 102, 241, 0.1)', padding: '0 4px', borderRadius: '4px', color: 'var(--primary-light)' }}>멀티모달 면접 분석</span> 기술을 활용하여 지원자의 역량을 객관적으로 평가하는 지능형 인터뷰 플랫폼입니다.
                                </p>
                                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ color: 'var(--success)' }}>✔</span>
                                        <span>공통 질문 중심의 기존 모의면접 한계 극복</span>
                                    </li>
                                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ color: 'var(--success)' }}>✔</span>
                                        <span>기업 인재상과 지원자 경험 데이터 결합</span>
                                    </li>
                                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ color: 'var(--success)' }}>✔</span>
                                        <span>개인 맞춤형 심층 면접 환경 제공</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                        <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '24px', padding: '2rem', textAlign: 'center' }}>
                            <img src="/logo.png" alt="BictorView Logo" style={{ width: '100%', height: 'auto', animation: 'subtle-pulse 4s infinite ease-in-out' }} />
                            <p style={{ marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>브랜드 로고</p>
                        </div>
                    </GlassCard>
                </section>

                {/* Section 2: 개인 맞춤형 면접 시스템 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.2s both' }}>
                    <GlassCard style={{
                        padding: '0',
                        display: 'flex',
                        position: 'relative',
                        overflow: 'hidden',
                        alignItems: 'center',
                        minHeight: '400px' // 높이 확보
                    }}>
                        {/* Text Content (Left Side) - 마스킹 되지 않도록 z-index 상위 배치 */}
                        <div style={{
                            flex: 1,
                            padding: '3rem',
                            zIndex: 2,
                            maxWidth: '60%', // 텍스트 영역 제한
                            position: 'relative'
                        }}>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <h2 style={{ fontSize: '2.2rem', fontWeight: '800', marginBottom: '0.8rem', fontFamily: "'Outfit', sans-serif" }}>
                                    개인 맞춤형 면접 시스템
                                </h2>
                                <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
                                    지원자의 이력·경험·답변패턴을 분석하여 <br /> 개인 맞춤 질문을 생성합니다.
                                </p>
                            </div>

                            <div style={{ display: 'flex', gap: '1rem' }}>
                                {[
                                    { icon: '📄', title: '이력서 기반', desc: '이력서 분석 질문 생성' },
                                    { icon: '🔗', title: '꼬리 질문', desc: '답변에 따른 심층 탐색' },
                                    { icon: '🧩', title: '성향 분석', desc: '지원자 성향 파악' }
                                ].map((item, i) => (
                                    <div key={i} className="feature-card" style={{ padding: '1rem' }}>
                                        <div style={{ fontSize: '1.2rem', marginBottom: '0.4rem' }}>{item.icon}</div>
                                        <h4 style={{ fontSize: '0.9rem', fontWeight: '700', marginBottom: '0.2rem', color: 'var(--text-main)' }}>{item.title}</h4>
                                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>{item.desc}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Integrated Image Area (Right Side Overlay) - 자연스럽게 섞이도록 처리 */}
                        <div style={{
                            position: 'absolute',
                            right: 0,
                            top: 0,
                            width: '60%', // 우측 60% 차지
                            height: '100%',
                            zIndex: 1,
                            maskImage: 'linear-gradient(to right, transparent 0%, black 40%)', // 왼쪽에서 오른쪽으로 나타나는 마스크
                            WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 40%)',
                            pointerEvents: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end'
                        }}>
                            <img
                                src={PersonalizedInterviewSystemImage}
                                alt="개인 맞춤형 면접 시스템"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover', // 꽉 차게 렌더링
                                    objectPosition: 'left center', // 이미지의 왼쪽 부분이 잘리지 않고 이어지도록
                                    opacity: 0.95
                                }}
                            />
                        </div>
                    </GlassCard>
                </section>

                {/* Section 3: 기업 맞춤형 HR 연동 솔루션 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.4s both' }}>
                    <GlassCard style={{
                        padding: '0',
                        display: 'flex',
                        position: 'relative',
                        overflow: 'hidden',
                        alignItems: 'center',
                        minHeight: '400px'
                    }}>
                        <div style={{
                            flex: 1,
                            padding: '3rem',
                            zIndex: 2,
                            maxWidth: '60%',
                            position: 'relative'
                        }}>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <h2 style={{ fontSize: '2.2rem', fontWeight: '800', marginBottom: '1rem', fontFamily: "'Outfit', sans-serif" }}>
                                    기업 맞춤형 HR 연동 솔루션
                                </h2>
                                <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
                                    기업 채용 시스템과의 Seamless한 연동 지원
                                </p>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                                {[
                                    { icon: '🔄', title: 'ATS 연동', desc: '기존 채용 시스템과 완벽 연동' },
                                    { icon: '🎯', title: '인재상 최적화', desc: '기업별 맞춤 평가 기준 설정' },
                                    { icon: '⚡', title: '자동 선별', desc: '대규모 지원자 AI 자동 스크리닝' },
                                    { icon: '📈', title: '데이터 분석', desc: '채용 전형별 상세 데이터 제공' }
                                ].map((item, i) => (
                                    <div key={i} className="feature-card" style={{ padding: '1rem' }}>
                                        <div style={{ fontSize: '1.2rem', marginBottom: '0.4rem', background: 'var(--primary-light)', width: '36px', height: '36px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.4rem auto' }}>{item.icon}</div>
                                        <h4 style={{ fontSize: '0.9rem', fontWeight: '700', marginBottom: '0.2rem', color: 'var(--text-main)' }}>{item.title}</h4>
                                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>{item.desc}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Side Overlay for Section 3 */}
                        <div style={{
                            position: 'absolute',
                            right: 0,
                            top: 0,
                            width: '60%',
                            height: '100%',
                            zIndex: 1,
                            maskImage: 'linear-gradient(to right, transparent 0%, black 40%)',
                            WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 40%)',
                            pointerEvents: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end'
                        }}>
                            <img
                                src={HRIntegrationSolutionImage}
                                alt="기업 맞춤형 HR 연동 솔루션"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover',
                                    objectPosition: 'center',
                                    opacity: 0.95
                                }}
                            />
                        </div>
                    </GlassCard>
                </section>

                {/* Section 4: AI 멀티모달 역량 분석 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.6s both' }}>
                    <GlassCard style={{
                        padding: '0',
                        display: 'flex',
                        position: 'relative',
                        overflow: 'hidden',
                        alignItems: 'center',
                        minHeight: '400px'
                    }}>
                        <div style={{
                            flex: 1,
                            padding: '3rem',
                            zIndex: 2,
                            maxWidth: '60%',
                            position: 'relative'
                        }}>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <h2 style={{ fontSize: '2.2rem', fontWeight: '800', marginBottom: '1rem', fontFamily: "'Outfit', sans-serif" }}>
                                    AI 멀티모달 역량 분석
                                </h2>
                                <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
                                    단순 답변 평가가 아닌 다양한 신호를 종합 분석합니다.
                                </p>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                                {[
                                    {
                                        icon: '👁️',
                                        title: '비언어 분석',
                                        desc: '표정, 시선, 태도 등 비언어적 요소 정밀 분석'
                                    },
                                    {
                                        icon: '🎙️',
                                        title: '음성 분석',
                                        desc: '발화 속도, 음성 떨림 등 목소리 특징 분석'
                                    },
                                    {
                                        icon: '📝',
                                        title: '언어 분석',
                                        desc: '답변의 논리성 및 직무 적합도 키워드 분석'
                                    }
                                ].map((item, i) => (
                                    <div key={i} className="feature-card" style={{ padding: '1rem' }}>
                                        <div style={{ fontSize: '1.2rem', marginBottom: '0.4rem' }}>{item.icon}</div>
                                        <h4 style={{ fontSize: '0.9rem', fontWeight: '700', marginBottom: '0.2rem', color: 'var(--text-main)' }}>{item.title}</h4>
                                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>{item.desc}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Side Overlay for Section 4 */}
                        <div style={{
                            position: 'absolute',
                            right: 0,
                            top: 0,
                            width: '60%',
                            height: '100%',
                            zIndex: 1,
                            maskImage: 'linear-gradient(to right, transparent 0%, black 40%)',
                            WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 40%)',
                            pointerEvents: 'none',
                        }}>
                            <img
                                src={AnalysisImage}
                                alt="AI 멀티모달 역량 분석"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover',
                                    objectPosition: 'center',
                                    opacity: 0.95
                                }}
                            />
                        </div>
                    </GlassCard>
                </section>

                {/* Section 5: BictorView 미래 확장 방향 */}
                <section style={{ animation: 'fade-in-up 0.8s ease-out 0.8s both', marginBottom: '3rem' }}>
                    <GlassCard style={{
                        padding: '0',
                        display: 'flex',
                        position: 'relative',
                        overflow: 'hidden',
                        alignItems: 'center',
                        minHeight: '400px'
                    }}>
                        <div style={{
                            flex: 1,
                            padding: '3rem',
                            zIndex: 2,
                            maxWidth: '60%',
                            position: 'relative'
                        }}>
                            <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '1.2rem', fontFamily: "'Outfit', sans-serif" }}>
                                BictorView 미래 확장 방향
                            </h2>
                            <p style={{ fontSize: '1.1rem', marginBottom: '2.5rem', opacity: 0.8 }}>
                                BictorView는 AI 면접 플랫폼을 넘어 지능형 채용 평가 솔루션으로 확장됩니다.
                            </p>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.2rem' }}>
                                {[
                                    { icon: '🤖', title: '기업 맞춤 AI 면접관', color: '#818cf8' },
                                    { icon: '🎯', title: '인재상 기반 맞춤', color: '#f472b6' },
                                    { icon: '📈', title: '채용 데이터 분석', color: '#34d399' },
                                    { icon: '🔗', title: 'HR 시스템 통합', color: '#60a5fa' }
                                ].map((item, i) => (
                                    <div key={i} className="future-box" style={{
                                        background: 'rgba(255,255,255,0.03)',
                                        padding: '1.5rem',
                                        borderRadius: '20px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '0.8rem',
                                        textAlign: 'center',
                                        border: '1px solid rgba(255,255,255,0.08)',
                                        transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                        cursor: 'default',
                                        position: 'relative',
                                        overflow: 'hidden'
                                    }}>
                                        <div style={{
                                            position: 'absolute',
                                            top: '-20%',
                                            left: '-20%',
                                            width: '140%',
                                            height: '140%',
                                            background: `radial-gradient(circle at center, ${item.color}15 0%, transparent 60%)`,
                                            opacity: 0,
                                            transition: 'opacity 0.3s ease',
                                            zIndex: 0
                                        }} className="glow-bg" />

                                        <div style={{
                                            fontSize: '2.5rem',
                                            marginBottom: '0.2rem',
                                            filter: `drop-shadow(0 0 10px ${item.color}40)`,
                                            zIndex: 1
                                        }} className="future-icon">
                                            {item.icon}
                                        </div>
                                        <div style={{ zIndex: 1 }}>
                                            <h4 style={{
                                                fontSize: '1rem',
                                                fontWeight: '700',
                                                color: 'var(--text-main)',
                                                marginBottom: '0.3rem',
                                                wordBreak: 'keep-all'
                                            }}>
                                                {item.title}
                                            </h4>
                                            <p style={{
                                                fontSize: '0.75rem',
                                                color: 'var(--text-muted)',
                                                fontFamily: "'Outfit', sans-serif",
                                                letterSpacing: '0.5px',
                                                opacity: 0.8
                                            }}>
                                                {item.sub}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Side Overlay for Section 5 */}
                        <div style={{
                            position: 'absolute',
                            right: 0,
                            top: 0,
                            width: '60%',
                            height: '100%',
                            zIndex: 1,
                            maskImage: 'linear-gradient(to right, transparent 0%, black 40%)',
                            WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 40%)',
                            pointerEvents: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end'
                        }}>
                            <img
                                src={FutureExpansionImage}
                                alt="Future Expansion"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover',
                                    opacity: 0.9,
                                    objectPosition: 'center',
                                }}
                            />
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
        .feature-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            cursor: default;
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            border-color: var(--primary);
        }
        body.dark-theme .feature-card {
            background: rgba(30, 41, 59, 0.8);
            border-color: rgba(255, 255, 255, 0.1);
        }
        body.dark-theme .feature-card:hover {
            border-color: var(--primary);
            background: rgba(30, 41, 59, 0.95);
        }

        .future-box:hover {
          transform: translateY(-8px);
          background: rgba(255, 255, 255, 0.1);
          border-color: var(--primary);
          box-shadow: 0 15px 30px -10px rgba(0, 0, 0, 0.2);
        }
        .future-box:hover .glow-bg {
            opacity: 1 !important;
        }
        .future-box:hover .future-icon {
            transform: scale(1.1) rotate(5deg);
            transition: transform 0.4s ease;
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
