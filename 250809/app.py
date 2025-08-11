# app.py - 디버깅 강화 버전 (v5.0)
# 실시간 로그 모니터링과 오류 추적 기능 추가

import streamlit as st
import requests
import json
import time
from PIL import Image
import base64
import io
import os
from datetime import datetime
import threading
import queue

# --- UI 설정 ---
st.set_page_config(
    page_title="지아 챗봇 (디버그 v5.0)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 백엔드 URL 설정 ---
BACKEND_URL = "http://localhost:8001"  # 포트 변경됨

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = False
if "model_status" not in st.session_state:
    st.session_state.model_status = None
if "typing_effect" not in st.session_state:
    st.session_state.typing_effect = True
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "show_logs" not in st.session_state:
    st.session_state.show_logs = False
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []
if "system_info" not in st.session_state:
    st.session_state.system_info = {}


def check_backend_connection():
    """백엔드 서버 연결 상태 확인"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            st.session_state.backend_connected = True
            st.session_state.last_error = None
            return True
    except Exception as e:
        st.session_state.last_error = f"연결 오류: {str(e)}"
        
    st.session_state.backend_connected = False
    return False


def get_model_status():
    """모델 로딩 상태 확인"""
    try:
        response = requests.get(f"{BACKEND_URL}/model-status", timeout=5)
        if response.status_code == 200:
            st.session_state.model_status = response.json()
            return response.json()
    except Exception as e:
        st.session_state.last_error = f"모델 상태 조회 오류: {str(e)}"
    return None


def get_debug_logs():
    """백엔드에서 디버그 로그 가져오기"""
    try:
        response = requests.get(f"{BACKEND_URL}/debug/logs", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.session_state.last_error = f"로그 조회 오류: {str(e)}"
    return None


def get_system_debug():
    """시스템 디버그 정보 가져오기"""
    try:
        response = requests.get(f"{BACKEND_URL}/debug/system", timeout=5)
        if response.status_code == 200:
            st.session_state.system_info = response.json()
            return response.json()
    except Exception as e:
        st.session_state.last_error = f"시스템 정보 조회 오류: {str(e)}"
    return None


def log_debug_message(level, message):
    """프론트엔드 디버그 로그 추가"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "source": "FRONTEND"
    }
    st.session_state.debug_logs.append(log_entry)
    
    # 로그가 너무 많아지면 오래된 것 제거
    if len(st.session_state.debug_logs) > 100:
        st.session_state.debug_logs = st.session_state.debug_logs[-50:]


def send_text_message(message: str):
    """텍스트 메시지 전송 (강화된 오류 처리와 디버깅)"""
    log_debug_message("INFO", f"메시지 전송 시작: {message[:50]}...")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"message": message},
            timeout=60  # 타임아웃 늘림
        )
        
        processing_time = time.time() - start_time
        log_debug_message("INFO", f"응답 수신 (처리시간: {processing_time:.2f}초, 상태: {response.status_code})")
        
        if response.status_code == 200:
            result = response.json().get("response", "응답을 받지 못했습니다.")
            log_debug_message("SUCCESS", f"응답 처리 완료: {len(result)}자")
            st.session_state.last_error = None
            return result
        else:
            error_msg = f"서버 응답 오류 (상태코드: {response.status_code})"
            log_debug_message("ERROR", error_msg)
            st.session_state.last_error = error_msg
            
            # 응답 내용이 있으면 로그에 추가
            try:
                error_detail = response.text[:200]
                log_debug_message("ERROR", f"응답 내용: {error_detail}")
            except:
                pass
                
            return f"❌ {error_msg}"
            
    except requests.exceptions.Timeout:
        error_msg = "요청 타임아웃 (60초 초과)"
        log_debug_message("ERROR", error_msg)
        st.session_state.last_error = error_msg
        return "⏰ 응답 시간이 초과되었습니다. 서버가 처리하는데 시간이 걸리고 있어요."
        
    except requests.exceptions.ConnectionError:
        error_msg = "백엔드 서버 연결 실패"
        log_debug_message("ERROR", error_msg)
        st.session_state.last_error = error_msg
        return "❌ 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
        
    except Exception as e:
        error_msg = f"예상치 못한 오류: {str(e)}"
        log_debug_message("CRITICAL", error_msg)
        st.session_state.last_error = error_msg
        return f"❌ 예상치 못한 오류 발생: {str(e)}"


