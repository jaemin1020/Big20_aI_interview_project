import React, { useState, useEffect } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import { getAllInterviews, getEvaluationReport } from '../../api/interview';

const InterviewHistoryPage = ({ onBack, onViewResult }) => {
    const [interviews, setInterviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Filters
    const [dateFilter, setDateFilter] = useState('all'); // all, 1month, 3month, 6month, custom
    const [customStartDate, setCustomStartDate] = useState('');
    const [customEndDate, setCustomEndDate] = useState('');
    const [companyFilter, setCompanyFilter] = useState('');
    const [positionFilter, setPositionFilter] = useState('');

    useEffect(() => {
        fetchInterviews();
    }, []);

    const fetchInterviews = async () => {
        try {
            setLoading(true);
            const data = await getAllInterviews();
            // 최신순 정렬
            const sortedData = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setInterviews(sortedData);
        } catch (err) {
            console.error("Failed to fetch interviews:", err);
            // setError("면접 기록을 불러오는데 실패했습니다."); // 조용히 실패 처리
            // 더미 데이터 (테스트용) - API 실패 시 보여줄지 여부는 선택사항이나, 여기서는 빈 배열로 둠.
            setInterviews([]);
        } finally {
            setLoading(false);
        }
    };

    // 고유한 회사명과 직무 목록 추출
    const uniqueCompanies = [...new Set(interviews.map(item => item.company_name).filter(Boolean))];
    const uniquePositions = [...new Set(interviews.map(item => item.position).filter(Boolean))];

    const handleSearch = () => {
        // 필터링은 클라이언트 사이드에서 처리 (데이터 양이 많지 않을 것으로 가정)
        // 실제로는 API에 파라미터를 보내는 것이 좋음.
        console.log("Filtering with:", { dateFilter, companyFilter, positionFilter });
    };

    const filteredInterviews = interviews.filter(item => {
        // 1. Company Filter
        if (companyFilter && companyFilter !== item.company_name) {
            return false;
        }
        // 2. Position Filter
        if (positionFilter && positionFilter !== item.position) {
            return false;
        }
        // 3. Date Filter
        if (dateFilter !== 'all') {
            const itemDate = new Date(item.created_at);
            const now = new Date();
            if (dateFilter === '1month') {
                const oneMonthAgo = new Date(now.setMonth(now.getMonth() - 1));
                if (itemDate < oneMonthAgo) return false;
            } else if (dateFilter === '3month') {
                const threeMonthsAgo = new Date(now.setMonth(now.getMonth() - 3));
                if (itemDate < threeMonthsAgo) return false;
            } else if (dateFilter === 'custom' && customStartDate && customEndDate) {
                const start = new Date(customStartDate);
                const end = new Date(customEndDate);
                end.setHours(23, 59, 59); // Include the end date
                if (itemDate < start || itemDate > end) return false;
            }
        }
        return true;
    });

    const handleViewDetail = async (interviewId) => {
        try {
            const interview = interviews.find(i => i.id === interviewId);
            try {
                // 리포트 데이터 가져오기 시도
                const report = await getEvaluationReport(interviewId);
                onViewResult(report, interview);
            } catch (err) {
                console.warn("Report fetch failed, showing placeholder:", err);
                // 리포트가 없어도 결과 페이지로 이동 (더미 데이터 사용)
                onViewResult(null, interview);
            }
        } catch (err) {
            console.error("Error in handleViewDetail:", err);
            alert("상세 정보를 불러오는 중 오류가 발생했습니다.");
        }
    };

    return (
        <div className="animate-fade-in" style={{ width: '100%', maxWidth: '1000px', margin: '0 auto', padding: '2rem 1rem' }}>

            {/* 1. 헤더 영역 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>면접 이력 조회</h2>
                    <p style={{ color: 'var(--text-muted)' }}>나의 면접 기록과 분석 결과를 한눈에 확인하세요.</p>
                </div>
                <PremiumButton variant="secondary" onClick={onBack} style={{ padding: '10px 20px' }}>
                    홈으로 이동
                </PremiumButton>
            </div>

            {/* 2. 필터 영역 (GlassCard) */}
            <GlassCard className="filter-section" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
                {/* 첫 번째 행: 모든 필터 */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', alignItems: 'end' }}>

                    {/* 기간 필터 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>조회 기간</label>
                        <select
                            value={dateFilter}
                            onChange={(e) => setDateFilter(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        >
                            <option value="all">전체 기간</option>
                            <option value="1month">최근 1개월</option>
                            <option value="3month">최근 3개월</option>
                            <option value="custom">직접 입력</option>
                        </select>
                    </div>

                    {/* 회사명 필터 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>지원 회사</label>
                        <select
                            value={companyFilter}
                            onChange={(e) => setCompanyFilter(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        >
                            <option value="">전체 회사</option>
                            {uniqueCompanies.map(company => (
                                <option key={company} value={company}>{company}</option>
                            ))}
                        </select>
                    </div>

                    {/* 직무 필터 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>지원 직무</label>
                        <select
                            value={positionFilter}
                            onChange={(e) => setPositionFilter(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        >
                            <option value="">전체 직무</option>
                            {uniquePositions.map(position => (
                                <option key={position} value={position}>{position}</option>
                            ))}
                        </select>
                    </div>

                    {/* 검색 버튼 */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <PremiumButton onClick={handleSearch} style={{ width: '100%', padding: '10px' }}>
                            검색 적용
                        </PremiumButton>
                    </div>
                </div>

                {/* 두 번째 행: 직접 입력 날짜 (조건부 표시) */}
                {dateFilter === 'custom' && (
                    <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <label style={{ color: 'var(--text-muted)', fontSize: '0.9rem', minWidth: '80px' }}>기간 선택:</label>
                        <input
                            type="date"
                            value={customStartDate}
                            onChange={(e) => setCustomStartDate(e.target.value)}
                            style={{
                                flex: 1,
                                padding: '10px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        />
                        <span style={{ color: 'var(--text-muted)' }}>~</span>
                        <input
                            type="date"
                            value={customEndDate}
                            onChange={(e) => setCustomEndDate(e.target.value)}
                            style={{
                                flex: 1,
                                padding: '10px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        />
                    </div>
                )}
            </GlassCard>

            {/* 3. 리스트 영역 */}
            <div>
                <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderLeft: '4px solid var(--primary)', paddingLeft: '10px' }}>
                    총 <span style={{ color: 'var(--primary)' }}>{filteredInterviews.length}</span>건의 기록이 있습니다.
                </h3>

                {loading ? (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
                        <div className="spinner"></div>
                    </div>
                ) : filteredInterviews.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '4rem', background: 'var(--glass-bg)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>검색 조건에 맞는 면접 기록이 없습니다.</p>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {filteredInterviews.map((item) => (
                            <GlassCard key={item.id} style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', transition: 'transform 0.2s', cursor: 'default' }}>
                                <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
                                    {/* 날짜 배지 */}
                                    <div style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        background: 'rgba(255,255,255,0.05)',
                                        padding: '10px',
                                        borderRadius: '12px',
                                        minWidth: '80px',
                                        border: '1px solid var(--glass-border)'
                                    }}>
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{new Date(item.created_at).getFullYear()}</span>
                                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                                            {new Date(item.created_at).toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' })}
                                        </span>
                                    </div>

                                    {/* 정보 */}
                                    <div>
                                        <h4 style={{ fontSize: '1.2rem', marginBottom: '4px' }}>{item.position || '직무 미정'}</h4>
                                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                                            {item.company_name || '회사명 미입력'} | {item.status === 'completed' ? '완료됨' : '진행 중'}
                                        </p>
                                    </div>
                                </div>

                                {/* 액션 */}
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    {/* 상태 뱃지 */}
                                    <div style={{
                                        padding: '6px 12px',
                                        borderRadius: '20px',
                                        fontSize: '0.8rem',
                                        background: item.status === 'completed' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(234, 179, 8, 0.1)',
                                        color: item.status === 'completed' ? '#22c55e' : '#eab308',
                                        border: `1px solid ${item.status === 'completed' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(234, 179, 8, 0.2)'}`,
                                        display: 'flex',
                                        alignItems: 'center',
                                        marginRight: '10px'
                                    }}>
                                        {item.status === 'completed' ? '분석 완료' : '미완료'}
                                    </div>

                                    <PremiumButton
                                        variant="secondary"
                                        onClick={() => handleViewDetail(item.id)}
                                        disabled={item.status !== 'completed'}
                                        style={{ padding: '8px 20px', fontSize: '0.9rem', opacity: item.status === 'completed' ? 1 : 0.5 }}
                                    >
                                        상세보기
                                    </PremiumButton>
                                </div>
                            </GlassCard>
                        ))}
                    </div>
                )}
            </div>

        </div>
    );
};

export default InterviewHistoryPage;
