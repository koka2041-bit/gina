# services/intent_classifier.py
# 사용자 메시지의 의도를 분류하는 개선된 분류기입니다.

import json
import os

# 키워드 파일 경로 설정
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "intent_keywords.json")

# 의도 우선순위 정의 (앞에 있을수록 우선)
INTENT_PRIORITY = ["code_generation", "creative_writing", "general_chat"]

# 키워드 로딩
with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
    INTENT_KEYWORDS = json.load(f)


def classify_intent(user_message: str) -> str:
    """사용자 메시지의 의도를 분류합니다."""
    message = user_message.lower()
    matched_intents = []

    # 키워드 기반 의도 매칭
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in message:
                matched_intents.append(intent)
                break  # 하나만 매칭되면 충분

    # 우선순위대로 반환
    for intent in INTENT_PRIORITY:
        if intent in matched_intents:
            return intent

    # 아무 키워드도 없으면 일반 대화로 간주
    return "general_chat"
