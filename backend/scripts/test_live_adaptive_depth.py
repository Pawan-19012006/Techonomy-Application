"""Script to verify live adaptive response depth across sample short & complex questions."""

import asyncio
from app.knowledge.rag.chat_service import ChatService


async def test_live_questions():
    service = ChatService()
    questions = [
        "What are the major working-capital concerns facing the company?",
        "How has the company's profitability changed across the available reporting periods?",
        "What was the company's revenue last year?",
    ]

    for q in questions:
        print(f"\n==================================================")
        print(f"QUESTION: {q}")
        print(f"==================================================")
        result = await service.ask_async(q)
        print(f"ARCHETYPE: {result.retrieval_result.retrieval_plan.question_archetype}")
        print(f"TOKEN BUDGET: {result.retrieval_result.retrieval_plan.adaptive_token_budget}")
        print(f"RESPONSE LENGTH: {len(result.answer)} chars")
        print(f"SOURCES ({len(result.sources)}): {[f'{s.document} P.{s.page}' for s in result.sources[:4]]}")
        print(f"\nANSWER SNIPPET:\n{result.answer[:600]}...\n")

if __name__ == "__main__":
    asyncio.run(test_live_questions())
