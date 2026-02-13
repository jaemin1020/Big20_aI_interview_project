import { useState } from 'react';
import './JobPostingCreatePage.css';

function JobPostingCreatePage({ user, onBack, embedded = false }) {
    const [formData, setFormData] = useState({
        title: '',
        companyName: 'Big20 AI',
        position: '',
        employmentType: '',
        recruitmentStartDate: '',
        recruitmentEndDate: '',
        description: '',
        interviewType: 'ai',
        questionGenerationType: 'auto',
        difficulty: 'medium',
        questionCount: '10',
        rubric: '',
        technicalWeight: 40,
        personalityWeight: 30,
        otherWeight: 30,
        requiredDocuments: {
            resume: false,
            coverLetter: false,
            portfolio: false,
            certificate: false
        }
    });

    const [showConfirmModal, setShowConfirmModal] = useState(false);

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleDocumentToggle = (doc) => {
        setFormData(prev => ({
            ...prev,
            requiredDocuments: {
                ...prev.requiredDocuments,
                [doc]: !prev.requiredDocuments[doc]
            }
        }));
    };

    const handleWeightChange = (field, value) => {
        const numValue = parseInt(value) || 0;
        setFormData(prev => ({ ...prev, [field]: numValue }));
    };

    const getTotalWeight = () => {
        return formData.technicalWeight + formData.personalityWeight + formData.otherWeight;
    };

    const handleTempSave = () => {
        alert('임시 저장되었습니다.');
        console.log('임시 저장:', formData);
    };

    const handleSubmit = () => {
        const total = getTotalWeight();
        if (total !== 100) {
            alert(`평가 비율의 합이 100%가 되어야 합니다. (현재: ${total}%)`);
            return;
        }

        if (!formData.title || !formData.position || !formData.employmentType) {
            alert('필수 항목을 모두 입력해주세요.');
            return;
        }

        setShowConfirmModal(true);
    };

    const confirmSubmit = () => {
        console.log('공고 등록:', formData);
        alert('공고가 성공적으로 등록되었습니다!');
        setShowConfirmModal(false);
        onBack();
    };

    const handleCancel = () => {
        if (confirm('입력한 내용이 저장되지 않습니다. 취소하시겠습니까?')) {
            onBack();
        }
    };

    return (
        <div className={`job-posting-create-container ${embedded ? 'embedded' : ''}`}>
            {/* 관리자 정보 영역 - embedded 모드에서는 숨김 */}
            {!embedded && (
                <div className="admin-info-section">
                    <div className="admin-avatar">
                        {(user?.full_name || '관리자')[0]}
                    </div>
                    <div className="admin-details">
                        <p className="admin-company">Big20 AI</p>
                        <p className="admin-name">{user?.full_name || '관리자'}</p>
                    </div>
                </div>
            )}

            <div className="form-container">
                {/* 페이지 제목 - embedded 모드에서는 숨김 */}
                {!embedded && <h1 className="page-title">공고 등록</h1>}

                {/* 공고 정보 입력 영역 */}
                <section className="form-section">
                    <h2 className="section-title">공고 정보</h2>

                    <div className="form-group">
                        <label className="form-label">공고 제목 <span className="required">*</span></label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="채용 공고명을 입력하세요"
                            value={formData.title}
                            onChange={(e) => handleInputChange('title', e.target.value)}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">회사명</label>
                        <input
                            type="text"
                            className="form-input"
                            value={formData.companyName}
                            onChange={(e) => handleInputChange('companyName', e.target.value)}
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">직무 <span className="required">*</span></label>
                            <select
                                className="form-select"
                                value={formData.position}
                                onChange={(e) => handleInputChange('position', e.target.value)}
                            >
                                <option value="">선택하세요</option>
                                <option value="frontend">Frontend Developer</option>
                                <option value="backend">Backend Developer</option>
                                <option value="fullstack">Full Stack Developer</option>
                                <option value="devops">DevOps Engineer</option>
                                <option value="data">Data Scientist</option>
                                <option value="ai">AI/ML Engineer</option>
                                <option value="designer">UI/UX Designer</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label className="form-label">채용 유형 <span className="required">*</span></label>
                            <select
                                className="form-select"
                                value={formData.employmentType}
                                onChange={(e) => handleInputChange('employmentType', e.target.value)}
                            >
                                <option value="">선택하세요</option>
                                <option value="regular">정규직</option>
                                <option value="contract">계약직</option>
                                <option value="intern">인턴</option>
                                <option value="parttime">파트타임</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">모집 시작일</label>
                            <input
                                type="date"
                                className="form-input date-input"
                                value={formData.recruitmentStartDate}
                                onChange={(e) => handleInputChange('recruitmentStartDate', e.target.value)}
                                max="9999-12-31"
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">모집 종료일</label>
                            <input
                                type="date"
                                className="form-input date-input"
                                value={formData.recruitmentEndDate}
                                onChange={(e) => handleInputChange('recruitmentEndDate', e.target.value)}
                                max="9999-12-31"
                            />
                        </div>
                    </div>
                </section>

                {/* 공고 세부 내용 */}
                <section className="form-section">
                    <h2 className="section-title">공고 세부 내용</h2>
                    <div className="form-group">
                        <label className="form-label">상세 내용</label>

                        {/* 에디터 툴바 */}
                        <div className="editor-toolbar">
                            <button
                                type="button"
                                className="toolbar-btn"
                                onClick={() => {
                                    const textarea = document.querySelector('.form-textarea');
                                    const start = textarea.selectionStart;
                                    const end = textarea.selectionEnd;
                                    const text = formData.description;
                                    const selectedText = text.substring(start, end);
                                    const newText = text.substring(0, start) + '**' + selectedText + '**' + text.substring(end);
                                    handleInputChange('description', newText);
                                }}
                                title="굵게"
                            >
                                <strong>B</strong>
                            </button>
                            <button
                                type="button"
                                className="toolbar-btn"
                                onClick={() => {
                                    const textarea = document.querySelector('.form-textarea');
                                    const start = textarea.selectionStart;
                                    const end = textarea.selectionEnd;
                                    const text = formData.description;
                                    const selectedText = text.substring(start, end);
                                    const newText = text.substring(0, start) + '*' + selectedText + '*' + text.substring(end);
                                    handleInputChange('description', newText);
                                }}
                                title="기울임"
                            >
                                <em>I</em>
                            </button>
                            <div className="toolbar-divider"></div>
                            <button
                                type="button"
                                className="toolbar-btn"
                                onClick={() => {
                                    const textarea = document.querySelector('.form-textarea');
                                    const start = textarea.selectionStart;
                                    const text = formData.description;
                                    const beforeText = text.substring(0, start);
                                    const afterText = text.substring(start);
                                    const newText = beforeText + '\n• ' + afterText;
                                    handleInputChange('description', newText);
                                }}
                                title="목록"
                            >
                                • 목록
                            </button>
                            <button
                                type="button"
                                className="toolbar-btn"
                                onClick={() => {
                                    const textarea = document.querySelector('.form-textarea');
                                    const start = textarea.selectionStart;
                                    const end = textarea.selectionEnd;
                                    const text = formData.description;
                                    const selectedText = text.substring(start, end);
                                    const newText = text.substring(0, start) + '## ' + selectedText + text.substring(end);
                                    handleInputChange('description', newText);
                                }}
                                title="제목"
                            >
                                H
                            </button>
                        </div>

                        <textarea
                            className="form-textarea"
                            rows="15"
                            placeholder="채용 공고 상세 내용을 작성하세요&#10;&#10;• 주요 업무&#10;• 자격 요건&#10;• 우대 사항&#10;• 근무 조건 등"
                            value={formData.description}
                            onChange={(e) => handleInputChange('description', e.target.value)}
                        />
                    </div>
                </section>

                {/* 면접 유형 설정 */}
                <section className="form-section">
                    <h2 className="section-title">면접 유형 설정</h2>

                    <div className="form-group">
                        <label className="form-label">면접 유형</label>
                        <div className="radio-group">
                            <label className="radio-label">
                                <input
                                    type="radio"
                                    name="interviewType"
                                    value="ai"
                                    checked={formData.interviewType === 'ai'}
                                    onChange={(e) => handleInputChange('interviewType', e.target.value)}
                                />
                                <span>AI 면접</span>
                            </label>
                            <label className="radio-label">
                                <input
                                    type="radio"
                                    name="interviewType"
                                    value="video"
                                    checked={formData.interviewType === 'video'}
                                    onChange={(e) => handleInputChange('interviewType', e.target.value)}
                                />
                                <span>화상 면접</span>
                            </label>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">질문 생성 방식</label>
                            <select
                                className="form-select"
                                value={formData.questionGenerationType}
                                onChange={(e) => handleInputChange('questionGenerationType', e.target.value)}
                            >
                                <option value="auto">자동 생성</option>
                                <option value="manual">수동 입력</option>
                                <option value="mixed">혼합</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label className="form-label">면접 난이도</label>
                            <select
                                className="form-select"
                                value={formData.difficulty}
                                onChange={(e) => handleInputChange('difficulty', e.target.value)}
                            >
                                <option value="easy">Easy</option>
                                <option value="medium">Medium</option>
                                <option value="hard">Hard</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label className="form-label">질문 개수</label>
                            <select
                                className="form-select"
                                value={formData.questionCount}
                                onChange={(e) => handleInputChange('questionCount', e.target.value)}
                            >
                                <option value="5">5개</option>
                                <option value="10">10개</option>
                                <option value="15">15개</option>
                                <option value="20">20개</option>
                            </select>
                        </div>
                    </div>
                </section>

                {/* 평가 기준 설정 */}
                <section className="form-section">
                    <h2 className="section-title">평가 기준 설정</h2>

                    <div className="form-group">
                        <label className="form-label">Rubrics 선택</label>
                        <select
                            className="form-select"
                            value={formData.rubric}
                            onChange={(e) => handleInputChange('rubric', e.target.value)}
                        >
                            <option value="">선택하세요</option>
                            <option value="developer">개발자 표준 평가</option>
                            <option value="designer">디자이너 표준 평가</option>
                            <option value="pm">PM 표준 평가</option>
                            <option value="custom">커스텀 평가</option>
                        </select>
                    </div>

                    <div className="weight-container">
                        <div className="weight-item">
                            <label className="form-label">직무 역량 평가 비율</label>
                            <div className="weight-input-group">
                                <input
                                    type="number"
                                    className="form-input weight-input"
                                    min="0"
                                    max="100"
                                    value={formData.technicalWeight}
                                    onChange={(e) => handleWeightChange('technicalWeight', e.target.value)}
                                />
                                <span className="weight-unit">%</span>
                            </div>
                        </div>

                        <div className="weight-item">
                            <label className="form-label">인성 역량 평가 비율</label>
                            <div className="weight-input-group">
                                <input
                                    type="number"
                                    className="form-input weight-input"
                                    min="0"
                                    max="100"
                                    value={formData.personalityWeight}
                                    onChange={(e) => handleWeightChange('personalityWeight', e.target.value)}
                                />
                                <span className="weight-unit">%</span>
                            </div>
                        </div>

                        <div className="weight-item">
                            <label className="form-label">기타 평가 비율</label>
                            <div className="weight-input-group">
                                <input
                                    type="number"
                                    className="form-input weight-input"
                                    min="0"
                                    max="100"
                                    value={formData.otherWeight}
                                    onChange={(e) => handleWeightChange('otherWeight', e.target.value)}
                                />
                                <span className="weight-unit">%</span>
                            </div>
                        </div>

                        <div className={`weight-total ${getTotalWeight() === 100 ? 'valid' : 'invalid'}`}>
                            총합: {getTotalWeight()}%
                        </div>
                    </div>
                </section>

                {/* 제출 서류 설정 */}
                <section className="form-section">
                    <h2 className="section-title">제출 서류 설정</h2>

                    <div className="checkbox-group">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={formData.requiredDocuments.resume}
                                onChange={() => handleDocumentToggle('resume')}
                            />
                            <span>이력서</span>
                        </label>

                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={formData.requiredDocuments.coverLetter}
                                onChange={() => handleDocumentToggle('coverLetter')}
                            />
                            <span>자기소개서</span>
                        </label>

                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={formData.requiredDocuments.portfolio}
                                onChange={() => handleDocumentToggle('portfolio')}
                            />
                            <span>포트폴리오</span>
                        </label>

                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={formData.requiredDocuments.certificate}
                                onChange={() => handleDocumentToggle('certificate')}
                            />
                            <span>증빙 서류</span>
                        </label>
                    </div>
                </section>

                {/* 버튼 영역 */}
                <div className="button-container">
                    <button className="btn btn-cancel" onClick={handleCancel}>
                        취소
                    </button>
                    <button className="btn btn-temp-save" onClick={handleTempSave}>
                        임시 저장
                    </button>
                    <button className="btn btn-submit" onClick={handleSubmit}>
                        공고 등록
                    </button>
                </div>
            </div>

            {/* 확인 모달 */}
            {showConfirmModal && (
                <div className="modal-overlay" onClick={() => setShowConfirmModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h3 className="modal-title">공고 등록 확인</h3>
                        <p className="modal-message">입력한 내용으로 공고를 등록하시겠습니까?</p>
                        <div className="modal-buttons">
                            <button className="btn btn-cancel" onClick={() => setShowConfirmModal(false)}>
                                취소
                            </button>
                            <button className="btn btn-submit" onClick={confirmSubmit}>
                                확인
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default JobPostingCreatePage;
