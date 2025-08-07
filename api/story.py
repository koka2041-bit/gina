# api/story.py - 이야기 생성 관련 API 엔드포인트
from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.request_models import StoryRequest
from services.gemini_service import GeminiStoryService
from config import config

router = APIRouter(prefix="/api/story", tags=["story"])


@router.post("/generate")
async def generate_custom_story(request: StoryRequest):
    """사용자 지정 이야기 생성"""
    if not config.is_gemini_available:
        raise HTTPException(status_code=503, detail="Gemini API가 설정되지 않았습니다.")
    
    try:
        gemini_service = GeminiStoryService(config.GEMINI_API_KEY)
        story_content = await gemini_service.generate_story(
            request.message,
            request.story_type
        )
        
        return {
            "title": "생성된 이야기",
            "content": story_content,
            "type": request.story_type,
            "word_count": len(story_content.replace('\n', '')),
            "generation_time": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이야기 생성 중 오류: {e}")


@router.get("/types")
async def get_story_types():
    """지원되는 이야기 타입 목록"""
    if not config.is_gemini_available:
        raise HTTPException(status_code=503, detail="Gemini API가 설정되지 않았습니다.")
    
    # 임시 서비스 인스턴스로 설정 정보 가져오기
    gemini_service = GeminiStoryService(config.GEMINI_API_KEY)
    
    return {
        "available_types": list(gemini_service.length_configs.keys()),
        "configurations": gemini_service.length_configs
    }