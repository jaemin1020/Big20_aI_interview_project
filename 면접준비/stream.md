# AI 면접 프로젝트: 실시간 스트리밍(Streaming) 구현 가이드

본 문서는 면접 질문 생성 시 물리적인 대기 시간을 획기적으로 줄이기 위해 도입한 **실시간 스트리밍(Streaming)** 기술의 아키텍처와 구현 내용을 정리한 자료입니다.

---

## 1. 개요 (Overview)

* **기존 방식 (Batch)**: 질문 전체(약 100~200자)를 AI가 다 만들 때까지 기다린 후 한꺼번에 응답. 약 10~15초 소요.
* **도입 방식 (Streaming)**: AI가 첫 글자를 생성하자마자 실시간으로 화면에 출력. **체감 대기 시간 0.5초 미만.**

---

## 2. 스트리밍 아키텍처

1. **AI-Worker (Producer)**:
   * `llama-cpp-python`의 `stream=True` 옵션을 활용하여 토큰 단위로 엔진에서 추출.
   * 각 토큰을 생성 즉시 **Redis Pub/Sub** 채널(`interview_{id}_stream`)로 발행(Publish).
2. **Backend-Core (Broker/Bridge)**:
   * Redis의 해당 채널을 구독(Subscribe)하고 대기.
   * 새로운 토큰이 들어올 때마다 **WebSocket** 또는 **SSE(Server-Sent Events)**를 통해 프론트엔드로 즉각 전송.
3. **Frontend (Consumer)**:
   * 전달받은 토큰들을 기존 문장에 합쳐서 화면에 실시간으로 타이핑 효과(Typing Effect)와 함께 출력.

---

## 3. 핵심 수정 파일 및 코드

### ① LLM 엔진 수정 (`ai-worker/utils/exaone_llm.py`)

LangChain의 `_stream` 인터페이스를 오버라이딩하여 `llama-cpp` 엔진의 스트리밍 출력을 제너레이터로 반환합니다.

```python
def _stream(self, prompt, stop=None, **kwargs):
    responses = ExaoneLLM.llm(
        prompt,
        stream=True,  # 핵심 옵션
        max_tokens=512,
        stop=stop,
        temperature=0.7
    )
    for response in responses:
        chunk = response['choices'][0]['text']
        if chunk:
            yield GenerationChunk(text=chunk)
```

### ② 워커 태스크 수정 (`ai-worker/tasks/question_generator.py`)

`chain.stream()`을 통해 얻은 토큰을 Redis 채널로 쏴줍니다.

```python
import redis
r = redis.Redis(host='redis', port=6379, db=0)

full_tokens = []
for chunk in chain.stream(input_dict):
    full_tokens.append(chunk)
    r.publish(f"interview_{interview_id}_stream", chunk)  # 실시간 발행

final_content = "".join(full_tokens)  # 마지막에 합쳐서 DB 저장
```

---

## 4. 백엔드 브릿지 및 프론트 연동 예시 (향후 과제)

### [Backend] FastAPI WebSocket Endpoint

```python
@router.websocket("/ws/interview/{interview_id}/stream")
async def websocket_stream(websocket: WebSocket, interview_id: int):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"interview_{interview_id}_stream")
  
    async for message in pubsub.listen():
        if message['type'] == 'message':
            content = message['data'].decode('utf-8')
            await websocket.send_text(content)
```

---

## 5. 면접용 예상 질문 (Q&A)

### Q: 스트리밍 방식을 쓰면 전체 생성 속도가 빨라지나요?

> **A**: "물리적인 전체 생성 시간은 동일하거나 오히려 아주 미미하게 늘어날 수 있습니다. 하지만 사용자의 **'최초 응답 시간(Time to First Token, TTFT)'**을 10초에서 0.5초로 혁신적으로 단축시키기 때문에, 사용자는 AI가 즉각적으로 응답하고 있다고 느끼게 되어 이탈률을 줄이고 UX를 극대화할 수 있습니다."

### Q: 글자가 한 자씩 나오면 음성(TTS)도 로봇처럼 끊겨서 읽게 되나요?
> **A**: "아니요, 이를 방지하기 위해 **'문장 단위 스트리밍(Sentence-level Streaming)'** 기법을 제안합니다. 시각적으로는 글자를 한 자씩 즉시 보여주지만, 음성 합성은 마침표(.), 물음표(?) 등 문장이 완성되는 기호를 감지했을 때 해당 문장 단위로 수행합니다. 이렇게 하면 읽어주는 목소리는 끊기지 않고 자연스러운 **억양과 호흡**을 유지하면서도, 전체 답변이 끝날 때까지 기다리지 않아도 되므로 속도와 품질을 동시에 잡을 수 있습니다."

---

## 6. 핵심 코드 위치
