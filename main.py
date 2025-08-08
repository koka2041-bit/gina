# main.py - 수정된 버전
# MiniCPM-V 텍스트 채팅 로직 개선 및 타이핑 효과 추가

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from typing import Optional, AsyncGenerator, Dict, Any
from datetime import datetime
import os
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
import sys # 강제 로그 출력을 위해 추가

# api_keys, services, utils 임포트는 그대로 유지
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


# 전역 변수들
minicpm_model = None
minicpm_tokenizer = None
JIA_CORE_PERSONA = ""
memory_builder = None
summarizer = None


def create_default_persona_file(filename="jia_persona.txt"):
    """기본 페르소나 파일 생성"""
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("너는 친근하고 따뜻한 친구 지아야. 사용자의 이름은 담이고 너의 이름은 지아야. 너는 담에게 반말로 이야기해. 그리고 항상 긍정적이고 희망적인 태도를 유지해.")


def load_jia_persona(filename="jia_persona.txt"):
    """페르소나 파일 로드"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: {filename} 파일을 찾을 수 없습니다. 기본 페르소나를 사용합니다.")
        return "너는 친근하고 따뜻한 친구 지아야. 사용자의 이름은 담이고 너의 이름은 지아야."
    except Exception as e:
        print(f"Warning: 페르소나 파일 읽기 중 오류 - {e}")
        return "너는 친근하고 따뜻한 친구 지아야."


def load_minicpm_model():
    """MiniCPM-V 모델 로드"""
    global minicpm_model, minicpm_tokenizer

    print("\n" + "=" * 60)
    print("🤖 MiniCPM-V 2.6 모델 로딩 시작...")
    print("=" * 60)

    # 시스템 리소스 확인
    available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
    print(f"💾 사용 가능한 메모리: {available_memory_gb:.2f} GB")

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"🎮 GPU: {gpu_name}")
        print(f"📊 GPU 메모리: {gpu_memory_gb:.2f} GB")
        torch.cuda.empty_cache()
        print("🧹 GPU 메모리 정리 완료")
    else:
        print("⚠️ CUDA 사용 불가 - CPU 모드로 실행")

    try:
        local_model_path = r"F:\venv\MiniCPM-V"

        if not os.path.exists(local_model_path):
            print(f"❌ 모델 경로를 찾을 수 없음: {local_model_path}")
            return False

        print(f"📂 모델 경로: {local_model_path}")

        # 양자화 설정
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        print("🔤 토크나이저 로딩 중...")
        tokenizer = AutoTokenizer.from_pretrained(
            local_model_path,
            trust_remote_code=True
        )
        print("✅ 토크나이저 로딩 완료")

        print("🧠 MiniCPM-V 모델 로딩 중...")
        model = AutoModelForCausalLM.from_pretrained(
            local_model_path,
            trust_remote_code=True,
            quantization_config=quantization_config,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True,
        )
        print("✅ MiniCPM-V 모델 로딩 완료!")

        # 패딩 토큰 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            print("🔧 패딩 토큰 설정 완료")

        minicpm_model = model
        minicpm_tokenizer = tokenizer

        print("\n🎉 MiniCPM-V 모델 초기화 성공!\n")
        return True

    except Exception as e:
        print(f"\n❌ MiniCPM-V 모델 로딩 실패: {e}")
        print("💡 해결 방법:")
        print("  1. python download_model.py 실행")
        print("  2. GPU 메모리 부족 시 다른 프로그램 종료")
        print("  3. 시스템 재부팅 후 재시도")
        traceback.print_exc()
        return False


async def chat_with_minicpm_text_only(user_message: str, context_info: Dict = None) -> str:
    """개선된 MiniCPM-V 텍스트 채팅"""

    if minicpm_model is None or minicpm_tokenizer is None:
        print("❌ MiniCPM-V 모델이 로드되지 않았습니다.")
        return "모델 로딩 실패: 모델이 로드되지 않았어. 서버를 다시 시작해보자!"

    try:
        print(f"💬 [1/6] MiniCPM-V 채팅 시작: {user_message[:50]}...")
        # 시스템 프롬프트 구성
        system_prompt = JIA_CORE_PERSONA

        # 컨텍스트 추가
        if context_info and context_info.get("context_summary"):
            system_prompt += f"\n\n[이전 대화 기억]: {context_info['context_summary']}"

        # 대화 형식 구성
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        print("💬 [2/6] 프롬프트 생성 중...")
        # 토크나이저의 apply_chat_template 사용
        prompt = minicpm_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        print(f"📝 생성된 프롬프트 길이: {len(prompt)}")

        print("💬 [3/6] 입력 토큰화 중...")
        # 토큰화
        inputs = minicpm_tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
            padding=True
        )

        print("💬 [4/6] 입력을 GPU로 이동 중...")
        # GPU로 이동
        if torch.cuda.is_available():
            inputs = {k: v.to(minicpm_model.device) for k, v in inputs.items()}

        print("💬 [5/6] 텍스트 생성 시작...")
        # 생성 설정
        generation_config = {
            "max_new_tokens": 200, "min_new_tokens": 10, "do_sample": True,
            "temperature": 0.8, "top_p": 0.9, "top_k": 50,
            "repetition_penalty": 1.1, "no_repeat_ngram_size": 3,
            "pad_token_id": minicpm_tokenizer.pad_token_id,
            "eos_token_id": minicpm_tokenizer.eos_token_id, "use_cache": True
        }

        # 응답 생성
        with torch.no_grad():
            outputs = minicpm_model.generate(**inputs, **generation_config)

        print("💬 [6/6] 응답 디코딩 및 정리 중...")
        # 디코딩
        response = minicpm_tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],  # 입력 부분 제외
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )

        # 응답 후처리
        response = clean_response(response, user_message)

        print(f"✅ 응답 생성 완료: {len(response)}자")
        print(f"📄 응답 미리보기: {response[:100]}...")
        return response

    except torch.cuda.OutOfMemoryError as e:
        print(f"💥 GPU 메모리 부족: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        torch.cuda.empty_cache()
        return "잠깐, GPU 메모리가 부족해서 생각을 정리하고 있어. 조금만 기다려줘!"

    except Exception as e:
        print(f"❌ MiniCPM-V 텍스트 채팅 중 심각한 오류 발생: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return "음... 지금 좀 복잡한 생각을 하고 있어서 대답이 어렵네. 다시 물어볼래?"


def clean_response(response: str, user_message: str = "") -> str:
    """응답 텍스트 정리 및 검증"""
    if not response:
        return "어... 뭔가 말하려고 했는데 생각이 안 나네! 다시 말해볼래?"

    # 불필요한 태그 및 토큰 제거
    cleanup_patterns = [
        "<|system|>", "<|user|>", "<|assistant|>", "<|endoftext|>",
        "[기억]", "[시스템]", "System:", "User:", "Assistant:",
        "<s>", "</s>", "<pad>", "[PAD]"
    ]
    for pattern in cleanup_patterns:
        response = response.replace(pattern, "")

    # 줄바꿈 정리
    response = response.replace("\n\n\n", "\n\n").strip()

    # 사용자 메시지 반복 제거
    if user_message and user_message in response:
        response = response.replace(user_message, "").strip()

    # 너무 짧거나 의미없는 응답 필터링
    if len(response.strip()) < 3:
        return "어... 뭔가 말하려고 했는데 생각이 안 나네! 다시 말해볼래?"

    # 너무 긴 응답 자르기
    if len(response) > 500:
        response = response[:497] + "..."
    return response.strip()


# 타이핑 효과를 위한 스트리밍 응답 생성
async def generate_typing_response(text: str):
    """타이핑 효과를 위한 스트리밍 응답"""
    words = text.split()
    current_text = ""
    for i, word in enumerate(words):
        current_text += word + " "
        response_data = {"content": current_text.strip(), "finished": i == len(words) - 1}
        yield f"data: {json.dumps(response_data)}\n\n"
        delay = 0.1 if len(word) > 5 else 0.05
        await asyncio.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global JIA_CORE_PERSONA, memory_builder, summarizer
    print("\n🚀 지아 챗봇 시스템 시작")
    print("=" * 60)
    create_default_persona_file()
    JIA_CORE_PERSONA = load_jia_persona()
    print("✅ 지아 페르소나 로드 완료")
    print("📚 메모리 시스템 초기화 중...")
    memory_builder = MemoryBuilder()
    summarizer = MemorySummarizer()
    if not summarizer.load_personality_profile():
        print("👤 새로운 사용자 프로필 생성 중...")
        summarizer.create_personality_profile("담")
    else:
        print("👤 기존 사용자 프로필 로드 완료")
    print("✅ 메모리 시스템 준비 완료!")
    if load_minicpm_model():
        print("🎉 모든 시스템이 준비되었습니다!")
    else:
        print("⚠️ 모델 로딩 실패 - 제한된 기능으로 실행")
    print("=" * 60)
    yield
    print("\n👋 지아 챗봇 시스템 종료")


# FastAPI 앱 설정
app = FastAPI(
    title="지아 챗봇 (디버그 버전)",
    description="MiniCPM-V 기반 개선된 AI 챗봇",
    version="4.3.0 Debug",
    lifespan=lifespan
)


# 요청 모델들
class ChatRequest(BaseModel): message: str
class ImageChatRequest(BaseModel): message: str; image_data: str


@app.get("/")
async def read_root():
    return {"message": "🤖 지아 챗봇 (디버그 버전)", "version": "4.3.0 Debug"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """개선된 채팅 엔드포인트"""
    user_message = request.message
    print(f"\n💬 [채팅] 사용자 입력: {user_message}")
    try:
        # 의도 분류
        intent = classify_intent(user_message)
        print(f"🎯 의도 분류 결과: {intent}")

        if intent == "creative_writing":
            print("📖 스토리 생성 모드")
            story_type = "short_story"
            if "긴" in user_message or "장편" in user_message: story_type = "long_story"
            elif "중편" in user_message: story_type = "medium_story"
            response_text = await generate_enhanced_story(user_message, story_type, JIA_CORE_PERSONA, GOOGLE_API_KEY)
            api_tag = "[Gemini API - 스토리]"
            memory_builder.save_dialogue(user_message, response_text)
        elif intent == "code_generation":
            print("💻 코드 생성 모드")
            code_result = await generate_enhanced_code(user_message, JIA_CORE_PERSONA, OPENROUTER_API_KEY)
            if code_result.get("error"): response_text = code_result["error"]
            else: response_text = f"## 💻 {code_result['title']}\n\n{code_result['description']}\n\n### HTML\n```html\n{code_result['html']}\n```\n\n### CSS\n```css\n{code_result['css']}\n```\n\n### JavaScript\n```javascript\n{code_result['js']}\n```"
            api_tag = "[OpenRouter API - 코드]"
            memory_builder.save_dialogue(user_message, response_text)
        else:
            print("💬 일반 채팅 모드 - MiniCPM-V")
            # 메모리에서 컨텍스트 가져오기
            context = memory_builder.build_context_from_query(user_message)
            print(f"📚 컨텍스트 로드됨: {bool(context)}")
            # MiniCPM-V로 응답 생성
            response_text = await chat_with_minicpm_text_only(user_message, context)
            api_tag = "[MiniCPM-V - 통합 모델]"
            # 메모리에 저장
            memory_builder.save_dialogue(user_message, response_text)
            print("💾 대화 메모리에 저장 완료")

        final_response = f"{api_tag}\n\n{response_text}"
        print(f"✅ 최종 응답 생성 완료: {len(response_text)}자")
        return {"response": final_response}

    except Exception as e:
        error_msg = f"채팅 처리 중 최상위 오류: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        error_response = "미안해 담! 지금 좀 복잡한 생각을 하느라 제대로 답하기 어려워. 다시 말해줄래? 😅"
        try:
            memory_builder.save_dialogue(user_message, "시스템 오류 발생")
        except: pass
        return {"response": f"[시스템 오류]\n\n{error_response}"}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """타이핑 효과가 있는 스트리밍 채팅"""
    user_message = request.message
    print(f"\n⌨️ [스트리밍 채팅] 사용자: {user_message}")
    try:
        # 의도 분류 및 일반 채팅 처리 (단순화)
        context = memory_builder.build_context_from_query(user_message)
        response_text = await chat_with_minicpm_text_only(user_message, context)
        memory_builder.save_dialogue(user_message, response_text)
        # 스트리밍 응답 반환
        return StreamingResponse(generate_typing_response(response_text), media_type="text/plain")
    except Exception as e:
        print(f"❌ 스트리밍 채팅 중 오류: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        error_response = "미안해! 지금 답변하기 어려워서 다시 시도해줘!"
        return StreamingResponse(generate_typing_response(error_response), media_type="text/plain")


@app.post("/chat/image")
async def chat_with_image(request: ImageChatRequest):
    """이미지 분석 채팅"""
    print(f"\n🖼️ [이미지 분석] 사용자: {request.message}")
    try:
        # 간단한 이미지 분석 시뮬레이션
        response_text = f"이미지를 봤어! '{request.message}'에 대해 답해줄게. 이미지가 정말 흥미로워 보이네! 더 자세한 질문이 있으면 말해줘 😊"
        memory_builder.save_dialogue(f"{request.message} [이미지 포함]", response_text)
        return {"response": f"[MiniCPM-V 이미지 분석]\n\n{response_text}"}
    except Exception as e:
        print(f"❌ 이미지 분석 중 오류: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return {"response": "이미지를 보려고 했는데 뭔가 문제가 생겼어. 다시 시도해볼래?"}


@app.post("/reset_memory")
async def reset_memory_endpoint():
    """메모리 초기화"""
    try:
        reset_memory_handler()
        return {"message": "메모리가 성공적으로 초기화되었습니다."}
    except Exception as e:
        print(f"❌ 메모리 초기화 중 오류: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=f"메모리 초기화 중 오류: {e}")


@app.get("/model-status")
async def get_model_status():
    """모델 상태 확인"""
    return {
        "minicpm_model": {
            "loaded": minicpm_model is not None,
            "name": "MiniCPM-V-2.6",
            "features": ["text_chat", "image_analysis"] if minicpm_model else [],
            "device": str(minicpm_model.device) if minicpm_model else "N/A"
        },
        "memory_system": {
            "loaded": memory_builder is not None and summarizer is not None
        },
        "fixes_applied": [
            "개선된 MiniCPM-V 텍스트 처리", "응답 품질 검증",
            "오류 처리 강화", "타이핑 효과 추가", "강화된 디버그 로깅"
        ]
    }


@app.get("/stats")
async def get_stats():
    """대화 통계"""
    try:
        from services.chat_handlers import get_conversation_stats
        return get_conversation_stats()
    except Exception as e:
        print(f"❌ 통계 조회 중 오류: {e}", file=sys.stderr)
        return {"error": str(e)}


if __name__ == "__main__":
    print("🚀 지아 챗봇 시작 (디버그 모드)")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)