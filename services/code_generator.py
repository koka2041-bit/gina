import httpx
import json
import asyncio
import re
import os
from typing import Dict, List, Any, Optional


class OpenRouterCodeGenerator:
    """
    OpenRouter API를 활용한 코드 생성기 클래스.
    사용자 요청에 따라 코드 계획을 세우고, 각 부분을 순차적으로 생성합니다.
    """

    def __init__(self, api_key: str, model_name: str = "qwen/qwen3-coder"):
        """
        OpenRouterCodeGenerator의 생성자.
        :param api_key: OpenRouter API 키
        :param model_name: 사용할 모델 이름 (기본값: "qwen/qwen3-coder")
        """
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def make_api_request(self, messages: List[Dict], max_tokens: int = 4000,
                               temperature: float = 0.5) -> str:
        """
        OpenRouter API 요청을 실행하고 응답을 반환합니다.

        :param messages: 모델에 전달할 메시지 리스트.
        :param max_tokens: 생성할 최대 토큰 수.
        :param temperature: 응답의 무작위성을 제어하는 값.
        :return: 모델의 응답 텍스트. 실패 시 오류 메시지를 반환.
        """
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
        except httpx.HTTPStatusError as http_err:
            print(f"[HTTP 오류] 상태코드: {http_err.response.status_code}, 본문: {http_err.response.text}")
            return f"[OpenRouter API 오류: {http_err.response.text}]"
        except Exception as e:
            print(f"[기타 오류] {e}")
            return f"[OpenRouter API 오류: {str(e)}]"

    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        응답 텍스트에서 JSON 객체를 추출하고 파싱합니다.

        :param text: 모델의 응답 텍스트.
        :return: 파싱된 JSON 딕셔너리 또는 None.
        """
        try:
            # 첫 '{'와 마지막 '}'를 찾아 그 사이의 내용을 JSON으로 파싱 시도
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and start < end:
                json_string = text[start:end + 1]
                return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"[JSON 파싱 오류] {e}")
        return None

    def extract_code_block(self, text: str, language: str) -> str:
        """
        응답 텍스트에서 특정 언어의 코드 블록만 추출합니다.

        :param text: 모델의 응답 텍스트.
        :param language: 추출할 코드의 언어 (예: 'html', 'css', 'javascript').
        :return: 코드 블록 내용 또는 원본 텍스트.
        """
        pattern = rf'```(?:{language.lower()})?\s*(.*?)\s*```'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else text.strip()

    def build_context(self, previous_code: Dict[str, str]) -> str:
        """
        이전 단계에서 생성된 코드를 현재 단계의 컨텍스트로 사용하기 위해 포맷팅합니다.

        :param previous_code: HTML, CSS, JS 코드를 담고 있는 딕셔너리.
        :return: 프롬프트에 추가할 컨텍스트 문자열.
        """
        context = ""
        if previous_code.get("html"):
            context += f"\n\n[HTML 코드 참고]\n```html\n{previous_code['html']}\n```"
        if previous_code.get("css"):
            context += f"\n\n[CSS 코드 참고]\n```css\n{previous_code['css']}\n```"
        if previous_code.get("js"):
            context += f"\n\n[JavaScript 코드 참고]\n```javascript\n{previous_code['js']}\n```"
        return context

    async def create_code_plan(self, user_request: str, jia_persona: str) -> Optional[Dict[str, Any]]:
        """
        사용자 요청에 따라 상세한 코드 계획을 생성합니다.

        :param user_request: 사용자의 원본 요청.
        :param jia_persona: 지아의 페르소나.
        :return: 코드 계획을 담은 딕셔너리 또는 None.
        """
        prompt = f"""
{jia_persona} 너는 친절하고 꼼꼼한 소프트웨어 개발자야.
다음 요청을 HTML, CSS, JavaScript로 이루어진 웹 애플리케이션으로 만들기 위한 상세한 구현 계획을 세워줘.

요청: {user_request}

