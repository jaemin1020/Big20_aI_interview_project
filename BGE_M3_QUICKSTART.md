# BGE-M3 모델 빠른 시작 가이드 (Quick Start)

## ✅ 완료된 작업

BGE-M3 모델이 성공적으로 다운로드되고 테스트되었습니다!

## 🚀 3단계로 시작하기

### 1단계: 모델 사용 (Python 코드)

```python
from sentence_transformers import SentenceTransformer

# 모델 로드 (처음 실행 시 자동 다운로드)
model = SentenceTransformer('BAAI/bge-m3')

# 텍스트 임베딩
texts = ["Python에서 GIL이 무엇인가요?", "FastAPI의 장점은?"]
embeddings = model.encode(texts)

print(f"임베딩 차원: {embeddings.shape}")  # (2, 1024)
```

### 2단계: 벡터 검색

```python
import numpy as np

# 검색 쿼리
query = "파이썬 멀티스레딩"
query_emb = model.encode([query], normalize_embeddings=True)[0]

# 문서 검색
documents = [
    "Python의 GIL은 멀티스레딩을 제한합니다.",
    "FastAPI는 비동기 프로그래밍을 지원합니다."
]
doc_embs = model.encode(documents, normalize_embeddings=True)

# 유사도 계산
similarities = np.dot(doc_embs, query_emb)
print(f"유사도: {similarities}")
```

### 3단계: 테스트 스크립트 실행

```bash
# Docker 컨테이너 내부에서
cd /app/scripts
python bge_m3_simple.py
```

## 📊 모델 정보

| 항목 | 값 |
|------|-----|
| **모델명** | BAAI/bge-m3 |
| **임베딩 차원** | 1024 |
| **지원 언어** | 100+ (한국어, 영어, 중국어, 일본어 등) |
| **최대 토큰** | 8192 |
| **모델 크기** | 2.27GB |

## 🎯 테스트 결과

✅ **기본 사용법**: 성공
✅ **벡터 검색**: 성공
✅ **다국어 지원**: 성공
✅ **면접 질문 검색**: 성공

### 검색 예시 결과

**쿼리**: "파이썬 멀티스레딩 성능 문제"

1. [0.659] Python의 GIL(Global Interpreter Lock)에 대해 설명하고...
2. [0.505] 데이터베이스 인덱스의 동작 원리와 장단점을...

## 📁 생성된 파일

1. **`bge_m3_simple.py`** - BGE-M3 사용 예시 코드
2. **`BGE_M3_GUIDE.md`** - 완전한 가이드 문서
3. **`BGE_M3_QUICKSTART.md`** - 이 파일 (빠른 시작)

## 🔄 기존 프로젝트에 적용하기

### vector_utils.py 수정

```python
# 22번째 줄 수정
# 기존: _model = SentenceTransformer('jhgan/ko-sroberta-multitask')
# 변경: _model = SentenceTransformer('BAAI/bge-m3')
```

### ⚠️ 주의: 데이터베이스 스키마 변경 필요

BGE-M3는 **1024차원**이므로 데이터베이스도 변경해야 합니다:

```sql
-- PostgreSQL에서 실행
ALTER TABLE questions ALTER COLUMN embedding TYPE vector(1024);
ALTER TABLE answer_bank ALTER COLUMN embedding TYPE vector(1024);

-- 기존 임베딩 삭제 (재생성 필요)
UPDATE questions SET embedding = NULL;
UPDATE answer_bank SET embedding = NULL;
```

```python
# models.py 수정
embedding: Optional[List[float]] = Field(
    default=None,
    sa_column=Column(Vector(1024))  # 768 → 1024
)
```

## 💡 다음 단계

1. ✅ **모델 다운로드 완료**
2. ⬜ 데이터베이스 스키마 변경 (768 → 1024)
3. ⬜ `vector_utils.py` 수정
4. ⬜ 기존 데이터 임베딩 재생성
5. ⬜ 성능 테스트 및 비교

## 📚 더 알아보기

- **상세 가이드**: `BGE_M3_GUIDE.md` 참고
- **예시 코드**: `bge_m3_simple.py` 참고
- **공식 문서**: https://huggingface.co/BAAI/bge-m3

---

**🎉 축하합니다! BGE-M3 모델을 성공적으로 다운로드하고 실행했습니다!**
