"""Integration test verifying QueryDecomposer & multi-query retrieval behavior end-to-end."""

import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge.rag.chat_service import ChatService
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline

async def run_integration_tests():
    pipeline = RetrievalPipeline()
    chat_service = ChatService(retrieval_pipeline=pipeline)

    print("\n" + "=" * 90)
    print(" 🚀 INTEGRATION TEST: QUERY DECOMPOSITION & MULTI-QUERY RETRIEVAL")
    print("=" * 90 + "\n")

    # Single-intent test
    q1 = "What was the company's revenue in 2025?"
    print(f"--- TEST 1 (Single Intent): '{q1}' ---")
    ret1 = pipeline.retrieve(q1)
    res1 = await chat_service.ask_async(q1)
    print(f"Raw Candidates Merged: {len(ret1.raw_search_results)}")
    print(f"Reranked Matches: {len(ret1.reranked_results)}")
    print(f"Answer Snippet: '{res1.answer[:120]}...'\n")

    # Compound query test
    q2 = "Who are the current owners of the company and what are its marketing strategies?"
    print(f"--- TEST 2 (Compound Query): '{q2}' ---")
    ret2 = pipeline.retrieve(q2)
    res2 = await chat_service.ask_async(q2)
    print(f"Raw Candidates Merged Across Subqueries: {len(ret2.raw_search_results)}")
    print(f"Reranked Matches: {len(ret2.reranked_results)}")
    print(f"Answer:\n{res2.answer}")
    print("\nSources Cited:")
    for src in res2.sources:
        print(f"  • Doc: {src.document} | Page: {src.page}")

    print("\n" + "=" * 90 + "\n")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
