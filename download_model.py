# download_model.py
from huggingface_hub import snapshot_download
import os

# 다운로드할 최신 모델 이름
model_name = "openbmb/MiniCPM-V-2_6"

# 저장할 로컬 경로
local_model_path = r"F:\venv\MiniCPM-V"

# 폴더가 없으면 생성
os.makedirs(local_model_path, exist_ok=True)

print(f"모델 '{model_name}'을(를) 다운로드합니다. 이 작업은 시간이 오래 걸릴 수 있습니다.")
try:
    # force_download=True 옵션으로 캐시를 무시하고 다시 다운로드
    snapshot_download(
        repo_id=model_name,
        local_dir=local_model_path,
        force_download=True,
    )
    print("모델 다운로드가 성공적으로 완료되었습니다!")
except Exception as e:
    print(f"모델 다운로드 중 오류 발생: {e}")
    print("인터넷 연결을 확인하거나, 권한 문제가 없는지 확인해주세요.")
