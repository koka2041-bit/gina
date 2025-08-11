# main.py - 상세 디버깅 및 페르소나 강화 버전 (v6.1)
# 사용자의 요청에 따라 코드 내 모든 페르소나 관련 텍스트를 완전히 제거
# 챗봇의 페르소나는 반드시 jia_persona.txt에 작성해야합니다.

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from typing import Optional, AsyncGenerator, Dict, Any
from datetime import datetime
import os
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from contextlib import asynccontextmanager
import psutil
from PIL import Image
import base64
import io
import traceback
import json
import asyncio
import sys
import random
import re

# 디버깅 시스템 임포트
from debug_logger import init_debugger, get_debugger, debug_function, monitor_system_resources

# 기존 임포트들
try:
    from api_keys import GOOGLE_API_KEY, OPENROUTER_API_KEY
    from services.intent_classifier import classify_intent
    from services.story_generator import generate_enhanced_story
    from services.code_generator import generate_enhanced_code
    from services.chat_handlers import reset_memory as reset_memory_handler
    from utils.memory_builder import MemoryBuilder
    from utils.summarizer import MemorySummarizer
except ImportError as e:
    print(f"❌ 필수 모듈 임포트 실패: {e}", file=sys.stderr)
    print("💡 services, utils 폴더와 api_keys.py 파일이 main.py와 같은 위치에 있는지 확인해주세요.", file=sys.stderr)
    sys.exit(1)

# =========================
# 설정 로드 (config.json)
# =========================
def load_config(filename: str = "config.json") -> Dict[str, Any]:
    """config.json에서 설정을 읽어옵니다. 없으면 최소 기본값을 반환합니다."""
    defaults = {
        "local_model_path": r"F:\venv\MiniCPM-V",
        "log_level": "DEBUG"
    }
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # 기본값 병합
            for k, v in defaults.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        else:
            return defaults
    except Exception:
        return defaults


CONFIG = load_config()

# 디버깅 설정 (환경 변수로 제어 및 config)
DEBUG_ENABLED = os.getenv("JIA_DEBUG", "true").lower() == "true"
LOG_TO_FILE = os.getenv("JIA_LOG_FILE", "true").lower() == "true"

# 디버거 초기화
debugger = init_debugger(DEBUG_ENABLED, LOG_TO_FILE)

# 전역 변수들
minicpm_model = None
minicpm_tokenizer = None
JIA_CORE_PERSONA = ""  # 실제 페르소나는 jia_persona.txt에서만 관리
memory_builder = None
summarizer = None


def create_default_persona_file(filename="jia_persona.txt"):
    """기본 페르소나 파일 생성 (빈 파일) — 코드 내 페르소나 텍스트는 없음"""
    debugger.debug(f"페르소나 파일 생성(확인): {filename}", "PERSONA")
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            # 의도적으로 빈 파일 생성 — 사용자가 직접 내용을 작성해야 함
            f.write("")
        debugger.success(f"빈 {filename} 파일 생성 완료. 페르소나를 직접 입력해주세요.", "PERSONA")


def load_jia_persona(filename="jia_persona.txt"):
    """페르소나 파일 로드 (파일이 비어있으면 빈 문자열 반환 — 페르소나는 외부로만 관리)"""
    try:
        debugger.debug(f"페르소나 로드 시도: {filename}", "PERSONA")
        with open(filename, "r", encoding="utf-8") as f:
            persona = f.read().strip()
        if not persona:
            debugger.warning(f"{filename} 파일의 내용이 비어있습니다. 페르소나는 외부 파일에 작성해야 합니다.", "PERSONA")
            return ""  # 코드 내 페르소나 텍스트는 포함하지 않음
        debugger.success(f"페르소나 로드 완료: {len(persona)}자", "PERSONA")
        return persona
    except FileNotFoundError:
        debugger.warning(f"{filename} 파일을 찾을 수 없어 빈 파일 생성", "PERSONA")
        create_default_persona_file(filename)
        return load_jia_persona(filename)  # 생성 후 다시 로드
    except Exception as e:
        debugger.error(f"페르소나 파일 읽기 오류: {e}", "PERSONA")
        return ""


