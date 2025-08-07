# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

# API 라우터들 임포트
from API.chat import router as chat_router
from API.story import router as story_router  
from API.code import router as code_router

# FastAPI 앱 생성
app = FastAPI(
    title="GINA - AI Assistant API",
    description="통합 AI 어시스턴트 API (스토리 생성, 코드 생성, 채팅)",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (필요한 경우)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# API 라우터 등록
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(story_router, prefix="/api", tags=["Story"])
app.include_router(code_router, prefix="/api", tags=["Code"])

# 루트 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>GINA - AI Assistant</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; }
                .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
                .method { color: #28a745; font-weight: bold; }
                .url { color: #007bff; font-family: monospace; }
                .description { color: #666; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 GINA - AI Assistant API</h1>
                <p>통합 AI 어시스턴트 서비스입니다. 스토리 생성, 코드 생성, 일반 채팅을 제공합니다.</p>
                
                <h2>📡 Available Endpoints</h2>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <span class="url">/api/chat</span></div>
                    <div class="description">통합 채팅 (자동 의도 분류)</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <span class="url">/api/story</span></div>
                    <div class="description">스토리 생성 (Gemini API)</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <span class="url">/api/code</span></div>
                    <div class="description">코드 생성 (OpenRouter API)</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="url">/docs</span></div>
                    <div class="description">API 문서 (Swagger UI)</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="url">/redoc</span></div>
                    <div class="description">API 문서 (ReDoc)</div>
                </div>
            </div>
        </body>
    </html>
    """

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)