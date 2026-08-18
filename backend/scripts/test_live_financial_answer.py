"""Executes ChatService.ask() for the financial query and verifies generated answer & company citations."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.knowledge.rag.chat_service import ChatService


def main():
    query = "Compare the company's financial performance across the available reporting periods and identify the key areas of improvement and concern."
    
    print("Executing ChatService.ask()...")
    service = ChatService()
    result = service.ask(query=query)

    print("\n" + "=" * 80)
    print("GENERATED LLM RESPONSE:")
    print("=" * 80)
    print(result.answer)

    print("\n" + "=" * 80)
    print("PARTICIPANT-VISIBLE SOURCE CITATIONS:")
    print("=" * 80)
    for src in result.sources:
        print(f"  📄 Document: {src.document} | Page: {src.page}")


if __name__ == "__main__":
    main()
