from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image

# 모델과 토크나이저 불러오기
model_name = "openbmb/MiniCPM-V-2.6"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 이미지 불러오기
image = Image.open(your_image_path.jpg) # 여기에 이미지 경로를 넣어줘

# 모델에 입력하기
# 여기에 모델에 이미지를 입력하고 텍스트를 생성하는 코드를 작성해야 해.
# 모델의 사용법은 공식 문서를 참고하는 게 제일 좋아.