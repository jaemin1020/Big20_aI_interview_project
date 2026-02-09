import difflib
import time
from typing import Dict, Any

class STTEvaluator:
    """
    STT 결과의 정확도를 측정하는 클래스입니다.
    추가 라이브러리(jiwer 등) 설치 없이 기본 라이브러리로 작동하도록 설계되었습니다.
    """

    def evaluate(self, reference: str, hypothesis: str) -> Dict[str, Any]:
        """
        정답(reference)과 추론(hypothesis) 문장을 비교하여 CER, WER 유사도를 계산합니다.
        """
        if not reference:
            return {"cer": 0.0, "wer": 0.0, "similarity": 0.0}

        # 1. 문자 단위 정확도 (CER 유사도 기반 계산)
        ref_chars = reference.replace(" ", "").lower()
        hyp_chars = hypothesis.replace(" ", "").lower()
        char_similarity = difflib.SequenceMatcher(None, ref_chars, hyp_chars).ratio()
        
        # 2. 단어 단위 정확도 (WER 유사도 기반 계산)
        ref_words = reference.split()
        hyp_words = hypothesis.split()
        word_similarity = difflib.SequenceMatcher(None, ref_words, hyp_words).ratio()

        return {
            "cer": (1.0 - char_similarity) * 100,  # 오차율 (%)
            "wer": (1.0 - word_similarity) * 100,   # 오차율 (%)
            "similarity": char_similarity * 100     # 유사도 점수 (%)
        }
