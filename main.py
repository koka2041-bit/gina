# main.py - 리팩토링된 메인 애플리케이션
from fastapi import FastAPI
import uvicorn
from config import config
from api.chat import router as chat_router
from api.story import router as story_router
from api.code import router as code_router

# FastAPI 애플리케이션 초기화
app = FastAPI(
    title="지아 챗봇 백엔드 (리팩토링 버전)",
    description="모듈화된 구조로 관리되는 챗봇, 이야기 생성, 코드 생성 시스템",
    version="3.0.0"
)

# 라우터 등록
app.include_router(chat_router)
app.include_router(story_router)
app.include_router(code_router)


@app.get("/")
async def read_root():
    """메인 페이지 - 서비스 상태 및 기능 안내"""
    return {
        "message": "🤖 지아 챗봇 백엔드 (리팩토링 버전) 실행 중",
        "version": "3.0.0",
        "features": {
            "chat": {
                "endpoint": "/api/chat",
                "description": "통합 채팅 (의도 자동 분류)",
                "available": True
            },
            "story_generation": {
                "endpoints": ["/api/story/generate", "/api/story/types"],
                "description": "Gemini API 기반 이야기 생성",
                "available": config.is_gemini_available
            },
            "code_generation": {
                "endpoints": ["/api/code/generate", "/api/code/models"],
                "description": "OpenRouter API 기반 코드 생성",
                "available": config.is_openrouter_available
            }
        },
        "health_check": "/api/health"
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 지아 챗봇 백엔드 서버 시작 (리팩토링 버전)")
    print("=" * 60)
    print(f"Gemini API: {'✅ 설정됨' if config.is_gemini_available else '❌ 미설정'}")
    print(f"OpenRouter API: {'✅ 설정됨' if config.is_openrouter_available else '❌ 미설정'}")
    print("=" * 60)
    print("📁 모듈 구조:")
    print("  ├── config.py (설정 관리)")
    print("  ├── models/ (요청 모델)")
    print("  ├── services/ (비즈니스 로직)")
    print("  ├── api/ (API 엔드포인트)")
    print("  └── utils/ (유틸리티)")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)