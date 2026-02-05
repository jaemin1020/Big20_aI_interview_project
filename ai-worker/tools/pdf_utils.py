
from PyPDF2 import PdfReader
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF 파일에서 텍스트를 추출하여 반환합니다."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"

        if not text.strip():
            logger.warning(f"PDF에서 텍스트를 추출하지 못했습니다: {pdf_path}")
            return ""

        return text.strip()
    except Exception as e:
        logger.error(f"PDF 읽기 오류: {e}")
        return ""
