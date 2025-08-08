#### 2. `api_keys.py`

#이제 API 키와 관련된 모든 코드는 이 파일에만 있을 거야.

#```python
# api_keys.py
# 모든 API 키를 로드하고 관리하는 역할을 담당합니다.

import os

# API 키 로딩 함수
def load_api_key_from_file(file_path: str) -> str:
    """지정된 파일에서 API 키를 로드합니다."""
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

# API 키 파일 경로 설정
GEMINI_API_KEY_FILE = os.path.join("API", "gemini_api_key.txt")
OPENROUTER_API_KEY_FILE = os.path.join("API", "openrouter_api_key.txt")

# API 키 로드
GOOGLE_API_KEY = load_api_key_from_file(GEMINI_API_KEY_FILE)
OPENROUTER_API_KEY = load_api_key_from_file(OPENROUTER_API_KEY_FILE)

if not GOOGLE_API_KEY:
    print("경고: Gemini API 키가 로드되지 않았습니다.")
if not OPENROUTER_API_KEY:
    print("경고: OpenRouter API 키가 로드되지 않았습니다.")
