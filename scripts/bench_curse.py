# flake8: noqa
# scripts/bench_curse.py
# 역할:
#   - LocalCurseModel 단일 배치/반복 호출 성능 측정(지연/처리량).
#   - 서버 없이 모델만 놓고 "최대 몇 RPS 가능한가?" 감을 잡습니다.
#
# 실행:
#   PYTHONPATH="$PWD" python scripts/bench_curse.py --iters 200 --concurrency 1 --text_len 80
#   PYTHONPATH="$PWD" python scripts/bench_curse.py --iters 200 --concurrency 8 --text_len 160

import argparse, time, threading, statistics, random
from app.filters.v1.curse_detection_model import LocalCurseModel

SAMPLES = [
    "안녕하세요 오늘 날씨 좋네요",
    "너 진짜 왜그러냐",
    "그 말은 좀 과한 표현 아닌가요?",
    "이 문장은 테스트를 위해 작성되었습니다.",
    "야 그만해라 진짜",
    "상처 주는 표현은 자제합시다.",
]

def make_text(n: int) -> str:
    s = []
    while len(" ".join(s)) < n:
        s.append(random.choice(SAMPLES))
    return " ".join(s)[:n]

def worker(model: LocalCurseModel, iters: int, text_len: int, latencies: list[int]):
    for _ in range(iters):
        text = make_text(text_len)
        t0 = time.perf_counter()
        _ = model.predict(text)  # 실측
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--text_len", type=int, default=120)
    args = ap.parse_args()

    # 모델은 프로세스당 1개만 로드(메모리 절약)
    model = LocalCurseModel(model_id=None)  # settings.CURSE_MODEL_ID 사용

    threads = []
    all_lat = []
    per_thread = args.iters // args.concurrency
    for _ in range(args.concurrency):
        lat = []
        t = threading.Thread(target=worker, args=(model, per_thread, args.text_len, lat))
        t.start()
        threads.append((t, lat))

    for t, _ in threads:
        t.join()

    for _, lat in threads:
        all_lat.extend(lat)

    if not all_lat:
        print("No samples?")
        return

    p50 = statistics.median(all_lat)
    p95 = sorted(all_lat)[int(len(all_lat)*0.95)-1]
    avg = statistics.mean(all_lat)
    rps = (args.concurrency * per_thread) / (sum(all_lat)/1000.0)  # 매우 러프한 근사

    print(f"iters={args.iters}, conc={args.concurrency}, text_len={args.text_len}")
    print(f"avg={avg:.1f}ms, p50={p50:.1f}ms, p95={p95:.1f}ms, ~RPS≈{rps:.1f}")

if __name__ == "__main__":
    main()