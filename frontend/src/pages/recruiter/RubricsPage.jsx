import React, { useState } from 'react';
import './RubricsPage.css';

function RubricsPage() {
    // 2. 직무 목록 및 루브릭 상태
    const [selectedJob, setSelectedJob] = useState('');
    const [isEditingArea, setIsEditingArea] = useState(false);

    // 3. 평가 목록 상태
    const [evaluationAreas, setEvaluationAreas] = useState([
        { id: 'job_eval', label: '직무평가', checked: true, active: true },
        { id: 'job_exp', label: '직무경험', checked: false, active: false },
        { id: 'comm', label: '소통능력', checked: false, active: false },
        { id: 'attitude', label: '업무태도', checked: false, active: false },
        { id: 'problem_solving', label: '문제해결능력', checked: false, active: false }
    ]);

    // 5. 탭 상태 (평가항목 / 평가레벨)
    const [activeTab, setActiveTab] = useState('items');

    // 6. 평가 항목 상태
    const [selectedItemId, setSelectedItemId] = useState(1);
    const [evaluationItems, setEvaluationItems] = useState([
        // 직무평가
        { id: 1, areaId: 'job_eval', label: '직무 이해 능력', criteria: '해당 직무의 핵심 개념과 프로세스를 정확히 이해하고 있는가?' },
        { id: 2, areaId: 'job_eval', label: '직무 활용 능력', criteria: '습득한 지식을 실무 상황에 적절히 적용하고 활용할 수 있는가?' },
        { id: 3, areaId: 'job_eval', label: '직무 적합성', criteria: '본인의 역량이 해당 직무의 요구사항과 얼마나 일치하는가?' },

        // 직무경험
        { id: 4, areaId: 'job_exp', label: '직무 접근성', criteria: '관련 분야의 프로젝트나 업무에 대한 접근 방식이 논리적인가?' },
        { id: 5, areaId: 'job_exp', label: '직무 해결 능력', criteria: '과거 경험에서 직면한 직무적 난관을 어떻게 해결하였는가?' },
        { id: 6, areaId: 'job_exp', label: '직무 적합성', criteria: '경험을 통해 쌓은 노하우가 우리 팀의 업무 방식과 조화를 이루는가?' },

        // 소통능력
        { id: 7, areaId: 'comm', label: '소통 방법 및 태도', criteria: '상대방의 의견을 경청하고 자신의 의사를 예의 바르게 전달하는가?' },
        { id: 8, areaId: 'comm', label: '전달 명확성', criteria: '복잡한 내용을 간결하고 이해하기 쉽게 설명할 수 있는가?' },
        { id: 9, areaId: 'comm', label: '질문 의도 파악 능력', criteria: '상대방이 질문하는 핵심 의도를 정확히 이해하고 답변하는가?' },

        // 업무태도
        { id: 10, areaId: 'attitude', label: '결과에 대한 책임감', score: 80, label: '결과에 대한 책임감', criteria: '맡은 업무를 끝까지 완수하려는 강한 책임 의식을 가지고 있는가?' },
        { id: 11, areaId: 'attitude', label: '성실성 및 준비도', criteria: '업무에 임하는 자세가 성실하며 필요한 준비가 선제적으로 되어 있는가?' },
        { id: 12, areaId: 'attitude', label: '협업 태도 및 수용 태도', criteria: '팀원과 원활히 협력하며 피드백을 열린 마음으로 수용하는가?' },

        // 문제해결능력
        { id: 13, areaId: 'problem_solving', label: '문제 분석 능력', criteria: '문제의 근본 원인을 논리적으로 파악하고 분석하는 능력이 있는가?' },
        { id: 14, areaId: 'problem_solving', label: '해결 전략 수립 능력', criteria: '효과적인 문제 해결을 위한 최적의 전략과 대안을 제시하는가?' },
        { id: 15, areaId: 'problem_solving', label: '결과 실행 능력', criteria: '수립된 해결책을 실행에 옮겨 실제적인 성과를 만들어내는가?' }
    ]);

    // 7. 평가 레벨 (단일 점수 슬라이더 및 기준 출력)
    const [rubricScore, setRubricScore] = useState(80);
    const assessmentLevels = [
        { label: '최우수', score: 90, desc: '원리 설명이 완벽하며, 상황별 최적의 기술 조합을 리스크까지 고려' },
        { label: '우수', score: 80, desc: '기술의 장단점을 명확히 인지하고 있으며, 선택에 대해 일관된 논리를 유지' },
        { label: '부족', score: 70, desc: '주요 개념은 이해하고 있으나, 대안 기술과의 비교 부족' },
        { label: '미흡', score: 60, desc: '기술 명칭이나 단순 사용법은 아나, 작동 원리나 선택 근거가 모호' }
    ];

    const handleJobChange = (e) => {
        setSelectedJob(e.target.value);
    };

    const handleEditRubric = () => {
        if (!selectedJob) {
            alert('직무를 먼저 선택해주세요.');
            return;
        }
        setIsEditingArea(true);
    };

    const handleAddRubric = () => {
        alert('새 루브릭 추가 화면으로 이동합니다.');
    };

    const toggleArea = (id) => {
        setEvaluationAreas(areas => areas.map(area =>
            area.id === id
                ? { ...area, checked: true, active: true }
                : { ...area, checked: false, active: false }
        ));

        // 해당 영역의 첫 번째 항목을 자동으로 선택
        const firstItemOfArea = evaluationItems.find(item => item.areaId === id);
        if (firstItemOfArea) {
            setSelectedItemId(firstItemOfArea.id);
        }
    };

    const handleSave = () => {
        if (window.confirm('설정된 루브릭 정보를 최종 저장하시겠습니까?')) {
            alert('저장되었습니다.');
            setIsEditingArea(false); // 8. 저장 후 설정 영역 비활성화
        }
    };

    const selectedItem = evaluationItems.find(item => item.id === selectedItemId);

    return (
        <div className="rubrics-container">
            {/* 2. 직무 목록 선택 영역 */}
            <section className="rubric-section rubric-top-control">
                <div className="control-group">
                    <label>적용 직무</label>
                    <select value={selectedJob} onChange={handleJobChange} className="job-dropdown">
                        <option value="">직무 유형 선택</option>
                        <option value="frontend">Frontend Developer</option>
                        <option value="backend">Backend Developer</option>
                        <option value="design">UI/UX Designer</option>
                    </select>
                </div>
                <div className="button-group">
                    <button className="btn-rubric-add" onClick={handleAddRubric}>Rubrics 추가</button>
                    <button className="btn-rubric-edit" onClick={handleEditRubric}>수정</button>
                </div>
            </section>

            {isEditingArea && (
                <div className="rubric-edit-layout">
                    <div className="rubric-sidebar">
                        {/* 3. 평가 목록 영역 */}
                        <section className="rubric-section evaluation-list-section">
                            <h4 className="section-title">평가 영역 관리</h4>
                            <div className="area-items">
                                {evaluationAreas.map(area => (
                                    <div key={area.id} className="area-item">
                                        <label className="checkbox-wrap">
                                            <input
                                                type="radio"
                                                name="evaluationArea"
                                                checked={area.checked}
                                                onChange={() => toggleArea(area.id)}
                                            />
                                            <span className="check-label">{area.label}</span>
                                        </label>
                                        <span className={`status-badge ${area.active ? 'active' : ''}`}>
                                            {area.active ? '활성' : '비활성'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>

                    <div className="rubric-main">
                        {/* 4 & 5. 직무 평가 기준 설정 영역 / 탭 */}
                        <section className="rubric-section criteria-config-section">
                            <div className="tab-header">
                                <button
                                    className={`tab-btn ${activeTab === 'items' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('items')}
                                >
                                    평가 항목 관리
                                </button>
                                <button
                                    className={`tab-btn ${activeTab === 'levels' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('levels')}
                                >
                                    평가 레벨 설정
                                </button>
                            </div>

                            <div className="tab-content">
                                {activeTab === 'items' ? (
                                    <div className="items-management">
                                        {/* 6. 평가 항목 상세 관리 */}
                                        <div className="items-list">
                                            {evaluationItems
                                                .filter(item => evaluationAreas.find(area => area.id === item.areaId)?.checked)
                                                .map(item => (
                                                    <div
                                                        key={item.id}
                                                        className={`item-row ${selectedItemId === item.id ? 'selected' : ''}`}
                                                        onClick={() => setSelectedItemId(item.id)}
                                                    >
                                                        <span className="item-label">{item.label}</span>
                                                        <div className="item-actions">
                                                            <button className="btn-mini">수정</button>
                                                            <button className="btn-mini delete">삭제</button>
                                                        </div>
                                                    </div>
                                                ))}
                                        </div>
                                        {selectedItem && evaluationAreas.find(area => area.id === selectedItem.areaId)?.checked && (
                                            <div className="item-detail-view">
                                                <h5>평가 기준 가이드</h5>
                                                <textarea
                                                    className="criteria-textarea"
                                                    value={selectedItem.criteria}
                                                    onChange={(e) => {
                                                        const newItems = evaluationItems.map(it =>
                                                            it.id === selectedItemId ? { ...it, criteria: e.target.value } : it
                                                        );
                                                        setEvaluationItems(newItems);
                                                    }}
                                                />
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="levels-management">
                                        {/* 7. 평가 레벨 출력 영역 */}
                                        <div className="single-slider-box">
                                            <div className="slider-header">
                                                <span className="current-set-label">기준 점수 설정</span>
                                                <div className="manual-score-input-wrap">
                                                    <input
                                                        type="number"
                                                        min="0" max="100"
                                                        value={rubricScore}
                                                        onChange={(e) => {
                                                            let val = parseInt(e.target.value);
                                                            if (isNaN(val)) val = 0;
                                                            if (val > 100) val = 100;
                                                            if (val < 0) val = 0;
                                                            setRubricScore(val);
                                                        }}
                                                        className="score-number-input"
                                                    />
                                                    <span className="unit">점</span>
                                                </div>
                                            </div>
                                            <input
                                                type="range"
                                                min="0" max="100"
                                                value={rubricScore}
                                                onChange={(e) => setRubricScore(parseInt(e.target.value))}
                                                className="score-slider large"
                                            />
                                        </div>

                                        <div className="level-criteria-list">
                                            {assessmentLevels.map((lvl, idx) => (
                                                <div key={idx} className={`criteria-card ${rubricScore >= lvl.score ? 'highlight' : ''}`}>
                                                    <div className="criteria-header">
                                                        <span className="lvl-name">{lvl.label} ({lvl.score}점)</span>
                                                    </div>
                                                    <p className="lvl-desc">{lvl.desc}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* 8. 저장 버튼 */}
                            <div className="save-footer">
                                <button className="btn-save-rubric" onClick={handleSave}>루브릭 최종 저장</button>
                            </div>
                        </section>
                    </div>
                </div>
            )}
        </div>
    );
}

export default RubricsPage;
