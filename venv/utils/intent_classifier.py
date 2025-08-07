# utils/intent_classifier.py
import re
from typing import Tuple
from models.request_models import IntentType

class IntentClassifier:
    """사용자 의도 분류 클래스"""
    
    def __init__(self):
        # 스토리 관련 키워드
        self.story_keywords = [
            '이야기', '스토리', '소설', '동화', '모험', '판타지', '로맨스', 
            '미스터리', '공포', '주인공', '등장인물', '플롯', '줄거리',
            'story', 'novel', 'tale', 'fiction', 'character', 'plot',
            '써줘', '만들어줘', '창작', '글쓰기', '문학', '서사'
        ]
        
        # 코드 관련 키워드  
        self.code_keywords = [
            '코드', '프로그램', '함수', '알고리즘', '구현', '개발', '프로그래밍',
            '파이썬', 'python', 'javascript', 'java', 'c++', 'html', 'css',
            'code', 'function', 'algorithm', 'programming', 'development',
            '만들어줘', '작성해줘', '구현해줘', 'def ', 'class ', 'import ',
            '웹', 'web', 'api', 'database', '데이터베이스', 'sql',
            '앱', 'app', 'application', '애플리케이션'
        ]
        
        # 스토리 생성을 나타내는 패턴
        self.story_patterns = [
            r'.*이야기.*써.*',
            r'.*소설.*만들.*',
            r'.*스토리.*생성.*',
            r'.*동화.*창작.*',
            r'.*story.*create.*',
            r'.*write.*story.*'
        ]
        
        # 코드 생성을 나타내는 패턴
        self.code_patterns = [
            r'.*코드.*작성.*',
            r'.*프로그램.*만들.*',
            r'.*함수.*구현.*',
            r'.*code.*write.*',
            r'.*program.*create.*',
            r'.*implement.*function.*',
            r'.*(만들어|작성해|구현해).*코드.*',
            r'.*코드.*(만들어|작성해|구현해).*'
        ]
    
    def classify_intent(self, message: str) -> Tuple[IntentType, float]:
        """
        메시지의 의도를 분류합니다.
        
        Args:
            message: 사용자 입력 메시지
            
        Returns:
            Tuple[IntentType, float]: (의도, 신뢰도)
        """
        message_lower = message.lower()
        
        # 패턴 매칭 먼저 확인 (높은 신뢰도)
        for pattern in self.story_patterns:
            if re.search(pattern, message_lower):
                return IntentType.STORY, 0.9
                
        for pattern in self.code_patterns:
            if re.search(pattern, message_lower):
                return IntentType.CODE, 0.9
        
        # 키워드 기반 분류
        story_score = self._calculate_keyword_score(message_lower, self.story_keywords)
        code_score = self._calculate_keyword_score(message_lower, self.code_keywords)
        
        # 점수 기반 의도 결정
        if story_score > code_score and story_score > 0.3:
            return IntentType.STORY, min(story_score, 0.8)
        elif code_score > story_score and code_score > 0.3:
            return IntentType.CODE, min(code_score, 0.8)
        elif story_score > 0.1 or code_score > 0.1:
            # 낮은 신뢰도로 분류
            if story_score > code_score:
                return IntentType.STORY, 0.5
            else:
                return IntentType.CODE, 0.5
        else:
            return IntentType.CHAT, 0.6
    
    def _calculate_keyword_score(self, message: str, keywords: list) -> float:
        """키워드 기반 점수 계산"""
        matches = 0
        total_words = len(message.split())
        
        for keyword in keywords:
            if keyword in message:
                matches += 1
        
        # 메시지 길이 대비 매칭 키워드 비율
        if total_words == 0:
            return 0.0
            
        score = matches / len(keywords) * 2  # 키워드 매칭 점수
        length_bonus = min(matches / total_words, 0.5)  # 길이 대비 보너스
        
        return min(score + length_bonus, 1.0)
    
    def get_intent_explanation(self, intent: IntentType, confidence: float) -> str:
        """의도 분류 결과 설명"""
        explanations = {
            IntentType.STORY: f"스토리 생성 의도로 분류됨 (신뢰도: {confidence:.1%})",
            IntentType.CODE: f"코드 생성 의도로 분류됨 (신뢰도: {confidence:.1%})", 
            IntentType.CHAT: f"일반 채팅으로 분류됨 (신뢰도: {confidence:.1%})",
            IntentType.UNKNOWN: f"의도를 알 수 없음 (신뢰도: {confidence:.1%})"
        }
        return explanations.get(intent, "알 수 없는 의도")

# 전역 분류기 인스턴스
classifier = IntentClassifier()