import { useState } from 'react';
import './JobPostingListPage.css';

function JobPostingListPage({ user, onNavigate }) {
    // 검색 조건
    const [searchFilters, setSearchFilters] = useState({
        title: '',
        position: '',
        employmentType: '',
        status: '',
        startDate: '',
        endDate: ''
    });

    // 정렬 및 페이지 설정
    const [sortOrder, setSortOrder] = useState('latest'); // latest, oldest
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [currentPage, setCurrentPage] = useState(1);
    const [selectedItems, setSelectedItems] = useState([]);

    // Mock 데이터
    const mockJobPostings = [
        { id: 1, title: 'Frontend Developer 채용', position: 'Frontend Developer', employmentType: '정규직', startDate: '2026-02-01', endDate: '2026-03-01', status: '진행중', registeredDate: '2026-01-25' },
        { id: 2, title: 'Backend Developer 채용', position: 'Backend Developer', employmentType: '정규직', startDate: '2026-02-05', endDate: '2026-03-05', status: '진행중', registeredDate: '2026-01-28' },
        { id: 3, title: 'Full Stack Developer 채용', position: 'Full Stack Developer', employmentType: '계약직', startDate: '2026-01-15', endDate: '2026-02-15', status: '마감', registeredDate: '2026-01-10' },
        { id: 4, title: 'UI/UX Designer 채용', position: 'UI/UX Designer', employmentType: '정규직', startDate: '2026-02-20', endDate: '2026-03-20', status: '대기', registeredDate: '2026-02-01' },
        { id: 5, title: 'DevOps Engineer 채용', position: 'DevOps Engineer', employmentType: '정규직', startDate: '2026-02-10', endDate: '2026-03-10', status: '진행중', registeredDate: '2026-02-03' },
        { id: 6, title: 'Data Scientist 채용', position: 'Data Scientist', employmentType: '계약직', startDate: '2026-01-20', endDate: '2026-02-20', status: '마감', registeredDate: '2026-01-15' },
        { id: 7, title: 'AI/ML Engineer 채용', position: 'AI/ML Engineer', employmentType: '정규직', startDate: '2026-02-15', endDate: '2026-03-15', status: '진행중', registeredDate: '2026-02-08' },
        { id: 8, title: 'Product Manager 채용', position: 'Product Manager', employmentType: '정규직', startDate: '2026-02-25', endDate: '2026-03-25', status: '대기', registeredDate: '2026-02-10' },
    ];

    // 필터링 및 정렬
    const getFilteredAndSortedData = () => {
        let filtered = mockJobPostings.filter(item => {
            if (searchFilters.title && !item.title.toLowerCase().includes(searchFilters.title.toLowerCase())) return false;
            if (searchFilters.position && item.position !== searchFilters.position) return false;
            if (searchFilters.employmentType && item.employmentType !== searchFilters.employmentType) return false;
            if (searchFilters.status && item.status !== searchFilters.status) return false;
            if (searchFilters.startDate && item.startDate < searchFilters.startDate) return false;
            if (searchFilters.endDate && item.endDate > searchFilters.endDate) return false;
            return true;
        });

        // 정렬
        filtered.sort((a, b) => {
            if (sortOrder === 'latest') {
                return new Date(b.registeredDate) - new Date(a.registeredDate);
            } else {
                return new Date(a.registeredDate) - new Date(b.registeredDate);
            }
        });

        return filtered;
    };

    const filteredData = getFilteredAndSortedData();
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    const paginatedData = filteredData.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    // 검색 조건 변경
    const handleFilterChange = (field, value) => {
        setSearchFilters(prev => ({ ...prev, [field]: value }));
        setCurrentPage(1);
    };

    // 초기화
    const handleReset = () => {
        setSearchFilters({
            title: '',
            position: '',
            employmentType: '',
            status: '',
            startDate: '',
            endDate: ''
        });
        setCurrentPage(1);
    };

    // 체크박스 선택
    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedItems(paginatedData.map(item => item.id));
        } else {
            setSelectedItems([]);
        }
    };

    const handleSelectItem = (id) => {
        setSelectedItems(prev =>
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    // 선택 삭제
    const handleDelete = () => {
        if (selectedItems.length === 0) {
            alert('삭제할 공고를 선택해주세요.');
            return;
        }
        if (confirm(`선택한 ${selectedItems.length}개의 공고를 삭제하시겠습니까?`)) {
            console.log('삭제할 항목:', selectedItems);
            alert('삭제되었습니다.');
            setSelectedItems([]);
        }
    };

    // 선택 변경
    const handleEdit = () => {
        if (selectedItems.length === 0) {
            alert('수정할 공고를 선택해주세요.');
            return;
        }
        if (selectedItems.length > 1) {
            alert('한 개의 공고만 선택해주세요.');
            return;
        }
        if (confirm('선택한 공고를 수정하시겠습니까?')) {
            console.log('수정할 항목:', selectedItems[0]);
            // onNavigate('job_posting_edit', selectedItems[0]);
        }
    };

    // 페이지 네비게이션
    const getPageNumbers = () => {
        const pageGroup = Math.ceil(currentPage / 5);
        const startPage = (pageGroup - 1) * 5 + 1;
        const endPage = Math.min(startPage + 4, totalPages);

        const pages = [];
        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }
        return pages;
    };

    const handlePrevGroup = () => {
        const pageGroup = Math.ceil(currentPage / 5);
        const newPage = Math.max((pageGroup - 2) * 5 + 1, 1);
        setCurrentPage(newPage);
    };

    const handleNextGroup = () => {
        const pageGroup = Math.ceil(currentPage / 5);
        const newPage = Math.min(pageGroup * 5 + 1, totalPages);
        setCurrentPage(newPage);
    };

    return (
        <div className="job-posting-list-container">
            {/* 검색 조건 영역 */}
            <div className="search-section">
                <div className="search-row">
                    <div className="search-group">
                        <label className="search-label">공고명</label>
                        <input
                            type="text"
                            className="search-input"
                            placeholder="공고 제목 검색"
                            value={searchFilters.title}
                            onChange={(e) => handleFilterChange('title', e.target.value)}
                        />
                    </div>

                    <div className="search-group">
                        <label className="search-label">직무</label>
                        <select
                            className="search-select"
                            value={searchFilters.position}
                            onChange={(e) => handleFilterChange('position', e.target.value)}
                        >
                            <option value="">전체</option>
                            <option value="Frontend Developer">Frontend Developer</option>
                            <option value="Backend Developer">Backend Developer</option>
                            <option value="Full Stack Developer">Full Stack Developer</option>
                            <option value="DevOps Engineer">DevOps Engineer</option>
                            <option value="Data Scientist">Data Scientist</option>
                            <option value="AI/ML Engineer">AI/ML Engineer</option>
                            <option value="UI/UX Designer">UI/UX Designer</option>
                            <option value="Product Manager">Product Manager</option>
                        </select>
                    </div>

                    <div className="search-group">
                        <label className="search-label">채용 유형</label>
                        <select
                            className="search-select"
                            value={searchFilters.employmentType}
                            onChange={(e) => handleFilterChange('employmentType', e.target.value)}
                        >
                            <option value="">전체</option>
                            <option value="정규직">정규직</option>
                            <option value="계약직">계약직</option>
                            <option value="인턴">인턴</option>
                            <option value="파트타임">파트타임</option>
                        </select>
                    </div>

                    <div className="search-group">
                        <label className="search-label">진행 현황</label>
                        <select
                            className="search-select"
                            value={searchFilters.status}
                            onChange={(e) => handleFilterChange('status', e.target.value)}
                        >
                            <option value="">전체</option>
                            <option value="진행중">진행중</option>
                            <option value="마감">마감</option>
                            <option value="대기">대기</option>
                        </select>
                    </div>
                </div>

                <div className="search-row">
                    <div className="search-group">
                        <label className="search-label">모집 시작일</label>
                        <input
                            type="date"
                            className="search-input date-input"
                            value={searchFilters.startDate}
                            onChange={(e) => handleFilterChange('startDate', e.target.value)}
                            max="9999-12-31"
                        />
                    </div>

                    <div className="search-group">
                        <label className="search-label">모집 종료일</label>
                        <input
                            type="date"
                            className="search-input date-input"
                            value={searchFilters.endDate}
                            onChange={(e) => handleFilterChange('endDate', e.target.value)}
                            max="9999-12-31"
                        />
                    </div>

                    <div className="search-actions">
                        <button className="btn btn-search" onClick={() => setCurrentPage(1)}>
                            검색
                        </button>
                        <button className="btn btn-reset" onClick={handleReset}>
                            초기화
                        </button>
                    </div>
                </div>
            </div>

            {/* 목록 제어 영역 */}
            <div className="list-controls">
                <div className="control-left">
                    <button className="btn btn-delete" onClick={handleDelete}>
                        선택 삭제
                    </button>
                    <button className="btn btn-edit" onClick={handleEdit}>
                        선택 수정
                    </button>
                    <span className="selected-count">
                        선택: {selectedItems.length}개
                    </span>
                </div>

                <div className="control-right">
                    <select
                        className="control-select"
                        value={sortOrder}
                        onChange={(e) => setSortOrder(e.target.value)}
                    >
                        <option value="latest">최신순</option>
                        <option value="oldest">과거순</option>
                    </select>

                    <select
                        className="control-select"
                        value={itemsPerPage}
                        onChange={(e) => {
                            setItemsPerPage(Number(e.target.value));
                            setCurrentPage(1);
                        }}
                    >
                        <option value={10}>10개씩 보기</option>
                        <option value={20}>20개씩 보기</option>
                        <option value={50}>50개씩 보기</option>
                    </select>
                </div>
            </div>

            {/* 결과 목록 테이블 */}
            <div className="table-container">
                <table className="job-posting-table">
                    <thead>
                        <tr>
                            <th className="th-checkbox">
                                <input
                                    type="checkbox"
                                    checked={paginatedData.length > 0 && selectedItems.length === paginatedData.length}
                                    onChange={handleSelectAll}
                                />
                            </th>
                            <th>공고명</th>
                            <th>직무</th>
                            <th>채용 유형</th>
                            <th>모집 기간</th>
                            <th>진행 현황</th>
                            <th>등록일</th>
                        </tr>
                    </thead>
                    <tbody>
                        {paginatedData.length === 0 ? (
                            <tr>
                                <td colSpan="7" className="no-data">
                                    조회된 공고가 없습니다.
                                </td>
                            </tr>
                        ) : (
                            paginatedData.map((item) => (
                                <tr key={item.id}>
                                    <td className="td-checkbox">
                                        <input
                                            type="checkbox"
                                            checked={selectedItems.includes(item.id)}
                                            onChange={() => handleSelectItem(item.id)}
                                        />
                                    </td>
                                    <td className="td-title">{item.title}</td>
                                    <td>{item.position}</td>
                                    <td>{item.employmentType}</td>
                                    <td>{item.startDate} ~ {item.endDate}</td>
                                    <td>
                                        <span className={`status-badge status-${item.status}`}>
                                            {item.status}
                                        </span>
                                    </td>
                                    <td>{item.registeredDate}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* 페이지네이션 */}
            {totalPages > 0 && (
                <div className="pagination">
                    <button
                        className="page-btn"
                        onClick={handlePrevGroup}
                        disabled={currentPage <= 5}
                    >
                        이전
                    </button>

                    {getPageNumbers().map((page) => (
                        <button
                            key={page}
                            className={`page-number ${currentPage === page ? 'active' : ''}`}
                            onClick={() => setCurrentPage(page)}
                        >
                            {page}
                        </button>
                    ))}

                    <button
                        className="page-btn"
                        onClick={handleNextGroup}
                        disabled={currentPage > totalPages - 5}
                    >
                        다음
                    </button>

                    <span className="page-info">
                        {currentPage} / {totalPages} 페이지
                    </span>
                </div>
            )}
        </div>
    );
}

export default JobPostingListPage;
