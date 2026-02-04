# 🚀 BGE-M3 모델 다운로드 및 사용 가이드

## 📌 BGE-M3란?

**BGE-M3** (BAAI General Embedding - Multi-lingual, Multi-functionality, Multi-granularity)는 베이징 인공지능 연구소(BAAI)에서 개발한 최신 임베딩 모델입니다.

### 주요 특징
- 🌍 **100개 이상의 언어 지원** (한국어, 영어, 중국어, 일본어 등)
- 📊 **1024차원 임베딩** (기존 ko-sroberta는 768차원)
- 🎯 **다양한 작업 지원**: 검색, 분류, 클러스터링, 재순위화
- 📏 **최대 8192 토큰** 처리 가능 (긴 문서 지원)
- ⚡ **우수한 성능**: MTEB 벤치마크에서 상위권

---

## 🔧 설치 방법

### 1단계: Docker 컨테이너 접속
```bash
docker exec -it interview_backend bash
```

### 2단계: 필요한 패키지 설치
```bash
# sentence-transformers만 있으면 됨 (이미 설치되어 있음)
pip install sentence-transformers

# 또는 최신 버전으로 업그레이드
pip install --upgrade sentence-transformers
```

---

## 📥 모델 다운로드

### 자동 다운로드 (권장)
모델을 처음 사용할 때 자동으로 다운로드됩니다:

```python
from sentence_transformers import SentenceTransformer

# 처음 실행 시 자동 다운로드 (약 2.27GB)
model = SentenceTransformer('BAAI/bge-m3')
```

### 수동 다운로드
미리 다운로드하려면:

```bash
# Python 스크립트로 다운로드
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
```

### 다운로드 위치
모델은 다음 위치에 저장됩니다:
- Linux/Mac: `~/.cache/huggingface/hub/`
- Windows: `C:\Users\<username>\.cache\huggingface\hub\`

---

## 💻 기본 사용법

### 1. 간단한 임베딩 생성

```python
from sentence_transformers import SentenceTransformer

# 모델 로드
model = SentenceTransformer('BAAI/bge-m3')

# 텍스트 임베딩
texts = [
    "Python에서 GIL이 무엇인가요?",
    "FastAPI의 장점은 무엇인가요?"
]

embeddings = model.encode(texts)
print(f"임베딩 shape: {embeddings.shape}")  # (2, 1024)
```

### 2. 유사도 검색

```python
import numpy as np

# 검색 쿼리
query = "파이썬 멀티스레딩"
query_emb = model.encode([query])[0]

# 문서 임베딩
documents = [
    "Python의 GIL은 멀티스레딩을 제한합니다.",
    "FastAPI는 비동기 프로그래밍을 지원합니다.",
    "Docker는 컨테이너 기술입니다."
]
doc_embs = model.encode(documents)

# 코사인 유사도 계산
similarities = np.dot(doc_embs, query_emb)
best_match = np.argmax(similarities)

print(f"가장 유사한 문서: {documents[best_match]}")
print(f"유사도: {similarities[best_match]:.4f}")
```

### 3. 배치 처리

```python
# 대량의 텍스트 처리
large_corpus = [f"문서 {i}" for i in range(1000)]

# 배치 크기 조정으로 메모리 효율성 향상
embeddings = model.encode(
    large_corpus,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True  # 코사인 유사도 최적화
)
```

---

## 🔄 기존 프로젝트에 적용하기

### vector_utils.py 수정

현재 프로젝트의 `vector_utils.py`를 BGE-M3로 변경:

```python
# 기존 코드 (17-24줄)
def get_embedding_model():
    """임베딩 모델 싱글톤"""
    global _model
    if _model is None:
        print("🔄 임베딩 모델 로딩 중...")
        _model = SentenceTransformer('jhgan/ko-sroberta-multitask')  # 768차원
        print("✅ 모델 로드 완료!")
    return _model

# BGE-M3로 변경
def get_embedding_model():
    """임베딩 모델 싱글톤"""
    global _model
    if _model is None:
        print("🔄 BGE-M3 모델 로딩 중...")
        _model = SentenceTransformer('BAAI/bge-m3')  # 1024차원
        print("✅ 모델 로드 완료!")
        print(f"📊 임베딩 차원: {_model.get_sentence_embedding_dimension()}")
    return _model
```

### 데이터베이스 스키마 변경 필요

BGE-M3는 1024차원이므로 데이터베이스 스키마도 변경해야 합니다:

```python
# models.py 수정
class Question(SQLModel, table=True):
    # ...
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(1024))  # 768 → 1024로 변경
    )

class AnswerBank(SQLModel, table=True):
    # ...
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(1024))  # 768 → 1024로 변경
    )
```

### 마이그레이션 스크립트

```sql
-- PostgreSQL에서 실행
ALTER TABLE questions
ALTER COLUMN embedding TYPE vector(1024);

ALTER TABLE answer_bank
ALTER COLUMN embedding TYPE vector(1024);