응답은 다음 JSON 형식으로 작성해줘. HTML, CSS, JS 각 부분에 대해 상세한 구현 내용을 설명해야 해.
```json
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
```
"""
        messages = [{"role": "user", "content": prompt}]
        print("=== 코드 계획 생성 중 (OpenRouter) ===")
        plan_text = await self.make_api_request(messages, max_tokens=2000, temperature=0.3)
        plan_json = self.extract_json(plan_text)
        if not plan_json:
            print("[계획 생성 실패] 응답 본문:", plan_text)
        return plan_json

    async def generate_code_segment(self, plan_step: Dict[str, Any], previous_code: Dict[str, str],
                                    jia_persona: str) -> str:
        """
        계획에 따라 개별 코드 부분을 작성합니다.

        :param plan_step: 코드 계획의 한 단계.
        :param previous_code: 이전에 생성된 코드.
        :param jia_persona: 지아의 페르소나.
        :return: 생성된 코드 블록 문자열.
        """
        language = plan_step.get("language")
        instructions = plan_step.get("instructions")
        step_name = plan_step.get("step_name")
        title = previous_code.get("title", "코드 생성")

        context_message = self.build_context(previous_code)

        prompt = f"""
{jia_persona} 너는 "{title}" 애플리케이션을 만드는 전문 개발자야.
다음 지침에 따라 {language} 코드를 작성해줘.

계획: {step_name} - {instructions}
{context_message}

작성 지침:

- 다른 설명 없이 오직 코드만 제공하고, 코드 블록({language})으로 감싸줘.
- 지침에 충실하게, 완전하고 독립적으로 실행 가능하게 작성해줘.
- 각 기능에 주석을 달아서 설명해줘.
- 필요한 <script>나 <style> 태그는 코드에 포함시켜줘.
"""
        messages = [{"role": "user", "content": prompt}]
        print(f"=== {step_name} ({language}) 코드 생성 중 (OpenRouter) ===")

        code_content = await self.make_api_request(messages, max_tokens=3000)
        await asyncio.sleep(1)
        return self.extract_code_block(code_content, language)


async def generate_enhanced_code(user_prompt: str, jia_persona: str, api_key: str) -> Dict[str, Any]:
    """
    사용자 요청에 따라 향상된 코드 생성 함수

    :param user_prompt: 사용자의 코드 생성 요청.
    :param jia_persona: 지아의 페르소나.
    :param api_key: OpenRouter API 키.
    :return: 생성된 코드를 담은 딕셔너리 또는 오류 메시지.
    """
    if not api_key:
        return {"error": "OpenRouter API 키가 설정되지 않았습니다. 'API/openrouter_api_key.txt' 파일을 확인해주세요."}

    generator = OpenRouterCodeGenerator(api_key)
    try:
        print("=== 향상된 코드 생성 시작 (OpenRouter) ===")
        code_plan = await generator.create_code_plan(user_prompt, jia_persona)

        if not code_plan or not code_plan.get("plan"):
            return {"error": "코드 계획을 생성하지 못했습니다. 더 구체적인 요청을 해주세요."}

        generated_code = {
            "title": code_plan.get("title", "제목 없는 코드"),
            "description": code_plan.get("description", "설명 없음"),
            "html": "",
            "css": "",
            "js": ""
        }

        for step in code_plan["plan"]:
            language = step["language"].lower()
            try:
                code = await generator.generate_code_segment(step, generated_code, jia_persona)
                if language == "html":
                    generated_code["html"] = code
                elif language == "css":
                    generated_code["css"] = code
                elif language == "javascript":
                    generated_code["js"] = code
                print(f"단계 {step['step_id']}: {step['step_name']} 완료")
            except Exception as e:
                print(f"{language.upper()} 코드 생성 실패: {e}")
                generated_code[language] = f"// [{language.upper()} 코드 생성 실패: {str(e)}]"

        print("=== 코드 생성 완료 (OpenRouter) ===")
        return generated_code

    except Exception as e:
        print(f"코드 생성 중 오류: {e}")
        return {"error": f"코드 생성 중 오류가 발생했습니다: {str(e)}"}
