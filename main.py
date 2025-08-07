# main.py - 앱 초기화 및 라우터 등록

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from API.chat import router as chat_router # 대문자 'API'로 수정
from API.story import router as story_router # 대문자 'API'로 수정
from API.code import router as code_router # 대문자 'API'로 수정
from config import settings # 설정 로드

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="지아 챗봇 백엔드",
    description="다양한 AI 모델을 활용한 챗봇 서비스 백엔드",
    version="1.0.0",
)

# CORS 미들웨어 설정
# 특정 출처(origins)에서만 접근을 허용하거나, 모든 출처를 허용할 수 있습니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # config.py에서 설정된 출처 사용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
# 각 엔드포인트 파일의 라우터를 앱에 포함시킵니다.
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(story_router, prefix="/story", tags=["story"])
app.include_router(code_router, prefix="/code", tags=["code"])

@app.get("/")
def read_root():
    """
    루트 경로에 대한 기본 응답을 제공합니다.
    """
    return {"message": "지아 챗봇 백엔드가 실행 중입니다!"}
