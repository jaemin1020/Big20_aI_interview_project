import { useState, useEffect } from 'react';
import './RecruiterMainPage.css';

function RecruiterMainPage({ user, onLogout }) {
    const [activeMenu, setActiveMenu] = useState('dashboard');
    const [jobPostingMenuOpen, setJobPostingMenuOpen] = useState(false);
    const [currentCandidatePage, setCurrentCandidatePage] = useState(0);

    // Mock Data - 실제로는 API에서 가져옴
    const dashboardStats = {
        todayInterviews: 12,
        todayChange: +15.3,
        completedInterviews: 248,
        completedChange: +8.7,
        waitingCandidates: 5
    };

    const monthlyData = [
        { month: '1월', count: 45 },
        { month: '2월', count: 52 },
        { month: '3월', count: 48 },
        { month: '4월', count: 61 },
        { month: '5월', count: 58 },
        { month: '6월', count: 72 }
    ];

    const todayCandidates = [
        { id: 1, name: '김지원', position: 'Frontend Developer', time: '10:00', status: 'waiting' },
        { id: 2, name: '이민수', position: 'Backend Developer', time: '11:00', status: 'in-progress' },
        { id: 3, name: '박서연', position: 'Full Stack Developer', time: '14:00', status: 'waiting' },
        { id: 4, name: '최현우', position: 'DevOps Engineer', time: '15:30', status: 'waiting' },
        { id: 5, name: '정수빈', position: 'Data Scientist', time: '16:00', status: 'waiting' },
        { id: 6, name: '강민지', position: 'UI/UX Designer', time: '17:00', status: 'completed' },
    ];

    const itemsPerPage = 4;
    const totalPages = Math.ceil(todayCandidates.length / itemsPerPage);

    // 5초마다 자동 슬라이드
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentCandidatePage((prev) => (prev + 1) % totalPages);
        }, 5000);
        return () => clearInterval(interval);
    }, [totalPages]);

    const currentCandidates = todayCandidates.slice(
        currentCandidatePage * itemsPerPage,
        (currentCandidatePage + 1) * itemsPerPage
    );

    const maxValue = Math.max(...monthlyData.map(d => d.count));

    return (
        <div className="recruiter-main-container">
            {/* 사이드바 네비게이션 */}
            <aside className="recruiter-sidebar">

                <nav className="sidebar-nav">
                    <button
                        className={`nav-item ${activeMenu === 'dashboard' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('dashboard')}
                    >
                        <span className="nav-icon">📊</span>
                        <span className="nav-label">대시보드</span>
                    </button>

                    {/* 공고 관리 메뉴 (드롭다운) */}
                    <div className="nav-dropdown">
                        <button
                            className={`nav-item ${activeMenu === 'job-posting' ? 'active' : ''}`}
                            onClick={() => setJobPostingMenuOpen(!jobPostingMenuOpen)}
                        >
                            <span className="nav-icon">📝</span>
                            <span className="nav-label">공고 관리</span>
                            <span className={`dropdown-arrow ${jobPostingMenuOpen ? 'open' : ''}`}>▼</span>
                        </button>
                        {jobPostingMenuOpen && (
                            <div className="dropdown-menu">
                                <button className="dropdown-item">공고 등록</button>
                                <button className="dropdown-item">공고 목록</button>
                                <button className="dropdown-item">공고 통계</button>
                            </div>
                        )}
                    </div>

                    <button
                        className={`nav-item ${activeMenu === 'candidates' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('candidates')}
                    >
                        <span className="nav-icon">👥</span>
                        <span className="nav-label">지원자 관리</span>
                    </button>

                    <button
                        className={`nav-item ${activeMenu === 'interviews' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('interviews')}
                    >
                        <span className="nav-icon">🎤</span>
                        <span className="nav-label">면접 관리</span>
                    </button>

                    <button
                        className={`nav-item ${activeMenu === 'analytics' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('analytics')}
                    >
                        <span className="nav-icon">📈</span>
                        <span className="nav-label">분석 리포트</span>
                    </button>

                    <div className="nav-divider"></div>

                    <button
                        className={`nav-item ${activeMenu === 'settings' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('settings')}
                    >
                        <span className="nav-icon">⚙️</span>
                        <span className="nav-label">설정</span>
                    </button>
                </nav>
            </aside>

            {/* 메인 콘텐츠 영역 */}
            <main className="recruiter-main-content">
                {/* 헤더 영역 */}
                <header className="recruiter-header">
                    <div className="header-left">
                        <h1 className="dashboard-title">면접 운영 대시보드</h1>
                        <p className="dashboard-subtitle">실시간 면접 현황을 한눈에 확인하세요</p>
                    </div>

                    <div className="header-right">
                        <button className="notification-btn">
                            <span className="notification-icon">🔔</span>
                            <span className="notification-badge">3</span>
                        </button>

                        <div className="user-info-area">
                            <div className="user-text">
                                <p className="company-name">Big20 AI</p>
                                <p className="user-name">{user?.full_name || '관리자'}</p>
                            </div>
                            <div className="user-avatar">
                                <img src="/default-avatar.png" alt="Profile" onError={(e) => {
                                    e.target.style.display = 'none';
                                    e.target.nextSibling.style.display = 'flex';
                                }} />
                                <div className="avatar-placeholder" style={{ display: 'none' }}>
                                    {(user?.full_name || '관리자')[0]}
                                </div>
                            </div>
                        </div>


                    </div>
                </header>

                {/* 대시보드 콘텐츠 */}
                <div className="dashboard-content">
                    {/* 면접 현황 요약 카드 */}
                    <div className="stats-grid">
                        <div className="stat-card stat-card-primary">
                            <div className="stat-icon">📅</div>
                            <div className="stat-content">
                                <p className="stat-label">당일 예정 면접</p>
                                <h3 className="stat-value">{dashboardStats.todayInterviews}건</h3>
                                <div className={`stat-change ${dashboardStats.todayChange >= 0 ? 'positive' : 'negative'}`}>
                                    <span className="change-icon">{dashboardStats.todayChange >= 0 ? '↑' : '↓'}</span>
                                    <span className="change-value">{Math.abs(dashboardStats.todayChange)}%</span>
                                    <span className="change-label">전일 대비</span>
                                </div>
                            </div>
                        </div>

                        <div className="stat-card stat-card-success">
                            <div className="stat-icon">✅</div>
                            <div className="stat-content">
                                <p className="stat-label">누적 완료 면접</p>
                                <h3 className="stat-value">{dashboardStats.completedInterviews}건</h3>
                                <div className={`stat-change ${dashboardStats.completedChange >= 0 ? 'positive' : 'negative'}`}>
                                    <span className="change-icon">{dashboardStats.completedChange >= 0 ? '↑' : '↓'}</span>
                                    <span className="change-value">{Math.abs(dashboardStats.completedChange)}%</span>
                                    <span className="change-label">전월 대비</span>
                                </div>
                            </div>
                        </div>

                        <div className="stat-card stat-card-warning">
                            <div className="stat-icon">⏳</div>
                            <div className="stat-content">
                                <p className="stat-label">대기 중인 지원자</p>
                                <h3 className="stat-value">{dashboardStats.waitingCandidates}명</h3>
                                <p className="stat-description">면접 대기 중</p>
                            </div>
                        </div>
                    </div>

                    {/* 면접 진행 그래프 & 지원자 현황 */}
                    <div className="content-grid">
                        {/* 면접 진행 그래프 */}
                        <div className="chart-card">
                            <div className="card-header">
                                <h3 className="card-title">월별 면접 진행 현황</h3>
                                <select className="period-selector">
                                    <option>최근 6개월</option>
                                    <option>최근 1년</option>
                                </select>
                            </div>
                            <div className="chart-container">
                                <div className="bar-chart">
                                    {monthlyData.map((data, index) => (
                                        <div key={index} className="bar-item">
                                            <div className="bar-wrapper">
                                                <div
                                                    className="bar-fill"
                                                    style={{
                                                        height: `${(data.count / maxValue) * 100}%`,
                                                        animationDelay: `${index * 0.1}s`
                                                    }}
                                                >
                                                    <span className="bar-value">{data.count}</span>
                                                </div>
                                            </div>
                                            <span className="bar-label">{data.month}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* 지원자 진행 상태 */}
                        <div className="candidates-card">
                            <div className="card-header">
                                <h3 className="card-title">당일 면접 대상 지원자</h3>
                                <div className="pagination-dots">
                                    {Array.from({ length: totalPages }).map((_, index) => (
                                        <span
                                            key={index}
                                            className={`dot ${index === currentCandidatePage ? 'active' : ''}`}
                                            onClick={() => setCurrentCandidatePage(index)}
                                        ></span>
                                    ))}
                                </div>
                            </div>
                            <div className="candidates-list">
                                {currentCandidates.map((candidate) => (
                                    <div key={candidate.id} className="candidate-item">
                                        <div className="candidate-avatar">
                                            {candidate.name[0]}
                                        </div>
                                        <div className="candidate-info">
                                            <h4 className="candidate-name">{candidate.name}</h4>
                                            <p className="candidate-position">{candidate.position}</p>
                                        </div>
                                        <div className="candidate-meta">
                                            <span className="candidate-time">🕐 {candidate.time}</span>
                                            <span className={`candidate-status status-${candidate.status}`}>
                                                {candidate.status === 'waiting' ? '대기중' :
                                                    candidate.status === 'in-progress' ? '진행중' : '완료'}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default RecruiterMainPage;
