# app.py 파일에 저장하세요.

import streamlit as st
import requests
import json
import asyncio

# --- UI 설정 ---
st.set_page_config(
    page_title="지아 챗봇",
    page_icon="🤖",
    layout="centered", # UI를 중앙에 배치
    initial_sidebar_state="collapsed" # 사이드바는 기본적으로 접혀있게
)

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = [] # 채팅 메시지를 저장할 리스트
if "api_tokens" not in st.session_state:
    st.session_state.api_tokens = { # 각 API의 토큰 사용량을 저장할 딕셔너리 (임시)
        "Gemini API": {"used": 0, "limit": "무제한"},
        "Claude API": {"used": 0, "limit": "300,000 토큰/일"},
        "Groq API": {"used": 0, "limit": "14,400 질문/일"},
        "Naver Search API": {"used": 0, "limit": "25,000 건/일"},
        "Google Cloud Vision/Video": {"used": 0, "limit": "1000분/1000건/월"},
        "OpenWeather API": {"used": 0, "limit": "무료 티어"},
        # MiniCPM-V 2.6은 로컬에서 실행되므로 토큰 제한 없음
    }

# --- 백엔드 API URL 설정 ---
# FastAPI 서버가 실행 중인 주소로 변경해주세요.
# 현재는 로컬에서 8000번 포트로 실행 중이므로 기본값으로 설정합니다.
BACKEND_URL = "http://localhost:8000/chat"

# --- 비동기 함수로 API 호출 ---
# Streamlit은 기본적으로 동기적으로 동작하지만,
# requests 라이브러리를 사용하여 외부 API를 호출할 때는 비동기 처리가 필요하지 않습니다.
# 하지만 향후 복잡한 비동기 로직이 필요할 경우를 대비하여 구조를 유지합니다.
async def send_message_to_backend(message: str):
    try:
        # 백엔드에 메시지 전송
        response = requests.post(BACKEND_URL, json={"message": message})
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        return response.json().get("response", "응답을 받지 못했습니다.")
    except requests.exceptions.ConnectionError:
        return "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
    except requests.exceptions.RequestException as e:
        return f"API 요청 중 오류 발생: {e}"

# --- UI 컴포넌트 ---

# 챗봇 제목
st.markdown("<h1 style='text-align: center; color: #4285F4;'>지아 챗봇 🤖</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5F6368;'>무엇을 도와드릴까요, 담?</p>", unsafe_allow_html=True)

# 채팅 메시지 표시 영역
# Gemini UI와 유사하게 메시지 버블 형태로 표시
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# --- 사용자 입력 처리 ---
user_input = st.chat_input("메시지를 입력하세요...", key="chat_input")

if user_input:
    # 사용자 메시지를 세션 상태에 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 사용자 메시지를 화면에 즉시 표시
    with chat_container:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

    # 백엔드로부터 응답 받기
    with st.spinner("지아가 생각 중..."):
        # 비동기 함수를 동기적으로 실행 (Streamlit은 기본적으로 동기)
        # asyncio.run()은 이벤트 루프가 이미 실행 중일 때 오류를 발생시킬 수 있으므로
        # requests.post를 직접 호출하는 방식으로 변경합니다.
        # 만약 복잡한 비동기 로직이 필요하다면, 별도의 스레드나 프로세스를 고려해야 합니다.
        response_from_backend = requests.post(BACKEND_URL, json={"message": user_input}).json().get("response", "응답을 받지 못했습니다.")

    # 챗봇 응답을 세션 상태에 추가
    st.session_state.messages.append({"role": "assistant", "content": response_from_backend})

    # 챗봇 응답을 화면에 표시
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response_from_backend)

    # 입력창 초기화 (선택 사항)
    # st.experimental_rerun() # 메시지 전송 후 화면을 새로 고쳐 입력창을 비웁니다.

# --- 토큰 사용량 대시보드 (사이드바) ---
st.sidebar.title("API 토큰 사용량")
st.sidebar.markdown("---")

for api_name, data in st.session_state.api_tokens.items():
    st.sidebar.markdown(f"**{api_name}**")
    st.sidebar.markdown(f"사용량: {data['used']}")
    st.sidebar.markdown(f"제한: {data['limit']}")
    st.sidebar.markdown("---")

st.sidebar.markdown("이 값은 임시이며, 실제 API 연동 시 업데이트됩니다.")

