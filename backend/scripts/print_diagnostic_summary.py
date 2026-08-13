import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge.rag.chat_service import ChatService
from app.knowledge.rag.prompt_builder import PromptBuilder
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline

QUERIES = [
    "What was the company's revenue in 2025?",
    "Who are the current owners of the company?",
    "What are the company's marketing strategies?",
    "Who are the current owners of the company and what are its marketing strategies?",
    "Compare the company's ownership structure and marketing strategy.",
]

def analyze_chunk_evidence(content: str):
    c = content.lower()
    own = any(t in c for t in ["shareholding", "promoter", "share capital", "equity", "director", "owner", "shreyans jain"])
    mkt = any(t in c for t in ["marketing", "sales promotion", "sales strategy", "advertising", "distribution channel"])
    return own, mkt

async def main():
    pipeline = RetrievalPipeline()
    prompt_builder = PromptBuilder()
    chat_service = ChatService(retrieval_pipeline=pipeline, prompt_builder=prompt_builder)

    print("\n" + "=" * 90)
    print(" 📊 DIAGNOSTIC SUMMARY FOR 5 TARGET QUERIES")
    print("=" * 90 + "\n")

    for i, q in enumerate(QUERIES, start=1):
        ret_res = pipeline.retrieve(q, top_k=10, top_n=5)
        chunks = ret_res.reranked_results

        pages = []
        scores = []
        own_found = False
        mkt_found = False

        for c in chunks:
            if c.page_numbers:
                pages.extend(c.page_numbers)
            scores.append(round(c.score, 4))
            o, m = analyze_chunk_evidence(c.content)
            if o: own_found = True
            if m: mkt_found = True

        chat_res = await chat_service.ask_async(q)

        print(f"--- QUERY #{i}: '{q}' ---")
        print(f"Retrieved Pages: {sorted(list(set(pages)))}")
        print(f"Retrieval Scores: {scores}")
        print(f"Evidence Found: Ownership={'YES' if own_found else 'NO'} | Marketing={'YES' if mkt_found else 'NO'}")
        print(f"Citations Count: {len(chat_res.sources)}")
        print("Generated Answer:")
        print(chat_res.answer)
        print("-" * 90 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
