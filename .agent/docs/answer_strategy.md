멀티모달 기반 면접 평가 최적화 프로세스단순히 "잘했다"가 아니라, "무엇을(Text), 어떻게(Audio), 어떤 태도로(Video)" 말했는지를 데이터로 증명하는 방식입니다.

1. 데이터 소스별 분석 전략
   분석 대상,핵심 기술 (Tool),분석 지표 (Features)
   텍스트 (DB),Solar 10.7B + RAG,"답변의 논리성, 직무 키워드 포함 여부, 루브릭 부합도"
   음성 (Audio),Deepgram + Wav2Vec,"말하기 속도(WPM), 휴지(Pause) 빈도, 자신감(Pitch 변동)"
   영상 (Video),MediaPipe / Vision LLM,"시선 처리, 표정 변화(긍정/부정), 자세의 안정성"
2. 최적의 평가 알고리즘: "Weighted Multimodal Scoring"
   가장 좋은 방법은 각 요소에 가중치를 부여한 후, Solar 10.7B가 최종 종합 의견을 작성하게 하는 것입니다.

1단계: 개별 정량 스코어링각 도메인별로 루브릭에 따른 점수를 매깁니다.
Text Score ($S_t$): 루브릭 항목별 매칭 점수 (Semantic Similarity)
Audio Score ($S_a$): 전달력 점수 (속도, 발음 정확도 등)
Video Score ($S_v$): 비언어적 태도 점수 (감정 표현, 시선)

2단계: 가중치 결합 (Weighted Sum)
최종 점수는 직무 성격에 따라 가중치를 조절한 수식으로 산출합니다.

$$
Total Score = (w_t \cdot S_t) + (w_a \cdot S_a) + (w_v \cdot S_v)
$$(예: 기술 면접은 $w_t$에 0.7 부여, 영업직 면접은 $w_v$와 $w_a$에 높은 비중 부여)
3. 루브릭 기반 AI 평가 리포트 생성 (Prompt 예시)Solar 10.7B 워커(AW)가 수행할 최종 평가 프롬프트 구조입니다.
Markdown
### Evaluation Task
당신은 인사 전문가입니다. 제공된 멀티모달 데이터를 바탕으로 루브릭에 따라 후보자를 평가하세요.

### Input Data
1. 루브릭 기준: {rubric_data}
2. 답변 텍스트(STT): {answer_text}
3. 음성 분석 로그: {audio_analysis} (예: "속도가 너무 빠름", "말끝을 흐림")
4. 영상 분석 로그: {video_analysis} (예: "시선이 불안정함", "미소 짓는 표정 많음")

### Output Format
- [정량 평가]: 각 루브릭 항목별 점수 (1-5점)
- [정성 피드백]: 답변의 논리적 결점 및 태도 개선점
4. 아키텍처상의 데이터 흐름
AI Worker (Celery):Deepgram에서 온 텍스트로 텍스트 분석 수행.
오디오 파일의 주파수와 볼륨 데이터로 전달력 분석 수행.영상 프레임 샘플링(1fps)으로 표정/태도 분석 수행.
PostgreSQL (Storage):산출된 모든 지표($S_t, S_a, S_v$)와 가중치 결과를 evaluation 테이블에 저장.
pgvector를 사용해 이전에 평가했던 우수 답변 사례와 비교 분석.
$$
