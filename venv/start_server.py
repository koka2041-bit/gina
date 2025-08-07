# start_server.py - Windows 친화적인 간단한 서버 시작 스크립트

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """필요한 패키지들이 설치되었는지 확인"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'google-generativeai', 
        'httpx',
        'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 다음 패키지들이 설치되지 않았습니다:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n설치 명령어:")
        print("pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_api_keys():
    """API 키 파일 존재 여부 확인"""
    api_dir = Path("API")
    api_dir.mkdir(exist_ok=True)
    
    gemini_key = api_dir / "gemini_api_key.txt"
    openrouter_key = api_dir / "openrouter_api_key.txt"
    
    has_keys = False
    
    print("\n🔑 API 키 확인:")
    if gemini_key.exists() and gemini_key.read_text().strip():
        print("✅ Gemini API 키 - 설정됨")
        has_keys = True
    else:
        print("⚠️ Gemini API 키 - 설정 필요")
        print("   파일: API/gemini_api_key.txt")
    
    if openrouter_key.exists() and openrouter_key.read_text().strip():
        print("✅ OpenRouter API 키 - 설정됨")
        has_keys = True
    else:
        print("⚠️ OpenRouter API 키 - 설정 필요")
        print("   파일: API/openrouter_api_key.txt")
    
    if not has_keys:
        print("\n⚠️ 최소 하나의 API 키가 필요합니다.")
        print("   Gemini API: https://makersuite.google.com/app/apikey")
        print("   OpenRouter API: https://openrouter.ai/keys")
    
    return has_keys

def start_server(port=8000):
    """서버 시작"""
    print(f"\n🚀 GINA 서버를 시작합니다 (포트: {port})")
    print("서버를 중지하려면 Ctrl+C를 누르세요.")
    print("="*50)
    
    try:
        # uvicorn 실행
        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ]
        
        # 서버 프로세스 시작
        process = subprocess.Popen(cmd)
        
        print(f"🌐 서버 주소: http://localhost:{port}")
        print(f"📚 API 문서: http://localhost:{port}/docs")
        print(f"🔧 ReDoc: http://localhost:{port}/redoc")
        print("="*50)
        
        # 사용자가 Ctrl+C를 누를 때까지 대기
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n\n⏹️ 서버 종료 중...")
            process.terminate()
            
            # Windows에서 프로세스 완전 종료 확인
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            print("✅ 서버가 종료되었습니다.")
            
    except FileNotFoundError:
        print("❌ uvicorn을 찾을 수 없습니다. 다음 명령어로 설치하세요:")
        print("pip install uvicorn[standard]")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")

def main():
    """메인 함수"""
    print("🤖 GINA - AI Assistant API Server")
    print("=" * 40)
    
    # 패키지 확인
    if not check_requirements():
        input("\n패키지를 설치한 후 Enter를 눌러주세요...")
        return
    
    # API 키 확인
    if not check_api_keys():
        input("\nAPI 키를 설정한 후 Enter를 눌러주세요...")
        # API 키 없이도 서버는 시작할 수 있도록 함
    
    # 포트 설정
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"⚠️ 잘못된 포트 번호: {sys.argv[1]}. 기본값 8000을 사용합니다.")
    
    # 서버 시작
    start_server(port)

if __name__ == "__main__":
    main()