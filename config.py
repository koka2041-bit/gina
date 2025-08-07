# config.py - 설정 관리
import os
from typing import Optional


class Config:
    """애플리케이션 설정 관리"""
    
    def __init__(self):
        # API 키 파일 경로
        self.GEMINI_API_KEY_FILE = os.path.join("API", "gemini_api_key.txt")
        self.OPENROUTER_API_KEY_FILE = os.path.join("API", "openrouter_api_key.txt")
        
        # API 키 로드
        self.GEMINI_API_KEY = self._load_api_key(self.GEMINI_API_KEY_FILE, "Gemini")
        self.OPENROUTER_API_KEY = self._load_api_key(self.OPENROUTER_API_KEY_FILE, "OpenRouter")
    
    def _load_api_key(self, file_path: str, service_name: str) -> str:
        """지정된 파일에서 API 키를 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                key = f.readline().strip()
                if not key:
                    print(f"경고: '{file_path}' 파일에 {service_name} API 키가 비어 있습니다.")
                else:
                    print(f"✅ {service_name} API 키 로드 완료")
                return key
        except FileNotFoundError:
            print(f"❌ {service_name} API 키 파일 '{file_path}'를 찾을 수 없습니다.")
            return ""
        except Exception as e:
            print(f"❌ {service_name} API 키 파일 읽기 오류: {e}")
            return ""
    
    @property
    def is_gemini_available(self) -> bool:
        """Gemini API 사용 가능 여부"""
        return bool(self.GEMINI_API_KEY)
    
    @property
    def is_openrouter_available(self) -> bool:
        """OpenRouter API 사용 가능 여부"""
        return bool(self.OPENROUTER_API_KEY)


# 전역 설정 인스턴스
config = Config()