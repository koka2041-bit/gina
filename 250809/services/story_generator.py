# services/story_generator.py

import httpx
import json
import asyncio
import os
import re
from typing import Dict, List, Any, Optional


# 💬 프롬프트 템플릿 생성기
class StoryPromptBuilder:
    @staticmethod
    def build_outline_prompt(user_request: str, config: Dict[str, Any], jia_persona: str) -> str:
        """
        이야기 개요 생성을 위한 단일 프롬프트 문자열을 생성합니다.
        페르소나와 사용자 요청을 하나의 메시지로 결합합니다.
        """
        return f"""
{jia_persona} 너는 전문 동화 작가야. 어린이를 위한 이야기를 써줘.

다음 요청을 바탕으로 {config['segments']}부분으로 구성된 이야기 개요를 만들어주세요.

요청: {user_request}

다음 형식으로 작성해주세요:

이야기 제목: (매력적인 제목)
주인공: (이름, 나이, 특징)
배경: (시간과 장소)
핵심 갈등: (주인공이 해결해야 할 문제)

{config['segments']}부분 구성:
1부: (시작 - 30자 이내 요약)
2부: (전개 - 30자 이내 요약)
...
{config['segments']}부: (결말 - 30자 이내 요약)

각 부분은 명확하고 연결성 있게 구성해주세요.
"""

    @staticmethod
    def build_segment_prompt(segment_index: int, segment_outline: str,
                             story_plan: Dict[str, Any], previous_content: str,
                             target_words: int, jia_persona: str) -> str:
        """
        이야기 부분 작성을 위한 단일 프롬프트 문자열을 생성합니다.
        페르소나와 이야기 정보를 하나의 메시지로 결합합니다.
        """
        context = f"\n\n이전 이야기:\n{previous_content[-1000:]}" if previous_content else ""
        return f"""
{jia_persona} 너는 어린이를 위한 따뜻하고 감동적인 이야기를 쓰는 작가야.

이야기 정보:

제목: {story_plan.get('title', '')}
주인공: {story_plan.get('protagonist', '')}
배경: {story_plan.get('setting', '')}
갈등: {story_plan.get('conflict', '')}
{context}

이번 부분 내용: {segment_outline}

작성 지침:

- 약 {target_words}자 분량
- 어린이가 읽기 쉬운 따뜻한 문체
- 생생한 장면과 감정 표현
- 교육적이고 긍정적인 메시지 포함
- 자연스럽게 연결되도록 진행
"""


