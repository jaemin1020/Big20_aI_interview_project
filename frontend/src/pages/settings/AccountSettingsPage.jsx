import React, { useState } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import { changePassword, withdrawUser } from '../../api/interview';

const AccountSettingsPage = ({ onBack, onLogout }) => {
    // 비밀번호 변경
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [pwErrors, setPwErrors] = useState({});
    const [isSavingPw, setIsSavingPw] = useState(false);
    const [showNew, setShowNew] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);

    // 알림 설정
    const [emailNotification, setEmailNotification] = useState(true);
    const [smsNotification, setSmsNotification] = useState(false);
    const [serviceNotification, setServiceNotification] = useState(true);

    // 약관 모달
    const [showTerms, setShowTerms] = useState(false);
    const [showPrivacy, setShowPrivacy] = useState(false);

    // 비밀번호 강도 계산
    const getPasswordStrength = (pw) => {
        if (!pw) return null;
        let score = 0;
        if (pw.length >= 8) score++;
        if (pw.length >= 12) score++;
        if (/[a-zA-Z]/.test(pw)) score++;
        if (/[0-9]/.test(pw)) score++;
        if (/[^a-zA-Z0-9]/.test(pw)) score++;
        if (score <= 2) return { label: '약함', color: '#ef4444', width: '33%' };
        if (score <= 3) return { label: '보통', color: '#f59e0b', width: '66%' };
        return { label: '강함', color: '#22c55e', width: '100%' };
    };

    const strength = getPasswordStrength(newPassword);

    // 비밀번호 유효성 검사
    const validatePassword = () => {
        const errs = {};
        if (!newPassword) {
            errs.newPassword = '새 비밀번호를 입력해주세요.';
        } else if (newPassword.length < 8) {
            errs.newPassword = '비밀번호는 최소 8자 이상이어야 합니다.';
        }
        if (!confirmPassword) {
            errs.confirmPassword = '비밀번호 확인을 입력해주세요.';
        } else if (newPassword !== confirmPassword) {
            errs.confirmPassword = '비밀번호가 일치하지 않습니다.';
        }
        setPwErrors(errs);
        return Object.keys(errs).length === 0;
    };

    const handlePasswordChange = async () => {
        if (!validatePassword()) return;
        setIsSavingPw(true);
        try {
            await changePassword(newPassword);
            alert('비밀번호가 변경되었습니다.');
            setNewPassword('');
            setConfirmPassword('');
            setPwErrors({});
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || '변경 중 오류가 발생했습니다.';
            alert(`비밀번호 변경 실패: ${msg}`);
        } finally {
            setIsSavingPw(false);
        }
    };

    const handleAccountSuspension = () => {
        if (confirm('계정을 휴면 상태로 전환하시겠습니까?')) {
            alert('계정이 휴면 상태로 전환되었습니다.');
        }
    };

    const handleAccountDeletion = async () => {
        if (!confirm('정말로 회원 탈퇴를 진행하시겠습니까?\n탈퇴 후 로그인이 불가능하며, 동일 아이디/이메일로 재가입할 수 있습니다.')) return;
        try {
            await withdrawUser();
            alert('회원 탈퇴가 완료되었습니다.');
            onLogout(); // App.jsx의 로그아웃 로직 호출
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || '탈퇴 중 오류가 발생했습니다.';
            alert(`탈퇴 실패: ${msg}`);
        }
    };

    const inputStyle = (hasError) => ({
        width: '100%',
        padding: '12px 44px 12px 12px',
        borderRadius: '8px',
        border: `1px solid ${hasError ? '#ef4444' : 'var(--glass-border)'}`,
        background: hasError ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.05)',
        color: 'var(--text-main)',
        outline: 'none',
        transition: 'border-color 0.2s',
        boxSizing: 'border-box',
    });

    const EyeBtn = ({ visible, onToggle }) => (
        <button
            type="button"
            onClick={onToggle}
            style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-muted)', fontSize: '1rem', padding: 0
            }}
        >
            {visible ? '🙈' : '👁️'}
        </button>
    );

    return (
        <div className="animate-fade-in" style={{ width: '100%', maxWidth: '900px', margin: '0 auto', padding: '2rem 1rem' }}>

            {/* 1. 헤더 */}
            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>⚙️ 계정 설정</h2>
                <p style={{ color: 'var(--text-muted)' }}>계정 정보를 관리하고 알림 설정을 변경할 수 있습니다.</p>
            </div>

            {/* 2. 비밀번호 변경 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    🔐 비밀번호 변경
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem', maxWidth: '480px' }}>

                    {/* 새 비밀번호 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            새 비밀번호 <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <div style={{ position: 'relative' }}>
                            <input
                                type={showNew ? 'text' : 'password'}
                                value={newPassword}
                                onChange={(e) => {
                                    setNewPassword(e.target.value);
                                    if (pwErrors.newPassword) setPwErrors(prev => ({ ...prev, newPassword: '' }));
                                }}
                                placeholder="새 비밀번호 입력 (최소 8자, 영문+숫자)"
                                style={inputStyle(!!pwErrors.newPassword)}
                            />
                            <EyeBtn visible={showNew} onToggle={() => setShowNew(v => !v)} />
                        </div>
                        {/* 강도 바 */}
                        {newPassword && strength && (
                            <div style={{ marginTop: '8px' }}>
                                <div style={{ height: '4px', borderRadius: '2px', background: 'var(--glass-border)', overflow: 'hidden' }}>
                                    <div style={{ height: '100%', width: strength.width, background: strength.color, transition: 'width 0.3s, background 0.3s' }} />
                                </div>
                                <p style={{ fontSize: '0.78rem', color: strength.color, marginTop: '4px' }}>
                                    비밀번호 강도: {strength.label}
                                </p>
                            </div>
                        )}
                        {pwErrors.newPassword && (
                            <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>⚠ {pwErrors.newPassword}</p>
                        )}
                    </div>

                    {/* 비밀번호 확인 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            비밀번호 확인 <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <div style={{ position: 'relative' }}>
                            <input
                                type={showConfirm ? 'text' : 'password'}
                                value={confirmPassword}
                                onChange={(e) => {
                                    setConfirmPassword(e.target.value);
                                    if (pwErrors.confirmPassword) setPwErrors(prev => ({ ...prev, confirmPassword: '' }));
                                }}
                                placeholder="새 비밀번호를 다시 입력하세요"
                                style={inputStyle(!!pwErrors.confirmPassword)}
                            />
                            <EyeBtn visible={showConfirm} onToggle={() => setShowConfirm(v => !v)} />
                        </div>
                        {/* 실시간 일치 여부 */}
                        {confirmPassword && newPassword && (
                            <p style={{ fontSize: '0.8rem', marginTop: '6px', color: newPassword === confirmPassword ? '#22c55e' : '#ef4444' }}>
                                {newPassword === confirmPassword ? '✅ 비밀번호가 일치합니다.' : '⚠ 비밀번호가 일치하지 않습니다.'}
                            </p>
                        )}
                        {pwErrors.confirmPassword && !confirmPassword && (
                            <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>⚠ {pwErrors.confirmPassword}</p>
                        )}
                    </div>

                    <PremiumButton
                        onClick={handlePasswordChange}
                        disabled={isSavingPw}
                        style={{ alignSelf: 'flex-start', padding: '10px 28px' }}
                    >
                        {isSavingPw ? '변경 중...' : '비밀번호 변경'}
                    </PremiumButton>
                </div>
            </GlassCard>

            {/* 3. 알림 설정 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    🔔 알림 설정
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                    {[
                        { label: '이메일 알림', desc: '면접 결과 및 중요 공지를 이메일로 받습니다.', checked: emailNotification, onChange: setEmailNotification },
                        { label: 'SMS 알림', desc: '면접 일정 및 긴급 알림을 문자로 받습니다.', checked: smsNotification, onChange: setSmsNotification },
                        { label: '서비스 알림', desc: '새로운 기능 및 업데이트 소식을 받습니다.', checked: serviceNotification, onChange: setServiceNotification },
                    ].map(({ label, desc, checked, onChange }) => (
                        <label key={label} style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={checked}
                                onChange={(e) => onChange(e.target.checked)}
                                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                            />
                            <div>
                                <div style={{ fontWeight: '500' }}>{label}</div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{desc}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </GlassCard>

            {/* 4. 계정 관리 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    계정 관리
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                        <div style={{ marginBottom: '8px', fontWeight: '500' }}>계정 휴면 설정</div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                            일정 기간 서비스를 이용하지 않을 경우 계정을 휴면 상태로 전환할 수 있습니다.
                        </p>
                        <PremiumButton variant="secondary" onClick={handleAccountSuspension} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
                            계정 휴면 전환
                        </PremiumButton>
                    </div>
                    <div style={{ padding: '1rem', background: 'rgba(239,68,68,0.05)', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.2)' }}>
                        <div style={{ marginBottom: '8px', fontWeight: '500', color: '#ef4444' }}>회원 탈퇴</div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                            탈퇴 시 모든 데이터가 삭제되며 복구할 수 없습니다. 신중하게 결정해 주세요.
                        </p>
                        <PremiumButton
                            variant="secondary"
                            onClick={handleAccountDeletion}
                            style={{ padding: '8px 20px', fontSize: '0.9rem', borderColor: '#ef4444', color: '#ef4444' }}
                        >
                            회원 탈퇴
                        </PremiumButton>
                    </div>
                </div>
            </GlassCard>

            {/* 5. 서비스 이용 정보 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    서비스 이용 정보
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {[
                        {
                            label: '서비스 이용약관', key: 'terms', show: showTerms, toggle: () => setShowTerms(v => !v),
                            content: (
                                <>
                                    <p>제1조 (목적)</p>
                                    <p>본 약관은 BIGVIEW(이하 "회사")가 제공하는 AI 면접 서비스의 이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.</p>
                                    <br />
                                    <p>제2조 (정의)</p>
                                    <p>1. "서비스"란 회사가 제공하는 AI 기반 모의 면접 및 분석 서비스를 의미합니다.</p>
                                    <p>2. "이용자"란 본 약관에 따라 회사가 제공하는 서비스를 이용하는 회원을 말합니다.</p>
                                </>
                            )
                        },
                        {
                            label: '개인정보 처리방침', key: 'privacy', show: showPrivacy, toggle: () => setShowPrivacy(v => !v),
                            content: (
                                <>
                                    <p>1. 개인정보의 수집 및 이용 목적</p>
                                    <p>회사는 다음의 목적을 위하여 개인정보를 처리합니다.</p>
                                    <br />
                                    <p>2. 수집하는 개인정보 항목</p>
                                    <p>- 필수항목: 이메일, 비밀번호, 이름</p>
                                    <p>- 선택항목: 전화번호, 지원 회사, 지원 직무</p>
                                </>
                            )
                        }
                    ].map(({ label, key, show, toggle, content }) => (
                        <div key={key}>
                            <button
                                onClick={toggle}
                                style={{
                                    width: '100%', padding: '12px', borderRadius: '8px',
                                    border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)',
                                    color: 'var(--text-main)', textAlign: 'left', cursor: 'pointer',
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', outline: 'none'
                                }}
                            >
                                <span>{label}</span>
                                <span>{show ? '▲' : '▼'}</span>
                            </button>
                            {show && (
                                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0 0 8px 8px', fontSize: '0.9rem', color: 'var(--text-muted)', maxHeight: '200px', overflowY: 'auto' }}>
                                    {content}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </GlassCard>

            {/* 6. 하단 버튼 */}
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <PremiumButton variant="secondary" onClick={onBack} style={{ padding: '12px 32px' }}>
                    닫기
                </PremiumButton>
            </div>

        </div>
    );
};

export default AccountSettingsPage;
