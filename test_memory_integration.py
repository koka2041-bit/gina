# test_memory_integration.py
# 메모리 시스템 통합 테스트 스크립트

import asyncio
import json
import os
from datetime import datetime
from utils.tagger import ConversationTagger
from utils.memory_builder import MemoryBuilder
from utils.summarizer import MemorySummarizer


async def test_conversation_flow():
    """실제 대화 플로우 테스트"""
    print("🧪 대화 플로우 테스트 시작")
    print("-" * 40)

    # 시스템 초기화
    memory_builder = MemoryBuilder()
    summarizer = MemorySummarizer()
    tagger = ConversationTagger()

    # 테스트 시나리오: 연속된 대화들
    conversation_scenarios = [
        # 시나리오 1: 음식 관련 대화
        {
            "messages": [
                "오늘 점심에 파스타 먹었어. 정말 맛있었어!",
                "그런데 파스타 소스가 좀 짰어.",
                "다음엔 다른 파스타집 가보고 싶어."
            ],
            "test_query": "오늘 점심 뭐 먹었지?",
            "expected_tags": ["음식"]
        },

        # 시나리오 2: 감정 연결 대화
        {
            "messages": [
                "요즘 기분이 좀 우울해...",
                "친구랑 싸웠거든.",
                "화해하고 싶은데 먼저 연락하기가 어려워."
            ],
            "test_query": "기분이 안 좋아",
            "expected_tags": ["감정", "관계"]
        },

        # 시나리오 3: 활동/취미 대화
        {
            "messages": [
                "어제 새로운 게임 시작했어!",
                "RPG 게임인데 스토리가 정말 재밌어.",
                "밤새서 플레이했더니 눈이 아파..."
            ],
            "test_query": "게임 어때?",
            "expected_tags": ["취미"]
        }
    ]

    total_tests = 0
    passed_tests = 0

    for i, scenario in enumerate(conversation_scenarios, 1):
        print(f"\n📝 시나리오 {i} 테스트")

        # 대화 저장
        scenario_id = f"scenario_{i}_{datetime.now().strftime('%H%M%S')}"

        for j, message in enumerate(scenario["messages"]):
            bot_response = f"알겠어! '{message}'에 대해 잘 이해했어."
            dialogue_id = memory_builder.save_dialogue(message, bot_response)
            print(f"  💬 대화 {j + 1}: {message[:30]}... (저장 ID: {dialogue_id})")

        # 문맥 테스트
        print(f"\n  🔍 테스트 쿼리: '{scenario['test_query']}'")
        context = memory_builder.build_context_from_query(scenario["test_query"])

        # 결과 검증
        detected_tags = set(context["detected_tags"])
        expected_tags = set(scenario["expected_tags"])

        total_tests += 1

        print(f"  🏷️ 감지된 태그: {detected_tags}")
        print(f"  ✅ 기대 태그: {expected_tags}")
        print(f"  📚 관련 기억: {len(context['related_memories'])}개")
        print(f"  📄 문맥 요약: {context['context_summary']}")

        # 태그 매칭 확인
        tag_match = bool(detected_tags.intersection(expected_tags))
        memory_found = len(context['related_memories']) > 0

        if tag_match and memory_found:
            print("  ✅ 테스트 통과!")
            passed_tests += 1
        else:
            print("  ❌ 테스트 실패!")
            if not tag_match:
                print("    - 태그 감지 실패")
            if not memory_found:
                print("    - 관련 기