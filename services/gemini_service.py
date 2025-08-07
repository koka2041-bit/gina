# services/gemini_service.py - Gemini API 이야기 생성 서비스
import httpx
import asyncio
import re
from typing import Dict, Optional


class GeminiStoryService:
    """Gemini API를 활용한 이야기 생성 서비스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model_name = "gemini-2.0-flash-exp"
        self.headers = {"Content-Type": "application/json"}
        
        # 이야기 길이별 설정
        self.length_configs = {
            "short_story": {
                "segments": 4,
                "words_per_segment": 800,
                "max_tokens": 1000,
                "description": "단편 이야기 (약 3,200자)"
            },
            "medium_story": {
                "segments": 8,
                "words_per_segment": 1000,
                "max_tokens": 1200,
                "description": "중편 이야기 (약 8,000자)"
            },
            "long_story": {
                "segments": 15,
                "words_per_segment": 1200,
                "max_tokens": 1400,
                "description": "장편 이야기 (약 18,000자)"
            }
        }
    
    async def _make_api_request(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Gemini API 요청 실행"""
        api_url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        
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
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if result and result.get("candidates"):
                    candidate = result["candidates"][0]
                    if candidate.get("content") and candidate["content"].get("parts"):
                        return candidate["content"]["parts"][0].get("text", "")
                
                return ""
        except Exception as e:
            print(f"Gemini API 요청 오류: {e}")
            return f"[API 오류: {str(e)}]"
    
    async def create_story_outline(self, user_request: str, story_type: str) -> Dict:
        """이야기 개요 생성"""
        config = self.length_configs.get(story_type, self.length_configs["short_story"])
        
        outline_prompt = f"""
당신은 전문 동화 작가입니다. 다음 요청을 바탕으로 {config['segments']}부분으로 구성된 이야기 개요를 만들어주세요.

요청: {user_request}

다음 형식으로 작성해주세요:

**이야기 제목**: (매력적인 제목)
**주인공**: (이름, 나이, 특징)
**배경**: (시간과 장소)
**핵심 갈등**: (주인공이 해결해야 할 문제)

**{config['segments']}부분 구성**:
1부: (시작 - 30자 이내 요약)
2부: (전개 - 30자 이내 요약)
3부: (갈등 - 30자 이내 요약)
...
{config['segments']}부: (결말 - 30자 이내 요약)

각 부분은 명확하고 연결성 있게 구성해주세요.
"""
        
        print(f"=== 이야기 개요 생성 중 ({config['description']}) ===")
        outline_text = await self._make_api_request(outline_prompt, max_tokens=800, temperature=0.4)
        return self._parse_outline(outline_text, config['segments'])
    
    def _parse_outline(self, outline_text: str, expected_segments: int) -> Dict:
        """개요 파싱"""
        outline_data = {
            "title": "",
            "protagonist": "",
            "setting": "",
            "conflict": "",
            "segments": []
        }
        
        lines = outline_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '**이야기 제목**:' in line:
                outline_data["title"] = line.split(':', 1)[1].strip()
            elif '**주인공**:' in line:
                outline_data["protagonist"] = line.split(':', 1)[1].strip()
            elif '**배경**:' in line:
                outline_data["setting"] = line.split(':', 1)[1].strip()
            elif '**핵심 갈등**:' in line:
                outline_data["conflict"] = line.split(':', 1)[1].strip()
            elif '부분 구성' in line:
                current_section = "segments"
            elif current_section == "segments" and re.match(r'^\d+부:', line):
                segment_info = re.sub(r'^\d+부:\s*', '', line)
                if segment_info:
                    outline_data["segments"].append(segment_info)
        
        # 부족한 세그먼트 채우기
        while len(outline_data["segments"]) < expected_segments:
            part_num = len(outline_data["segments"]) + 1
            outline_data["segments"].append(f"제{part_num}부 - 이야기 전개")
        
        return outline_data
    
    async def write_story_segment(self, segment_index: int, segment_outline: str, 
                                  story_plan: Dict, previous_content: str, 
                                  target_words: int, max_tokens: int) -> str:
        """이야기 세그먼트 작성"""
        context = ""
        if previous_content:
            context = f"\n\n이전 이야기:\n{previous_content[-500:]}\n"
        
        segment_prompt = f"""
당신은 어린이를 위한 따뜻하고 감동적인 이야기를 쓰는 작가입니다.

**이야기 정보**:
- 제목: {story_plan.get('title', '')}
- 주인공: {story_plan.get('protagonist', '')}
- 배경: {story_plan.get('setting', '')}
- 갈등: {story_plan.get('conflict', '')}

{context}

**이번 부분 내용**: {segment_outline}

**작성 지침**:
1. {target_words}자 정도로 작성해주세요
2. 어린이가 읽기 쉬운 따뜻한 문체로 써주세요
3. 생생한 장면 묘사와 감정 표현을 포함해주세요
4. 교육적이고 긍정적인 메시지를 담아주세요
5. 이전 내용과 자연스럽게 연결되도록 해주세요

이야기를 계속 써주세요:
"""
        
        print(f"=== {segment_index + 1}부 작성 중: {segment_outline[:30]}... ===")
        segment_content = await self._make_api_request(segment_prompt, max_tokens=max_tokens, temperature=0.75)
        await asyncio.sleep(1.5)  # API 호출 간 지연
        return segment_content
    
    async def generate_story(self, prompt: str, story_type: str = "short_story") -> str:
        """완전한 이야기 생성"""
        config = self.length_configs.get(story_type, self.length_configs["short_story"])
        
        try:
            print(f"=== 향상된 이야기 생성 시작 ({config['description']}) ===")
            
            # 1단계: 이야기 개요 생성
            story_plan = await self.create_story_outline(prompt, story_type)
            
            if not story_plan.get("segments"):
                return "이야기 개요를 생성하지 못했습니다. 더 구체적인 요청을 해주세요."
            
            print(f"개요 생성 완료: {len(story_plan['segments'])}개 부분")
            
            # 2단계: 각 부분 순차 생성
            full_story = ""
            previous_content = ""
            
            for i, segment_outline in enumerate(story_plan["segments"]):
                segment_content = await self.write_story_segment(
                    i, segment_outline, story_plan, previous_content,
                    config["words_per_segment"], config["max_tokens"]
                )
                
                if segment_content and "[API 오류:" not in segment_content:
                    full_story += segment_content + "\n\n"
                    previous_content = full_story
                
                print(f"부분 {i + 1}/{len(story_plan['segments'])} 완료")
            
            # 3단계: 이야기 포맷팅
            story_header = f"""
┌{'─' * 60}┐
│  🌟 {story_plan.get('title', '제목 없는 이야기'): ^54} 🌟  │
└{'─' * 60}┘

👧 주인공: {story_plan.get('protagonist', '미설정')}
🏠 배경: {story_plan.get('setting', '미설정')}
📖 길이: {len(full_story):,}자 ({config['description']})

{'─' * 64}

"""
            
            story_footer = f"""

{'─' * 64}
✨ 이야기 끝 ✨

📚 총 길이: {len(full_story):,}자
📖 예상 읽기 시간: 약 {len(full_story) // 300 + 1}분
{'─' * 64}
"""
            
            final_story = story_header + full_story.strip() + story_footer
            print(f"=== 이야기 생성 완료 (총 {len(final_story):,}자) ===")
            return final_story
            
        except Exception as e:
            print(f"이야기 생성 중 오류: {e}")
            return f"이야기 생성 중 오류가 발생했습니다: {str(e)}"