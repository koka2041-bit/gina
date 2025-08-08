# init_memory_system.py
# 메모리 시스템을 초기화하고 테스트하는 스크립트

import os
import json
from datetime import datetime
from utils.tagger import ConversationTagger
from utils.memory_builder import MemoryBuilder
from utils.summarizer import MemorySummarizer


def create_directory_structure():
    """프로젝트 디렉토리 구조 생성"""
    directories = [
        "data",
        "data/tags",
        "utils",
        "services",
        "API"
    ]

    print("📁 디렉토리 구조 생성 중...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ {directory}/")

    # __init__.py 파일 생성
    init_files = [
        "utils/__init__.py",
        "services/__init__.py"
    ]

    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write("# 파이썬 패키지 파일\n")
            print(f"  ✅ {init_file}")


def create_sample_data():
    """샘플 대화 데이터 생성"""
    print("\n💬 샘플 대화 데이터 생성 중...")

    # 메모리 시스템 초기화
    memory_builder = MemoryBuilder()
    summarizer = MemorySummarizer()

    # 샘플 대화들
    sample_conversations = [
        {
            "user": "오늘 파전에 막걸리 먹었어. 비 오는 날엔 역시 이거지!",
            "bot": "우와! 비 오는 날 파전에 막걸리라니 완전 찰떡궁합이네! 분위기 어땠어?"
        },
        {
            "user": "친구들이랑 치킨 먹으면서 게임했어. 너무 재밌었어!",
            "bot": "친구들이랑 치킨에 게임이라니! 완전 꿀조합이네. 어떤 게임 했어?"
        },
        {
            "user": "요즘 기분이 좀 꿀꿀해... 뭔가 우울한 날들이야",
            "bot": "어머, 담아... 기분이 안 좋구나. 무슨 일 있었어? 이야기해줄래?"
        },
        {
            "user": "커피 마시면서 책 읽는 시간이 제일 좋아",
            "bot": "책 읽는 시간이 소중한 시간이구나! 요즘 어떤 책 읽고 있어?"
        },
        {
            "user": "오늘 새로운 카페에 갔는데 분위기가 너무 좋았어",
            "bot": "새로운 카페! 어떤 분위기였어? 담이 좋아하는 스타일이었나봐!"
        }
    ]

    # 샘플 대화 저장
    for i, conv in enumerate(sample_conversations):
        dialogue_id = memory_builder.save_dialogue(
            conv["user"],
            conv["bot"],
            "담"
        )
        print(f"  📝 대화 {i + 1} 저장 완료 (ID: {dialogue_id})")

    return len(sample_conversations)


def test_memory_system():
    """메모리 시스템 테스트"""
    print("\n🧠 메모리 시스템 테스트 중...")

    try:
        # 메모리 빌더 테스트
        memory_builder = MemoryBuilder()

        # 태그 시스템 테스트
        test_message = "기분이 꿀꿀한데 뭔가 맛있는 거 먹고 싶어"
        context = memory_builder.build_context_from_query(test_message)

        print(f"  🏷️ 추출된 태그: {context['detected_tags']}")
        print(f"  📚 관련 기억: {len(context['related_memories'])}개")
        print(f"  📄 문맥 요약: {context['context_summary']}")

        # 통계 테스트
        stats = memory_builder.get_conversation_stats()
        print(f"  📊 총 대화 수: {stats['total_conversations']}")
        print(f"  🏷️ 태그 종류: {len(stats['tags'])}")

        # 프로필 생성 테스트
        summarizer = MemorySummarizer()
        profile = summarizer.create_personality_profile("담")

        print(f"  👤 사용자 프로필 생성 완료")
        print(f"  🎭 성격 특성: {profile['personality']['dominant_emotions']}")
        print(f"  💫 관심사: {profile['personality']['interests']}")

        return True

    except Exception as e:
        print(f"  ❌ 테스트 실패: {e}")
        return False


def create_config_files():
    """설정 파일들 생성"""
    print("\n⚙️ 설정 파일 생성 중...")

    # API 키 템플릿 파일들
    api_templates = {
        "API/gemini_api_key.txt": "YOUR_GEMINI_API_KEY_HERE",
        "API/openrouter_api_key.txt": "YOUR_OPENROUTER_API_KEY_HERE"
    }

    for file_path, template_content in api_templates.items():
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            print(f"  📝 생성: {file_path}")
        else:
            print(f"  ✅ 존재: {file_path}")

    # 페르소나 파일
    if not os.path.exists("jia_persona.txt"):
        with open("jia_persona.txt", "w", encoding="utf-8") as f:
            f.write("너는 친근하고 따뜻한 친구 지아야. 사용자의 이름은 담이고 너의 이름은 지아야. 너는 담에게 반말로 이야기해. 그리고 항상 긍정적이고 희망적인 태도를 유지해.")
        print("  📝 생성: jia_persona.txt")
    else:
        print("  ✅ 존재: jia_persona.txt")