# 📘 이야기 생성기 클래스
class EnhancedStoryGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.headers = {"Content-Type": "application/json"}

        # 길이 및 토큰 설정 변경 (더 현실적인 값으로 조정)
        self.length_configs = {
            "short_story": {
                "segments": 3,
                "words_per_segment": 200,
                "max_tokens": 1000,
                "description": "단편 이야기 (약 600자)"
            },
            "medium_story": {
                "segments": 5,
                "words_per_segment": 300,
                "max_tokens": 2000,
                "description": "중편 이야기 (약 1500자)"
            },
            "long_story": {
                "segments": 7,
                "words_per_segment": 400,
                "max_tokens": 3000,
                "description": "장편 이야기 (약 2800자)"
            }
        }

    async def make_api_request(self, prompt: str, max_tokens: int = 1000,
                               temperature: float = 0.7) -> Optional[str]:
        """Gemini API 요청"""
        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.9,
                "topK": 40,
                "maxOutputTokens": max_tokens,
                "candidateCount": 1
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception as e:
            print(f"[API 요청 오류]: {e}")
            return None

    def parse_outline(self, text: str, expected_segments: int) -> Dict[str, Any]:
        """응답 텍스트에서 이야기 구조 추출"""
        data = {"title": "", "protagonist": "", "setting": "", "conflict": "", "segments": []}
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "이야기 제목" in line:
                data["title"] = line.split(":", 1)[-1].strip()
            elif "주인공" in line:
                data["protagonist"] = line.split(":", 1)[-1].strip()
            elif "배경" in line:
                data["setting"] = line.split(":", 1)[-1].strip()
            elif "갈등" in line:
                data["conflict"] = line.split(":", 1)[-1].strip()
            elif re.match(r"^\d+부:", line):
                data["segments"].append(re.sub(r"^\d+부:\s*", "", line))

        while len(data["segments"]) < expected_segments:
            part_num = len(data["segments"]) + 1
            data["segments"].append(f"제{part_num}부 - 이야기 전개")

        return data

    async def create_story_outline(self, user_request: str, config: Dict[str, Any], jia_persona: str) -> Optional[
        Dict[str, Any]]:
        """이야기 개요 생성"""
        prompt = StoryPromptBuilder.build_outline_prompt(user_request, config, jia_persona)
        print(f"=== 이야기 개요 생성 중 ({config['description']}) ===")
        outline_text = await self.make_api_request(prompt, max_tokens=800, temperature=0.4)

        if not outline_text:
            print("[개요 생성 실패] 응답이 비어있습니다.")
            return None

        # 간혹 마크다운 코드 블록으로 감싸져 오는 경우 제거
        if outline_text.strip().startswith("```"):
            outline_text = re.sub(r"```(?:json)?\n(.*)```", r"\1", outline_text, flags=re.DOTALL)

        return self.parse_outline(outline_text, config['segments'])

    async def write_story_segment(self, segment_index: int, segment_outline: str,
                                  story_plan: Dict[str, Any], previous_content: str,
                                  target_words: int, max_tokens: int, jia_persona: str) -> str:
        """이야기 부분 작성"""
        prompt = StoryPromptBuilder.build_segment_prompt(segment_index, segment_outline, story_plan,
                                                         previous_content, target_words, jia_persona)

        print(f"=== {segment_index + 1}부 작성 중: {segment_outline[:30]}... ===")
        content = await self.make_api_request(prompt, max_tokens=max_tokens, temperature=0.75)
        await asyncio.sleep(1)
        return content or f"(부분 {segment_index + 1}) 생성 실패"


# 🎯 외부에서 호출하는 메인 함수
async def generate_enhanced_story(prompt: str, story_type: str, jia_persona: str, api_key: str) -> str:
    """전체 이야기 생성"""
    if not api_key:
        return "Gemini API 키가 설정되지 않았습니다."

    generator = EnhancedStoryGenerator(api_key)
    config = generator.length_configs.get(story_type, generator.length_configs["short_story"])

    try:
        print(f"=== 향상된 이야기 생성 시작 ({config['description']}) ===")
        story_plan = await generator.create_story_outline(prompt, config, jia_persona)

        if not story_plan or not story_plan.get("segments"):
            return "이야기 개요를 생성하지 못했습니다."

        full_story = ""
        previous_content = ""

        for i, segment_outline in enumerate(story_plan["segments"]):
            segment = await generator.write_story_segment(i, segment_outline, story_plan,
                                                          previous_content, config["words_per_segment"],
                                                          config["max_tokens"], jia_persona)
            full_story += segment + "\n\n"
            previous_content = full_story
            print(f"부분 {i + 1}/{len(story_plan['segments'])} 완료")

        # 결과 출력 구성
        header = f"""
┌{'─' * 60}┐
│  🌟 {story_plan.get('title', '제목 없는 이야기'): ^54} 🌟  │
└{'─' * 60}┘

👧 주인공: {story_plan.get('protagonist', '미설정')}
🏠 배경: {story_plan.get('setting', '미설정')}
📖 길이: {len(full_story):,}자 ({config['description']})

{'─' * 64}
"""
        footer = f"""
{'─' * 64}
✨ 이야기 끝 ✨
📚 총 길이: {len(full_story):,}자
📖 예상 읽기 시간: 약 {max(1, len(full_story) // 500)}분
{'─' * 64}
"""
        return header + full_story.strip() + footer

    except Exception as e:
        print(f"[오류] 이야기 생성 실패: {e}")
        return f"이야기 생성 중 오류가 발생했습니다: {str(e)}"
