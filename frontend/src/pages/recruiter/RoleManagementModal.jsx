import { useState, useEffect } from 'react';
import './RoleManagementModal.css';

const ROLES = [
    { value: 'all', label: '전체' },
    { value: 'candidate', label: 'Candidate' },
    { value: 'recruiter', label: 'Recruiter' },
    { value: 'admin', label: 'Admin' },
];

const ROLE_COLORS = {
    all: 'role-all',
    candidate: 'role-candidate',
    recruiter: 'role-recruiter',
    admin: 'role-admin',
};

// Mock 사용자 데이터 (실제로는 API에서 가져옴)
const MOCK_USERS = [
    { id: 1, name: '김지원', email: 'jiwon.kim@example.com', role: 'candidate' },
    { id: 2, name: '이민수', email: 'minsu.lee@example.com', role: 'recruiter' },
    { id: 3, name: '박서연', email: 'seoyeon.park@example.com', role: 'candidate' },
    { id: 4, name: '최현우', email: 'hyunwoo.choi@example.com', role: 'admin' },
    { id: 5, name: '정수빈', email: 'subin.jung@example.com', role: 'candidate' },
    { id: 6, name: '강민지', email: 'minji.kang@example.com', role: 'recruiter' },
    { id: 7, name: '윤태양', email: 'taeyang.yoon@example.com', role: 'candidate' },
    { id: 8, name: '한예린', email: 'yerin.han@example.com', role: 'candidate' },
    { id: 9, name: '오준혁', email: 'junhyuk.oh@example.com', role: 'recruiter' },
];

const ITEMS_PER_PAGE = 4;

