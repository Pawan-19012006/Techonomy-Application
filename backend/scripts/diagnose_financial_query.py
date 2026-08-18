"""Diagnostic script to trace financial performance query through Two-Stage RAG pipeline."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.knowledge.retrieval.instruction_planner import InstructionPlanner
from app.knowledge.retrieval.query_decomposer import QueryDecomposer
from app.knowledge.retrieval.query_embedder import QueryEmbedder
from app.knowledge.retrieval.query_processor import QueryProcessor
from app.knowledge.retrieval.reranker import Reranker
from app.knowledge.retrieval.search_filters import SearchFilters
from app.knowledge.retrieval.vector_search import VectorSearch
from app.utils.logging import logger


def run_diagnostics():
    query = "Compare the company's financial performance across the available reporting periods and identify the key areas of improvement and concern."

    print("=" * 80)
    print("STEP 1: QUERY & INSTRUCTION RETRIEVAL (STAGE 1)")
    print("=" * 80)
    print(f"Target User Query: '{query}'\n")

    planner = InstructionPlanner()
    instruction_chunks = planner.retrieve_instruction_guidance(query=query, top_k=4)

    print(f"Retrieved {len(instruction_chunks)} Instruction Guidance Chunks from '{settings.QDRANT_INSTRUCTION_COLLECTION_NAME}':")
    for idx, chk in enumerate(instruction_chunks, start=1):
        print(f"  [{idx}] Doc: {chk.document_name} | Score: {chk.score:.4f} | Section: {chk.section_title}")
        print(f"      Content: {chk.content[:150]}...\n")

    print("=" * 80)
    print("STEP 2: RETRIEVAL PLAN GENERATION")
    print("=" * 80)
    plan = planner.create_retrieval_plan(query=query, instruction_chunks=instruction_chunks)
    print(f"Intent: {plan.intent}")
    print(f"Required Metrics: {plan.required_metrics}")
    print(f"Preferred Doc Types: {plan.preferred_document_types}")
    print(f"Analytical Operations: {plan.analytical_operations}")
    print(f"Company Search Queries: {plan.company_search_queries}")
    print(f"Guidance Summary:\n{plan.instruction_guidance_summary}\n")

    print("=" * 80)
    print("STEP 3: STAGE 2 COMPANY RETRIEVAL (QDRANT VECTOR SEARCH)")
    print("=" * 80)

    processor = QueryProcessor()
    decomposer = QueryDecomposer()
    embedder = QueryEmbedder()
    vsearch = VectorSearch()
    reranker = Reranker()

    processed_q = processor.process(query)
    subqueries = decomposer.decompose(processed_q.normalized_query)
    combined_queries = list(dict.fromkeys(subqueries + plan.company_search_queries))

    print(f"Subqueries + Plan Queries ({len(combined_queries)} total):")
    for idx, sq in enumerate(combined_queries, start=1):
        print(f"  {idx}. {sq}")

    company_filters = SearchFilters(document_type="company", visibility="user_visible")
    merged_raw_matches = []
    seen_keys = set()

    print("\n--- Per-Query Retrieval Candidates ---")
    for idx, sq in enumerate(combined_queries, start=1):
        sq_proc = processor.process(sq)
        sq_vec = embedder.embed_query(sq_proc)
        hits = vsearch.search(
            query_vector=sq_vec,
            top_k=settings.RETRIEVAL_TOP_K,
            filters=company_filters,
            collection_name=settings.QDRANT_COMPANY_COLLECTION_NAME,
        )
        print(f"\nQuery #{idx}: '{sq}' -> {len(hits)} hits returned:")
        for h_idx, hit in enumerate(hits, start=1):
            doc_type = getattr(hit, "document_type", "company")
            vis = getattr(hit, "visibility", "user_visible")
            pages_str = ", ".join(str(p) for p in hit.page_numbers) if hit.page_numbers else "N/A"
            print(f"   Hit #{h_idx}: [{hit.document_name}] Page(s): {pages_str} | Score: {hit.score:.4f} | Type: {doc_type} | Vis: {vis}")
            print(f"           Text: {hit.content[:120].strip()}...")

            if doc_type == "company" and vis == "user_visible":
                pages_tuple = tuple(sorted(hit.page_numbers)) if hit.page_numbers else ()
                key = (hit.document_name, pages_tuple, hit.chunk_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    merged_raw_matches.append(hit)

    print("\n" + "=" * 80)
    print(f"STEP 4: MERGED & DEDUPLICATED COMPANY CANDIDATES ({len(merged_raw_matches)} candidates)")
    print("=" * 80)
    doc_counts = {}
    for idx, cand in enumerate(merged_raw_matches, start=1):
        doc_name = cand.document_name
        doc_counts[doc_name] = doc_counts.get(doc_name, 0) + 1
        pages_str = ", ".join(str(p) for p in cand.page_numbers) if cand.page_numbers else "N/A"
        print(f"Candidate #{idx}: [{cand.document_name}] Page {pages_str} | Score: {cand.score:.4f} | Section: {cand.section_title}")

    print("\nCandidate Breakdown by Document:")
    for dname, count in doc_counts.items():
        print(f"   - {dname}: {count} chunk(s)")

    print("\n" + "=" * 80)
    print("STEP 5: RERANKING")
    print("=" * 80)
    reranked = reranker.rerank(
        results=merged_raw_matches,
        query=processed_q,
        top_n=settings.RETRIEVAL_RERANK_TOP_N,
    )
    print(f"Reranked Top-{len(reranked)} Chunks:")
    for idx, r_chunk in enumerate(reranked, start=1):
        pages_str = ", ".join(str(p) for p in r_chunk.page_numbers) if r_chunk.page_numbers else "N/A"
        print(f"  Reranked #{idx}: [{r_chunk.document_name}] Page {pages_str} | Rerank Score: {getattr(r_chunk, 'score', 'N/A')}")
        print(f"               Snippet: {r_chunk.content[:150].strip()}...\n")


if __name__ == "__main__":
    run_diagnostics()