-- 기존 데이터 삭제 (임베딩 재생성 필요)
UPDATE questions SET embedding = NULL;
UPDATE answer_bank SET embedding = NULL;
```

---

## 📊 성능 비교

| 모델 | 차원 | 언어 지원 | 최대 토큰 | 크기 |
|------|------|-----------|-----------|------|
| **ko-sroberta-multitask** | 768 | 한국어 | 512 | ~450MB |
| **BGE-M3** | 1024 | 100+ | 8192 | ~2.27GB |

### 벤치마크 결과 (MTEB)
- BGE-M3: **66.1** (평균 점수)
- ko-sroberta: 한국어 특화 (다국어 미지원)

---

## 🎯 실전 예시

### 예시 1: 면접 질문 검색 시스템

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 모델 로드
model = SentenceTransformer('BAAI/bge-m3')

# 면접 질문 데이터베이스
questions = [
    "Python의 GIL에 대해 설명해주세요.",
    "RESTful API 설계 원칙은 무엇인가요?",
    "Docker와 VM의 차이점은?",
    "비동기 프로그래밍의 장점은?"
]

# 임베딩 생성
question_embs = model.encode(questions, normalize_embeddings=True)

# 사용자 검색
user_query = "파이썬 멀티스레딩 제약사항"
query_emb = model.encode([user_query], normalize_embeddings=True)[0]

# 유사도 계산 (정규화된 벡터이므로 내적 = 코사인 유사도)
similarities = np.dot(question_embs, query_emb)

# 결과 출력
for i, (q, sim) in enumerate(zip(questions, similarities)):
    print(f"{i+1}. [{sim:.3f}] {q}")
```

### 예시 2: 답변 평가 시스템

```python
# 우수 답변 (참고 답변)
reference_answer = """
GIL(Global Interpreter Lock)은 Python 인터프리터가
한 번에 하나의 스레드만 Python 바이트코드를 실행할 수
있도록 제한하는 뮤텍스입니다. 이는 멀티코어 CPU에서도
CPU-bound 작업의 병렬 처리를 제한합니다.
"""

# 사용자 답변
user_answer = "GIL은 Python의 멀티스레딩을 제한하는 락입니다."

# 임베딩 및 유사도 계산
ref_emb = model.encode([reference_answer], normalize_embeddings=True)[0]
user_emb = model.encode([user_answer], normalize_embeddings=True)[0]

similarity = np.dot(ref_emb, user_emb)

# 점수 계산 (유사도 기반)
score = similarity * 100

print(f"유사도: {similarity:.4f}")
print(f"점수: {score:.1f}/100")

if similarity > 0.85:
    print("✅ 우수한 답변입니다!")
elif similarity > 0.70:
    print("👍 좋은 답변입니다.")
else:
    print("⚠️ 답변을 보완해주세요.")
```

---

## 🚀 실행 방법

### 테스트 스크립트 실행

```bash
# Docker 컨테이너 내부에서
cd /app/scripts
python bge_m3_simple.py
```

### 예상 출력

```
🚀 BGE-M3 모델 사용 가이드
============================================================
🔄 BGE-M3 모델 로딩 중...
✅ 모델 로드 완료! (3.45초)
📦 모델: BAAI/bge-m3
📊 임베딩 차원: 1024
🌍 지원 언어: 100+ (한국어, 영어, 중국어, 일본어 등)

============================================================
📝 기본 사용법
============================================================
✅ 3개 텍스트 임베딩 완료
   임베딩 shape: (3, 1024)

============================================================
🔍 벡터 검색 예시
============================================================
🔎 검색 쿼리: '파이썬 멀티스레딩 제약사항'

1. 유사도: 0.8234
   내용: Python의 GIL(Global Interpreter Lock)은...
```

---

## ⚠️ 주의사항

### 1. 메모리 사용량
- BGE-M3는 약 **2.3GB RAM** 필요
- 배치 크기를 줄여 메모리 절약: `batch_size=8`

### 2. 데이터베이스 마이그레이션
- 기존 768차원 → 1024차원 변경 필요
- **기존 임베딩 데이터는 모두 재생성해야 함**

### 3. 처리 속도
- 첫 실행 시 모델 다운로드로 시간 소요 (약 2-5분)
- GPU 사용 시 속도 향상 (CPU 대비 5-10배)

---

## 🔧 문제 해결

### 1. 다운로드 실패
```bash
# 네트워크 문제 시 재시도
pip install --upgrade sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
```

### 2. 메모리 부족
```python
# 배치 크기 줄이기
embeddings = model.encode(texts, batch_size=8)  # 기본값 32 → 8
```

### 3. 차원 불일치 오류
```sql
-- 데이터베이스 스키마 확인
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'questions' AND column_name = 'embedding';

-- Vector 차원 변경
ALTER TABLE questions ALTER COLUMN embedding TYPE vector(1024);
```

---

## 📚 추가 자료

- **공식 문서**: https://huggingface.co/BAAI/bge-m3
- **논문**: [BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation](https://arxiv.org/abs/2402.03216)
- **GitHub**: https://github.com/FlagOpen/FlagEmbedding

---

## ✅ 체크리스트

- [ ] sentence-transformers 설치 확인
- [ ] BGE-M3 모델 다운로드 (2.27GB)
- [ ] 테스트 스크립트 실행 (`bge_m3_simple.py`)
- [ ] 데이터베이스 스키마 변경 (768 → 1024)
- [ ] 기존 데이터 임베딩 재생성
- [ ] API 엔드포인트 테스트

---

## 🎯 다음 단계

1. **프로덕션 적용**: `vector_utils.py` 수정
2. **성능 최적화**: 배치 크기 조정, GPU 사용
3. **모니터링**: 검색 품질 및 응답 시간 측정
4. **A/B 테스트**: BGE-M3 vs ko-sroberta 성능 비교
