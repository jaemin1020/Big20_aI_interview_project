import React, { useState } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const ProfileManagementPage = ({ onBack, user }) => {
    // 프로필 이미지
    const [profileImage, setProfileImage] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);

    // 희망 지원 정보 (복수 선택)
    const [desiredCompanyTypes, setDesiredCompanyTypes] = useState([]);
    const [desiredPositions, setDesiredPositions] = useState([]);

    // 개인 정보 (회원가입 시 입력한 정보를 기본값으로)
    const [name, setName] = useState(user?.name || '');
    const [birthDate, setBirthDate] = useState(user?.birthDate || '');
    const [email, setEmail] = useState(user?.email || '');
    const [phone, setPhone] = useState(user?.phone || '');

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

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            setProfileImage(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSave = () => {
        // API 호출 로직
        const profileData = {
            profileImage,
            desiredCompanyTypes,
            desiredPositions,
            name,
            birthDate,
            email,
            phone
        };
        console.log('저장할 프로필 데이터:', profileData);
        alert('프로필이 저장되었습니다.');
        // 실제 API 호출 후 onBack() 호출
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

                <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    {/* 프로필 이미지 미리보기 */}
                    <div style={{
                        width: '150px',
                        height: '150px',
                        borderRadius: '50%',
                        overflow: 'hidden',
                        border: '3px solid var(--glass-border)',
                        background: 'var(--glass-bg)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        {imagePreview ? (
                            <img src={imagePreview} alt="프로필" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                            <div style={{ fontSize: '4rem', color: 'var(--text-muted)' }}>👤</div>
                        )}
                    </div>

                    {/* 업로드 버튼 */}
                    <div>
                        <input
                            type="file"
                            id="profile-image-upload"
                            accept="image/*"
                            onChange={handleImageUpload}
                            style={{ display: 'none' }}
                        />
                        <label htmlFor="profile-image-upload">
                            <PremiumButton
                                as="span"
                                variant="secondary"
                                style={{ padding: '10px 24px', cursor: 'pointer', display: 'inline-block' }}
                            >
                                이미지 업로드
                            </PremiumButton>
                        </label>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                            JPG, PNG 파일 (최대 5MB)
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
                            onChange={(e) => setName(e.target.value)}
                            placeholder="이름을 입력하세요"
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

                    {/* 생년월일 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            생년월일
                        </label>
                        <input
                            type="text"
                            value={birthDate}
                            onChange={(e) => {
                                const val = e.target.value.replace(/[^0-9]/g, '');
                                let result = '';
                                if (val.length <= 4) result = val;
                                else if (val.length <= 6) result = `${val.slice(0, 4)}-${val.slice(4)}`;
                                else result = `${val.slice(0, 4)}-${val.slice(4, 6)}-${val.slice(6, 8)}`;
                                setBirthDate(result);
                            }}
                            placeholder="0000-00-00"
                            maxLength={10}
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

                    {/* 이메일 */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            이메일 <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="example@email.com"
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
                <PremiumButton onClick={handleSave} style={{ padding: '12px 32px' }}>
                    저장
                </PremiumButton>
            </div>

        </div>
    );
};

export default ProfileManagementPage;
