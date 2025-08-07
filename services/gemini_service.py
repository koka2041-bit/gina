# services/gemini_service.py - Gemini API 이야기 생성

import os
import requests
import json
from config import settings  # 'settings' 객체 가져오기

# Gemini API의 기본 URL
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"

# Gemini 모델이 사용할 프롬프트 설정 (이야기 생성을 위한 예시)
STORY_GENERATION_PROMPT = """
다음 주제를 바탕으로 재미있는 이야기를 생성해 주세요.
주제: {prompt}
"""


def get_story_response(prompt: str) -> str:
    """
    Gemini API를 호출하여 이야기 생성 요청을 보냅니다.
    """
    if not settings.GEMINI_API_KEY:
        print("경고: Gemini API 키가 설정되지 않았습니다.")
        return "죄송합니다. Gemini API 키가 설정되지 않아 이야기를 생성할 수 없습니다."

    headers = {
        "Content-Type": "application/json"
    }

    # API 호출을 위한 페이로드 구성
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": STORY_GENERATION_PROMPT.format(prompt=prompt)
                    }
                ]
            }
        ]
    }

    try:
        # Gemini API 호출
        response = requests.post(f"{BASE_URL}?key={settings.GEMINI_API_KEY}", headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        # 응답에서 텍스트 추출
        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "죄송합니다. Gemini API로부터 유효한 응답을 받지 못했습니다."
    except requests.exceptions.RequestException as e:
        print(f"Gemini API 요청 중 오류 발생: {e}")
        return "API 요청 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    except Exception as e:
        print(f"응답 처리 중 오류 발생: {e}")
        return "응답을 처리하는 중 오류가 발생했습니다."

