import { useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const AuthPage = ({
  authMode,
  setAuthMode,
  account,
  setAccount,
  handleAuth,
  authError,
  onBack
}) => {
  const fileInputRef = useRef(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setAccount({ ...account, profileImage: reader.result });
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="auth-container animate-fade-in" style={{
      flex: 1,
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '4rem 0'
    }}>
      <GlassCard className="auth-card" style={{ width: '100%', maxWidth: '450px', position: 'relative' }}>
        {/* Back Button */}
        <button
          onClick={onBack}
          style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            borderRadius: '6px',
            transition: 'all 0.2s'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.color = 'var(--text-main)';
            e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.color = 'var(--text-muted)';
            e.currentTarget.style.background = 'none';
          }}
        >
          ← 메인화면으로
        </button>

        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-wrapper" style={{ width: '100px' }}>
            <img src="/logo.png" alt="Logo" className="theme-logo" />
          </div>
        </div>

        <h1 className="text-gradient" style={{ textAlign: 'center', marginBottom: '0.5rem', fontSize: '2rem' }}>
          {authMode === 'login' ? '환영합니다' : '회원가입'}
        </h1>
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.95rem' }}>
          {authMode === 'login'
            ? 'BIGVIEW AI 면접 시스템에 로그인하세요'
            : '새로운 계정을 생성하여 면접을 시작하세요'}
        </p>

        <div className="input-group" style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>

          {authMode === 'register' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '0.5rem' }}>
              <div
                onClick={() => fileInputRef.current?.click()}
                style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  background: 'var(--bg-darker)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  overflow: 'hidden',
                  border: '2px dashed var(--glass-border)',
                  position: 'relative'
                }}
              >
                {account.profileImage ? (
                  <img src={account.profileImage} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <div style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    📷<br />사진 업로드
                  </div>
                )}
              </div>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageChange}
                accept="image/*"
                style={{ display: 'none' }}
              />
            </div>
          )}

          {authMode === 'register' && (
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-muted)' }}>이메일</label>
              <input
                type="email"
                placeholder="example@email.com"
                value={account.email}
                onChange={(e) => setAccount({ ...account, email: e.target.value })}
              />
            </div>
          )}

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-muted)' }}>아이디</label>
            <input
              type="text"
              placeholder="user_id"
              value={account.username || ''}
              onChange={(e) => setAccount({ ...account, username: e.target.value })}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-muted)' }}>비밀번호</label>
            <input
              type="password"
              placeholder="••••••••"
              value={account.password}
              onChange={(e) => setAccount({ ...account, password: e.target.value })}
            />
          </div>

          {authMode === 'register' && (
            <>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-muted)' }}>비밀번호 확인</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={account.passwordConfirm}
                  onChange={(e) => setAccount({ ...account, passwordConfirm: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-muted)' }}>이름</label>
                <input
                  type="text"
                  placeholder="홍길동"
                  value={account.fullName || ''}
                  onChange={(e) => setAccount({ ...account, fullName: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-muted)' }}>생년월일</label>
                <input
                  type="text"
                  placeholder="0000-00-00"
                  value={account.birthDate || ''}
                  onChange={(e) => {
                    const val = e.target.value.replace(/[^0-9]/g, '');
                    let result = '';
                    if (val.length <= 4) result = val;
                    else if (val.length <= 6) result = `${val.slice(0, 4)}-${val.slice(4)}`;
                    else result = `${val.slice(0, 4)}-${val.slice(4, 6)}-${val.slice(6, 8)}`;
                    setAccount({ ...account, birthDate: result });
                  }}
                  maxLength={10}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="terms"
                  checked={account.termsAgreed}
                  onChange={(e) => setAccount({ ...account, termsAgreed: e.target.checked })}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <label htmlFor="terms" style={{ fontSize: '0.85rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
                  <span style={{ color: 'var(--primary)' }}>이용약관</span> 및 <span style={{ color: 'var(--primary)' }}>개인정보 처리방침</span>에 동의합니다.
                </label>
              </div>
            </>
          )}

          {authError && (
            <p style={{ color: '#ef4444', fontSize: '0.85rem', margin: '4px 0 0 0', textAlign: 'center', fontWeight: '500' }}>
              ⚠️ {authError}
            </p>
          )}

          <PremiumButton
            onClick={handleAuth}
            style={{ marginTop: '1rem', width: '100%', height: '50px' }}
          >
            {authMode === 'login' ? '로그인' : '회원가입 완료'}
          </PremiumButton>

          {authMode === 'login' && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', marginTop: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', cursor: 'pointer' }}>아이디 찾기</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--glass-border)', cursor: 'default' }}>|</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', cursor: 'pointer' }}>비밀번호 찾기</span>
            </div>
          )}

          <p style={{ textAlign: 'center', fontSize: '0.9rem', marginTop: '1rem', color: 'var(--text-muted)' }}>
            {authMode === 'login' ? '계정이 없으신가요?' : '이미 계정이 있으신가요?'}
            <span
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'register' : 'login');
                setAccount({ ...account, password: '', passwordConfirm: '', termsAgreed: false });
              }}
              style={{ color: 'var(--primary)', cursor: 'pointer', marginLeft: '8px', fontWeight: '700' }}
            >
              {authMode === 'login' ? '회원가입' : '로그인'}
            </span>
          </p>
        </div>
      </GlassCard>
    </div>
  );
};

export default AuthPage;
