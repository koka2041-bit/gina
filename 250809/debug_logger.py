# debug_logger.py - 상세 디버깅 시스템
import logging
import sys
import os
from datetime import datetime
from typing import Optional
import traceback
import threading
import queue
import time

class DebugLogger:
    def __init__(self, debug_enabled: bool = True, log_to_file: bool = True):
        self.debug_enabled = debug_enabled
        self.log_to_file = log_to_file
        self.log_queue = queue.Queue()
        self.terminal_thread = None
        
        # 로그 디렉토리 생성
        self.logs_dir = "logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # 파일 로거 설정
        if self.log_to_file:
            self.setup_file_logger()
        
        # 터미널 스레드 시작
        if self.debug_enabled:
            self.start_debug_terminal()
    
    def setup_file_logger(self):
        """파일 로거 설정"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{self.logs_dir}/jia_debug_{timestamp}.log"
        
        # 파일 핸들러 설정
        self.file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        
        # 루트 로거에 핸들러 추가
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(self.file_handler)
        
        print(f"📄 디버그 로그 파일: {log_filename}")
    
    def start_debug_terminal(self):
        """디버그 터미널 스레드 시작"""
        self.terminal_thread = threading.Thread(
            target=self._debug_terminal_worker,
            daemon=True
        )
        self.terminal_thread.start()
        print("🖥️ 디버그 터미널이 시작되었습니다.")
    
    def _debug_terminal_worker(self):
        """디버그 터미널 워커"""
        print("\n" + "=" * 80)
        print("🔍 JIA 디버그 터미널 시작")
        print("=" * 80)
        print("📋 사용 가능한 명령어:")
        print("  - 'status': 현재 상태 확인")
        print("  - 'clear': 화면 지우기")
        print("  - 'logs': 최근 로그 보기")
        print("  - 'memory': 메모리 사용량 확인")
        print("  - 'model': 모델 상태 확인")
        print("  - 'test': 테스트 메시지 전송")
        print("  - 'exit': 디버그 모드 종료")
        print("=" * 80)
        
        while True:
            try:
                # 큐에서 로그 메시지 출력
                while not self.log_queue.empty():
                    try:
                        log_msg = self.log_queue.get_nowait()
                        print(log_msg)
                    except queue.Empty:
                        break
                
                time.sleep(0.1)  # CPU 사용량 제어
                
            except Exception as e:
                print(f"❌ 디버그 터미널 오류: {e}")
    
    def log(self, level: str, message: str, module: str = "SYSTEM", 
            function: str = "", line: int = 0, exc_info: bool = False):
        """통합 로그 함수"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 레벨별 아이콘
        icons = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "💥",
            "SUCCESS": "✅"
        }
        
        icon = icons.get(level.upper(), "📝")
        
        # 포맷된 메시지
        if function and line:
            formatted_msg = f"{timestamp} | {icon} {level:<8} | {module}:{function}:{line} | {message}"
        else:
            formatted_msg = f"{timestamp} | {icon} {level:<8} | {module} | {message}"
        
        # 콘솔 출력
        if self.debug_enabled:
            print(formatted_msg, file=sys.stderr)
            sys.stderr.flush()
            
            # 터미널 큐에 추가
            self.log_queue.put(formatted_msg)
        
        # 파일 로그
        if self.log_to_file:
            logger = logging.getLogger(module)
            log_level = getattr(logging, level.upper(), logging.INFO)
            
            if exc_info:
                logger.log(log_level, message, exc_info=True)
            else:
                logger.log(log_level, message)
    
    def debug(self, message: str, module: str = "DEBUG", **kwargs):
        """디버그 로그"""
        self.log("DEBUG", message, module, **kwargs)
    
    def info(self, message: str, module: str = "INFO", **kwargs):
        """정보 로그"""
        self.log("INFO", message, module, **kwargs)
    
    def warning(self, message: str, module: str = "WARNING", **kwargs):
        """경고 로그"""
        self.log("WARNING", message, module, **kwargs)
    
    def error(self, message: str, module: str = "ERROR", exc_info: bool = True, **kwargs):
        """오류 로그"""
        self.log("ERROR", message, module, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, module: str = "CRITICAL", exc_info: bool = True, **kwargs):
        """치명적 오류 로그"""
        self.log("CRITICAL", message, module, exc_info=exc_info, **kwargs)
    
    def success(self, message: str, module: str = "SUCCESS", **kwargs):
        """성공 로그"""
        self.log("SUCCESS", message, module, **kwargs)
    
    def model_debug(self, stage: str, details: str, **kwargs):
        """모델 관련 디버그"""
        self.debug(f"[{stage}] {details}", "MODEL", **kwargs)
    
    def chat_debug(self, user_input: str, response: str, processing_time: float, **kwargs):
        """채팅 관련 디버그"""
        self.debug(f"사용자: {user_input[:50]}...", "CHAT", **kwargs)
        self.debug(f"응답 길이: {len(response)}자, 처리시간: {processing_time:.2f}초", "CHAT", **kwargs)
        self.debug(f"응답 미리보기: {response[:100]}...", "CHAT", **kwargs)
    
    def memory_debug(self, action: str, details: str, **kwargs):
        """메모리 관련 디버그"""
        self.debug(f"[{action}] {details}", "MEMORY", **kwargs)
    
    def api_debug(self, endpoint: str, status: int, details: str, **kwargs):
        """API 관련 디버그"""
        icon = "✅" if status == 200 else "❌"
        self.debug(f"{icon} [{endpoint}] {status} - {details}", "API", **kwargs)

    def exception_handler(self, exc_type, exc_value, exc_traceback):
        """전역 예외 핸들러"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"처리되지 않은 예외: {exc_type.__name__}: {exc_value}"
        self.critical(error_msg, "GLOBAL_EXCEPTION")
        
        # 상세 트레이스백
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in tb_lines:
            self.debug(line.strip(), "TRACEBACK")

# 전역 디버거 인스턴스
_global_debugger: Optional[DebugLogger] = None

def init_debugger(debug_enabled: bool = True, log_to_file: bool = True) -> DebugLogger:
    """디버거 초기화"""
    global _global_debugger
    
    if _global_debugger is None:
        _global_debugger = DebugLogger(debug_enabled, log_to_file)
        
        # 전역 예외 핸들러 설정
        if debug_enabled:
            sys.excepthook = _global_debugger.exception_handler
    
    return _global_debugger

def get_debugger() -> Optional[DebugLogger]:
    """전역 디버거 인스턴스 반환"""
    return _global_debugger

def debug_print(*args, **kwargs):
    """간편한 디버그 출력"""
    if _global_debugger and _global_debugger.debug_enabled:
        message = " ".join(str(arg) for arg in args)
        _global_debugger.debug(message, "PRINT")

# 데코레이터
def debug_function(func):
    """함수 실행을 디버깅하는 데코레이터"""
    def wrapper(*args, **kwargs):
        debugger = get_debugger()
        if debugger:
            func_name = func.__name__
            module_name = func.__module__
            
            debugger.debug(f"함수 시작: {func_name}", module_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                debugger.success(f"함수 완료: {func_name} ({end_time - start_time:.3f}초)", module_name)
                return result
            except Exception as e:
                debugger.error(f"함수 오류: {func_name} - {str(e)}", module_name)
                raise
        else:
            return func(*args, **kwargs)
    
    return wrapper

# 시스템 모니터링 함수들
def get_system_info():
    """시스템 정보 수집"""
    try:
        import psutil
        import torch
        
        info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_usage_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
        }
        
        if torch.cuda.is_available():
            info.update({
                "gpu_available": True,
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_allocated": torch.cuda.memory_allocated(0) / (1024**3),
                "gpu_memory_reserved": torch.cuda.memory_reserved(0) / (1024**3),
                "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory / (1024**3)
            })
        else:
            info["gpu_available"] = False
        
        return info
    except ImportError:
        return {"error": "psutil not available"}

def monitor_system_resources():
    """시스템 리소스 모니터링"""
    debugger = get_debugger()
    if not debugger:
        return
    
    info = get_system_info()
    
    if "error" not in info:
        debugger.info(f"CPU: {info['cpu_percent']:.1f}%, 메모리: {info['memory_percent']:.1f}%, 디스크: {info['disk_usage_percent']:.1f}%", "SYSTEM")
        
        if info.get("gpu_available"):
            gpu_usage = (info["gpu_memory_allocated"] / info["gpu_memory_total"]) * 100
            debugger.info(f"GPU: {info['gpu_name']}, 메모리 사용률: {gpu_usage:.1f}%", "GPU")

# 테스트 함수
def test_debugger():
    """디버거 테스트"""
    debugger = get_debugger()
    if not debugger:
        print("디버거가 초기화되지 않았습니다.")
        return
    
    debugger.info("디버거 테스트 시작")
    debugger.debug("이것은 디버그 메시지입니다")
    debugger.warning("이것은 경고 메시지입니다")
    debugger.success("이것은 성공 메시지입니다")
    
    try:
        # 의도적 오류
        1 / 0
    except Exception:
        debugger.error("의도적 테스트 오류")
    
    debugger.model_debug("TEST_STAGE", "모델 테스트 중...")
    debugger.chat_debug("안녕하세요", "안녕하세요! 잘 지내세요?", 0.5)
    debugger.memory_debug("SAVE", "대화 저장 중...")
    debugger.api_debug("/chat", 200, "채팅 요청 성공")
    
    monitor_system_resources()

if __name__ == "__main__":
    # 테스트 실행
    init_debugger(debug_enabled=True, log_to_file=True)
    test_debugger()
    
    print("디버거가 실행 중입니다. 'exit'를 입력하면 종료됩니다.")
    while True:
        user_input = input("명령어: ").strip()
        if user_input == "exit":
            break
        elif user_input == "test":
            test_debugger()
        elif user_input == "status":
            monitor_system_resources()
        elif user_input == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')