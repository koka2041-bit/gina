# API/chat.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import time
import asyncio
from typing import Dict, Any

from models.request_models import ChatRequest, ChatResponse, IntentType
from utils.intent_classifier import classifier
from utils.response_formatter import formatter
from services.gemini_service import gemini_service
from services.openrouter_service import openrouter_service

router = APIRouter()

@router.post("/chat", response_model=Dict[str, Any])
async def chat_endpoint(request: ChatRequest):
    """
    통합 채팅 엔드포인트 - 자동 의도 분류
    
    사용자의 메시지를 분석해서 스토리 생성, 코드 생성, 일반 채팅 중 
    적절한 서비스로 라우팅합니다.
    """
    start_time = time.time()
    
    try:
        # 입력 검증
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="메시지가 비어있습니다.")
        
        # 의도 분류
        intent, confidence = classifier.classify_intent(request.message)
        
        # 응답 생성
        response_text = ""
        model_used = ""
        
        if intent == IntentType.STORY:
            # 스토리 생성 서비스로 라우팅
            if gemini_service.is_available():
                try:
                    # ChatRequest를 StoryRequest로 변환
                    from models.request_models import StoryRequest
                    story_request = StoryRequest(
                        prompt=request.message,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    )
                    
                    story_response = gemini_service.generate_story(story_request)
                    response_text = f"**{story_response.title or '생성된 이야기'}**\n\n{story_response.story}"
                    model_used = "Gemini Pro (Story)"
                    
                except Exception as e:
                    # Gemini 실패시 OpenRouter로 폴백
                    response_text = await openrouter_service.generate_chat_response(
                        f"다음 내용으로 재미있는 이야기를 써주세요: {request.message}",
                        request.conversation_history
                    )
                    model_used = "OpenRouter (Story Fallback)"
            else:
                # Gemini 불가능시 OpenRouter 사용
                response_text = await openrouter_service.generate_chat_response(
                    f"다음 내용으로 재미있는 이야기를 써주세요: {request.message}",
                    request.conversation_history
                )
                model_used = "OpenRouter (Story)"
        
        elif intent == IntentType.CODE:
            # 코드 생성 서비스로 라우팅
            if openrouter_service.is_available():
                try:
                    # ChatRequest를 CodeRequest로 변환
                    from models.request_models import CodeRequest
                    code_request = CodeRequest(
                        description=request.message,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    )
                    
                    code_response = await openrouter_service.generate_code(code_request)
                    response_text = f"**생성된 코드 ({code_response.language})**\n\n```{code_response.language}\n{code_response.code}\n```"
                    if code_response.explanation:
                        response_text += f"\n\n**설명:**\n{code_response.explanation}"
                    model_used = "OpenRouter (Code)"
                    
                except Exception as e:
                    # OpenRouter 실패시 Gemini로 폴백
                    if gemini_service.is_available():
                        response_text = gemini_service.generate_chat_response(
                            f"다음 요구사항에 맞는 코드를 작성해주세요: {request.message}",
                            request.conversation_history
                        )
                        model_used = "Gemini Pro (Code Fallback)"
                    else:
                        raise Exception("코드 생성 서비스를 사용할 수 없습니다.")
            else:
                # OpenRouter 불가능시 Gemini 사용
                if gemini_service.is_available():
                    response_text = gemini_service.generate_chat_response(
                        f"다음 요구사항에 맞는 코드를 작성해주세요: {request.message}",
                        request.conversation_history
                    )
                    model_used = "Gemini Pro (Code)"
                else:
                    raise Exception("코드 생성 서비스를 사용할 수 없습니다.")
        
        else:
            # 일반 채팅
            if gemini_service.is_available():
                try:
                    response_text = gemini_service.generate_chat_response(
                        request.message, 
                        request.conversation_history
                    )
                    model_used = "Gemini Pro (Chat)"
                except Exception as e:
                    # Gemini 실패시 OpenRouter로 폴백
                    response_text = await openrouter_service.generate_chat_response(
                        request.message,
                        request.conversation_history
                    )
                    model_used = "OpenRouter (Chat Fallback)"
            elif openrouter_service.is_available():
                response_text = await openrouter_service.generate_chat_response(
                    request.message,
                    request.conversation_history
                )
                model_used = "OpenRouter (Chat)"
            else:
                raise Exception("사용 가능한 AI 서비스가 없습니다. API 키를 확인해주세요.")
        
        # 응답 포맷팅
        processing_time = time.time() - start_time
        response_text = formatter.sanitize_response(response_text)
        
        formatted_response = formatter.format_chat_response(
            response=response_text,
            intent=intent,
            confidence=confidence,
            processing_time=processing_time,
            model_used=model_used
        )
        
        return JSONResponse(content=formatted_response)
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = formatter.format_error_response(
            error="채팅 응답 생성 실패",
            detail=str(e),
            error_code="CHAT_ERROR"
        )
        return JSONResponse(content=error_response, status_code=500)

@router.get("/chat/status")
async def chat_status():
    """채팅 서비스 상태 확인"""
    gemini_available = gemini_service.is_available()
    openrouter_available = openrouter_service.is_available()
    
    return {
        "services": {
            "gemini": {
                "available": gemini_available,
                "purpose": "Story generation & General chat"
            },
            "openrouter": {
                "available": openrouter_available, 
                "purpose": "Code generation & General chat"
            }
        },
        "overall_status": "healthy" if (gemini_available or openrouter_available) else "degraded",
        "intent_classifier": "active",
        "supported_intents": [intent.value for intent in IntentType]
    }