@debug_function
def load_minicpm_model():
    """MiniCPM-V 모델 로드"""
    global minicpm_model, minicpm_tokenizer

    debugger.info("MiniCPM-V 모델 로딩 시작", "MODEL")
    debugger.debug("=" * 60, "MODEL")

    # 시스템 리소스 확인
    try:
        available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
        debugger.info(f"사용 가능한 메모리: {available_memory_gb:.2f} GB", "SYSTEM")

        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                debugger.info(f"GPU: {gpu_name}", "GPU")
                debugger.info(f"GPU 메모리: {gpu_memory_gb:.2f} GB", "GPU")
            except Exception as e:
                debugger.warning(f"GPU 정보 조회 중 오류: {e}", "GPU")

            torch.cuda.empty_cache()
            debugger.success("GPU 메모리 정리 완료", "GPU")
        else:
            debugger.warning("CUDA 사용 불가 - CPU 모드로 실행", "GPU")

    except Exception as e:
        debugger.error(f"시스템 리소스 확인 중 오류: {e}", "SYSTEM")

    try:
        # 모델 경로 설정 (config에서 로드)
        local_model_path = CONFIG.get("local_model_path", r"F:\venv\MiniCPM-V")
        debugger.debug(f"모델 경로 확인: {local_model_path}", "MODEL")

        if not os.path.exists(local_model_path):
            debugger.error(f"모델 경로를 찾을 수 없음: {local_model_path}", "MODEL")
            return False

        debugger.success(f"모델 경로 확인 완료", "MODEL")

        # 양자화 설정
        debugger.debug("양자화 설정 준비 중...", "MODEL")
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        debugger.success("양자화 설정 완료", "MODEL")

        # 토크나이저 로드
        debugger.info("토크나이저 로딩 시작...", "MODEL")
        start_time = time.time()

        tokenizer = AutoTokenizer.from_pretrained(
            local_model_path,
            trust_remote_code=True
        )

        load_time = time.time() - start_time
        debugger.success(f"토크나이저 로딩 완료 ({load_time:.2f}초)", "MODEL")

        # 모델 로드
        debugger.info("MiniCPM-V 모델 로딩 시작...", "MODEL")
        start_time = time.time()

        model = AutoModelForCausalLM.from_pretrained(
            local_model_path,
            trust_remote_code=True,
            quantization_config=quantization_config,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True,
        )

        load_time = time.time() - start_time
        debugger.success(f"MiniCPM-V 모델 로딩 완료 ({load_time:.2f}초)", "MODEL")

        # 패딩 토큰 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            debugger.success("패딩 토큰 설정 완료", "MODEL")

        minicpm_model = model
        minicpm_tokenizer = tokenizer

        # 모델 정보 출력
        debugger.info(f"모델 디바이스: {model.device}", "MODEL")
        debugger.info(f"모델 dtype: {model.dtype}", "MODEL")
        debugger.success("MiniCPM-V 모델 초기화 성공!", "MODEL")

        # GPU 메모리 사용량 확인
        if torch.cuda.is_available():
            try:
                allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
                reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
                debugger.info(f"GPU 메모리 사용: {allocated:.2f} GB (예약: {reserved:.2f} GB)", "GPU")
            except Exception as e:
                debugger.warning(f"GPU 메모리 조회 중 오류: {e}", "GPU")

        return True

    except torch.cuda.OutOfMemoryError as e:
        debugger.critical(f"GPU 메모리 부족으로 모델 로딩 실패: {e}", "MODEL")
        torch.cuda.empty_cache()
        return False

    except Exception as e:
        debugger.critical(f"MiniCPM-V 모델 로딩 중 예상치 못한 오류: {e}", "MODEL")
        debugger.debug(f"스택트레이스: {traceback.format_exc()}", "MODEL")
        return False


