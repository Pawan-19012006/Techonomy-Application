import time
import httpx

API_URL = "http://127.0.0.1:8000/api/chat"
QUESTION = "What is the company's annual revenue?"

def run():
    print("\n" + "=" * 80)
    print(f" 🎯 BENCHMARKING HTTP POST {API_URL} (3 RUNS)")
    print("=" * 80 + "\n")

    for i in range(1, 4):
        print(f"--- RUN {i} ---")
        t0 = time.perf_counter()
        resp = httpx.post(API_URL, json={"team_name": "TEAM-01", "question": QUESTION}, timeout=75.0)
        t_total = time.perf_counter() - t0
        
        assert resp.status_code == 200, f"HTTP Error {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Status: {resp.status_code} | Duration: {t_total:.3f}s")
        print(f"Answer: '{data['answer'][:120]}...'\n")

if __name__ == "__main__":
    run()
