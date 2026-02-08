"""
PDF 이력서 파싱 유틸리티
"""
import logging
from typing import Dict, Optional
import re

logger = logging.getLogger("PDFParser")

try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    logger.warning("PDF parsing libraries not installed. Install: pip install PyPDF2 pdfplumber")
    PDF_AVAILABLE = False


class ResumePDFParser:
    """이력서 PDF 파싱 클래스"""
    
    @staticmethod
    def extract_text_pypdf2(pdf_path: str) -> str:
        """
        PyPDF2를 사용한 텍스트 추출 (기본)
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            str: 추출된 텍스트
        """
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not installed")
        
        try:
            text_parts = []
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                logger.info(f"PDF 총 페이지 수: {total_pages}")
                
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                        logger.debug(f"페이지 {page_num}/{total_pages} 추출 완료")
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"총 {len(full_text)} 글자 추출됨")
            return full_text
            
        except Exception as e:
            logger.error(f"PyPDF2 텍스트 추출 실패: {e}")
            raise
    
    @staticmethod
    def extract_text_pdfplumber(pdf_path: str) -> str:
        """
        pdfplumber를 사용한 텍스트 추출 (더 정확함)
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            str: 추출된 텍스트
        """
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber not installed")
        
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF 총 페이지 수: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                        logger.debug(f"페이지 {page_num}/{total_pages} 추출 완료")
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"총 {len(full_text)} 글자 추출됨")
            return full_text
            
        except Exception as e:
            logger.error(f"pdfplumber 텍스트 추출 실패: {e}")
            raise
    
    @staticmethod
    def extract_text(pdf_path: str, method: str = "pdfplumber") -> str:
        """
        PDF에서 텍스트 추출 (자동 fallback)
        
        Args:
            pdf_path: PDF 파일 경로
            method: 추출 방법 ("pdfplumber" 또는 "pypdf2")
            
        Returns:
            str: 추출된 텍스트
        """
        try:
            if method == "pdfplumber":
                return ResumePDFParser.extract_text_pdfplumber(pdf_path)
            else:
                return ResumePDFParser.extract_text_pypdf2(pdf_path)
        except Exception as e:
            logger.warning(f"{method} 실패, 다른 방법 시도: {e}")
            # Fallback
            if method == "pdfplumber":
                return ResumePDFParser.extract_text_pypdf2(pdf_path)
            else:
                return ResumePDFParser.extract_text_pdfplumber(pdf_path)
    
    @staticmethod
    def extract_metadata(pdf_path: str) -> Dict:
        """
        PDF 메타데이터 추출
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            dict: 메타데이터
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata
                
                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "creation_date": metadata.get("/CreationDate", ""),
                    "modification_date": metadata.get("/ModDate", ""),
                    "page_count": len(reader.pages)
                }
        except Exception as e:
            logger.error(f"메타데이터 추출 실패: {e}")
            return {}
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        추출된 텍스트 정제
        
        Args:
            text: 원본 텍스트
            
        Returns:
            str: 정제된 텍스트
        """
        # 여러 개의 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 여러 개의 줄바꿈을 최대 2개로
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 특수문자 정리 (선택적)
        # text = re.sub(r'[^\w\s가-힣.,!?@\-():/]', '', text)
        
        return text.strip()


# 사용 예시
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python pdf_parser.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # 텍스트 추출
    print("="*50)
    print("PDF 텍스트 추출 중...")
    print("="*50)
    
    text = ResumePDFParser.extract_text(pdf_path)
    cleaned_text = ResumePDFParser.clean_text(text)
    
    print(f"\n추출된 텍스트 ({len(cleaned_text)} 글자):")
    print("-"*50)
    print(cleaned_text[:500])  # 앞부분만 출력
    print("...")
    
    # 메타데이터 추출
    print("\n" + "="*50)
    print("PDF 메타데이터:")
    print("="*50)
    metadata = ResumePDFParser.extract_metadata(pdf_path)
    for key, value in metadata.items():
        print(f"{key}: {value}")
