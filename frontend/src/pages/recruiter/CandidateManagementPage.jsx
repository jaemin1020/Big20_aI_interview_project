import React, { useState, useEffect } from 'react';
import './CandidateManagementPage.css';

const TimerCell = ({ dateString }) => {
    const [remaining, setRemaining] = useState('');

    useEffect(() => {
        const updateTimer = () => {
            const target = new Date(dateString).getTime();
            const now = new Date().getTime();
            const diff = target - now;

            if (diff > 0) {
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const secs = Math.floor((diff % (1000 * 60)) / 1000);
                setRemaining(`${days > 0 ? days + '일 ' : ''}${hours}시간 ${mins}분 ${secs}초`);
            } else {
                setRemaining('진행/완료');
            }
        };

        const interval = setInterval(updateTimer, 1000);
        updateTimer();
        return () => clearInterval(interval);
    }, [dateString]);

    return <span>{remaining}</span>;
}

const mockCandidates = [
    { id: 1, name: '김지원', photo: '', job: 'Frontend Developer', interviewCode: 'INT-2026-001', resumeSubmitted: true, coverLetterSubmitted: true, portfolioSubmitted: true, evidenceSubmitted: true, interviewDate: '2026-02-25T14:00:00', applicationDate: '2026-02-10' },
    { id: 2, name: '이민수', photo: '', job: 'Backend Developer', interviewCode: 'INT-2026-001', resumeSubmitted: true, coverLetterSubmitted: true, portfolioSubmitted: false, evidenceSubmitted: false, interviewDate: '2026-02-24T18:00:00', applicationDate: '2026-02-11' },
    { id: 3, name: '박서연', photo: '', job: 'UI/UX Designer', interviewCode: 'INT-2026-002', resumeSubmitted: false, coverLetterSubmitted: false, portfolioSubmitted: true, evidenceSubmitted: false, interviewDate: '2026-02-26T10:00:00', applicationDate: '2026-02-12' },
    { id: 4, name: '최현우', photo: '', job: 'DevOps Engineer', interviewCode: 'INT-2026-003', resumeSubmitted: true, coverLetterSubmitted: true, portfolioSubmitted: false, evidenceSubmitted: true, interviewDate: '2026-02-23T15:30:00', applicationDate: '2026-02-12' },
];

function CandidateManagementPage() {
    const [candidates, setCandidates] = useState(mockCandidates);
    const [filteredCandidates, setFilteredCandidates] = useState(mockCandidates);

    const [searchJob, setSearchJob] = useState('');
    const [searchCode, setSearchCode] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const [selectedIds, setSelectedIds] = useState([]);

    // Modals
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);

    const handleSearch = () => {
        let result = candidates;

        if (searchJob) {
            result = result.filter(c => c.job.toLowerCase().includes(searchJob.toLowerCase()));
        }
        if (searchCode) {
            result = result.filter(c => c.interviewCode.toLowerCase().includes(searchCode.toLowerCase()));
        }
        if (startDate && endDate) {
            result = result.filter(c => {
                const date = c.interviewDate.split('T')[0];
                return date >= startDate && date <= endDate;
            });
        }

        setFilteredCandidates(result);
        setSelectedIds([]);
    };

    const handleReset = () => {
        setSearchJob('');
        setSearchCode('');
        setStartDate('');
        setEndDate('');
        setFilteredCandidates(candidates);
        setSelectedIds([]);
    };

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedIds(filteredCandidates.map(c => c.id));
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
            alert('삭제할 지원자를 선택해주세요.');
            return;
        }
        setShowDeleteModal(true);
    };

    const confirmDelete = () => {
        const newData = candidates.filter(c => !selectedIds.includes(c.id));
        setCandidates(newData);
        setFilteredCandidates(newData.filter(c => filteredCandidates.some(fc => fc.id === c.id && !selectedIds.includes(c.id))));
        setSelectedIds([]);
        setShowDeleteModal(false);
    };

    const requestEdit = () => {
        if (selectedIds.length === 0) {
            alert('변경할 지원자를 선택해주세요.');
            return;
        }
        if (selectedIds.length > 1) {
            alert('변경은 한 번에 한 명만 가능합니다.');
            return;
        }
        setShowEditModal(true);
    };

    const confirmEdit = () => {
        // Edit navigation logic here
        setShowEditModal(false);
        alert('변경 화면으로 이동합니다.');
    };

    return (
        <div className="candidate-management">
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
                    <h3>면접 결과 목록 ({filteredCandidates.length}건)</h3>
                    <div className="list-actions">
                        <button className="btn-edit" onClick={requestEdit}>선택 변경</button>
                        <button className="btn-delete" onClick={requestDelete}>선택 삭제</button>
                    </div>
                </div>

                <div className="table-responsive">
                    <table className="candidate-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox" checked={filteredCandidates.length > 0 && selectedIds.length === filteredCandidates.length} onChange={handleSelectAll} /></th>
                                <th>지원자</th>
                                <th>지원직무</th>
                                <th>제출서류</th>
                                <th>면접진행일</th>
                                <th>남은시간</th>
                                <th>지원일</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredCandidates.length > 0 ? filteredCandidates.map(c => (
                                <tr key={c.id}>
                                    <td><input type="checkbox" checked={selectedIds.includes(c.id)} onChange={() => handleSelect(c.id)} /></td>
                                    <td className="profile-cell">
                                        <div className="avatar">{c.name[0]}</div>
                                        <span>{c.name}</span>
                                    </td>
                                    <td>{c.job}</td>
                                    <td>
                                        <div className="docs-cell">
                                            <span className={`doc-icon ${c.resumeSubmitted ? 'submitted' : 'missing'}`}>📄 이력서</span>
                                            <span className={`doc-icon ${c.coverLetterSubmitted ? 'submitted' : 'missing'}`}>📝 자기소개서</span>
                                            <span className={`doc-icon ${c.portfolioSubmitted ? 'submitted' : 'missing'}`}>📁 포트폴리오</span>
                                            <span className={`doc-icon ${c.evidenceSubmitted ? 'submitted' : 'missing'}`}>📎 증빙서류</span>
                                        </div>
                                    </td>
                                    <td>{new Date(c.interviewDate).toLocaleString()}</td>
                                    <td className="timer-col"><TimerCell dateString={c.interviewDate} /></td>
                                    <td>{c.applicationDate}</td>
                                </tr>
                            )) : (
                                <tr><td colSpan="7" className="no-data">조회된 내역이 없습니다.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Delete Modal */}
            {showDeleteModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>선택 항목 삭제</h3>
                        <p>선택한 {selectedIds.length}건의 면접 결과 데이터를 삭제하시겠습니까?</p>
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowDeleteModal(false)}>취소</button>
                            <button className="btn-confirm-delete" onClick={confirmDelete}>삭제</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Modal */}
            {showEditModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>선택 항목 변경</h3>
                        <p>선택한 1건의 면접 결과 데이터를 변경하시겠습니까? (변경 화면으로 이동합니다)</p>
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowEditModal(false)}>취소</button>
                            <button className="btn-confirm-edit" onClick={confirmEdit}>이동</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default CandidateManagementPage;
