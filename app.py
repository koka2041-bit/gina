# app.py - 타이핑 효과가 포함된 개선된 Streamlit UI

import streamlit as st
import requests
import json
import time
from PIL import Image
import base64
import io

# --- UI 설정 ---
st.set_page_config(
    page_title="지아 챗봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 백엔드 URL 설정 ---
BACKEND_URL = "http://localhost:8000"

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = False
if "model_status" not in st.session_state:
    st.session_state.model_status = None
if "typing_effect" not in st.session_state:
    st.session_state.typing_effect = True


def check_backend_connection():
    """백엔드 서버 연결 상태 확인"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            st.session_state.backend_connected = True
            return True
    except:
        pass

    st.session_state.backend_connected = False
    return False


def get_model_status():
    """모델 로딩 상태 확인"""
    try:
        response = requests.get(f"{BACKEND_URL}/model-status", timeout=5)
        if response.status_code == 200:
            st.session_state.model_status = response.json()
            return response.json()
    except:
        pass
    return None


def send_text_message(message: str):
    """텍스트 메시지 전송 (개선된 오류 처리)"""
    try:
        print(f"🔄 메시지 전송 중: {message[:50]}...")

        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"message": message},
            timeout=45  # 타임아웃 늘림
        )

        print(f"📡 응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json().get("response", "응답을 받지 못했습니다.")
            print(f"✅ 응답 수신 성공: {len(result)}자")
            return result
        else:
            error_msg = f"서버 응답 오류 (상태코드: {response.status_code})"
            print(f"❌ {error_msg}")
            return f"❌ {error_msg}"

    except requests.exceptions.Timeout:
        print("❌ 요청 타임아웃")
        return "⏰ 응답 시간이 초과되었습니다. 서버가 응답하는데 시간이 걸리고 있어요."
    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류")
        return "❌ 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return f"❌ 예상치 못한 오류 발생: {str(e)}"


def send_text_message_with_typing(message: str):
    """타이핑 효과가 있는 텍스트 메시지 전송"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat/stream",
            json={"message": message},
            timeout=45,
            stream=True
        )

        if response.status_code == 200:
            full_response = ""
            placeholder = st.empty()

            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])  # "data: " 부분 제거
                        content = data.get("content", "")
                        full_response = content

                        # 타이핑 효과 표시
                        with placeholder.container():
                            st.markdown(f"🤖 **지아**: {content}")

                        time.sleep(0.03)  # 타이핑 속도 조절

                        if data.get("finished", False):
                            break
                    except json.JSONDecodeError:
                        continue

            return full_response
        else:
            return send_text_message(message)  # 스트리밍 실패 시 일반 요청으로 폴백

    except Exception as e:
        print(f"❌ 스트리밍 요청 실패: {e}")
        return send_text_message(message)  # 오류 시 일반 요청으로 폴백


