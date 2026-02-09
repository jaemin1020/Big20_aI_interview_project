import React, { useState } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import { uploadResume, getResume } from '../../api/interview';

const ResumePage = ({ onNext, onFileSelect, onParsedData }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [step, setStep] = useState('upload'); // upload, confirm
  const [uploadResult, setUploadResult] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (onFileSelect) {
        onFileSelect(selectedFile);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    
    try {
      // 1. 초기 업로드 요청
      const uploadData = await uploadResume(file);
      const resumeId = uploadData.resume_id;
      console.log('Upload basic success, ID:', resumeId);
      
      // 2. 폴링 (분석 완료 대기)
      let pollCount = 0;
      const maxPolls = 90; // 최대 180초 (2초 * 90) - 첫 실행 시 모델 로딩으로 인해 오래 걸릴 수 있음
      
      const poll = async () => {
        try {
          const result = await getResume(resumeId);
          console.log('Polling result:', result.processing_status);
          
          if (result.processing_status === 'completed') {
            setUploadResult(result);
            if (onParsedData) {
              onParsedData(result);
            }
            setStep('confirm');
            setIsUploading(false);
          } else if (result.processing_status === 'failed') {
            throw new Error("분석에 실패했습니다.");
          } else if (pollCount < maxPolls) {
            pollCount++;
            setTimeout(poll, 2000); // 2초 뒤 다시 확인
          } else {
            throw new Error("분석 시간이 초과되었습니다. (AI 모델 로딩 지연 가능성)");
          }
        } catch (err) {
          console.error('Polling error:', err);
          setIsUploading(false);
          alert(err.message || "이력서 분석 중 오류가 발생했습니다.");
        }
      };
      
      setTimeout(poll, 1000); // 1초 뒤 첫 폴링 시작
      
    } catch (err) {
      console.error(err);
      setIsUploading(false);
      alert("이력서 업로드 중 오류가 발생했습니다.");
    }
  };

  if (step === 'confirm') {
    return (
      <div className="resume-confirm animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%' }}>
        <GlassCard style={{ maxWidth: '700px', width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="logo-wrapper" style={{ width: '200px' }}>
              <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
            </div>
          </div>
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
              <dt style={{ color: 'var(--text-muted)' }}>파일 분석</dt>
              <dd style={{ fontWeight: '600' }}>성공 ({(file.size / 1024).toFixed(1)} KB)</dd>
              
              <dt style={{ color: 'var(--text-muted)' }}>지원 직무</dt>
              <dd style={{ fontWeight: '600', color: 'var(--primary)' }}>
                {uploadResult?.structured_data?.target_position || uploadResult?.position || '지원 직무를 파악하고 있습니다...'}
              </dd>
              
              {uploadResult?.structured_data?.skills && uploadResult.structured_data.skills.length > 0 && (
                <>
                  <dt style={{ color: 'var(--text-muted)' }}>추출 기술</dt>
                  <dd>{uploadResult.structured_data.skills.join(', ')}</dd>
                </>
              )}
              
             {/* If additional parsed info exists, add here */}
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
    <div className="resume-upload animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%' }}>
      <GlassCard style={{ maxWidth: '600px', width: '100%', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-wrapper" style={{ width: '240px' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
          </div>
        </div>
        <h1 className="text-gradient">이력서를 업로드 해주세요.</h1>
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