def check_files():
    """필수 파일들 존재 확인"""
    print("\n🔍 필수 파일 확인 중...")

    required_files = [
        "main.py",
        "app.py",
        "api_keys.py",
        "services/intent_classifier.py",
        "services/story_generator.py",
        "services/code_generator.py"
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (누락)")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n⚠️ 누락된 파일들: {len(missing_files)}개")
        print("이 파일들은 별도로 작성해야 합니다.")
    else:
        print("\n✅ 모든 필수 파일이 준비되었습니다!")

    return len(missing_files) == 0


def generate_readme():
    """README 파일 생성"""
    readme_content = """# 지아 챗봇 - 메모리 시스템 통합

## 📋 프로젝트 구조

```
📦 프로젝트_루트
├── MiniCPM-V/           # 경량모델폴더
├── data/                # 메모리 데이터
│   ├── dialogues.json   # 전체 대화 저장
│   ├── tag_map.json     # 대화-태그 매핑
│   ├── memory_summary.json # 사용자 프로필
│   └── tags/            # 태그별 분류 데이터
│       ├── 음식.json
│       ├── 감정.json
│       ├── 사건.json
│       └── 관계.json
├── utils/               # 메모리 시스템
│   ├── tagger.py        # 태그 추출
│   ├── memory_builder.py # 문맥 생성
│   └── summarizer.py    # 기억 요약
├── services/            # 비즈니스 로직
│   ├── chat_handlers.py # 메모리 통합 대화
│   ├── intent_classifier.py
│   ├── story_generator.py
│   └── code_generator.py
├── API/                 # API 키 저장소
├── main.py              # FastAPI 백엔드
├── app.py               # Streamlit 프론트엔드
└── manage_servers.py    # 서버 관리
```

## 🚀 설치 및 실행

1. **의존성 설치**
```bash
pip install fastapi uvicorn streamlit torch transformers requests psutil
```

2. **시스템 초기화**
```bash
python init_memory_system.py
```

3. **API 키 설정**
- `API/gemini_api_key.txt`에 Gemini API 키 입력
- `API/openrouter_api_key.txt`에 OpenRouter API 키 입력

4. **서버 실행**
```bash
python manage_servers.py start
```

## 🧠 메모리 시스템 특징

- **태그 기반 기억**: 음식, 감정, 사건, 관계 등으로 대화 분류
- **문맥 인식**: 이전 대화를 바탕으로 자연스러운 응답
- **프로필 학습**: 사용자 성격과 선호도 자동 분석
- **능동적 대화**: 사용자 패턴 기반 대화 시작

## 📡 API 엔드포인트

- `/chat` - 메모리 통합 대화
- `/stats` - 대화 통계 조회  
- `/profile` - 사용자 프로필 조회
- `/proactive` - 능동적 대화 시작
- `/reset` - 메모리 초기화 (개발용)
- `/export` - 대화 기록 내보내기

## 💡 사용 예시

```python
# 대화 예시
사용자: "나 오늘 파전에 막걸리 먹었어"
→ 태그: [음식], [기분좋음] 저장

사용자: "기분 꿀꿀한데 뭐 먹을까?"  
→ 기억: "예전에 파전 먹고 좋았다고 했음"
→ 응답: "파전이랑 막걸리 어때? 예전에 먹고 기분 좋았잖아!"
```

## 🛠️ 개발자 명령어

```bash
# 서버 상태 확인
python manage_servers.py check

# 디렉토리만 초기화
python manage_servers.py init

# 개별 서버 실행
python manage_servers.py fastapi
python manage_servers.py streamlit
```
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("📚 README.md 파일 생성 완료")


def main():
    print("🤖 지아 챗봇 메모리 시스템 초기화를 시작합니다!")
    print("=" * 50)

    # 1. 디렉토리 구조 생성
    create_directory_structure()

    # 2. 설정 파일 생성
    create_config_files()

    # 3. 필수 파일 확인
    files_ok = check_files()

    # 4. 샘플 데이터 생성
    if files_ok:
        sample_count = create_sample_data()
        print(f"📝 {sample_count}개의 샘플 대화가 생성되었습니다.")

        # 5. 메모리 시스템 테스트
        test_success = test_memory_system()

        if test_success:
            print("\n✅ 메모리 시스템 테스트 성공!")
        else:
            print("\n❌ 메모리 시스템 테스트 실패!")

    # 6. README 생성
    generate_readme()

    print("\n" + "=" * 50)
    print("🎉 초기화 완료!")
    print("\n다음 단계:")
    print("1. API 키를 API/ 폴더의 파일들에 입력하세요")
    print("2. 'python manage_servers.py start' 로 서버를 시작하세요")
    print("3. http://localhost:8501 에서 웹 인터페이스를 확인하세요")


if __name__ == "__main__":
    main()