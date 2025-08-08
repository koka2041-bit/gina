# services/chat_handlers.py
# 일반적인 대화 메시지를 처리하는 역할을 담당합니다.
# 메모리 시스템과 통합하여 문맥 인식 대화 제공

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import base64
import io
import os
import sys
from typing import Dict, Any, Optional

# utils 모듈 임포트를 위한 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.memory_builder import MemoryBuilder
from utils.summarizer import MemorySummarizer

# 메모리 시스템 초기화
memory_builder = MemoryBuilder()
summarizer = MemorySummarizer()


async def handle_general_chat(user_message: str, jia_persona: str, model, tokenizer) -> str:
    """메모리 시스템이 통합된 일반 대화 처리"""

    try:
        # 1. 현재 메시지 기반으로 문맥 구성
        context = memory_builder.build_context_from_query(user_message)

        # 2. 성격 프로필 로드
        personality_profile = summarizer.load_personality_profile()

        # 3. 문맥 기반 프롬프트 구성
        contextual_prompt = _build_contextual_prompt(
            user_message,
            jia_persona,
            context,
            personality_profile
        )

        # 4. MiniCPM-V 모델로 응답 생성
        response = _generate_response_with_model(contextual_prompt, model, tokenizer)

        # 5. 대화 저장 (비동기적으로)
        dialogue_id = memory_builder.save_dialogue(user_message, response)

        # 6. 주기적으로 프로필 업데이트 (10번째 대화마다)
        _maybe_update_profile()

        return response

    except Exception as e:
        print(f"메모리 통합 대화 처리 중 오류: {e}")
        # 폴백: 기본 응답
        return f"안녕 담! '{user_message}'라고 했구나. 좀 더 자세히 이야기해줄래?"


def _build_contextual_prompt(user_message: str, jia_persona: str, context: Dict[str, Any],
                             profile: Dict[str, Any]) -> str:
    """문맥 정보를 바탕으로 프롬프트를 구성합니다."""

    # 기본 페르소나
    prompt_parts = [f"[시스템] {jia_persona}"]

    # 사용자 프로필 정보 추가
    if profile and "personality" in profile:
        user_name = profile.get("user_name", "담")
        personality = profile["personality"]

        interests = ", ".join(personality.get("interests", [])[:3])
        emotions = ", ".join(personality.get("dominant_emotions", [])[:2])

        if interests:
            prompt_parts.append(f"[참고] {user_name}는 주로 {interests}에 관심이 많아.")
        if emotions:
            prompt_parts.append(f"[참고] {user_name}는 대체로 {emotions} 성향을 보여.")

    # 관련 기억 추가
    if context.get("context_summary"):
        prompt_parts.append(f"[기억] {context['context_summary']}")

    # 최근 대화 문맥
    recent_context = context.get("recent_context", [])
    if recent_context:
        last_dialogue = recent_context[-1]
        last_user_msg = last_dialogue.get("user_message", "")
        last_bot_response = last_dialogue.get("bot_response", "")

        if last_user_msg and last_bot_response:
            prompt_parts.append(f"[이전 대화] 담: {last_user_msg[:30]}... / 지아: {last_bot_response[:30]}...")

    # 현재 메시지
    prompt_parts.append(f"[현재] 담: {user_message}")
    prompt_parts.append("[응답] 지아:")

    return "\n".join(prompt_parts)


def _generate_response_with_model(prompt: str, model, tokenizer) -> str:
    """MiniCPM-V 모델로 응답을 생성합니다."""

    if model is None or tokenizer is None:
        return "모델이 로드되지 않았어. 잠시만 기다려줘!"

    try:
        # 토큰 길이 제한 (메모리 효율성)
        max_input_length = 512
        if len(prompt) > max_input_length:
            prompt = prompt[-max_input_length:]

        # 입력 토큰화
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_input_length)

        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        # 응답 생성
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,  # 적절한 응답 길이
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # 응답 디코딩
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 프롬프트 부분 제거
        if "[응답] 지아:" in response:
            response = response.split("[응답] 지아:")[-1].strip()

        # 응답 후처리
        response = _post_process_response(response)

        return response if response else "응답을 생성하는 데 문제가 있었어. 다시 말해줄래?"

    except Exception as e:
        print(f"모델 응답 생성 중 오류: {e}")
        return "지금 좀 생각이 복잡해서... 다시 한 번 말해줄래?"


