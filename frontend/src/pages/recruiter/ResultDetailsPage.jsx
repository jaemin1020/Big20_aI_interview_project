import React, { useState } from 'react';
import './ResultDetailsPage.css';

function ResultDetailsPage({ applicantId, onClose }) {
    // 임시 모의 데이터
    const mockData = {
        name: '김지원',
        job: 'Frontend Developer',
        birthDate: '1995.05.15',
        education: '한국대학교 컴퓨터공학과 학사',
        email: 'jiwon.kim@example.com',
        phone: '010-1234-5678',
        interviewDate: '2026-02-25 14:00',
        duration: '45분 20초',
        questions: [
            { id: 1, text: 'Frontend 개발에서 성능 최적화를 위해 시도했던 경험을 말씀해주세요.', summary: 'React.memo, useMemo를 활용한 리렌더링 최적화, 이미지 Lazy Loading 적용, Lighthouse 점수 개선 경험을 구체적으로 답변함.' },
            { id: 2, text: '팀 프로젝트 중 갈등이 발생했을 때 어떻게 해결했나요?', summary: '커뮤니케이션 부재로 인한 작업 겹침 문제를 주간 스크럼 도입과 명확한 역할 분담으로 해결한 사례를 설명함.' },
            { id: 3, text: '가장 자신 있는 기술 스택과 그 이유는 무엇인가요?', summary: '리액트(React)와 타입스크립트(TypeScript). 정적 타이핑을 통한 런타임 에러 방지 및 컴포넌트 재사용성을 장점으로 꼽음.' },
            { id: 4, text: '최근 기술 트렌드 중 관심 있게 보는 것은 무엇인가요?', summary: 'Next.js의 Server Components와 SSR의 동작 방식, 그리고 웹팩에서 Vite로의 마이그레이션 경험에 대해 언급함.' },
            { id: 5, text: '본인의 단점과 이를 극복하려는 노력은?', summary: '때때로 지나치게 디테일에 집착해 시간을 초과하는 경우가 있어, 작업 기한을 세분화하여 타이머를 두고 작업하는 습관을 기름.' }
        ],
        evaluation: {
            // 직무 역량 상세
            techCriteria: [
                { label: '직무 이해도', score: 70, desc: '해당 직무에 대한 기초 지식과 프로세스를 안정적으로 이해' },
                { label: '직무 경험', score: 60, desc: '실무 경험 면에서 보완이 필요하나, 학습 의지를 통해 충분히 극복 가능한 수준' },
                { label: '직무 해결 역량', score: 75, desc: '주어진 상황에 대해 논리적인 접근 방식을 취함' }
            ],
            // 인성 역량 상세
            personalityCriteria: [
                { label: '의사소통 능력', score: 70, desc: '자신의 생각을 명확하게 전달하며 경청하는 태도를 보임' },
                { label: '성장의지', score: 85, desc: '새로운 기술에 대한 습득 의지가 강함' },
                { label: '책임·성실 태도', score: 90, desc: '맡은 바 임무에 대해 끝까지 완수하려는 책임감이 돋보임' },
                { label: '조직적합성 및 태도', score: 80, desc: '책임감 있는 태도와 조직의 방향성에 부합하는 가치관을 보유' }
            ]
        }
    };

    const [comment, setComment] = useState('');
    const [isCommentSaved, setIsCommentSaved] = useState(false);

    // 질문 확장 상태 (답변 요약 보기)
    const [expandedQuestionIds, setExpandedQuestionIds] = useState([]);
    const [visibleQuestionCount, setVisibleQuestionCount] = useState(3);

    // 탭 상태 (직무 역량 / 인성 역량)
    const [activeTab, setActiveTab] = useState('tech');

    const handleSaveComment = () => {
        if (!comment.trim()) {
            alert('의견 내용을 입력해주세요.');
            return;
        }
        setIsCommentSaved(true);
        alert('관리자 의견이 저장되었습니다.');
    };

    const handleSubmitEvaluation = () => {
        if (comment.trim() && !isCommentSaved) {
            alert('작성 중인 의견을 저장해주세요.');
            return;
        }
        alert('종합 평가 및 면접 결과가 최종 제출되었습니다.');
        onClose();
    };

    const toggleQuestion = (id) => {
        if (expandedQuestionIds.includes(id)) {
            setExpandedQuestionIds(expandedQuestionIds.filter(qId => qId !== id));
        } else {
            setExpandedQuestionIds([...expandedQuestionIds, id]);
        }
    };

    const loadMoreQuestions = () => {
        setVisibleQuestionCount(prev => prev + 3);
    };

    return (
        <div className="result-details-container">
            {/* Header / Title Area */}
            <div className="details-header">
                <div className="header-left">
                    <h2>면접 결과 상세</h2>
                </div>
                <button className="btn-close-page" onClick={onClose}>×</button>
            </div>

            <div className="details-content">
                {/* 2. 지원자 정보 영역 */}
                <section className="info-card">
                    <div className="applicant-profile">
                        <div className="avatar details-avatar">{mockData.name[0]}</div>
                        <div className="details-info-wrap">
                            <h3>{mockData.name} <span className="job-badge">{mockData.job}</span></h3>
                            <div className="details-meta-grid">
                                <div><span className="meta-label">생년월일</span> {mockData.birthDate}</div>
                                <div><span className="meta-label">학력/전공</span> {mockData.education}</div>
                                <div><span className="meta-label">연락처</span> {mockData.phone}</div>
                                <div><span className="meta-label">이메일</span> {mockData.email}</div>
                            </div>
                        </div>
                    </div>
                </section>

                <div className="columns-grid">
                    {/* 좌측 영역 */}
                    <div className="left-column">
                        {/* 3. 면접 내용 영역 */}
                        <section className="section-card">
                            <h4 className="section-title">면접 진행 정보</h4>
                            <div className="interview-meta-info">
                                <div className="info-item">
                                    <span className="label">진행 일시</span>
                                    <span className="value">{mockData.interviewDate}</span>
                                </div>
                                <div className="info-item">
                                    <span className="label">총 소요 시간</span>
                                    <span className="value">{mockData.duration}</span>
                                </div>
                            </div>
                            <div className="interview-actions">
                                <button className="btn-action primary" onClick={() => alert('진행 면접 영상을 재생합니다.')}>면접 영상 다시보기</button>
                                <button className="btn-action secondary" onClick={() => alert('면접 전체 텍스트 내용(STT)을 다운로드/출력합니다.')}>진행 텍스트 출력</button>
                            </div>
                        </section>

                        {/* 4 & 5. 의견 작성 및 저장 */}
                        <section className="section-card">
                            <h4 className="section-title">면접관 / 관리자 의견</h4>
                            <div className="opinion-box">
                                <textarea
                                    placeholder="지원자에 대한 전반적인 의견이나 특이사항을 작성해주세요."
                                    value={comment}
                                    onChange={(e) => {
                                        setComment(e.target.value);
                                        setIsCommentSaved(false);
                                    }}
                                ></textarea>
                                <div className="opinion-actions">
                                    {comment && !isCommentSaved && <span className="warning-text">저장하지 않은 의견이 있습니다.</span>}
                                    <button
                                        className={`btn-save-comment ${isCommentSaved ? 'saved' : ''}`}
                                        onClick={handleSaveComment}
                                    >
                                        {isCommentSaved ? '저장 완료' : '의견 저장'}
                                    </button>
                                </div>
                            </div>
                        </section>

                        {/* 9 & 10. 종합 평가 영역 */}
                        <section className="section-card evaluation-section">
                            <div className="eval-tabs">
                                <button
                                    className={`eval-tab ${activeTab === 'tech' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('tech')}
                                >
                                    직무 역량
                                </button>
                                <button
                                    className={`eval-tab ${activeTab === 'personality' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('personality')}
                                >
                                    인성 역량
                                </button>
                            </div>
                            <div className="eval-content">
                                {activeTab === 'tech' ? (
                                    <div className="eval-pane">
                                        <div className="text-eval-list">
                                            {mockData.evaluation.techCriteria.map((item, idx) => (
                                                <div className="text-eval-row" key={idx}>
                                                    <span className="text-eval-label">
                                                        {item.label} ({item.score}점):
                                                    </span>
                                                    <span className="text-eval-desc">{item.desc}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="eval-pane">
                                        <div className="text-eval-list">
                                            {mockData.evaluation.personalityCriteria.map((item, idx) => (
                                                <div className="text-eval-row" key={idx}>
                                                    <span className="text-eval-label">
                                                        {item.label} ({item.score}점):
                                                    </span>
                                                    <span className="text-eval-desc">{item.desc}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="final-submit-wrapper">
                                <button className="btn-final-submit" onClick={handleSubmitEvaluation}>
                                    종합 평가 최종 제출
                                </button>
                            </div>
                        </section>
                    </div>

                    {/* 우측 분리 영역: 6, 7, 8 질문 및 답변 목록 */}
                    <div className="right-column">
                        <section className="section-card questions-section">
                            <div className="q-header">
                                <h4 className="section-title">면접 질문 내역</h4>
                                <span className="q-count">총 {mockData.questions.length}개 질의</span>
                            </div>

                            <div className="questions-list">
                                {mockData.questions.slice(0, visibleQuestionCount).map((q, idx) => {
                                    const isExpanded = expandedQuestionIds.includes(q.id);
                                    return (
                                        <div className={`question-item ${isExpanded ? 'expanded' : ''}`} key={q.id}>
                                            <div className="q-upper">
                                                <div className="q-num">Q{idx + 1}</div>
                                                <div className="q-text">{q.text}</div>
                                                <button
                                                    className={`btn-toggle-answer ${isExpanded ? 'active' : ''}`}
                                                    onClick={() => toggleQuestion(q.id)}
                                                >
                                                    {isExpanded ? '답변 닫기' : '답변 보기'}
                                                </button>
                                            </div>
                                            {isExpanded && (
                                                <div className="q-summary-box">
                                                    <strong>AI 답변 요약:</strong>
                                                    <p>{q.summary}</p>
                                                </div>
                                            )}
                                        </div>
                                    )
                                })}

                                {/* 8 더보기 버튼 */}
                                {visibleQuestionCount < mockData.questions.length && (
                                    <button className="btn-load-more" onClick={loadMoreQuestions}>
                                        더 많은 질문 보기 ({mockData.questions.length - visibleQuestionCount}개 남음) ▼
                                    </button>
                                )}
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ResultDetailsPage;
