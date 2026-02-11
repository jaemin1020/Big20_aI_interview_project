import React, { useState } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import { uploadResume, getResume } from '../../api/interview';

const ResumePage = ({ onNext, onFileSelect, onParsedData }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [step, setStep] = useState('upload'); // upload, confirm
  const [uploadResult, setUploadResult] = useState(null);

  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);

  const handleFile = (selectedFile) => {
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      if (onFileSelect) {
        onFileSelect(selectedFile);
      }
    } else if (selectedFile) {
      alert("PDF 형식의 파일만 업로드 가능합니다.");
    }
  };

  React.useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      handleFile(e.target.files[0]);
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
             setIsUploading(false);
             alert("이력서 분석에 실패했습니다.");
          } else if (pollCount < maxPolls) {
            pollCount++;
            setTimeout(poll, 2000); // 2초 뒤 다시 확인
          } else {
             setIsUploading(false);
             alert("분석 시간이 초과되었습니다. (AI 모델 로딩 지연 가능성)");
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
                {uploadResult?.position || '지원 직무를 파악하고 있습니다...'}
              </dd>

              {uploadResult?.skills && uploadResult.skills.length > 0 && (
                <>
                  <dt style={{ color: 'var(--text-muted)' }}>추출 기술</dt>
                  <dd>{uploadResult.skills.join(', ')}</dd>
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
    <div className="resume-upload animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%', padding: '2rem 1rem' }}>
      <GlassCard style={{ maxWidth: file ? '900px' : '600px', width: '100%', textAlign: 'center', transition: 'max-width 0.5s cubic-bezier(0.4, 0, 0.2, 1)' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-wrapper" style={{ width: '240px' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
          </div>
        </div>
        <h2 className="text-gradient" style={{ fontSize: '1.8rem', marginBottom: '1rem' }}>이력서를 업로드 해주세요.</h2>
        <p style={{ marginBottom: '2rem', color: 'var(--text-muted)' }}>면접 질문 생성을 위해 PDF 형식의 이력서를 업로드해주세요.</p>

        {file ? (
          <div style={{ display: 'flex', gap: '2rem', textAlign: 'left', animation: 'fadeIn 0.5s ease-out' }}>
            {/* 왼쪽: 문서 미리보기 */}
            <div style={{
              flex: 1,
              height: '520px',
              background: 'rgba(255, 255, 255, 0.02)',
              borderRadius: '16px',
              overflow: 'hidden',
              border: '1px solid var(--glass-border)',
              position: 'relative',
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
            }}>
              <object
                data={previewUrl}
                type="application/pdf"
                style={{ width: '100%', height: '100%' }}
              >
                <div style={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '2rem',
                  textAlign: 'center'
                }}>
                  <span style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</span>
                  <p>이 브라우저는 PDF 미리보기를 지원하지 않습니다.</p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', width: '100%' }}>{file.name}</p>
                </div>
              </object>
            </div>

            {/* 오른쪽: 정보 및 작업 */}
            <div style={{ width: '300px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{
                padding: '1.2rem',
                background: 'rgba(255, 255, 255, 0.03)',
                borderRadius: '16px',
                border: '1px solid var(--glass-border)',
              }}>
                <h4 style={{ margin: '0 0 1rem 0', fontSize: '0.9rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>선택된 파일</h4>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1.2rem' }}>
                  <div style={{ fontSize: '2rem' }}>📄</div>
                  <div style={{ overflow: 'hidden' }}>
                    <div style={{ fontWeight: '600', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{file.name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                  </div>
                </div>
                <PremiumButton
                  variant="secondary"
                  onClick={() => { setFile(null); setPreviewUrl(null); }}
                  style={{ width: '100%', padding: '10px' }}
                >
                  다른 파일로 변경
                </PremiumButton>
              </div>

              <div style={{ flex: 1 }}></div>

              <PremiumButton
                disabled={isUploading}
                onClick={handleUpload}
                style={{ width: '100%', padding: '16px' }}
              >
                {isUploading ? (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <div className="spinner" style={{ width: '20px', height: '20px', margin: 0 }}></div>
                    <span>분석 중...</span>
                  </div>
                ) : '이력서 분석 시작'}
              </PremiumButton>
            </div>
          </div>
        ) : (
          <>
            <div
              style={{
                border: `2px dashed ${isDragging ? 'var(--primary)' : 'var(--glass-border)'}`,
                borderRadius: '20px',
                padding: '4rem 2rem',
                marginBottom: '2rem',
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                background: isDragging ? 'rgba(99, 102, 241, 0.05)' : 'transparent',
                transform: isDragging ? 'scale(1.02)' : 'scale(1)'
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onMouseOver={(e) => { if (!isDragging) e.currentTarget.style.borderColor = 'var(--primary)'; }}
              onMouseOut={(e) => { if (!isDragging) e.currentTarget.style.borderColor = 'var(--glass-border)'; }}
              onClick={() => document.getElementById('resume-input').click()}
            >
              <div style={{ fontSize: '4rem', marginBottom: '1.5rem', transform: isDragging ? 'translateY(-10px)' : 'translateY(0)', transition: 'transform 0.3s' }}>📁</div>
              <p style={{ margin: 0, fontWeight: '500', fontSize: '1.2rem' }}>클릭하거나 파일을 이곳에 드래그하세요</p>
              <p style={{ margin: '8px 0 0 0', fontSize: '0.9rem', color: 'var(--text-muted)' }}>PDF 형식만 지원합니다.</p>
            </div>

            <PremiumButton
              disabled={true}
              style={{ width: '100%', padding: '16px', opacity: 0.5 }}
            >
              파일을 업로드 해주세요
            </PremiumButton>
          </>
        )}
        <input
          id="resume-input"
          type="file"
          accept=".pdf"
          hidden
          onChange={handleFileChange}
        />
      </GlassCard>
    </div>
  );
};

export default ResumePage;
