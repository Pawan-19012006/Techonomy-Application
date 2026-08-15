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

QUERIES = [
    "What is the total revenue of the company for FY24?",
    "Which geographic region contributed the highest sales revenue?",
    "What is the EBITDA margin performance and growth strategy?",
]

async def benchmark():
    team = TeamService.join_team(db, "TIMING-BENCHMARK", ["Tester"])
    chat_service = ChatService()

    print("\n" + "=" * 80)
    print(" ⏱️ INDIVIDUAL RAG STAGE LATENCY BREAKDOWN (3 REAL QUERIES)")
    print("=" * 80 + "\n")

    for i, q in enumerate(QUERIES, start=1):
        t0 = time.perf_counter()
        res = await chat_service.ask_async(q)
        t_service = time.perf_counter() - t0

        t_db_start = time.perf_counter()
        TeamService.log_prompt(db, team.team_name, q, res.answer)
        t_db = time.perf_counter() - t_db_start

        t_total = time.perf_counter() - t0

        print(f"--- QUERY #{i}: '{q}' ---")
        print(f"query_processing = {res.timing.get('query_processing', 0.0):.4f}s")
        print(f"embedding        = {res.timing.get('embedding', 0.0):.4f}s")
        print(f"vector_search    = {res.timing.get('vector_search', 0.0):.4f}s")
        print(f"reranking        = {res.timing.get('reranking', 0.0):.4f}s")
        print(f"context_building = {res.timing.get('context_building', 0.0):.4f}s")
        print(f"prompt_building  = {res.timing.get('prompt_building', 0.0):.4f}s")
        print(f"llm_generation   = {res.timing.get('llm_generation', 0.0):.4f}s")
        print(f"logging          = {t_db:.4f}s")
        print(f"TOTAL            = {t_total:.4f}s\n")

if __name__ == "__main__":
    asyncio.run(benchmark())
