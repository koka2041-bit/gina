# simple_main.py - 임시 해결책 (모델 없이 작동)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import random
import os

# 간단한 대화 패턴들
SIMPLE_RESPONSES = {
    "greetings": [
        "안녕 담! 나는 지아야 😊",
        "담! 오늘 기분은 어때?",
        "안녕하세요! 지아예요~"
    ],
    "questions": [
        "흥미로운 질문이네! 더 자세히 말해줄래?",
        "그건 정말 좋은 질문이야! 어떻게 생각해?",
        "오, 그것에 대해 이야기해보자!"
    ],
    "default": [
        "담의 말이 정말 흥미로워! 더 말해줄래?",
        "그렇게 생각하는구나! 나도 그런 것 같아.",
        "정말? 더 자세히 들려줘!",
        "와, 그런 이야기구나! 재밌어!",
        "담이 말하는 걸 들으니까 기분이 좋아져!"
    ],
    "story_requests": [
        "좋아! 이야기를 만들어볼게!\n\n한 작은 마을에 특별한 소녀가 살고 있었어. 그 소녀는 매일 같은 길을 걸었지만, 언제나 새로운 것을 발견했어. 어느 날, 그녀는...\n\n(아직 간단한 버전이야. 더 멋진 이야기는 모델이 로딩되면 들려줄게!)",
        "이야기 타임! 📖\n\n옛날 옛적에, 구름 위에 살고 있는 고양이가 있었어. 이 고양이는 매일 밤 별들과 이야기를 나누었는데...\n\n(전체 모델이 로딩되면 더 긴 이야기를 만들어줄게!)"
    ],
    "code_requests": [
        "코딩 도움이 필요하구나! 간단한 예시를 만들어볼게:\n\n```python\nprint('안녕, 담!')\nname = input('이름을 입력하세요: ')\nprint(f'반가워, {name}!')\n```\n\n더 복잡한 코드는 모델이 완전히 로딩되면 만들어줄게!",
        "프로그래밍! 좋아해! 간단한 웹페이지 만들기:\n\n```html\n<!DOCTYPE html>\n<html>\n<head><title>담의 페이지</title></head>\n<body>\n<h1>안녕하세요!</h1>\n<p>지아가 만든 간단한 페이지예요!</p>\n</body>\n</html>\n```\n\n전체 기능은 모델 로딩 후에 사용할 수 있어!"
    ]
}

app = FastAPI(
    title="지아 챗봇 (간단 버전)",
    description="모델 로딩 중 사용하는 임시 버전",
    version="0.5.0 Simple"
)

class ChatRequest(BaseModel):
    message: str

def get_simple_response(message: str) -> str:
    """간단한 패턴 매칭으로 응답 생성"""
    message_lower = message.lower()
    
    # 인사 패턴
    greet_keywords = ["안녕", "hello", "hi", "하이", "헬로"]
    if any(keyword in message_lower for keyword in greet_keywords):
        return random.choice(SIMPLE_RESPONSES["greetings"])
    
    # 이야기/소설 요청
    story_keywords = ["이야기", "소설", "스토리", "story", "tale", "써줘", "만들어"]
    if any(keyword in message_lower for keyword in story_keywords):
        return random.choice(SIMPLE_RESPONSES["story_requests"])
    
    # 코드 요청
    code_keywords = ["코드", "프로그램", "웹사이트", "html", "python", "javascript", "만들어줘"]
    if any(keyword in message_lower for keyword in code_keywords):
        return random.choice(SIMPLE_RESPONSES["code_requests"])
    
    # 질문 패턴
    question_keywords = ["뭐", "어떻게", "왜", "언제", "어디서", "누가", "?", "？"]
    if any(keyword in message_lower for keyword in question_keywords):
        return random.choice(SIMPLE_RESPONSES["questions"])
    
    # 기본 응답
    return random.choice(SIMPLE_RESPONSES["default"])

@app.get("/")
def read_root():
    return {
        "message": "🤖 지아 챗봇 (간단 버전)",
        "version": "0.5.0 Simple", 
        "status": "모델 없이 기본 기능으로 실행 중",
        "note": "MiniCPM-V 모델이 로딩되면 완전한 기능을 사용할 수 있습니다."
    }

@app.post("/chat") 
def chat(request: ChatRequest):
    """간단한 패턴 매칭 기반 채팅"""
    user_message = request.message
    
    try:
        response = get_simple_response(user_message)
        return {"response": f"[간단 모드]\n\n{response}"}
    except Exception as e:
        return {"response": f"미안해! 간단 모드에서 오류가 생겼어: {str(e)}"}

@app.post("/chat/image")
def chat_image_simple(request: dict):
    """이미지 분석 (간단 버전)"""
    message = request.get("message", "")
    return {
        "response": f"[간단 모드]\n\n이미지를 봤어! '{message}'에 대한 질문이구나. 지금은 간단 모드라서 이미지를 정확히 분석할 수는 없지만, 곧 전체 모델이 로딩되면 제대로 분석해줄게! 📸"
    }

@app.get("/model-status")
def model_status_simple():
    """간단 버전 상태"""
    return {
        "minicpm_model": {
            "loaded": False,
            "name": "Simple Pattern Matching",
            "features": ["basic_chat", "pattern_responses"]
        },
        "memory_system": {"loaded": False},
        "mode": "simple_fallback",
        "note": "이것은 모델 로딩 문제를 우회하는 간단한 버전입니다."
    }

@app.post("/reset_memory")
def reset_simple():
    return {"message": "간단 모드에서는 메모리 기능이 없습니다."}

@app.get("/stats")
def stats_simple():
    return {
        "mode": "simple",
        "total_messages": "추적 안함",
        "note": "간단 모드에서는 통계를 수집하지 않습니다."
    }

if __name__ == "__main__":
    print("🤖 지아 챗봇 간단 버전 시작")
    print("=" * 50)
    print("⚠️ 이것은 모델 로딩 문제를 우회하는 임시 버전입니다.")
    print("✅ 기본적인 채팅은 가능합니다.")
    print("=" * 50)
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8001, reload=False)