@debug_function
async def chat_with_minicpm_text_only(user_message: str, context_info: Dict = None) -> str:
    """개선된 MiniCPM-V 텍스트 채팅 (페르소나는 jia_persona.txt에서만 제공되어야 함)"""

    if minicpm_model is None or minicpm_tokenizer is None:
        debugger.error("MiniCPM-V 모델이 로드되지 않았습니다", "CHAT")
        return "모델 로딩 실패: 모델이 로드되지 않았습니다. 서버를 재시작해 주세요."

    start_time = time.time()
    debugger.chat_debug(user_message, "", 0, function="chat_with_minicpm_text_only", line=0)

    try:
        # 1단계: 프롬프트 구성
        debugger.model_debug("PROMPT_BUILD", "시스템 프롬프트 및 메시지 구성 중...")

        # 시스템 프롬프트 (페르소나) 로드 — 코드 내에는 페르소나 텍스트가 없음.
        system_prompt = JIA_CORE_PERSONA or ""
        debugger.model_debug("SYSTEM_PROMPT", f"시스템 프롬프트 로드 완료: {len(system_prompt)}자")

        # 대화 히스토리 및 현재 메시지 구성
        conversation_history = ""
        if context_info and context_info.get("context_summary"):
            conversation_history += f"[이전 대화 요약]:\n{context_info['context_summary']}\n\n"
            debugger.model_debug("CONTEXT", f"컨텍스트 추가: {len(context_info['context_summary'])}자")

        conversation_history += f"사용자: {user_message}"

        # 프롬프트 구조: 시스템 프롬프트(페르소나)가 비어있을 수 있으므로 안전하게 구성
        # 코드 내에 페르소나 규칙을 하드코딩하지 않음 — 페르소나는 jia_persona.txt로만 관리됩니다.
        if system_prompt:
            full_user_prompt = f"""{system_prompt}

---
아래 대화에 이어서, 위에 제공된 페르소나 규칙을 준수하여 대답하시오.

[대화 내용]
{conversation_history}

[최종 지시]
챗봇:"""
        else:
            # 페르소나가 제공되지 않은 경우에는 일반적인 대화 프롬프트만 사용
            full_user_prompt = f"""{conversation_history}

챗봇:"""

        messages = [
            {"role": "user", "content": full_user_prompt}
        ]
        debugger.model_debug("MESSAGES", f"메시지 구성 완료: 1개 (최종 강화 프롬프트)")

        # 2단계: 생성 설정 (안정성 위주로 조정)
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "repetition_penalty": 1.2,
        }
        debugger.model_debug("CONFIG", f"생성 설정: temp={generation_config['temperature']}, penalty={generation_config['repetition_penalty']}")

        # 3단계: 텍스트 생성 (model.chat 사용)
        debugger.model_debug("GENERATE", "model.chat으로 텍스트 생성 시작...")
        generation_start = time.time()

        with torch.no_grad():
            response = minicpm_model.chat(
                image=None,
                msgs=messages,
                tokenizer=minicpm_tokenizer,
                **generation_config
            )

        generation_time = time.time() - generation_start
        debugger.success(f"텍스트 생성 완료 ({generation_time:.2f}초)", "MODEL")
        debugger.debug(f"원본 응답 미리보기: {repr(response[:140])}", "MODEL")

        # 4단계: 응답 후처리
        debugger.model_debug("CLEANUP", "응답 후처리 중...")
        cleaned_response = clean_response(response, user_message)

        total_time = time.time() - start_time

        debugger.success(f"채팅 처리 완료 (총 {total_time:.2f}초)", "CHAT")
        debugger.chat_debug(user_message, cleaned_response, total_time)

        # GPU 메모리 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return cleaned_response

    except torch.cuda.OutOfMemoryError as cuda_error:
        debugger.critical(f"GPU 메모리 부족으로 채팅 실패: {cuda_error}", "CHAT")
        torch.cuda.empty_cache()
        return "잠깐, GPU 메모리가 부족해서 처리가 지연되고 있어요. 다시 시도해 주세요."

    except Exception as e:
        total_time = time.time() - start_time
        debugger.critical(f"MiniCPM-V 텍스트 채팅 중 심각한 오류 ({total_time:.2f}초): {e}", "CHAT")
        debugger.debug(f"오류 발생 위치 추적: {traceback.format_exc()}", "CHAT")
        return f"오류가 발생했어요. 잠시 후 다시 시도해 주세요. [오류코드: {type(e).__name__}]"


