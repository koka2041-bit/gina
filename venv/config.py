# config.py
import os
from pathlib import Path
from typing import Optional

class Config:
    """앱 설정 관리 클래스"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.api_dir = self.base_dir / "API"
        
    def get_gemini_api_key(self) -> Optional[str]:
        """Gemini API 키 가져오기"""
        try:
            key_file = self.api_dir / "gemini_api_key.txt"
            if key_file.exists():
                return key_file.read_text().strip()
            
            # 환경변수에서도 확인
            return os.getenv("GEMINI_API_KEY")
        except Exception as e:
            print(f"Gemini API 키를 읽는 중 오류: {e}")
            return None
    
    def get_openrouter_api_key(self) -> Optional[str]:
        """OpenRouter API 키 가져오기"""
        try:
            key_file = self.api_dir / "openrouter_api_key.txt"
            if key_file.exists():
                return key_file.read_text().strip()
            
            # 환경변수에서도 확인
            return os.getenv("OPENROUTER_API_KEY")
        except Exception as e:
            print(f"OpenRouter API 키를 읽는 중 오류: {e}")
            return None
    
    def validate_api_keys(self) -> dict:
        """API 키들 유효성 검사"""
        gemini_key = self.get_gemini_api_key()
        openrouter_key = self.get_openrouter_api_key()
        
        return {
            "gemini": {
                "available": gemini_key is not None and len(gemini_key) > 0,
                "key": gemini_key[:10] + "..." if gemini_key else None
            },
            "openrouter": {
                "available": openrouter_key is not None and len(openrouter_key) > 0,
                "key": openrouter_key[:10] + "..." if openrouter_key else None
            }
        }

# 전역 설정 인스턴스
config = Config()