"""Automated test suite verifying LLM response quality, reasoning isolation, finish_reason metrics, and multi-intent completeness."""

from unittest.mock import patch
import pytest
from app.knowledge.rag.llm_gateway import LLMGateway, extract_clean_answer


def test_reasoning_isolation_mock_response():
    """TEST 5: Validates that reasoning/thinking fields are discarded and only clean content is returned."""
    mock_payload = {
        "id": "gen-test-123",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "reasoning": "The user is asking for 2025 revenue. I need to scan context for financial numbers...",
                    "thinking": "Step 1: Check Page 7. Step 2: Extract revenue.",
                    "content": "The company reported total revenue of ₹6,429.38 Crores in FY 2024-25."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 450,
            "completion_tokens": 30,
            "total_tokens": 480
        }
    }

    clean_content, metrics = extract_clean_answer(mock_payload)

    assert clean_content == "The company reported total revenue of ₹6,429.38 Crores in FY 2024-25."
    assert "reasoning" not in clean_content
    assert "thinking" not in clean_content
    assert metrics["finish_reason"] == "stop"
    assert metrics["prompt_tokens"] == 450
    assert metrics["completion_tokens"] == 30


def test_inline_think_tag_stripping():
    """Validates that inline <think>...</think> tags inside content are stripped out cleanly."""
    mock_payload = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "<think>Analyzing financial figures for 2025...</think>\n\nRevenue for FY 2024-25 is ₹6,429.38 Crores."
                }
            }
        ]
    }

    clean_content, metrics = extract_clean_answer(mock_payload)
    assert clean_content == "Revenue for FY 2024-25 is ₹6,429.38 Crores."
    assert "<think>" not in clean_content


def test_finish_reason_length_diagnosis():
    """TEST 6: Validates that finish_reason='length' is captured in metrics and does not leak into output text."""
    mock_payload = {
        "choices": [
            {
                "finish_reason": "length",
                "message": {
                    "role": "assistant",
                    "content": "The company operates in..."
                }
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 500, "total_tokens": 600}
    }

    clean_content, metrics = extract_clean_answer(mock_payload)
    assert clean_content == "The company operates in..."
    assert metrics["finish_reason"] == "length"
    assert "finish_reason" not in clean_content
