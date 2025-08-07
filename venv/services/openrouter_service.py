# services/openrouter_service.py
import httpx
import time
import json
from typing import Optional, Dict, Any
from config import config
from models.request_models import CodeRequest, CodeResponse

class OpenRouterService:
    """OpenRouter API를 사용한 코드 생성 서비스"""
    
    def __init__(self):
        self.api_key = config.get_openrouter_api_key()
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3-sonnet"  # 기본 모델
        self.headers = self._build_headers()
    
    def _build_code_prompt(self, request: CodeRequest) -> str:
        """코드 생성 프롬프트 구성"""
        complexity_guide = {
            "beginner": "초보자도 이해할 수 있는 간단하고 명확한",
            "intermediate": "중급 수준의 효율적이고 구조화된",
            "advanced": "고급 기술을 활용한 최적화된"
        }
        
        complexity_desc = complexity_guide.get(request.complexity, "적절한 수준의")
        comments_instruction = "상세한 주석을 포함해서" if request.include_comments else "주석 없이"
        
        prompt = f"""
다음 요구사항에 맞는 {request.language} 코드를 작성해주세요:

요구사항: {request.description}

조건:
- {complexity_desc} 코드로 작성
- {comments_instruction} 작성
- 실행 가능한 완전한 코드 제공
- 코드의 기능과 사용법에 대한 간단한 설명 포함

응답 형식:
```{request.language}
[코드 내용]
```

설명:
[코드에 대한 설명]
"""
        return prompt.strip()
    
    def _extract_code_and_explanation(self, response_text: str) -> tuple[str, str]:
        """응답에서 코드와 설명 분리"""
        try:
            import re
            
            # 코드 블록 추출
            code_pattern = r'```(?:\w+)?\n(.*?)\n```'
            code_match = re.search(code_pattern, response_text, re.DOTALL)
            
            if code_match:
                code = code_match.group(1).strip()
                # 설명은 코드 블록을 제외한 나머지 텍스트
                explanation = re.sub(code_pattern, '', response_text, flags=re.DOTALL).strip()
            else:
                # 코드 블록이 없으면 전체를 코드로 처리
                lines = response_text.strip().split('\n')
                # 설명으로 보이는 줄들 찾기
                explanation_lines = []
                code_lines = []
                
                in_explanation = True
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['def ', 'class ', 'import ', 'from ', '#!/', '<', '{']):
                        in_explanation = False
                    
                    if in_explanation and not line.strip().startswith(('#', '//', '/*')):
                        explanation_lines.append(line)
                    else:
                        code_lines.append(line)
                
                code = '\n'.join(code_lines).strip()
                explanation = '\n'.join(explanation_lines).strip()
            
            return code if code else response_text, explanation
            
        except Exception:
            return response_text, "코드에 대한 설명을 생성할 수 없습니다."
    
    async def generate_chat_response(self, message: str, history: list = None) -> str:
        """일반 채팅 응답 생성 (OpenRouter 사용)"""
        if not self.is_available():
            raise Exception("OpenRouter 서비스를 사용할 수 없습니다.")
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "당신은 친근하고 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 유용한 답변을 제공해주세요."
                }
            ]
            
            # 대화 히스토리 추가 (최근 5개만)
            if history:
                for h in history[-5:]:
                    if 'user' in h:
                        messages.append({"role": "user", "content": h['user']})
                    if 'assistant' in h:
                        messages.append({"role": "assistant", "content": h['assistant']})
            
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            if "choices" not in result or not result["choices"]:
                raise Exception("OpenRouter API에서 응답을 받지 못했습니다.")
            
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise Exception(f"채팅 응답 생성 중 오류: {str(e)}")

# 전역 서비스 인스턴스
openrouter_service = OpenRouterService()headers(self) -> Dict[str, str]:
        """API 요청 헤더 구성"""
        if not self.api_key:
            return {}
            
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",  # 선택사항
            "X-Title": "GINA Code Generator"  # 선택사항
        }
    
    def is_available(self) -> bool:
        """서비스 사용 가능 여부 확인"""
        return bool(self.api_key and self.headers)
    
    async def generate_code(self, request: CodeRequest) -> CodeResponse:
        """코드 생성"""
        if not self.is_available():
            raise Exception("OpenRouter 서비스를 사용할 수 없습니다. API 키를 확인해주세요.")
        
        start_time = time.time()
        
        try:
            # 프롬프트 구성
            prompt = self._build_code_prompt(request)
            
            # API 요청 데이터
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "당신은 전문적인 프로그래머입니다. 사용자의 요청에 따라 깔끔하고 효율적인 코드를 작성해주세요."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": 0.9
            }
            
            # API 호출
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            # 응답 처리
            if "choices" not in result or not result["choices"]:
                raise Exception("OpenRouter API에서 응답을 받지 못했습니다.")
            
            generated_text = result["choices"][0]["message"]["content"]
            code, explanation = self._extract_code_and_explanation(generated_text)
            processing_time = time.time() - start_time
            
            return CodeResponse(
                code=code,
                language=request.language,
                explanation=explanation,
                complexity=request.complexity,
                processing_time=processing_time
            )
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"OpenRouter API 오류 (HTTP {e.response.status_code}): {e.response.text}")
        except httpx.TimeoutException:
            raise Exception("OpenRouter API 요청 시간 초과")
        except Exception as e:
            raise Exception(f"코드 생성 중 오류가 발생했습니다: {str(e)}")
    
    def _build_