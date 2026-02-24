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
        { id: 1, areaId: 'job_eval', label: '직무 이해도', criteria: '해당 직무에 대한 기초 지식과 프로세스를 안정적으로 이해하고 있는가?' },
        { id: 2, areaId: 'job_exp', label: '직무 경험', criteria: '관련 분야에서의 실무 경험이 충분하며 즉시 전력감이 될 수 있는가?' },
        { id: 3, areaId: 'problem_solving', label: '문제 해결 능력', criteria: '예상치 못한 상황에서 논리적이고 효율적인 대안을 제시하는가?' },
        { id: 4, areaId: 'comm', label: '커뮤니케이션 기술', criteria: '복잡한 기술적 개념을 비전공자도 이해하기 쉽게 설명할 수 있는가?' },
        { id: 5, areaId: 'attitude', label: '협업 태도', criteria: '팀의 목표를 위해 개인의 성취보다 팀워크를 우선시하는가?' }
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
