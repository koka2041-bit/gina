# 🤖 GINA - AI Assistant API

**G**eneral **I**ntelligent **N**atural **A**ssistant

통합 AI 어시스턴트 API 서버로, 스토리 생성, 코드 생성, 일반 채팅을 제공합니다.

## 🌟 주요 기능

- **🎭 스토리 생성**: Gemini API를 사용한 창의적인 스토리 생성
- **💻 코드 생성**: OpenRouter API를 사용한 다양한 언어의 코드 생성  
- **💬 통합 채팅**: 자동 의도 분류를 통한 스마트한 응답
- **🔍 의도 분류**: 사용자 메시지를 자동으로 분석하여 적절한 서비스로 라우팅

## 📁 프로젝트 구조

```
venv/
├── main.py                     # FastAPI 메인 애플리케이션
├── config.py                   # 설정 및 API 키 관리
├── manage_servers.py           # 서버 관리 스크립트
├── test_client.py              # API 테스트 클라이언트
├── requirements.txt            # 필요한 패키지 목록
├── README.md                   # 프로젝트 가이드
├── .venv                  # 가상환경파일
├── models/
│   ├── __init__.py
│   └── request_models.py       # Pydantic 요청/응답 모델
├── services/
│   ├── __init__.py
│   ├── gemini_service.py       # Gemini API 서비스
│   └── openrouter_service.py   # OpenRouter API 서비스
├── utils/
│   ├── __init__.py
│   ├── intent_classifier.py    # 의도 분류기
│   └── response_formatter.py   # 응답 포맷터
└── API/
    ├── __init__.py
    ├── gemini_api_key.txt      # Gemini API 키 (생성 필요)
    ├── openrouter_api_key.txt  # OpenRouter API 키 (생성 필요)
    ├── chat.py                 # 통합 채팅 엔드포인트
    ├── story.py                # 스토리 생성 엔드포인트
    └── code.py                 # 코드 생성 엔드포인트
```


## 🚀 빠른 시작

### 1. 프로젝트 클론 및 설정

```bash
git clone <your-repository>
cd gina
```

### 2. 자동 설정 (권장)

```bash
python manage_servers.py setup
```

이 명령어는 다음을 수행합니다:
- 필요한 패키지 자동 설치
- API 키 설정 가이드
- 디렉토리 구조 확인

### 3. 서버 시작

```bash
python manage_servers.py start
```

### 4. 테스트

```bash
python test_client.py
```

## 🔧 수동 설정

### 패키지 설치

```bash
pip install -r requirements.txt
```

### API 키 설정

다음 파일들을 생성하고 각각의 API 키를 입력하세요:

1. `API/gemini_api_key.txt` - Google Gemini API 키
2. `API/openrouter_api_key.txt` - OpenRouter API 키