function RoleManagementModal({ onClose }) {
    const [users, setUsers] = useState(
        MOCK_USERS.map(u => ({ ...u, pendingRole: u.role }))
    );
    const [currentPage, setCurrentPage] = useState(0);
    const [savedMsg, setSavedMsg] = useState('');

    // 검색 필터
    const [searchName, setSearchName] = useState('');
    const [searchEmail, setSearchEmail] = useState('');
    const [filterRole, setFilterRole] = useState('all');

    const filteredUsers = users.filter(u => {
        const nameMatch = u.name.includes(searchName);
        const emailMatch = u.email.toLowerCase().includes(searchEmail.toLowerCase());
        const roleMatch = filterRole === 'all' || u.role === filterRole;
        return nameMatch && emailMatch && roleMatch;
    });

    const totalPages = Math.ceil(filteredUsers.length / ITEMS_PER_PAGE);
    const pagedUsers = filteredUsers.slice(
        currentPage * ITEMS_PER_PAGE,
        (currentPage + 1) * ITEMS_PER_PAGE
    );

    // 페이지 초과 방지
    useEffect(() => {
        if (currentPage >= totalPages && totalPages > 0) {
            setCurrentPage(totalPages - 1);
        }
    }, [totalPages, currentPage]);

    const hasChange = (user) => user.pendingRole !== user.role;

    const handleRoleChange = (userId, newRole) => {
        setUsers(prev =>
            prev.map(u => u.id === userId ? { ...u, pendingRole: newRole } : u)
        );
    };

    const handleSave = (userId) => {
        setUsers(prev =>
            prev.map(u => u.id === userId ? { ...u, role: u.pendingRole } : u)
        );
        setSavedMsg('저장되었습니다.');
        setTimeout(() => setSavedMsg(''), 2000);
    };

    const handleReset = (userId) => {
        setUsers(prev =>
            prev.map(u => u.id === userId ? { ...u, pendingRole: u.role } : u)
        );
    };

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) onClose();
    };

    return (
        <div className="rm-backdrop" onClick={handleBackdropClick}>
            <div className="rm-modal" role="dialog" aria-modal="true" aria-label="권한 관리">
                {/* 헤더 */}
                <div className="rm-header">
                    <div className="rm-header-left">
                        <span className="rm-header-icon">🔐</span>
                        <div>
                            <h2 className="rm-title">권한 관리</h2>
                            <p className="rm-subtitle">사용자별 시스템 접근 권한을 설정합니다</p>
                        </div>
                    </div>
                    <button className="rm-close-btn" onClick={onClose} aria-label="닫기">✕</button>
                </div>

                {/* 신규 사용자 추가 섹션 */}
                <div className="rm-add-section">
                    <h3 className="rm-section-title">
                        <span className="rm-section-icon">➕</span>
                        사용자 권한 추가
                    </h3>
                    <AddUserRow onAdd={(newUser) => {
                        setUsers(prev => [...prev, { ...newUser, id: Date.now(), pendingRole: newUser.role }]);
                        setSavedMsg('사용자가 추가되었습니다.');
                        setTimeout(() => setSavedMsg(''), 2000);
                    }} />
                </div>

                {/* 구분선 */}
                <div className="rm-divider" />

                {/* 사용자 목록 섹션 */}
                <div className="rm-list-section">
                    <div className="rm-list-header">
                        <h3 className="rm-section-title">
                            <span className="rm-section-icon">👥</span>
                            사용자 권한 관리 목록
                            <span className="rm-count-badge">{filteredUsers.length}명</span>
                        </h3>
                        {/* 필터 */}
                        <div className="rm-filters">
                            <input
                                className="rm-filter-input"
                                type="text"
                                placeholder="이름 검색"
                                value={searchName}
                                onChange={e => { setSearchName(e.target.value); setCurrentPage(0); }}
                            />
                            <input
                                className="rm-filter-input"
                                type="text"
                                placeholder="이메일 검색"
                                value={searchEmail}
                                onChange={e => { setSearchEmail(e.target.value); setCurrentPage(0); }}
                            />
                            <select
                                className="rm-filter-select"
                                value={filterRole}
                                onChange={e => { setFilterRole(e.target.value); setCurrentPage(0); }}
                            >
                                {ROLES.map(r => (
                                    <option key={r.value} value={r.value}>{r.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* 테이블 헤더 */}
                    <div className="rm-table-header">
                        <span className="rm-col-name">이름</span>
                        <span className="rm-col-email">이메일</span>
                        <span className="rm-col-role">현재 권한</span>
                        <span className="rm-col-change">권한 변경</span>
                        <span className="rm-col-action">저장 / 초기화</span>
                    </div>

                    {/* 사용자 행 */}
                    <div className="rm-table-body">
                        {pagedUsers.length === 0 ? (
                            <div className="rm-empty">검색 결과가 없습니다.</div>
                        ) : (
                            pagedUsers.map(user => (
                                <div
                                    key={user.id}
                                    className={`rm-table-row ${hasChange(user) ? 'rm-row-changed' : ''}`}
                                >
                                    <span className="rm-col-name rm-user-name">
                                        <span className="rm-avatar">{user.name[0]}</span>
                                        {user.name}
                                    </span>
                                    <span className="rm-col-email rm-user-email">{user.email}</span>
                                    <span className="rm-col-role">
                                        <span className={`rm-role-badge ${ROLE_COLORS[user.role]}`}>
                                            {ROLES.find(r => r.value === user.role)?.label || user.role}
                                        </span>
                                    </span>
                                    <span className="rm-col-change">
                                        <select
                                            className={`rm-role-select ${hasChange(user) ? 'rm-select-changed' : ''}`}
                                            value={user.pendingRole}
                                            onChange={e => handleRoleChange(user.id, e.target.value)}
                                        >
                                            {ROLES.filter(r => r.value !== 'all').map(r => (
                                                <option key={r.value} value={r.value}>{r.label}</option>
                                            ))}
                                        </select>
                                    </span>
                                    <span className="rm-col-action">
                                        {hasChange(user) ? (
                                            <button
                                                className="rm-save-btn"
                                                onClick={() => handleSave(user.id)}
                                            >
                                                💾 저장
                                            </button>
                                        ) : (
                                            <button
                                                className="rm-reset-btn"
                                                onClick={() => handleReset(user.id)}
                                                disabled
                                            >
                                                🔄 초기화
                                            </button>
                                        )}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>

                    {/* 페이지네이션 */}
                    {totalPages > 1 && (
                        <div className="rm-pagination">
                            <button
                                className="rm-page-btn"
                                onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                                disabled={currentPage === 0}
                            >
                                ‹
                            </button>
                            {Array.from({ length: totalPages }).map((_, i) => (
                                <button
                                    key={i}
                                    className={`rm-page-btn ${i === currentPage ? 'rm-page-active' : ''}`}
                                    onClick={() => setCurrentPage(i)}
                                >
                                    {i + 1}
                                </button>
                            ))}
                            <button
                                className="rm-page-btn"
                                onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))}
                                disabled={currentPage === totalPages - 1}
                            >
                                ›
                            </button>
                            <span className="rm-page-info">
                                {currentPage + 1} / {totalPages} 페이지
                            </span>
                        </div>
                    )}
                </div>

                {/* 저장 성공 토스트 */}
                {savedMsg && (
                    <div className="rm-toast">
                        <span>✅ {savedMsg}</span>
                    </div>
                )}
            </div>
        </div>
    );
}

// 신규 사용자 추가 행 컴포넌트
function AddUserRow({ onAdd }) {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [role, setRole] = useState('candidate');
    const [error, setError] = useState('');

    const handleSave = () => {
        if (!name.trim()) { setError('이름을 입력하세요.'); return; }
        if (!email.trim() || !email.includes('@')) { setError('유효한 이메일을 입력하세요.'); return; }
        setError('');
        onAdd({ name: name.trim(), email: email.trim(), role });
        setName('');
        setEmail('');
        setRole('candidate');
    };

    return (
        <div className="rm-add-row">
            <input
                className="rm-add-input"
                type="text"
                placeholder="이름"
                value={name}
                onChange={e => setName(e.target.value)}
                id="rm-add-name"
            />
            <input
                className="rm-add-input rm-add-email"
                type="email"
                placeholder="이메일"
                value={email}
                onChange={e => setEmail(e.target.value)}
                id="rm-add-email"
            />
            <select
                className="rm-add-select"
                value={role}
                onChange={e => setRole(e.target.value)}
                id="rm-add-role"
            >
                {ROLES.filter(r => r.value !== 'all').map(r => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                ))}
            </select>
            {error && <span className="rm-add-error">{error}</span>}
            <button className="rm-add-save-btn" onClick={handleSave} id="rm-add-save">
                💾 저장
            </button>
        </div>
    );
}

export default RoleManagementModal;
