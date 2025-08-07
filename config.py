# config.py - 설정 및 API 키 관리

import os
from pydantic_settings import BaseSettings

# 현재 스크립트의 경로를 기준으로 BASE_DIR을 설정합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# API 키 파일을 읽어오는 함수
def load_api_key_from_file(file_path: str) -> str:
    """
    지정된 파일 경로에서 API 키를 불러옵니다.
    파일이 없거나 읽을 수 없으면 빈 문자열을 반환합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            key = f.readline().strip()
            if not key:
                print(f"경고: '{file_path}' 파일에 API 키가 비어 있습니다.")
            return key
    except FileNotFoundError:
        print(f"오류: API 키 파일 '{file_path}'를 찾을 수 없습니다.")
        return ""
    except Exception as e:
        print(f"오류: API 키 파일 '{file_path}'를 읽는 중 오류 발생: {e}")
        return ""


class Settings(BaseSettings):
    """
    애플리케이션의 모든 설정을 관리하는 클래스입니다.
    """
    # CORS 설정
    # Streamlit 앱이 실행되는 포트(8501)를 허용합니다.
    CORS_ORIGINS: list[str] = ["http://localhost:8501"]

    # --- API 키 설정 ---
    # API 키 파일 경로
    GEMINI_API_KEY_FILE: str = os.path.join(BASE_DIR, "API", "gemini_api_key.txt")
    OPENROUTER_API_KEY_FILE: str = os.path.join(BASE_DIR, "API", "openrouter_api_key.txt")

    # 실제 API 키
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    def load_api_keys(self):
        """
        초기화 시 API 키를 파일에서 불러옵니다.
        """
        self.GEMINI_API_KEY = load_api_key_from_file(self.GEMINI_API_KEY_FILE)
        self.OPENROUTER_API_KEY = load_api_key_from_file(self.OPENROUTER_API_KEY_FILE)

        if self.GEMINI_API_KEY:
            print("✅ Gemini API 키 로드 완료")
        if self.OPENROUTER_API_KEY:
            print("✅ OpenRouter API 키 로드 완료")


# Settings 클래스의 인스턴스를 생성하여 전역에서 사용할 수 있도록 합니다.
# 이 'settings' 객체가 main.py에서 'from config import settings'로 가져오는 대상입니다.
settings = Settings()
settings.load_api_keys()

