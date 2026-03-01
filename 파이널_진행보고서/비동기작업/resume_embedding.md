# Resume Embedding Task 모듈 (resume_embedding.py)

구조화된 이력서 데이터를 벡터로 변환하여 RAG(Retrieval-Augmented Generation) 시스템에서 활용할 수 있게 준비합니다.

## 주요 기능

### 1. `tasks.resume_embedding.generate_resume_embeddings`

- **설명**: 파싱된 이력서 데이터를 의미 단위로 쪼개고(Chunking), 이를 고차원 벡터(Embedding)로 변환하여 저장합니다.
- **매개변수**:
  - `resume_id`: 이력서 ID
- **흐름**:
  1. DB에서 구조화된 이력서 데이터 로드
  2. **청킹(Chunking)**: `chunk_resume` 함수를 통해 의미 단위 분할
  3. **임베딩 생성**: GPU를 사용하여 각 청크를 1024차원 벡터로 변환
  4. **벡터 DB 저장**: `pgvector`를 활용하여 `resume_embeddings` 테이블에 벡터 저장
- **결과**: 성공 시 이력서 처리 상태를 `completed`로 업데이트하며, 이후 면접 질문 생성 시 실시간 검색(RAG)에 활용됩니다.
- **큐(Queue)**: `gpu_queue` (GPU 가속 필요)