def send_text_message_with_typing(message: str):
    """타이핑 효과가 있는 텍스트 메시지 전송"""
    log_debug_message("INFO", f"스트리밍 요청 시작: {message[:30]}...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat/stream",
            json={"message": message},
            timeout=60,
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
                    except json.JSONDecodeError as json_error:
                        log_debug_message("WARNING", f"JSON 파싱 오류: {json_error}")
                        continue
                        
            log_debug_message("SUCCESS", f"스트리밍 완료: {len(full_response)}자")
            return full_response
        else:
            log_debug_message("WARNING", "스트리밍 실패, 일반 요청으로 폴백")
            return send_text_message(message)  # 스트리밍 실패 시 일반 요청으로 폴백

    except Exception as e:
        log_debug_message("ERROR", f"스트리밍 요청 실패: {e}")
        return send_text_message(message)  # 오류 시 일반 요청으로 폴백


def send_image_message(message: str, image):
    """이미지가 포함된 메시지 전송"""
    log_debug_message("INFO", f"이미지 분석 요청: {message[:30]}...")
    
    try:
        # 이미지를 base64로 인코딩
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = base64.b64encode(buffer.getvalue()).decode()
        
        log_debug_message("INFO", f"이미지 인코딩 완료: {len(image_data)} bytes")

        response = requests.post(
            f"{BACKEND_URL}/chat/image",
            json={"message": message, "image_data": image_data},
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json().get("response", "응답을 받지 못했습니다.")
            log_debug_message("SUCCESS", f"이미지 분석 완료: {len(result)}자")
            return result
        else:
            error_msg = f"이미지 분석 실패 (상태: {response.status_code})"
            log_debug_message("ERROR", error_msg)
            return f"❌ {error_msg}"
            
    except Exception as e:
        error_msg = f"이미지 분석 중 오류: {str(e)}"
        log_debug_message("ERROR", error_msg)
        return f"❌ {error_msg}"


# --- 메인 UI ---
st.markdown("<h1 style='text-align: center; color: #4285F4;'>지아 챗봇 (디버그 v5.0) 🤖</h1>", unsafe_allow_html=True)

# --- 사이드바: 시스템 상태 및 디버그 ---
with st.sidebar:
    st.header("🔧 시스템 상태")
    
    # 디버그 모드 토글
    st.session_state.debug_mode = st.checkbox("🐛 디버그 모드", value=st.session_state.debug_mode)
    
    if st.session_state.debug_mode:
        st.session_state.show_logs = st.checkbox("📋 실시간 로그 보기", value=st.session_state.show_logs)

    # 백엔드 연결 상태 확인
    if st.button("🔄 상태 새로고침"):
        with st.spinner("상태 확인 중..."):
            log_debug_message("INFO", "시스템 상태 새로고침 시작")
            check_backend_connection()
            if st.session_state.backend_connected:
                get_model_status()
                if st.session_state.debug_mode:
                    get_system_debug()

    # 연결 상태 표시
    if st.session_state.backend_connected:
        st.success("✅ 백엔드 서버 연결됨")
    else:
        st.error("❌ 백엔드 서버 연결 실패")
        st.info("서버를 시작하려면: `python manage_servers.py start`")
        
        if st.session_state.last_error:
            st.error(f"오류: {st.session_state.last_error}")

    # 모델 상태 표시
    st.subheader("🤖 AI 모델 상태")

    if st.session_state.model_status:
        status = st.session_state.model_status
        minicpm_status = status.get("minicpm_model", {})
        memory_status = status.get("memory_system", {})
        gpu_info = status.get("gpu_info", {})
        debug_info = status.get("debug_info", {})

        if minicpm_status.get("loaded"):
            st.success(f"✅ 통합 모델: {minicpm_status.get('name', 'MiniCPM-V')}")
            st.success("✅ 텍스트 채팅: 활성화")
            st.success("✅ 이미지 분석: 활성화")

            device = minicpm_status.get("device", "N/A")
            if device != "N/A":
                st.info(f"🎮 실행 디바이스: {device}")
                
            # GPU 정보
            if gpu_info.get("available"):
                gpu_usage = (gpu_info.get("memory_allocated", 0) / gpu_info.get("memory_total", 1)) * 100
                st.info(f"🔥 GPU: {gpu_info.get('name', 'N/A')}")
                st.info(f"📊 GPU 메모리: {gpu_usage:.1f}% 사용 중")
        else:
            st.error("❌ 통합 모델: MiniCPM-V (로드 실패)")
            st.warning("⚠️ 텍스트 채팅: 제한된 모드")
            st.error("❌ 이미지 분석: 비활성화")

        # 메모리 시스템
        if memory_status.get("loaded"):
            st.success("✅ 메모리 시스템: 활성화")
        else:
            st.error("❌ 메모리 시스템: 비활성화")
            
        # 디버그 정보
        if st.session_state.debug_mode and debug_info:
            st.subheader("🔍 디버그 정보")
            debug_enabled = debug_info.get("debug_enabled", False)
            log_to_file = debug_info.get("log_to_file", False)
            
            if debug_enabled:
                st.success("✅ 백엔드 디버깅: 활성화")
            else:
                st.warning("⚠️ 백엔드 디버깅: 비활성화")
                
            if log_to_file:
                st.success("✅ 로그 파일: 활성화")
                logs_dir = debug_info.get("logs_directory")
                if logs_dir:
                    st.info(f"📁 로그 위치: {logs_dir}/")
            else:
                st.warning("⚠️ 로그 파일: 비활성화")

    else:
        st.info("모델 상태를 가져오는 중...")

    # 시스템 리소스 정보 (디버그 모드)
    if st.session_state.debug_mode:
        st.subheader("💻 시스템 리소스")
        
        if st.button("📊 시스템 정보 새로고침"):
            get_system_debug()
        
        if st.session_state.system_info:
            sys_info = st.session_state.system_info
            
            if "error" not in sys_info:
                st.info(f"🖥️ CPU: {sys_info.get('cpu_percent', 0):.1f}%")
                st.info(f"🧠 메모리: {sys_info.get('memory_percent', 0):.1f}%")
                st.info(f"💾 디스크: {sys_info.get('disk_usage_percent', 0):.1f}%")
                
                if sys_info.get('gpu_available'):
                    gpu_usage = (sys_info.get('gpu_memory_allocated', 0) / sys_info.get('gpu_memory_total', 1)) * 100
                    st.info(f"🎮 GPU 메모리: {gpu_usage:.1f}%")
            else:
                st.error(f"시스템 정보 오류: {sys_info.get('error')}")

    st.markdown("---")

    # UI 설정
    st.subheader("⚙️ UI 설정")
    st.session_state.typing_effect = st.checkbox("⌨️ 타이핑 효과", value=st.session_state.typing_effect)

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

    # 디버그 액션들
    if st.session_state.debug_mode:
        st.subheader("🛠️ 디버그 도구")
        
        if st.button("🔍 백엔드 로그 조회"):
            logs = get_debug_logs()
            if logs:
                st.success(f"로그 파일: {logs.get('log_file', 'N/A')}")
                st.info(f"총 라인 수: {logs.get('total_lines', 0)}")
                
                recent_lines = logs.get('recent_lines', [])
                if recent_lines:
                    st.text_area("최근 로그 (100줄)", "\n".join(recent_lines), height=200)
            else:
                st.error("로그를 가져올 수 없습니다.")
        
        # 프론트엔드 디버그 로그 지우기
        if st.button("🧹 프론트엔드 로그 지우기"):
            st.session_state.debug_logs = []
            st.success("프론트엔드 로그가 지워졌습니다.")

# --- 실시간 로그 표시 영역 (디버그 모드) ---
if st.session_state.debug_mode and st.session_state.show_logs:
    st.subheader("📋 실시간 디버그 로그")
    
    # 로그 레벨 필터
    log_levels = st.multiselect(
        "로그 레벨 필터", 
        ["INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"], 
        default=["ERROR", "CRITICAL", "WARNING"]
    )
    
    # 로그 표시
    log_container = st.container()
    
    with log_container:
        if st.session_state.debug_logs:
            filtered_logs = [log for log in st.session_state.debug_logs if log["level"] in log_levels]
            
            if filtered_logs:
                # 최근 10개만 표시
                recent_logs = filtered_logs[-10:]
                
                for log_entry in reversed(recent_logs):  # 최신순
                    level = log_entry["level"]
                    timestamp = log_entry["timestamp"]
                    message = log_entry["message"]
                    source = log_entry["source"]
                    
                    # 레벨별 색상
                    if level == "ERROR" or level == "CRITICAL":
                        st.error(f"[{timestamp}] {source} | {level}: {message}")
                    elif level == "WARNING":
                        st.warning(f"[{timestamp}] {source} | {level}: {message}")
                    elif level == "SUCCESS":
                        st.success(f"[{timestamp}] {source} | {level}: {message}")
                    else:
                        st.info(f"[{timestamp}] {source} | {level}: {message}")
            else:
                st.info("선택한 레벨의 로그가 없습니다.")
        else:
            st.info("아직 로그가 없습니다.")

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
        log_debug_message("INFO", "대화 기록이 삭제되었습니다")
        st.success("대화 기록이 삭제되었습니다.")
        st.rerun()

    # 메모리 초기화 (개발자용)
    if st.button("⚠️ 메모리 초기화", help="개발자용 - 모든 기억을 삭제합니다"):
        try:
            response = requests.post(f"{BACKEND_URL}/reset_memory")
            if response.status_code == 200:
                st.success("메모리가 초기화되었습니다.")
                st.session_state.messages = []
                log_debug_message("INFO", "메모리 초기화 완료")
            else:
                st.error("초기화에 실패했습니다.")
                log_debug_message("ERROR", "메모리 초기화 실패")
        except Exception as e:
            error_msg = f"메모리 초기화 오류: {str(e)}"
            st.error("백엔드 서버에 연결할 수 없습니다.")
            log_debug_message("ERROR", error_msg)

# --- 메시지 처리 ---
if user_input and st.session_state.backend_connected:
    log_debug_message("INFO", f"사용자 입력: {user_input[:50]}...")
    
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
            log_debug_message("INFO", f"이미지 업로드: {image.size}")
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

    # 응답 품질 검증 (디버그 모드)
    if st.session_state.debug_mode:
        if "복잡한 생각" in response_text or "다시 말해줄래" in response_text:
            log_debug_message("WARNING", "기본 오류 응답 감지됨")
        elif len(response_text) < 20:
            log_debug_message("WARNING", f"응답이 너무 짧음: {len(response_text)}자")
        else:
            log_debug_message("SUCCESS", f"정상적인 응답 생성: {len(response_text)}자")

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
    log_debug_message("ERROR", "백엔드 서버 미연결 상태에서 메시지 전송 시도")

# --- 하단 정보 ---
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("🌐 **웹 인터페이스**: localhost:8501")

with col2:
    st.info(f"🔧 **API 문서**: localhost:{BACKEND_URL.split(':')[-1]}/docs")

with col3:
    if st.button("🚀 백엔드 서버 상태 확인"):
        if check_backend_connection():
            st.success("백엔드 서버가 실행 중입니다!")
            get_model_status()
            log_debug_message("SUCCESS", "백엔드 서버 연결 확인됨")
        else:
            st.error("백엔드 서버를 찾을 수 없습니다.")
            log_debug_message("ERROR", "백엔드 서버 연결 실패")

# --- 실시간 상태 업데이트 ---
if st.session_state.get("first_run", True):
    st.session_state.first_run = False
    with st.spinner("시스템 상태 확인 중..."):
        log_debug_message("INFO", "초기 상태 확인 시작")
        if check_backend_connection():
            get_model_status()
            if st.session_state.debug_mode:
                get_system_debug()

# --- 문제 해결 가이드 ---
with st.expander("🔧 문제 해결 가이드"):
    st.markdown("""
    ### 🚨 "음... 지금 좀 복잡한 생각을 하고 있어서..." 오류 해결법

    **1. 디버그 모드 활성화 (⭐ 강력 추천!)**
    - 사이드바에서 **"🐛 디버그 모드"** 체크박스를 켜세요.
    - **"📋 실시간 로그 보기"**를 켜면 모든 오류를 실시간으로 확인할 수 있습니다.
    - **"ERROR"** 또는 **"CRITICAL"** 레벨의 로그를 찾아 원인을 파악하세요.

    **2. 백엔드 로그 직접 확인**
    - 사이드바 **"🔍 백엔드 로그 조회"** 버튼을 눌러 서버의 상세 로그를 확인하세요.
    - 모델 로딩 실패, 메모리 부족 등 상세한 원인이 기록됩니다.

    **3. 모델 로딩 실패**
    - 사이드바의 **"🤖 AI 모델 상태"**가 "로드 실패"로 표시되는지 확인하세요.
    - 실패 시, 터미널에서 `python manage_servers.py start` 실행 시 출력되는 로그를 확인하세요.
    - 모델 파일 경로가 정확한지 (`main.py`의 `local_model_path`) 확인하세요.

    **4. 메모리 부족 (GPU/RAM)**
    - 사이드바 **"💻 시스템 리소스"**에서 CPU, 메모리, GPU 사용량을 확인하세요.
    - GPU 메모리가 꽉 찼다면, 다른 프로그램을 종료하거나 서버를 재시작하세요. (`python manage_servers.py stop` 후 `start`)

    **5. 서버 재시작**
    - 가장 간단하고 확실한 방법입니다. 터미널에서 아래 명령어를 실행하세요.
    ```bash
    python manage_servers.py stop
    python manage_servers.py start
    ```
    """)

# --- 개선 사항 ---
with st.expander("✨ v5.0 개선 사항"):
    st.markdown("""
    ### 🛠️ v5.0 - 디버깅 시스템 완비

    **주요 개선**
    - ✅ **실시간 로그 모니터링**: 프론트엔드에서 발생하는 모든 이벤트를 실시간으로 추적합니다.
    - ✅ **상세한 시스템 상태**: 사이드바에서 백엔드 모델, 메모리, GPU 상태, 디버그 설정을 상세히 볼 수 있습니다.
    - ✅ **백엔드 로그 조회**: 버튼 클릭 한 번으로 백엔드 서버의 최신 로그를 가져올 수 있습니다.
    - ✅ **강화된 오류 처리**: 모든 함수에 상세한 예외 처리와 로그 기록을 추가하여, 오류 발생 시 원인 파악이 쉬워졌습니다.

    **새로운 기능**
    - 🎯 **디버그 모드**: 디버깅에 필요한 모든 기능을 켜고 끌 수 있는 토글 기능입니다.
    - 🎯 **시스템 리소스 모니터링**: CPU, RAM, Disk, GPU 사용량을 실시간으로 확인할 수 있습니다.
    - 🎯 **프론트엔드 로그**: 프론트엔드에서 발생하는 로그(사용자 입력, API 요청 등)를 별도로 기록하고 보여줍니다.
    """)
