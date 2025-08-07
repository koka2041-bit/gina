# models/request_models.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class ChatRequest(BaseModel):
    """통합 채팅 요청 모델"""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class StoryRequest(BaseModel):
    """스토리 생성 요청 모델"""
    prompt: str
    genre: Optional[str] = "fantasy"
    length: Optional[str] = "short"  # short, medium, long
    style: Optional[str] = "narrative"
    max_tokens: Optional[int] = 1500
    temperature: Optional[float] = 0.8

class CodeRequest(BaseModel):
    """코드 생성 요청 모델"""
    description: str
    language: Optional[str] = "python"
    complexity: Optional[str] = "beginner"  # beginner, intermediate, advanced
    include_comments: Optional[bool] = True
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.3

class IntentType(str, Enum):
    """의도 분류 타입"""
    STORY = "story"
    CODE = "code"
    CHAT = "chat"
    UNKNOWN = "unknown"

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str
    intent: IntentType
    confidence: float
    processing_time: float
    model_used: str

class StoryResponse(BaseModel):
    """스토리 응답 모델"""
    story: str
    title: Optional[str] = None
    genre: str
    word_count: int
    processing_time: float

class CodeResponse(BaseModel):
    """코드 응답 모델"""
    code: str
    language: str
    explanation: Optional[str] = None
    complexity: str
    processing_time: float

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None