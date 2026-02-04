import React, { useState } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const ResumePage = ({ onNext }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [step, setStep] = useState('upload'); // upload, confirm

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (!file) return;
    setIsUploading(true);
    // 실제 서비스에서는 여기서 API 호출
    setTimeout(() => {
      setIsUploading(false);
      setStep('confirm');
    }, 1500);
  };

  if (step === 'confirm') {
    return (
      <div className="resume-confirm animate-fade-in">
        <GlassCard style={{ maxWidth: '700px', margin: '0 auto' }}>
          <h1 className="text-gradient" style={{ textAlign: 'center', marginBottom: '2rem' }}>지원 정보 확인</h1>
          <p style={{ textAlign: 'center', marginBottom: '2rem', color: 'var(--text-muted)' }}>
            업로드하신 이력서에서 추출된 정보입니다. 내용이 맞다면 면접 진행을 눌러주세요.
          </p>

          <div style={{ 
            background: 'rgba(255, 255, 255, 0.03)', 
            padding: '2rem', 
            borderRadius: '16px',
            marginBottom: '2rem',
            border: '1px solid var(--glass-border)'
          }}>
            <dl style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '1.2rem', margin: 0 }}>
              <dt style={{ color: 'var(--text-muted)' }}>지원 회사</dt>
              <dd style={{ fontWeight: '600' }}>삼성전자</dd>
              <dt style={{ color: 'var(--text-muted)' }}>지원 직무</dt>
              <dd style={{ fontWeight: '600' }}>S/W 개발</dd>
              <dt style={{ color: 'var(--text-muted)' }}>경력 요약</dt>
              <dd>AWS 인턴십 6개월</dd>
              <dt style={{ color: 'var(--text-muted)' }}>전공</dt>
              <dd>컴퓨터공학 학사</dd>
              <dt style={{ color: 'var(--text-muted)' }}>관련 기술</dt>
              <dd>정보처리기사, 네트워크관리사 2급</dd>
            </dl>
          </div>

          <div style={{ display: 'flex', gap: '1rem' }}>
            <PremiumButton onClick={onNext} style={{ flex: 1 }}>면접 진행</PremiumButton>
            <PremiumButton variant="secondary" onClick={() => setStep('upload')}>다시 업로드</PremiumButton>
          </div>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="resume-upload animate-fade-in">
      <GlassCard style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h1 className="text-gradient">이력서 업로드</h1>
        <p style={{ marginBottom: '2rem' }}>면접 질문 생성을 위해 PDF 형식의 이력서를 업로드해주세요.</p>

        <div 
          style={{ 
            border: '2px dashed var(--glass-border)', 
            borderRadius: '20px', 
            padding: '3rem 2rem',
            marginBottom: '2rem',
            cursor: 'pointer',
            transition: 'border-color 0.3s'
          }}
          onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--primary)'}
          onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--glass-border)'}
          onClick={() => document.getElementById('resume-input').click()}
        >
          {file ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '3rem' }}>📄</span>
              <span style={{ fontWeight: '600' }}>{file.name}</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
          ) : (
            <>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
              <p style={{ margin: 0, fontWeight: '500' }}>클릭하거나 파일을 이곳에 드래그하세요</p>
              <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>PDF 형식만 지원합니다.</p>
            </>
          )}
          <input 
            id="resume-input" 
            type="file" 
            accept=".pdf" 
            hidden 
            onChange={handleFileChange} 
          />
        </div>

        <PremiumButton 
          disabled={!file || isUploading} 
          onClick={handleUpload}
          style={{ width: '100%', padding: '16px' }}
        >
          {isUploading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              <div className="spinner" style={{ width: '20px', height: '20px', margin: 0 }}></div>
              <span>분석 중...</span>
            </div>
          ) : '파일 업로드'}
        </PremiumButton>
      </GlassCard>
    </div>
  );
};

export default ResumePage;