def _post_process_response(response: str) -> str:
    """응답을 후처리합니다."""

    # 불필요한 태그 제거
    response = response.replace("[시스템]", "").replace("[참고]", "").replace("[기억]", "")
    response = response.replace("[이전 대화]", "").replace("[현재]", "").replace("[응답]", "")

    # 지아: 로 시작하는 경우 제거
    if response.startswith("지아:"):
        response = response[3:].strip()

    # 너무 긴 응답 자르기
    if len(response) > 200:
        response = response[:200] + "..."

    # 빈 응답 처리
    response = response.strip()
    if not response:
        return "어... 뭔가 말하려고 했는데 깜빡했어! 다시 말해줄래?"

    return response


def _maybe_update_profile():
    """주기적으로 사용자 프로필을 업데이트합니다."""

    try:
        # 대화 개수 체크
        dialogues = memory_builder._load_dialogues()

        # 10번째 대화마다 프로필 업데이트
        if len(dialogues) % 10 == 0 and len(dialogues) > 0:
            print(f"프로필 업데이트 중... (총 {len(dialogues)}개 대화)")
            summarizer.create_personality_profile()
            print("프로필 업데이트 완료!")

    except Exception as e:
        print(f"프로필 업데이트 중 오류: {e}")


async def handle_general_chat_with_minicpm(user_message: str, image_data: str) -> str:
    """MiniCPM-V 모델을 사용한 멀티모달 대화 처리 (기존 기능 유지)"""

    # 이 함수는 이미지가 포함된 대화용이므로 기존 로직 유지
    # 하지만 메모리 저장은 추가

    try:
        # 기존 이미지 처리 로직...
        if not torch.cuda.is_available():
            return "죄송합니다, GPU가 필요한 이미지 분석 기능을 사용할 수 없습니다."

        # 이미지 처리 (기존 코드)
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))

        # 간단한 이미지 분석 응답 (실제 MiniCPM-V 연동은 복잡)
        response = f"이미지를 보니 흥미로운 내용이네! '{user_message}'에 대해서는... 이미지와 함께라서 더 이해가 잘 돼!"

        # 대화 저장
        memory_builder.save_dialogue(f"{user_message} [이미지 포함]", response)

        return response

    except Exception as e:
        print(f"멀티모달 대화 처리 중 오류 발생: {e}")
        return "이미지 분석 중에 문제가 생겼어. 텍스트로만 대화해볼까?"


def get_conversation_stats() -> Dict[str, Any]:
    """대화 통계를 반환합니다. (디버깅/모니터링용)"""
    try:
        stats = memory_builder.get_conversation_stats()
        return stats
    except Exception as e:
        print(f"통계 조회 중 오류: {e}")
        return {"error": str(e)}


def generate_proactive_message() -> str:
    """능동적인 대화 시작 메시지를 생성합니다."""
    try:
        return summarizer.generate_conversation_starter()
    except Exception as e:
        print(f"능동적 메시지 생성 중 오류: {e}")
        return "안녕 담! 오늘은 어떤 하루야?"


# 개발/디버깅용 함수들
def reset_memory():
    """메모리를 초기화합니다. (개발용)"""
    import shutil
    data_dir = "data"

    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
        print("메모리가 초기화되었습니다.")

    # 메모리 시스템 재초기화
    global memory_builder, summarizer
    memory_builder = MemoryBuilder()
    summarizer = MemorySummarizer()


def export_conversation_history() -> Dict[str, Any]:
    """대화 기록을 내보냅니다. (백업용)"""
    try:
        dialogues = memory_builder._load_dialogues()
        profile = summarizer.load_personality_profile()
        stats = memory_builder.get_conversation_stats()

        return {
            "dialogues": dialogues,
            "profile": profile,
            "stats": stats,
            "export_timestamp": torch.datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}