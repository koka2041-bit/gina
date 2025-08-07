# utils/response_formatter.py - 응답 포맷 유틸리티

def format_response(response: str, intent: str) -> str:
    """
    백엔드 응답을 프런트엔드에 맞게 포맷팅합니다.
    예시: 코드 블록, 마크다운 등
    """
    # 현재는 간단하게 응답을 그대로 반환합니다.
    # 향후 의도(intent)에 따라 다른 포맷팅을 추가할 수 있습니다.
    # 예를 들어, intent가 "code"인 경우 ```python ... ```로 감싸는 로직을 추가할 수 있습니다.

    return response

