# utils/memory_builder.py
# 관련 기억들을 바탕으로 문맥을 생성하는 모듈

import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from utils.tagger import ConversationTagger


class MemoryBuilder:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.dialogues_file = os.path.join(data_dir, "dialogues.json")
        self.tag_map_file = os.path.join(data_dir, "tag_map.json")
        self.tagger = ConversationTagger(data_dir)

        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)

    def save_dialogue(self, user_message: str, bot_response: str, user_name: str = "담") -> str:
        """대화를 저장하고 고유 ID를 반환합니다."""
        dialogue_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(user_message) % 10000}"
        timestamp = datetime.now().isoformat()

        # 새 대화 항목
        new_dialogue = {
            "id": dialogue_id,
            "timestamp": timestamp,
            "user_name": user_name,
            "user_message": user_message,
            "bot_response": bot_response,
            "tags": []  # 태그는 나중에 추가
        }

        # 기존 대화들 로드
        dialogues = self._load_dialogues()
        dialogues.append(new_dialogue)

        # 최근 1000개 대화만 유지
        if len(dialogues) > 1000:
            dialogues = dialogues[-1000:]

        # 파일에 저장
        with open(self.dialogues_file, "w", encoding="utf-8") as f:
            json.dump(dialogues, f, ensure_ascii=False, indent=2)

        # 태그 추출 및 저장
        self._extract_and_save_tags(dialogue_id, user_message)

        return dialogue_id

    def _load_dialogues(self) -> List[Dict]:
        """저장된 대화들을 로드합니다."""
        if os.path.exists(self.dialogues_file):
            try:
                with open(self.dialogues_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _extract_and_save_tags(self, dialogue_id: str, user_message: str):
        """대화에서 태그를 추출하고 저장합니다."""
        # 태그 추출
        tags = self.tagger.extract_tags_from_text(user_message)

        if tags:
            # 태그별 저장
            self.tagger.save_tagged_dialogue(user_message, tags, dialogue_id)

            # 태그 맵 업데이트
            self._update_tag_map(dialogue_id, tags)

            # 원본 대화에 태그 정보 추가
            self._add_tags_to_dialogue(dialogue_id, tags)

    def _update_tag_map(self, dialogue_id: str, tags: set):
        """태그-대화 매핑 정보를 업데이트합니다."""
        tag_map = {}

        if os.path.exists(self.tag_map_file):
            try:
                with open(self.tag_map_file, "r", encoding="utf-8") as f:
                    tag_map = json.load(f)
            except:
                tag_map = {}

        # 매핑 정보 추가
        for tag in tags:
            if tag not in tag_map:
                tag_map[tag] = []

            if dialogue_id not in tag_map[tag]:
                tag_map[tag].append(dialogue_id)

        # 저장
        with open(self.tag_map_file, "w", encoding="utf-8") as f:
            json.dump(tag_map, f, ensure_ascii=False, indent=2)

    def _add_tags_to_dialogue(self, dialogue_id: str, tags: set):
        """원본 대화에 태그 정보를 추가합니다."""
        dialogues = self._load_dialogues()

        for dialogue in dialogues:
            if dialogue["id"] == dialogue_id:
                dialogue["tags"] = list(tags)
                break

        with open(self.dialogues_file, "w", encoding="utf-8") as f:
            json.dump(dialogues, f, ensure_ascii=False, indent=2)

    def build_context_from_query(self, current_message: str, context_limit: int = 3) -> Dict[str, Any]:
        """현재 메시지를 바탕으로 관련 문맥을 구성합니다."""
        # 현재 메시지에서 태그 추출
        current_tags = self.tagger.extract_tags_from_text(current_message)

        # 관련 기억들 가져오기
        related_memories = self.tagger.get_related_memories(current_tags, limit=context_limit)

        # 최근 대화 몇 개도 포함
        recent_dialogues = self._get_recent_dialogues(limit=2)

        context = {
            "current_message": current_message,
            "detected_tags": list(current_tags),
            "related_memories": related_memories,
            "recent_context": recent_dialogues,
            "context_summary": self._generate_context_summary(related_memories, current_tags)
        }

        return context

    def _get_recent_dialogues(self, limit: int = 2) -> List[Dict]:
        """최근 대화들을 가져옵니다."""
        dialogues = self._load_dialogues()
        return dialogues[-limit:] if dialogues else []

    def _generate_context_summary(self, memories: List[Dict], current_tags: set) -> str:
        """관련 기억들을 바탕으로 문맥 요약을 생성합니다."""
        if not memories:
            return "관련된 이전 대화가 없습니다."

        summary_parts = []

        # 태그별로 그룹화
        tag_groups = {}
        for memory in memories:
            for tag in memory.get("tags", []):
                if tag in current_tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append(memory["text"])

        # 요약 생성
        for tag, texts in tag_groups.items():
            recent_text = texts[-1]  # 가장 최근 것만
            summary_parts.append(f"[{tag}] {recent_text[:50]}...")

        if not summary_parts:
            summary_parts = [f"이전에: {memories[-1]['text'][:50]}..."]

        return " | ".join(summary_parts)

    def get_conversation_stats(self) -> Dict[str, Any]:
        """대화 통계를 반환합니다."""
        dialogues = self._load_dialogues()

        if not dialogues:
            return {"total_conversations": 0, "tags": {}, "recent_activity": None}

        # 태그 통계
        tag_counts = {}
        for dialogue in dialogues:
            for tag in dialogue.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 최근 활동
        recent_dialogue = dialogues[-1]
        last_activity = datetime.fromisoformat(recent_dialogue["timestamp"])

        return {
            "total_conversations": len(dialogues),
            "tags": tag_counts,
            "recent_activity": last_activity.strftime("%Y-%m-%d %H:%M"),
            "most_common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }