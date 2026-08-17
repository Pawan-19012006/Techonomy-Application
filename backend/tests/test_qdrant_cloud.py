"""Unit tests for Qdrant Cloud connection support, local fallback behavior, and API key privacy."""

import logging
from unittest.mock import MagicMock, patch
import pytest

from app.config import settings
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper


@pytest.fixture(autouse=True)
def clear_qdrant_singleton():
    """Resets shared QdrantClient singleton before and after each test."""
    QdrantClientWrapper.reset_shared_instance()
    yield
    QdrantClientWrapper.reset_shared_instance()


def test_local_qdrant_configuration_behavior():
    """Verifies that when QDRANT_URL is empty, QdrantClient connects to local host/port."""
    wrapper = QdrantClientWrapper(
        host="127.0.0.1",
        port=6333,
        storage_path="./qdrant_storage",
        url="",
        api_key="",
    )

    with patch("app.knowledge.indexing.qdrant_client.QdrantClient") as mock_qdrant_cls:
        mock_client = MagicMock()
        mock_qdrant_cls.return_value = mock_client

        client = wrapper.connect()

        assert client == mock_client
        # Assert host/port were passed, url/api_key were NOT passed
        mock_qdrant_cls.assert_called_once_with(host="127.0.0.1", port=6333, timeout=2.0)
        mock_client.get_collections.assert_called_once()


def test_qdrant_cloud_configuration_behavior():
    """Verifies that when QDRANT_URL and QDRANT_API_KEY are configured, QdrantClient connects to Cloud URL."""
    cloud_url = "https://cluster-xyz.cloud.qdrant.io:6333"
    cloud_key = "test-secret-api-key-999"

    wrapper = QdrantClientWrapper(
        url=cloud_url,
        api_key=cloud_key,
        storage_path="./qdrant_storage",
    )

    with patch("app.knowledge.indexing.qdrant_client.QdrantClient") as mock_qdrant_cls:
        mock_client = MagicMock()
        mock_qdrant_cls.return_value = mock_client

        client = wrapper.connect()

        assert client == mock_client
        mock_qdrant_cls.assert_called_once_with(
            url=cloud_url,
            api_key=cloud_key,
            timeout=settings.QDRANT_TIMEOUT_SECONDS,
        )
        mock_client.get_collections.assert_called_once()


def test_api_key_privacy_in_logs_and_errors(caplog):
    """Verifies that QDRANT_API_KEY is never exposed or logged in connection warnings or errors."""
    cloud_url = "https://cluster-xyz.cloud.qdrant.io:6333"
    sensitive_api_key = "super-secret-qdrant-cloud-token-12345"

    wrapper = QdrantClientWrapper(
        url=cloud_url,
        api_key=sensitive_api_key,
        storage_path=":memory:",
    )

    with patch("app.knowledge.indexing.qdrant_client.QdrantClient") as mock_qdrant_cls:
        # First call (Cloud connection) throws exception containing sensitive key string
        mock_cloud_client = MagicMock()
        mock_cloud_client.get_collections.side_effect = Exception(
            f"Unauthorized HTTP 401 error using key '{sensitive_api_key}'"
        )

        # Fallback call succeeds
        mock_fallback_client = MagicMock()

        mock_qdrant_cls.side_effect = [mock_cloud_client, mock_fallback_client]

        with caplog.at_level(logging.WARNING):
            client = wrapper.connect()

        # Confirm fallback succeeded
        assert client == mock_fallback_client

        # Verify sensitive API key NEVER appears in captured log records
        log_text = caplog.text
        assert sensitive_api_key not in log_text
        assert "[REDACTED_API_KEY]" in log_text
