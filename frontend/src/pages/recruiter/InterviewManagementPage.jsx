import React, { useState } from 'react';
import './InterviewManagementPage.css';

const mockInterviews = [
    { id: 1, name: '김지원', job: 'Frontend Developer', interviewCode: 'INT-2026-001', status: '진행중', interviewDate: '2026-02-25T14:00:00' },
    { id: 2, name: '이민수', job: 'Backend Developer', interviewCode: 'INT-2026-001', status: '면접완료', interviewDate: '2026-02-24T18:00:00' },
    { id: 3, name: '박서연', job: 'UI/UX Designer', interviewCode: 'INT-2026-002', status: '평가완료', interviewDate: '2026-02-20T10:00:00' },
    { id: 4, name: '최현우', job: 'DevOps Engineer', interviewCode: 'INT-2026-003', status: '진행중', interviewDate: '2026-02-26T15:30:00' },
];

function InterviewManagementPage() {
    const [interviews, setInterviews] = useState(mockInterviews);
    const [filteredInterviews, setFilteredInterviews] = useState(mockInterviews);

    // 검색 상태
    const [searchJob, setSearchJob] = useState('');
    const [searchCode, setSearchCode] = useState('');
    const [searchStatus, setSearchStatus] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const [selectedIds, setSelectedIds] = useState([]);

    // 모달 상태
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);

    const handleSearch = () => {
        let result = interviews;

        if (searchJob) {
            result = result.filter(item => item.job.toLowerCase().includes(searchJob.toLowerCase()));
        }
        if (searchCode) {
            result = result.filter(item => item.interviewCode.toLowerCase().includes(searchCode.toLowerCase()));
        }
        if (searchStatus) {
            result = result.filter(item => item.status === searchStatus);
        }
        if (startDate && endDate) {
            result = result.filter(item => {
                const date = item.interviewDate.split('T')[0];
                return date >= startDate && date <= endDate;
            });
        }

        setFilteredInterviews(result);
        setSelectedIds([]);
    };

    const handleReset = () => {
        setSearchJob('');
        setSearchCode('');
        setSearchStatus('');
        setStartDate('');
        setEndDate('');
        setFilteredInterviews(interviews);
        setSelectedIds([]);
    };

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedIds(filteredInterviews.map(item => item.id));
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
        const newData = interviews.filter(item => !selectedIds.includes(item.id));
        setInterviews(newData);
        setFilteredInterviews(newData.filter(item => filteredInterviews.some(fi => fi.id === item.id && !selectedIds.includes(item.id))));
        setSelectedIds([]);
        setShowDeleteModal(false);
    };

    const requestEdit = () => {
        if (selectedIds.length === 0) {
            alert('변경할 면접 결과 데이터를 선택해주세요.');
            return;
        }
        if (selectedIds.length > 1) {
            alert('변경은 한 번에 한 항목만 가능합니다.');
            return;
        }
        setShowEditModal(true);
    };

    const confirmEdit = () => {
        setShowEditModal(false);
        alert('변경 화면으로 이동합니다.');
    };

    return (
        <div className="interview-management">
            {/* 2. 조회조건 입력 영역 */}
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
                        <label>현황</label>
                        <select value={searchStatus} onChange={(e) => setSearchStatus(e.target.value)}>
                            <option value="">전체 (진행중/면접완료/평가완료)</option>
                            <option value="진행중">진행중</option>
                            <option value="면접완료">면접완료</option>
                            <option value="평가완료">평가완료</option>
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

            {/* 5. 결과 목록 표시 영역 */}
            <div className="list-section">
                <div className="list-header">
                    <h3>면접 결과 목록 ({filteredInterviews.length}건)</h3>
                    <div className="list-actions">
                        <button className="btn-edit" onClick={requestEdit}>선택 변경</button>
                        <button className="btn-delete" onClick={requestDelete}>선택 삭제</button>
                    </div>
                </div>

                <div className="table-responsive">
                    <table className="interview-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox" checked={filteredInterviews.length > 0 && selectedIds.length === filteredInterviews.length} onChange={handleSelectAll} /></th>
                                <th>지원자</th>
                                <th>지원직무</th>
                                <th>진행상태</th>
                                <th>면접진행일</th>
                                <th>관리영역</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredInterviews.length > 0 ? filteredInterviews.map(item => (
                                <tr key={item.id}>
                                    <td><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => handleSelect(item.id)} /></td>
                                    <td className="profile-cell">
                                        <div className="avatar">{item.name[0]}</div>
                                        <span>{item.name}</span>
                                    </td>
                                    <td>{item.job}</td>
                                    <td>
                                        <span className={`status-badge ${item.status === '진행중' ? 'in-progress' : item.status === '면접완료' ? 'completed' : 'evaluated'}`}>{item.status}</span>
                                    </td>
                                    <td>{new Date(item.interviewDate).toLocaleString()}</td>
                                    <td>
                                        <div className="management-actions">
                                            {item.status === '진행중' && (
                                                <button className="btn-mgmt btn-monitor" onClick={() => alert('모니터링 화면으로 이동합니다.')}>모니터링</button>
                                            )}
                                            {(item.status === '면접완료' || item.status === '평가완료') && (
                                                <button className="btn-mgmt btn-video" onClick={() => alert('영상 확인 팝업을 엽니다.')}>영상확인</button>
                                            )}
                                            <button className="btn-mgmt btn-info" onClick={() => alert(`${item.name}님의 상세 지원정보 팝업을 엽니다.`)}>지원정보</button>
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

            {/* 삭제 확인 모달 */}
            {showDeleteModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>선택 항목 삭제</h3>
                        <p>선택한 {selectedIds.length}건의 면접 결과 데이터를 정말 삭제하시겠습니까?</p>
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowDeleteModal(false)}>취소</button>
                            <button className="btn-confirm-delete" onClick={confirmDelete}>삭제</button>
                        </div>
                    </div>
                </div>
            )}

            {/* 변경 확인 모달 */}
            {showEditModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>선택 항목 변경</h3>
                        <p>선택한 면접 결과 데이터의 변경 화면으로 이동하시겠습니까?</p>
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

export default InterviewManagementPage;
