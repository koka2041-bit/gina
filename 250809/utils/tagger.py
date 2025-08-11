# utils/tagger.py
# 대화에서 태그를 추출하고 분류하는 모듈

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Set


class ConversationTagger:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tags_dir = os.path.join(data_dir, "tags")

        # 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.tags_dir, exist_ok=True)

        # 태그 키워드 매핑 (확장 가능)
        self.tag_keywords = {
            "음식": [
                "파전", "막걸리", "치킨", "피자", "라면", "밥", "국", "찌개", "김치", "과자",
                "케이크", "아이스크림", "커피", "차", "물", "주스", "맥주", "소주", "와인",
                "먹다", "마시다", "배고프다", "배부르다", "달다", "짜다", "매콤하다", "맛있다", "맛없다"
            ],
            "감정": [
                "기쁘다", "슬프다", "화나다", "우울하다", "행복하다", "즐겁다", "짜증나다", "스트레스",
                "꿀꿀하다", "신나다", "걱정", "불안", "편하다", "좋다", "나쁘다", "최고", "최악",
                "기분", "마음", "감정", "느낌", "힘들다", "쉽다", "재미있다", "지루하다"
            ],
            "사건": [
                "비", "날씨", "맑다", "흐리다", "눈", "바람", "더위", "추위", "봄", "여름", "가을", "겨울",
                "일어나다", "잠자다", "공부하다", "일하다", "놀다", "쉬다", "운동", "산책", "여행",
                "만나다", "헤어지다", "시작", "끝", "성공", "실패", "약속", "계획"
            ],
            "관계": [
                "친구", "가족", "부모님", "형", "누나", "동생", "애인", "남친", "여친", "선배", "후배",
                "동료", "선생님", "학생", "이웃", "사람", "만나다", "연락", "통화", "문자", "카톡",
                "소통", "대화", "싸우다", "화해", "도움", "고마워", "미안해"
            ]
        }

    def extract_tags_from_text(self, text: str) -> Set[str]:
        """텍스트에서 태그를 추출합니다."""
        found_tags = set()
        text_lower = text.lower()

        for tag_category, keywords in self.tag_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_tags.add(tag_category)
                    break

        # 추가 패턴 매칭 (정규식 활용)
        # 시간 관련
        time_patterns = [r'\d+시', r'\d+분', r'오전', r'오후', r'새벽', r'밤', r'낮']
        for pattern in time_patterns:
            if re.search(pattern, text):
                found_tags.add("시간")
                break

        # 장소 관련
        place_patterns = [r'집', r'학교', r'회사', r'카페', r'음식점', r'마트', r'병원', r'공원']
        for pattern in place_patterns:
            if re.search(pattern, text):
                found_tags.add("장소")
                break

        return found_tags

    def save_tagged_dialogue(self, dialogue_text: str, tags: Set[str], dialogue_id: str):
        """태그별로 대화를 분류하여 저장합니다."""
        timestamp = datetime.now().isoformat()

        dialogue_entry = {
            "id": dialogue_id,
            "text": dialogue_text,
            "timestamp": timestamp,
            "tags": list(tags)
        }

        # 각 태그 파일에 저장
        for tag in tags:
            tag_file = os.path.join(self.tags_dir, f"{tag}.json")

            # 기존 데이터 로드
            tag_data = []
            if os.path.exists(tag_file):
                try:
                    with open(tag_file, "r", encoding="utf-8") as f:
                        tag_data = json.load(f)
                except:
                    tag_data = []

            # 새 대화 추가
            tag_data.append(dialogue_entry)

            # 최근 50개만 유지 (메모리 효율성)
            if len(tag_data) > 50:
                tag_data = tag_data[-50:]

            # 파일에 저장
            with open(tag_file, "w", encoding="utf-8") as f:
                json.dump(tag_data, f, ensure_ascii=False, indent=2)

    def get_related_memories(self, query_tags: Set[str], limit: int = 5) -> List[Dict]:
        """관련된 기억들을 가져옵니다."""
        related_memories = []

        for tag in query_tags:
            tag_file = os.path.join(self.tags_dir, f"{tag}.json")

            if os.path.exists(tag_file):
                try:
                    with open(tag_file, "r", encoding="utf-8") as f:
                        tag_data = json.load(f)

                    # 최근 기억들을 우선으로
                    recent_memories = sorted(tag_data, key=lambda x: x["timestamp"], reverse=True)[:limit]
                    related_memories.extend(recent_memories)

                except Exception as e:
                    print(f"태그 파일 읽기 오류 ({tag}): {e}")

        # 중복 제거 및 시간순 정렬
        unique_memories = {}
        for memory in related_memories:
            unique_memories[memory["id"]] = memory

        sorted_memories = sorted(unique_memories.values(), key=lambda x: x["timestamp"], reverse=True)
        return sorted_memories[:limit]

    def add_custom_keywords(self, category: str, keywords: List[str]):
        """사용자 정의 키워드를 추가합니다."""
        if category not in self.tag_keywords:
            self.tag_keywords[category] = []

        self.tag_keywords[category].extend(keywords)

        # 중복 제거
        self.tag_keywords[category] = list(set(self.tag_keywords[category]))