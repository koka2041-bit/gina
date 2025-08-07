# services/gemini_service.py
import google.generativeai as genai
from typing import Optional, Dict, Any
import time
import re
from config import config
from models.request_models import StoryRequest, StoryResponse

class GeminiService:
    """Gemini API를 사용한 스토리 생성 서비스"""
    
    def __init__(self):
        self.api_key = config.get_gemini_api_key()
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Gemini 모델 초기화"""
        if not self.api_key:
            print("⚠️ Gemini API 키가 설정되지 않았습니다.")
            return
            
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            print("✅ Gemini 모델이 성공적으로 초기화되었습니다.")
        except Exception as e:
            print(f"❌ Gemini 모델 초기화 실패: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """서비스 사용 가능 여부 확인"""
        return self.model is not None
    
    def generate_story(self, request: StoryRequest) -> StoryResponse:
        """스토리 생성"""
        if not self.is_available():
            raise Exception("Gemini 서비스를 사용할 수 없습니다. API 키를 확인해주세요.")
        
        start_time = time.time()
        
        try:
            # 프롬프트 구성
            prompt = self._build_story_prompt(request)
            
            # 생성 설정
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
                top_p=0.8,
                top_k=40
            )
            
            # 스토리 생성
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # 응답 처리
            story_text = response.text
            title = self._extract_title(story_text)
            word_count = len(story_text.split())
            processing_time = time.time() - start_time
            
            return StoryResponse(
                story=story_text,
                title=title,
                genre=request.genre,
                word_count=word_count,
                processing_time=processing_time
            )
            
        except Exception as e:
            raise Exception(f"스토리 생성 중 오류가 발생했습니다: {str(e)}")
    
    def generate_chat_response(self, message: str, history: list = None) -> str:
        """일반 채팅 응답 생성"""
        if not self.is_available():
            raise Exception("Gemini 서비스를 사용할 수 없습니다.")
        
        try:
            # 대화 히스토리 포함한 프롬프트 구성
            if history:
                context = "\n".join([f"사용자: {h.get('user', '')}\n어시스턴트: {h.get('assistant', '')}" for h in history[-5:]])
                full_prompt = f"이전 대화:\n{context}\n\n현재 질문: {message}\n\n친근하고 도움이 되는 답변을 해주세요:"
            else:
                full_prompt = f"질문: {message}\n\n친근하고 도움이 되는 답변을 해주세요:"
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1000,
                top_p=0.8
            )
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"채팅 응답 생성 중 오류: {str(e)}")
    
    def _build_story_prompt(self, request: StoryRequest) -> str:
        """스토리 생성 프롬프트 구성"""
        length_guide = {
            "short": "300-500단어의 짧은",
            "medium": "800-1200단어의 중간 길이",
            "long": "1500-2000단어의 긴"
        }
        
        style_guide = {
            "narrative": "서술적이고 묘사가 풍부한",
            "dialogue": "대화 중심의 생동감 있는", 
            "poetic": "시적이고 운율감 있는",
            "simple": "간단하고 명확한"
        }
        
        length_desc = length_guide.get(request.length, "적당한 길이의")
        style_desc = style_guide.get(request.style, "흥미진진한")
        
        prompt = f"""
다음 조건에 맞는 {request.genre} 장르의 {length_desc} 스토리를 {style_desc} 스타일로 작성해주세요:

요청: {request.prompt}

작성 가이드:
1. 매력적인 제목을 포함해주세요
2. 흥미로운 등장인물과 갈등을 만들어주세요
3. 생생한 묘사와 감정을 담아주세요
4. 만족스러운 결말을 제공해주세요
5. 한국어로 작성해주세요

제목은 "제목: [제목명]" 형식으로 시작하고, 그 다음 줄부터 본문을 작성해주세요.
"""
        
        return prompt.strip()
    
    def _extract_title(self, story_text: str) -> Optional[str]:
        """스토리 텍스트에서 제목 추출"""
        try:
            # "제목:" 패턴으로 제목 찾기
            title_match = re.search(r'제목:\s*(.+)', story_text)
            if title_match:
                return title_match.group(1).strip()
            
            # 첫 줄이 제목일 가능성 체크
            first_line = story_text.split('\n')[0].strip()
            if len(first_line) < 50 and not first_line.endswith('.'):
                return first_line
                
            return None
            
        except Exception:
            return None

# 전역 서비스 인스턴스
gemini_service = GeminiService()