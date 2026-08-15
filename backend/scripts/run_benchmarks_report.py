import asyncio
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.database.db import SessionLocal, init_db
from app.knowledge.rag.chat_service import ChatService
from app.services.team_service import TeamService

init_db()
db = SessionLocal()

async def run_report():
    team = TeamService.join_team(db, "BENCHMARK-RUNNER", ["Tester"])
    chat_service = ChatService()
    question = "What is the company's annual revenue?"

    print("\n" + "=" * 80)
    print(" 📊 LATENCY MEASUREMENT REPORT FOR 3 RUNS")
    print("=" * 80 + "\n")

    for run_idx in range(1, 4):
        t0 = time.perf_counter()
        res = await chat_service.ask_async(question)
        t_total = time.perf_counter() - t0

        emb = res.timing.get("embedding", 0.0)
        llm = res.timing.get("llm_generation", 0.0)

        print(f"Run {run_idx}:")
        print(f"embedding={emb:.3f}s")
        print(f"llm={llm:.3f}s")
        print(f"total={t_total:.3f}s\n")

if __name__ == "__main__":
    asyncio.run(run_report())
