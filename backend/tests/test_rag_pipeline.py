"""Automated Pytest unit test suite for RAG Serving Pipeline (Phase 6)."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx

from app.config import settings
from app.knowledge.exceptions import (
    ChatServiceError,
    LLMServiceError,
    LLMTimeoutError,
    OpenRouterAPIError,
    PromptBuilderError,
)
from app.knowledge.models.search_result import SearchResult
from app.knowledge.rag.chat_service import ChatService, ChatServiceResult
from app.knowledge.rag.llm_service import LLMService
from app.knowledge.rag.prompt_builder import PromptBuilder
from app.schemas.chat import ChatResponse, SourceItem


from app.database.models import LLMLaneModel, TeamQuotaModel
from app.database.db import SessionLocal, init_db


@pytest.fixture(autouse=True)
def clean_db():
    """Ensures database tables are fresh before each test in test_rag_pipeline.py."""
    init_db()
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).delete()
        db.query(TeamQuotaModel).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def sample_search_results():
    """Fixture returning sample SearchResult objects for testing."""
    return [
        SearchResult(
            chunk_id="chunk-001",
            document_id="doc-001",
            document_name="annual_report.pdf",
            score=0.82,
            content="Revenue from operations for FY24 was INR 4,520 Crores.",
            page_numbers=[78],
            section_title="STATEMENT OF PROFIT AND LOSS",
        ),
        SearchResult(
            chunk_id="chunk-002",
            document_id="doc-001",
            document_name="annual_report.pdf",
            score=0.76,
            content="Segment revenue for environmental solutions grew 24% year-over-year.",
            page_numbers=[96, 97],
            section_title="NOTE 19: REVENUE FROM OPERATIONS",
        ),
    ]


def test_prompt_builder_structure(sample_search_results):
    """Tests PromptBuilder formatted output structure and content assembly."""
    builder = PromptBuilder()

    query = "What is the annual revenue?"
    prompt = builder.build_prompt(query, sample_search_results)

    assert "You are Techonomy Intelligence Assistant." in prompt
    assert "Never invent information." in prompt
    assert "Retrieved Context" in prompt
    assert "Chunk 1" in prompt
    assert "annual_report.pdf" in prompt
    assert "Page(s): 78" in prompt
    assert "Page(s): 96, 97" in prompt
    assert "User Question" in prompt
    assert query in prompt


def test_prompt_builder_empty_query():
    """Tests PromptBuilder validation on empty user query."""
    builder = PromptBuilder()
    with pytest.raises(PromptBuilderError, match="cannot be empty"):
        builder.build_prompt("   ", [])


@patch("app.knowledge.rag.llm_gateway.settings.GEMINI_ENABLED", False)
@patch("app.knowledge.rag.llm_gateway.settings.GEMINI_API_KEY", "")
def test_llm_service_missing_api_key():
    """Tests LLMService exception raising when OPENROUTER_API_KEY is not configured."""
    service = LLMService(api_key="")
    with pytest.raises(OpenRouterAPIError, match="API key is missing"):
        service.generate("Hello", raise_on_missing_key=True)



@patch("app.knowledge.rag.llm_gateway.settings.GEMINI_ENABLED", False)
@patch("httpx.Client.post")
def test_llm_service_successful_generation(mock_post):
    """Tests successful LLMService text generation via OpenRouter API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "According to the annual report on page 78, revenue was INR 4,520 Crores."
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    service = LLMService(api_key="sk-or-test-key")
    res = service.generate("Test prompt")

    assert "INR 4,520 Crores" in res
    assert mock_post.call_count == 1


@patch("httpx.Client.post")
def test_llm_service_timeout_retry(mock_post):
    """Tests LLMService 30-second timeout and retry logic."""
    mock_post.side_effect = httpx.TimeoutException("Connection timed out")

    service = LLMService(api_key="sk-or-test-key", timeout_seconds=0.1, max_retries=1)

    with pytest.raises(LLMTimeoutError, match="timed out"):
        service.generate("Test prompt")

    # Verify attempt + 1 retry = 2 calls
    assert mock_post.call_count == 2


def test_chat_service_ask_with_mock_llm(sample_search_results):
    """Tests ChatService orchestration with mocked RetrievalPipeline and LLMService."""
    mock_retrieval = MagicMock()
    mock_retrieval_res = MagicMock()
    mock_retrieval_res.reranked_results = sample_search_results
    mock_retrieval.retrieve.return_value = mock_retrieval_res

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "The revenue for FY24 was INR 4,520 Crores."

    chat_service = ChatService(
        retrieval_pipeline=mock_retrieval,
        llm_service=mock_llm,
    )

    res = chat_service.ask("What is the revenue?")

    assert isinstance(res, ChatServiceResult)
    assert res.answer == "The revenue for FY24 was INR 4,520 Crores."
    assert len(res.sources) == 3  # Page 78, Page 96, Page 97
    assert res.sources[0].document == "annual_report.pdf"
    assert res.sources[0].page == 78
    assert res.confidence == 0.82

    # Verify retrieval pipeline was called
    mock_retrieval.retrieve.assert_called_once()
    # Verify LLM generate was called
    mock_llm.generate.assert_called_once()


def test_chat_api_endpoint():
    """Tests POST /api/chat endpoint execution for an event team."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database.db import reset_db

    reset_db()
    client = TestClient(app)

    # Join team
    client.post(
        f"{settings.API_PREFIX}/teams/join",
        json={
            "team_name": "TEAM-RAG",
            "member_names": ["Member 1", "Member 2"],
        },
    )

    mock_chat_res = ChatServiceResult(
        answer="Total revenue was INR 4,520 Crores.",
        sources=[SourceItem(document="annual_report.pdf", page=78)],
        confidence=0.82,
    )

    with patch.object(ChatService, "ask_async", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = mock_chat_res

        response = client.post(
            f"{settings.API_PREFIX}/chat",
            json={"team_name": "TEAM-RAG", "question": "What is the revenue?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "Total revenue was INR 4,520 Crores."
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document"] == "annual_report.pdf"
        assert data["sources"][0]["page"] == 78
        assert "team_name" in data
        assert data["team_name"] == "TEAM-RAG"


