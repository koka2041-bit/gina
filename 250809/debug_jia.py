# debug_jia.py - 지아 챗봇 문제 진단 스크립트

import os
import sys
import torch
import requests
import json
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def check_files():
    """필수 파일들 존재 확인"""
    print_section("파일 존재 확인")
    
    required_files = [
        "main.py", "app.py", "api_keys.py", "jia_persona.txt",
        "services/intent_classifier.py", "services/story_generator.py", 
        "services/code_generator.py", "services/chat_handlers.py",
        "utils/memory_builder.py", "utils/summarizer.py"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - 존재")
        else:
            print(f"❌ {file} - 없음")

def check_api_keys():
    """API 키 확인"""
    print_section("API 키 확인")
    
    try:
        from api_keys import GOOGLE_API_KEY, OPENROUTER_API_KEY
        
        if GOOGLE_API_KEY and len(GOOGLE_API_KEY.strip()) > 10:
            print(f"✅ Google API Key: 설정됨 ({len(GOOGLE_API_KEY)}자)")
        else:
            print("❌ Google API Key: 설정되지 않음")
            
        if OPENROUTER_API_KEY and len(OPENROUTER_API_KEY.strip()) > 10:
            print(f"✅ OpenRouter API Key: 설정됨 ({len(OPENROUTER_API_KEY)}자)")
        else:
            print("❌ OpenRouter API Key: 설정되지 않음")
            
    except ImportError as e:
        print(f"❌ api_keys.py 임포트 실패: {e}")
    except Exception as e:
        print(f"❌ API 키 확인 중 오류: {e}")

def check_model_path():
    """모델 경로 확인"""
    print_section("모델 경로 확인")
    
    model_path = r"F:\venv\MiniCPM-V"
    print(f"📂 확인할 경로: {model_path}")
    
    if os.path.exists(model_path):
        print("✅ 모델 폴더 존재")
        
        # 모델 파일들 확인
        model_files = [
            "config.json", "tokenizer_config.json", 
            "pytorch_model.bin", "model.safetensors"
        ]
        
        for file in model_files:
            file_path = os.path.join(model_path, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024*1024)  # MB
                print(f"  ✅ {file} ({size:.1f} MB)")
            else:
                print(f"  ❓ {file} - 없음 (선택적)")
                
    else:
        print("❌ 모델 폴더가 존재하지 않음")
        print("💡 해결책: python download_model.py 실행")

def test_torch():
    """PyTorch 및 CUDA 확인"""
    print_section("PyTorch 환경 확인")
    
    print(f"🐍 Python 버전: {sys.version}")
    print(f"🔥 PyTorch 버전: {torch.__version__}")
    print(f"🎮 CUDA 사용 가능: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"🎯 CUDA 버전: {torch.version.cuda}")
        print(f"📊 GPU 개수: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            name = torch.cuda.get_device_name(i)
            memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            print(f"  GPU {i}: {name} ({memory:.1f} GB)")

def test_imports():
    """필수 라이브러리 임포트 테스트"""
    print_section("라이브러리 임포트 테스트")
    
    test_imports = [
        "torch", "transformers", "fastapi", "uvicorn", 
        "streamlit", "requests", "PIL", "psutil"
    ]
    
    for lib in test_imports:
        try:
            __import__(lib)
            print(f"✅ {lib}")
        except ImportError as e:
            print(f"❌ {lib}: {e}")

def test_model_loading():
    """간단한 모델 로딩 테스트"""
    print_section("모델 로딩 테스트")
    
    try:
        from transformers import AutoTokenizer
        
        model_path = r"F:\venv\MiniCPM-V"
        
        if not os.path.exists(model_path):
            print("❌ 모델 경로가 존재하지 않아 로딩 테스트 건너뜀")
            return
            
        print("🔤 토크나이저 로딩 테스트...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path, 
            trust_remote_code=True
        )
        print("✅ 토크나이저 로딩 성공")
        
        # 간단한 토큰화 테스트
        test_text = "안녕하세요"
        tokens = tokenizer.encode(test_text)
        decoded = tokenizer.decode(tokens)
        print(f"🧪 토큰화 테스트: '{test_text}' → {len(tokens)}개 토큰 → '{decoded}'")
        
        print("⚠️ 전체 모델 로딩은 시간이 오래 걸리므로 건너뜀")
        
    except Exception as e:
        print(f"❌ 모델 로딩 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def test_backend_connection():
    """백엔드 서버 연결 테스트"""
    print_section("백엔드 서버 연결 테스트")
    
    backend_url = "http://localhost:8001"
    
    try:
        response = requests.get(f"{backend_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ 백엔드 서버 연결 성공")
            
            data = response.json()
            print(f"📄 서버 정보:")
            print(f"  버전: {data.get('version', 'N/A')}")
            print(f"  기능: {', '.join(data.get('features', []))}")
            
            # 모델 상태 확인
            try:
                status_response = requests.get(f"{backend_url}/model-status", timeout=5)
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"🤖 모델 상태:")
                    
                    minicpm = status.get("minicpm_model", {})
                    print(f"  MiniCPM-V 로드됨: {minicpm.get('loaded', False)}")
                    print(f"  디바이스: {minicpm.get('device', 'N/A')}")
                    
                    memory = status.get("memory_system", {})
                    print(f"  메모리 시스템: {memory.get('loaded', False)}")
                    
            except Exception as e:
                print(f"⚠️ 모델 상태 확인 실패: {e}")
                
        else:
            print(f"❌ 백엔드 서버 응답 오류: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 백엔드 서버에 연결할 수 없음")
        print("💡 해결책: python manage_servers.py start")
    except Exception as e:
        print(f"❌ 백엔드 연결 테스트 실패: {e}")

def test_chat_request():
    """간단한 채팅 요청 테스트"""
    print_section("채팅 요청 테스트")
    
    backend_url = "http://localhost:8001"
    
    try:
        test_message = "안녕"
        print(f"📤 테스트 메시지 전송: '{test_message}'")
        
        response = requests.post(
            f"{backend_url}/chat",
            json={"message": test_message},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "응답 없음")
            print(f"📥 응답 수신 성공:")
            print(f"  길이: {len(answer)}자")
            print(f"  내용 미리보기: {answer[:100]}...")
            
            if "음... 지금 좀 복잡한 생각을 하고 있어서" in answer:
                print("⚠️ 여전히 기본 오류 메시지가 나타남!")
            else:
                print("✅ 정상적인 응답을 받음!")
                
        else:
            print(f"❌ 채팅 요청 실패: {response.status_code}")
            try:
                error = response.json()
                print(f"  오류 내용: {error}")
            except:
                print(f"  응답 텍스트: {response.text}")
                
    except Exception as e:
        print(f"❌ 채팅 요청 테스트 실패: {e}")

def create_minimal_test():
    """최소한의 테스트용 main.py 생성"""
    print_section("최소한의 테스트 코드 생성")
    
    minimal_code = '''
# minimal_test.py - 최소한의 테스트용 FastAPI 서버
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "최소한의 테스트 서버", "status": "OK"}

@app.post("/chat")
def simple_chat(request: dict):
    user_message = request.get("message", "")
    
    # 간단한 응답 로직
    if "안녕" in user_message:
        response = "안녕 담! 나는 지아야. 테스트가 성공했어!"
    elif "이름" in user_message:
        response = "내 이름은 지아야! 지금은 테스트 모드로 실행 중이야."
    else:
        response = f"너가 '{user_message}'라고 했구나! 테스트 응답이야."
    
    return {"response": response}

if __name__ == "__main__":
    print("🧪 최소한의 테스트 서버 시작")
    uvicorn.run("minimal_test:app", host="0.0.0.0", port=8001, reload=False)
'''
    
    with open("minimal_test.py", "w", encoding="utf-8") as f:
        f.write(minimal_code.strip())
    
    print("✅ minimal_test.py 파일이 생성되었습니다.")
    print("🔧 테스트 방법:")
    print("  1. python minimal_test.py")
    print("  2. 브라우저에서 http://localhost:8001 접속")
    print("  3. Streamlit에서 채팅 테스트")

def main():
    """메인 진단 실행"""
    print("🔍 지아 챗봇 종합 진단 시작")
    print("=" * 60)
    
    # 1. 기본 환경 확인
    check_files()
    check_api_keys()
    test_imports()
    test_torch()
    
    # 2. 모델 관련 확인
    check_model_path()
    test_model_loading()
    
    # 3. 서버 연결 테스트
    test_backend_connection()
    test_chat_request()
    
    # 4. 문제 해결 제안
    print_section("문제 해결 제안")
    
    print("🛠️ 추천 해결 순서:")
    print("1. 최소한의 테스트 서버 실행:")
    print("   python debug_jia.py && python minimal_test.py")
    print()
    print("2. 모델 없이 작동하는지 확인")
    print("3. API 키 설정 확인")
    print("4. 원본 main.py 문제 확인")
    print()
    print("💡 즉시 해결책:")
    print("- minimal_test.py를 생성하겠습니까? (y/n): ", end="")
    
    answer = input().strip().lower()
    if answer in ['y', 'yes', '예']:
        create_minimal_test()
    
    print("\n🎯 진단 완료!")

if __name__ == "__main__":
    main()