**API 키 획득 방법:**
- **Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenRouter API**: [OpenRouter](https://openrouter.ai/keys)

## 📡 API 엔드포인트

### 기본 정보

- **Base URL**: `http://localhost:8000`
- **API 문서**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`

### 주요 엔드포인트

#### 1. 통합 채팅 API
```http
POST /api/chat
Content-Type: application/json

{
  "message": "파이썬으로 Hello World 프로그램 만들어줘",
  "conversation_history": [],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

#### 2. 스토리 생성 API
```http
POST /api/story
Content-Type: application/json

{
  "prompt": "마법의 숲에서 모험을 떠나는 이야기",
  "genre": "fantasy",
  "length": "short",
  "style": "narrative",
  "max_tokens": 1500,
  "temperature": 0.8
}
```

#### 3. 코드 생성 API
```http
POST /api/code
Content-Type: application/json

{
  "description": "이진 검색 알고리즘 구현",
  "language": "python",
  "complexity": "intermediate",
  "include_comments": true,
  "max_tokens": 2000,
  "temperature": 0.3
}
```

### 정보 조회 엔드포인트

- `GET /api/story/genres` - 지원되는 스토리 장르
- `GET /api/story/lengths` - 스토리 길이 옵션
- `GET /api/story/styles` - 스토리 스타일 옵션
- `GET /api/code/languages` - 지원되는 프로그래밍 언어
- `GET /api/code/complexities` - 코드 복잡도 레벨
- `GET /api/code/examples` - 코드 생성 예시

### 상태 확인 엔드포인트

- `GET /health` - 서버 헬스 체크
- `GET /api/chat/status` - 채팅 서비스 상태
- `GET /api/story/status` - 스토리 서비스 상태
- `GET /api/code/status` - 코드 서비스 상태

## 🎯 의도 분류 시스템

GINA는 사용자의 메시지를 자동으로 분석하여 적절한 서비스로 라우팅합니다:

### 스토리 생성으로 분류되는 키워드
- 이야기, 스토리, 소설, 동화, 모험, 판타지, 로맨스
- "~써줘", "~만들어줘", "창작", "글쓰기"

### 코드 생성으로 분류되는 키워드
- 코드, 프로그램, 함수, 알고리즘, 구현, 개발
- 프로그래밍 언어명 (python, javascript, java 등)
- "~만들어줘", "~작성해줘", "~구현해줘"

### 일반 채팅
- 위 카테고리에 해당하지 않는 모든 질문

## 🛠️ 서버 관리

### manage_servers.py 사용법

```bash
# 패키지 설치
python manage_servers.py install

# 초기 설정 (패키지 설치 + API 키 설정)
python manage_servers.py setup

# 서버 시작
python manage_servers.py start

# 서버 중지
python manage_servers.py stop

# 서버 재시작
python manage_servers.py restart

# 서버 상태 확인
python manage_servers.py status
```

## 🧪 테스트

### 자동 테스트 실행

```bash
python test_client.py
```

### 수동 테스트 예시

#### cURL로 채팅 테스트
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요! 간단한 계산기 프로그램 만들어주세요."}'
```

#### Python requests로 테스트
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"message": "용과 공주에 대한 짧은 동화 써줘"}
)

print(response.json())
```

## 🔍 문제 해결

### 자주 발생하는 문제들

#### 1. 질문 내용이 바뀌는 문제
**원인**: 대화 히스토리 관리 오류
**해결**: 새로운 `response_formatter.py`의 `sanitize_response()` 메서드가 응답을 정제합니다.

#### 2. 코드 생성 기능이 작동하지 않는 문제
**원인**: 구조 분리 후 라우팅 오류
**해결**: `chat.py`의 통합 채팅 엔드포인트가 자동으로 올바른 서비스로 라우팅합니다.

#### 3. API 키 오류
```
⚠️ Gemini API 키가 설정되지 않았습니다.
```
**해결**: `API/gemini_api_key.txt` 파일에 올바른 API 키 입력

#### 4. 모듈 임포트 오류
```
ModuleNotFoundError: No module named 'services'
```
**해결**: 각 폴더에 `__init__.py` 파일이 있는지 확인

#### 5. 서버가 시작되지 않는 문제
```bash
# 포트 사용 중 확인
lsof -i :8000

# 다른 포트로 시작
python manage_servers.py start --port 8001
```

### 로그 확인

서버 실행 중 콘솔에서 다음과 같은 로그를 확인할 수 있습니다:

```
✅ Gemini 모델이 성공적으로 초기화되었습니다.
⚠️ OpenRouter API 키가 설정되지 않았습니다.
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 🔧 개발자 가이드

### 새로운 서비스 추가

1. `services/` 폴더에 새 서비스 클래스 생성
2. `models/request_models.py`에 요청/응답 모델 추가
3. `API/` 폴더에 새 엔드포인트 파일 생성
4. `main.py`에 라우터 등록
5. `utils/intent_classifier.py`에 의도 분류 로직 추가

### 코드 스타일

- **타입 힌트**: 모든 함수에 타입 힌트 사용
- **문서화**: docstring으로 함수 기능 설명
- **에러 처리**: try-catch로 예외 상황 처리
- **로깅**: 중요한 동작에 로그 출력

## 📊 성능 최적화

### 권장 설정

- **Production 환경**: `--reload` 옵션 제거
- **동시 연결**: `--workers` 옵션으로 워커 프로세스 수 조정
- **메모리**: 대화 히스토리는 최근 5개만 유지

```bash
# Production 실행 예시
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🤝 기여하기

1. 이슈 확인 또는 새 이슈 생성
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면:

1. GitHub Issues 생성
2. 프로젝트 위키 확인
3. API 문서(`/docs`) 참조

---

**🎉 GINA와 함께 즐거운 AI 개발 경험을 만들어보세요!**