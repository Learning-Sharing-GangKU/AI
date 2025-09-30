from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_ID = "skt/kogpt2-base-v2"

# 최초 로딩 시 모델과 토크나이저 준비
print("✅ [LocalProvider] 한국어 모델 로드 중...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)


def generate_intro(prompt: str, max_tokens: int = 200) -> str:
    """
    로컬 Hugging Face 한국어 모델을 이용한 모임 소개문 생성
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    # 입력 데이터 변환
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # 텍스트 생성
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=True,      # 샘플링 기반
        top_p=0.95,          # nucleus sampling
        top_k=50,            # 상위 k 단어 제한
        temperature=0.8      # 창의성 조절
    )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)