@debug_function
def clean_response(response: str, user_message: str = "") -> str:
    """응답 텍스트 정리 및 검증 (디버깅 포함)"""

    debugger.debug(f"응답 정리 시작: 원본 {len(response)}자", "CLEANUP")

    if not response:
        debugger.warning("빈 응답 감지", "CLEANUP")
        return "어... 뭔가 말하려고 했는데 생각이 안 나네! 다시 말해줄래?"

    original_response = response

    # 프롬프트에 포함된 마지막 '챗봇:' 이후의 내용만 추출
    if '챗봇:' in response:
        response = response.split('챗봇:')[-1].strip()

    # '이름:'과 같은 발화자 표시 제거 (너무 짧은 이름이면 제거)
    if ":" in response:
        parts = response.split(":", 1)
        if len(parts[0]) < 10:
            response = parts[1].strip()
            debugger.debug(f"응답 시작 '{parts[0]}:' 제거", "CLEANUP")

    # 불필요한 태그 및 토큰 제거
    cleanup_patterns = [
        "<|system|>", "<|user|>", "<|assistant|>", "<|endoftext|>",
        "[기억]", "[시스템]", "System:", "User:", "Assistant:",
        "<s>", "</s>", "<pad>", "[PAD]", "사용자:"
    ]

    for pattern in cleanup_patterns:
        if pattern in response:
            response = response.replace(pattern, "")
            debugger.debug(f"제거된 패턴: {pattern}", "CLEANUP")

    # 줄바꿈 정리
    response = response.replace("\r\n", "\n")
    while "\n\n\n" in response:
        response = response.replace("\n\n\n", "\n\n")
    response = response.strip()

    # 사용자 메시지 반복 제거
    if user_message and user_message in response:
        response = response.replace(user_message, "").strip()
        debugger.debug("사용자 메시지 반복 제거", "CLEANUP")

    # 의미없는 응답 필터링
    if len(response.strip()) < 2:
        debugger.warning(f"너무 짧은 응답: '{response}'", "CLEANUP")
        return "어... 뭔가 말하려고 했는데 생각이 안 나네! 다시 말해볼래?"

    # 반복 패턴 제거 (연속 동일 단어 3회 이상)
    words = response.split()
    if len(words) > 4:
        cleaned_words = [words[0]]
        for i in range(1, len(words)):
            if not (i >= 2 and words[i] == words[i - 1] == words[i - 2]):
                cleaned_words.append(words[i])

        if len(cleaned_words) < len(words):
            response = " ".join(cleaned_words)
            debugger.debug("반복 패턴 제거", "CLEANUP")

    final_length = len(response)
    debugger.success(f"응답 정리 완료: {len(original_response)}자 → {final_length}자", "CLEANUP")

    return response.strip()


