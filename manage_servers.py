# manage_servers.py - 출력 리디렉션으로 디버깅

import subprocess
import os
import sys
import time
import signal

# 현재 스크립트가 실행되는 디렉토리 (예: F:\VENV)
# 이 디렉토리가 프로젝트의 루트 디렉토리와 같습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# FastAPI 앱의 경로와 Streamlit 앱의 경로를 설정합니다.
# 새로운 구조에서는 FastAPI와 Streamlit 앱이 BASE_DIR에 바로 있습니다.
FASTAPI_DIR = BASE_DIR
STREAMLIT_APP_PATH = os.path.join(BASE_DIR, "app.py")

# 가상 환경의 python 실행 파일 경로를 사용
PYTHON_EXECUTABLE = sys.executable

fastapi_process = None
streamlit_process = None


def get_pid_on_port(port):
    """
    지정된 포트를 사용하는 프로세스 ID (PID)를 찾습니다.
    Windows와 Unix-like 시스템 모두에서 동작합니다.
    """
    if sys.platform == "win32":
        try:
            # netstat -ano 명령을 사용하여 포트와 PID를 찾고, "LISTENING" 상태인 경우만 필터링합니다.
            cmd = f'netstat -ano | findstr LISTEN | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True, text=True, encoding='cp949', errors='ignore')

            # 출력에서 PID (마지막 열) 추출
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) > 4 and parts[3] == "LISTENING":
                    return int(parts[4])
            return None
        except Exception as e:
            # 포트가 사용 중이 아닐 때 발생하는 오류는 무시합니다.
            print(f"PID를 찾는 중 오류 발생 (포트: {port}): {e}")
            return None
    else:  # Unix-like 시스템 (Linux, macOS)
        try:
            # lsof -t -i :<port> 명령으로 PID 찾기
            cmd = f'lsof -t -i :{port}'
            output = subprocess.check_output(cmd, shell=True, text=True)
            return int(output.strip()) if output.strip() else None
        except Exception as e:
            print(f"PID를 찾는 중 오류 발생 (포트: {port}): {e}")
            return None


def kill_process_by_pid(pid, name="프로세스"):
    """
    지정된 PID의 프로세스를 종료합니다.
    """
    if pid is None:
        return

    print(f"{name} (PID: {pid}) 종료 중...")
    try:
        if sys.platform == "win32":
            subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True, capture_output=True)
        else:
            subprocess.run(['kill', '-9', str(pid)], check=True, capture_output=True)
        print(f"{name} 종료 완료.")
    except subprocess.CalledProcessError as e:
        print(f"오류: {name} (PID: {pid}) 종료 실패: {e.stderr.strip()}")
    except Exception as e:
        print(f"오류: {name} 종료 중 예기치 않은 오류 발생: {e}")
    time.sleep(1)


def stop_all_servers_forcefully():
    """
    FastAPI 및 Streamlit 서버 프로세스를 강제로 종료합니다.
    """
    print("--- 기존 서버 프로세스 강제 종료 시도 ---")

    # FastAPI 서버 PID 찾기 및 종료
    fastapi_pid = get_pid_on_port(8000)
    kill_process_by_pid(fastapi_pid, "FastAPI 서버")

    # Streamlit 앱 PID 찾기 및 종료
    streamlit_pid = get_pid_on_port(8501)
    kill_process_by_pid(streamlit_pid, "Streamlit 앱")

    print("--- 기존 서버 프로세스 강제 종료 시도 완료 ---")


