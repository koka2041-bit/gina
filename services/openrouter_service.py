# services/openrouter_service.py - OpenRouter API 코드 생성

import os
import requests
import json
from config import settings  # 'settings' 객체 가져오기

# OpenRouter API의 기본 URL
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# OpenRouter 모델이 사용할 프롬프트 설정 (코드 생성을 위한 예시)
CODE_GENERATION_PROMPT = """
다음 요청에 따라 코드를 생성해 주세요.
요청: {prompt}
"""


def get_code_response(prompt: str) -> str:
    """
    OpenRouter API를 호출하여 코드 생성 요청을 보냅니다.
    """
    if not settings.OPENROUTER_API_KEY:
        print("경고: OpenRouter API 키가 설정되지 않았습니다.")
        return "죄송합니다. OpenRouter API 키가 설정되지 않아 코드를 생성할 수 없습니다."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"
    }

    # API 호출을 위한 페이로드 구성
    # OpenRouter는 다양한 모델을 지원하며, 여기서는 예시로 "openrouter/auto"를 사용합니다.
    payload = {
        "model": "openrouter/auto",
        "messages": [
            {"role": "user", "content": CODE_GENERATION_PROMPT.format(prompt=prompt)}
        ]
    }

    try:
        # OpenRouter API 호출
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        # 응답에서 텍스트 추출
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "죄송합니다. OpenRouter API로부터 유효한 응답을 받지 못했습니다."
    except requests.exceptions.RequestException as e:
        print(f"OpenRouter API 요청 중 오류 발생: {e}")
        return "API 요청 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    except Exception as e:
        print(f"응답 처리 중 오류 발생: {e}")
        return "응답을 처리하는 중 오류가 발생했습니다."

