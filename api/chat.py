# api/chat.py - 채팅 관련 API 엔드포인트
from fastapi import APIRouter, HTTPException
import uuid
from models.request_models import ChatRequest
from services.gemini_service import GeminiStoryService
from services.openrouter_service import OpenRouterCodeService
from utils.intent_classifier import intent_classifier
from config import config

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat_with_zia(request: ChatRequest):
    """통합 채팅 엔드포인트 - 의도에 따라 적절한 서비스 호출"""
    user_message = request.message
    print(f"사용자 메시지 수신: {user_message}")
    
    try:
        # 의도 분류
        intent = intent_classifier.classify(user_message)
        print(f"의도 분류 결과: {intent}")
        
        if intent == "creative_writing":
            if not config.is_gemini_available:
                raise HTTPException(status_code=503, detail="Gemini API가 설정되지 않았습니다.")
            
            # 이야기 생성
            gemini_service = GeminiStoryService(config.GEMINI_API_KEY)
            
            # 이야기 길이 자동 결정
            story_type = "short_story"
            if "긴" in user_message or "장편" in user_message:
                story_type = "long_story"
            elif "중편" in user_message or "조금 긴" in user_message:
                story_type = "medium_story"
            
            response_text = await gemini_service.generate_story(user_message, story_type)
            api_tag = "[Gemini API - 향상된 스토리텔링]"
            final_response = f"{api_tag} {response_text}"
            return {"response": final_response}
        
        elif intent == "code_generation":
            if not config.is_openrouter_available:
                raise HTTPException(status_code=503, detail="OpenRouter API가 설정되지 않았습니다.")
            
            # 코드 생성
            openrouter_service = OpenRouterCodeService(config.OPENROUTER_API_KEY)
            code_result = await openrouter_service.generate_code(user_message)
            
            if code_result.get("error"):
                api_tag = "[OpenRouter API - 코드 생성 오류]"
                final_response = f"{api_tag} {code_result['error']}"
                return {"response": final_response}
            else:
                # HTML 파일 생성
                html_code = openrouter_service.format_html_file(code_result)
                
                return {
                    "immersive_type": "code",
                    "immersive_id": "generated_code_" + str(uuid.uuid4()),
                    "immersive_title": f"🤖 {code_result['title']} (OpenRouter 생성)",
                    "immersive_content": f"```html\n{html_code}\n```"
                }
        
        else:
            # 일반 대화
            api_tag = "[일반 대화]"
            response_text = f"안녕하세요! '{user_message}'라고 말씀하셨군요. 무엇을 도와드릴까요? '어린 여자아이 이야기 들려줘' 또는 '파이썬 코드 짜줘'라고 말씀해보세요!"
            final_response = f"{api_tag} {response_text}"
            return {"response": final_response}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"챗봇 응답 생성 중 예외 발생: {e}")
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류 발생: {e}")


@router.get("/health")
async def health_check():
    """서비스 상태 확인"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "apis": {
            "gemini": "available" if config.is_gemini_available else "not_configured",
            "openrouter": "available" if config.is_openrouter_available else "not_configured"
        }
    }