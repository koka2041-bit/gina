# manage_servers.py
import subprocess
import sys
import os
import signal
import time
from pathlib import Path

class ServerManager:
    """서버 관리 클래스"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.pid_file = self.base_dir / "server.pid"
        
    def install_dependencies(self):
        """필요한 패키지 설치"""
        print("📦 패키지 설치 중...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ 패키지 설치 완료!")
        except subprocess.CalledProcessError as e:
            print(f"❌ 패키지 설치 실패: {e}")
            sys.exit(1)
    
    def check_api_keys(self):
        """API 키 존재 여부 확인"""
        api_dir = self.base_dir / "API"
        gemini_key_file = api_dir / "gemini_api_key.txt"
        openrouter_key_file = api_dir / "openrouter_api_key.txt"
        
        print("\n🔑 API 키 확인 중...")
        
        # API 디렉토리 생성
        api_dir.mkdir(exist_ok=True)
        
        # Gemini API 키 확인
        if not gemini_key_file.exists():
            print("⚠️ Gemini API 키 파일이 없습니다.")
            key = input("Gemini API 키를 입력하세요 (엔터로 건너뛰기): ").strip()
            if key:
                gemini_key_file.write_text(key)
                print("✅ Gemini API 키 저장됨")
        else:
            print("✅ Gemini API 키 파일 존재")
        
        # OpenRouter API 키 확인
        if not openrouter_key_file.exists():
            print("⚠️ OpenRouter API 키 파일이 없습니다.")
            key = input("OpenRouter API 키를 입력하세요 (엔터로 건너뛰기): ").strip()
            if key:
                openrouter_key_file.write_text(key)
                print("✅ OpenRouter API 키 저장됨")
        else:
            print("✅ OpenRouter API 키 파일 존재")
    
    def start_server(self, port=8000, reload=True):
        """서버 시작"""
        print(f"\n🚀 서버 시작 중 (포트: {port})...")
        
        # 기존 서버 프로세스가 있으면 종료
        if self.is_running():
            print("기존 서버를 종료합니다...")
            self.stop_server()
            time.sleep(2)
        
        try:
            # uvicorn 명령어 구성
            cmd = [
                sys.executable, "-m", "uvicorn",
                "main:app",
                "--host", "0.0.0.0",
                "--port", str(port)
            ]
            
            if reload:
                cmd.append("--reload")
            
            # 서버 시작
            process = subprocess.Popen(cmd)
            
            # PID 저장
            self.pid_file.write_text(str(process.pid))
            
            print(f"✅ 서버가 시작되었습니다!")
            print(f"🌐 접속 주소: http://localhost:{port}")
            print(f"📚 API 문서: http://localhost:{port}/docs")
            print(f"🔧 관리 명령어: python manage_servers.py [start|stop|restart|status]")
            
            # 서버 프로세스 대기
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n⏹️ 서버 종료 중...")
                process.terminate()
                self.cleanup()
                
        except Exception as e:
            print(f"❌ 서버 시작 실패: {e}")
            self.cleanup()
    
    def stop_server(self):
        """서버 중지"""
        if not self.is_running():
            print("실행 중인 서버가 없습니다.")
            return
        
        try:
            pid = int(self.pid_file.read_text())
            if sys.platform == "win32":
                # Windows에서 프로세스 종료
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                             capture_output=True, check=False)
            else:
                os.kill(pid, signal.SIGTERM)
            print("✅ 서버가 중지되었습니다.")
        except (ProcessLookupError, ValueError, FileNotFoundError):
            print("서버 프로세스를 찾을 수 없습니다.")
        finally:
            self.cleanup()
    
    def restart_server(self, port=8000, reload=True):
        """서버 재시작"""
        print("🔄 서버 재시작 중...")
        self.stop_server()
        time.sleep(2)
        self.start_server(port, reload)
    
    def is_running(self):
        """서버 실행 상태 확인 (Windows 호환)"""
        if not self.pid_file.exists():
            return False
        
        try:
            pid = int(self.pid_file.read_text())
            return self._check_process_exists(pid)
        except (ValueError, FileNotFoundError):
            return False
    
    def _check_process_exists(self, pid):
        """플랫폼별 프로세스 존재 확인"""
        try:
            if sys.platform == "win32":
                # Windows: tasklist 명령어 사용
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'], 
                    capture_output=True, text=True, check=False
                )
                return str(pid) in result.stdout
            else:
                # Unix/Linux: os.kill 사용
                os.kill(pid, 0)
                return True
        except (ProcessLookupError, subprocess.SubprocessError, OSError):
            return False
    
    def get_status(self):
        """서버 상태 확인"""
        if self.is_running():
            pid = int(self.pid_file.read_text()) if self.pid_file.exists() else "Unknown"
            print(f"✅ 서버 실행 중 (PID: {pid})")
        else:
            print("❌ 서버가 실행되지 않음")
        
        # API 키 상태
        try:
            from config import config
            key_status = config.validate_api_keys()
            print(f"\n🔑 API 키 상태:")
            print(f"   Gemini: {'✅' if key_status['gemini']['available'] else '❌'}")
            print(f"   OpenRouter: {'✅' if key_status['openrouter']['available'] else '❌'}")
        except ImportError:
            print("\n⚠️ config 모듈을 찾을 수 없습니다. API 키 상태를 확인할 수 없습니다.")
    
    def cleanup(self):
        """정리 작업"""
        if self.pid_file.exists():
            self.pid_file.unlink()

def main():
    """메인 함수"""
    manager = ServerManager()
    
    if len(sys.argv) < 2:
        print("사용법: python manage_servers.py [command]")
        print("Commands:")
        print("  install  - 패키지 설치")
        print("  setup    - 초기 설정 (패키지 설치 + API 키 설정)")
        print("  start    - 서버 시작")
        print("  stop     - 서버 중지")
        print("  restart  - 서버 재시작")
        print("  status   - 서버 상태 확인")
        return
    
    command = sys.argv[1].lower()
    
    if command == "install":
        manager.install_dependencies()
    elif command == "setup":
        manager.install_dependencies()
        manager.check_api_keys()
    elif command == "start":
        manager.check_api_keys()
        manager.start_server()
    elif command == "stop":
        manager.stop_server()
    elif command == "restart":
        manager.restart_server()
    elif command == "status":
        manager.get_status()
    else:
        print(f"알 수 없는 명령어: {command}")

if __name__ == "__main__":
    main()