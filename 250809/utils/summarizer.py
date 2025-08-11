# utils/summarizer.py
# 대화 기억을 요약하고 정리하는 모듈

import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import Counter


class MemorySummarizer:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.dialogues_file = os.path.join(data_dir, "dialogues.json")
        self.summary_file = os.path.join(data_dir, "memory_summary.json")

    def create_personality_profile(self, user_name: str = "담") -> Dict[str, Any]:
        """사용자의 성격과 선호도 프로필을 생성합니다."""
        dialogues = self._load_dialogues()

        if not dialogues:
            return self._default_profile(user_name)

        # 감정 패턴 분석
        emotion_patterns = self._analyze_emotion_patterns(dialogues)

        # 관심사 분석
        interests = self._analyze_interests(dialogues)

        # 대화 패턴 분석
        conversation_style = self._analyze_conversation_style(dialogues)

        # 시간대 활동 패턴
        activity_patterns = self._analyze_activity_patterns(dialogues)

        profile = {
            "user_name": user_name,
            "personality": {
                "dominant_emotions": emotion_patterns,
                "interests": interests,
                "conversation_style": conversation_style,
                "active_times": activity_patterns
            },
            "preferences": self._extract_preferences(dialogues),
            "memorable_moments": self._extract_memorable_moments(dialogues),
            "last_updated": datetime.now().isoformat()
        }

        # 프로필 저장
        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

        return profile

    def _load_dialogues(self) -> List[Dict]:
        """대화 데이터를 로드합니다."""
        if os.path.exists(self.dialogues_file):
            try:
                with open(self.dialogues_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _default_profile(self, user_name: str) -> Dict[str, Any]:
        """기본 프로필을 반환합니다."""
        return {
            "user_name": user_name,
            "personality": {
                "dominant_emotions": ["긍정적"],
                "interests": ["일상대화"],
                "conversation_style": "친근함",
                "active_times": "언제나"
            },
            "preferences": {},
            "memorable_moments": [],
            "last_updated": datetime.now().isoformat()
        }

    def _analyze_emotion_patterns(self, dialogues: List[Dict]) -> List[str]:
        """감정 패턴을 분석합니다."""
        emotion_keywords = {
            "긍정적": ["좋다", "최고", "행복", "기쁘다", "신나다", "즐겁다", "감사", "고마워"],
            "우울함": ["꿀꿀하다", "우울", "슬프다", "힘들다", "지치다", "피곤"],
            "화남": ["짜증", "화나다", "열받다", "스트레스"],
            "걱정": ["걱정", "불안", "조심", "무서워"]
        }

        emotion_counts = Counter()

        for dialogue in dialogues:
            user_message = dialogue.get("user_message", "").lower()
            for emotion, keywords in emotion_keywords.items():
                for keyword in keywords:
                    if keyword in user_message:
                        emotion_counts[emotion] += 1
                        break

        # 상위 3개 감정 반환
        return [emotion for emotion, count in emotion_counts.most_common(3)]

    def _analyze_interests(self, dialogues: List[Dict]) -> List[str]:
        """관심사를 분석합니다."""
        interest_keywords = {
            "음식": ["먹다", "맛있다", "요리", "음식", "레시피", "맛집"],
            "취미": ["게임", "영화", "음악", "책", "운동", "여행"],
            "일상": ["일어나다", "잠", "집", "학교", "회사", "친구"],
            "감정표현": ["기분", "느낌", "마음", "생각"]
        }

        interest_counts = Counter()

        for dialogue in dialogues:
            user_message = dialogue.get("user_message", "").lower()
            for interest, keywords in interest_keywords.items():
                for keyword in keywords:
                    if keyword in user_message:
                        interest_counts[interest] += 1
                        break

        return [interest for interest, count in interest_counts.most_common(5)]

    def _analyze_conversation_style(self, dialogues: List[Dict]) -> str:
        """대화 스타일을 분석합니다."""
        total_length = sum(len(d.get("user_message", "")) for d in dialogues)
        avg_length = total_length / len(dialogues) if dialogues else 0

        # 질문 빈도
        question_count = sum(1 for d in dialogues if "?" in d.get("user_message", ""))
        question_ratio = question_count / len(dialogues) if dialogues else 0

        # 감탄사 빈도
        exclamation_count = sum(1 for d in dialogues if "!" in d.get("user_message", ""))
        exclamation_ratio = exclamation_count / len(dialogues) if dialogues else 0

        if avg_length > 50:
            style = "상세한 대화"
        elif question_ratio > 0.3:
            style = "호기심 많음"
        elif exclamation_ratio > 0.4:
            style = "감정 표현 풍부"
        else:
            style = "간결한 대화"

        return style

    def _analyze_activity_patterns(self, dialogues: List[Dict]) -> str:
        """활동 시간 패턴을 분석합니다."""
        hour_counts = Counter()

        for dialogue in dialogues:
            timestamp = dialogue.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp)
                hour_counts[dt.hour] += 1
            except:
                continue

        if not hour_counts:
            return "언제나"

        most_active_hour = hour_counts.most_common(1)[0][0]

        if 6 <= most_active_hour < 12:
            return "오전형"
        elif 12 <= most_active_hour < 18:
            return "오후형"
        elif 18 <= most_active_hour < 24:
            return "저녁형"
        else:
            return "새벽형"

    def _extract_preferences(self, dialogues: List[Dict]) -> Dict[str, Any]:
        """사용자 선호도를 추출합니다."""
        preferences = {"좋아하는것": [], "싫어하는것": []}

        positive_patterns = ["좋아", "최고", "마음에 들어", "괜찮아"]
        negative_patterns = ["싫어", "별로", "안 좋아", "최악"]

        for dialogue in dialogues:
            message = dialogue.get("user_message", "")

            for pattern in positive_patterns:
                if pattern in message:
                    # 간단한 문맥 추출 (개선 가능)
                    context = message[:30] + "..." if len(message) > 30 else message
                    preferences["좋아하는것"].append(context)
                    break

            for pattern in negative_patterns:
                if pattern in message:
                    context = message[:30] + "..." if len(message) > 30 else message
                    preferences["싫어하는것"].append(context)
                    break

        # 중복 제거 및 최근 5개만 유지
        preferences["좋아하는것"] = list(set(preferences["좋아하는것"]))[-5:]
        preferences["싫어하는것"] = list(set(preferences["싫어하는것"]))[-5:]

        return preferences

    def _extract_memorable_moments(self, dialogues: List[Dict], limit: int = 10) -> List[Dict]:
        """기억할 만한 순간들을 추출합니다."""
        memorable = []

        # 길이가 긴 대화 (상세한 이야기)
        long_messages = [d for d in dialogues if len(d.get("user_message", "")) > 50]

        # 감정이 강한 대화
        emotional_keywords = ["최고", "최악", "정말", "진짜", "완전", "너무", "엄청"]
        emotional_messages = []

        for dialogue in dialogues:
            message = dialogue.get("user_message", "")
            if any(keyword in message for keyword in emotional_keywords):
                emotional_messages.append(dialogue)

        # 특별한 태그가 있는 대화
        special_tagged = [d for d in dialogues if len(d.get("tags", [])) >= 3]

        # 합치기 및 중복 제거
        all_memorable = long_messages + emotional_messages + special_tagged
        unique_memorable = {}

        for dialogue in all_memorable:
            dialogue_id = dialogue.get("id")
            if dialogue_id and dialogue_id not in unique_memorable:
                unique_memorable[dialogue_id] = {
                    "id": dialogue_id,
                    "timestamp": dialogue.get("timestamp"),
                    "user_message": dialogue.get("user_message", "")[:100] + "..." if len(
                        dialogue.get("user_message", "")) > 100 else dialogue.get("user_message", ""),
                    "tags": dialogue.get("tags", [])
                }

        # 시간순 정렬 후 최근 것부터 반환
        memorable = sorted(unique_memorable.values(),
                           key=lambda x: x.get("timestamp", ""), reverse=True)

        return memorable[:limit]

    def generate_conversation_starter(self) -> str:
        """대화 시작을 위한 문장을 생성합니다."""
        profile = self.load_personality_profile()

        if not profile:
            return "안녕, 담! 오늘은 어떤 하루를 보내고 있어?"

        interests = profile.get("personality", {}).get("interests", [])
        recent_emotions = profile.get("personality", {}).get("dominant_emotions", [])

        starters = [
            f"담, 안녕! 요즘 {interests[0] if interests else '일상'}은 어때?",
            "오늘은 기분이 어때? 뭔가 특별한 일 있었어?",
            "어서 와! 오늘은 뭘 하고 지냈어?",
            f"담! 최근에 {interests[0] if interests else '재미있는 일'} 어땠어?"
        ]

        import random
        return random.choice(starters)

    def load_personality_profile(self) -> Dict[str, Any]:
        """저장된 성격 프로필을 로드합니다."""
        if os.path.exists(self.summary_file):
            try:
                with open(self.summary_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}