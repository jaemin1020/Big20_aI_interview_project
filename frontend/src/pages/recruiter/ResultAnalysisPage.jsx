import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import './ResultAnalysisPage.css';

const mockResults = [
    { id: 1, name: '김지원', job: 'Frontend Developer', interviewCode: 'INT-2026-001', resultStatus: '예비합격', interviewDate: '2026-02-25T14:00:00' },
    { id: 2, name: '이민수', job: 'Backend Developer', interviewCode: 'INT-2026-001', resultStatus: '최종합격', interviewDate: '2026-02-24T18:00:00' },
    { id: 3, name: '박서연', job: 'UI/UX Designer', interviewCode: 'INT-2026-002', resultStatus: '불합격', interviewDate: '2026-02-20T10:00:00' },
];

function ResultAnalysisPage() {
    const [analysisData, setAnalysisData] = useState(mockResults);
    const [filteredData, setFilteredData] = useState(mockResults);

    // 검색 상태
    const [searchJob, setSearchJob] = useState('');
    const [searchCode, setSearchCode] = useState('');
    const [searchStatus, setSearchStatus] = useState(''); // 예비합격, 불합격, 최종합격
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const [selectedIds, setSelectedIds] = useState([]);

    // 모달 상태
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [historyTarget, setHistoryTarget] = useState(null);

    const handleSearch = () => {
        let result = analysisData;

        if (searchJob) {
            result = result.filter(item => item.job.toLowerCase().includes(searchJob.toLowerCase()));
        }
        if (searchCode) {
            result = result.filter(item => item.interviewCode.toLowerCase().includes(searchCode.toLowerCase()));
        }
        if (searchStatus) {
            result = result.filter(item => item.resultStatus === searchStatus);
        }
        if (startDate && endDate) {
            result = result.filter(item => {
                const date = item.interviewDate.split('T')[0];
                return date >= startDate && date <= endDate;
            });
        }

        setFilteredData(result);
        setSelectedIds([]);
    };

    const handleReset = () => {
        setSearchJob('');
        setSearchCode('');
        setSearchStatus('');
        setStartDate('');
        setEndDate('');
        setFilteredData(analysisData);
        setSelectedIds([]);
    };

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedIds(filteredData.map(item => item.id));
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

    // 선택 삭제
    const requestDelete = () => {
        if (selectedIds.length === 0) {
            alert('삭제할 데이터를 선택해주세요.');
            return;
        }
        setShowDeleteModal(true);
    };

    const confirmDelete = () => {
        const newData = analysisData.filter(item => !selectedIds.includes(item.id));
        setAnalysisData(newData);
        setFilteredData(newData.filter(item => filteredData.some(fi => fi.id === item.id && !selectedIds.includes(item.id))));
        setSelectedIds([]);
        setShowDeleteModal(false);
    };

    // 선택 변경
    const requestEdit = () => {
        if (selectedIds.length === 0) {
            alert('변경할 데이터를 선택해주세요.');
            return;
        }
        if (selectedIds.length > 1) {
            alert('변경 화면 이동은 한 건씩만 가능합니다.');
            return;
        }
        setShowEditModal(true);
    };

    const confirmEdit = () => {
        setShowEditModal(false);
        alert('면접 결과 변경 화면으로 이동합니다.');
    };

    // row action callbacks
    const handleViewDetails = (id) => {
        alert('결과 상세 보기 화면(INT-06-1)으로 이동합니다.');
    };

    const handleViewHistory = (item) => {
        setHistoryTarget(item);
        setShowHistoryModal(true);
    };

    const handleRequestReevaluation = (id) => {
        if (window.confirm('재평가를 요청하시겠습니까? 결과 상태가 보류로 변경됩니다.')) {
            const updated = analysisData.map(item => {
                if (item.id === id) return { ...item, resultStatus: '보류' };
                return item;
            });
            setAnalysisData(updated);
            setFilteredData(updated.filter(i => filteredData.find(fi => fi.id === i.id)));
            alert('재평가 요청이 처리되었습니다.');
        }
    };

    return (
        <div className="result-analysis">
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
                        <select value={searchStatus} onChange={(e) => setSearchStatus(e.target.value)}>
                            <option value="">전체 (예비합격/불합격/최종합격 등)</option>
                            <option value="최종합격">최종합격</option>
                            <option value="예비합격">예비합격</option>
                            <option value="불합격">불합격</option>
                            <option value="보류">보류</option>
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
                    <h3>면접 결과 분석 목록 ({filteredData.length}건)</h3>
                    <div className="list-actions">
                        <button className="btn-edit-selected" onClick={requestEdit}>선택 변경</button>
                        <button className="btn-delete" onClick={requestDelete}>선택 삭제</button>
                    </div>
                </div>

                <div className="table-responsive">
                    <table className="analysis-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox" checked={filteredData.length > 0 && selectedIds.length === filteredData.length} onChange={handleSelectAll} /></th>
                                <th>지원자 정보</th>
                                <th>지원직무</th>
                                <th>면접일</th>
                                <th>결과상태</th>
                                <th>관리영역</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredData.length > 0 ? filteredData.map(item => (
                                <tr key={item.id}>
                                    <td><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => handleSelect(item.id)} /></td>
                                    <td className="profile-cell">
                                        <div className="avatar">{item.name[0]}</div>
                                        <span>{item.name}</span>
                                    </td>
                                    <td>{item.job}</td>
                                    <td>{new Date(item.interviewDate).toLocaleDateString()}</td>
                                    <td>
                                        <span className={`result-badge ${item.resultStatus === '최종합격' ? 'pass' : item.resultStatus === '예비합격' ? 'reserve' : item.resultStatus === '보류' ? 'pending' : 'fail'}`}>
                                            {item.resultStatus}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="management-actions">
                                            <button className="btn-mgmt btn-details" onClick={() => handleViewDetails(item.id)}>결과 상세 보기</button>
                                            <button className="btn-mgmt btn-history" onClick={() => handleViewHistory(item)}>평가 이력 보기</button>
                                            <button className="btn-mgmt btn-reeval" onClick={() => handleRequestReevaluation(item.id)}>재평가 요청</button>
                                        </div>
                                    </td>
                                </tr>
                            )) : (
                                <tr><td colSpan="6" className="no-data">조회된 내역이 없습니다.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 선택 삭제 모달 */}
            {showDeleteModal && ReactDOM.createPortal(
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>선택 항목 삭제</h3>
                        <p>선택한 {selectedIds.length}건의 데이터를 정말 삭제하시겠습니까?</p>
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowDeleteModal(false)}>취소</button>
                            <button className="btn-confirm-delete" onClick={confirmDelete}>삭제</button>
                        </div>
                    </div>
                </div>,
                document.body
            )}

            {/* 변경 확인 모달 */}
            {showEditModal && ReactDOM.createPortal(
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>선택 항목 변경</h3>
                        <p>선택한 면접 결과 데이터 통계/분석 변경 화면으로 이동하시겠습니까?</p>
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowEditModal(false)}>취소</button>
                            <button className="btn-confirm-edit" onClick={confirmEdit}>이동</button>
                        </div>
                    </div>
                </div>,
                document.body
            )}

            {/* 이력 보기 팝업 */}
            {showHistoryModal && historyTarget && ReactDOM.createPortal(
                <div className="modal-overlay">
                    <div className="modal-content history-modal">
                        <div className="modal-header-flex">
                            <h3>평가 이력 내역</h3>
                            <button className="btn-close-x" onClick={() => setShowHistoryModal(false)}>×</button>
                        </div>
                        <div className="history-target-info">
                            <strong>{historyTarget.name}</strong> ({historyTarget.job}) - 현재 상태: <span className="highlight-text">{historyTarget.resultStatus}</span>
                        </div>
                        <ul className="history-timeline">
                            <li>
                                <div className="time">2026-02-25 15:30</div>
                                <div className="event">평가자: 시스템 자동 평가 기록 (대기상태 처리)</div>
                            </li>
                            <li>
                                <div className="time">2026-02-25 18:00</div>
                                <div className="event">평가자: 김채용 매니저<br />내용: 의사소통능력: 70점 → 90점<br />결과: 불합격 → 최종합격</div>
                            </li>
                            <li className="recent">
                                <div className="time">2026-02-26 09:00</div>
                                <div className="event">평가자: 이인사 파트장<br />내용: 재평가 요청 등록 (상태: 보류 전환)</div>
                            </li>
                        </ul>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
}

export default ResultAnalysisPage;
