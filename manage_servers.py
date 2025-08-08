# manage_servers.py
# FastAPI와 Streamlit 서버를 관리하는 스크립트

import subprocess
import time
import signal
import sys
import os
import threading
from typing import Optional, List
import socket
import psutil

# requests 라이브러리가 설치되어 있는지 확인 (상태 체크용)
# 이 스크립트의 다른 부분은 requests가 없어도 동작합니다.
try:
    import requests
except ImportError:
    requests = None


def find_streamlit_executable() -> Optional[List[str]]:
    """
    Streamlit 실행 명령어를 찾습니다.
    'streamlit'이 PATH에 없으면 'python -m streamlit'를 사용합니다.
    """
    # 'streamlit'이 직접 실행 가능한지 확인
    try:
        subprocess.run(["streamlit", "--version"], check=True, capture_output=True)
        return ["streamlit"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 'python -m streamlit'로 실행 가능한지 확인
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "--version"], check=True, capture_output=True)
        return [sys.executable, "-m", "streamlit"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def find_free_port(start_port: int, max_retries: int = 10) -> Optional[int]:
    """
    지정된 포트부터 시작하여 사용 가능한 포트를 찾습니다.
    """
    for i in range(max_retries):
        port = start_port + i
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    return None


def kill_port_process(port: int):
    """특정 포트를 사용하는 프로세스를 종료합니다."""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                try:
                    parent = psutil.Process(conn.pid)
                    children = parent.children(recursive=True)
                    print(f"🔧 포트 {port}을 사용하는 프로세스 종료 중... (PID: {parent.pid})")
                    for child in children:
                        child.terminate()
                    parent.terminate()
                    gone, alive = psutil.wait_procs([parent] + children, timeout=5)
                    for p in alive:
                        p.kill()  # 남아있는 프로세스 강제 종료
                    print(f"✅ 프로세스 종료 완료")
                    return True
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
    except ImportError:
        print("⚠️ psutil이 설치되지 않아 포트 정리 기능을 사용할 수 없습니다. (pip install psutil)")
    except Exception as e:
        print(f"⚠️ 포트 정리 중 오류: {e}")
    return False


class ServerManager:
    def __init__(self):
        self.fastapi_process: Optional[subprocess.Popen] = None
        self.streamlit_process: Optional[subprocess.Popen] = None
        self.streamlit_command = find_streamlit_executable()
        self.streamlit_port = 8501
        self.fastapi_port = 8001

    def _log_output(self, pipe, name):
        """서브프로세스의 출력을 실시간으로 로깅하는 스레드 함수"""
        try:
            for line in iter(pipe.readline, ''):
                print(f"[{name}] {line.strip()}")
        except ValueError:  # I/O operation on closed file.
            pass
        except Exception as e:
            print(f"[{name}] 로그 리딩 중 오류: {e}")

    def start_fastapi(self):
        """FastAPI 서버 시작"""
        print("🚀 FastAPI 서버 시작 중...")

        if not os.path.exists("main.py"):
            print("❌ main.py 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
            return False

        # 포트가 이미 사용 중인 경우 처리
        if not self._is_port_available(self.fastapi_port):
            print(f"⚠️ 포트 {self.fastapi_port}이 이미 사용 중입니다. 자동으로 정리합니다.")
            if kill_port_process(self.fastapi_port):
                time.sleep(2)
            else:
                new_port = find_free_port(8001)
                if new_port:
                    self.fastapi_port = new_port
                    print(f"📍 새로운 포트 {new_port}을 사용합니다.")
                else:
                    print("❌ 사용 가능한 포트를 찾을 수 없어 FastAPI 서버를 시작할 수 없습니다.")
                    return False

        try:
            # 환경 변수 설정
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # --reload 옵션을 다시 활성화하고, 안정적인 로그 처리를 위해 stderr 분리
            command = [
                sys.executable, "-m", "uvicorn", "main:app",
                "--host", "0.0.0.0",
                "--port", str(self.fastapi_port),
                "--reload"
            ]

            self.fastapi_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # STDOUT과 분리
                text=True,
                encoding="utf-8",
                bufsize=1
            )

            # 실시간 로그 출력을 위한 별도 스레드 실행
            threading.Thread(target=self._log_output, args=(self.fastapi_process.stdout, "FastAPI"),
                             daemon=True).start()
            threading.Thread(target=self._log_output, args=(self.fastapi_process.stderr, "FastAPI-ERR"),
                             daemon=True).start()

            print(f"⏳ FastAPI 서버 시작 대기 중... (최대 60초)")
            start_time = time.time()
            # 서버가 응답할 때까지 상태 확인
            while time.time() - start_time < 60:
                if self.fastapi_process.poll() is not None:
                    print("❌ FastAPI 서버가 예기치 않게 종료되었습니다. 위 로그를 확인하세요.")
                    return False
                if self._check_server_health(f"http://localhost:{self.fastapi_port}/docs"):
                    print(f"✅ FastAPI 서버가 http://localhost:{self.fastapi_port} 에서 실행 중입니다.")
                    return True
                time.sleep(1)

            # 타임아웃
            print("❌ FastAPI 서버가 시간 내에 시작되지 않았습니다. 로그를 확인하세요.")
            self.stop_fastapi()
            return False

        except Exception as e:
            print(f"❌ FastAPI 서버 시작 중 오류: {e}")
            return False

    def start_streamlit(self):
        """Streamlit 서버 시작"""
        if not self.streamlit_command:
            print("❌ Streamlit을 실행할 수 없습니다. 'streamlit' 명령어를 찾지 못했습니다.")
            print("💡 'pip install streamlit' 명령어로 Streamlit을 설치해주세요.")
            return False

        if not os.path.exists("app.py"):
            print("❌ app.py 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
            return False

        # 포트가 이미 사용 중인 경우 처리
        if not self._is_port_available(self.streamlit_port):
            print(f"⚠️ 포트 {self.streamlit_port}이 이미 사용 중입니다. 자동으로 정리합니다.")
            if kill_port_process(self.streamlit_port):
                time.sleep(2)
            else:
                new_port = find_free_port(8502)
                if new_port:
                    self.streamlit_port = new_port
                    print(f"📍 새로운 포트 {new_port}을 사용합니다.")
                else:
                    print("❌ Streamlit을 실행할 수 있는 사용 가능한 포트를 찾지 못했습니다.")
                    return False

        print(f"🎨 Streamlit 서버 시작 중... (포트: {self.streamlit_port})")
        try:
            # 환경 변수 설정
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            full_command = self.streamlit_command + [
                "run", "app.py",
                f"--server.port={self.streamlit_port}",
                "--server.address=0.0.0.0",
                "--server.headless=true"
            ]

            self.streamlit_process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=env
            )

            threading.Thread(target=self._log_output, args=(self.streamlit_process.stdout, "Streamlit"),
                             daemon=True).start()
            threading.Thread(target=self._log_output, args=(self.streamlit_process.stderr, "Streamlit-ERR"),
                             daemon=True).start()

            print(f"⏳ Streamlit 서버 시작 대기 중... (최대 30초)")
            start_time = time.time()
            while time.time() - start_time < 30:
                if self.streamlit_process.poll() is not None:
                    print("❌ Streamlit 서버 시작 실패. 위 로그를 확인하세요.")
                    return False
                if self._check_server_health(f"http://localhost:{self.streamlit_port}"):
                    print(f"✅ Streamlit 서버가 http://localhost:{self.streamlit_port} 에서 실행 중입니다.")
                    return True
                time.sleep(1)

            print("❌ Streamlit 서버가 시간 내에 시작되지 않았습니다. 로그를 확인하세요.")
            self.stop_streamlit()
            return False

        except Exception as e:
            print(f"❌ Streamlit 서버 시작 중 오류: {e}")
            return False

    def _is_port_available(self, port: int) -> bool:
        """포트가 사용 가능한지 확인"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) != 0

    def _check_server_health(self, url: str) -> bool:
        """서버 상태 확인"""
        if requests is None:
            return False
        try:
            # 200 상태 코드가 아니어도 일단 응답이 오면 성공으로 간주
            response = requests.get(url, timeout=2)
            return response.status_code in [200, 404]
        except requests.exceptions.ConnectionError:
            return False
        except:
            return False

    def start_both(self):
        """FastAPI와 Streamlit 서버를 동시에 시작"""
        if not self.check_requirements():
            print("요구사항을 먼저 설치해주세요.")
            return

        print("=== 지아 챗봇 시스템 시작 ===")
        self.initialize_directories()
        print("📁 필요한 디렉토리들이 준비되었습니다.")

        fastapi_success = self.start_fastapi()
        if not fastapi_success:
            print("❌ FastAPI 서버 시작에 실패했습니다.")
            self.stop_both()
            return

        streamlit_success = self.start_streamlit()
        if not streamlit_success:
            print("❌ Streamlit 서버 시작에 실패했습니다.")
            self.stop_both()
            return

        print("\n=== 서버 시작 완료 ===")
        print(f"🌐 웹 인터페이스: http://localhost:{self.streamlit_port}")
        print(f"🔧 API 문서: http://localhost:{self.fastapi_port}/docs")
        print(f"📊 API 상태: http://localhost:{self.fastapi_port}")
        print("\n종료하려면 Ctrl+C를 누르세요.")

        self._wait_for_termination()

    def _wait_for_termination(self):
        """서버가 종료될 때까지 대기"""

        def signal_handler(sig, frame):
            print("\n\n🛑 서버 종료 중...")
            self.stop_both()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        try:
            while True:
                fastapi_running = self.fastapi_process and self.fastapi_process.poll() is None
                streamlit_running = self.streamlit_process and self.streamlit_process.poll() is None

                if not fastapi_running and not streamlit_running:
                    print("⚠️ 모든 서버가 종료되었습니다.")
                    break
                elif not fastapi_running:
                    print("⚠️ FastAPI 서버가 종료되었습니다. 나머지 서버도 종료합니다.")
                    self.stop_streamlit()
                    break
                elif not streamlit_running:
                    print("⚠️ Streamlit 서버가 종료되었습니다. 나머지 서버도 종료합니다.")
                    self.stop_fastapi()
                    break

                time.sleep(2)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_both()

    def stop_fastapi(self):
        """FastAPI 서버 종료"""
        if self.fastapi_process:
            print("🛑 FastAPI 서버 종료 중...")
            self._stop_process(self.fastapi_process, "FastAPI")
            self.fastapi_process = None

    def stop_streamlit(self):
        """Streamlit 서버 종료"""
        if self.streamlit_process:
            print("🛑 Streamlit 서버 종료 중...")
            self._stop_process(self.streamlit_process, "Streamlit")
            self.streamlit_process = None

    def _stop_process(self, process: subprocess.Popen, name: str):
        """Helper function to terminate a process and its children."""
        if not process:
            return
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()
            gone, alive = psutil.wait_procs([parent] + children, timeout=5)
            for p in alive:
                p.kill()
        except psutil.NoSuchProcess:
            pass  # 프로세스가 이미 종료된 경우
        except Exception as e:
            print(f"⚠️ {name} 프로세스 종료 중 오류: {e}")

    def stop_both(self):
        """두 서버 모두 종료"""
        self.stop_fastapi()
        self.stop_streamlit()
        print("🎉 모든 서버가 안전하게 종료되었습니다.")

    def check_requirements(self):
        """필수 패키지 설치 여부 확인"""
        required_packages = [
            "fastapi", "uvicorn", "streamlit", "torch",
            "transformers", "requests", "psutil"
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            print("❌ 다음 패키지들이 누락되었습니다:")
            for package in missing_packages:
                print(f"  - {package}")
            print(f"\n설치 명령어: pip install {' '.join(missing_packages)}")
            return False

        print("✅ 모든 필수 패키지가 설치되어 있습니다.")
        return True

    def status_check(self):
        """현재 서버 상태 확인"""
        if requests is None:
            print("❌ 'requests' 라이브러리가 설치되지 않아 상태 확인 기능을 사용할 수 없습니다.")
            print("pip install requests")
            return

        print("\n=== 서버 상태 확인 ===")

        try:
            response = requests.get(f"http://localhost:{self.fastapi_port}/", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI: 정상 동작")
            else:
                print(f"⚠️ FastAPI: 상태 코드 {response.status_code}")
        except requests.exceptions.RequestException:
            print("❌ FastAPI: 연결 실패")

        try:
            response = requests.get(f"http://localhost:{self.streamlit_port}", timeout=5)
            if response.status_code == 200:
                print("✅ Streamlit: 정상 동작")
            else:
                print(f"⚠️ Streamlit: 상태 코드 {response.status_code}")
        except requests.exceptions.RequestException:
            print("❌ Streamlit: 연결 실패")

    def initialize_directories(self):
        """필요한 디렉토리와 파일들 생성"""
        dirs = ["data", "data/tags", "API"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

        if not os.path.exists("api_keys.py"):
            with open("api_keys.py", "w", encoding="utf-8") as f:
                f.write("GOOGLE_API_KEY = \"\"\nOPENROUTER_API_KEY = \"\"")
            print("⚠️ api_keys.py 파일이 생성되었습니다. API 키를 입력해주세요.")

    def debug_fastapi(self):
        """FastAPI 디버그 모드"""
        print("🔍 FastAPI 디버그 모드")

        if not os.path.exists("main.py"):
            print("❌ main.py 파일이 없습니다. 경로를 확인해주세요.")
            return

        print("✅ main.py 파일 존재")

        try:
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
                if "app" in content and "FastAPI" in content:
                    print("✅ main.py에 FastAPI 앱이 있는 것 같습니다.")
                else:
                    print("⚠️ main.py에 FastAPI 앱이 없을 수 있습니다. 코드를 확인해주세요.")
        except Exception as e:
            print(f"⚠️ main.py 읽기 오류: {e}")

        print("\n🧪 uvicorn 직접 실행 테스트:")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "uvicorn", "main:app", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("✅ uvicorn 명령어 작동")
            else:
                print("❌ uvicorn 명령어 오류:")
                print(f"--- STDERR ---\n{result.stderr}")
        except Exception as e:
            print(f"❌ uvicorn 테스트 실패: {e}")

    def test_setup(self):
        """기본 설정 테스트"""
        print("🧪 환경 테스트")

        print(f"🐍 Python 버전: {sys.version}")

        packages_to_test = ["fastapi", "uvicorn", "streamlit", "requests", "psutil"]
        for package in packages_to_test:
            try:
                __import__(package)
                print(f"✅ {package} 설치됨")
            except ImportError:
                print(f"❌ {package} 미설치")

        files_to_check = ["main.py", "app.py"]
        for file in files_to_check:
            if os.path.exists(file):
                print(f"✅ {file} 존재")
            else:
                print(f"❌ {file} 없음")

        ports_to_check = [8001, 8501]
        for port in ports_to_check:
            if self._is_port_available(port):
                print(f"✅ 포트 {port} 사용 가능")
            else:
                print(f"⚠️ 포트 {port} 사용 중")


def main():
    manager = ServerManager()
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "start":
            manager.start_both()
        elif command == "fastapi":
            manager.start_fastapi()
            manager.stop_fastapi()
        elif command == "streamlit":
            manager.start_streamlit()
            manager.stop_streamlit()
        elif command == "check":
            manager.check_requirements()
            manager.status_check()
        elif command == "init":
            manager.initialize_directories()
            print("디렉토리 초기화가 완료되었습니다.")
        elif command == "kill":
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                    kill_port_process(port)
                except ValueError:
                    print("올바른 포트 번호를 입력해주세요.")
            else:
                kill_port_process(8001)
                kill_port_process(8501)
        elif command == "debug":
            manager.debug_fastapi()
        elif command == "test":
            manager.test_setup()
        elif command == "stop":
            manager.stop_both()
        else:
            print_help()
    else:
        # 인자 없이 실행 시 기본값으로 start 실행
        manager.start_both()


def print_help():
    """도움말 출력"""
    print("""
🤖 지아 챗봇 서버 관리자

사용법:
  python manage_servers.py <명령어>

명령어:
  start           FastAPI와 Streamlit 서버를 모두 시작합니다.
  fastapi         FastAPI 서버만 시작합니다. (실행 후 종료)
  streamlit       Streamlit 서버만 시작합니다. (실행 후 종료)
  check           필수 패키지 설치 및 서버 상태를 확인합니다.
  init            필요한 디렉토리와 파일을 초기화합니다.
  kill [port]     특정 포트(기본값: 8001, 8501)를 사용하는 프로세스를 종료합니다.
  debug           FastAPI 서버 설정 및 파일을 디버그합니다.
  test            기본 환경을 테스트합니다.
  stop            실행 중인 서버를 모두 종료합니다.
""")


if __name__ == '__main__':
    # Streamlit은 별도의 터미널에서 실행되므로, 여기서는 시작만 하고 종료
    main()