def send_image_message(message: str, image):
    """이미지가 포함된 메시지 전송"""
    try:
        # 이미지를 base64로 인코딩
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = base64.b64encode(buffer.getvalue()).decode()

        response = requests.post(
            f"{BACKEND_URL}/chat/image",
            json={"message": message, "image_data": image_data},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("response", "응답을 받지 못했습니다.")
    except Exception as e:
        return f"❌ 이미지 분석 중 오류: {str(e)}"


# --- 메인 UI ---
st.markdown("<h1 style='text-align: center; color: #4285F4;'>지아 챗봇 🤖</h1>", unsafe_allow_html=True)

# --- 사이드바: 시스템 상태 ---
with st.sidebar:
    st.header("🔧 시스템 상태")

    # 백엔드 연결 상태 확인
    if st.button("🔄 상태 새로고침"):
        with st.spinner("상태 확인 중..."):
            check_backend_connection()
            if st.session_state.backend_connected:
                get_model_status()

    # 연결 상태 표시
    if st.session_state.backend_connected:
        st.success("✅ 백엔드 서버 연결됨")
    else:
        st.error("❌ 백엔드 서버 연결 실패")
        st.info("서버를 시작하려면: `python manage_servers.py start`")

    # 모델 상태 표시
    st.subheader("🤖 AI 모델 상태")

    if st.session_state.model_status:
        status = st.session_state.model_status
        minicpm_status = status.get("minicpm_model", {})
        memory_status = status.get("memory_system", {})
        fixes = status.get("fixes_applied", [])

        if minicpm_status.get("loaded"):
            st.success(f"✅ 통합 모델: {minicpm_status.get('name', 'MiniCPM-V')}")
            st.success("✅ 텍스트 채팅: 활성화")
            st.success("✅ 이미지 분석: 활성화")

            device = minicpm_status.get("device", "N/A")
            if device != "N/A":
                st.info(f"🎮 실행 디바이스: {device}")
        else:
            st.error("❌ 통합 모델: MiniCPM-V (로드 실패)")
            st.warning("⚠️ 텍스트 채팅: 메모리 기반 모드")
            st.error("❌ 이미지 분석: 비활성화")
            st.info("💡 모델 로딩 실패 시 `python download_model.py`를 실행하거나 메모리를 확보해주세요.")

        # 메모리 시스템
        if memory_status.get("loaded"):
            st.success("✅ 메모리 시스템: 활성화")
        else:
            st.error("❌ 메모리 시스템: 비활성화")

        # 적용된 수정사항
        if fixes:
            st.subheader("🛠️ 적용된 개선사항")
            for fix in fixes:
                st.info(f"✅ {fix}")
    else:
        st.info("모델 상태를 가져오는 중...")

    st.markdown("---")

    # UI 설정
    st.subheader("⚙️ UI 설정")
    st.session_state.typing_effect = st.checkbox("⌨️ 타이핑 효과", value=st.session_state.typing_effect)

    # 기능 설명
    st.subheader("💡 사용 가능한 기능")
    st.markdown("""
    **텍스트 채팅**
    - 일반 대화
    - 이야기 생성 (자동 감지)
    - 코드 생성 (자동 감지)

    **이미지 분석** (MiniCPM-V)
    - 이미지 업로드 후 분석
    - 이미지와 관련된 질문

    **메모리 기능**
    - 대화 기록 저장
    - 사용자 성격 분석
    - 문맥 인식 대화
    """)

    st.markdown("---")

    # 통계 정보
    if st.button("📊 대화 통계 보기"):
        try:
            response = requests.get(f"{BACKEND_URL}/stats")
            if response.status_code == 200:
                stats = response.json()
                st.json(stats)
            else:
                st.error("통계를 가져올 수 없습니다.")
        except:
            st.error("백엔드 서버에 연결할 수 없습니다.")

# --- 메인 채팅 영역 ---
col1, col2 = st.columns([3, 1])

with col1:
    # 채팅 메시지 표시
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # 이미지 업로드 옵션
    uploaded_image = st.file_uploader(
        "🖼️ 이미지 업로드 (선택사항)",
        type=['png', 'jpg', 'jpeg'],
        help="이미지를 업로드하면 MiniCPM-V가 분석합니다"
    )

    # 사용자 입력
    user_input = st.chat_input("메시지를 입력하세요...", key="chat_input")

with col2:
    st.subheader("🎛️ 채팅 옵션")

    # 채팅 모드 선택
    chat_mode = st.radio(
        "채팅 모드",
        ["💬 일반 대화", "📖 이야기 생성", "💻 코드 생성"],
        help="특정 모드를 선택하거나 자동 감지를 사용하세요"
    )

    # 초기화 버튼
    if st.button("🗑️ 대화 기록 지우기"):
        st.session_state.messages = []
        st.success("대화 기록이 삭제되었습니다.")
        st.rerun()

    # 메모리 초기화 (개발자용)
    if st.button("⚠️ 메모리 초기화", help="개발자용 - 모든 기억을 삭제합니다"):
        try:
            response = requests.post(f"{BACKEND_URL}/reset_memory")
            if response.status_code == 200:
                st.success("메모리가 초기화되었습니다.")
                st.session_state.messages = []
            else:
                st.error("초기화에 실패했습니다.")
        except:
            st.error("백엔드 서버에 연결할 수 없습니다.")

# --- 메시지 처리 ---
if user_input and st.session_state.backend_connected:
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 사용자 메시지 표시
    with chat_container:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

    # 챗봇 응답 생성
    with st.spinner("지아가 생각 중..."):
        if uploaded_image is not None:
            # 이미지가 있으면 이미지 분석 모드
            image = Image.open(uploaded_image)
            response_text = send_image_message(user_input, image)
            st.success("📸 이미지가 분석되었습니다!")
        else:
            # 텍스트 전용 모드
            if st.session_state.typing_effect:
                with chat_container:
                    with st.chat_message("assistant", avatar="🤖"):
                        response_text = send_text_message_with_typing(user_input)
            else:
                response_text = send_text_message(user_input)

    # 챗봇 응답 추가 (타이핑 효과가 없는 경우에만)
    if not st.session_state.typing_effect or uploaded_image is not None:
        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # 응답 표시 (타이핑 효과가 없는 경우)
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(response_text)
    else:
        # 타이핑 효과가 있는 경우 메시지 추가
        st.session_state.messages.append({"role": "assistant", "content": response_text})

    # 이미지 업로드 상태 초기화
    if uploaded_image is not None:
        uploaded_image = None

    st.rerun()

elif user_input and not st.session_state.backend_connected:
    st.error("❌ 백엔드 서버가 연결되지 않았습니다. 서버를 먼저 시작해주세요.")

# --- 하단 정보 ---
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("🌐 **웹 인터페이스**: localhost:8501")

with col2:
    st.info("🔧 **API 문서**: localhost:8000/docs")

with col3:
    if st.button("🚀 백엔드 서버 상태 확인"):
        if check_backend_connection():
            st.success("백엔드 서버가 실행 중입니다!")
            get_model_status()
        else:
            st.error("백엔드 서버를 찾을 수 없습니다.")

# --- 실시간 상태 업데이트 ---
if st.session_state.get("first_run", True):
    st.session_state.first_run = False
    with st.spinner("시스템 상태 확인 중..."):
        if check_backend_connection():
            get_model_status()

# --- 문제 해결 가이드 ---
with st.expander("🔧 문제 해결 가이드"):
    st.markdown("""
    ### 🚨 "음... 지금 좀 복잡한 생각을 하고 있어서..." 오류 해결법

    **1. 모델 로딩 확인**
    - 사이드바에서 "MiniCPM-V 모델 상태" 확인
    - "로드 실패" 시 → `python download_model.py` 실행

    **2. 메모리 부족**
    - 시스템 메모리 8GB 이상 권장
    - 다른 프로그램 종료 후 재시도
    - GPU 메모리 정리: 서버 재시작

    **3. API 키 설정**
    - `api_keys.py` 파일에 올바른 API 키 입력
    - Google API Key (Gemini)
    - OpenRouter API Key

    **4. 서버 재시작**
    ```bash
    python manage_servers.py stop
    python manage_servers.py start
    ```

    **5. 로그 확인**
    - 터미널에서 오류 메시지 확인
    - FastAPI 서버 로그 모니터링
    """)

# --- 개선 사항 ---
with st.expander("✨ 최근 개선 사항"):
    st.markdown("""
    ### 🛠️ v4.1.0 수정 사항

    **주요 개선**
    - ✅ MiniCPM-V 텍스트 채팅 로직 완전 재작성
    - ✅ 응답 품질 검증 및 후처리 강화
    - ✅ 오류 처리 및 디버깅 정보 추가
    - ✅ 타이핑 효과 구현 (켜기/끄기 가능)

    **버그 수정**
    - 🔧 기본 오류 메시지만 나오는 문제 해결
    - 🔧 MiniCPM-V 토크나이저 호환성 개선
    - 🔧 GPU 메모리 관리 최적화
    - 🔧 응답 길이 및 품질 제어

    **새로운 기능**
    - 🎯 스트리밍 응답 지원 (`/chat/stream`)
    - 🎯 실시간 타이핑 효과
    - 🎯 상세한 모델 상태 정보
    - 🎯 개선된 오류 메시지
    """)

# --- 사용법 안내 ---
with st.expander("📖 사용법 안내"):
    st.markdown("""
    ### 🤖 지아 챗봇 사용법

    **1. 서버 시작**
    ```bash
    python manage_servers.py start
    ```

    **2. 텍스트 채팅**
    - 일반적인 대화를 나누세요
    - "이야기 써줘", "소설 만들어줘" → 자동으로 이야기 생성
    - "코드 만들어줘", "웹사이트 만들어줘" → 자동으로 코드 생성

    **3. 이미지 분석**
    - 이미지를 업로드하고 질문하세요
    - MiniCPM-V 모델이 이미지를 분석합니다

    **4. 메모리 기능**
    - 지아는 여러분과의 대화를 기억합니다
    - 성격, 관심사, 대화 패턴을 학습합니다
    - 문맥을 이해하고 더 자연스러운 대화를 제공합니다

    **5. 타이핑 효과**
    - 사이드바에서 켜기/끄기 가능
    - 실시간으로 텍스트가 타이핑되는 효과

    **⚠️ 문제 해결**
    - 모델 로딩이 안 될 때: `python download_model.py` 실행
    - API 오류: `API/` 폴더의 API 키 파일들 확인
    - 메모리 부족: 시스템 메모리 8GB 이상 권장
    """)

# --- 자동 새로고침 비활성화 (성능 향상) ---
if not st.session_state.backend_connected:
    st.warning("⚠️ 백엔드 서버가 실행되지 않았습니다. `python manage_servers.py start`로 서버를 시작해주세요.")