"""Diagnostic script to inspect retrieved chunks, coverage, prompt structure, and LLM responses for test queries."""

import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.database.db import SessionLocal, init_db
from app.knowledge.rag.chat_service import ChatService
from app.knowledge.rag.prompt_builder import PromptBuilder
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline
from app.services.team_service import TeamService

init_db()
db = SessionLocal()

QUERIES = [
    "What was the company's revenue in 2025?",
    "Who are the current owners of the company?",
    "What are the company's marketing strategies?",
    "Who are the current owners of the company and what are its marketing strategies?",
    "Compare the company's ownership structure and marketing strategy.",
]

def analyze_chunk_evidence(chunk_content: str):
    c_lower = chunk_content.lower()
    has_ownership = any(term in c_lower for term in ["shareholding", "promoter", "shares", "equity", "owner", "holding", "stake"])
    has_marketing = any(term in c_lower for term in ["marketing", "sales strategy", "distribution", "brand", "advertis", "market expansion"])
    return has_ownership, has_marketing

async def run_diagnostics():
    pipeline = RetrievalPipeline()
    prompt_builder = PromptBuilder()
    chat_service = ChatService(retrieval_pipeline=pipeline, prompt_builder=prompt_builder)

    print("\n" + "=" * 90)
    print(" 🔬 TECHONOMY RAG RETRIEVAL VS GENERATION DIAGNOSTIC SUITE")
    print("=" * 90 + "\n")

    for idx, q in enumerate(QUERIES, start=1):
        print("\n" + "#" * 90)
        print(f" QUERY #{idx}: '{q}'")
        print("#" * 90 + "\n")

        # Step 1: Retrieve raw SearchResult objects
        ret_res = pipeline.retrieve(q, top_k=10, top_n=5)
        chunks = ret_res.reranked_results

        print("--- [STEP 1] RETRIEVED SEARCH RESULTS (Reranked Top 5) ---")
        ownership_found = False
        marketing_found = False

        for rank, chunk in enumerate(chunks, start=1):
            has_own, has_mkt = analyze_chunk_evidence(chunk.content)
            if has_own:
                ownership_found = True
            if has_mkt:
                marketing_found = True

            pages_str = ", ".join(str(p) for p in chunk.page_numbers) if chunk.page_numbers else "N/A"
            print(f"Rank {rank}:")
            print(f"  Doc: {chunk.document_name} | Page(s): {pages_str} | Section: {chunk.section_title}")
            print(f"  Score: {chunk.score:.4f}")
            print(f"  Evidence Match: Ownership={has_own}, Marketing={has_mkt}")
            print(f"  Content Snippet (~500 chars):\n    {chunk.content.strip()[:500]}...\n")

        # Step 2: Coverage Check
        print("--- [STEP 2] EVIDENCE COVERAGE CHECK ---")
        print(f"  Ownership evidence: {'FOUND' if ownership_found else 'NOT FOUND'}")
        print(f"  Marketing evidence: {'FOUND' if marketing_found else 'NOT FOUND'}")
        print()

        # Step 3: Inspect Prompt
        prompt = prompt_builder.build_prompt(q, chunks)
        print("--- [STEP 3] FINAL PROMPT SENT TO LLM (Redacted) ---")
        print(f"Prompt Length: {len(prompt)} chars")
        print(prompt[:600] + "\n...\n" + prompt[-400:])
        print()

        # Step 6: Execute Chat Service & Get Answer
        res = await chat_service.ask_async(q)
        print("--- [STEP 6] GENERATED LLM ANSWER ---")
        print(res.answer)
        print("\nSources Cited:")
        for src in res.sources:
            print(f"  • Doc: {src.document} | Page: {src.page}")
        print(f"Confidence: {res.confidence}\n")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
