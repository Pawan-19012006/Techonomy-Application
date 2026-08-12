"""Script to measure 3 real end-to-end RAG chat queries through API and log detailed timing breakdowns."""

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

QUERIES = [
    "What is the total revenue of the company for FY24?",
    "Which geographic region contributed the highest sales revenue?",
    "What is the EBITDA margin performance and growth strategy?",
]

def run_measurements():
    print("\n" + "=" * 80)
    print(" ⏱️ MEASURING END-TO-END RAG CHAT LATENCY (3 REAL QUERIES)")
    print("=" * 80 + "\n")

    for i, q in enumerate(QUERIES, start=1):
        print(f"\n--- QUERY #{i}: '{q}' ---")
        t_start = time.perf_counter()
        
        response = client.post(
            f"{settings.API_PREFIX}/chat",
            json={"team_name": "BENCHMARK-TEAM", "question": q},
        )
        
        t_duration = time.perf_counter() - t_start
        assert response.status_code == 200, f"Query #{i} failed with status {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Status: {response.status_code} | Total Measured Client Time: {t_duration:.3f}s")
        print(f"Answer snippet: '{data['answer'][:120]}...'")
        print(f"Sources count: {len(data['sources'])}")

    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    run_measurements()
