# utils/intent_classifier.py - 사용자 의도 분류
from typing import Literal

IntentType = Literal["code_generation", "creative_writing", "general_chat"]


class IntentClassifier:
    """사용자 메시지의 의도를 분류하는 클래스"""
    
    def __init__(self):
        self.code_keywords = [
            "코드", "만들어", "파이썬", "python", "자바스크립트", "javascript", 
            "html", "css", "웹사이트", "앱 만들어", "프로그램", "코드 짜줘", 
            "계산기", "게임", "웹페이지", "앱", "사이트"
        ]
        
        self.story_keywords = [
            "이야기", "동화", "소설", "글 써줘", "스토리", "창작", "글쓰기",
            "주인공", "여자아이", "남자아이", "어린이", "아이가", "들려줘",
            "옛날에", "한번은", "어느날"
        ]
    
    def classify(self, user_message: str) -> IntentType:
        """사용자 메시지 의도 분류"""
        message = user_message.lower()
        
        # 코드 생성 의도 확인
        for keyword in self.code_keywords:
            if keyword in message:
                return "code_generation"
        
        # 창작 의도 확인
        for keyword in self.story_keywords:
            if keyword in message:
                return "creative_writing"
        
        # 기본값은 일반 대화
        return "general_chat"


# 전역 분류기 인스턴스
intent_classifier = IntentClassifier()