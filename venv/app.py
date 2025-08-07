# app.py 파일에 저장하세요.

import streamlit as st
import requests
import json
import asyncio

# --- UI 설정 ---
st.set_page_config(
    page_title="지아 챗봇",
    page_icon="🤖",
    layout="centered",  # UI를 중앙에 배치
    initial_sidebar_state="collapsed"  # 사이드바는 기본적으로 접혀있게
)

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []  # 채팅 메시지를 저장할 리스트
if "api_tokens" not in st.session_state:
    st.session_state.api_tokens = {  # 각 API의 토큰 사용량을 저장할 딕셔너리 (임시)
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

# --- UI 컴포넌트 ---

# 챗봇 제목
st.markdown("<h1 style='text-align: center; color: #4285F4;'>지아 챗봇 🤖</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5F6368;'>무엇을 도와드릴까요, 담?</p>", unsafe_allow_html=True)

# 채팅 메시지 표시 영역
# Gemini UI와 유사하게 메시지 버블 형태로 표시
# st.session_state.messages에 있는 모든 메시지를 화면에 표시
for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- 사용자 입력 처리 ---
if user_input := st.chat_input("메시지를 입력하세요...", key="chat_input"):
    # 1. 사용자 메시지를 세션 상태에 즉시 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. 새로운 사용자 메시지가 화면에 표시되도록 스크립트 재실행
    #    st.chat_input은 메시지 입력 시 스크립트를 재실행하므로,
    #    여기서 st.rerun()을 호출하면 UI가 업데이트됩니다.
    #    이 시점에서 사용자는 자신이 입력한 메시지를 즉시 볼 수 있습니다.
    st.rerun()

# --- 챗봇 응답 생성 ---
# 마지막 메시지가 사용자 메시지이고, 아직 챗봇 응답이 없는 경우에만 실행
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":

    # 챗봇 응답을 위한 메시지 컨테이너와 스피너 표시
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("지아가 생각 중..."):
            try:
                # 백엔드에 메시지 전송
                response_from_backend = requests.post(BACKEND_URL,
                                                      json={"message": st.session_state.messages[-1]["content"]})
                response_from_backend.raise_for_status()
                response_text = response_from_backend.json().get("response", "응답을 받지 못했습니다.")
            except requests.exceptions.ConnectionError:
                response_text = "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
            except requests.exceptions.RequestException as e:
                response_text = f"API 요청 중 오류 발생: {e}"

        # 챗봇 응답을 화면에 표시
        st.markdown(response_text)

    # 챗봇 응답을 세션 상태에 추가
    st.session_state.messages.append({"role": "assistant", "content": response_text})

    # 챗봇 메시지가 추가되었으므로, 채팅 UI의 스크롤을 맨 아래로 내리기 위해 다시 새로고침
    st.rerun()

# --- 토큰 사용량 대시보드 (사이드바) ---
st.sidebar.title("API 토큰 사용량")
st.sidebar.markdown("---")

for api_name, data in st.session_state.api_tokens.items():
    st.sidebar.markdown(f"**{api_name}**")
    st.sidebar.markdown(f"사용량: {data['used']}")
    st.sidebar.markdown(f"제한: {data['limit']}")
    st.sidebar.markdown("---")

st.sidebar.markdown("이 값은 임시이며, 실제 API 연동 시 업데이트됩니다.")
