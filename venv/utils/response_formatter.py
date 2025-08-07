# utils/response_formatter.py
import json
import re
from typing import Dict, Any, Optional
from models.request_models import IntentType

class ResponseFormatter:
    """응답 포맷팅 유틸리티 클래스"""
    
    @staticmethod
    def format_chat_response(response: str, intent: IntentType, confidence: float, 
                           processing_time: float, model_used: str) -> Dict[str, Any]:
        """채팅 응답 포맷팅"""
        return {
            "response": response.strip(),
            "intent": intent.value,
            "confidence": round(confidence, 2),
            "processing_time": round(processing_time, 2),
            "model_used": model_used,
            "timestamp": ResponseFormatter._get_timestamp()
        }
    
    @staticmethod
    def format_story_response(story: str, title: Optional[str], genre: str, 
                            word_count: int, processing_time: float) -> Dict[str, Any]:
        """스토리 응답 포맷팅"""
        return {
            "story": story.strip(),
            "title": title,
            "genre": genre,
            "word_count": word_count,
            "processing_time": round(processing_time, 2),
            "timestamp": ResponseFormatter._get_timestamp(),
            "metadata": {
                "estimated_reading_time": ResponseFormatter._estimate_reading_time(word_count),
                "story_length": ResponseFormatter._categorize_length(word_count)
            }
        }
    
    @staticmethod
    def format_code_response(code: str, language: str, explanation: Optional[str],
                           complexity: str, processing_time: float) -> Dict[str, Any]:
        """코드 응답 포맷팅"""
        return {
            "code": code.strip(),
            "language": language,
            "explanation": explanation.strip() if explanation else None,
            "complexity": complexity,
            "processing_time": round(processing_time, 2),
            "timestamp": ResponseFormatter._get_timestamp(),
            "metadata": {
                "lines_of_code": len(code.strip().split('\n')),
                "has_comments": ResponseFormatter._has_comments(code, language),
                "estimated_functions": ResponseFormatter._count_functions(code, language)
            }
        }
    
    @staticmethod
    def format_error_response(error: str, detail: Optional[str] = None, 
                            error_code: Optional[str] = None) -> Dict[str, Any]:
        """에러 응답 포맷팅"""
        return {
            "error": error,
            "detail": detail,
            "error_code": error_code,
            "timestamp": ResponseFormatter._get_timestamp(),
            "status": "error"
        }
    
    @staticmethod
    def sanitize_response(response: str) -> str:
        """응답 텍스트 정제"""
        # 불필요한 공백 제거
        response = re.sub(r'\n{3,}', '\n\n', response)
        response = response.strip()
        
        # 특수 문자 이스케이프
        response = response.replace('\r', '')
        
        return response
    
    @staticmethod
    def _get_timestamp() -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    @staticmethod
    def _estimate_reading_time(word_count: int) -> str:
        """읽기 시간 추정 (한국어 기준 분당 200단어)"""
        minutes = max(1, word_count // 200)
        return f"약 {minutes}분"
    
    @staticmethod
    def _categorize_length(word_count: int) -> str:
        """스토리 길이 분류"""
        if word_count < 300:
            return "매우 짧음"
        elif word_count < 800:
            return "짧음"
        elif word_count < 1500:
            return "보통"
        elif word_count < 3000:
            return "김"
        else:
            return "매우 김"
    
    @staticmethod
    def _has_comments(code: str, language: str) -> bool:
        """코드에 주석이 포함되어 있는지 확인"""
        comment_patterns = {
            'python': [r'#', r'"""', r"'''"],
            'javascript': [r'//', r'/\*', r'\*/'],
            'java': [r'//', r'/\*', r'\*/'],
            'c++': [r'//', r'/\*', r'\*/'],
            'html': [r'<!--', r'-->'],
            'css': [r'/\*', r'\*/']
        }
        
        patterns = comment_patterns.get(language.lower(), [r'#', r'//', r'/\*'])
        
        for pattern in patterns:
            if re.search(pattern, code):
                return True
        return False
    
    @staticmethod
    def _count_functions(code: str, language: str) -> int:
        """함수/메서드 개수 추정"""
        function_patterns = {
            'python': [r'def\s+\w+', r'class\s+\w+'],
            'javascript': [r'function\s+\w+', r'\w+\s*=\s*function', r'\w+\s*=\s*\(.*\)\s*=>'],
            'java': [r'(public|private|protected)?\s*(static\s+)?\w+\s+\w+\s*\('],
            'c++': [r'\w+\s+\w+\s*\([^)]*\)\s*{']
        }
        
        patterns = function_patterns.get(language.lower(), [r'def\s+\w+', r'function\s+\w+'])
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, code, re.IGNORECASE))
        
        return count

# 전역 포맷터 인스턴스
formatter = ResponseFormatter()