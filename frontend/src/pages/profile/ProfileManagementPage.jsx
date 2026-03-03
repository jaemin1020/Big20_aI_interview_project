import React, { useState, useMemo, useEffect, useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import { updateUserProfile } from '../../api/interview';

const ProfileManagementPage = ({ onBack, user, onSave, onDirtyChange, saveTriggerRef }) => {
    // 프로필 이미지
    // 프로필 이미지 (백엔드 URL 또는 base64)
    const [profileImage, setProfileImage] = useState(user?.profile_image || null);
    const [imagePreview, setImagePreview] = useState(user?.profile_image || null);

    // 희망 지원 정보 (복수 선택)
    const [desiredCompanyTypes, setDesiredCompanyTypes] = useState(user?.desired_company_types || []);
    const [desiredPositions, setDesiredPositions] = useState(user?.desired_positions || []);

    // 개인 정보 (회원가입 시 입력한 정보를 기본값으로 - DB 필드명 snake_case 주의)
    const [name, setName] = useState(user?.full_name || '');
    const [birthDate, setBirthDate] = useState(user?.birth_date || '');
    const [email, setEmail] = useState(user?.email || '');
    const [phone, setPhone] = useState(user?.phone_number || '');

    // 변경사항 감지: 원본 값과 현재 값 비교
    const isDirty = useMemo(() => {
        const origCompanyTypes = JSON.stringify([...(user?.desired_company_types || [])].sort());
        const origPositions = JSON.stringify([...(user?.desired_positions || [])].sort());
        const curCompanyTypes = JSON.stringify([...desiredCompanyTypes].sort());
        const curPositions = JSON.stringify([...desiredPositions].sort());
        return (
            name !== (user?.full_name || '') ||
            birthDate !== (user?.birth_date || '') ||
            email !== (user?.email || '') ||
            phone !== (user?.phone_number || '') ||
            profileImage instanceof File ||
            curCompanyTypes !== origCompanyTypes ||
            curPositions !== origPositions
        );
    }, [name, birthDate, email, phone, profileImage, desiredCompanyTypes, desiredPositions, user]);



    // isDirty 변화를 부모(App.jsx)에 알림
    useEffect(() => {
        if (onDirtyChange) onDirtyChange(isDirty);
    }, [isDirty]);

    // App.jsx의 네비게이션 가드 모달에서 호출할 저장 함수 등록
    // 성공 시 true 반환, 실패(유효성 오류/API 오류) 시 false 반환
    useEffect(() => {
        if (!saveTriggerRef) return;
        saveTriggerRef.current = async () => {
            if (!validate()) return false;
            try {
                const updatedUser = await updateUserProfile({
                    fullName: name,
                    birthDate,
                    email,
                    phoneNumber: phone,
                    profileImageFile: profileImage instanceof File ? profileImage : undefined,
                    desiredCompanyTypes,
                    desiredPositions,
                });
                if (onSave) onSave(updatedUser);
                return true;
            } catch (err) {
                const msg = err.response?.data?.detail || err.message || '저장 중 오류가 발생했습니다.';
                alert(`저장 실패: ${msg}`);
                return false;
            }
        };
    });

    const companyTypeOptions = [
        '대기업', '중견기업', '중소기업', '스타트업', '외국계기업', '공기업'
    ];

    const positionOptions = [
        '프론트엔드 개발자', '백엔드 개발자', '풀스택 개발자',
        '데이터 엔지니어', 'AI/ML 엔지니어', 'DevOps 엔지니어',
        'QA 엔지니어', '프로덕트 매니저', 'UI/UX 디자이너', '기타'
    ];

    const handleCompanyTypeToggle = (type) => {
        setDesiredCompanyTypes(prev =>
            prev.includes(type)
                ? prev.filter(t => t !== type)
                : [...prev, type]
        );
    };

    const handlePositionToggle = (position) => {
        setDesiredPositions(prev =>
            prev.includes(position)
                ? prev.filter(p => p !== position)
                : [...prev, position]
        );
    };

    const [isDragging, setIsDragging] = useState(false);

    const handleFile = (file) => {
        if (file && file.type.startsWith('image/')) {
            setProfileImage(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
            };
            reader.readAsDataURL(file);
        } else if (file) {
            alert("이미지 파일만 업로드 가능합니다.");
        }
    };

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    const [isSaving, setIsSaving] = useState(false);
    const [errors, setErrors] = useState({});

    const today = new Date().toISOString().split('T')[0];

    const validate = () => {
        const newErrors = {};
        if (!name.trim()) newErrors.name = '이름은 필수 입력 항목입니다.';
        if (!birthDate.trim()) {
            newErrors.birthDate = '생년월일은 필수 입력 항목입니다.';
        } else if (birthDate.length < 10) {
            newErrors.birthDate = '생년월일을 올바르게 입력해주세요. (예: 1990-01-01)';
        } else if (birthDate > today) {
            newErrors.birthDate = '생년월일은 오늘 날짜 이전이어야 합니다.';
        }
        if (!email.trim()) {
            newErrors.email = '이메일은 필수 입력 항목입니다.';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            newErrors.email = '올바른 이메일 형식을 입력해주세요.';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSave = async () => {
        if (!validate()) return;
        setIsSaving(true);
        try {
            const updatedUser = await updateUserProfile({
                fullName: name,
                birthDate,
                email,
                phoneNumber: phone,
                profileImageFile: profileImage instanceof File ? profileImage : undefined,
                desiredCompanyTypes,
                desiredPositions,
            });
            // 부모(App.jsx)의 user 상태 갱신
            if (onSave) onSave(updatedUser);
            alert('프로필이 저장되었습니다.');
            onBack(true); // force=true 전달하여 확인 모달 없이 즉시 이동
        } catch (err) {
            console.error('프로필 저장 실패:', err);
            const msg = err.response?.data?.detail || err.message || '저장 중 오류가 발생했습니다.';
            alert(`저장 실패: ${msg}`);
        } finally {
            setIsSaving(false);
        }
    };


    return (
        <div className="animate-fade-in" style={{ width: '100%', maxWidth: '900px', margin: '0 auto', padding: '2rem 1rem' }}>



            {/* 1. 헤더 영역 */}
            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>프로필 관리</h2>
                <p style={{ color: 'var(--text-muted)' }}>프로필 정보를 수정하고 희망 지원 정보를 입력할 수 있습니다.</p>
            </div>

            {/* 2. 프로필 이미지 영역 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    프로필 이미지
                </h3>

                <div
                    style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                >
                    {/* 프로필 이미지 미리보기 */}
                    <div
                        onClick={() => document.getElementById('profile-image-upload')?.click()}
                        style={{
                            width: '150px',
                            height: '150px',
                            borderRadius: '50%',
                            overflow: 'hidden',
                            border: `3px solid ${isDragging ? 'var(--primary)' : 'var(--glass-border)'}`,
                            background: isDragging ? 'rgba(99, 102, 241, 0.1)' : 'var(--glass-bg)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            transform: isDragging ? 'scale(1.05)' : 'scale(1)',
                            boxShadow: isDragging ? '0 0 20px rgba(99, 102, 241, 0.3)' : 'none'
                        }}
                    >
                        {imagePreview ? (
                            <img src={imagePreview} alt="프로필" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                            <div style={{ fontSize: '4rem', color: isDragging ? 'var(--primary)' : 'var(--text-muted)' }}>👤</div>
                        )}
                    </div>

                    {/* 업로드 버튼 */}
                    <div>
                        <input
                            type="file"
                            id="profile-image-upload"
                            accept="image/*"
                            onChange={handleImageUpload}
                            style={{ position: 'absolute', opacity: 0, width: 0, height: 0, pointerEvents: 'none' }}
                        />
                        <label
                            htmlFor="profile-image-upload"
                            style={{ cursor: 'pointer', display: 'inline-block' }}
                        >
                            <PremiumButton
                                as="span"
                                variant="secondary"
                                style={{ padding: '10px 24px', pointerEvents: 'none' }}
                            >
                                이미지 업로드
                            </PremiumButton>
                        </label>
                        <p style={{ fontSize: '0.85rem', color: isDragging ? 'var(--primary)' : 'var(--text-muted)', marginTop: '8px', fontWeight: isDragging ? '600' : '400' }}>
                            {isDragging ? '여기에 이미지를 놓으세요!' : 'JPG, PNG 파일 (최대 5MB) - 드래그 앤 드롭 지원'}
                        </p>
                    </div>
                </div>
            </GlassCard>

            {/* 3. 희망 지원 정보 영역 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    희망 지원 정보
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                    {/* 희망 기업 유형 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '12px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            희망 기업 유형 (복수 선택 가능)
                        </label>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
                            gap: '12px',
                            padding: '1rem',
                            background: 'rgba(255,255,255,0.03)',
                            borderRadius: '8px',
                            border: '1px solid var(--glass-border)'
                        }}>
                            {companyTypeOptions.map(type => (
                                <label
                                    key={type}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        cursor: 'pointer',
                                        padding: '8px',
                                        borderRadius: '6px',
                                        background: desiredCompanyTypes.includes(type) ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                        border: `1px solid ${desiredCompanyTypes.includes(type) ? '#6366f1' : 'transparent'}`,
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <input
                                        type="checkbox"
                                        checked={desiredCompanyTypes.includes(type)}
                                        onChange={() => handleCompanyTypeToggle(type)}
                                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                                    />
                                    <span style={{ fontSize: '0.9rem' }}>{type}</span>
                                </label>
                            ))}
                        </div>
                        {desiredCompanyTypes.length > 0 && (
                            <p style={{ fontSize: '0.85rem', color: '#6366f1', marginTop: '8px' }}>
                                선택됨: {desiredCompanyTypes.join(', ')}
                            </p>
                        )}
                    </div>

                    {/* 희망 직무 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '12px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            희망 직무 (복수 선택 가능)
                        </label>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                            gap: '12px',
                            padding: '1rem',
                            background: 'rgba(255,255,255,0.03)',
                            borderRadius: '8px',
                            border: '1px solid var(--glass-border)'
                        }}>
                            {positionOptions.map(position => (
                                <label
                                    key={position}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        cursor: 'pointer',
                                        padding: '8px',
                                        borderRadius: '6px',
                                        background: desiredPositions.includes(position) ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                        border: `1px solid ${desiredPositions.includes(position) ? '#6366f1' : 'transparent'}`,
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <input
                                        type="checkbox"
                                        checked={desiredPositions.includes(position)}
                                        onChange={() => handlePositionToggle(position)}
                                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                                    />
                                    <span style={{ fontSize: '0.9rem' }}>{position}</span>
                                </label>
                            ))}
                        </div>
                        {desiredPositions.length > 0 && (
                            <p style={{ fontSize: '0.85rem', color: '#6366f1', marginTop: '8px' }}>
                                선택됨: {desiredPositions.join(', ')}
                            </p>
                        )}
                    </div>
                </div>
            </GlassCard>

            {/* 4. 개인 정보 영역 */}
            <GlassCard style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', paddingLeft: '12px' }}>
                    개인 정보
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                    {/* 이름 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            이름 <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => { setName(e.target.value); if (errors.name) setErrors(prev => ({ ...prev, name: '' })); }}
                            placeholder="이름을 입력하세요"
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: `1px solid ${errors.name ? '#ef4444' : 'var(--glass-border)'}`,
                                background: errors.name ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none',
                                transition: 'border-color 0.2s'
                            }}
                        />
                        {errors.name && <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>⚠ {errors.name}</p>}
                    </div>

                    {/* 생년월일 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            생년월일 <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <input
                            type="date"
                            max={today}
                            value={birthDate}
                            onChange={(e) => {
                                setBirthDate(e.target.value);
                                if (errors.birthDate) setErrors(prev => ({ ...prev, birthDate: '' }));
                            }}
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: `1px solid ${errors.birthDate ? '#ef4444' : 'var(--glass-border)'}`,
                                background: errors.birthDate ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none',
                                transition: 'border-color 0.2s',
                                colorScheme: 'dark'
                            }}
                        />
                        {errors.birthDate && <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>⚠ {errors.birthDate}</p>}
                    </div>

                    {/* 이메일 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            이메일 <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => { setEmail(e.target.value); if (errors.email) setErrors(prev => ({ ...prev, email: '' })); }}
                            placeholder="example@email.com"
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: `1px solid ${errors.email ? '#ef4444' : 'var(--glass-border)'}`,
                                background: errors.email ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.05)',
                                color: 'var(--text-main)',
                                outline: 'none',
                                transition: 'border-color 0.2s'
                            }}
                        />
                        {errors.email && <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>⚠ {errors.email}</p>}
                    </div>

                    {/* 연락처 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            연락처
                        </label>
                        <input
                            type="tel"
                            value={phone}
                            onChange={(e) => setPhone(e.target.value)}
                            placeholder="010-0000-0000"
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
                </div>
            </GlassCard>

            {/* 5. 하단 버튼 영역 */}
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <PremiumButton variant="secondary" onClick={onBack} style={{ padding: '12px 32px' }}>
                    취소
                </PremiumButton>
                <PremiumButton onClick={handleSave} style={{ padding: '12px 32px' }} disabled={isSaving}>
                    {isSaving ? '저장 중...' : '저장'}
                </PremiumButton>
            </div>

        </div>
    );
};

export default ProfileManagementPage;
