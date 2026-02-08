import React, { useState } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const AccountSettingsPage = ({ onBack }) => {
    // 비밀번호 변경
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [passwordError, setPasswordError] = useState('');

    // 알림 설정
    const [emailNotification, setEmailNotification] = useState(true);
    const [smsNotification, setSmsNotification] = useState(false);
    const [serviceNotification, setServiceNotification] = useState(true);

    // 약관 모달
    const [showTerms, setShowTerms] = useState(false);
    const [showPrivacy, setShowPrivacy] = useState(false);

    const handlePasswordChange = () => {
        // 비밀번호 일치 확인
        if (newPassword !== confirmPassword) {
            setPasswordError('새 비밀번호가 일치하지 않습니다.');
            return;
        }
        if (newPassword.length < 8) {
            setPasswordError('비밀번호는 최소 8자 이상이어야 합니다.');
            return;
        }
        setPasswordError('');
        alert('비밀번호가 변경되었습니다.');
        // API 호출 로직 추가
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
    };

    const handleSave = () => {
        alert('설정이 저장되었습니다.');
        // API 호출 로직 추가
    };

    const handleAccountSuspension = () => {
        if (confirm('계정을 휴면 상태로 전환하시겠습니까?')) {
            alert('계정이 휴면 상태로 전환되었습니다.');
            // API 호출 로직
        }
    };

    const handleAccountDeletion = () => {
        if (confirm('정말로 회원 탈퇴를 진행하시겠습니까?\n탈퇴 후 모든 데이터가 삭제되며 복구할 수 없습니다.')) {
            alert('회원 탈퇴가 완료되었습니다.');
            // API 호출 및 로그아웃 처리
            onBack();
        }
    };

    return (
        <div className="animate-fade-in" style={{ width: '100%', maxWidth: '900px', margin: '0 auto', padding: '2rem 1rem' }}>

            {/* 1. 헤더 영역 */}
            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>계정 설정</h2>
                <p style={{ color: 'var(--text-muted)' }}>계정 정보를 관리하고 알림 설정을 변경할 수 있습니다.</p>
            </div>

            {/* 2. 비밀번호 변경 영역 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    비밀번호 변경
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* 현재 비밀번호 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            현재 비밀번호
                        </label>
                        <input
                            type="password"
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            placeholder="현재 비밀번호를 입력하세요"
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        />
                    </div>

                    {/* 새 비밀번호 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            새 비밀번호
                        </label>
                        <input
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            placeholder="새 비밀번호를 입력하세요 (최소 8자)"
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        />
                    </div>

                    {/* 비밀번호 확인 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            비밀번호 확인
                        </label>
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="새 비밀번호를 다시 입력하세요"
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: `1px solid ${passwordError ? '#ef4444' : 'var(--glass-border)'}`,
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        />
                        {passwordError && (
                            <p style={{ color: '#ef4444', fontSize: '0.85rem', marginTop: '6px' }}>{passwordError}</p>
                        )}
                    </div>

                    <PremiumButton onClick={handlePasswordChange} style={{ alignSelf: 'flex-start', padding: '10px 24px' }}>
                        비밀번호 변경
                    </PremiumButton>
                </div>
            </GlassCard>

            {/* 3. 알림 설정 영역 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    알림 설정
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                    {/* 이메일 알림 */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={emailNotification}
                            onChange={(e) => setEmailNotification(e.target.checked)}
                            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                        />
                        <div>
                            <div style={{ fontWeight: '500' }}>이메일 알림</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>면접 결과 및 중요 공지를 이메일로 받습니다.</div>
                        </div>
                    </label>

                    {/* SMS 알림 */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={smsNotification}
                            onChange={(e) => setSmsNotification(e.target.checked)}
                            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                        />
                        <div>
                            <div style={{ fontWeight: '500' }}>SMS 알림</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>면접 일정 및 긴급 알림을 문자로 받습니다.</div>
                        </div>
                    </label>

                    {/* 서비스 알림 */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={serviceNotification}
                            onChange={(e) => setServiceNotification(e.target.checked)}
                            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                        />
                        <div>
                            <div style={{ fontWeight: '500' }}>서비스 알림</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>새로운 기능 및 업데이트 소식을 받습니다.</div>
                        </div>
                    </label>
                </div>
            </GlassCard>

            {/* 4. 계정 관리 영역 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    계정 관리
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {/* 계정 휴면 */}
                    <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                        <div style={{ marginBottom: '8px', fontWeight: '500' }}>계정 휴면 설정</div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                            일정 기간 서비스를 이용하지 않을 경우 계정을 휴면 상태로 전환할 수 있습니다.
                        </p>
                        <PremiumButton variant="secondary" onClick={handleAccountSuspension} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
                            계정 휴면 전환
                        </PremiumButton>
                    </div>

                    {/* 회원 탈퇴 */}
                    <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.05)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                        <div style={{ marginBottom: '8px', fontWeight: '500', color: '#ef4444' }}>회원 탈퇴</div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                            탈퇴 시 모든 데이터가 삭제되며 복구할 수 없습니다. 신중하게 결정해 주세요.
                        </p>
                        <PremiumButton
                            variant="secondary"
                            onClick={handleAccountDeletion}
                            style={{
                                padding: '8px 20px',
                                fontSize: '0.9rem',
                                borderColor: '#ef4444',
                                color: '#ef4444'
                            }}
                        >
                            회원 탈퇴
                        </PremiumButton>
                    </div>
                </div>
            </GlassCard>

            {/* 5. 서비스 이용 정보 및 약관 영역 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    서비스 이용 정보
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <button
                        onClick={() => setShowTerms(!showTerms)}
                        style={{
                            padding: '12px',
                            borderRadius: '8px',
                            border: '1px solid var(--glass-border)',
                            background: 'rgba(255,255,255,0.05)',
                            color: 'var(--text-main)',
                            textAlign: 'left',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            outline: 'none'
                        }}
                    >
                        <span>서비스 이용약관</span>
                        <span>{showTerms ? '▲' : '▼'}</span>
                    </button>
                    {showTerms && (
                        <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', fontSize: '0.9rem', color: 'var(--text-muted)', maxHeight: '200px', overflowY: 'auto' }}>
                            <p>제1조 (목적)</p>
                            <p>본 약관은 BIGVIEW(이하 "회사")가 제공하는 AI 면접 서비스의 이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.</p>
                            <br />
                            <p>제2조 (정의)</p>
                            <p>1. "서비스"란 회사가 제공하는 AI 기반 모의 면접 및 분석 서비스를 의미합니다.</p>
                            <p>2. "이용자"란 본 약관에 따라 회사가 제공하는 서비스를 이용하는 회원을 말합니다.</p>
                        </div>
                    )}

                    <button
                        onClick={() => setShowPrivacy(!showPrivacy)}
                        style={{
                            padding: '12px',
                            borderRadius: '8px',
                            border: '1px solid var(--glass-border)',
                            background: 'rgba(255,255,255,0.05)',
                            color: 'var(--text-main)',
                            textAlign: 'left',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            outline: 'none'
                        }}
                    >
                        <span>개인정보 처리방침</span>
                        <span>{showPrivacy ? '▲' : '▼'}</span>
                    </button>
                    {showPrivacy && (
                        <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', fontSize: '0.9rem', color: 'var(--text-muted)', maxHeight: '200px', overflowY: 'auto' }}>
                            <p>1. 개인정보의 수집 및 이용 목적</p>
                            <p>회사는 다음의 목적을 위하여 개인정보를 처리합니다. 처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며, 이용 목적이 변경되는 경우에는 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.</p>
                            <br />
                            <p>2. 수집하는 개인정보 항목</p>
                            <p>- 필수항목: 이메일, 비밀번호, 이름</p>
                            <p>- 선택항목: 전화번호, 지원 회사, 지원 직무</p>
                        </div>
                    )}
                </div>
            </GlassCard>

            {/* 6. 하단 버튼 영역 */}
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <PremiumButton variant="secondary" onClick={onBack} style={{ padding: '12px 32px' }}>
                    취소
                </PremiumButton>
                <PremiumButton onClick={handleSave} style={{ padding: '12px 32px' }}>
                    저장
                </PremiumButton>
            </div>

        </div>
    );
};

export default AccountSettingsPage;
