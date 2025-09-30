from huggingface_hub import InferenceClient
import os
import traceback

token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
client = InferenceClient(model="distilgpt2", token=token)  


def generate_intro(prompt: str, max_tokens: int = 200) -> str:
    try:
        response = client.text_generation(prompt, max_new_tokens=max_tokens)
        return response.strip()
    except Exception as e:
        print("[HF DEBUG] Exception 발생:")
        traceback.print_exc()
        return f"[HF ERROR] {repr(e)}"
