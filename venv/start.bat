@echo off
chcp 65001 > nul
echo 🤖 GINA - AI Assistant API Server
echo =======================================

REM Python 설치 확인
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo https://python.org에서 Python을 설치하세요.
    pause
    exit /b 1
)

REM 가상환경 확인 및 생성 (선택사항)
if not exist ".venv" (
    echo 📦 가상환경을 생성합니다...
    python -m venv .venv
)

REM 가상환경 활성화 (존재하는 경우)
if exist ".venv\Scripts\activate.bat" (
    echo ✅ 가상환경을 활성화합니다...
    call .venv\Scripts\activate.bat
)

REM 필요한 패키지 설치
echo 📦 필요한 패키지를 확인합니다...
pip install -q fastapi uvicorn[standard] google-generativeai httpx pydantic

REM API 디렉토리 생성
if not exist "API" mkdir API

REM 서버 시작
echo.
echo 🚀 서버를 시작합니다...
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

python start_server.py

echo.
echo ✅ 서버가 종료되었습니다.
pause