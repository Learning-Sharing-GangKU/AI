from transformers import pipeline

model = pipeline("text-classification", model="jinkyeongk/kcELECTRA-toxic-detector")

text = "실제로 만났는데 존나 못생겼습니다."
result = model(text)

print(result)
# [{'label': 'LABEL_1', 'score': 0.987}]  ← 혐오
