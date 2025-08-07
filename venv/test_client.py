# test_client.py
import requests
import json
import time
from typing import Dict, Any

class GINATestClient:
    """GINA API 테스트 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def test_health_check(self):
        """헬스 체크 테스트"""
        print("🏥 헬스 체크 테스트...")
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"상태: {response.status_code}")
            print(f"응답: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 오류: {e}")
            return False
    
    def test_chat(self):
        """채팅 API 테스트"""
        print("\n💬 채팅 API 테스트...")
        
        test_messages = [
            "안녕하세요! 오늘 날씨가 어떤가요?",
            "파이썬으로 Hello World 출력하는 코드 만들어줘",
            "용과 기사에 대한 재미있는 이야기 써줘"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n테스트 {i}: {message}")
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={"message": message}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 성공 - 의도: {data.get('intent')}, 신뢰도: {data.get('confidence')}")
                    print(f"모델: {data.get('model_used')}")
                    print(f"응답: {data.get('response')[:100]}...")
                else:
                    print(f"❌ 실패 - 상태 코드: {response.status_code}")
                    print(f"오류: {response.text}")
                    
            except Exception as e:
                print(f"❌ 오류: {e}")
                
            time.sleep(1)  # API 호출 간격
    
    def test_story_generation(self):
        """스토리 생성 API 테스트"""
        print("\n📚 스토리 생성 API 테스트...")
        
        story_request = {
            "prompt": "마법의 숲에서 길을 잃은 소녀의 모험",
            "genre": "fantasy",
            "length": "short",
            "style": "narrative"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/story",
                json=story_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 성공 - 제목: {data.get('title')}")
                print(f"장르: {data.get('genre')}, 단어 수: {data.get('word_count')}")
                print(f"스토리: {data.get('story')[:200]}...")
            else:
                print(f"❌ 실패 - 상태 코드: {response.status_code}")
                print(f"오류: {response.text}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    def test_code_generation(self):
        """코드 생성 API 테스트"""
        print("\n💻 코드 생성 API 테스트...")
        
        code_request = {
            "description": "리스트에서 중복된 요소를 제거하는 함수",
            "language": "python",
            "complexity": "beginner",
            "include_comments": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/code",
                json=code_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 성공 - 언어: {data.get('language')}")
                print(f"복잡도: {data.get('complexity')}, 코드 라인: {data.get('metadata', {}).get('lines_of_code')}")
                print(f"코드:\n{data.get('code')[:300]}...")
                if data.get('explanation'):
                    print(f"설명: {data.get('explanation')[:100]}...")
            else:
                print(f"❌ 실패 - 상태 코드: {response.status_code}")
                print(f"오류: {response.text}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    def test_service_status(self):
        """서비스 상태 테스트"""
        print("\n📊 서비스 상태 테스트...")
        
        endpoints = [
            "/api/chat/status",
            "/api/story/status", 
            "/api/code/status"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint}: {data.get('available', 'N/A')}")
                else:
                    print(f"❌ {endpoint}: 실패 ({response.status_code})")
            except Exception as e:
                print(f"❌ {endpoint}: 오류 - {e}")
    
    def test_endpoints_info(self):
        """엔드포인트 정보 테스트"""
        print("\n📋 엔드포인트 정보 테스트...")
        
        info_endpoints = [
            "/api/story/genres",
            "/api/story/lengths", 
            "/api/story/styles",
            "/api/code/languages",
            "/api/code/complexities",
            "/api/code/examples"
        ]
        
        for endpoint in info_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get(list(data.keys())[0], []))
                    print(f"✅ {endpoint}: {count}개 항목")
                else:
                    print(f"❌ {endpoint}: 실패 ({response.status_code})")
            except Exception as e:
                print(f"❌ {endpoint}: 오류 - {e}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 GINA API 전체 테스트 시작\n" + "="*50)
        
        # 기본 연결 테스트
        if not self.test_health_check():
            print("❌ 서버 연결 실패. 서버가 실행 중인지 확인하세요.")
            return
        
        # 각 기능 테스트
        self.test_service_status()
        self.test_endpoints_info() 
        self.test_chat()
        self.test_story_generation()
        self.test_code_generation()
        
        print("\n" + "="*50)
        print("✅ 모든 테스트 완료!")

def main():
    """메인 실행 함수"""
    import sys
    
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    client = GINATestClient(base_url)
    
    print(f"🎯 테스트 대상: {base_url}")
    print("서버가 실행되고 있는지 확인하세요...")
    
    try:
        client.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ 테스트 중단됨")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()