def start_fastapi():
    """
    FastAPI 서버를 시작합니다.
    새로운 구조에서는 manage_servers.py와 main.py가 같은 폴더에 있습니다.
    """
    global fastapi_process
    if not os.path.exists(os.path.join(FASTAPI_DIR, "main.py")):
        print(f"오류: 'main.py' 파일을 찾을 수 없습니다: {os.path.join(FASTAPI_DIR, 'main.py')}")
        return

    print(f"FastAPI 서버 (디렉토리: {FASTAPI_DIR})를 시작합니다...")
    # 'uvicorn main:app --host 0.0.0.0 --port 8000' 명령을 실행합니다.
    # cwd를 FastAPI 앱이 있는 디렉토리로 설정합니다.
    # PYTHONPATH를 BASE_DIR로 설정하여 파이썬이 모든 모듈을 찾을 수 있도록 합니다.
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR
    cmd = [PYTHON_EXECUTABLE, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

    # stdout과 stderr을 부모 프로세스와 연결하여 출력 내용을 즉시 확인할 수 있도록 수정합니다.
    fastapi_process = subprocess.Popen(cmd, cwd=FASTAPI_DIR, env=env, stdout=sys.stdout, stderr=sys.stderr)
    print("FastAPI 서버 시작 명령 완료.")


def start_streamlit():
    """
    Streamlit 앱을 시작합니다.
    """
    global streamlit_process
    if not os.path.exists(STREAMLIT_APP_PATH):
        print(f"오류: 'app.py' 파일을 찾을 수 없습니다: {STREAMLIT_APP_PATH}")
        return

    print(f"Streamlit 앱 ({STREAMLIT_APP_PATH})을 시작합니다...")
    cmd = [PYTHON_EXECUTABLE, "-m", "streamlit", "run", STREAMLIT_APP_PATH]

    # Streamlit 앱도 출력을 부모 프로세스로 리디렉션하여 디버깅을 용이하게 합니다.
    streamlit_process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    print("Streamlit 앱 시작 명령 완료.")


def stop_managed_servers():
    """
    manage_servers.py가 시작한 서버들을 종료합니다.
    """
    print("관리 중인 서버를 종료합니다...")

    if fastapi_process and fastapi_process.poll() is None:
        print("FastAPI 서버 종료 중...")
        fastapi_process.terminate()
        try:
            fastapi_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            fastapi_process.kill()
        print("FastAPI 서버 종료 완료.")

    if streamlit_process and streamlit_process.poll() is None:
        print("Streamlit 앱 종료 중...")
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()
        print("Streamlit 앱 종료 완료.")
    print("모든 관리 서버 종료 완료.")


def signal_handler(sig, frame):
    """
    Ctrl+C (SIGINT) 신호를 처리하여 서버를 종료합니다.
    """
    print("\nCtrl+C 감지. 서버를 종료합니다...")
    stop_managed_servers()
    sys.exit(0)


# Ctrl+C (SIGINT) 시그널 핸들러 등록
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print("--- 지아 챗봇 서버 관리 스크립트 시작 ---")
    print("이 스크립트를 종료하고 모든 서버를 끄려면 이 터미널에서 Ctrl+C를 누르세요.")

    # 스크립트 시작 시 기존에 실행 중인 서버를 강제로 종료
    stop_all_servers_forcefully()
    time.sleep(2)  # 프로세스 종료 후 잠시 대기

    # 서버 시작
    start_fastapi()
    time.sleep(5)  # FastAPI 서버가 완전히 시작될 시간을 충분히 기다림
    start_streamlit()

    try:
        # 메인 스크립트가 계속 실행되도록 유지하여 자식 프로세스를 관리
        while True:
            # 자식 프로세스가 예기치 않게 종료되었는지 주기적으로 확인
            if fastapi_process and fastapi_process.poll() is not None:
                print("경고: FastAPI 서버가 예기치 않게 종료되었습니다. 스크립트를 종료합니다.")
                break
            if streamlit_process and streamlit_process.poll() is not None:
                print("경고: Streamlit 앱이 예기치 않게 종료되었습니다. 스크립트를 종료합니다.")
                break
            time.sleep(1)  # 1초마다 확인
    except KeyboardInterrupt:
        pass  # signal_handler가 처리
    finally:
        # 스크립트가 어떤 방식으로든 종료될 때 관리 중인 서버를 정리
        stop_managed_servers()
        print("--- 지아 챗봇 서버 관리 스크립트 종료 ---")
