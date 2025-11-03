# from transformers import pipeline

# model_curse = pipeline(
#     "text-classification",
#     model="2tle/korean-curse-detection",
#     return_all_scores=True
# )

# model_xlmr = pipeline(
#     "text-classification",
#     model="textdetox/xlmr-large-toxicity-classifier",
#     return_all_scores=True
# )
# text = "못생겼는데 ㄹㅇ 못생겼음 근데 귀여움 ㅋㅋ 근데 좀 더러움 코 파먹음"


# result_curse = model_curse(text)
# result_xlmr = model_xlmr(text)


# print(result_curse)
# print(result_xlmr)
# [{'label': 'LABEL_1', 'score': 0.987}]  ← 혐오


# tests/test_curse.py
# 역할:
# - 로컬 모델이 정상 로드되는지
# - '욕설'과 '정상 인사' 입력에서 확률 차이가 나는지 확인


from app.filters.v1.curse_detection_model import LocalCurseModel

if __name__ == "__main__":
    model = LocalCurseModel()

    toxic_text = "병신"
    clean_text = "안녕하세요"

    toxic_p = model.score(toxic_text)
    clean_p = model.score(clean_text)

    print(f"toxic('{toxic_text}')  -> {toxic_p:.4f}")
    print(f"clean('{clean_text}')  -> {clean_p:.4f}")

    # 단순 검증: 욕설 확률이 인사말보다 커야 한다
    assert toxic_p > clean_p, "욕설 확률이 정상 확률보다 커야 합니다."
    print("OK")