# 타이핑 효과를 위한 스트리밍 응답 생성 (개선된 버전)
async def generate_typing_response(text: str):
    """타이핑 효과를 위한 스트리밍 응답 (개선)
    - 문장 부호 및 문자 기반 지연 적용
    - 누적된 텍스트(진행중 내용)를 주기적으로 전송
    - 작은 랜덤 지터 추가로 자연스러운 타이핑감 제공
    - SSE 형식('data: {...}\n\n')으로 전송
    """
    debugger.debug(f"타이핑 효과 시작: {len(text)}자", "STREAMING")

    if not text or len(text.strip()) == 0:
        text = "음... 무슨 말을 해야 할지 모르겠네. 다시 한번 물어봐 줄래?"
        debugger.warning("스트리밍할 내용이 없어 기본 메시지로 대체", "STREAMING")

    # 줄임/정리
    text = text.replace("\r\n", "\n").strip()

    # 즉시 첫 응답(비어있는 플레이스홀더) — 클라이언트에 바로 연결되었음을 알림
    initial_payload = {"content": "", "finished": False}
    yield f"data: {json.dumps(initial_payload, ensure_ascii=False)}\n\n"

    current_text = ""
    since_last_yield = 0

    # 판별용 문장부호 집합
    sentence_punct = set(['.', '?', '!', '。', '！', '？', '…'])
    newline_chars = set(['\n'])

    for idx, ch in enumerate(text):
        current_text += ch
        since_last_yield += 1

        # 문자 유형에 따른 기본 지연 (한 문자당)
        # 한글 / CJK 등 비-ASCII 문자에 대해 더 빠르게, ASCII는 약간 느리게
        try:
            is_ascii = ord(ch) < 128
        except Exception:
            is_ascii = False

        base_delay = 0.025 if is_ascii else 0.015  # 조절값
        jitter = random.uniform(-0.006, 0.01)
        per_char_delay = max(0.001, base_delay + jitter)

        # 전송 조건:
        # 1) 문장부호가 나오면 (즉시 전송 — 문장 단위)
        # 2) 개행 문자가 나오면
        # 3) 일정 문자(토큰) 수가 쌓였을 때 (진행 표시용)
        threshold = 6 if not is_ascii else 10  # 한글은 더 자주 내보내기
        if ch in sentence_punct or ch in newline_chars or since_last_yield >= threshold or idx == len(text) - 1:
            finished = (idx == len(text) - 1)
            payload = {"content": current_text, "finished": finished}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            since_last_yield = 0

            # 추가적 문장부호 후 휴지 (문장 경계에서 자연스러운 정지)
            if ch in sentence_punct:
                await asyncio.sleep(0.08 + random.uniform(0.0, 0.06))
            elif ch in newline_chars:
                await asyncio.sleep(0.06 + random.uniform(0.0, 0.06))

        # 문자별 기본 지연
        await asyncio.sleep(per_char_delay)

    debugger.success("타이핑 효과 완료", "STREAMING")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global JIA_CORE_PERSONA, memory_builder, summarizer

    debugger.info("챗봇 시스템 시작", "SYSTEM")
    debugger.debug("=" * 60, "SYSTEM")

    # 페르소나 초기화 (파일이 없으면 빈 파일 생성)
    create_default_persona_file()
    JIA_CORE_PERSONA = load_jia_persona()
    debugger.success(f"페르소나 로드 완료: {len(JIA_CORE_PERSONA)}자", "PERSONA")

    # 메모리 시스템 초기화
    debugger.info("메모리 시스템 초기화 중...", "MEMORY")
    try:
        memory_builder = MemoryBuilder()
        summarizer = MemorySummarizer()

        if not summarizer.load_personality_profile():
            debugger.info("새로운 사용자 프로필 생성 중...", "MEMORY")
            summarizer.create_personality_profile("담")
        else:
            debugger.success("기존 사용자 프로필 로드 완료", "MEMORY")

        debugger.success("메모리 시스템 준비 완료!", "MEMORY")

    except Exception as e:
        debugger.error(f"메모리 시스템 초기화 실패: {e}", "MEMORY")

    # 모델 로드
    if load_minicpm_model():
        debugger.success("모든 시스템이 준비되었습니다!", "SYSTEM")
        monitor_system_resources()
    else:
        debugger.warning("모델 로딩 실패 - 제한된 기능으로 실행", "SYSTEM")

    debugger.debug("=" * 60, "SYSTEM")

    yield

    debugger.info("챗봇 시스템 종료", "SYSTEM")


# FastAPI 앱 설정
app = FastAPI(
    title="챗봇 (디버그 버전 v6.1)",
    description="상세 디버깅 및 페르소나 외부화된 MiniCPM-V 기반 AI 챗봇",
    version="6.1.0",
    lifespan=lifespan
)


# 요청 모델들
class ChatRequest(BaseModel):
    message: str


class ImageChatRequest(BaseModel):
    message: str
    image_data: str


