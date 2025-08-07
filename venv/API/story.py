# API/story.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from models.request_models import StoryRequest, StoryResponse
from services.gemini_service import gemini_service
from utils.response_formatter import formatter

router = APIRouter()

@router.post("/story", response_model=Dict[str, Any])
async def generate_story(request: StoryRequest):
    """
    스토리 생성 엔드포인트
    
    Gemini API를 사용하여 창의적인 스토리를 생성합니다.
    """
    try:
        # 입력 검증
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="스토리 프롬프트가 비어있습니다.")
        
        # 서비스 가용성 확인
        if not gemini_service.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Gemini 서비스를 사용할 수 없습니다. API 키를 확인해주세요."
            )
        
        # 스토리 생성
        story_response = gemini_service.generate_story(request)
        
        # 응답 포맷팅
        formatted_response = formatter.format_story_response(
            story=story_response.story,
            title=story_response.title,
            genre=story_response.genre,
            word_count=story_response.word_count,
            processing_time=story_response.processing_time
        )
        
        return JSONResponse(content=formatted_response)
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = formatter.format_error_response(
            error="스토리 생성 실패",
            detail=str(e),
            error_code="STORY_GENERATION_ERROR"
        )
        return JSONResponse(content=error_response, status_code=500)

@router.get("/story/genres")
async def get_story_genres():
    """사용 가능한 스토리 장르 목록"""
    return {
        "genres": [
            {"value": "fantasy", "name": "판타지", "description": "마법과 모험이 가득한 환상적인 이야기"},
            {"value": "romance", "name": "로맨스", "description": "사랑과 감정에 집중한 따뜻한 이야기"},
            {"value": "mystery", "name": "미스터리", "description": "수수께끼와 추리가 핵심인 긴장감 있는 이야기"},
            {"value": "horror", "name": "공포", "description": "무서움과 긴장감을 주는 스릴러 이야기"},
            {"value": "scifi", "name": "SF", "description": "과학 기술과 미래를 다룬 상상력 넘치는 이야기"},
            {"value": "drama", "name": "드라마", "description": "인간의 감정과 관계를 깊이 있게 다룬 이야기"},
            {"value": "comedy", "name": "코미디", "description": "유머와 웃음이 가득한 재미있는 이야기"},
            {"value": "adventure", "name": "모험", "description": "여행과 모험으로 가득한 흥미진진한 이야기"}
        ]
    }

@router.get("/story/lengths")
async def get_story_lengths():
    """사용 가능한 스토리 길이 옵션"""
    return {
        "lengths": [
            {"value": "short", "name": "짧음", "description": "300-500단어, 5분 내외 읽기"},
            {"value": "medium", "name": "보통", "description": "800-1200단어, 10분 내외 읽기"},
            {"value": "long", "name": "김", "description": "1500-2000단어, 15분 이상 읽기"}
        ]
    }

@router.get("/story/styles")
async def get_story_styles():
    """사용 가능한 스토리 스타일 옵션"""
    return {
        "styles": [
            {"value": "narrative", "name": "서술형", "description": "묘사가 풍부한 전통적인 서술 방식"},
            {"value": "dialogue", "name": "대화형", "description": "등장인물 간의 대화 중심"},
            {"value": "poetic", "name": "시적", "description": "운율과 리듬감이 있는 문학적 표현"},
            {"value": "simple", "name": "간단함", "description": "명확하고 이해하기 쉬운 표현"}
        ]
    }

@router.post("/story/preview")
async def preview_story_settings(request: StoryRequest):
    """
    스토리 설정 미리보기
    
    실제 생성 전에 어떤 스타일의 스토리가 생성될지 미리 확인
    """
    try:
        # 설정 정보 반환
        preview_info = {
            "settings": {
                "genre": request.genre,
                "length": request.length,
                "style": request.style,
                "temperature": request.temperature
            },
            "estimated_output": {
                "word_count_range": {
                    "short": "300-500단어",
                    "medium": "800-1200단어", 
                    "long": "1500-2000단어"
                }.get(request.length, "적당한 길이"),
                "reading_time": {
                    "short": "약 3-5분",
                    "medium": "약 8-12분",
                    "long": "약 15-20분"
                }.get(request.length, "적당한 시간"),
                "creativity_level": "높음" if request.temperature > 0.7 else "보통" if request.temperature > 0.4 else "낮음"
            },
            "sample_prompt": f"{request.genre} 장르의 {request.length} 길이 스토리: {request.prompt[:100]}..."
        }
        
        return JSONResponse(content=preview_info)
        
    except Exception as e:
        error_response = formatter.format_error_response(
            error="스토리 설정 미리보기 실패",
            detail=str(e),
            error_code="STORY_PREVIEW_ERROR"
        )
        return JSONResponse(content=error_response, status_code=500)

@router.get("/story/status")
async def story_service_status():
    """스토리 생성 서비스 상태"""
    return {
        "service": "story_generation",
        "provider": "Gemini Pro",
        "available": gemini_service.is_available(),
        "supported_genres": 8,
        "supported_lengths": 3,
        "supported_styles": 4
    }