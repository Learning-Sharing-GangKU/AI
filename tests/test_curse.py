# flake8: noqa
from transformers import pipeline
from app.callout.filter.xlmr_client import XLMRClient
from app.callout.filter.registry import get_xlmr_client,init_xlmr_client

try:
        init_xlmr_client()  # env 기반 초기화
        xlmr = get_xlmr_client()
        if xlmr is None:
            print("[Startup] XLMR client not configured (env missing).")
        else:
            # 3-1) 워밍업
            _ = xlmr.predict("this is a normal sentence")
            print("[Startup] XLMR client warmed up.")
except Exception as e:
        # 외부 모델 장애가 있어도 서버 부트는 계속할지 여부는 정책으로 결정
        print(f"[Startup] XLMR init/warmup failed: {e}")


print(xlmr)

result=xlmr.predict("개보지년")
print(result)



# model_xlmr = pipeline(
#     "text-classification",
#     model="textdetox/xlmr-large-toxicity-classifier",
#     return_all_scores=True
# )
# text = "이새끼 애미 없음"


# # result_curse = model_curse(text)
# result_xlmr = model_xlmr(text)


# print(result_xlmr)

# model_curse = pipeline(
#     "text-classification",
#     model="2tle/korean-curse-detection",
#     return_all_scores=True
# )
# from app.filters.v1.curse_detection_model import LocalCurseModel

# if __name__ == "__main__":
#     model = LocalCurseModel()

#     toxic_text = "병신"
#     clean_text = "안녕하세요"

#     toxic_p = model.predict(toxic_text)
#     clean_p = model.predict(clean_text)

#     print(f"toxic('{toxic_text}')  -> {toxic_p:.4f}")
#     print(f"clean('{clean_text}')  -> {clean_p:.4f}")

#     # 단순 검증: 욕설 확률이 인사말보다 커야 한다
#     # assert toxic_p > clean_p, "욕설 확률이 정상 확률보다 커야 합니다."
#     print("OK")