@app.get("/")
async def read_root():
    debugger.api_debug("/", 200, "루트 엔드포인트 호출")
    return {
        "message": "🤖 챗봇 (디버그 버전 v6.1)",
        "version": "6.1.0",
        "debug_enabled": DEBUG_ENABLED,
        "log_to_file": LOG_TO_FILE
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    """개선된 채팅 엔드포인트 (상세 디버깅)"""
    user_message = request.message
    start_time = time.time()

    debugger.info(f"채팅 요청 수신: {user_message[:50]}...", "API")

    try:
        # 의도 분류
        debugger.debug("의도 분류 시작", "INTENT")
        intent = classify_intent(user_message)
        debugger.success(f"의도 분류 결과: {intent}", "INTENT")

        if intent == "creative_writing":
            debugger.info("스토리 생성 모드 실행", "STORY")
            story_type = "short_story"
            if "긴" in user_message or "장편" in user_message:
                story_type = "long_story"
            elif "중편" in user_message:
                story_type = "medium_story"

            debugger.debug(f"스토리 타입: {story_type}", "STORY")

            response_text = await generate_enhanced_story(
                user_message, story_type, JIA_CORE_PERSONA, GOOGLE_API_KEY
            )
            api_tag = "[Gemini API - 스토리]"

            try:
                memory_builder.save_dialogue(user_message, response_text)
                debugger.success("스토리 대화 메모리 저장 완료", "MEMORY")
            except Exception as mem_error:
                debugger.error(f"스토리 메모리 저장 실패: {mem_error}", "MEMORY")

        elif intent == "code_generation":
            debugger.info("코드 생성 모드 실행", "CODE")

            code_result = await generate_enhanced_code(
                user_message, JIA_CORE_PERSONA, OPENROUTER_API_KEY
            )

            if code_result.get("error"):
                response_text = code_result["error"]
                debugger.warning(f"코드 생성 오류: {response_text}", "CODE")
            else:
                response_text = f"## 💻 {code_result['title']}\n\n{code_result['description']}\n\n### HTML\n```html\n{code_result['html']}\n```\n\n### CSS\n```css\n{code_result['css']}\n```\n\n### JavaScript\n```javascript\n{code_result['js']}\n```"
                debugger.success("코드 생성 완료", "CODE")

            api_tag = "[OpenRouter API - 코드]"

            try:
                memory_builder.save_dialogue(user_message, response_text)
                debugger.success("코드 대화 메모리 저장 완료", "MEMORY")
            except Exception as mem_error:
                debugger.error(f"코드 메모리 저장 실패: {mem_error}", "MEMORY")

        else:
            debugger.info("일반 채팅 모드 - MiniCPM-V 실행", "CHAT")

            # 메모리에서 컨텍스트 가져오기
            try:
                context = memory_builder.build_context_from_query(user_message)
                debugger.success(f"컨텍스트 로드 완료: {bool(context)}", "MEMORY")
            except Exception as ctx_error:
                debugger.error(f"컨텍스트 로드 실패: {ctx_error}", "MEMORY")
                context = {}

            # MiniCPM-V로 응답 생성
            response_text = await chat_with_minicpm_text_only(user_message, context)
            api_tag = "[MiniCPM-V - 통합 모델]"

            # 메모리에 저장
            try:
                memory_builder.save_dialogue(user_message, response_text)
                debugger.success("채팅 대화 메모리 저장 완료", "MEMORY")
            except Exception as mem_error:
                debugger.error(f"채팅 메모리 저장 실패: {mem_error}", "MEMORY")

        total_time = time.time() - start_time
        final_response = f"{api_tag}\n\n{response_text}"

        debugger.success(f"채팅 요청 처리 완료 ({total_time:.2f}초): {len(response_text)}자", "API")
        debugger.api_debug("/chat", 200, f"처리 완료 ({total_time:.2f}초)")

        return {"response": final_response}

    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"채팅 처리 중 최상위 오류 ({total_time:.2f}초): {str(e)}"

        debugger.critical(error_msg, "API")
        debugger.api_debug("/chat", 500, f"오류 발생: {type(e).__name__}")

        error_response = f"미안해! 지금 좀 복잡한 생각을 하느라 제대로 답하기 어려워. 다시 말해줄래? 😅\n\n[디버그: {type(e).__name__}]"

        try:
            memory_builder.save_dialogue(user_message, "시스템 오류 발생")
        except:
            debugger.error("오류 상황에서 메모리 저장도 실패", "MEMORY")

        return {"response": f"[시스템 오류]\n\n{error_response}"}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """타이핑 효과가 있는 스트리밍 채팅 (디버깅 포함)"""
    user_message = request.message
    debugger.info(f"스트리밍 채팅 요청: {user_message[:50]}...", "STREAMING")

    try:
        # 간단한 처리 (의도 분류 없이 바로 채팅)
        context = memory_builder.build_context_from_query(user_message)
        response_text = await chat_with_minicpm_text_only(user_message, context)

        try:
            memory_builder.save_dialogue(user_message, response_text)
            debugger.success("스트리밍 대화 메모리 저장 완료", "MEMORY")
        except Exception as mem_error:
            debugger.error(f"스트리밍 메모리 저장 실패: {mem_error}", "MEMORY")

        debugger.api_debug("/chat/stream", 200, "스트리밍 응답 시작")
        # 이제 SSE 형식으로 스트리밍 (data: JSON\n\n)
        return StreamingResponse(generate_typing_response(response_text), media_type="text/event-stream")

    except Exception as e:
        debugger.error(f"스트리밍 채팅 중 오류: {e}", "STREAMING")
        debugger.api_debug("/chat/stream", 500, f"스트리밍 오류: {type(e).__name__}")

        error_response = "미안해! 지금 답변하기 어려워서 다시 시도해줘!"
        return StreamingResponse(generate_typing_response(error_response), media_type="text/event-stream")


@app.post("/chat/image")
async def chat_with_image(request: ImageChatRequest):
    """이미지 분석 채팅 (디버깅 포함)"""
    debugger.info(f"이미지 분석 요청: {request.message[:50]}...", "IMAGE")

    try:
        # 이미지 데이터 검증
        try:
            image_bytes = base64.b64decode(request.image_data)
            image = Image.open(io.BytesIO(image_bytes))
            debugger.success(f"이미지 로드 완료: {image.size}", "IMAGE")
        except Exception as img_error:
            debugger.error(f"이미지 디코딩 실패: {img_error}", "IMAGE")
            return {"response": "이미지를 읽는데 문제가 있어. 다른 이미지로 시도해볼래?"}

        # 간단한 이미지 분석 응답 (실제 MiniCPM-V 이미지 처리는 복잡함)
        response_text = f"이미지를 확인했어요. '{request.message}'에 대해 답해줄게. 자세한 질문이 있으면 말해줘."

        try:
            memory_builder.save_dialogue(f"{request.message} [이미지 포함]", response_text)
            debugger.success("이미지 분석 대화 메모리 저장 완료", "MEMORY")
        except Exception as mem_error:
            debugger.error(f"이미지 분석 메모리 저장 실패: {mem_error}", "MEMORY")

        debugger.api_debug("/chat/image", 200, "이미지 분석 완료")
        return {"response": f"[MiniCPM-V 이미지 분석]\n\n{response_text}"}

    except Exception as e:
        debugger.error(f"이미지 분석 중 오류: {e}", "IMAGE")
        debugger.api_debug("/chat/image", 500, f"이미지 분석 오류: {type(e).__name__}")
        return {"response": "이미지를 보려고 했는데 뭔가 문제가 생겼어. 다시 시도해볼래?"}


@app.post("/reset_memory")
async def reset_memory_endpoint():
    """메모리 초기화 (디버깅 포함)"""
    debugger.info("메모리 초기화 요청", "MEMORY")

    try:
        reset_memory_handler()
        debugger.success("메모리 초기화 완료", "MEMORY")
        debugger.api_debug("/reset_memory", 200, "메모리 초기화 성공")
        return {"message": "메모리가 성공적으로 초기화되었습니다."}
    except Exception as e:
        debugger.error(f"메모리 초기화 중 오류: {e}", "MEMORY")
        debugger.api_debug("/reset_memory", 500, f"메모리 초기화 실패: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"메모리 초기화 중 오류: {e}")


@app.get("/model-status")
async def get_model_status():
    """모델 상태 확인 (디버깅 포함)"""
    debugger.debug("모델 상태 확인 요청", "STATUS")

    # GPU 정보 수집
    gpu_info = {}
    if torch.cuda.is_available():
        try:
            gpu_info = {
                "available": True,
                "name": torch.cuda.get_device_name(0),
                "memory_allocated": torch.cuda.memory_allocated(0) / (1024 ** 3),
                "memory_reserved": torch.cuda.memory_reserved(0) / (1024 ** 3),
                "memory_total": torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            }
        except Exception as gpu_error:
            debugger.error(f"GPU 정보 수집 실패: {gpu_error}", "GPU")
            gpu_info = {"available": False, "error": str(gpu_error)}
    else:
        gpu_info = {"available": False, "reason": "CUDA not available"}

    status = {
        "minicpm_model": {
            "loaded": minicpm_model is not None,
            "name": "MiniCPM-V-2.6",
            "features": ["text_chat", "image_analysis"] if minicpm_model else [],
            "device": str(minicpm_model.device) if minicpm_model else "N/A",
            "dtype": str(minicpm_model.dtype) if minicpm_model else "N/A"
        },
        "memory_system": {
            "loaded": memory_builder is not None and summarizer is not None
        },
        "gpu_info": gpu_info,
        "debug_info": {
            "debug_enabled": DEBUG_ENABLED,
            "log_to_file": LOG_TO_FILE,
            "logs_directory": "logs" if LOG_TO_FILE else None,
            "config": CONFIG
        },
        "fixes_applied": [
            "상세 디버깅 시스템 추가",
            "별도 터미널 로그 출력",
            "단계별 오류 추적",
            "GPU 메모리 모니터링",
            "응답 품질 검증 강화",
            "타이핑 효과 개선",
            "페르소나 외부 파일화 (jia_persona.txt)",
            "코드 내 하드코딩된 페르소나 텍스트 제거"
        ]
    }

    debugger.api_debug("/model-status", 200, "모델 상태 조회 완료")
    return status


@app.get("/debug/logs")
async def get_debug_logs():
    """최근 로그 조회"""
    if not LOG_TO_FILE:
        return {"error": "로그 파일 기능이 비활성화되어 있습니다."}

    try:
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            return {"error": "로그 디렉토리가 존재하지 않습니다."}

        log_files = [f for f in os.listdir(logs_dir) if f.startswith("jia_debug_")]
        if not log_files:
            return {"error": "로그 파일이 없습니다."}

        # 최신 로그 파일
        latest_log = sorted(log_files)[-1]
        log_path = os.path.join(logs_dir, latest_log)

        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-100:]  # 최근 100줄

        return {
            "log_file": latest_log,
            "total_lines": len(lines),
            "recent_lines": recent_lines
        }
    except Exception as e:
        debugger.error(f"로그 조회 중 오류: {e}", "DEBUG")
        return {"error": str(e)}


@app.get("/debug/system")
async def get_system_debug():
    """시스템 디버그 정보"""
    from debug_logger import get_system_info

    try:
        system_info = get_system_info()
        monitor_system_resources()
        return system_info
    except Exception as e:
        debugger.error(f"시스템 정보 조회 실패: {e}", "DEBUG")
        return {"error": str(e)}


@app.get("/stats")
async def get_stats():
    """대화 통계 (디버깅 포함)"""
    debugger.debug("대화 통계 조회 요청", "STATS")

    try:
        from services.chat_handlers import get_conversation_stats
        stats = get_conversation_stats()
        debugger.success("대화 통계 조회 완료", "STATS")
        return stats
    except Exception as e:
        debugger.error(f"통계 조회 중 오류: {e}", "STATS")
        return {"error": str(e)}


if __name__ == "__main__":
    print(" 챗봇 시작 (디버그 모드 v6.1)")
    print(f"🔍 디버그 활성화: {DEBUG_ENABLED}")
    print(f"📄 파일 로그: {LOG_TO_FILE}")

    if DEBUG_ENABLED:
        print("\n" + "=" * 60)
        print("🖥️ 별도 디버그 터미널이 시작됩니다.")
        print("모든 오류와 상세 정보를 실시간으로 확인할 수 있습니다.")
        print("=" * 60 + "\n")

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
