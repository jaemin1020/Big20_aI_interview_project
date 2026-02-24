import React, { useState } from 'react';
import './ResultManagementPage.css';

const mockResults = [
    { id: 1, name: '김지원', job: 'Frontend Developer', interviewCode: 'INT-2026-001', evaluationStatus: '평가대기', result: '-', interviewDate: '2026-02-25T14:00:00' },
    { id: 2, name: '이민수', job: 'Backend Developer', interviewCode: 'INT-2026-001', evaluationStatus: '평가완료', result: '최종합격', interviewDate: '2026-02-24T18:00:00' },
    { id: 3, name: '박서연', job: 'UI/UX Designer', interviewCode: 'INT-2026-002', evaluationStatus: '평가완료', result: '불합격', interviewDate: '2026-02-20T10:00:00' },
    { id: 4, name: '최현우', job: 'DevOps Engineer', interviewCode: 'INT-2026-003', evaluationStatus: '평가완료', result: '예비합격', interviewDate: '2026-02-26T15:30:00' },
];

function ResultManagementPage() {
    const [resultsData, setResultsData] = useState(mockResults);
    const [filteredResults, setFilteredResults] = useState(mockResults);

    // 검색 상태
    const [searchJob, setSearchJob] = useState('');
    const [searchCode, setSearchCode] = useState('');
    const [searchResult, setSearchResult] = useState(''); // 예비합격, 불합격, 최종합격
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const [selectedIds, setSelectedIds] = useState([]);

    // 모달 상태
    const [showDeleteModal, setShowDeleteModal] = useState(false);

    // 결과 수정 모달 상태
    const [showEditResultModal, setShowEditResultModal] = useState(false);
    const [editingItem, setEditingItem] = useState(null);
    const initialScores = {
        jobUnderstanding: 0,
        jobExperience: 0,
        jobProblemSolving: 0,
        communication: 0,
        growthWill: 0,
        responsibility: 0,
        cultureFit: 0
    };
    const [editScores, setEditScores] = useState(initialScores);
    const [originalScores, setOriginalScores] = useState(initialScores);
    const [editFinalResult, setEditFinalResult] = useState('');
    const [originalFinalResult, setOriginalFinalResult] = useState('');

    const handleSearch = () => {
        let result = resultsData;

        if (searchJob) {
            result = result.filter(item => item.job.toLowerCase().includes(searchJob.toLowerCase()));
        }
        if (searchCode) {
            result = result.filter(item => item.interviewCode.toLowerCase().includes(searchCode.toLowerCase()));
        }
        if (searchResult) {
            result = result.filter(item => item.result === searchResult);
        }
        if (startDate && endDate) {
            result = result.filter(item => {
                const date = item.interviewDate.split('T')[0];
                return date >= startDate && date <= endDate;
            });
        }

        setFilteredResults(result);
        setSelectedIds([]);
    };

    const handleReset = () => {
        setSearchJob('');
        setSearchCode('');
        setSearchResult('');
        setStartDate('');
        setEndDate('');
        setFilteredResults(resultsData);
        setSelectedIds([]);
    };

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedIds(filteredResults.map(item => item.id));
        } else {
            setSelectedIds([]);
        }
    };

    const handleSelect = (id) => {
        if (selectedIds.includes(id)) {
            setSelectedIds(selectedIds.filter(itemId => itemId !== id));
        } else {
            setSelectedIds([...selectedIds, id]);
        }
    };

    const requestDelete = () => {
        if (selectedIds.length === 0) {
            alert('삭제할 면접 결과 데이터를 선택해주세요.');
            return;
        }
        setShowDeleteModal(true);
    };

    const confirmDelete = () => {
        const newData = resultsData.filter(item => !selectedIds.includes(item.id));
        setResultsData(newData);
        setFilteredResults(newData.filter(item => filteredResults.some(fi => fi.id === item.id && !selectedIds.includes(item.id))));
        setSelectedIds([]);
        setShowDeleteModal(false);
    };

    // row action callbacks
    const handleEvaluate = (id, currentStatus) => {
        if (currentStatus === '평가완료') {
            alert('평가가 완료되었습니다.');
            return;
        }
        // 평가 로직 처리 (예: 평가완료 상태로 강제 변경 시뮬레이션)
        alert('평가 화면으로 이동합니다.');
    };

    const handleCancel = (id, currentStatus) => {
        if (currentStatus !== '평가완료') {
            alert('취소할 결과가 없습니다.');
            return;
        }
        // 평가 완료 결과를 대기로 초기화
        const updated = resultsData.map(item => {
            if (item.id === id) return { ...item, evaluationStatus: '평가대기', result: '-' };
            return item;
        });
        setResultsData(updated);
        setFilteredResults(updated.filter(i => filteredResults.find(fi => fi.id === i.id)));
        alert('평가가 취소되어 평가대기 상태로 변경되었습니다.');
    };

    const handleEditResult = (id, currentStatus) => {
        if (currentStatus !== '평가완료') {
            alert('수정할 결과가 없습니다.');
            return;
        }

        const item = resultsData.find(i => i.id === id);
        setEditingItem(item);
        // 기존 점수를 불러왔다고 가정한 임의의 초기값
        const mockInitial = {
            jobUnderstanding: 85,
            jobExperience: 80,
            jobProblemSolving: 75,
            communication: 70,
            growthWill: 85,
            responsibility: 90,
            cultureFit: 70
        };
        setEditScores(mockInitial);
        setOriginalScores(mockInitial);
        setEditFinalResult(item.result);
        setOriginalFinalResult(item.result);
        setShowEditResultModal(true);
    };

    const confirmEditResult = () => {
        const updated = resultsData.map(item => {
            if (item.id === editingItem.id) {
                return { ...item, result: editFinalResult };
            }
            return item;
        });
        setResultsData(updated);
        setFilteredResults(updated.filter(i => filteredResults.find(fi => fi.id === i.id)));
        setShowEditResultModal(false);
        alert('평가 결과가 성공적으로 수정되었습니다.');
    };

    const handleNotify = (id, currentStatus, name) => {
        if (currentStatus !== '평가완료') {
            alert('전송할 결과가 없습니다.');
            return;
        }
        alert(`${name} 님에게 면접 결과를 통보합니다 (이메일/연락처 발송).`);
    };

    return (
        <div className="result-management">
            <div className="search-section">
                <div className="search-row">
                    <div className="search-field">
                        <label>직무</label>
                        <input type="text" value={searchJob} onChange={(e) => setSearchJob(e.target.value)} placeholder="채용직무 입력" />
                    </div>
                    <div className="search-field">
                        <label>면접코드</label>
                        <input type="text" value={searchCode} onChange={(e) => setSearchCode(e.target.value)} placeholder="면접회차/공고단위" />
                    </div>
                    <div className="search-field">
                        <label>현황 (결과)</label>
                        <select value={searchResult} onChange={(e) => setSearchResult(e.target.value)}>
                            <option value="">전체</option>
                            <option value="최종합격">최종합격</option>
                            <option value="예비합격">예비합격</option>
                            <option value="불합격">불합격</option>
                        </select>
                    </div>
                    <div className="search-field">
                        <label>기간 (면접진행일)</label>
                        <div className="date-range">
                            <input type="date" value={startDate} max="9999-12-31" onChange={(e) => setStartDate(e.target.value)} />
                            <span>~</span>
                            <input type="date" value={endDate} max="9999-12-31" onChange={(e) => setEndDate(e.target.value)} />
                        </div>
                    </div>
                </div>
                <div className="search-actions">
                    <button className="btn-search" onClick={handleSearch}>검색</button>
                    <button className="btn-reset" onClick={handleReset}>초기화</button>
                </div>
            </div>

            <div className="list-section">
                <div className="list-header">
                    <h3>면접 결과 관리 목록 ({filteredResults.length}건)</h3>
                    <div className="list-actions">
                        <button className="btn-delete" onClick={requestDelete}>선택 삭제</button>
                    </div>
                </div>

                <div className="table-responsive">
                    <table className="result-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox" checked={filteredResults.length > 0 && selectedIds.length === filteredResults.length} onChange={handleSelectAll} /></th>
                                <th>지원자</th>
                                <th>지원직무</th>
                                <th>면접진행일</th>
                                <th>면접결과</th>
                                <th>관리영역</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredResults.length > 0 ? filteredResults.map(item => (
                                <tr key={item.id}>
                                    <td><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => handleSelect(item.id)} /></td>
                                    <td className="profile-cell">
                                        <div className="avatar">{item.name[0]}</div>
                                        <span>{item.name}</span>
                                    </td>
                                    <td>{item.job}</td>
                                    <td>{new Date(item.interviewDate).toLocaleString()}</td>
                                    <td>
                                        {item.evaluationStatus === '평가대기' ? (
                                            <span className="result-badge pending">평가대기</span>
                                        ) : (
                                            <span className={`result-badge ${item.result === '최종합격' ? 'pass' : item.result === '예비합격' ? 'reserve' : 'fail'}`}>
                                                {item.result}
                                            </span>
                                        )}
                                    </td>
                                    <td>
                                        <div className="management-actions">
                                            <button
                                                className={`btn-mgmt ${item.evaluationStatus === '평가대기' ? 'btn-eval-active' : 'btn-disabled'}`}
                                                onClick={() => handleEvaluate(item.id, item.evaluationStatus)}
                                            >평가</button>

                                            <button
                                                className={`btn-mgmt ${item.evaluationStatus === '평가완료' ? 'btn-cancel-active' : 'btn-disabled'}`}
                                                onClick={() => handleCancel(item.id, item.evaluationStatus)}
                                            >취소</button>

                                            <button
                                                className={`btn-mgmt ${item.evaluationStatus === '평가완료' ? 'btn-edit-active' : 'btn-disabled'}`}
                                                onClick={() => handleEditResult(item.id, item.evaluationStatus)}
                                            >결과 수정</button>

                                            <button
                                                className={`btn-mgmt ${item.evaluationStatus === '평가완료' ? 'btn-notify-active' : 'btn-disabled'}`}
                                                onClick={() => handleNotify(item.id, item.evaluationStatus, item.name)}
                                            >결과 통보</button>
                                        </div>
                                    </td>
                                </tr>
                            )) : (
                                <tr><td colSpan="6" className="no-data">조회된 결과가 없습니다.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {showDeleteModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>선택 항목 삭제</h3>
                        <p>선택한 {selectedIds.length}건의 데이터를 삭제하시겠습니까? (삭제 시 복구할 수 없습니다)</p>
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowDeleteModal(false)}>취소</button>
                            <button className="btn-confirm-delete" onClick={confirmDelete}>삭제</button>
                        </div>
                    </div>
                </div>
            )}

            {showEditResultModal && editingItem && (
                <div className="modal-overlay">
                    <div className="modal-content edit-result-modal">
                        <div className="modal-header-flex">
                            <h3>평가 수정 <span>(INT-05-1)</span></h3>
                            <button className="btn-close-x" onClick={() => setShowEditResultModal(false)}>×</button>
                        </div>

                        <div className="edit-candidate-info">
                            <div className="avatar edit-avatar">{editingItem.name[0]}</div>
                            <div className="edit-info-text">
                                <h4>{editingItem.name}</h4>
                                <p>{editingItem.job}</p>
                            </div>
                        </div>

                        <div className="edit-section">
                            <h4>평가 항목 점수 조정</h4>
                            <div className="edit-scores-container">
                                {Object.keys(editScores).map(key => {
                                    const labels = {
                                        jobUnderstanding: '직무이해도',
                                        jobExperience: '직무경험',
                                        jobProblemSolving: '직무해결역량',
                                        communication: '의사소통능력',
                                        growthWill: '성장의지',
                                        responsibility: '책임·성실 태도',
                                        cultureFit: '조직적합성'
                                    };
                                    return (
                                        <div className="score-control" key={key}>
                                            <label>{labels[key]}</label>
                                            <div className="score-input-group">
                                                <input
                                                    type="range"
                                                    min="0" max="100"
                                                    value={editScores[key]}
                                                    onChange={(e) => setEditScores({ ...editScores, [key]: parseInt(e.target.value) })}
                                                />
                                                <input
                                                    type="number"
                                                    min="0" max="100"
                                                    value={editScores[key]}
                                                    onChange={(e) => {
                                                        let val = parseInt(e.target.value);
                                                        if (isNaN(val)) val = 0;
                                                        if (val > 100) val = 100;
                                                        setEditScores({ ...editScores, [key]: val });
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="edit-section">
                            <h4>최종 결과 선택</h4>
                            <div className="final-buttons">
                                {['최종합격', '보류', '불합격'].map(res => (
                                    <button
                                        key={res}
                                        className={`btn-final-sel ${editFinalResult === res || (editFinalResult === '예비합격' && res === '보류') ? 'selected' : ''}`}
                                        onClick={() => setEditFinalResult(res === '보류' ? '예비합격' : res)}
                                    >
                                        {res}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="edit-section no-border border-bottom">
                            <h4>수정 이력</h4>
                            <div className="history-card">
                                <div className="history-row">
                                    <span className="history-label">최종 수정자</span>
                                    <span className="history-value">홍길동 관리자</span>
                                </div>
                                <div className="history-row">
                                    <span className="history-label">수정 일시</span>
                                    <span className="history-value">{new Date().toLocaleString()}</span>
                                </div>
                                <div className="history-desc">
                                    {(() => {
                                        const labels = {
                                            jobUnderstanding: '직무이해도',
                                            jobExperience: '직무경험',
                                            jobProblemSolving: '직무해결역량',
                                            communication: '의사소통능력',
                                            growthWill: '성장의지',
                                            responsibility: '책임·성실 태도',
                                            cultureFit: '조직적합성'
                                        };
                                        const changes = [];
                                        Object.keys(editScores).forEach(key => {
                                            if (editScores[key] !== originalScores[key]) {
                                                changes.push(`${labels[key]}: ${originalScores[key]}점 → ${editScores[key]}점`);
                                            }
                                        });
                                        if (editFinalResult !== originalFinalResult) {
                                            changes.push(`최종결과: ${originalFinalResult} → ${editFinalResult}`);
                                        }

                                        if (changes.length === 0) {
                                            return <span>수정된 항목이 없습니다.</span>;
                                        }
                                        return changes.map((text, idx) => <div key={idx}>{text}</div>);
                                    })()}
                                </div>
                            </div>
                        </div>

                        <div className="modal-actions edit-modal-actions">
                            <button className="btn-cancel" onClick={() => setShowEditResultModal(false)}>취소</button>
                            <button className="btn-confirm-edit" onClick={confirmEditResult}>저장</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ResultManagementPage;
