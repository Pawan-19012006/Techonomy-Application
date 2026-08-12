"""CLI Script measuring 3 executions of the exact target question: 'What is the company's annual revenue?'"""

from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from app.config import settings
from app.database.sqlite import init_db
from app.main import app

init_db()
client = TestClient(app)

TARGET_QUESTION = "What is the company's annual revenue?"

def run_tests():
    print("\n" + "=" * 80)
    print(f" 🎯 TESTING TARGET QUESTION 3 TIMES: '{TARGET_QUESTION}'")
    print("=" * 80 + "\n")

    results = []

    for req_idx in range(1, 4):
        print(f"--- REQUEST #{req_idx} ---")
        t_start = time.perf_counter()

        response = client.post(
            f"{settings.API_PREFIX}/chat",
            json={"team_name": "TEAM-01", "question": TARGET_QUESTION},
        )

        t_total = time.perf_counter() - t_start
        assert response.status_code == 200, f"Request #{req_idx} failed with {response.status_code}: {response.text}"

        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Answer snippet: '{data['answer'][:120]}...'")
        print(f"Sources count: {len(data['sources'])}")
        print(f"Total Client Request Time: {t_total:.3f}s\n")
        
        results.append({
            "request": req_idx,
            "status": response.status_code,
            "total_time": round(t_total, 3),
            "sources": data["sources"],
            "team_name": data["team_name"],
        })

    print("=" * 80)
    print(" SUMMARY OF 3 TARGET QUESTION REQUESTS:")
    for r in results:
        print(f" Request #{r['request']}: Status {r['status']} | Total: {r['total_time']}s | Sources: {len(r['sources'])} | Team: {r['team_name']}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_tests()
