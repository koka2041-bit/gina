# models/request_models.py - 요청 모델 정의
from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """기본 채팅 요청"""
    message: str


class StoryRequest(BaseModel):
    """이야기 생성 요청"""
    message: str
    story_type: str = "short_story"  # short_story, medium_story, long_story
    writing_style: str = "modern"
    target_length: Optional[int] = None


class CodeRequest(BaseModel):
    """코드 생성 요청"""
    message: str
    language: Optional[str] = "web"  # web, python, javascript 등
    complexity: Optional[str] = "simple"  # simple, intermediate, advanced