# api/code.py - 코드 생성 관련 API 엔드포인트
from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.request_models import CodeRequest, ChatRequest
from services.openrouter_service import OpenRouterCodeService
from config import config

router = APIRouter(prefix="/api/code", tags=["code"])


@router.post("/generate")
async def generate_custom_code(request: CodeRequest):
    """사용자 지정 코드 생성"""
    if not config.is_openrouter_available:
        raise HTTPException(status_code=503, detail="OpenRouter API가 설정되지 않았습니다.")
    
    try:
        openrouter_service = OpenRouterCodeService(config.OPENROUTER_API_KEY)
        code_result = await openrouter_service.generate_code(request.message)
        
        if code_result.get("error"):
            raise HTTPException(status_code=500, detail=code_result["error"])
        
        # HTML 파일 생성
        html_code = openrouter_service.format_html_file(code_result)
        
        return {
            "title": code_result['title'],
            "description": code_result['description'],
            "html_file": html_code,
            "separate_files": {
                "html": code_result['html'],
                "css": code_result['css'],
                "javascript": code_result['js']
            },
            "generation_time": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 생성 중 오류: {e}")


@router.post("/generate_simple")
async def generate_simple_code(request: ChatRequest):
    """간단한 코드 생성 (ChatRequest 호환)"""
    code_request = CodeRequest(message=request.message)
    return await generate_custom_code(code_request)


@router.get("/models")
async def get_available_models():
    """사용 가능한 코드 생성 모델 정보"""
    if not config.is_openrouter_available:
        raise HTTPException(status_code=503, detail="OpenRouter API가 설정되지 않았습니다.")
    
    return {
        "current_model": "qwen/qwen-2.5-coder-32b-instruct",
        "supported_languages": ["HTML", "CSS", "JavaScript"],
        "output_format": "웹 애플리케이션 (HTML + CSS + JS)",
        "complexity_levels": ["simple", "intermediate", "advanced"]
    }