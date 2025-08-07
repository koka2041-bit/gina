# services/openrouter_service.py - OpenRouter API 코드 생성 서비스
import httpx
import asyncio
import json
import re
from typing import Dict, List


class OpenRouterCodeService:
    """OpenRouter API를 활용한 코드 생성 서비스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_name = "qwen/qwen-2.5-coder-32b-instruct"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_api_request(self, messages: List[Dict], max_tokens: int = 4000, temperature: float = 0.5) -> str:
        """OpenRouter API 요청 실행"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(self.base_url, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                if result and result.get("choices"):
                    return result["choices"][0]["message"]["content"]
                return ""
        except Exception as e:
            print(f"OpenRouter API 요청 오류: {e}")
            return f"[OpenRouter API 오류: {str(e)}]"
    
    async def create_code_plan(self, user_request: str) -> Dict:
        """코드 생성 계획 수립"""
        plan_prompt = f"""
너는 소프트웨어 개발자야. 다음 요청을 HTML, CSS, JavaScript로 이루어진 웹 애플리케이션으로 만들기 위한 상세한 구현 계획을 세워줘.

요청: {user_request}

다음 JSON 형식으로 응답해줘:
{{
    "title": "애플리케이션 제목",
    "description": "애플리케이션에 대한 한두 문장 요약",
    "plan": [
        {{
            "step_id": 1,
            "step_name": "HTML 구조 작성",
            "language": "HTML",
            "instructions": "애플리케이션의 기본 구조를 만드는 방법을 설명해줘."
        }},
        {{
            "step_id": 2,
            "step_name": "CSS 스타일링",
            "language": "CSS",
            "instructions": "애플리케이션의 시각적인 디자인을 위한 CSS 스타일을 설명해줘."
        }},
        {{
            "step_id": 3,
            "step_name": "JavaScript 기능 구현",
            "language": "JavaScript",
            "instructions": "애플리케이션의 핵심 기능을 구현하는 방법을 설명해줘."
        }}
    ]
}}
"""
        
        messages = [{"role": "user", "content": plan_prompt}]
        print("=== 코드 계획 생성 중 (OpenRouter) ===")
        plan_text = await self._make_api_request(messages, max_tokens=2000, temperature=0.3)
        
        try:
            clean_text = plan_text.replace('```json', '').replace('```', '').strip()
            plan_json = json.loads(clean_text)
            return plan_json
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            # 기본 계획 반환
            return {
                "title": "간단한 웹 애플리케이션",
                "description": "사용자 요청에 따른 기본 웹 애플리케이션",
                "plan": [
                    {
                        "step_id": 1,
                        "step_name": "HTML 구조 작성",
                        "language": "HTML",
                        "instructions": "기본 HTML 구조와 필요한 요소들을 작성"
                    },
                    {
                        "step_id": 2,
                        "step_name": "CSS 스타일링", 
                        "language": "CSS",
                        "instructions": "시각적 디자인과 레이아웃 스타일링"
                    },
                    {
                        "step_id": 3,
                        "step_name": "JavaScript 기능 구현",
                        "language": "JavaScript",
                        "instructions": "핵심 기능과 인터랙션 구현"
                    }
                ]
            }
    
    async def generate_code_segment(self, plan_step: Dict, previous_code: Dict) -> str:
        """코드 세그먼트 생성"""
        language = plan_step.get("language", "HTML")
        instructions = plan_step.get("instructions", "")
        step_name = plan_step.get("step_name", "코드 작성")
        title = previous_code.get("title", "코드 생성")
        
        context_message = ""
        if previous_code.get("html"):
            context_message += f"\n\n**기존 HTML 코드:**\n```html\n{previous_code['html']}\n```"
        if previous_code.get("css"):
            context_message += f"\n\n**기존 CSS 코드:**\n```css\n{previous_code['css']}\n```"
        
        code_prompt = f"""
너는 {title} 애플리케이션을 만드는 전문 개발자야. 다음 지침에 따라 **{language}** 코드를 작성해줘.

**계획**: {step_name} - {instructions}
{context_message}

**작성 지침**:
1. 코드만 제공하고, 코드 블록(```{language.lower()} ... ```)으로 감싸줘.
2. 코드는 지침에 충실하게 작성하되, 완전하고 독립적으로 실행 가능하게 만들어줘.
3. 코드 내부에 상세한 주석을 달아서 각 기능이 무엇을 하는지 설명해줘.

코드를 작성해줘:
"""
        
        messages = [{"role": "user", "content": code_prompt}]
        print(f"=== {step_name} ({language}) 코드 생성 중 (OpenRouter) ===")
        
        code_content = await self._make_api_request(messages, max_tokens=3000)
        await asyncio.sleep(2)  # API 호출 간 지연
        
        # 코드 블록 추출
        return self._extract_code_block(code_content, language)
    
    def _extract_code_block(self, content: str, language: str) -> str:
        """코드 블록에서 실제 코드 추출"""
        language_lower = language.lower()
        patterns = [
            rf'```{re.escape(language_lower)}\n(.*?)\n```',
            r'```html\n(.*?)\n```',
            r'```css\n(.*?)\n```',
            r'```javascript\n(.*?)\n```',
            r'```js\n(.*?)\n```',
            r'```\n(.*?)\n```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 코드 블록이 없으면 전체 내용 반환 (단, API 오류 메시지 제외)
        if not content.startswith("[OpenRouter API 오류:"):
            return content.strip()
        
        return ""
    
    async def generate_code(self, user_prompt: str) -> Dict:
        """완전한 코드 생성"""
        try:
            print("=== 향상된 코드 생성 시작 (OpenRouter) ===")
            
            # 1단계: 코드 계획 수립
            code_plan = await self.create_code_plan(user_prompt)
            
            if not code_plan or not code_plan.get("plan"):
                return {"error": "코드 계획을 생성하지 못했습니다. 더 구체적인 요청을 해주세요."}
            
            # 2단계: 각 부분 순차 생성
            generated_code = {
                "title": code_plan.get("title", "제목 없는 코드"),
                "description": code_plan.get("description", "설명 없음"),
                "html": "",
                "css": "",
                "js": ""
            }
            
            for step in code_plan["plan"]:
                language = step.get("language", "").lower()
                if language == "html":
                    generated_code["html"] = await self.generate_code_segment(step, generated_code)
                elif language == "css":
                    generated_code["css"] = await self.generate_code_segment(step, generated_code)
                elif language in ["javascript", "js"]:
                    generated_code["js"] = await self.generate_code_segment(step, generated_code)
                
                print(f"단계 {step.get('step_id', '?')}: {step.get('step_name', '알 수 없음')} 완료")
            
            print("=== 코드 생성 완료 (OpenRouter) ===")
            
            # 빈 코드 섹션 체크
            if not any([generated_code["html"], generated_code["css"], generated_code["js"]]):
                return {"error": "코드 생성에 실패했습니다. API 응답을 확인해주세요."}
            
            return generated_code
            
        except Exception as e:
            print(f"코드 생성 중 오류: {e}")
            return {"error": f"코드 생성 중 오류가 발생했습니다: {str(e)}"}
    
    def format_html_file(self, code_data: Dict) -> str:
        """완전한 HTML 파일 생성"""
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{code_data['title']}</title>
    <style>
{code_data['css']}
    </style>
</head>
<body>
{code_data['html']}
    <script>
{code_data['js']}
    </script>
</body>
</html>"""